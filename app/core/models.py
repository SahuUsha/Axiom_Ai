from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class QueryRequest(BaseModel):
    task_description: str = Field(..., description="The user's natural language request")
    schema_context: Optional[str] = Field(None, description="Details about the available tables and overall schema")
    column_context: Optional[str] = Field(None, description="Details about the individual columns")

class ExplainRequest(QueryRequest):
    pass

class AggregateRequest(BaseModel):
    # Depending on the expected structure of aggregate context spec
    spec: Dict[str, Any]

class QueryResult(BaseModel):
    sql_generated: str
    dialect: str
    rows_returned: int
    rows_total: Optional[int] = None
    execution_time_ms: int
    columns: List[str]
    data_preview: List[Dict[str, Any]]
    summary_stats: Dict[str, Any]
    natural_language_summary: str
    has_more: bool
    result_token_estimate: int
