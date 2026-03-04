"""Warning collection utilities."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class WarningCollector:
    """Collect non-fatal warnings during parsing/translation/loading."""

    messages: list[str] = field(default_factory=list)

    def warn(self, message: str) -> None:
        self.messages.append(message)
