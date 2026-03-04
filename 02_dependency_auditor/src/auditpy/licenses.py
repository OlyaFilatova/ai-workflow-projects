"""License normalization and policy checks."""

from auditpy.models import LicenseFinding


def evaluate_licenses() -> list[LicenseFinding]:
    """Evaluate package licenses against policy."""
    raise NotImplementedError("Implemented in later stage")
