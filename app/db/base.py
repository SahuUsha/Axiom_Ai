from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple

class DatabaseConnector(ABC):
    @abstractmethod
    async def connect(self):
        """Initialize connection pool or client"""
        pass
        
    @abstractmethod
    async def execute(self, sql: str, max_rows: int = 1000) -> Tuple[List[str], List[Dict[str, Any]], int]:
        """
        Execute SQL query and return columns, preview data, and row count.
        Returns:
            columns: list of column names
            data: list of dicts (max `max_rows` length)
            total_rows: total number of rows (if supported, otherwise length of data)
        """
        pass

    @abstractmethod
    async def explain(self, sql: str) -> str:
        """
        Generate an EXPLAIN plan for the query without fully executing it.
        """
        pass

    @abstractmethod
    async def close(self):
        """Close connections"""
        pass

    async def get_schema_context(self) -> str:
        """Fetch schema string. Override in specific connectors."""
        return ""
