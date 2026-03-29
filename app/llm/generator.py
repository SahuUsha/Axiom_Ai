from app.config import settings
from app.core.exceptions import SQLGenerationError
from typing import Optional

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatOllama

def generate_prompt(task: str, schema: str, dialect: str, max_rows: int = 1000) -> str:
    return f"""You are a senior SQL analyst. Generate a single SQL SELECT query to answer the user's request.

Database dialect: {dialect}
Available tables and schema: {schema}
User request: {task}

Rules:
1. Generate ONLY a SELECT query — no INSERT, UPDATE, DELETE, DROP, CREATE
2. Always include LIMIT {max_rows} unless user explicitly asks for all rows
3. Use column names exactly as shown in schema
4. For aggregations, always include meaningful column aliases
5. Prefer CTEs over nested subqueries for readability
6. Output ONLY the SQL query, no explanation, no markdown fences"""

async def _call_llm(prompt: str) -> str:
    provider = settings.LLM_PROVIDER.lower()

    # Auto-select
    if getattr(settings, "XAI_API_KEY", None) and provider != "ollama":
        provider = "grok"
    elif getattr(settings, "GROQ_API_KEY", None) and provider != "ollama":
        provider = "groq"

    messages = [
        SystemMessage(content="You are an SQL generator. Only reply with the raw SQL code."),
        HumanMessage(content=prompt)
    ]
    
    try:
        if provider == "groq":
            llm = ChatGroq(api_key=settings.GROQ_API_KEY, model_name=settings.GROQ_MODEL, temperature=0.0)
        elif provider == "grok" or getattr(settings, "XAI_API_KEY", None):
            llm = ChatOpenAI(api_key=settings.XAI_API_KEY, base_url="https://api.x.ai/v1", model="grok-2-latest", temperature=0.0)
        elif provider == "ollama":
            llm = ChatOllama(base_url=settings.OLLAMA_BASE_URL, model=settings.OLLAMA_MODEL, temperature=0.0)
        elif provider == "mcp":
            # MCP (Model Context Protocol)
            llm = ChatOpenAI(api_key=settings.OPENAI_API_KEY, model_name="gpt-4", temperature=0.0)
        elif provider == "openai":
            if not getattr(settings, "OPENAI_API_KEY", None):
                raise SQLGenerationError("OPENAI_API_KEY is missing for OpenAI provider")
            llm = ChatOpenAI(api_key=settings.OPENAI_API_KEY, model_name=getattr(settings, "OPENAI_MODEL", "gpt-4o"), temperature=0.0)
        else:
            raise SQLGenerationError(f"Unsupported LLM Provider: {provider}")

        response = await llm.ainvoke(messages)
        return response.content.strip().strip("```sql").strip("`").strip("```").strip()
    except Exception as e:
        raise SQLGenerationError(f"LLM call failed: {e}")

async def generate_sql(task: str, schema: str, dialect: str) -> str:
    prompt = generate_prompt(task, schema, dialect, settings.MAX_RESULT_ROWS)
    sql = await _call_llm(prompt)
    if not sql:
        raise SQLGenerationError("LLM returned empty SQL")
    return sql

async def correct_sql(sql: str, error_msg: str, task: str, schema: str, dialect: str) -> str:
    prompt = f"""The following SQL query generated for the task '{task}' resulted in an error when executing on {dialect}.

Query:
{sql}

Error:
{error_msg}

Schema:
{schema}

Please correct the query. Output ONLY the raw SQL code. No markdown fences, no explanations.
"""
    corrected_sql = await _call_llm(prompt)
    if not corrected_sql:
        raise SQLGenerationError("LLM returned empty SQL on correction attempt")
    return corrected_sql
