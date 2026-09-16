from __future__ import annotations

from app.blockchain.models import (
    BlockchainStatus,
    EvidenceCommitment,
    FindingCommitment,
    IntegrityState,
    LedgerHistoryEntry,
    LedgerRecord,
    RecordType,
    SubmissionCommitment,
    VerificationResponse,
)


def test_models_serialization():
    sub = SubmissionCommitment(
        recordId="SUB-001",
        entityId="CSE-011",
        period="2026-Q2",
        contentHash="a" * 64,
        manifestHash="b" * 64,
        createdAt="2026-09-16T10:00:00Z",
    )
    dump = sub.model_dump(by_alias=True)
    assert dump["recordId"] == "SUB-001"
    assert dump["recordType"] == "SUBMISSION"
    assert dump["version"] == 1

    finding = FindingCommitment(
        recordId="F-100",
        entityId="CSE-011",
        findingHash="c" * 64,
        sourcePhase="phase6",
        detectorId="EG002",
        createdAt="2026-09-16T10:00:00Z",
    )
    dump_f = finding.model_dump(by_alias=True)
    assert dump_f["recordId"] == "F-100"
    assert dump_f["detectorId"] == "EG002"

    verify_res = VerificationResponse(
        recordId="F-100",
        status=IntegrityState.VERIFIED,
        localHash="c" * 64,
        ledgerHash="c" * 64,
        message="Valid",
    )
    assert verify_res.status == IntegrityState.VERIFIED
