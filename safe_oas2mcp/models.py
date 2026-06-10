from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


RiskLevel = Literal["low", "medium", "high", "critical"]
ToolStatus = Literal["enabled", "confirm", "disabled"]


class Parameter(BaseModel):
    name: str
    location: Literal["path", "query", "header"]
    required: bool = False
    schema_: dict[str, Any] = Field(default_factory=dict, alias="schema")
    description: str | None = None

    model_config = {"populate_by_name": True}


class Operation(BaseModel):
    method: str
    path: str
    server_urls: list[str] = Field(default_factory=list)
    operation_id: str | None = None
    summary: str | None = None
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    path_parameters: list[Parameter] = Field(default_factory=list)
    query_parameters: list[Parameter] = Field(default_factory=list)
    header_parameters: list[Parameter] = Field(default_factory=list)
    request_body_schema: dict[str, Any] | None = None
    request_body_required: bool = False


class RiskResult(BaseModel):
    risk: RiskLevel
    status: ToolStatus
    reasons: list[str] = Field(default_factory=list)


class ToolDefinition(BaseModel):
    name: str
    description: str
    input_schema: dict[str, Any]
    operation: Operation
    risk: RiskResult


class ToolMetadata(BaseModel):
    name: str
    description: str
    input_schema: dict[str, Any]
