class SQLSafetyError(Exception):
    """Raised when forbidden SQL keywords are detected"""
    pass

class SQLExecutionError(Exception):
    """Raised when SQL engine fails to execute a query"""
    pass

class SQLGenerationError(Exception):
    """Raised when LLM fails to generate SQL"""
    pass
