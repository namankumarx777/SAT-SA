"""Registered location of every analysis phase output within the processed data root.

This module is the single source of truth for resolving each phase's canonical
output directory (or feature file) inside a processed dataset. Consumers that
need Phase 4-9 outputs should use these resolvers instead of probing arbitrary
directory names, so a rename or a new canonical location only needs to change
here.

Resolution rules:
- ``preferred`` (an explicit user-supplied path) always wins and is used as-is.
- Otherwise the phase's ``dir_candidates`` are checked in order, then finally
  the root itself if it directly contains the phase outputs.
- A phase that cannot be resolved returns ``None`` so callers can record a
  "NOT_FOUND" outcome without failing the whole run.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PhaseDataset:
    phase: str
    label: str
    dir_candidates: tuple[str, ...] = ()
    marker_file: str = "findings.parquet"
    feature_file: str | None = None
    feature_dir_candidates: tuple[str, ...] = ()

    @property
    def is_feature_dataset(self) -> bool:
        return self.feature_file is not None


PHASE_DATASETS: dict[str, PhaseDataset] = {
    "phase4": PhaseDataset(
        phase="phase4",
        label="Phase 4 - Operational Features",
        feature_file="entity_features.parquet",
        feature_dir_candidates=("phase4-final", "phase4-features", "phase4-check", ""),
    ),
    "phase5": PhaseDataset(
        phase="phase5",
        label="Phase 5 - Deterministic Supervisory Rules",
        dir_candidates=("phase5-final", "phase5-findings", "phase5-final-a"),
    ),
    "phase6": PhaseDataset(
        phase="phase6",
        label="Phase 6 - Execution Gaps",
        dir_candidates=("execution_gap-final", "execution_gap"),
    ),
    "phase7": PhaseDataset(
        phase="phase7",
        label="Phase 7 - Negative Space",
        dir_candidates=("negative_space-final", "negative_space"),
    ),
    "phase8": PhaseDataset(
        phase="phase8",
        label="Phase 8 - Peer Benchmarking & Anomaly",
        dir_candidates=("peer_anomaly-final", "peer_anomaly"),
    ),
    "phase9": PhaseDataset(
        phase="phase9",
        label="Phase 9 - Supervisory Risk",
        dir_candidates=("supervisory_risk-final", "supervisory_risk"),
        marker_file="entity_risk.parquet",
    ),
}


def get_phase_dataset(phase: str) -> PhaseDataset:
    try:
        return PHASE_DATASETS[phase]
    except KeyError:
        raise ValueError(f"Unknown phase dataset: {phase!r}. Known: {sorted(PHASE_DATASETS)}") from None


def resolve_phase_dir(root: str | Path, phase: str, preferred: str | Path | None = None) -> Path | None:
    """Resolve the directory holding a phase's findings/evidence outputs.

    Returns ``None`` when the phase outputs cannot be located rather than
    raising, so callers can record availability per phase.
    """
    root = Path(root)
    dataset = get_phase_dataset(phase)
    if preferred is not None:
        candidate = Path(preferred)
        return candidate if candidate.is_dir() else None
    for name in dataset.dir_candidates:
        candidate = root / name
        if candidate.is_dir() and (candidate / dataset.marker_file).is_file():
            return candidate
    if (root / dataset.marker_file).is_file():
        return root
    return None


def resolve_feature_path(root: str | Path, phase: str, preferred: str | Path | None = None) -> Path | None:
    """Resolve a phase feature file (e.g. Phase 4 ``entity_features.parquet``)."""
    root = Path(root)
    dataset = get_phase_dataset(phase)
    if not dataset.is_feature_dataset:
        raise ValueError(f"Phase dataset {phase!r} has no feature file")
    if preferred is not None:
        candidate = Path(preferred)
        file_candidate = candidate if candidate.is_file() else candidate / (dataset.feature_file or "")
        return file_candidate if file_candidate.is_file() else None
    for name in dataset.feature_dir_candidates:
        candidate = root / name / (dataset.feature_file or "") if name else root / (dataset.feature_file or "")
        if candidate.is_file():
            return candidate
    return None