from __future__ import annotations

from pydantic import BaseModel, Field

MIN_COHORT_SIZE = 3
MIN_CRITICAL_CASES = 5
MIN_CLOSED_CASES = 10
MIN_ASSETS = 20
CONTAMINATION = 0.10
RANDOM_STATE = 42
N_ESTIMATORS = 200


class DetectorDefinition(BaseModel):
    detector_id: str
    name: str
    description: str
    enabled: bool = True
    thresholds: dict[str, float | int] = Field(default_factory=dict)


DETECTORS = {
    "PB001": DetectorDefinition(detector_id="PB001", name="Critical Escalation Peer Deviation", description="Critical escalation differs materially from structural peers.", thresholds={"minimum_peers": 3, "minimum_critical_cases": MIN_CRITICAL_CASES, "minimum_rate_gap": 0.15}),
    "PB002": DetectorDefinition(detector_id="PB002", name="Investigation Duration Peer Deviation", description="Critical investigation duration differs materially from structural peers.", thresholds={"minimum_peers": 3, "minimum_critical_cases": MIN_CRITICAL_CASES}),
    "PB003": DetectorDefinition(detector_id="PB003", name="Remediation Rate Peer Deviation", description="Remediation rate differs materially from structural peers.", thresholds={"minimum_peers": 3, "minimum_closed_cases": MIN_CLOSED_CASES, "minimum_rate_gap": 0.15}),
    "PB004": DetectorDefinition(detector_id="PB004", name="Operational Volume Per Asset Deviation", description="Alert volume per asset differs materially from structural peers.", thresholds={"minimum_peers": 3, "minimum_assets": MIN_ASSETS}),
    "AN001": DetectorDefinition(detector_id="AN001", name="Unusual Operational Profile", description="Entity operational profile is unusual in the global population.", thresholds={"minimum_entities": 10, "contamination": CONTAMINATION}),
}
