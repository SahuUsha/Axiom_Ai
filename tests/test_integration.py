import pytest
import pytest_asyncio
from app.main import app
from httpx import AsyncClient, ASGITransport
import sqlite3
from app.config import settings

@pytest_asyncio.fixture
async def sqlite_db():
    # Override settings to force simple test connection without LLM mocking if needed
    # (In a real test suite, you'd mock generator.py responses)
    settings.DB_DIALECT = "sqlite"
    
    # We will do a pure route test mock for raw query to ensure DB integrates
    yield
    
@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "sql_query_agent"}

@pytest.mark.asyncio
async def test_raw_query(sqlite_db):
    # Testing the raw query to SQLite to prove DB connection and execution works
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # We need to set up the DB state first. Let's do it directly
        from app.db.connectors import get_database_connector
        db = get_database_connector()
        await db.connect()
        # Create table bypassing validator directly on conn
        cur = db.conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS test_users (id INTEGER, name TEXT)")
        cur.execute("INSERT INTO test_users VALUES (1, 'Alice')")
        cur.execute("INSERT INTO test_users VALUES (2, 'Bob')")
        db.conn.commit()
        await db.close()
        
        # Now use raw query endpoint
        payload = {"sql": "SELECT * FROM test_users;"}
        response = await ac.post("/query/raw", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert "columns" in data
    assert "data" in data
    assert len(data["data"]) == 2
