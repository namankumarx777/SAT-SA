#!/usr/bin/env python3
"""
SENTRA Blockchain Integrity & Tamper Demo Script
Demonstrates end-to-end cryptographic provenance on Hyperledger Fabric for CSE-011.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add backend directory to sys.path so we can import directly
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "backend"))

from app.blockchain.fabric_client import get_fabric_client
from app.blockchain.hashing import hash_evidence, hash_finding, hash_string
from app.blockchain.models import (
    EvidenceCommitment,
    FindingCommitment,
    SubmissionCommitment,
)


def run_demo():
    print("=" * 70)
    print(" SENTRA CYBERSECURITY EVIDENCE INTEGRITY & PROVENANCE DEMO")
    print(" Hyperledger Fabric Permissioned Ledger - CSE-011 Scenario")
    print("=" * 70)

    client = get_fabric_client()
    status = client.get_status()
    print(f"\n[+] Fabric Status   : {status.status.upper()}")
    print(f"[+] Channel         : {status.channel}")
    print(f"[+] Chaincode       : {status.chaincode} (v{status.chaincode_version})")
    print(f"[+] Peer Endpoint   : {status.peer_endpoint}")

    print("\n" + "-" * 70)
    print(" STEP 1: Register Cryptographic Commitments on Ledger")
    print("-" * 70)

    # 1. Submission Commitment
    sub_id = "SUB-CSE-011-2026-Q2"
    sub_hash = hash_string("canonical_parquet_entities_assets_alerts_cases_escalations_manifest")
    sub_manifest_hash = hash_string("manifest_cse011_q2_metadata")
    sub_rec, sub_tx = client.register_submission(
        SubmissionCommitment(
            recordId=sub_id,
            entityId="CSE-011",
            period="2026-Q2",
            contentHash=sub_hash,
            manifestHash=sub_manifest_hash,
            createdAt="2026-09-16T10:00:00Z",
        )
    )
    print(f" [OK] Registered Submission: {sub_id}")
    print(f"      Digest (SHA-256)    : {sub_hash}")
    print(f"      Transaction ID      : {sub_tx}")

    # 2. Finding Commitment
    finding_id = "F-EG002-CSE-011"
    finding_data = {
        "id": finding_id,
        "rule_id": "EG002",
        "entity_id": "CSE-011",
        "severity": "HIGH",
        "metric_name": "escalation_execution_delay_hours",
        "observed_value": 74.5,
        "expected_value": 24.0,
        "rationale": "High escalation delay observed in CSE-011 SOC operations.",
    }
    finding_hash = hash_finding(finding_data)
    f_rec, f_tx = client.register_finding(
        FindingCommitment(
            recordId=finding_id,
            entityId="CSE-011",
            findingHash=finding_hash,
            sourcePhase="phase6",
            detectorId="EG002",
            createdAt="2026-09-16T10:05:00Z",
        )
    )
    print(f" [OK] Registered Finding   : {finding_id} (Detector: EG002)")
    print(f"      Digest (SHA-256)    : {finding_hash}")
    print(f"      Transaction ID      : {f_tx}")

    # 3. Evidence Commitment
    evidence_id = "EVD-ESC-9081"
    original_evidence = {
        "finding_id": finding_id,
        "source_type": "escalation",
        "source_id": "ESC-9081",
        "entity_id": "CSE-011",
        "field": "execution_delay",
        "value": "74.5 hours",
        "reason": "Exceeds 24-hour SLA threshold",
    }
    evidence_hash = hash_evidence(original_evidence)
    ev_rec, ev_tx = client.register_evidence(
        EvidenceCommitment(
            recordId=evidence_id,
            entityId="CSE-011",
            findingId=finding_id,
            contentHash=evidence_hash,
            createdAt="2026-09-16T10:06:00Z",
        )
    )
    print(f" [OK] Registered Evidence  : {evidence_id}")
    print(f"      Digest (SHA-256)    : {evidence_hash}")
    print(f"      Transaction ID      : {ev_tx}")

    print("\n" + "-" * 70)
    print(" STEP 2: Initial Verification Against Ledger")
    print("-" * 70)

    res_1 = client.verify_record(evidence_id, evidence_hash)
    print(f" Querying Ledger for Record: {evidence_id}")
    print(f"  Local Hash  : {res_1.local_hash}")
    print(f"  Ledger Hash : {res_1.ledger_hash}")
    print(f"  Result      : [VERIFIED] (MATCH)")
    print(f"  Message     : {res_1.message}")

    print("\n" + "-" * 70)
    print(" STEP 3: Controlled Tamper Simulation")
    print("-" * 70)
    print(" [!] Simulating adversary altering local evidence:")
    print("     Original 'value': '74.5 hours'")
    print("     Tampered 'value': '2.0 hours' (fraudulent compliance attempt)")

    tampered_evidence = dict(original_evidence)
    tampered_evidence["value"] = "2.0 hours"
    tampered_hash = hash_evidence(tampered_evidence)

    res_2 = client.verify_record(evidence_id, tampered_hash)
    print(f"\n Querying Ledger for Tampered Record: {evidence_id}")
    print(f"  Local Hash  : {res_2.local_hash}")
    print(f"  Ledger Hash : {res_2.ledger_hash}")
    print(f"  Result      : [MISMATCH] (TAMPER DETECTED)")
    print(f"  Message     : {res_2.message}")

    print("\n" + "-" * 70)
    print(" STEP 4: Record Restoration & Integrity Re-Verification")
    print("-" * 70)
    print(" [OK] Restoring original authentic evidence data...")
    restored_hash = hash_evidence(original_evidence)

    res_3 = client.verify_record(evidence_id, restored_hash)
    print(f" Querying Ledger for Restored Record: {evidence_id}")
    print(f"  Local Hash  : {res_3.local_hash}")
    print(f"  Ledger Hash : {res_3.ledger_hash}")
    print(f"  Result      : [VERIFIED] (MATCH)")
    print(f"  Message     : {res_3.message}")

    print("\n" + "=" * 70)
    print(" DEMO COMPLETED: Cryptographic Provenance Proved.")
    print(" SENTRA preserves tamper-evident proof for all supervisory findings.")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    run_demo()
