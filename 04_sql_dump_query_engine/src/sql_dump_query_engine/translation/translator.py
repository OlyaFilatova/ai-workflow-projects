"""Statement translation for supported dump formats."""

from __future__ import annotations

import re

from ..models import ParseEvent, TranslationArtifact, WarningEvent
from .mapper import normalize_type_tokens

_UNSUPPORTED_PREFIXES = (
    "CREATE VIEW",
    "CREATE TRIGGER",
    "CREATE FUNCTION",
    "CREATE PROCEDURE",
)

_SKIP_PREFIXES = (
    "LOCK TABLES",
    "UNLOCK TABLES",
    "DELIMITER",
    "SET ",
)


def translate_statement(event: ParseEvent) -> TranslationArtifact:
    """Translate source SQL into DuckDB-compatible SQL."""

    original = event.statement
    sql = original.text.strip()
    warnings: list[WarningEvent] = []
    if not sql:
        warnings.append(
            WarningEvent(code="empty_statement", message="Skipped empty statement", line=original.line)
        )
        return TranslationArtifact(original=original, sql="", skipped=True, warnings=warnings)

    upper = sql.upper()
    if upper.startswith(_UNSUPPORTED_PREFIXES):
        warnings.append(
            WarningEvent(
                code="skipped_construct",
                message=f"Skipped unsupported statement: {upper.split()[0]} {upper.split()[1]}",
                line=original.line,
            )
        )
        return TranslationArtifact(original=original, sql="", skipped=True, warnings=warnings)

    if upper.startswith(_SKIP_PREFIXES) or upper.startswith("/*!"):
        warnings.append(
            WarningEvent(
                code="skipped_construct",
                message="Skipped dump directive not required for data loading",
                line=original.line,
            )
        )
        return TranslationArtifact(original=original, sql="", skipped=True, warnings=warnings)

    translated = _translate_mysql(sql) if original.dialect == "mysql" else sql
    translated = normalize_type_tokens(translated)

    return TranslationArtifact(original=original, sql=translated, skipped=False, warnings=warnings)


def _translate_mysql(sql: str) -> str:
    translated = sql.replace("`", '"')

    # Remove MySQL table options that DuckDB does not support.
    translated = re.sub(
        r"\)\s*ENGINE\s*=\s*[^;]+;",
        ");",
        translated,
        flags=re.IGNORECASE | re.DOTALL,
    )

    translated = re.sub(r"\bAUTO_INCREMENT\s*=\s*\d+\b", "", translated, flags=re.IGNORECASE)
    translated = re.sub(r"\bAUTO_INCREMENT\b", "", translated, flags=re.IGNORECASE)
    translated = re.sub(r"\bUNSIGNED\b", "", translated, flags=re.IGNORECASE)
    translated = re.sub(r"\bCHARACTER\s+SET\s+\w+\b", "", translated, flags=re.IGNORECASE)
    translated = re.sub(r"\bCOLLATE\s+\w+\b", "", translated, flags=re.IGNORECASE)
    translated = re.sub(r"\s+", " ", translated)
    translated = translated.replace(" ,", ",")

    return translated.strip()
