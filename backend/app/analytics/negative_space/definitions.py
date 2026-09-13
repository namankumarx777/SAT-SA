from __future__ import annotations

from app.analytics.negative_space.models import NegativeSpaceDefinition

MIN_INACTIVE_EXPECTED = 5
MIN_MONITORING_COVERAGE = 0.90
MIN_CRITICAL_ASSETS = 3
MIN_INACTIVE_CRITICAL = 2
MIN_CRITICAL_ALERTS_WITHOUT_CASE = 3
MAX_EVIDENCE_PER_FINDING = 20

DETECTORS: dict[str, NegativeSpaceDefinition] = {
    "NS001": NegativeSpaceDefinition(
        detector_id="NS001", name="Expected-Monitored Asset With No Activity",
        description="Expected-monitored assets without observable alert activity during the observation period.",
        severity="Medium", data_requirements=["asset_features", "entity_features", "alert_features"],
        expectation_method="EXPECTED_MONITORING", minimum_population=5,
        thresholds={"minimum_inactive_assets": MIN_INACTIVE_EXPECTED, "maximum_coverage": MIN_MONITORING_COVERAGE},
    ),
    "NS002": NegativeSpaceDefinition(
        detector_id="NS002", name="Critical Asset With No Security Activity",
        description="Critical assets without observable security-alert activity during the observation period.",
        severity="High", data_requirements=["asset_features", "entity_features", "alert_features"],
        expectation_method="EXPECTED_MONITORING", minimum_population=MIN_CRITICAL_ASSETS,
        thresholds={"minimum_critical_assets": MIN_CRITICAL_ASSETS, "minimum_inactive_critical": MIN_INACTIVE_CRITICAL},
    ),
    "NS003": NegativeSpaceDefinition(
        detector_id="NS003", name="Missing Alert Source Activity",
        description="Deferred: the current contract does not establish which alert sources each entity is expected to use historically or explicitly.",
        severity="Medium", enabled=False, data_requirements=["alert_features"], expectation_method="HISTORICAL_PRESENCE",
        deferred_reason="No source expectation or sufficient historical source-period contract is available.",
    ),
    "NS004": NegativeSpaceDefinition(
        detector_id="NS004", name="Unexpectedly Low Activity",
        description="Entity activity materially below its own trailing observed monthly baseline.",
        severity="Medium", data_requirements=["entity_month_features"], expectation_method="DERIVED_EXPECTATION",
        minimum_population=3, thresholds={"minimum_previous_months": 3, "maximum_current_ratio": 0.30, "minimum_historical_alerts": 1},
    ),
    "NS005": NegativeSpaceDefinition(
        detector_id="NS005", name="Expected Investigation Missing",
        description="Critical alerts without associated cases, where the critical-alert population is sufficient for an absence signal.",
        severity="High", data_requirements=["alert_features"], expectation_method="CONFIGURED_EXPECTATION",
        minimum_population=3, thresholds={"minimum_eligible_critical_alerts": MIN_CRITICAL_ALERTS_WITHOUT_CASE},
    ),
    "NS006": NegativeSpaceDefinition(
        detector_id="NS006", name="Expected Escalation Evidence Missing",
        description="Deferred: this would duplicate Phase 6 entity-level escalation execution-gap evidence without a distinct absence contract.",
        severity="High", enabled=False, data_requirements=["case_features", "entity_features"], expectation_method="CONFIGURED_EXPECTATION",
        deferred_reason="Phase 6 already evaluates critical escalation execution against an explicit expectation; no additional absence-of-record contract is defined.",
    ),
}


def enabled_detectors() -> list[NegativeSpaceDefinition]:
    return [detector for detector in DETECTORS.values() if detector.enabled]
