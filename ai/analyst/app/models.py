from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    sql: str = Field(min_length=1)


class QueryResponse(BaseModel):
    columns: list[str]
    rows: list[list[object]]
    row_count: int
    trace_id: str
    execution_ms: int
