from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from app.analytics.detectors.output import canonical_frame
from app.analytics.supervisory_risk.aggregation import aggregate_entity_risk
from app.analytics.supervisory_risk.config import DEFERRED_DETECTORS, DIMENSION_WEIGHTS
from app.analytics.supervisory_risk.correlation import (
    CorrelatedGroupSignal,
    build_risk_contributions,
    evaluate_correlation_groups,
)
from app.analytics.supervisory_risk.dimensions import calculate_dimension_scores
from app.analytics.supervisory_risk.inputs import (
    StandardizedFinding,
    UpstreamBundle,
    load_upstream_bundle,
)
from app.analytics.supervisory_risk.manifest import write_manifest
from app.analytics.supervisory_risk.models import (
    EntityRisk,
    RiskContribution,
    ReviewQueueItem,
    SupervisoryRiskRunResult,
)
from app.analytics.supervisory_risk.normalization import (
    NormalizedSignal,
    normalize_finding_signal,
)
from app.analytics.supervisory_risk.priority import build_review_queue

DEFAULT_OUTPUT = Path(__file__).resolve().parents[4] / "data" / "processed" / "supervisory_risk"


def evaluate_supervisory_risk(bundle: UpstreamBundle) -> SupervisoryRiskRunResult:
    """Evaluate and aggregate all upstream findings into entity risks, contributions, and review queue."""
    findings_by_entity: dict[str, list[StandardizedFinding]] = {eid: [] for eid in bundle.entities}
    for f in bundle.findings:
        findings_by_entity.setdefault(f.entity_id, []).append(f)

    entity_risks: list[EntityRisk] = []
    all_contributions: list[RiskContribution] = []
    group_signals_by_entity: dict[str, list[CorrelatedGroupSignal]] = {}
    consumed_detectors: set[str] = set()

    for entity_id in sorted(bundle.entities.keys()):
        entity_meta = bundle.entities[entity_id]
        entity_findings = findings_by_entity.get(entity_id, [])

        # 1. Group findings by detector ID to compute normalized signals
        findings_by_det: dict[str, list[StandardizedFinding]] = {}
        for f in entity_findings:
            findings_by_det.setdefault(f.rule_id, []).append(f)
            consumed_detectors.add(f.rule_id)

        normalized_signals: list[NormalizedSignal] = []
        for det_id, det_findings in findings_by_det.items():
            representative_finding = det_findings[0]
            sig = normalize_finding_signal(representative_finding, entity_meta, det_findings)
            normalized_signals.append(sig)

        # 2. Correlate overlapping signals into anti-double-counting correlation groups
        group_signals = evaluate_correlation_groups(entity_id, normalized_signals)
        group_signals_by_entity[entity_id] = group_signals

        # 3. Build auditable risk contributions
        contributions = build_risk_contributions(entity_id, group_signals, DIMENSION_WEIGHTS)
        all_contributions.extend(contributions)

        # 4. Calculate Level 1 dimension scores
        dimension_scores, unassessable_dimensions = calculate_dimension_scores(entity_id, group_signals, entity_meta)

        # 5. Calculate Level 2 overall risk and metadata
        risk = aggregate_entity_risk(
            entity_id, dimension_scores, unassessable_dimensions, group_signals, entity_findings, entity_meta
        )
        entity_risks.append(risk)

    # 6. Generate separate supervisory manual-review prioritisation queue
    review_queue = build_review_queue(
        entity_risks=entity_risks,
        group_signals_by_entity=group_signals_by_entity,
        findings_by_entity=findings_by_entity,
        evidence_by_finding=bundle.evidence_by_finding,
    )

    # Deterministic sorting
    sorted_entity_risks = sorted(entity_risks, key=lambda r: r.entity_id)
    sorted_contributions = sorted(all_contributions, key=lambda c: (c.entity_id, c.dimension, c.id))
    sorted_review_queue = sorted(review_queue, key=lambda q: q.rank)

    return SupervisoryRiskRunResult(
        entity_risks=sorted_entity_risks,
        risk_contributions=sorted_contributions,
        review_queue=sorted_review_queue,
        entities_evaluated=sorted(bundle.entities.keys()),
        detectors_consumed=sorted(consumed_detectors),
        detectors_excluded=DEFERRED_DETECTORS,
    )


def write_outputs(
    result: SupervisoryRiskRunResult,
    bundle: UpstreamBundle,
    output_dir: str | Path,
    dataset_id: str,
) -> None:
    """Write Parquet datasets and auditable JSON manifest deterministically and atomically."""
    import tempfile
    destination = Path(output_dir)
    destination.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(dir=destination.parent, prefix=".tmp-risk-") as temporary:
        temp_path = Path(temporary)
        canonical_frame(result.entity_risks).write_parquet(temp_path / "entity_risk.parquet")
        canonical_frame(result.risk_contributions).write_parquet(temp_path / "risk_contributions.parquet")
        canonical_frame(result.review_queue).write_parquet(temp_path / "review_queue.parquet")
        write_manifest(temp_path, dataset_id, bundle, result)
        
        temp_path.replace(destination)


def run_supervisory_risk(
    input_dir: str | Path,
    output_dir: str | Path = DEFAULT_OUTPUT,
    dataset_id: str | None = None,
    phase4_dir: str | Path | None = None,
    phase5_dir: str | Path | None = None,
    phase6_dir: str | Path | None = None,
    phase7_dir: str | Path | None = None,
    phase8_dir: str | Path | None = None,
) -> SupervisoryRiskRunResult:
    """Main pipeline execution for Phase 9 Supervisory Risk Engine."""
    bundle = load_upstream_bundle(
        input_dir,
        phase4_dir=phase4_dir,
        phase5_dir=phase5_dir,
        phase6_dir=phase6_dir,
        phase7_dir=phase7_dir,
        phase8_dir=phase8_dir,
    )
    result = evaluate_supervisory_risk(bundle)
    write_outputs(result, bundle, output_dir, dataset_id or Path(input_dir).name)
    return result


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run SENTRA Phase 9 Supervisory Risk Engine & Manual Review Prioritisation."
    )
    parser.add_argument("--input", required=True, type=Path, help="Path to processed data root directory")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Output destination directory")
    parser.add_argument("--dataset-id", default=None, help="Identifier for the dataset run")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    result = run_supervisory_risk(args.input, args.output, args.dataset_id)
    print("SENTRA Supervisory Risk Engine & Manual Review Prioritisation Complete")
    print(f"Entities evaluated: {len(result.entities_evaluated)}")
    print(f"Risk bands: {dict(Counter(r.risk_band for r in result.entity_risks))}")
    print(f"Risk contributions: {len(result.risk_contributions)}")
    print(f"Review queue items: {len(result.review_queue)}")
    print(f"Top priority items (High): {len([q for q in result.review_queue if q.priority == 'HIGH'])}")
    print(f"Detectors consumed: {', '.join(result.detectors_consumed)}")
    print(f"Output directory: {args.output}")


if __name__ == "__main__":
    main()
