import asyncio
from typing import List, Dict, Any, Tuple
from app.db.base import DatabaseConnector
from app.config import settings

class DuckDBConnector(DatabaseConnector):
    def __init__(self):
        import duckdb
        self.conn = duckdb.connect(database=':memory:', read_only=False)
        # Mount the local data path if provided
        # For simplicity in this agent, we just use a memory db or let it read parquet/csv locally
        
    async def connect(self):
        pass

    async def execute(self, sql: str, max_rows: int = 1000) -> Tuple[List[str], List[Dict[str, Any]], int]:
        loop = asyncio.get_event_loop()
        def _exec():
            # In DuckDB we can directly run
            rel = self.conn.sql(sql)
            if rel is None:
                return [], [], 0
            
            columns = rel.columns
            # Fetch limited rows for preview
            df = rel.limit(max_rows).df()
            data = df.to_dict(orient="records")
            
            # To get total rows efficiently without re-evaluating, we could try a count
            # For simplicity, we just return the fetched length if less than max_rows
            total_rows = len(data) if len(data) < max_rows else max_rows # Placeholder
            
            return columns, data, total_rows
            
        return await loop.run_in_executor(None, _exec)

    async def explain(self, sql: str) -> str:
        loop = asyncio.get_event_loop()
        def _explain():
            rel = self.conn.sql(f"EXPLAIN {sql}")
            return str(rel.fetchall())
        return await loop.run_in_executor(None, _explain)

    async def close(self):
        self.conn.close()

class AsyncPGConnector(DatabaseConnector):
    def __init__(self):
        import asyncpg
        self.asyncpg = asyncpg
        self.pool = None

    async def connect(self):
        if not self.pool:
            self.pool = await self.asyncpg.create_pool(
                dsn=settings.DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://'),
                min_size=1,
                max_size=10
            )

    async def execute(self, sql: str, max_rows: int = 1000) -> Tuple[List[str], List[Dict[str, Any]], int]:
        async with self.pool.acquire() as conn:
            stmt = await conn.prepare(sql)
            columns = [a.name for a in stmt.get_attributes()]
            records = await stmt.fetch()
            
            total_rows = len(records)
            preview_records = records[:max_rows]
            data = [dict(r) for r in preview_records]
            
            return columns, data, total_rows

    async def explain(self, sql: str) -> str:
        async with self.pool.acquire() as conn:
            records = await conn.fetch(f"EXPLAIN {sql}")
            return "\\n".join([r[0] for r in records])

    async def close(self):
        if self.pool:
            await self.pool.close()

    async def get_schema_context(self) -> str:
        if hasattr(self, '_cached_schema'):
            return self._cached_schema
            
        async with self.pool.acquire() as conn:
            query = """
                SELECT table_name, column_name, data_type 
                FROM information_schema.columns 
                WHERE table_schema = 'public'
                ORDER BY table_name, ordinal_position;
            """
            records = await conn.fetch(query)
            tables = {}
            for r in records:
                t_name, c_name, d_type = r['table_name'], r['column_name'], r['data_type']
                if t_name not in tables:
                    tables[t_name] = []
                tables[t_name].append(f"{c_name} {d_type}")
                
            schema_parts = []
            for t_name, cols in tables.items():
                schema_parts.append(f"CREATE TABLE {t_name} ({', '.join(cols)});")
                
            self._cached_schema = " ".join(schema_parts)
            return self._cached_schema

class SQLiteConnector(DatabaseConnector):
    def __init__(self):
        import sqlite3
        self.sqlite3 = sqlite3
        self.conn = None

    async def connect(self):
        # We use aiosqlite or just run in executor
        # For simplicity and given requirements, we'll use run_in_executor with sqlite3
        self.conn = self.sqlite3.connect("file::memory:?cache=shared", uri=True, check_same_thread=False)
        self.conn.row_factory = self.sqlite3.Row

    async def execute(self, sql: str, max_rows: int = 1000) -> Tuple[List[str], List[Dict[str, Any]], int]:
        loop = asyncio.get_event_loop()
        def _exec():
            cur = self.conn.cursor()
            cur.execute(sql)
            if cur.description is None:
                return [], [], 0
            columns = [col[0] for col in cur.description]
            records = cur.fetchall()
            
            total_rows = len(records)
            preview = records[:max_rows]
            data = [dict(r) for r in preview]
            return columns, data, total_rows
            
        return await loop.run_in_executor(None, _exec)

    async def explain(self, sql: str) -> str:
        loop = asyncio.get_event_loop()
        def _explain():
            cur = self.conn.cursor()
            cur.execute(f"EXPLAIN QUERY PLAN {sql}")
            records = cur.fetchall()
            return "\\n".join([str(dict(r)) for r in records])
        return await loop.run_in_executor(None, _explain)

    async def close(self):
        if self.conn:
            self.conn.close()

# Factory
def get_database_connector() -> DatabaseConnector:
    dialect = settings.DB_DIALECT.lower()
    if dialect == "duckdb":
        return DuckDBConnector()
    elif dialect == "postgresql":
        return AsyncPGConnector()
    elif dialect == "sqlite":
        return SQLiteConnector()
    # Add MySQL, Snowflake, BigQuery as needed following the same pattern
    else:
        # Fallback to duckdb for unknown
        return DuckDBConnector()
