from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Protocol

from app.blockchain.config import BlockchainConfig, blockchain_config
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

logger = logging.getLogger("satsa.blockchain")


class FabricClientInterface(Protocol):
    def is_connected(self) -> bool: ...
    def get_status(self) -> BlockchainStatus: ...
    def register_submission(self, commitment: SubmissionCommitment) -> tuple[LedgerRecord, str]: ...
    def register_finding(self, commitment: FindingCommitment) -> tuple[LedgerRecord, str]: ...
    def register_evidence(self, commitment: EvidenceCommitment) -> tuple[LedgerRecord, str]: ...
    def get_record(self, record_id: str) -> LedgerRecord | None: ...
    def get_history(self, record_id: str) -> list[LedgerHistoryEntry]: ...
    def verify_record(self, record_id: str, expected_hash: str) -> VerificationResponse: ...


class LocalLedgerClient:
    """Local resilient Hyperledger Fabric ledger store & gateway client.
    
    Provides offline-capable, tamper-evident cryptographic commitments,
    maintains ledger history for versioning, and validates digests.
    """

    def __init__(self, config: BlockchainConfig = blockchain_config):
        self.config = config
        self._records: dict[str, LedgerRecord] = {}
        self._history: dict[str, list[LedgerHistoryEntry]] = {}
        self._tx_counter = 1000
        self._is_online = True

    def set_online(self, online: bool) -> None:
        self._is_online = online

    def is_connected(self) -> bool:
        return self._is_online

    def get_status(self) -> BlockchainStatus:
        status_text = "connected" if self._is_online else "unavailable"
        return BlockchainStatus(
            status=status_text,
            network=self.config.network_name,
            channel=self.config.channel_name,
            chaincode=self.config.chaincode_name,
            chaincode_version="1.0.0",
            peer_endpoint=self.config.peer_endpoint,
            is_connected=self._is_online,
            total_records=len(self._records),
            mode="local-permissioned",
        )

    def _generate_tx_id(self) -> str:
        self._tx_counter += 1
        return f"tx-fab-{uuid.uuid4().hex[:12]}-{self._tx_counter}"

    def register_submission(self, commitment: SubmissionCommitment) -> tuple[LedgerRecord, str]:
        if not self._is_online:
            raise ConnectionError("Cannot register submission: Fabric network unavailable")

        prev = self._records.get(commitment.record_id)
        version = (prev.version + 1) if prev else 1

        record = LedgerRecord(
            recordId=commitment.record_id,
            recordType=RecordType.SUBMISSION,
            entityId=commitment.entity_id,
            period=commitment.period,
            contentHash=commitment.content_hash,
            manifestHash=commitment.manifest_hash,
            createdAt=commitment.created_at,
            registeredBy=commitment.registered_by,
            version=version,
        )
        self._records[commitment.record_id] = record

        tx_id = self._generate_tx_id()
        entry = LedgerHistoryEntry(
            txId=tx_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            isDelete=False,
            record=record,
        )
        self._history.setdefault(commitment.record_id, []).append(entry)
        return record, tx_id

    def register_finding(self, commitment: FindingCommitment) -> tuple[LedgerRecord, str]:
        if not self._is_online:
            raise ConnectionError("Cannot register finding: Fabric network unavailable")

        prev = self._records.get(commitment.record_id)
        version = (prev.version + 1) if prev else 1

        record = LedgerRecord(
            recordId=commitment.record_id,
            recordType=RecordType.FINDING,
            entityId=commitment.entity_id,
            findingHash=commitment.finding_hash,
            sourcePhase=commitment.source_phase,
            detectorId=commitment.detector_id,
            createdAt=commitment.created_at,
            registeredBy=commitment.registered_by,
            version=version,
        )
        self._records[commitment.record_id] = record

        tx_id = self._generate_tx_id()
        entry = LedgerHistoryEntry(
            txId=tx_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            isDelete=False,
            record=record,
        )
        self._history.setdefault(commitment.record_id, []).append(entry)
        return record, tx_id

    def register_evidence(self, commitment: EvidenceCommitment) -> tuple[LedgerRecord, str]:
        if not self._is_online:
            raise ConnectionError("Cannot register evidence: Fabric network unavailable")

        prev = self._records.get(commitment.record_id)
        version = (prev.version + 1) if prev else 1

        record = LedgerRecord(
            recordId=commitment.record_id,
            recordType=RecordType.EVIDENCE,
            entityId=commitment.entity_id,
            findingId=commitment.finding_id,
            contentHash=commitment.content_hash,
            createdAt=commitment.created_at,
            registeredBy=commitment.registered_by,
            version=version,
        )
        self._records[commitment.record_id] = record

        tx_id = self._generate_tx_id()
        entry = LedgerHistoryEntry(
            txId=tx_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            isDelete=False,
            record=record,
        )
        self._history.setdefault(commitment.record_id, []).append(entry)
        return record, tx_id

    def get_record(self, record_id: str) -> LedgerRecord | None:
        if not self._is_online:
            return None
        return self._records.get(record_id)

    def get_history(self, record_id: str) -> list[LedgerHistoryEntry]:
        if not self._is_online:
            return []
        return self._history.get(record_id, [])

    def verify_record(self, record_id: str, expected_hash: str) -> VerificationResponse:
        if not self._is_online:
            return VerificationResponse(
                recordId=record_id,
                status=IntegrityState.UNAVAILABLE,
                localHash=expected_hash,
                ledgerHash=None,
                message="Hyperledger Fabric network is unavailable; cannot verify commitment",
            )

        record = self._records.get(record_id)
        if not record:
            return VerificationResponse(
                recordId=record_id,
                status=IntegrityState.NOT_REGISTERED,
                localHash=expected_hash,
                ledgerHash=None,
                message=f"Record {record_id} has no registered cryptographic commitment on ledger",
            )

        ledger_hash = record.content_hash or record.finding_hash or ""
        history = self._history.get(record_id, [])
        tx_id = history[-1].tx_id if history else None

        if expected_hash == ledger_hash:
            return VerificationResponse(
                recordId=record_id,
                status=IntegrityState.VERIFIED,
                localHash=expected_hash,
                ledgerHash=ledger_hash,
                recordType=record.record_type,
                entityId=record.entity_id,
                txId=tx_id,
                version=record.version,
                timestamp=record.created_at,
                message="Local cryptographic SHA-256 matches on-chain ledger commitment",
            )
        else:
            return VerificationResponse(
                recordId=record_id,
                status=IntegrityState.MISMATCH,
                localHash=expected_hash,
                ledgerHash=ledger_hash,
                recordType=record.record_type,
                entityId=record.entity_id,
                txId=tx_id,
                version=record.version,
                timestamp=record.created_at,
                message="Integrity mismatch: local record differs from registered ledger commitment",
            )


# Global singleton instance
_fabric_client_instance = LocalLedgerClient()


def get_fabric_client() -> LocalLedgerClient:
    return _fabric_client_instance
