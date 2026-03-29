# SQL Query Agent

SQL Query Agent is a FastAPI-based backend application that translates Natural Language (NL) tasks into SQL queries, ensures query safety, and executes them against target databases.

## Features
- **Natural Language to SQL:** Uses LLMs to generate SQL queries from natural language text.
- **Multiple LLM Providers:** Supports Ollama, OpenAI, Anthropic, and Groq.
- **Multi-Database Support:** Executes queries against various database systems like DuckDB, PostgreSQL, MySQL, Snowflake, and BigQuery.
- **Query Safety:** Analyzes and ensures that the generated SQL queries are safe for execution.

## Prerequisites
- Python 3.9+
- Database of choice (DuckDB, PostgreSQL, etc.)
- LLM Provider setup (e.g., local Ollama running, or API keys for OpenAI/Anthropic/Groq)

## Installation

1. Clone the repository and navigate to the project directory:
   ```bash
   cd sql_query_agent
   ```

2. Create a virtual environment and activate it (optional but recommended):
   ```bash
   python -m venv .venv
   # On Windows:
   .venv\Scripts\activate
   # On macOS/Linux:
   source .venv/bin/activate
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

Copy the example environment file and update the configuration variables:

```bash
cp .env.example .env
```

### Database Setup

This microservice requires schema context to generate SQL queries. You have two options:

**Option 1: Provide schema_context in API requests (Recommended for microservices)**
```json
{
  "task_description": "What is the total revenue by product category?",
  "schema_context": "CREATE TABLE sales (product_id INT, product_name VARCHAR, category VARCHAR, quantity INT, price DECIMAL, revenue DECIMAL, sale_date DATE, region VARCHAR);"
}
```

**Option 2: Use DuckDB with local data files (For testing/development)**
- Set `DB_DIALECT=duckdb` in `.env`
- Place CSV or Parquet files in the directory specified by `DUCKDB_DATA_PATH` (default: `./data`)
- Files are automatically loaded as tables (e.g., `sales.csv` → table `sales`)

**Option 3: Connect to external database (PostgreSQL, MySQL, etc.)**
- Set `DB_DIALECT` and `DATABASE_URL` in `.env`
- The agent will introspect the database schema automatically

The current `.env` configuration uses:
- **LLM PROVIDER:** Groq (`llama-3.3-70b-versatile`)
- **DATABASE:** PostgreSQL (Neon)
- **INFRASTRUCTURE:** Docker and EC2 (as flags)

Example `.env`:
```env
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile
DB_DIALECT=postgresql
DATABASE_URL=postgresql://neondb_owner:***@ep-winter-union-a1at35ky-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require
USE_DOCKER=true
USE_EC2=true
PORT=8002
```

## API Endpoints

The following REST API endpoints are available:

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Service health check. |
| `POST` | `/query` | Execute a Natural Language query. Translates task description into SQL and runs it. |
| `POST` | `/query/explain` | Returns the query plan for a given Natural Language task. |
| `POST` | `/query/raw` | Executes a raw SQL query (Admin use). Still performs safety validation. |
| `POST` | `/aggregate` | Executes an aggregation query based on a strict specification (JSON). |

## Running the Application

Start the FastAPI application using Uvicorn:
```bash
python -m app.main
```
Or start Uvicorn directly:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```

The API will be accessible at `http://localhost:8002`.
You can access the Swagger UI documentation at `http://localhost:8002/docs`.

## Tech Stack
- **FastAPI:** Web framework for building APIs.
- **SQLAlchemy & Databases:** Asyncpg, Aiomysql, DuckDB, Snowflake, BigQuery.
- **LLM Integration:** Ollama, OpenAI, Anthropic, Groq.
- **Query Generation:** Sqlglot.
- **Testing:** Pytest, Pytest-asyncio.
