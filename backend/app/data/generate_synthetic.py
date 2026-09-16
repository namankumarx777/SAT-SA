from __future__ import annotations

import argparse
import random
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, TypeVar

import polars as pl
from pydantic import BaseModel

from app.schemas.alert import Alert
from app.schemas.asset import Asset
from app.schemas.case import Case
from app.schemas.entity import Entity
from app.schemas.escalation import Escalation


SEED = 42
ENTITIES = 12
MIN_ASSETS_PER_ENTITY = 40
MAX_ASSETS_PER_ENTITY = 80
ALERTS = 10_000
OUTPUT_DIR = Path(__file__).resolve().parents[3] / "data" / "synthetic"

SECTORS = ["Energy", "Banking", "Telecom", "Transport", "Government"]
SIZES = ["Small", "Medium", "Large"]
CRITICALITIES = ["Low", "Medium", "High", "Critical"]
ALERT_SEVERITIES = ["Low", "Medium", "High", "Critical"]
ALERT_SOURCES = ["EDR", "Firewall", "IAM", "IDS", "Email Security", "Cloud Security"]
ASSET_TYPES = ["Server", "Database", "Endpoint", "Network Device", "Application", "Cloud Resource"]
DISPOSITIONS = ["True Positive", "False Positive", "Benign", "Duplicate"]
ESCALATION_TYPES = ["Management", "Incident Response", "Critical Infrastructure", "External Coordination"]

# Generator-only controls. They are intentionally absent from the output files.
EXECUTION_GAP_ENTITIES = {"CSE-004", "CSE-011"}
NEGATIVE_SPACE_ENTITIES = {"CSE-007", "CSE-008"}
INVESTIGATION_TEMPLATE_ENTITIES = {"CSE-005", "CSE-009"}
PEER_DEVIATION_ENTITIES = {"CSE-003", "CSE-010"}

GROUND_TRUTH_ENTITY_SETS = {
    "execution_gap": EXECUTION_GAP_ENTITIES,
    "negative_space": NEGATIVE_SPACE_ENTITIES,
    "investigation_template": INVESTIGATION_TEMPLATE_ENTITIES,
    "peer_deviation": PEER_DEVIATION_ENTITIES,
}

# Stable profiles create comparable cohorts while retaining varied names and inventories.
ENTITY_PROFILES = {
    "CSE-001": ("Energy", "Medium", "Medium"),
    "CSE-002": ("Banking", "Small", "Medium"),
    "CSE-003": ("Telecom", "Small", "Medium"),
    "CSE-004": ("Transport", "Medium", "High"),
    "CSE-005": ("Government", "Large", "Medium"),
    "CSE-006": ("Energy", "Medium", "Medium"),
    "CSE-007": ("Banking", "Large", "High"),
    "CSE-008": ("Telecom", "Small", "Medium"),
    "CSE-009": ("Government", "Large", "Medium"),
    "CSE-010": ("Government", "Large", "Medium"),
    "CSE-011": ("Energy", "Medium", "Medium"),
    "CSE-012": ("Telecom", "Small", "Medium"),
}

ASSET_COUNT_RANGES = {
    ("Energy", "Medium", "Medium"): (52, 62),
    ("Banking", "Small", "Medium"): (46, 56),
    ("Telecom", "Small", "Medium"): (52, 62),
    ("Transport", "Medium", "High"): (58, 70),
    ("Government", "Large", "Medium"): (58, 68),
    ("Banking", "Large", "High"): (64, 76),
}

START = datetime(2025, 1, 1)
END = datetime(2025, 6, 30, 23, 59)
ModelT = TypeVar("ModelT", bound=BaseModel)


def random_datetime(rng: random.Random, start: datetime, end: datetime) -> datetime:
    """Return a deterministic timestamp in the inclusive interval."""
    seconds = int((end - start).total_seconds())
    return start + timedelta(seconds=rng.randint(0, seconds))


def later_datetime(rng: random.Random, start: datetime, minimum_minutes: int, maximum_minutes: int) -> datetime:
    """Return a timestamp after start, bounded to the generation window."""
    candidate = start + timedelta(minutes=rng.randint(minimum_minutes, maximum_minutes))
    return min(candidate, END)


def validate_models(rows: list[dict[str, Any]], model: type[ModelT]) -> list[dict[str, Any]]:
    """Validate generated dictionaries and return model data."""
    return [model.model_validate(row).model_dump() for row in rows]


def validate_configuration(entity_count: int, alert_count: int) -> None:
    """Reject configurations that cannot produce a valid ground-truth dataset."""
    required_entity_count = max(int(entity_id.split("-")[1]) for entity_ids in GROUND_TRUTH_ENTITY_SETS.values() for entity_id in entity_ids)
    if entity_count < required_entity_count:
        raise ValueError(f"--entities must be at least {required_entity_count} to include all ground-truth entities")
    if alert_count <= 0:
        raise ValueError("--alerts must be greater than zero")


def validate_ground_truth_entities(entity_ids: set[str]) -> None:
    """Ensure every validation-only ground-truth entity exists in the dataset."""
    missing = {
        entity_id
        for entity_set in GROUND_TRUTH_ENTITY_SETS.values()
        for entity_id in entity_set
        if entity_id not in entity_ids
    }
    if missing:
        raise ValueError(f"Missing ground-truth entities: {sorted(missing)}")


def generate_entities(count: int, rng: random.Random) -> pl.DataFrame:
    """Generate CSE records with stable IDs and varied operating profiles."""
    rows = []
    for number in range(1, count + 1):
        entity_id = f"CSE-{number:03d}"
        if entity_id in ENTITY_PROFILES:
            sector, size, criticality = ENTITY_PROFILES[entity_id]
        else:
            sector = rng.choice(SECTORS)
            size = rng.choices(SIZES, weights=[3, 5, 2])[0]
            criticality = rng.choices(CRITICALITIES, weights=[1, 3, 4, 2])[0]
        rows.append(
            {
                "id": entity_id,
                "name": f"{rng.choice(['North', 'Central', 'Eastern', 'Western'])} {rng.choice(['Grid', 'Holdings', 'Networks', 'Authority'])} {number:02d}",
                "sector": sector,
                "size": size,
                "criticality": criticality,
                "created_at": random_datetime(rng, datetime(2018, 1, 1), datetime(2022, 12, 31)),
            }
        )
    return pl.DataFrame(validate_models(rows, Entity))


def generate_assets(entities: pl.DataFrame, rng: random.Random, minimum: int, maximum: int) -> pl.DataFrame:
    """Generate one-to-many asset inventories with monitored high-value assets."""
    rows = []
    asset_number = 1
    entity_profiles = {row["id"]: (row["sector"], row["size"], row["criticality"]) for row in entities.to_dicts()}
    for entity_id in entities["id"].to_list():
        count = rng.randint(*ASSET_COUNT_RANGES.get(entity_profiles[entity_id], (minimum, maximum)))
        for _ in range(count):
            asset_type = rng.choices(ASSET_TYPES, weights=[25, 12, 30, 12, 15, 6])[0]
            criticality = rng.choices(CRITICALITIES, weights=[35, 35, 22, 8])[0]
            expected = criticality in {"High", "Critical"} or rng.random() < 0.45
            rows.append(
                {
                    "id": f"AST-{asset_number:06d}",
                    "entity_id": entity_id,
                    "asset_type": asset_type,
                    "criticality": criticality,
                    "expected_monitoring": expected,
                    "monitoring_source": rng.choice(ALERT_SOURCES) if expected else None,
                }
            )
            asset_number += 1
    return pl.DataFrame(validate_models(rows, Asset))


def _investigation_text(entity_id: str, rng: random.Random, severity: str) -> str:
    if entity_id in INVESTIGATION_TEMPLATE_ENTITIES:
        subject = rng.choice(["authentication", "endpoint", "network", "email"])
        context = rng.choice(["the affected host", "the user account", "the reported mailbox", "the network segment"])
        result = rng.choice(["no malicious activity was observed", "no indicator of compromise was identified", "the activity appeared consistent with expected operations"])
        return rng.choice([
            f"Reviewed {subject} activity for {context}. {result.capitalize()}.",
            f"Analyst reviewed {subject} logs and confirmed that {result}.",
            f"Checked {subject} telemetry for {context}; {result}.",
        ])

    observations = [
        "The initial signal was associated with a scheduled administrative task",
        "The alert involved an unusual authentication pattern",
        "The affected asset showed a short burst of process activity",
        "The reported message matched a known security-control trigger",
        "The network event originated from an approved service account",
        "The event was correlated with a recent configuration change",
    ]
    actions = [
        "Reviewed endpoint process activity and recent authentication records",
        "Compared firewall events with identity and asset-owner records",
        "Examined the related email headers and neighboring alerts",
        "Checked the cloud audit trail and recent administrative changes",
        "Correlated the detection with host, network, and user telemetry",
        "Reviewed the alert history and contacted the responsible service owner",
    ]
    evidence = [
        "No persistence mechanism or suspicious follow-on activity was identified",
        "The observed account activity matched the approved maintenance window",
        "No additional indicators were found in the surrounding telemetry",
        "The destination, process lineage, and source identity were consistent with policy",
        "Related events did not show lateral movement or privilege escalation",
        "The evidence supported a benign explanation for the detection",
    ]
    conclusions = [
        "The alert was classified as benign and documented for audit purposes",
        "The activity was closed as a false positive after evidence review",
        "The event was retained as a true positive and routed for follow-up",
        "The alert was marked as a duplicate of an existing investigation",
        "The case was closed with no further containment required",
    ]
    follow_ups = [
        "The asset owner was notified and no remediation was required",
        "A detection-tuning note was recorded for future review",
        "The relevant evidence was attached to the case record",
        "The analyst requested confirmation from the system owner",
        "Follow-up monitoring was scheduled for the next review period",
    ]
    if entity_id in EXECUTION_GAP_ENTITIES and severity in {"High", "Critical"}:
        actions = [
            "Reviewed the alert summary and checked the affected asset",
            "Validated the detection against the available event context",
            "Checked the recent alert history for related activity",
        ]
        evidence = [
            "No immediate additional activity was observed",
            "The available context did not show a confirmed compromise",
            "The signal appeared consistent with an expected operation",
        ]
    return (
        f"{rng.choice(observations)}. {rng.choice(actions)}. "
        f"{rng.choice(evidence)}. {rng.choice(conclusions)}. {rng.choice(follow_ups)}."
    )


def generate_alerts_and_cases(entities: pl.DataFrame, assets: pl.DataFrame, alert_count: int, rng: random.Random) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Generate correlated alerts and cases, including subtle entity-level patterns."""
    entity_ids = entities["id"].to_list()
    assets_by_entity: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for asset in assets.to_dicts():
        assets_by_entity[asset["entity_id"]].append(asset)

    entity_weights = {entity_id: rng.uniform(0.75, 1.25) for entity_id in entity_ids}
    alerts: list[dict[str, Any]] = []
    cases: list[dict[str, Any]] = []

    for alert_number in range(1, alert_count + 1):
        entity_id = rng.choices(entity_ids, weights=[entity_weights[item] for item in entity_ids])[0]
        candidates = assets_by_entity[entity_id]
        if entity_id in NEGATIVE_SPACE_ENTITIES:
            candidates = [asset for asset in candidates if not (
                asset["criticality"] in {"High", "Critical"}
                and (asset["asset_type"] in {"Cloud Resource", "Database"} or asset["id"][-1] in {"0", "1", "2"})
            )] or candidates
        asset = rng.choice(candidates)
        source = asset["monitoring_source"] or rng.choice(ALERT_SOURCES)
        if entity_id in NEGATIVE_SPACE_ENTITIES and source == "Cloud Security":
            source = rng.choice(["EDR", "Firewall", "IAM", "IDS", "Email Security"])
        severity = rng.choices(ALERT_SEVERITIES, weights=[62, 27, 9, 2])[0]
        timestamp = random_datetime(rng, START, END - timedelta(days=2))
        acknowledged = None if rng.random() < 0.08 else later_datetime(rng, timestamp, 2, 240)
        alert_id = f"ALT-{alert_number:06d}"
        alert = {
            "id": alert_id, "entity_id": entity_id, "asset_id": asset["id"],
            "timestamp": timestamp, "severity": severity, "source": source,
            "acknowledged_at": acknowledged, "closed_at": None, "status": "Open", "case_id": None,
        }
        make_case = rng.random() < (0.34 if severity in {"High", "Critical"} else 0.20)
        if make_case:
            opened = max(timestamp, acknowledged or timestamp) + timedelta(minutes=rng.randint(1, 90))
            gap_entity = entity_id in EXECUTION_GAP_ENTITIES
            peer_deviation = entity_id in PEER_DEVIATION_ENTITIES
            if severity == "Critical" and not gap_entity and not peer_deviation:
                investigation_minutes = rng.randint(25, 50)
            elif severity in {"High", "Critical"} and (gap_entity or peer_deviation):
                investigation_minutes = rng.randint(5, 15)
            else:
                investigation_minutes = rng.randint(15, 180)
            rapid_critical_scenario = (
                severity == "Critical"
                and entity_id in EXECUTION_GAP_ENTITIES
                and alert_number % 4 == 0
            )
            if rapid_critical_scenario:
                case_closed = later_datetime(rng, opened, 5, 9)
            else:
                case_closed = None if rng.random() < 0.12 else later_datetime(rng, opened, investigation_minutes, investigation_minutes + 120)
            case_id = f"CASE-{len(cases) + 1:06d}"
            escalated = severity in {"High", "Critical"} and rng.random() < (0.32 if gap_entity else 0.68)
            if peer_deviation:
                escalated = severity in {"High", "Critical"} and rng.random() < 0.35
            case = {
                "id": case_id, "entity_id": entity_id, "alert_id": alert_id,
                "opened_at": opened, "closed_at": case_closed,
                "investigation_text": _investigation_text(entity_id, rng, severity),
                "disposition": rng.choices(DISPOSITIONS, weights=[28, 38, 24, 10])[0],
                "escalated": escalated, "remediation_recorded": rng.random() < (0.72 if not gap_entity else 0.45),
            }
            cases.append(case)
            alert["case_id"] = case_id
            if case_closed is not None:
                alert["closed_at"] = later_datetime(rng, case_closed, 1, 45)
                alert["status"] = "Closed"
            else:
                alert["status"] = "Acknowledged" if acknowledged else "Open"
        elif acknowledged is not None and rng.random() < 0.72:
            alert["closed_at"] = later_datetime(rng, acknowledged, 5, 720)
            alert["status"] = "Closed"
        elif acknowledged is not None:
            alert["status"] = "Acknowledged"
        alerts.append(alert)

    return pl.DataFrame(validate_models(alerts, Alert)), pl.DataFrame(validate_models(cases, Case))


def generate_escalations(cases: pl.DataFrame, rng: random.Random) -> pl.DataFrame:
    """Generate one escalation for each escalated case with valid chronology."""
    rows = []
    for number, case in enumerate(cases.filter(pl.col("escalated")).to_dicts(), 1):
        escalation_time = later_datetime(rng, case["opened_at"], 5, 240)
        if case["closed_at"] is not None:
            escalation_time = min(escalation_time, case["closed_at"])
        rows.append({
            "id": f"ESC-{number:06d}", "entity_id": case["entity_id"], "case_id": case["id"],
            "created_at": escalation_time,
            "escalation_type": rng.choice(ESCALATION_TYPES),
        })
    return pl.DataFrame(validate_models(rows, Escalation))


def validate_datasets(entities: pl.DataFrame, assets: pl.DataFrame, alerts: pl.DataFrame, cases: pl.DataFrame, escalations: pl.DataFrame) -> None:
    """Raise ValueError if relational, categorical, or temporal integrity is violated."""
    entity_ids = set(entities["id"].to_list())
    asset_map = {row["id"]: row["entity_id"] for row in assets.to_dicts()}
    alert_map = {row["id"]: row for row in alerts.to_dicts()}
    case_map = {row["id"]: row for row in cases.to_dicts()}
    if (
        len(entity_ids) != entities.height
        or any(frame["id"].n_unique() != frame.height for frame in (assets, alerts, cases, escalations))
    ):
        raise ValueError("IDs must be unique")
    if (
        not set(entities["sector"].to_list()) <= set(SECTORS)
        or not set(entities["size"].to_list()) <= set(SIZES)
        or not set(entities["criticality"].to_list()) <= set(CRITICALITIES)
        or not set(assets["asset_type"].to_list()) <= set(ASSET_TYPES)
        or not set(assets["criticality"].to_list()) <= set(CRITICALITIES)
        or not set(alerts["severity"].to_list()) <= set(ALERT_SEVERITIES)
        or not set(alerts["source"].to_list()) <= set(ALERT_SOURCES)
        or not set(alerts["status"].to_list()) <= {"Open", "Acknowledged", "Closed"}
        or not set(cases["disposition"].to_list()) <= set(DISPOSITIONS)
        or not set(escalations["escalation_type"].to_list()) <= set(ESCALATION_TYPES)
    ):
        raise ValueError("Invalid categorical value")
    if any(row["entity_id"] not in entity_ids for row in assets.to_dicts()):
        raise ValueError("Orphan asset entity")
    for row in alerts.to_dicts():
        if row["entity_id"] not in entity_ids or asset_map.get(row["asset_id"]) != row["entity_id"]:
            raise ValueError("Invalid alert relationship")
        if row["case_id"] is not None and row["case_id"] not in case_map:
            raise ValueError("Alert references missing case")
        if row["acknowledged_at"] and row["acknowledged_at"] < row["timestamp"]:
            raise ValueError("Invalid alert acknowledgement timestamp")
        if row["closed_at"] and row["acknowledged_at"] and row["closed_at"] < row["acknowledged_at"]:
            raise ValueError("Invalid alert closure timestamp")
    for row in cases.to_dicts():
        alert = alert_map.get(row["alert_id"])
        if not alert or row["entity_id"] != alert["entity_id"] or alert["case_id"] != row["id"] or row["opened_at"] < alert["timestamp"]:
            raise ValueError("Invalid case relationship or opening timestamp")
        if row["closed_at"] and row["closed_at"] < row["opened_at"]:
            raise ValueError("Invalid case closure timestamp")
    escalation_case_ids = set()
    for row in escalations.to_dicts():
        case = case_map.get(row["case_id"])
        if not case or row["entity_id"] != case["entity_id"] or row["created_at"] < case["opened_at"]:
            raise ValueError("Invalid escalation relationship or timestamp")
        if not case["escalated"] or (case["closed_at"] is not None and row["created_at"] > case["closed_at"]):
            raise ValueError("Escalation does not match case lifecycle")
        escalation_case_ids.add(row["case_id"])
    if escalation_case_ids != {row["id"] for row in cases.filter(pl.col("escalated")).to_dicts()}:
        raise ValueError("Escalated cases and escalation rows differ")


def write_outputs(datasets: dict[str, pl.DataFrame], output_dir: Path) -> None:
    """Write the five canonical datasets as Parquet files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in datasets.items():
        frame.write_parquet(output_dir / f"{name}.parquet")


def generate_dataset(entity_count: int, alert_count: int, seed: int, output_dir: Path) -> dict[str, pl.DataFrame]:
    """Generate, validate, and write one deterministic synthetic dataset."""
    validate_configuration(entity_count, alert_count)
    rng = random.Random(seed)
    entities = generate_entities(entity_count, rng)
    validate_ground_truth_entities(set(entities["id"].to_list()))
    assets = generate_assets(entities, rng, MIN_ASSETS_PER_ENTITY, MAX_ASSETS_PER_ENTITY)
    alerts, cases = generate_alerts_and_cases(entities, assets, alert_count, rng)
    escalations = generate_escalations(cases, rng)
    datasets = {"entities": entities, "assets": assets, "alerts": alerts, "cases": cases, "escalations": escalations}
    validate_datasets(entities, assets, alerts, cases, escalations)
    write_outputs(datasets, output_dir)
    return datasets


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate the SENTRA synthetic SOC dataset.")
    parser.add_argument("--entities", type=int, default=ENTITIES)
    parser.add_argument("--alerts", type=int, default=ALERTS)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--output", type=Path, default=OUTPUT_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    datasets = generate_dataset(args.entities, args.alerts, args.seed, args.output)
    print("SENTRA Synthetic Dataset")
    for name, frame in datasets.items():
        print(f"{name.capitalize()}: {frame.height}")
    print("Validation: [OK] relationships, IDs, categories, and timestamps")
    print(f"Output: {args.output}")
    entity_ids = set(datasets["entities"]["id"].to_list())
    print(f"Ground Truth: execution gap {len(EXECUTION_GAP_ENTITIES & entity_ids)}, negative space {len(NEGATIVE_SPACE_ENTITIES & entity_ids)}, investigation templates {len(INVESTIGATION_TEMPLATE_ENTITIES & entity_ids)}, peer deviation {len(PEER_DEVIATION_ENTITIES & entity_ids)}")


if __name__ == "__main__":
    main()

    