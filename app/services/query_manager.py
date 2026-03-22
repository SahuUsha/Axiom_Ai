import time
import sqlglot
from typing import Dict, Any, Tuple, Optional
from app.config import settings
from app.core.exceptions import SQLSafetyError, SQLExecutionError
from app.core.safety import validate_sql_safety
from app.db.connectors import get_database_connector
from app.llm.generator import generate_sql, correct_sql
from app.llm.summarizer import generate_summary
from app.core.models import QueryResult

def transpile_sql(sql: str, to_dialect: str) -> str:
    """Transpile generic SQL to target dialect using SQLGlot"""
    valid_dialects = ["postgresql", "mysql", "sqlite", "duckdb", "snowflake", "bigquery"]
    if to_dialect.lower() not in valid_dialects:
        return sql # No-op or handle appropriately
    
    try:
        # sqlglot reads "generic" by default if not specified or might try to guess
        return sqlglot.transpile(sql, read="postgres", write=to_dialect.lower())[0]
    except Exception:
        # Fallback to original if sqlglot transpile fails to parse
        return sql

def calculate_summary_stats(data: list) -> dict:
    """Calculate basic min/max/mean for numeric columns."""
    stats = {}
    if not data:
        return stats
        
    sample = data[0]
    numeric_cols = [k for k, v in sample.items() if isinstance(v, (int, float))]
    
    for col in numeric_cols:
        values = [row[col] for row in data if row.get(col) is not None]
        if values:
            stats[col] = {
                "min": min(values),
                "max": max(values),
                "mean": sum(values) / len(values)
            }
            
    return stats

async def process_query(task: str, schema: Optional[str]) -> QueryResult:
    start_time = time.time()
    dialect = settings.DB_DIALECT
    db = get_database_connector()
    await db.connect()
    
    if not schema:
        schema = await db.get_schema_context()
        
    raw_sql = await generate_sql(task, schema, dialect)
    
    async def try_execute(query_sql: str) -> Tuple[str, list, list, int]:
        """Attempts to run SQL. Returns (final_sql, columns, data, total_rows). Raises exception on failure"""
        validate_sql_safety(query_sql)
        native_sql = transpile_sql(query_sql, dialect)
        cols, result_data, rows_total = await db.execute(native_sql, settings.MAX_RESULT_ROWS)
        return native_sql, cols, result_data, rows_total

    try:
        final_sql, columns, data, total_rows = await try_execute(raw_sql)
    except Exception as e:
        # Retry once
        corrected_sql = await correct_sql(raw_sql, str(e), task, schema, dialect)
        try:
            final_sql, columns, data, total_rows = await try_execute(corrected_sql)
        except Exception as e2:
            await db.close()
            raise SQLExecutionError(f"Failed after retry. First Error: {e}, Retry Error: {e2}")

    # Generate summary & compress
    summary_stats = calculate_summary_stats(data)
    nl_summary = await generate_summary(task, data)
    
    has_more = total_rows > settings.MAX_RESULT_ROWS if total_rows is not None else len(data) == settings.MAX_RESULT_ROWS
    
    exec_time_ms = int((time.time() - start_time) * 1000)
    
    await db.close()
    
    return QueryResult(
        sql_generated=final_sql,
        dialect=dialect,
        rows_returned=len(data),
        rows_total=total_rows,
        execution_time_ms=exec_time_ms,
        columns=columns,
        data_preview=data,
        summary_stats=summary_stats,
        natural_language_summary=nl_summary,
        has_more=has_more,
        result_token_estimate=len(str(data)) // 4  # rough estimate
    )

async def explain_query(task: str, schema: Optional[str]) -> str:
    dialect = settings.DB_DIALECT
    db = get_database_connector()
    await db.connect()
    
    if not schema:
        schema = await db.get_schema_context()
        
    raw_sql = await generate_sql(task, schema, dialect)
    validate_sql_safety(raw_sql)
    native_sql = transpile_sql(raw_sql, dialect)
    
    plan = await db.explain(native_sql)
    await db.close()
    
    return plan
