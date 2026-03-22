import re
from app.core.exceptions import SQLSafetyError

FORBIDDEN_SQL_KEYWORDS = [
    "INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER",
    "TRUNCATE", "REPLACE", "MERGE", "EXEC", "EXECUTE",
    "GRANT", "REVOKE", "SET", "BEGIN", "COMMIT", "ROLLBACK"
]

def validate_sql_safety(sql: str) -> None:
    """
    Validates SQL string to ensure it contains no DML or DDL statements.
    Raises SQLSafetyError if a forbidden keyword is found.
    """
    # Remove single line and multi-line comments to avoid false positives/negatives
    sql_no_comments = re.sub(r'--.*$', '', sql, flags=re.MULTILINE)
    sql_no_comments = re.sub(r'/\\*.*?\\*/', '', sql_no_comments, flags=re.DOTALL)
    
    # Tokenize the SQL string
    # We use a simple word boundary regex to find tokens
    tokens = re.findall(r'\b[a-zA-Z_]+\b', sql_no_comments.upper())
    
    for token in tokens:
        if token in FORBIDDEN_SQL_KEYWORDS:
            raise SQLSafetyError(f"Forbidden SQL keyword detected: {token}")
            
    # As an extra safety net, ensure the query starts with SELECT or WITH
    first_token = tokens[0] if tokens else ""
    if first_token not in ["SELECT", "WITH", "EXPLAIN"]:
        raise SQLSafetyError(f"SQL query must start with SELECT or WITH. Found: {repr(first_token)}. Raw SQL was: {repr(sql)}")
