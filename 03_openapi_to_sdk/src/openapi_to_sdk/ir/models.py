"""Typed intermediate representation consumed by code generation."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class FieldIR:
    name: str
    python_name: str
    type_hint: str
    required: bool


@dataclass(slots=True)
class SchemaIR:
    name: str
    python_name: str
    kind: str
    type_hint: str
    fields: list[FieldIR] = field(default_factory=list)
    enum_values: list[str] = field(default_factory=list)
    additional_properties_type: str | None = None


@dataclass(slots=True)
class ParameterIR:
    name: str
    python_name: str
    location: str
    required: bool
    type_hint: str


@dataclass(slots=True)
class RequestBodyIR:
    required: bool
    content_type: str
    type_hint: str


@dataclass(slots=True)
class ResponseIR:
    status_code: str
    content_type: str | None
    type_hint: str | None


@dataclass(slots=True)
class OperationIR:
    operation_id: str
    python_name: str
    method: str
    path: str
    parameters: list[ParameterIR] = field(default_factory=list)
    request_body: RequestBodyIR | None = None
    responses: list[ResponseIR] = field(default_factory=list)
    auth_required: bool = False


@dataclass(slots=True)
class AuthSchemeIR:
    name: str
    python_name: str
    kind: str
    location: str | None = None
    scheme: str | None = None


@dataclass(slots=True)
class ApiIR:
    title: str
    version: str
    operations: list[OperationIR] = field(default_factory=list)
    schemas: list[SchemaIR] = field(default_factory=list)
    auth_schemes: list[AuthSchemeIR] = field(default_factory=list)
