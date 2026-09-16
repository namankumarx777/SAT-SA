from __future__ import annotations

from typing import Any
from app.blockchain.fabric_client import get_fabric_client
from app.blockchain.hashing import hash_evidence, hash_finding, hash_submission_directory
from app.blockchain.models import IntegrityState, VerificationResponse


def verify_content_integrity(
    record_id: str,
    content_data: dict[str, Any] | bytes | str,
    record_type: str = "FINDING",
) -> VerificationResponse:
    """Convenience helper to hash content and verify against on-chain Fabric commitment."""
    client = get_fabric_client()
    if record_type.upper() == "FINDING" and isinstance(content_data, dict):
        calculated_hash = hash_finding(content_data)
    elif record_type.upper() == "EVIDENCE" and isinstance(content_data, dict):
        calculated_hash = hash_evidence(content_data)
    elif isinstance(content_data, bytes):
        import hashlib
        calculated_hash = hashlib.sha256(content_data).hexdigest()
    elif isinstance(content_data, str):
        calculated_hash = content_data
    else:
        raise ValueError(f"Unsupported content_data type: {type(content_data)}")

    return client.verify_record(record_id, calculated_hash)
