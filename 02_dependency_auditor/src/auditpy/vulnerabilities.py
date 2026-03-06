"""Vulnerability scanning functionality using OSV only."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from packaging.utils import canonicalize_name

from auditpy.models import PackageNode, Severity, VulnerabilityFinding

OSV_BATCH_URL = "https://api.osv.dev/v1/querybatch"


@dataclass(slots=True)
class VulnerabilityScanResult:
    findings: list[VulnerabilityFinding]
    warnings: list[str]


def scan_vulnerabilities(
    nodes: list[PackageNode],
    dependency_paths: dict[str, list[list[str]]],
    *,
    cache_ttl_hours: int = 24,
    cache_dir: str = ".auditpy_cache",
    timeout_seconds: int = 20,
) -> VulnerabilityScanResult:
    cache_path = Path(cache_dir) / "osv_cache.json"
    cache_data = _load_cache(cache_path)

    now = datetime.now(UTC)
    ttl = timedelta(hours=cache_ttl_hours)

    vulnerability_results_by_key, queries, query_keys = _prepare_cached_and_pending_queries(
        nodes,
        cache_data,
        now=now,
        ttl=ttl,
    )

    warnings: list[str] = []
    if queries:
        try:
            fetched = _query_osv_batch(queries, timeout_seconds=timeout_seconds)
            _merge_fetched_results_into_cache(
                fetched,
                query_keys,
                vulnerability_results_by_key,
                cache_data,
                fetched_at_iso=now.isoformat(),
            )
            _save_cache(cache_path, cache_data)
        except (TimeoutError, URLError, HTTPError, OSError, json.JSONDecodeError) as exc:
            warnings.append(f"OSV query failed; using cached data where available: {exc}")
            for key in query_keys:
                vulnerability_results_by_key[key] = cache_data.get(key, {}).get("vulns", [])

    findings = _build_findings(nodes, dependency_paths, vulnerability_results_by_key)
    findings.sort(key=lambda item: (item.severity.value, item.package.lower(), item.vuln_id))

    return VulnerabilityScanResult(findings=findings, warnings=warnings)


def _prepare_cached_and_pending_queries(
    nodes: list[PackageNode],
    cache_data: dict[str, dict[str, Any]],
    *,
    now: datetime,
    ttl: timedelta,
) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]], list[str]]:
    vulnerability_results_by_key: dict[str, list[dict[str, Any]]] = {}
    queries: list[dict[str, Any]] = []
    query_keys: list[str] = []

    for node in sorted(nodes, key=lambda item: (item.name.lower(), item.version)):
        key = _cache_key(node.name, node.version)
        cached_entry = cache_data.get(key)
        if cached_entry and _is_cache_fresh(cached_entry.get("fetched_at"), now, ttl):
            vulnerability_results_by_key[key] = cached_entry.get("vulns", [])
            continue

        queries.append(
            {
                "package": {"name": node.name, "ecosystem": "PyPI"},
                "version": node.version,
            }
        )
        query_keys.append(key)

    return vulnerability_results_by_key, queries, query_keys


def _merge_fetched_results_into_cache(
    fetched: list[dict[str, Any]],
    query_keys: list[str],
    vulnerability_results_by_key: dict[str, list[dict[str, Any]]],
    cache_data: dict[str, dict[str, Any]],
    *,
    fetched_at_iso: str,
) -> None:
    for index, key in enumerate(query_keys):
        vulnerabilities = fetched[index].get("vulns", [])
        vulnerability_results_by_key[key] = vulnerabilities
        cache_data[key] = {
            "fetched_at": fetched_at_iso,
            "vulns": vulnerabilities,
        }


def _query_osv_batch(queries: list[dict[str, Any]], *, timeout_seconds: int) -> list[dict[str, Any]]:
    payload = json.dumps({"queries": queries}).encode("utf-8")
    request = Request(OSV_BATCH_URL, data=payload, headers={"Content-Type": "application/json"}, method="POST")

    with urlopen(request, timeout=timeout_seconds) as response:
        body = response.read().decode("utf-8")

    parsed = json.loads(body)
    results = parsed.get("results")
    if not isinstance(results, list):
        raise json.JSONDecodeError("Missing 'results' in OSV response", body, 0)
    return results


def _build_findings(
    nodes: list[PackageNode],
    dependency_paths: dict[str, list[list[str]]],
    cache_results: dict[str, list[dict[str, Any]]],
) -> list[VulnerabilityFinding]:
    findings: list[VulnerabilityFinding] = []
    nodes_by_key = {_cache_key(node.name, node.version): node for node in nodes}

    for key, vulns in cache_results.items():
        node = nodes_by_key.get(key)
        if not node:
            continue

        normalized_name = canonicalize_name(node.name)
        paths = dependency_paths.get(normalized_name, [])

        for vuln in vulns:
            vuln_id = str(vuln.get("id", "UNKNOWN"))
            summary = vuln.get("summary")
            severity = _normalize_severity(vuln)
            findings.append(
                VulnerabilityFinding(
                    package=node.name,
                    version=node.version,
                    vuln_id=vuln_id,
                    severity=severity,
                    summary=str(summary) if summary is not None else None,
                    paths=paths,
                )
            )

    return findings


def _normalize_severity(vuln: dict[str, Any]) -> Severity:
    severity_entries = vuln.get("severity") or []
    numeric_score = None

    for entry in severity_entries:
        score_value = entry.get("score") if isinstance(entry, dict) else None
        if isinstance(score_value, str) and score_value.startswith("CVSS"):
            parts = score_value.split("/")
            if parts:
                maybe_score = parts[-1]
                try:
                    numeric_score = float(maybe_score)
                except ValueError:
                    continue

    if numeric_score is None:
        # Deterministic fallback for records without machine-readable score.
        return Severity.MEDIUM
    if numeric_score >= 9.0:
        return Severity.CRITICAL
    if numeric_score >= 7.0:
        return Severity.HIGH
    if numeric_score >= 4.0:
        return Severity.MEDIUM
    return Severity.LOW


def _cache_key(name: str, version: str) -> str:
    return f"{canonicalize_name(name)}=={version}"


def _is_cache_fresh(fetched_at: str | None, now: datetime, ttl: timedelta) -> bool:
    if not fetched_at:
        return False
    try:
        ts = datetime.fromisoformat(fetched_at)
    except ValueError:
        return False

    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=UTC)
    return now - ts <= ttl


def _load_cache(cache_path: Path) -> dict[str, dict[str, Any]]:
    if not cache_path.exists():
        return {}
    try:
        raw = json.loads(cache_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(raw, dict):
        return {}
    return raw


def _save_cache(cache_path: Path, cache_data: dict[str, dict[str, Any]]) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    stable = {key: cache_data[key] for key in sorted(cache_data)}
    cache_path.write_text(json.dumps(stable, indent=2, sort_keys=True), encoding="utf-8")
