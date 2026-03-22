import pytest
from app.core.safety import validate_sql_safety, SQLSafetyError

def test_valid_select():
    sql = "SELECT * FROM users;"
    # Should not raise
    validate_sql_safety(sql)

def test_drop_table():
    sql = "DROP TABLE users;"
    with pytest.raises(SQLSafetyError, match="SQL query must start with SELECT or WITH"):
        validate_sql_safety(sql)

def test_select_with_drop_inside():
    # Attempting SQL injection trick
    sql = "SELECT * FROM users; DROP TABLE accounts;"
    with pytest.raises(SQLSafetyError, match="Forbidden SQL keyword detected: DROP"):
        validate_sql_safety(sql)

def test_delete():
    sql = "WITH del AS (DELETE FROM users) SELECT * FROM del;"
    with pytest.raises(SQLSafetyError, match="Forbidden SQL keyword detected: DELETE"):
        validate_sql_safety(sql)

def test_comments_bypass():
    # Ensure comments don't hide bad keywords effectively
    # validate_sql_safety removes comments before checking tokens
    sql = "/* DROP TABLE */ SELECT * FROM users;"
    # This should pass because the dropped table is in a comment, and the query is actually safe.
    validate_sql_safety(sql)

def test_trick_case():
    # Case insensitivity check
    sql = "sElEcT * FrOm users; dRoP tAbLe accounts;"
    with pytest.raises(SQLSafetyError, match="Forbidden SQL keyword detected: DROP"):
        validate_sql_safety(sql)
