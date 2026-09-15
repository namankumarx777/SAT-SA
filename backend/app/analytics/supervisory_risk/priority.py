from __future__ import annotations

from typing import Any

from app.analytics.supervisory_risk.config import PRIORITY_THRESHOLDS
from app.analytics.supervisory_risk.correlation import CorrelatedGroupSignal
from app.analytics.supervisory_risk.inputs import StandardizedEvidence, StandardizedFinding
from app.analytics.supervisory_risk.models import EntityRisk, PriorityLevel, ReviewQueueItem


def _determine_priority(score: float) -> PriorityLevel:
    if score >= PRIORITY_THRESHOLDS["HIGH"]:
        return "HIGH"
    if score >= PRIORITY_THRESHOLDS["MEDIUM"]:
        return "MEDIUM"
    return "LOW"


def build_review_queue(
    entity_risks: list[EntityRisk],
    group_signals_by_entity: dict[str, list[CorrelatedGroupSignal]],
    findings_by_entity: dict[str, list[StandardizedFinding]],
    evidence_by_finding: dict[str, list[StandardizedEvidence]],
) -> list[ReviewQueueItem]:
    """Generate a separate, ranked supervisory manual-review prioritisation queue.

    Prioritisation explicitly favors:
    1. Systemic execution gaps (Phase 6) and unmonitored blindspots (Phase 7)
    2. Strong multi-phase corroboration
    3. Severe, well-supported operational failures
    rather than raw counts of low-severity record findings.
    """
    queue_items: list[ReviewQueueItem] = []

    for er in entity_risks:
        entity_id = er.entity_id
        group_signals = group_signals_by_entity.get(entity_id, [])
        findings = findings_by_entity.get(entity_id, [])

        if not findings and er.overall_score == 0:
            continue

        # Check for presence of systemic execution gaps (Phase 6) and negative space (Phase 7)
        has_execution_gap = any(f.source_phase == "phase6" for f in findings)
        has_negative_space = any(f.source_phase == "phase7" for f in findings)
        has_strong_corroboration = any(gs.corroboration_level == "Strong" for gs in group_signals)
        has_moderate_corroboration = any(gs.corroboration_level == "Moderate" for gs in group_signals)

        # 1. ENTITY-level queue item
        base_priority = er.overall_score * 0.40
        systemic_boost = 25.0 if has_execution_gap else 0.0
        blindspot_boost = 15.0 if has_negative_space else 0.0
        corroboration_boost = 15.0 if has_strong_corroboration else (8.0 if has_moderate_corroboration else 0.0)

        # Evidence strength factor
        ev_factor = 1.05 if "High" in er.evidence_strength_summary else (0.90 if "Low" in er.evidence_strength_summary else 1.0)
        entity_priority_score = min(100.0, max(0.0, round((base_priority + systemic_boost + blindspot_boost + corroboration_boost) * ev_factor, 2)))

        entity_reason = (
            f"Supervisory audit recommendation for {entity_id}: Risk band {er.risk_band} ({er.overall_score:.1f}/100). "
            f"Key concern: {er.top_reason}. "
            f"{'Systemic execution gap detected; ' if has_execution_gap else ''}"
            f"{'Unmonitored assets/blindspots observed; ' if has_negative_space else ''}"
            f"Corroboration: {er.corroboration_summary}."
        )

        all_finding_ids = [f.id for f in findings]
        queue_items.append(
            ReviewQueueItem(
                rank=1,  # Temporary, recalculated after global sorting
                entity_id=entity_id,
                record_type="ENTITY",
                record_id=entity_id,
                priority=_determine_priority(entity_priority_score),
                priority_score=entity_priority_score,
                reason=entity_reason,
                supporting_finding_ids=all_finding_ids[:10],
                evidence_strength="High" if "High" in er.evidence_strength_summary else "Medium",
            )
        )

        # 2. Granular Record Items for Systemic / High-Impact Findings
        # Emit individual review items for Phase 6 Execution Gaps and Phase 7 Blindspots
        for f in findings:
            if f.source_phase == "phase6":  # Systemic Execution Gap
                gap_val = float(f.gap_value) if f.gap_value is not None else 0.0
                score = min(100.0, round(65.0 + abs(gap_val) * 40.0, 2))
                queue_items.append(
                    ReviewQueueItem(
                        rank=1,
                        entity_id=entity_id,
                        record_type="FINDING",
                        record_id=f.id,
                        priority=_determine_priority(score),
                        priority_score=score,
                        reason=f"Execution Gap ({f.rule_id}): {f.title}. Gap: {gap_val:.3g} vs baseline {f.baseline_value}.",
                        supporting_finding_ids=[f.id],
                        evidence_strength=f.evidence_strength,
                    )
                )
            elif f.rule_id in ("NS001", "NS002"):  # Inactive expected or critical assets
                # Extract asset source IDs from linked evidence
                ev_records = evidence_by_finding.get(f.id, [])
                asset_ids = [ev.source_id for ev in ev_records if ev.source_type == "asset_feature"]
                target_asset = asset_ids[0] if asset_ids else f.id
                score = 80.0 if f.rule_id == "NS002" else 65.0
                queue_items.append(
                    ReviewQueueItem(
                        rank=1,
                        entity_id=entity_id,
                        record_type="ASSET",
                        record_id=target_asset,
                        priority=_determine_priority(score),
                        priority_score=score,
                        reason=f"Unmonitored Blindspot ({f.rule_id}): {f.title}. Critical asset without observed security activity.",
                        supporting_finding_ids=[f.id],
                        evidence_strength=f.evidence_strength,
                    )
                )

    # Sort queue deterministically: highest priority_score first, then by priority level, entity_id, record_id
    PRIORITY_ORDER = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
    sorted_items = sorted(
        queue_items,
        key=lambda item: (-item.priority_score, -PRIORITY_ORDER.get(item.priority, 0), item.entity_id, item.record_type, item.record_id),
    )

    # Assign 1-indexed ranks
    for rank_idx, item in enumerate(sorted_items, start=1):
        item.rank = rank_idx

    return sorted_items
