from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from app.analytics.execution_gap.definitions import DETECTORS, enabled_detectors
from app.analytics.execution_gap.models import ExecutionGapRunResult


def write_manifest(output_dir: str | Path, dataset_id: str, result: ExecutionGapRunResult) -> dict[str, object]:
    manifest = {
        "schema_version": "1.0",
        "dataset_id": dataset_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "detectors": [detector.detector_id for detector in enabled_detectors()],
        "detectors_evaluated": result.detectors_evaluated,
        "deferred_detectors": result.deferred_detectors,
        "baseline_types": {
            detector.detector_id: ("configured_expectation" if detector.enabled else "deferred")
            for detector in DETECTORS.values()
        },
        "baseline_methods": {detector.detector_id: detector.baseline_method for detector in DETECTORS.values()},
        "thresholds": {detector_id: detector.thresholds for detector_id, detector in DETECTORS.items()},
        "evidence_strength_methodology": "Evidence strength reflects supporting population size and deviation magnitude; it is not statistical confidence and does not imply statistical significance.",
        "row_counts": {"findings": len(result.findings), "evidence": len(result.evidence)},
    }
    (Path(output_dir) / "execution_gap_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest
