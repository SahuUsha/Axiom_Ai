from app.config import settings
from app.core.exceptions import SQLGenerationError
import anthropic
import openai
from typing import Optional

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
    
    if provider == "groq":
        import groq
        client = groq.AsyncGroq(api_key=settings.GROQ_API_KEY)
        response = await client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "system", "content": "You are an SQL generator. Only reply with the raw SQL code."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0
        )
        return response.choices[0].message.content.strip().strip("```sql").strip("```").strip()
        
    elif provider == "ollama":
        from openai import AsyncOpenAI
        # Ollama API structure matches OpenAI locally
        client = AsyncOpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
        response = await client.chat.completions.create(
            model=settings.OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": "You are an SQL generator. Only reply with the raw SQL code."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0
        )
        return response.choices[0].message.content.strip().strip("```sql").strip("```").strip()
        
    else:
        raise SQLGenerationError(f"Unsupported LLM Provider: {provider}")

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
