"""Typed intermediate representation consumed by code generation."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class FieldIR:
    """IR for one model field.

    Attributes:
        name: Original field name from the API schema.
        python_name: Safe Python attribute name.
        type_hint: Python type hint for the field.
        required: Whether the field is required.
    """

    name: str
    python_name: str
    type_hint: str
    required: bool


@dataclass(slots=True)
class SchemaIR:
    """IR for one OpenAPI schema.

    Attributes:
        name: Public schema name in generated code.
        python_name: Internal Python-safe schema name.
        kind: Schema kind (`model`, `enum`, or `alias`).
        type_hint: Type hint representing this schema.
        fields: Model fields for `model` schemas.
        enum_values: Enum literal values for `enum` schemas.
        additional_properties_type: Type for dynamic object values when allowed.
    """

    name: str
    python_name: str
    kind: str
    type_hint: str
    fields: list[FieldIR] = field(default_factory=list)
    enum_values: list[str] = field(default_factory=list)
    additional_properties_type: str | None = None


@dataclass(slots=True)
class ParameterIR:
    """IR for one operation parameter.

    Attributes:
        name: Original parameter name.
        python_name: Safe Python parameter name.
        location: Parameter location (`path`, `query`, `header`, etc.).
        required: Whether the parameter is required.
        type_hint: Python type hint for the parameter.
    """

    name: str
    python_name: str
    location: str
    required: bool
    type_hint: str


@dataclass(slots=True)
class RequestBodyIR:
    """IR for one operation request body.

    Attributes:
        required: Whether the request body is required.
        content_type: Media type supported by this request body.
        type_hint: Python type hint for the request payload.
    """

    required: bool
    content_type: str
    type_hint: str


@dataclass(slots=True)
class ResponseIR:
    """IR for one operation response variant.

    Attributes:
        status_code: HTTP status code string.
        content_type: Media type for response body when present.
        type_hint: Python type hint for response payload when present.
    """

    status_code: str
    content_type: str | None
    type_hint: str | None


@dataclass(slots=True)
class OperationIR:
    """IR for one API operation.

    Attributes:
        operation_id: Original operation identifier.
        python_name: Generated Python method name.
        method: HTTP method in uppercase.
        path: Operation path template.
        parameters: Operation parameter definitions.
        request_body: Optional request body definition.
        responses: Response definitions.
        auth_required: Whether operation requires authentication.
    """

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
    """IR for one authentication scheme.

    Attributes:
        name: Original auth scheme name.
        python_name: Safe Python identifier for the scheme.
        kind: Auth kind (`apiKey` or `bearer`).
        location: API key location when `kind` is `apiKey`.
        scheme: HTTP scheme value when applicable.
    """

    name: str
    python_name: str
    kind: str
    location: str | None = None
    scheme: str | None = None


@dataclass(slots=True)
class ApiIR:
    """Root IR consumed by the SDK renderer.

    Attributes:
        title: API title from the OpenAPI document.
        version: API version string.
        operations: Mapped operation IR nodes.
        schemas: Mapped schema IR nodes.
        auth_schemes: Mapped authentication schemes.
    """

    title: str
    version: str
    operations: list[OperationIR] = field(default_factory=list)
    schemas: list[SchemaIR] = field(default_factory=list)
    auth_schemes: list[AuthSchemeIR] = field(default_factory=list)
