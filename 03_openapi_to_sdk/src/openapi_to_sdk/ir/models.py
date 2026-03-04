"""Core intermediate-representation models for generation."""

from pydantic import BaseModel, Field


class OperationIR(BaseModel):
    """Represents a single API operation in the internal model."""

    operation_id: str = Field(min_length=1)
    method: str = Field(min_length=1)
    path: str = Field(min_length=1)


class ApiIR(BaseModel):
    """Top-level IR object consumed by code generators."""

    title: str = Field(min_length=1)
    version: str = Field(min_length=1)
    operations: list[OperationIR] = Field(default_factory=list)
