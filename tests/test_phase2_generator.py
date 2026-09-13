from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import polars as pl
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.data.generate_synthetic import (  # noqa: E402
    ALERTS,
    EXECUTION_GAP_ENTITIES,
    GROUND_TRUTH_ENTITY_SETS,
    INVESTIGATION_TEMPLATE_ENTITIES,
    NEGATIVE_SPACE_ENTITIES,
    PEER_DEVIATION_ENTITIES,
    SEED,
    generate_dataset,
)

EXPECTED_SOURCES = {"EDR", "Firewall", "IAM", "IDS", "Email Security", "Cloud Security"}


@pytest.fixture(scope="session")
def dataset(tmp_path_factory: pytest.TempPathFactory) -> dict[str, pl.DataFrame]:
    output_dir = tmp_path_factory.mktemp("synthetic")
    return generate_dataset(12, ALERTS, SEED, output_dir)


def test_generator_writes_all_parquet_files(dataset: dict[str, pl.DataFrame], tmp_path: Path) -> None:
    output_dir = tmp_path / "outputs"
    generated = generate_dataset(12, 250, SEED, output_dir)
    assert set(generated) == {"entities", "assets", "alerts", "cases", "escalations"}
    assert {path.name for path in output_dir.glob("*.parquet")} == {
        "entities.parquet", "assets.parquet", "alerts.parquet", "cases.parquet", "escalations.parquet",
    }


def test_same_seed_produces_identical_parquet(dataset: dict[str, pl.DataFrame], tmp_path: Path) -> None:
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    generate_dataset(12, 500, SEED, first_dir)
    generate_dataset(12, 500, SEED, second_dir)
    for first in sorted(first_dir.glob("*.parquet")):
        second = second_dir / first.name
        assert hashlib.sha256(first.read_bytes()).digest() == hashlib.sha256(second.read_bytes()).digest()


def test_all_ground_truth_entities_exist(dataset: dict[str, pl.DataFrame]) -> None:
    entity_ids = set(dataset["entities"]["id"].to_list())
    assert set().union(*GROUND_TRUTH_ENTITY_SETS.values()) <= entity_ids


def test_relational_integrity(dataset: dict[str, pl.DataFrame]) -> None:
    entities, assets, alerts, cases, escalations = (dataset[name] for name in dataset)
    entity_ids = set(entities["id"].to_list())
    asset_entities = dict(zip(assets["id"].to_list(), assets["entity_id"].to_list()))
    alert_entities = dict(zip(alerts["id"].to_list(), alerts["entity_id"].to_list()))
    case_entities = dict(zip(cases["id"].to_list(), cases["entity_id"].to_list()))
    assert set(assets["entity_id"].to_list()) <= entity_ids
    assert set(alerts["entity_id"].to_list()) <= entity_ids
    assert all(asset_entities[row["asset_id"]] == row["entity_id"] for row in alerts.to_dicts())
    assert all(row["entity_id"] in entity_ids and alert_entities[row["alert_id"]] == row["entity_id"] for row in cases.to_dicts())
    assert all(row["entity_id"] in entity_ids and case_entities[row["case_id"]] == row["entity_id"] for row in escalations.to_dicts())


def test_temporal_integrity(dataset: dict[str, pl.DataFrame]) -> None:
    alerts = {row["id"]: row for row in dataset["alerts"].to_dicts()}
    cases = {row["id"]: row for row in dataset["cases"].to_dicts()}
    for alert in alerts.values():
        if alert["acknowledged_at"] is not None:
            assert alert["timestamp"] <= alert["acknowledged_at"]
        if alert["closed_at"] is not None and alert["acknowledged_at"] is not None:
            assert alert["acknowledged_at"] <= alert["closed_at"]
    for case in cases.values():
        alert = alerts[case["alert_id"]]
        assert alert["timestamp"] <= case["opened_at"]
        if alert["acknowledged_at"] is not None:
            assert alert["acknowledged_at"] <= case["opened_at"]
        if case["closed_at"] is not None:
            assert case["opened_at"] <= case["closed_at"]
    for escalation in dataset["escalations"].to_dicts():
        case = cases[escalation["case_id"]]
        assert case["opened_at"] <= escalation["created_at"]
        if case["closed_at"] is not None:
            assert escalation["created_at"] <= case["closed_at"]


def test_required_source_coverage(dataset: dict[str, pl.DataFrame]) -> None:
    assert set(dataset["alerts"]["source"].unique().to_list()) == EXPECTED_SOURCES


def test_case_variation(dataset: dict[str, pl.DataFrame]) -> None:
    cases = dataset["cases"]
    assert cases["escalated"].any() and (~cases["escalated"]).any()
    assert cases["remediation_recorded"].any() and (~cases["remediation_recorded"]).any()


def test_investigation_diversity(dataset: dict[str, pl.DataFrame]) -> None:
    cases = dataset["cases"]
    assert cases["investigation_text"].n_unique() / cases.height > 0.70
    uniqueness = cases.group_by("entity_id").agg(
        (pl.col("investigation_text").n_unique() / pl.len()).alias("ratio")
    )
    template_ratio = uniqueness.filter(pl.col("entity_id").is_in(list(INVESTIGATION_TEMPLATE_ENTITIES)))["ratio"].mean()
    normal_ratio = uniqueness.filter(~pl.col("entity_id").is_in(list(INVESTIGATION_TEMPLATE_ENTITIES)))["ratio"].mean()
    assert normal_ratio > 0.70
    assert template_ratio < normal_ratio - 0.20


def test_negative_space_is_observable(dataset: dict[str, pl.DataFrame]) -> None:
    activity = dataset["assets"].join(
        dataset["alerts"].group_by("asset_id").len().rename({"len": "alerts"}),
        left_on="id", right_on="asset_id", how="left",
    ).with_columns(pl.col("alerts").fill_null(0))
    gaps = activity.filter(pl.col("expected_monitoring") & (pl.col("alerts") == 0)).group_by("entity_id").len()
    gap_entities = set(gaps.filter(pl.col("len") > 0)["entity_id"].to_list())
    assert NEGATIVE_SPACE_ENTITIES <= gap_entities
    sources = dataset["alerts"].group_by(["entity_id", "source"]).len()
    assert all(sources.filter((pl.col("entity_id") == entity_id) & (pl.col("source") == "Cloud Security")).height == 0 for entity_id in NEGATIVE_SPACE_ENTITIES)


def test_execution_gap_is_observable(dataset: dict[str, pl.DataFrame]) -> None:
    cases = dataset["cases"].join(dataset["alerts"].select(["id", "severity"]), left_on="alert_id", right_on="id")
    critical = cases.filter(pl.col("severity") == "Critical")
    gap_rate = critical.filter(pl.col("entity_id").is_in(list(EXECUTION_GAP_ENTITIES)))["escalated"].cast(pl.Float64).mean()
    normal_rate = critical.filter(~pl.col("entity_id").is_in(list(EXECUTION_GAP_ENTITIES)))["escalated"].cast(pl.Float64).mean()
    assert gap_rate < normal_rate
    assert critical.filter(pl.col("entity_id").is_in(list(EXECUTION_GAP_ENTITIES))).height > 10


def test_peer_cohort_availability(dataset: dict[str, pl.DataFrame]) -> None:
    entities = dataset["entities"]
    assets = dataset["assets"]
    cohorts = entities.group_by(["sector", "size", "criticality"]).len()
    useful = cohorts.filter(pl.col("len") >= 3)
    assert useful.height >= 3
    profiles = entities.select(["id", "sector", "size", "criticality"]).join(assets.group_by("entity_id").len().rename({"len": "assets"}), left_on="id", right_on="entity_id")
    for entity_id in PEER_DEVIATION_ENTITIES:
        target = profiles.filter(pl.col("id") == entity_id).row(0, named=True)
        peers = profiles.filter(
            (pl.col("sector") == target["sector"])
            & (pl.col("size") == target["size"])
            & (pl.col("criticality") == target["criticality"])
            & (pl.col("id") != entity_id)
        )
        assert peers.height >= 2
        assert abs(target["assets"] - peers["assets"].median()) <= 10


def test_peer_deviation_is_observable(dataset: dict[str, pl.DataFrame]) -> None:
    critical = dataset["cases"].join(dataset["alerts"].select(["id", "severity"]), left_on="alert_id", right_on="id").filter(pl.col("severity") == "Critical")
    deviation_rate = critical.filter(pl.col("entity_id").is_in(list(PEER_DEVIATION_ENTITIES)))["escalated"].cast(pl.Float64).mean()
    peer_rate = critical.filter(~pl.col("entity_id").is_in(list(PEER_DEVIATION_ENTITIES)))["escalated"].cast(pl.Float64).mean()
    assert deviation_rate < peer_rate
