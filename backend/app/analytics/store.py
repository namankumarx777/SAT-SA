"""Typed, single-path readers for detector phase outputs.

Every detector phase (5-8) writes the same ``findings.parquet`` /
``evidence.parquet`` pair. ``PhaseStore`` centralizes the reading of those
files so API routers and tools do not re-implement the same probe/read/filter
logic with subtly different behaviour.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import polars as pl


class PhaseNotFoundError(ValueError):
    """Raised when a phase output is missing or does not contain an item."""


@dataclass(frozen=True)
class FindingDetail:
    finding: dict[str, Any]
    evidence: list[dict[str, Any]]


@dataclass(frozen=True)
class PhaseStore:
    phase: str
    output_dir: Path

    def findings_path(self) -> Path:
        return self.output_dir / "findings.parquet"

    def evidence_path(self) -> Path:
        return self.output_dir / "evidence.parquet"

    def read_findings(self) -> list[dict[str, Any]]:
        """Return all findings as rows, or an empty list when not produced."""
        path = self.findings_path()
        if not path.is_file():
            return []
        return pl.read_parquet(path).to_dicts()

    def read_finding_count(self) -> int:
        path = self.findings_path()
        if not path.is_file():
            return 0
        return int(pl.read_parquet(path).height)

    def get_finding(self, finding_id: str) -> FindingDetail:
        """Look up one finding plus its linked evidence.

        Raises ``PhaseNotFoundError`` when the phase output is missing or the
        finding id is unknown.
        """
        path = self.findings_path()
        if not path.is_file():
            raise PhaseNotFoundError(f"No {self.phase} findings dataset at {path}")
        rows = pl.read_parquet(path).filter(pl.col("id") == finding_id).to_dicts()
        if not rows:
            raise PhaseNotFoundError("Finding not found")
        evidence: list[dict[str, Any]] = []
        evidence_path = self.evidence_path()
        if evidence_path.is_file():
            evidence = pl.read_parquet(evidence_path).filter(pl.col("finding_id") == finding_id).to_dicts()
        return FindingDetail(finding=rows[0], evidence=evidence)