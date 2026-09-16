from __future__ import annotations

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class RecordType(str, Enum):
    SUBMISSION = "SUBMISSION"
    FINDING = "FINDING"
    EVIDENCE = "EVIDENCE"


class IntegrityState(str, Enum):
    VERIFIED = "VERIFIED"
    MISMATCH = "MISMATCH"
    NOT_REGISTERED = "NOT_REGISTERED"
    UNAVAILABLE = "UNAVAILABLE"


class SubmissionCommitment(BaseModel):
    record_id: str = Field(..., alias="recordId")
    record_type: RecordType = Field(RecordType.SUBMISSION, alias="recordType")
    entity_id: str = Field(..., alias="entityId")
    period: str
    content_hash: str = Field(..., alias="contentHash")
    manifest_hash: str = Field(..., alias="manifestHash")
    created_at: str = Field(..., alias="createdAt")
    registered_by: str = Field("SENTRA", alias="registeredBy")
    version: int = 1

    model_config = {"populate_by_name": True}


class FindingCommitment(BaseModel):
    record_id: str = Field(..., alias="recordId")
    record_type: RecordType = Field(RecordType.FINDING, alias="recordType")
    entity_id: str = Field(..., alias="entityId")
    finding_hash: str = Field(..., alias="findingHash")
    source_phase: str = Field(..., alias="sourcePhase")
    detector_id: str = Field(..., alias="detectorId")
    created_at: str = Field(..., alias="createdAt")
    registered_by: str = Field("SENTRA", alias="registeredBy")
    version: int = 1

    model_config = {"populate_by_name": True}


class EvidenceCommitment(BaseModel):
    record_id: str = Field(..., alias="recordId")
    record_type: RecordType = Field(RecordType.EVIDENCE, alias="recordType")
    entity_id: str = Field(..., alias="entityId")
    finding_id: str = Field(..., alias="findingId")
    content_hash: str = Field(..., alias="contentHash")
    created_at: str = Field(..., alias="createdAt")
    registered_by: str = Field("SENTRA", alias="registeredBy")
    version: int = 1

    model_config = {"populate_by_name": True}


class LedgerRecord(BaseModel):
    record_id: str = Field(..., alias="recordId")
    record_type: RecordType = Field(..., alias="recordType")
    entity_id: str = Field(..., alias="entityId")
    content_hash: str | None = Field(default=None, alias="contentHash")
    finding_hash: str | None = Field(default=None, alias="findingHash")
    manifest_hash: str | None = Field(default=None, alias="manifestHash")
    finding_id: str | None = Field(default=None, alias="findingId")
    source_phase: str | None = Field(default=None, alias="sourcePhase")
    detector_id: str | None = Field(default=None, alias="detectorId")
    period: str | None = None
    created_at: str = Field(..., alias="createdAt")
    registered_by: str = Field("SENTRA", alias="registeredBy")
    version: int = 1

    model_config = {"populate_by_name": True}


class VerificationResponse(BaseModel):
    record_id: str = Field(..., alias="recordId")
    status: IntegrityState
    local_hash: str = Field(..., alias="localHash")
    ledger_hash: str | None = Field(default=None, alias="ledgerHash")
    record_type: RecordType | None = Field(default=None, alias="recordType")
    entity_id: str | None = Field(default=None, alias="entityId")
    tx_id: str | None = Field(default=None, alias="txId")
    version: int | None = None
    timestamp: str | None = None
    message: str

    model_config = {"populate_by_name": True}


class LedgerHistoryEntry(BaseModel):
    tx_id: str = Field(..., alias="txId")
    timestamp: str
    is_delete: bool = Field(False, alias="isDelete")
    record: LedgerRecord | None = None

    model_config = {"populate_by_name": True}


class BlockchainStatus(BaseModel):
    status: str
    network: str
    channel: str
    chaincode: str
    chaincode_version: str = "1.0.0"
    peer_endpoint: str
    is_connected: bool
    total_records: int = 0
    mode: str = "local-permissioned"
