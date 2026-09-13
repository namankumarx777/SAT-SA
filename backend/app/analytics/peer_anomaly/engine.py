from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import polars as pl

from app.analytics.peer_anomaly.anomaly import ANOMALY_FEATURES, detect_anomalies, prepare_anomaly_matrix
from app.analytics.peer_anomaly.benchmarks import METRICS, peer_statistics
from app.analytics.peer_anomaly.cohorts import COHORT_COLUMNS, MIN_COHORT_SIZE, attach_cohort_keys, build_cohorts
from app.analytics.peer_anomaly.definitions import DETECTORS, MIN_ASSETS, MIN_CLOSED_CASES, MIN_CRITICAL_CASES
from app.analytics.peer_anomaly.evidence import add_feature_evidence, anomaly_finding, peer_finding
from app.analytics.peer_anomaly.models import PeerAnomalyRunResult
from app.analytics.peer_anomaly.statistics import deviation, material_peer_deviation
from app.analytics.rules.engine import load_feature_bundle
from app.analytics.rules.models import Evidence, Finding

DEFAULT_OUTPUT = Path(__file__).resolve().parents[4] / "data" / "processed" / "peer_anomaly"


def _strength(peer_count: int, magnitude: float, support: int = 1) -> str:
    if peer_count >= 4 and magnitude >= 0.25 and support >= 1:
        return "High"
    if peer_count >= 2 and magnitude >= 0.15:
        return "Medium"
    return "Low"


def evaluate_peer_findings(entity_features: pl.DataFrame) -> tuple[list[Finding], list[Evidence], int]:
    frame = attach_cohort_keys(entity_features)
    findings: list[Finding] = []
    evidence: list[Evidence] = []
    benchmarked = 0
    detector_metric = {"PB001": "critical_escalation_rate", "PB002": "critical_median_investigation_minutes", "PB003": "remediation_rate", "PB004": "alerts_per_asset"}
    for row in frame.sort("entity_id").to_dicts():
        peers = frame.filter(
            (pl.col("cohort_key") == row["cohort_key"]) & (pl.col("entity_id") != row["entity_id"])
        )
        if peers.height < MIN_COHORT_SIZE - 1:
            continue
        for detector_id, metric in detector_metric.items():
            if metric not in row or row[metric] is None:
                continue
            if detector_id == "PB001" and int(row["critical_case_count"]) < MIN_CRITICAL_CASES:
                continue
            if detector_id == "PB002" and int(row["critical_case_count"]) < MIN_CRITICAL_CASES:
                continue
            if detector_id == "PB003" and int(row["closed_case_count"]) < MIN_CLOSED_CASES:
                continue
            if detector_id == "PB004" and int(row["total_assets"]) < MIN_ASSETS:
                continue
            values = peers.select(metric).drop_nulls()[metric].to_list()
            if len(values) < MIN_COHORT_SIZE - 1:
                continue
            median = float(pl.Series(values).median())
            observed = float(row[metric])
            if not material_peer_deviation(metric, observed, median):
                continue
            absolute, relative = deviation(observed, median)
            benchmarked += 1
            strength = _strength(len(values), absolute / max(abs(median), 1e-9))
            finding = peer_finding(
                detector_id=detector_id, entity_id=row["entity_id"], metric=metric, observed=observed,
                median=median, deviation=absolute, peer_count=len(values), cohort_key=row["cohort_key"],
                strength=strength, title=f"Significant peer deviation in {metric}",
                rationale=f"Observed {metric}: {observed:.3g}. Peer median: {median:.3g} across {len(values)} comparable entities in cohort {row['cohort_key']}. Absolute deviation: {absolute:.3g}. This is a peer-relative signal, not a control-failure finding.",
            )
            findings.append(finding)
            evidence.extend(add_feature_evidence(finding, "entity_feature", row["entity_id"], {metric: observed, "cohort_key": row["cohort_key"]}, "Observed entity value and structural peer cohort."))
            for peer in peers.select(["entity_id", metric]).drop_nulls().sort("entity_id").to_dicts():
                evidence.extend(add_feature_evidence(finding, "entity_feature", peer["entity_id"], {metric: peer[metric]}, "Comparable peer value used to calculate the reference median."))
    return findings, evidence, benchmarked


def evaluate_anomalies(entity_features: pl.DataFrame) -> tuple[list[Finding], list[Evidence], list[str]]:
    anomalies, features = detect_anomalies(entity_features)
    if not features or anomalies.height == 0:
        return [], [], features
    matrix, _ = prepare_anomaly_matrix(entity_features)
    medians = {feature: float(matrix[feature].median()) for feature in features}
    findings, evidence = [], []
    for row in anomalies.sort(["anomaly_rank", "entity_id"]).to_dicts():
        entity = entity_features.filter(pl.col("entity_id") == row["entity_id"]).to_dicts()[0]
        contributions = []
        for feature in features:
            observed = entity.get(feature)
            reference = medians[feature]
            if observed is None:
                continue
            magnitude = abs(float(observed) - reference) if reference == 0 else abs(float(observed) - reference) / abs(reference)
            contributions.append({"feature": feature, "observed_value": float(observed), "reference_value": reference, "relative_deviation": magnitude})
        contributions = sorted(contributions, key=lambda item: (-item["relative_deviation"], item["feature"]))[:3]
        strength = "High" if len(contributions) >= 3 else "Medium"
        rationale = "Contributing deviations: " + "; ".join(f"{item['feature']}={item['observed_value']:.3g} vs population median {item['reference_value']:.3g}" for item in contributions) + ". These are contextual deviations, not formal feature attribution or risk scores."
        finding = anomaly_finding(entity_id=row["entity_id"], score=float(row["anomaly_score"]), rank=int(row["anomaly_rank"]), contributions=contributions, strength=strength, rationale=rationale)
        findings.append(finding)
        evidence.extend(add_feature_evidence(finding, "entity_feature", row["entity_id"], {feature: item["observed_value"] for item in contributions}, "Operational feature contributing to the unusual-profile context."))
    return findings, evidence, features


def evaluate_all(bundle: dict[str, pl.DataFrame]) -> PeerAnomalyRunResult:
    peer_findings, peer_evidence, benchmarked = evaluate_peer_findings(bundle["entity_features"])
    anomaly_findings, anomaly_evidence, features = evaluate_anomalies(bundle["entity_features"])
    findings = sorted(peer_findings + anomaly_findings, key=lambda item: (item.rule_id, item.entity_id, item.id))
    evidence_map = {item.id: item for item in peer_evidence + anomaly_evidence}
    evidence = sorted(evidence_map.values(), key=lambda item: (item.finding_id, item.source_type, item.source_id, item.field, item.id))
    return PeerAnomalyRunResult(findings=findings, evidence=evidence, cohort_count=len(build_cohorts(bundle["entity_features"])), entities_benchmarked=benchmarked, anomalies=len(anomaly_findings))


def _frame(items: list) -> pl.DataFrame:
    if not items:
        return pl.DataFrame()
    rows = [item.model_dump() for item in items]
    for row in rows:
        for key, value in row.items():
            if value is not None and not isinstance(value, (str, int, float, bool)):
                row[key] = json.dumps(value, sort_keys=True) if isinstance(value, (list, dict)) else str(value)
    return pl.DataFrame(rows)


def write_outputs(result: PeerAnomalyRunResult, output_dir: str | Path, dataset_id: str, feature_list: list[str]) -> None:
    destination = Path(output_dir); destination.mkdir(parents=True, exist_ok=True)
    _frame(result.findings).write_parquet(destination / "findings.parquet")
    _frame(result.evidence).write_parquet(destination / "evidence.parquet")
    manifest = {
        "schema_version": "1.0", "dataset_id": dataset_id, "generated_at": datetime.now(timezone.utc).isoformat(),
        "peer_detectors": [key for key in DETECTORS if key.startswith("PB")], "anomaly_detectors": ["AN001"],
        "cohort_definition": COHORT_COLUMNS, "minimum_cohort_size": MIN_COHORT_SIZE,
        "thresholds": {key: value.thresholds for key, value in DETECTORS.items()},
        "anomaly_configuration": {"contamination": 0.10, "random_state": 42, "n_estimators": 200, "feature_imputation": "column median after excluding features with >50% missingness"},
        "feature_list": feature_list, "deferred_detectors": {},
        "evidence_strength_methodology": "Evidence strength reflects peer count, deviation magnitude, supporting metrics, and model context; it is not statistical confidence.",
        "limitations": "AN001 uses one global entity-level Isolation Forest; peer cohorts provide contextual comparison but are not used as model labels.",
        "row_counts": {"findings": len(result.findings), "evidence": len(result.evidence)},
    }
    (destination / "peer_anomaly_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def run_peer_anomaly(input_dir: str | Path, output_dir: str | Path = DEFAULT_OUTPUT, dataset_id: str | None = None) -> PeerAnomalyRunResult:
    bundle = load_feature_bundle(input_dir)
    result = evaluate_all(bundle)
    _, features = prepare_anomaly_matrix(bundle["entity_features"])
    write_outputs(result, output_dir, dataset_id or Path(input_dir).name, features)
    return result


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run SAT-SA peer benchmarking and unknown anomaly detection.")
    parser.add_argument("--input", required=True, type=Path); parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT); parser.add_argument("--dataset-id")
    return parser.parse_args()


def main() -> None:
    args = _parse_args(); result = run_peer_anomaly(args.input, args.output, args.dataset_id)
    print(f"Cohorts: {result.cohort_count}"); print(f"Entities benchmarked: {result.entities_benchmarked}")
    print(f"Peer findings: {dict(Counter(item.rule_id for item in result.findings if item.rule_id.startswith('PB')))}")
    print(f"Anomalies: {result.anomalies}"); print(f"Evidence: {len(result.evidence)}"); print(f"Output: {args.output}")


if __name__ == "__main__":
    main()
