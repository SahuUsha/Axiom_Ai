import asyncio
import httpx

async def test():
    try:
        async with httpx.AsyncClient() as client:
            payload = {
                "query": "Give me a full analysis: revenue by category, top products, and regional breakdown.",
                "_context": {
                    "t01": {
                        "source_id": "cia:local_file:528cc9767f4d5197",
                        "columns": [
                            {"name": "category", "dtype": "VARCHAR"},
                            {"name": "revenue", "dtype": "DECIMAL"},
                            {"name": "product", "dtype": "VARCHAR"},
                            {"name": "region", "dtype": "VARCHAR"}
                        ]
                    }
                }
            }
            r = await client.post('http://localhost:8002/run', json=payload, timeout=20.0)
            print("Status:", r.status_code)
            print("Response:", r.text)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    asyncio.run(test())
