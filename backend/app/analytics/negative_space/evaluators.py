from __future__ import annotations

import polars as pl

from app.analytics.detectors.models import Evidence, Finding
from app.analytics.negative_space.baselines import evidence_strength
from app.analytics.negative_space.definitions import (
    MAX_EVIDENCE_PER_FINDING,
    MIN_CRITICAL_ALERTS_WITHOUT_CASE,
    MIN_CRITICAL_ASSETS,
    MIN_INACTIVE_CRITICAL,
    MIN_INACTIVE_EXPECTED,
    MIN_MONITORING_COVERAGE,
)
from app.analytics.negative_space.evidence import add_evidence, negative_finding, sample_rows
from app.analytics.negative_space.models import NegativeSpaceDefinition, ObservationWindow

Bundle = dict[str, pl.DataFrame]


def evaluate_ns001(detector: NegativeSpaceDefinition, bundle: Bundle, window: ObservationWindow) -> tuple[list[Finding], list[Evidence]]:
    if not window.sufficient:
        return [], []
    entities = bundle["entity_features"]
    inactive = bundle["asset_features"].filter(pl.col("expected_monitoring") & (pl.col("alert_count") == 0))
    counts = inactive.group_by("entity_id").len().rename({"len": "inactive_count"})
    candidates = entities.join(counts, on="entity_id", how="inner").filter(
        (pl.col("inactive_count") >= MIN_INACTIVE_EXPECTED)
        & (pl.col("expected_monitored_assets") >= detector.minimum_population)
        & (pl.col("monitoring_coverage_rate") < MIN_MONITORING_COVERAGE)
    ).sort("entity_id")
    findings, evidence = [], []
    for row in candidates.to_dicts():
        strength = evidence_strength(int(row["expected_monitored_assets"]), 1 - float(row["monitoring_coverage_rate"]))
        finding = negative_finding(detector_id="NS001", entity_id=row["entity_id"], source_id=row["entity_id"], finding_type="Monitoring Coverage", severity="Medium", strength=strength, title="Potential monitoring coverage gap", summary=f"{row['inactive_count']} expected-monitored assets have no observable alert activity.", rationale=f"Expected monitored assets: {row['expected_monitored_assets']}. Assets with activity: {row['expected_monitored_assets_with_activity']}. Missing activity: {row['inactive_count']}. Coverage: {row['monitoring_coverage_rate']:.1%}. Observation window: {window.start} to {window.end}. This is a potential coverage gap, not confirmed telemetry loss.", observed=row["assets_with_alert_activity"], expected=row["expected_monitored_assets"], population=int(row["expected_monitored_assets"]), method="expected_monitoring", baseline_type="configured_expectation", baseline_value=1.0, gap=1 - float(row["monitoring_coverage_rate"]))
        findings.append(finding)
        evidence.extend(add_evidence(finding, "entity_feature", row["entity_id"], ["expected_monitored_assets", "assets_with_alert_activity", "expected_monitored_assets_with_activity", "expected_monitored_assets_without_activity", "monitoring_coverage_rate"], row, "Entity monitoring features establish expected versus observed activity."))
        for asset in sample_rows(inactive.filter(pl.col("entity_id") == row["entity_id"]), ["id"], MAX_EVIDENCE_PER_FINDING):
            evidence.extend(add_evidence(finding, "asset_feature", asset["id"], ["id", "expected_monitoring", "alert_count", "expected_monitoring_no_activity"], asset, "Expected-monitored asset has no alert activity."))
    return findings, evidence


def evaluate_ns002(detector: NegativeSpaceDefinition, bundle: Bundle, window: ObservationWindow) -> tuple[list[Finding], list[Evidence]]:
    if not window.sufficient:
        return [], []
    inactive = bundle["asset_features"].filter((pl.col("criticality") == "Critical") & (pl.col("alert_count") == 0))
    counts = inactive.group_by("entity_id").len().rename({"len": "inactive_critical_count"})
    candidates = bundle["entity_features"].join(counts, on="entity_id", how="inner").filter(
        (pl.col("critical_assets") >= MIN_CRITICAL_ASSETS) & (pl.col("inactive_critical_count") >= MIN_INACTIVE_CRITICAL)
    ).sort("entity_id")
    findings, evidence = [], []
    for row in candidates.to_dicts():
        finding = negative_finding(detector_id="NS002", entity_id=row["entity_id"], source_id=row["entity_id"], finding_type="Critical Asset Inactivity", severity="High", strength=evidence_strength(int(row["critical_assets"]), row["inactive_critical_count"] / row["critical_assets"]), title="Critical assets with no observable security activity", summary=f"{row['inactive_critical_count']} critical assets have no observable security-alert activity.", rationale=f"Critical assets: {row['critical_assets']}. Critical assets with activity: {row['critical_assets_with_activity']}. No-activity critical assets: {row['inactive_critical_count']}. Observation window: {window.start} to {window.end}. No observable activity does not prove the assets are unmonitored.", observed=row["critical_assets_with_activity"], expected=row["critical_assets"], population=int(row["critical_assets"]), method="expected_monitoring", baseline_type="configured_expectation", baseline_value=1.0, gap=row["inactive_critical_count"] / row["critical_assets"])
        findings.append(finding)
        for asset in sample_rows(inactive.filter(pl.col("entity_id") == row["entity_id"]), ["id"]):
            evidence.extend(add_evidence(finding, "asset_feature", asset["id"], ["id", "criticality", "expected_monitoring", "alert_count"], asset, "Critical asset has no observable security-alert activity."))
    return findings, evidence


def evaluate_ns003(detector: NegativeSpaceDefinition, bundle: Bundle, window: ObservationWindow) -> tuple[list[Finding], list[Evidence]]:
    if not window.sufficient:
        return [], []
    if "alert_features" not in bundle or bundle["alert_features"].is_empty():
        return [], []
    alerts = bundle["alert_features"]
    if "source" not in alerts.columns:
        return [], []

    entity_alert_counts = alerts.group_by("entity_id").len().rename({"len": "total_alerts"})
    min_pop = detector.minimum_population or 20
    active_entities = entity_alert_counts.filter(pl.col("total_alerts") >= min_pop)
    if active_entities.height < 2:
        return [], []

    entity_sources = alerts.group_by(["entity_id", "source"]).len()
    total_active_entities = active_entities.height
    source_entity_counts = entity_sources.join(active_entities.select("entity_id"), on="entity_id", how="inner").group_by("source").agg(pl.col("entity_id").n_unique().alias("entity_count"))
    prevalence_thresh = detector.thresholds.get("cohort_prevalence_threshold", 0.60)
    expected_sources = source_entity_counts.filter((pl.col("entity_count") / total_active_entities) >= prevalence_thresh).sort("source")["source"].to_list()

    if not expected_sources:
        return [], []

    findings, evidence = [], []
    for ent in active_entities.sort("entity_id").to_dicts():
        ent_id = ent["entity_id"]
        observed_sources = set(entity_sources.filter(pl.col("entity_id") == ent_id)["source"].to_list())
        missing_sources = sorted([s for s in expected_sources if s not in observed_sources])

        if not missing_sources:
            continue

        gap_ratio = len(missing_sources) / len(expected_sources)
        strength = evidence_strength(int(ent["total_alerts"]), gap_ratio)
        missing_str = ", ".join(missing_sources)
        observed_str = ", ".join(sorted(list(observed_sources))) if observed_sources else "None"

        finding = negative_finding(
            detector_id="NS003",
            entity_id=ent_id,
            source_id=ent_id,
            finding_type="Alert Source Coverage",
            severity="Medium",
            strength=strength,
            title="Absence of expected security telemetry category",
            summary=f"Entity has no observable alerts from expected core category: {missing_str}.",
            rationale=(
                f"Entity has {ent['total_alerts']} total alerts across sources [{observed_str}], "
                f"but 0 alerts from expected core categories [{missing_str}] present in >= {prevalence_thresh:.0%} "
                f"of cohort peers ({len(expected_sources)} expected categories total). Observation window: {window.start} to {window.end}."
            ),
            observed=len(observed_sources),
            expected=len(expected_sources),
            population=int(ent["total_alerts"]),
            method="cohort_telemetry_presence",
            baseline_type="cohort_expectation",
            baseline_value=float(len(expected_sources)),
            gap=gap_ratio,
        )
        findings.append(finding)

        ent_row = {
            "entity_id": ent_id,
            "total_alerts": ent["total_alerts"],
            "observed_sources": observed_str,
            "missing_categories": missing_str,
            "expected_categories": ", ".join(expected_sources),
        }
        evidence.extend(add_evidence(
            finding,
            "alert_feature",
            ent_id,
            ["entity_id", "total_alerts", "observed_sources", "missing_categories"],
            ent_row,
            f"Entity alert telemetry lacks expected core category: {missing_str}.",
        ))

    return findings, evidence


def evaluate_ns004(detector: NegativeSpaceDefinition, bundle: Bundle, window: ObservationWindow) -> tuple[list[Finding], list[Evidence]]:
    if not window.sufficient:
        return [], []
    monthly = bundle["entity_month_features"].sort(["entity_id", "year", "month"])
    findings, evidence = [], []
    for entity_id, frame in monthly.group_by("entity_id", maintain_order=True):
        rows = frame.sort(["year", "month"]).to_dicts()
        if len(rows) < 4:
            continue
        current, history = rows[-1], rows[-4:-1]
        historical_values = [row["alert_count"] for row in history]
        baseline = float(pl.Series(historical_values).median())
        if baseline < 1 or current["alert_count"] >= baseline * 0.30:
            continue
        observed = float(current["alert_count"]); gap = baseline - observed
        finding = negative_finding(detector_id="NS004", entity_id=entity_id[0], source_id=f"{entity_id[0]}-{current['year']}-{current['month']}", finding_type="Low Activity", severity="Medium", strength=evidence_strength(len(history), gap / baseline, "self_history"), title="Potentially low activity relative to own history", summary=f"Current monthly alert activity is materially below the entity's own trailing observed baseline.", rationale=f"Trailing three-month median: {baseline:.1f} alerts. Current month: {observed:.1f} alerts. Observation window: {window.start} to {window.end}. This is a temporal absence signal, not a peer comparison.", observed=observed, expected=None, population=len(history), method="historical_self_median", baseline_type="reference_statistic", baseline_value=baseline, gap=gap)
        findings.append(finding)
        for month in history + [current]:
            evidence.extend(add_evidence(finding, "entity_month_feature", f"{entity_id[0]}-{month['year']}-{month['month']}", ["year", "month", "alert_count", "case_count"], month, "Entity's own monthly activity history supports NS004."))
    return findings, evidence


def evaluate_ns005(detector: NegativeSpaceDefinition, bundle: Bundle, window: ObservationWindow) -> tuple[list[Finding], list[Evidence]]:
    if not window.sufficient:
        return [], []
    eligible = bundle["alert_features"].filter((pl.col("severity") == "Critical") & ~pl.col("has_case"))
    counts = eligible.group_by("entity_id").len().rename({"len": "missing_case_count"})
    total = bundle["alert_features"].filter(pl.col("severity") == "Critical").group_by("entity_id").len().rename({"len": "eligible_critical_count"})
    candidates = total.join(counts, on="entity_id", how="left").with_columns(pl.col("missing_case_count").fill_null(0)).filter(pl.col("eligible_critical_count") >= MIN_CRITICAL_ALERTS_WITHOUT_CASE).sort("entity_id")
    findings, evidence = [], []
    for row in candidates.filter(pl.col("missing_case_count") > 0).to_dicts():
        finding = negative_finding(detector_id="NS005", entity_id=row["entity_id"], source_id=row["entity_id"], finding_type="Missing Investigation", severity="High", strength=evidence_strength(int(row["eligible_critical_count"]), row["missing_case_count"] / row["eligible_critical_count"]), title="Potential missing investigation evidence", summary=f"{row['missing_case_count']} critical alerts have no associated case.", rationale=f"Eligible critical alerts: {row['eligible_critical_count']}. Critical alerts without cases: {row['missing_case_count']}. Observation window: {window.start} to {window.end}. The rule treats critical alerts as the configured expected-investigation population and does not assume this for lower severities.", observed=row["missing_case_count"], expected=0, population=int(row["eligible_critical_count"]), method="configured_critical_investigation_expectation", baseline_type="configured_expectation", baseline_value=0.0, gap=float(row["missing_case_count"]))
        findings.append(finding)
        for alert in sample_rows(eligible.filter(pl.col("entity_id") == row["entity_id"]), ["severity", "timestamp", "id"]):
            evidence.extend(add_evidence(finding, "alert_feature", alert["id"], ["id", "severity", "timestamp", "has_case", "case_id"], alert, "Critical alert lacks an associated case."))
    return findings, evidence


EVALUATORS = {
    "NS001": evaluate_ns001,
    "NS002": evaluate_ns002,
    "NS003": evaluate_ns003,
    "NS004": evaluate_ns004,
    "NS005": evaluate_ns005,
}
