"""License normalization and policy checks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from packaging.utils import canonicalize_name

from auditpy.models import LicenseFinding

NORMALIZATION_MAP = {
    "mit": "MIT",
    "mit license": "MIT",
    "apache-2.0": "Apache-2.0",
    "apache 2.0": "Apache-2.0",
    "apache license 2.0": "Apache-2.0",
    "bsd": "BSD-3-Clause",
    "bsd license": "BSD-3-Clause",
    "bsd-3-clause": "BSD-3-Clause",
    "bsd-2-clause": "BSD-2-Clause",
    "gpl": "GPL-3.0-only",
    "gpl-3.0": "GPL-3.0-only",
    "gplv3": "GPL-3.0-only",
    "gnu general public license v3": "GPL-3.0-only",
    "lgpl": "LGPL-3.0-only",
}


@dataclass(slots=True)
class LicenseScanResult:
    """License scanning output with findings and non-fatal warnings.

    Attributes:
        findings: Per-package license evaluation findings.
        warnings: Non-fatal warnings for unknown/ambiguous licenses.
    """

    findings: list[LicenseFinding]
    warnings: list[str]


def evaluate_licenses(
    distributions: list[dict[str, Any]],
    dependency_paths: dict[str, list[list[str]]],
    *,
    policy: str = "no-gpl",
) -> LicenseScanResult:
    """Normalize package licenses and evaluate them against the active policy.

    Args:
        distributions: Installed package metadata collected from resolution.
        dependency_paths: Dependency paths keyed by normalized package name.
        policy: Active license policy name.
    """
    warnings: list[str] = []
    findings: list[LicenseFinding] = []

    for dist in sorted(distributions, key=lambda item: (str(item.get("name", "")).lower(), str(item.get("version", "")))):
        name = str(dist.get("name", ""))
        version = str(dist.get("version", ""))
        declared = dist.get("license")
        classifiers = list(dist.get("classifiers", []))

        normalized_list = _normalize_candidates(_license_candidates(declared, classifiers))
        normalized_expr = " OR ".join(sorted(normalized_list)) if normalized_list else None

        if not normalized_list:
            warnings.append(f"Unknown or ambiguous license for {name}=={version}")
            policy_result = "warn"
        else:
            policy_result = _evaluate_policy(policy, normalized_list)

        norm_name = canonicalize_name(name)
        finding = LicenseFinding(
            package=name,
            version=version,
            declared=str(declared) if declared is not None else None,
            normalized_spdx=normalized_expr,
            policy_name=policy,
            policy_result=policy_result,
            paths=dependency_paths.get(norm_name, []),
        )
        findings.append(finding)

    return LicenseScanResult(findings=findings, warnings=warnings)


def _license_candidates(declared: Any, classifiers: list[Any]) -> list[str]:
    """Collect raw license candidate strings from metadata fields.

    Args:
        declared: Raw license field value from package metadata.
        classifiers: Classifier entries from package metadata.
    """
    candidates: list[str] = []
    if isinstance(declared, str) and declared.strip():
        candidates.extend(_split_multi_license_string(declared.strip()))

    for classifier in classifiers:
        if not isinstance(classifier, str):
            continue
        if "License ::" not in classifier:
            continue
        segment = classifier.split("::")[-1].strip()
        if segment:
            candidates.append(segment)

    return candidates


def _split_multi_license_string(value: str) -> list[str]:
    """Split a multi-license string into individual candidate expressions.

    Args:
        value: Raw license expression string.
    """
    lowered = value.lower().replace("|", " or ").replace("/", " or ")
    parts = [part.strip() for part in lowered.split(" or ") if part.strip()]
    if len(parts) > 1:
        return parts
    return [value]


def _normalize_candidates(candidates: list[str]) -> set[str]:
    """Map raw license candidates to normalized SPDX identifiers.

    Args:
        candidates: Raw candidate license strings.
    """
    normalized: set[str] = set()
    for raw in candidates:
        key = raw.strip().lower()
        mapped = NORMALIZATION_MAP.get(key)
        if mapped:
            normalized.add(mapped)
    return normalized


def _evaluate_policy(policy: str, normalized_spdx: set[str]) -> str:
    """Evaluate normalized identifiers and return allow/warn/violation outcome.

    Args:
        policy: Active license policy name.
        normalized_spdx: Normalized SPDX identifiers for a package.
    """
    if policy != "no-gpl":
        return "warn"

    if any("gpl" in identifier.lower() for identifier in normalized_spdx):
        return "violation"
    return "allow"
