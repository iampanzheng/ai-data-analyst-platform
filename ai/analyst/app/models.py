from typing import Any

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    sql: str = Field(min_length=1)


class QueryResponse(BaseModel):
    columns: list[str]
    rows: list[list[Any]]
    row_count: int
    trace_id: str
    execution_ms: float


class ErrorDetail(BaseModel):
    code: str
    message: str
    trace_id: str


class ErrorResponse(BaseModel):
    detail: ErrorDetail


class ColumnMetadata(BaseModel):
    name: str
    business_name: str
    description: str
    data_type: str
    semantic_type: str
    nullable: bool
    queryable: bool


class TableMetadata(BaseModel):
    table_name: str
    business_name: str
    description: str
    source: str
    update_frequency: str | None
    columns: list[ColumnMetadata]


class SchemaResponse(BaseModel):
    schema_name: str
    tables: list[TableMetadata]
