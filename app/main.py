from fastapi import FastAPI
from app.api.router import router

app = FastAPI(
    title="SQL Query Agent",
    description="Translates NL tasks into SQL, ensures safety, and executes against target databases",
    version="1.0.0"
)

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    from app.config import settings
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.PORT, reload=True)
