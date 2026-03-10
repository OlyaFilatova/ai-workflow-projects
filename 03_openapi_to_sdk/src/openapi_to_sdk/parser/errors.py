"""Parser-specific error types."""


class OpenAPILoadError(ValueError):
    """Raised when an OpenAPI document cannot be loaded or resolved."""
