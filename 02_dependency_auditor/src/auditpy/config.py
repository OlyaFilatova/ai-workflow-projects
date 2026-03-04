"""Runtime configuration and validation rules."""

from __future__ import annotations

from dataclasses import dataclass


VALID_POLICIES = {"no-gpl"}
VALID_FAIL_THRESHOLDS = {"high", "critical"}


@dataclass(slots=True, frozen=True)
class ScanConfig:
    policy: str = "no-gpl"
    fail_on: str = "high"
    cache_ttl_hours: int = 24
    verbose: bool = False

    @classmethod
    def create(
        cls,
        *,
        policy: str = "no-gpl",
        fail_on: str = "high",
        cache_ttl_hours: int = 24,
        verbose: bool = False,
    ) -> "ScanConfig":
        if policy not in VALID_POLICIES:
            supported = ", ".join(sorted(VALID_POLICIES))
            raise ValueError(f"Unsupported policy '{policy}'. Supported policies: {supported}")
        if fail_on not in VALID_FAIL_THRESHOLDS:
            supported = ", ".join(sorted(VALID_FAIL_THRESHOLDS))
            raise ValueError(f"Unsupported fail threshold '{fail_on}'. Use one of: {supported}")
        if cache_ttl_hours <= 0:
            raise ValueError("Cache TTL must be a positive integer number of hours")

        return cls(
            policy=policy,
            fail_on=fail_on,
            cache_ttl_hours=cache_ttl_hours,
            verbose=verbose,
        )
