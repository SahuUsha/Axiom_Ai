import pytest
from app.services.query_manager import transpile_sql

def test_transpile_to_snowflake():
    # A generic postgres-like query
    sql = 'SELECT DATE_TRUNC(\\'month\\', created_at) FROM users'
    # Snowflake equivalent
    result = transpile_sql(sql, "snowflake")
    # Depending on sqlglot behavior, might look like DATE_TRUNC('month', created_at)
    assert "DATE_TRUNC" in result.upper()

def test_transpile_to_mysql():
    sql = 'SELECT * FROM users LIMIT 10 OFFSET 5'
    result = transpile_sql(sql, "mysql")
    # MySQL supports LIMIT n OFFSET m exactly as well.
    assert "LIMIT 10" in result.upper()

def test_transpile_unsupported_dialect():
    sql = 'SELECT * FROM users'
    # Should return original
    assert transpile_sql(sql, "unknown_db") == sql
