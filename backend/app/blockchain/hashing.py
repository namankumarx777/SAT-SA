from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def canonical_json_dumps(obj: Any) -> str:
    """Serialize any JSON-compatible object into a deterministic canonical string.
    
    Keys are sorted, whitespace separators are stripped, and UTF-8 representation
    is guaranteed to be identical across platforms and executions.
    """
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def hash_bytes(data: bytes) -> str:
    """Calculate SHA-256 hex digest of raw bytes."""
    return hashlib.sha256(data).hexdigest()


def hash_string(text: str) -> str:
    """Calculate SHA-256 hex digest of a UTF-8 string."""
    return hash_bytes(text.encode("utf-8"))


def hash_file(file_path: Path | str) -> str:
    """Calculate SHA-256 hex digest of a single file."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"File not found for hashing: {path}")
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


SUBMISSION_CANONICAL_FILES = (
    "entities.parquet",
    "assets.parquet",
    "alerts.parquet",
    "cases.parquet",
    "escalations.parquet",
    "manifest.json",
)


def hash_submission_directory(directory: Path | str) -> dict[str, str]:
    """Compute deterministic SHA-256 digests for a submission directory.
    
    Returns a dict with individual file digests and a overall 'content_hash'
    computed deterministically over the canonical file sequence.
    """
    dir_path = Path(directory)
    if not dir_path.is_dir():
        raise NotADirectoryError(f"Directory not found: {dir_path}")

    file_hashes: dict[str, str] = {}
    for filename in SUBMISSION_CANONICAL_FILES:
        target = dir_path / filename
        if target.is_file():
            file_hashes[filename] = hash_file(target)

    # Compute overall combined content digest across available canonical files in fixed order
    ordered_digests = [
        {"file": filename, "sha256": file_hashes[filename]}
        for filename in SUBMISSION_CANONICAL_FILES
        if filename in file_hashes
    ]

    manifest_hash = file_hashes.get("manifest.json", "")
    canonical_repr = canonical_json_dumps(ordered_digests)
    combined_hash = hash_string(canonical_repr)

    return {
        "content_hash": combined_hash,
        "manifest_hash": manifest_hash,
        "file_hashes": file_hashes,
    }


def canonicalize_finding(finding: dict[str, Any]) -> dict[str, Any]:
    """Extract and normalize canonical identity & integrity fields of a finding."""
    return {
        "entity_id": str(finding.get("entity_id", "")),
        "expected_value": finding.get("expected_value"),
        "finding_id": str(finding.get("id") or finding.get("finding_id", "")),
        "metric_name": str(finding.get("metric_name", "")),
        "observed_value": finding.get("observed_value"),
        "rationale": str(finding.get("rationale", "")),
        "rule_id": str(finding.get("rule_id", "")),
        "severity": str(finding.get("severity", "")),
    }


def hash_finding(finding: dict[str, Any]) -> str:
    """Calculate deterministic SHA-256 digest of a finding."""
    canonical = canonicalize_finding(finding)
    return hash_string(canonical_json_dumps(canonical))


def canonicalize_evidence(evidence: dict[str, Any]) -> dict[str, Any]:
    """Extract and normalize canonical identity & integrity fields of an evidence record."""
    return {
        "entity_id": str(evidence.get("entity_id", "")),
        "field": str(evidence.get("field", "")),
        "finding_id": str(evidence.get("finding_id", "")),
        "reason": str(evidence.get("reason", "")),
        "source_id": str(evidence.get("source_id", "")),
        "source_type": str(evidence.get("source_type", "")),
        "value": str(evidence.get("value", "")),
    }


def hash_evidence(evidence: dict[str, Any]) -> str:
    """Calculate deterministic SHA-256 digest of an evidence record."""
    canonical = canonicalize_evidence(evidence)
    return hash_string(canonical_json_dumps(canonical))
