"""Canonical deterministic finding/evidence factories (shared detector core).

Kept importable from ``app.analytics.rules.evidence`` for backward
compatibility; the canonical implementation lives in
``app.analytics.detectors.evidence``.
"""

from app.analytics.detectors.evidence import (
    RULE_EVALUATION_TIME,
    evidence_id,
    make_evidence,
    make_finding,
    stable_id,
)

__all__ = [
    "RULE_EVALUATION_TIME",
    "evidence_id",
    "make_evidence",
    "make_finding",
    "stable_id",
]
