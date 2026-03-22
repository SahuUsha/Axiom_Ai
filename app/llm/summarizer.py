import json
from typing import List, Dict, Any
from app.config import settings

async def generate_summary(task: str, current_preview: List[Dict[str, Any]]) -> str:
    preview_json = json.dumps(current_preview[:20], default=str)
    prompt = f"""The user asked: "{task}".
    
Here are the first up to 20 rows of the executed query result:
{preview_json}

Write a natural language summary (2-3 sentences max) explaining what this data shows in response to the user's request.
"""
    provider = settings.LLM_PROVIDER.lower()
    
    if provider == "groq":
        import groq
        client = groq.AsyncGroq(api_key=settings.GROQ_API_KEY)
        response = await client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        return response.choices[0].message.content.strip()
        
    elif provider == "ollama":
        from openai import AsyncOpenAI
        client = AsyncOpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
        response = await client.chat.completions.create(
            model=settings.OLLAMA_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        return response.choices[0].message.content.strip()
        
    return "Summary unavailable."
