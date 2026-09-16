from __future__ import annotations

import tempfile
from pathlib import Path

from app.blockchain.fabric_client import get_fabric_client
from app.blockchain.hashing import hash_evidence, hash_finding, hash_submission_directory
from app.blockchain.models import EvidenceCommitment, FindingCommitment, IntegrityState


def test_finding_tamper_and_restore_lifecycle():
    client = get_fabric_client()
    finding_id = "F-EG002-CSE011-DEMO"

    # Step 1: Original finding data
    original_finding = {
        "id": finding_id,
        "rule_id": "EG002",
        "entity_id": "CSE-011",
        "severity": "HIGH",
        "metric_name": "escalation_execution_delay_hours",
        "observed_value": 74.5,
        "expected_value": 24.0,
        "rationale": "High escalation delay observed in CSE-011 SOC operations.",
    }

    # Register on Fabric ledger
    orig_hash = hash_finding(original_finding)
    commitment = FindingCommitment(
        recordId=finding_id,
        entityId="CSE-011",
        findingHash=orig_hash,
        sourcePhase="phase6",
        detectorId="EG002",
        createdAt="2026-09-16T10:00:00Z",
    )
    record, tx_id = client.register_finding(commitment)
    assert record.version == 1

    # Step 2: Verify against original -> VERIFIED
    verify_1 = client.verify_record(finding_id, orig_hash)
    assert verify_1.status == IntegrityState.VERIFIED

    # Step 3: Tamper with finding (modify observed value)
    tampered_finding = dict(original_finding)
    tampered_finding["observed_value"] = 8.0  # Reduced to safe level
    tampered_hash = hash_finding(tampered_finding)
    assert tampered_hash != orig_hash

    # Step 4: Verify against tampered data -> MISMATCH
    verify_2 = client.verify_record(finding_id, tampered_hash)
    assert verify_2.status == IntegrityState.MISMATCH

    # Step 5: Restore original data -> VERIFIED
    restored_hash = hash_finding(original_finding)
    verify_3 = client.verify_record(finding_id, restored_hash)
    assert verify_3.status == IntegrityState.VERIFIED


def test_evidence_tamper_and_restore_lifecycle():
    client = get_fabric_client()
    evidence_id = "EVD-ESC-9081"
    finding_id = "F-EG002-CSE011-DEMO"

    orig_ev = {
        "finding_id": finding_id,
        "source_type": "escalation",
        "source_id": "ESC-9081",
        "entity_id": "CSE-011",
        "field": "execution_delay",
        "value": "74.5 hours",
        "reason": "Exceeds SLA",
    }

    orig_ev_hash = hash_evidence(orig_ev)
    commitment = EvidenceCommitment(
        recordId=evidence_id,
        entityId="CSE-011",
        findingId=finding_id,
        contentHash=orig_ev_hash,
        createdAt="2026-09-16T10:05:00Z",
    )
    client.register_evidence(commitment)

    # 1. Original verification
    assert client.verify_record(evidence_id, orig_ev_hash).status == IntegrityState.VERIFIED

    # 2. Tampered evidence
    tampered_ev = dict(orig_ev)
    tampered_ev["value"] = "2.5 hours"
    tampered_ev_hash = hash_evidence(tampered_ev)
    assert client.verify_record(evidence_id, tampered_ev_hash).status == IntegrityState.MISMATCH

    # 3. Restored evidence
    assert client.verify_record(evidence_id, orig_ev_hash).status == IntegrityState.VERIFIED
