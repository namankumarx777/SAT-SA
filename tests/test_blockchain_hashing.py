from __future__ import annotations

import json
import tempfile
from pathlib import Path

from app.blockchain.hashing import (
    canonical_json_dumps,
    canonicalize_evidence,
    canonicalize_finding,
    hash_bytes,
    hash_evidence,
    hash_file,
    hash_finding,
    hash_string,
    hash_submission_directory,
)


def test_canonical_json_dumps_key_invariance():
    obj_a = {"z": 100, "a": "hello", "m": [3, 2, 1], "nested": {"k2": "v2", "k1": "v1"}}
    obj_b = {"nested": {"k1": "v1", "k2": "v2"}, "a": "hello", "m": [3, 2, 1], "z": 100}

    dump_a = canonical_json_dumps(obj_a)
    dump_b = canonical_json_dumps(obj_b)

    assert dump_a == dump_b
    assert hash_string(dump_a) == hash_string(dump_b)


def test_hash_finding_determinism():
    finding_1 = {
        "id": "F-EG002-CSE-011",
        "rule_id": "EG002",
        "entity_id": "CSE-011",
        "severity": "HIGH",
        "metric_name": "escalation_execution_delay_hours",
        "observed_value": 74.5,
        "expected_value": 24.0,
        "rationale": "Severe gap between alert escalation and ticket creation.",
        "extra_ui_field_that_should_not_affect_hash": "custom_color_blue",
    }
    finding_2 = {
        "entity_id": "CSE-011",
        "expected_value": 24.0,
        "finding_id": "F-EG002-CSE-011",
        "metric_name": "escalation_execution_delay_hours",
        "observed_value": 74.5,
        "rationale": "Severe gap between alert escalation and ticket creation.",
        "rule_id": "EG002",
        "severity": "HIGH",
    }

    hash_1 = hash_finding(finding_1)
    hash_2 = hash_finding(finding_2)

    assert hash_1 == hash_2
    assert len(hash_1) == 64  # Valid SHA-256 hex string


def test_hash_finding_tamper_detection():
    finding_original = {
        "id": "F-EG002-CSE-011",
        "rule_id": "EG002",
        "entity_id": "CSE-011",
        "severity": "HIGH",
        "metric_name": "escalation_execution_delay_hours",
        "observed_value": 74.5,
        "expected_value": 24.0,
        "rationale": "Severe gap between alert escalation and ticket creation.",
    }
    finding_tampered = dict(finding_original)
    finding_tampered["observed_value"] = 12.0  # Tampered down to normal

    hash_orig = hash_finding(finding_original)
    hash_tamp = hash_finding(finding_tampered)

    assert hash_orig != hash_tamp


def test_hash_evidence_determinism():
    ev_1 = {
        "finding_id": "F-EG002-CSE-011",
        "source_type": "escalation",
        "source_id": "ESC-9081",
        "entity_id": "CSE-011",
        "field": "execution_delay",
        "value": "74.5 hours",
        "reason": "Exceeds 24-hour threshold",
    }
    ev_2 = {
        "value": "74.5 hours",
        "source_type": "escalation",
        "reason": "Exceeds 24-hour threshold",
        "source_id": "ESC-9081",
        "field": "execution_delay",
        "finding_id": "F-EG002-CSE-011",
        "entity_id": "CSE-011",
    }

    assert hash_evidence(ev_1) == hash_evidence(ev_2)


def test_hash_submission_directory_deterministic():
    with tempfile.TemporaryDirectory() as tmpdir:
        p = Path(tmpdir)
        (p / "entities.parquet").write_bytes(b"entities_sample_content_123")
        (p / "alerts.parquet").write_bytes(b"alerts_sample_content_456")
        (p / "manifest.json").write_text(json.dumps({"version": "1.0", "cse": "CSE-011"}))

        result_1 = hash_submission_directory(p)
        result_2 = hash_submission_directory(p)

        assert result_1["content_hash"] == result_2["content_hash"]
        assert result_1["manifest_hash"] == result_2["manifest_hash"]
        assert len(result_1["content_hash"]) == 64
