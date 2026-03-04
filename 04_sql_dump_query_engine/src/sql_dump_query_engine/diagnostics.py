"""Warning collection utilities."""

from __future__ import annotations

from dataclasses import dataclass, field

from .models import WarningCode, WarningEvent


@dataclass(slots=True)
class WarningCollector:
    """Collect non-fatal warnings during parsing/translation/loading."""

    events: list[WarningEvent] = field(default_factory=list)

    def warn(self, code: WarningCode, message: str, line: int | None = None) -> None:
        self.events.append(WarningEvent(code=code, message=message, line=line))
