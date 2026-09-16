from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.analytics.store import PhaseNotFoundError, PhaseStore
from app.blockchain.fabric_client import get_fabric_client
from app.blockchain.hashing import (
    hash_evidence,
    hash_finding,
    hash_submission_directory,
)
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

PHASE_DIRS = (
    ("phase5", "phase5"),
    ("phase5", "phase5-final"),
    ("phase6", "phase6"),
    ("phase6", "execution_gap"),
    ("phase6", "execution_gap-final"),
    ("phase7", "phase7"),
    ("phase7", "negative_space"),
    ("phase7", "negative_space-final"),
    ("phase8", "phase8"),
    ("phase8", "peer_anomaly"),
    ("phase8", "peer_anomaly-final"),
    ("phase9", "phase9"),
    ("phase9", "supervisory_risk"),
    ("phase9", "supervisory_risk-final"),
)


def _find_finding_in_stores(finding_id: str, output_path: str | None = None) -> tuple[dict[str, Any], list[dict[str, Any]], str]:
    """Search for finding across phases 5-9."""
    if output_path:
        base = Path(output_path)
        for phase, dirname in PHASE_DIRS:
            store = PhaseStore(phase, base / dirname if (base / dirname).exists() else base)
            try:
                detail = store.get_finding(finding_id)
                return detail.finding, detail.evidence, phase
            except (PhaseNotFoundError, ValueError):
                continue
    # Default search locations (supports running from repo root or backend/)
    data_dir_candidates = [
        Path("data/processed"),
        Path("../data/processed"),
        Path(__file__).resolve().parents[3] / "data/processed",
    ]
    data_dir = next((p for p in data_dir_candidates if p.is_dir()), Path("data/processed"))

    for phase, dirname in PHASE_DIRS:
        store = PhaseStore(phase, data_dir / dirname)
        try:
            detail = store.get_finding(finding_id)
            return detail.finding, detail.evidence, phase
        except (PhaseNotFoundError, ValueError):
            continue
    raise PhaseNotFoundError(f"Finding {finding_id} not found in any phase dataset")


class BlockchainIntegrityService:
    def __init__(self):
        self.client = get_fabric_client()

    def get_status(self) -> BlockchainStatus:
        return self.client.get_status()

    def register_submission_commitment(
        self,
        submission_id: str,
        entity_id: str,
        period: str,
        data_directory: Path | str,
    ) -> tuple[LedgerRecord, str]:
        hashes = hash_submission_directory(data_directory)
        commitment = SubmissionCommitment(
            recordId=submission_id,
            entityId=entity_id,
            period=period,
            contentHash=hashes["content_hash"],
            manifestHash=hashes["manifest_hash"],
            createdAt=datetime.now(timezone.utc).isoformat(),
            registeredBy="SENTRA",
        )
        return self.client.register_submission(commitment)

    def register_finding_commitment(
        self,
        finding_id: str,
        output_path: str | None = None,
    ) -> tuple[LedgerRecord, str]:
        finding, _, phase = _find_finding_in_stores(finding_id, output_path)
        digest = hash_finding(finding)
        commitment = FindingCommitment(
            recordId=finding_id,
            entityId=str(finding.get("entity_id", "")),
            findingHash=digest,
            sourcePhase=phase,
            detectorId=str(finding.get("rule_id", "")),
            createdAt=datetime.now(timezone.utc).isoformat(),
            registeredBy="SENTRA",
        )
        return self.client.register_finding(commitment)

    def register_evidence_commitment(
        self,
        evidence_id: str,
        finding_id: str,
        output_path: str | None = None,
    ) -> tuple[LedgerRecord, str]:
        _, evidence_list, _ = _find_finding_in_stores(finding_id, output_path)
        target_ev = next((ev for ev in evidence_list if str(ev.get("id") or ev.get("evidence_id")) == evidence_id or str(ev.get("source_id")) == evidence_id), None)
        if not target_ev:
            if evidence_list:
                target_ev = evidence_list[0]
            else:
                raise PhaseNotFoundError(f"Evidence {evidence_id} not found for finding {finding_id}")

        digest = hash_evidence(target_ev)
        commitment = EvidenceCommitment(
            recordId=evidence_id,
            entityId=str(target_ev.get("entity_id", "")),
            findingId=finding_id,
            contentHash=digest,
            createdAt=datetime.now(timezone.utc).isoformat(),
            registeredBy="SENTRA",
        )
        return self.client.register_evidence(commitment)

    def verify_record_live(
        self,
        record_id: str,
        expected_hash: str | None = None,
    ) -> VerificationResponse:
        """Verify record against ledger.
        
        If expected_hash is not provided, computes live local hash from storage.
        """
        if not self.client.is_connected():
            return VerificationResponse(
                recordId=record_id,
                status=IntegrityState.UNAVAILABLE,
                localHash=expected_hash or "",
                ledgerHash=None,
                message="Hyperledger Fabric ledger is unavailable",
            )

        # If hash not explicitly provided, try to find and compute from stored finding/evidence
        computed_hash = expected_hash
        if not computed_hash:
            try:
                finding, _, _ = _find_finding_in_stores(record_id)
                computed_hash = hash_finding(finding)
            except PhaseNotFoundError:
                computed_hash = ""

        return self.client.verify_record(record_id, computed_hash)

    def get_record(self, record_id: str) -> LedgerRecord | None:
        return self.client.get_record(record_id)

    def get_history(self, record_id: str) -> list[LedgerHistoryEntry]:
        return self.client.get_history(record_id)


integrity_service = BlockchainIntegrityService()
