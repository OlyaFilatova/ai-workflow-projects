"""Warning collection utilities."""

from __future__ import annotations

from dataclasses import dataclass, field

from .models import WarningEvent


@dataclass(slots=True)
class WarningCollector:
    """Collect non-fatal warnings during parsing/translation/loading."""

    events: list[WarningEvent] = field(default_factory=list)
    """Accumulated warning events."""
