"""Template rendering orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from openapi_to_sdk.ir.models import ApiIR, FieldIR, OperationIR, SchemaIR


@dataclass(slots=True)
class _TemplateField:
    """Template-ready representation of one model field.

    Attributes:
        name: Python field name used in generated code.
        type_hint: Python type hint string for the field.
        required: Whether the field is required.
        alias: Optional original API field name when different from `name`.
    """

    name: str
    type_hint: str
    required: bool
    alias: str | None


@dataclass(slots=True)
class _TemplateSchema:
    """Template-ready representation of one schema.

    Attributes:
        name: Public schema class/type name.
        kind: Schema kind (`model`, `enum`, or `alias`).
        type_hint: Type hint expression used for aliases/enums.
        fields: Normalized model fields for `model` schemas.
    """

    name: str
    kind: str
    type_hint: str
    fields: list[_TemplateField]


@dataclass(slots=True)
class _TemplateOperation:
    """Template-ready representation of one API operation.

    Attributes:
        method_name: Generated Python method name.
        http_method: HTTP method in uppercase.
        path: Request path template.
        return_type: Return type hint for the generated method.
        response_model: Optional response model symbol used for parsing.
        error_model: Optional error model symbol used for parsing.
    """

    method_name: str
    http_method: str
    path: str
    return_type: str
    response_model: str | None
    error_model: str | None


def render_sdk(ir: ApiIR, output_dir: Path) -> None:
    """Render SDK package files from IR using Jinja2 templates."""
    output_dir.mkdir(parents=True, exist_ok=True)
    package_name = _package_name(ir.title)
    package_dir = output_dir / package_name
    package_dir.mkdir(parents=True, exist_ok=True)

    env = _build_environment()

    template_schemas = [_schema_to_template(schema) for schema in sorted(ir.schemas, key=lambda item: item.name)]
    exports = [schema.name for schema in template_schemas]
    typing_imports, stdlib_imports = _collect_type_imports(template_schemas)
    schema_names = {schema.name for schema in template_schemas}
    operations = [_operation_to_template(item, schema_names) for item in ir.operations]

    models_source = env.get_template("models.py.j2").render(
        schemas=template_schemas,
        typing_imports=typing_imports,
        stdlib_imports=stdlib_imports,
    )
    client_source = env.get_template("client.py.j2").render(operations=operations)
    init_source = env.get_template("package_init.py.j2").render(exports=exports)

    (package_dir / "models.py").write_text(models_source, encoding="utf-8")
    (package_dir / "client.py").write_text(client_source, encoding="utf-8")
    (package_dir / "__init__.py").write_text(init_source, encoding="utf-8")
    (package_dir / "py.typed").write_text("", encoding="utf-8")


def _build_environment() -> Environment:
    """Build the Jinja2 rendering environment for SDK templates."""
    template_dir = Path(__file__).resolve().parents[1] / "templates"
    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
        undefined=StrictUndefined,
    )
    env.globals["render_field_declaration"] = _render_field_declaration
    return env


def _schema_to_template(schema: SchemaIR) -> _TemplateSchema:
    """Convert one schema IR node to a template-facing schema object.

    Args:
        schema: Source schema IR model.
    """
    fields = [_field_to_template(field) for field in schema.fields]
    return _TemplateSchema(
        name=schema.name,
        kind=schema.kind,
        type_hint=schema.type_hint,
        fields=fields,
    )


def _field_to_template(field: FieldIR) -> _TemplateField:
    """Convert one field IR node to a template-facing field object.

    Args:
        field: Source field IR model.
    """
    alias = field.name if field.python_name != field.name else None
    return _TemplateField(
        name=field.python_name,
        type_hint=field.type_hint,
        required=field.required,
        alias=alias,
    )


def _render_field_declaration(field: _TemplateField) -> str:
    """Render a single model field declaration line for templates.

    Args:
        field: Template-facing field model.
    """
    declaration = f"    {field.name}: {field.type_hint}"
    if field.alias and field.required:
        declaration += f' = Field(alias="{field.alias}")'
    elif field.alias and not field.required:
        declaration += f' = Field(default=None, alias="{field.alias}")'
    elif not field.required:
        declaration += " = None"
    return declaration + "\n"


def _operation_to_template(operation: OperationIR, schema_names: set[str]) -> _TemplateOperation:
    """Convert one operation IR node to a template-facing operation object.

    Args:
        operation: Source operation IR model.
        schema_names: Set of generated schema names usable as model symbols.
    """
    success_response = next(
        (
            response
            for response in operation.responses
            if response.status_code.startswith("2") and response.type_hint is not None
        ),
        None,
    )
    error_response = next(
        (
            response
            for response in operation.responses
            if response.status_code.startswith(("4", "5")) and response.type_hint is not None
        ),
        None,
    )

    return_type = (
        success_response.type_hint
        if success_response is not None and success_response.type_hint is not None
        else "None"
    )
    response_model = return_type if return_type in schema_names else None

    error_type = error_response.type_hint if error_response is not None else None
    error_model = error_type if error_type in schema_names else None

    return _TemplateOperation(
        method_name=operation.python_name,
        http_method=operation.method,
        path=operation.path,
        return_type=return_type,
        response_model=response_model,
        error_model=error_model,
    )


def _collect_type_imports(schemas: list[_TemplateSchema]) -> tuple[list[str], list[str]]:
    """Collect typing and stdlib imports required by rendered model hints.

    Args:
        schemas: Template-facing schema list.
    """
    hints: list[str] = []
    for schema in schemas:
        hints.append(schema.type_hint)
        hints.extend(field.type_hint for field in schema.fields)

    typing_imports: list[str] = []
    stdlib_imports: list[str] = []

    if any("Any" in hint for hint in hints):
        typing_imports.append("Any")
    if any("Literal[" in hint for hint in hints):
        typing_imports.append("Literal")
    if any("datetime" in hint for hint in hints):
        stdlib_imports.append("datetime")
    if any("date" in hint for hint in hints):
        stdlib_imports.append("date")
    if any("UUID" in hint for hint in hints):
        stdlib_imports.append("UUID")

    return sorted(set(typing_imports)), sorted(set(stdlib_imports))


def _package_name(title: str) -> str:
    """Normalize an API title into a valid Python package name.

    Args:
        title: Raw API title from the OpenAPI document.
    """
    cleaned = "".join(ch if ch.isalnum() else "_" for ch in title.lower()).strip("_")
    collapsed = "_".join(segment for segment in cleaned.split("_") if segment)
    return collapsed or "generated_sdk"
