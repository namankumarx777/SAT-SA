from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.analytics.supervisory_risk.config import (
    ANOMALY_SCORE_CEILING,
    SEVERITY_WEIGHTS,
)
from app.analytics.supervisory_risk.inputs import StandardizedFinding


@dataclass
class NormalizedSignal:
    entity_id: str
    detector_id: str
    source_phase: str
    signal_name: str
    raw_value: float | int | str | None
    normalized_value: float  # Bounded strictly 0.0 to 100.0
    severity: str
    evidence_strength: str | None
    assessment_strength: str  # "Low", "Medium", "High"
    supporting_finding_ids: list[str] = field(default_factory=list)
    contributing_features: list[str] = field(default_factory=list)
    rationale: str = ""
    is_assessable: bool = True
    unassessable_reason: str | None = None


def _derive_assessment_strength(evidence_strength: str | None, sample_size: int | None) -> str:
    """Explicit deterministic assessment strength rule (not statistical confidence)."""
    if evidence_strength == "High":
        return "High"
    if evidence_strength == "Medium":
        return "Medium"
    if evidence_strength == "Low":
        return "Low"
    # Fallback for Phase 5 (where evidence_strength is None) based on sample support
    if sample_size is not None and sample_size >= 10:
        return "Medium"
    return "Low"


def normalize_finding_signal(
    finding: StandardizedFinding,
    entity_metadata: dict[str, Any],
    all_entity_findings_for_detector: list[StandardizedFinding],
) -> NormalizedSignal:
    """Transform an individual or aggregated finding into a normalized supervisory signal."""
    detector_id = finding.rule_id
    entity_id = finding.entity_id
    source_phase = finding.source_phase
    finding_ids = [f.id for f in all_entity_findings_for_detector]
    finding_count = len(all_entity_findings_for_detector)

    # 1. Phase 5: Record-level findings aggregated to signal prevalence
    if source_phase == "phase5":
        if detector_id == "R001":  # Critical Alert Closed Rapidly
            denominator = int(entity_metadata.get("critical_closed_case_count", 0))
            if denominator == 0:
                denominator = int(entity_metadata.get("closed_case_count", 0))
            if denominator == 0:
                return NormalizedSignal(
                    entity_id=entity_id, detector_id=detector_id, source_phase=source_phase,
                    signal_name="Critical Rapid Closure Prevalence", raw_value=finding_count,
                    normalized_value=0.0, severity=finding.severity, evidence_strength=None,
                    assessment_strength="Low", supporting_finding_ids=finding_ids,
                    is_assessable=False, unassessable_reason="No closed cases observed for entity.",
                )
            prevalence = min(1.0, finding_count / denominator)
            norm_val = round(prevalence * 100.0, 2)
            strength = _derive_assessment_strength(None, denominator)
            return NormalizedSignal(
                entity_id=entity_id, detector_id=detector_id, source_phase=source_phase,
                signal_name="Critical Rapid Closure Prevalence", raw_value=finding_count,
                normalized_value=norm_val, severity=finding.severity, evidence_strength=None,
                assessment_strength=strength, supporting_finding_ids=finding_ids,
                rationale=f"{finding_count} critical rapid closure findings observed across {denominator} closed cases ({norm_val:.1f}% prevalence).",
            )

        elif detector_id == "R002":  # Critical Alert Without Escalation
            denominator = int(entity_metadata.get("critical_case_count", 0))
            if denominator == 0:
                return NormalizedSignal(
                    entity_id=entity_id, detector_id=detector_id, source_phase=source_phase,
                    signal_name="Unescalated Critical Case Prevalence", raw_value=finding_count,
                    normalized_value=0.0, severity=finding.severity, evidence_strength=None,
                    assessment_strength="Low", supporting_finding_ids=finding_ids,
                    is_assessable=False, unassessable_reason="No critical cases observed for entity.",
                )
            prevalence = min(1.0, finding_count / denominator)
            norm_val = round(prevalence * 100.0, 2)
            strength = _derive_assessment_strength(None, denominator)
            return NormalizedSignal(
                entity_id=entity_id, detector_id=detector_id, source_phase=source_phase,
                signal_name="Unescalated Critical Case Prevalence", raw_value=finding_count,
                normalized_value=norm_val, severity=finding.severity, evidence_strength=None,
                assessment_strength=strength, supporting_finding_ids=finding_ids,
                rationale=f"{finding_count} unescalated critical cases out of {denominator} critical cases ({norm_val:.1f}% prevalence).",
            )

        elif detector_id == "R003":  # Repeated Alerts Without Remediation
            denominator = int(entity_metadata.get("total_assets", 0))
            if denominator == 0:
                return NormalizedSignal(
                    entity_id=entity_id, detector_id=detector_id, source_phase=source_phase,
                    signal_name="Unremediated Repeated Alert Asset Prevalence", raw_value=finding_count,
                    normalized_value=0.0, severity=finding.severity, evidence_strength=None,
                    assessment_strength="Low", supporting_finding_ids=finding_ids,
                    is_assessable=False, unassessable_reason="No asset inventory available.",
                )
            prevalence = min(1.0, finding_count / denominator)
            # Scaling asset prevalence: even 10% of assets with repeated unremediated alerts is significant
            norm_val = min(100.0, round(prevalence * 300.0, 2))
            strength = _derive_assessment_strength(None, denominator)
            return NormalizedSignal(
                entity_id=entity_id, detector_id=detector_id, source_phase=source_phase,
                signal_name="Unremediated Repeated Alert Asset Prevalence", raw_value=finding_count,
                normalized_value=norm_val, severity=finding.severity, evidence_strength=None,
                assessment_strength=strength, supporting_finding_ids=finding_ids,
                rationale=f"{finding_count} assets with repeated unremediated alerts across {denominator} total assets.",
            )

        elif detector_id == "R004":  # Short High/Critical Investigation
            denominator = int(entity_metadata.get("case_count", 0))
            if denominator == 0:
                return NormalizedSignal(
                    entity_id=entity_id, detector_id=detector_id, source_phase=source_phase,
                    signal_name="Short Investigation Duration Prevalence", raw_value=finding_count,
                    normalized_value=0.0, severity=finding.severity, evidence_strength=None,
                    assessment_strength="Low", supporting_finding_ids=finding_ids,
                    is_assessable=False, unassessable_reason="No cases observed for entity.",
                )
            prevalence = min(1.0, finding_count / denominator)
            norm_val = round(prevalence * 100.0, 2)
            strength = _derive_assessment_strength(None, denominator)
            return NormalizedSignal(
                entity_id=entity_id, detector_id=detector_id, source_phase=source_phase,
                signal_name="Short Investigation Duration Prevalence", raw_value=finding_count,
                normalized_value=norm_val, severity=finding.severity, evidence_strength=None,
                assessment_strength=strength, supporting_finding_ids=finding_ids,
                rationale=f"{finding_count} short investigation cases out of {denominator} total cases ({norm_val:.1f}% prevalence).",
            )

        elif detector_id == "R005":  # Low Monitoring Coverage
            denominator = int(entity_metadata.get("expected_monitored_assets", 0))
            if denominator == 0:
                return NormalizedSignal(
                    entity_id=entity_id, detector_id=detector_id, source_phase=source_phase,
                    signal_name="Monitoring Coverage Gap", raw_value=finding.observed_value,
                    normalized_value=0.0, severity=finding.severity, evidence_strength=None,
                    assessment_strength="Low", supporting_finding_ids=finding_ids,
                    is_assessable=False, unassessable_reason="No expected-monitored assets defined.",
                )
            observed_gap = finding.observed_value
            norm_val = min(100.0, round((float(observed_gap) / denominator) * 100.0, 2)) if isinstance(observed_gap, (int, float)) else 50.0
            strength = _derive_assessment_strength(None, denominator)
            return NormalizedSignal(
                entity_id=entity_id, detector_id=detector_id, source_phase=source_phase,
                signal_name="Monitoring Coverage Gap", raw_value=observed_gap,
                normalized_value=norm_val, severity=finding.severity, evidence_strength=None,
                assessment_strength=strength, supporting_finding_ids=finding_ids,
                rationale=f"Observed monitoring gap on expected-monitored assets: {observed_gap} gap assets out of {denominator}.",
            )

    # 2. Phase 6: Configured Execution Gaps
    if source_phase == "phase6":
        gap = float(finding.gap_value) if finding.gap_value is not None else 0.0
        baseline = float(finding.baseline_value) if finding.baseline_value is not None else 1.0
        if baseline <= 0:
            baseline = 1.0

        if detector_id == "EG001":  # Critical Escalation Gap (expected 0.60)
            norm_val = min(100.0, round((gap / baseline) * 100.0, 2))
        elif detector_id == "EG002":  # Investigation Effort Gap (expected 20 min)
            norm_val = min(100.0, round((gap / baseline) * 100.0, 2))
        elif detector_id == "EG003":  # Remediation Gap (expected 0.75)
            norm_val = min(100.0, round((gap / baseline) * 100.0, 2))
        elif detector_id == "EG004":  # Rapid Closure Gap (expected max 0.10)
            # Gap above 10% maximum expected rapid closure
            norm_val = min(100.0, round((gap / 0.40) * 100.0, 2))
        else:
            norm_val = min(100.0, round(abs(gap) * 100.0, 2))

        strength = _derive_assessment_strength(finding.evidence_strength, finding.population_size)
        return NormalizedSignal(
            entity_id=entity_id, detector_id=detector_id, source_phase=source_phase,
            signal_name=finding.title, raw_value=gap, normalized_value=norm_val,
            severity=finding.severity, evidence_strength=finding.evidence_strength,
            assessment_strength=strength, supporting_finding_ids=[finding.id],
            rationale=f"Execution gap of {gap:.3g} against configured baseline {baseline:.3g} ({finding.rationale})",
        )

    # 3. Phase 7: Negative Space Detectors
    if source_phase == "phase7":
        obs = float(finding.observed_value) if finding.observed_value is not None else 0.0
        if detector_id == "NS001":  # Inactive expected-monitored assets
            denom = int(entity_metadata.get("expected_monitored_assets", 1))
            norm_val = min(100.0, round((obs / max(denom, 1)) * 100.0, 2))
        elif detector_id == "NS002":  # Inactive critical assets
            denom = int(entity_metadata.get("critical_assets", 1))
            norm_val = min(100.0, round((obs / max(denom, 1)) * 100.0, 2))
        elif detector_id == "NS003":  # Missing telemetry category blindspot
            gap = float(finding.gap_value) if finding.gap_value is not None else 0.5
            norm_val = min(100.0, round(gap * 100.0, 2))
        elif detector_id == "NS004":  # Unexpectedly low activity vs self-history
            gap = float(finding.gap_value) if finding.gap_value is not None else 0.5
            norm_val = min(100.0, round(gap * 100.0, 2))
        elif detector_id == "NS005":  # Uninvestigated critical alerts
            denom = int(entity_metadata.get("critical_alert_count", 1))
            norm_val = min(100.0, round((obs / max(denom, 1)) * 100.0, 2))
        else:
            norm_val = 50.0

        strength = _derive_assessment_strength(finding.evidence_strength, finding.population_size)
        return NormalizedSignal(
            entity_id=entity_id, detector_id=detector_id, source_phase=source_phase,
            signal_name=finding.title, raw_value=obs, normalized_value=norm_val,
            severity=finding.severity, evidence_strength=finding.evidence_strength,
            assessment_strength=strength, supporting_finding_ids=[finding.id],
            rationale=finding.rationale,
        )

    # 4. Phase 8: Peer Benchmarks & Anomaly Detection
    if source_phase == "phase8":
        if detector_id == "AN001":
            # Strict Non-Probability Anomaly Score Handling:
            # AN001 Isolation Forest score is non-linear and relative within the population.
            # Bounded strictly to ANOMALY_SCORE_CEILING (25.0) to ensure it acts strictly as contextual evidence.
            rank = int(finding.anomaly_rank) if finding.anomaly_rank is not None else 1
            contributions = finding.contributing_deviations or []
            contributing_features = [
                item["feature"] for item in contributions if isinstance(item, dict) and "feature" in item
            ]
            avg_rel_dev = 0.0
            if contributions:
                valid_devs = [float(item.get("relative_deviation", 0.0)) for item in contributions if isinstance(item, dict)]
                avg_rel_dev = sum(valid_devs) / len(valid_devs) if valid_devs else 0.0

            # Rank-based base contextual signal (Rank 1 -> 18.0, Rank 2 -> 14.0, Rank 3 -> 10.0, etc.)
            base_rank_score = max(5.0, 18.0 - (rank - 1) * 4.0)
            # Deviation intensity component (bounded up to +7.0)
            dev_intensity = min(7.0, round(avg_rel_dev * 8.0, 2))
            norm_val = min(ANOMALY_SCORE_CEILING, round(base_rank_score + dev_intensity, 2))

            strength = _derive_assessment_strength(finding.evidence_strength, finding.population_size)
            return NormalizedSignal(
                entity_id=entity_id, detector_id=detector_id, source_phase=source_phase,
                signal_name="Unusual Operational Profile (Contextual Anomaly)", raw_value=finding.anomaly_score,
                normalized_value=norm_val, severity=finding.severity, evidence_strength=finding.evidence_strength,
                assessment_strength=strength, supporting_finding_ids=[finding.id],
                contributing_features=contributing_features,
                rationale=f"Contextual relative anomaly signal (rank {rank}, avg dev {avg_rel_dev:.2f}) from Isolation Forest; not a probability of compromise or compliance violation.",
            )
        else:
            # Peer deviations: PB001 - PB004
            abs_gap = float(finding.absolute_gap) if finding.absolute_gap is not None else 0.0
            ref_val = float(finding.reference_value) if finding.reference_value is not None else 1.0
            rel_dev = abs_gap / max(abs(ref_val), 1e-6)
            norm_val = min(100.0, round(rel_dev * 60.0, 2))
            strength = _derive_assessment_strength(finding.evidence_strength, finding.population_size)
            return NormalizedSignal(
                entity_id=entity_id, detector_id=detector_id, source_phase=source_phase,
                signal_name=finding.title, raw_value=abs_gap, normalized_value=norm_val,
                severity=finding.severity, evidence_strength=finding.evidence_strength,
                assessment_strength=strength, supporting_finding_ids=[finding.id],
                rationale=finding.rationale,
            )

    # Generic Fallback
    return NormalizedSignal(
        entity_id=entity_id, detector_id=detector_id, source_phase=source_phase,
        signal_name=finding.title, raw_value=finding.observed_value,
        normalized_value=30.0, severity=finding.severity, evidence_strength=finding.evidence_strength,
        assessment_strength="Low", supporting_finding_ids=[finding.id],
        rationale=finding.rationale,
    )
