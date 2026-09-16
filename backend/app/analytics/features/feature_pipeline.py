from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import polars as pl

from app.analytics.features.alert_features import build_alert_features
from app.analytics.features.asset_features import build_asset_features
from app.analytics.features.case_features import build_case_features
from app.analytics.features.entity_features import build_entity_features
from app.analytics.features.schemas import SCHEMA_VERSION, feature_definitions
from app.analytics.features.time_features import build_entity_month_features

DATASET_NAMES = ("entities", "assets", "alerts", "cases", "escalations")
DEFAULT_OUTPUT = Path(__file__).resolve().parents[4] / "data" / "processed" / "phase4-features"


def load_canonical_dataset(input_dir: str | Path) -> dict[str, pl.DataFrame]:
    """Load the five canonical Parquet tables from a Phase 3 run directory."""
    directory = Path(input_dir)
    if not directory.is_dir():
        raise ValueError(f"Canonical input directory not found: {directory}")
    bundle = {}
    missing = []
    for name in DATASET_NAMES:
        path = directory / f"{name}.parquet"
        if not path.is_file():
            missing.append(name)
        else:
            bundle[name] = pl.read_parquet(path)
    if missing:
        raise ValueError(f"Canonical dataset is missing: {', '.join(missing)}")
    return bundle


def build_feature_tables(bundle: dict[str, pl.DataFrame]) -> dict[str, pl.DataFrame]:
    """Derive all Phase 4 operational feature tables without labels or judgements."""
    alerts = build_alert_features(bundle["alerts"])
    cases = build_case_features(bundle["cases"], bundle["escalations"])
    cases = cases.join(
        bundle["alerts"].select(["id", "severity"]).rename({"id": "alert_id"}),
        on="alert_id",
        how="left",
    )
    assets = build_asset_features(bundle["assets"], bundle["alerts"], bundle["cases"])
    entities = build_entity_features(bundle["entities"], alerts, cases, assets)
    entity_month = build_entity_month_features(alerts, cases)
    return {
        "alert_features": alerts,
        "case_features": cases,
        "asset_features": assets,
        "entity_features": entities,
        "entity_month_features": entity_month,
    }


def _manifest(dataset_id: str, input_dir: Path, tables: dict[str, pl.DataFrame]) -> dict[str, object]:
    return {
        "dataset_id": dataset_id,
        "source_dataset": str(input_dir),
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "row_counts": {name: frame.height for name, frame in tables.items()},
        "feature_counts": {name: len(frame.columns) for name, frame in tables.items()},
        "features": feature_definitions(tables),
        "table_columns": {name: frame.columns for name, frame in tables.items()},
        "monthly_semantics": "entity_month_features contains only entity-months with observed alert or case records; absent months are not imputed as zero rows.",
    }


def write_feature_tables(tables: dict[str, pl.DataFrame], output_dir: str | Path, manifest: dict[str, object]) -> None:
    """Write feature Parquet tables and machine-readable manifest."""
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    for name, frame in tables.items():
        frame.write_parquet(destination / f"{name}.parquet")
    (destination / "feature_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def generate_features(input_dir: str | Path, output_dir: str | Path = DEFAULT_OUTPUT, dataset_id: str | None = None) -> dict[str, pl.DataFrame]:
    """Load canonical data, generate deterministic features, and write Parquet outputs."""
    source = Path(input_dir)
    bundle = load_canonical_dataset(source)
    tables = build_feature_tables(bundle)
    manifest = _manifest(dataset_id or source.name, source, tables)
    write_feature_tables(tables, output_dir, manifest)
    return tables


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate SENTRA Phase 4 operational features.")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--dataset-id")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    tables = generate_features(args.input, args.output, args.dataset_id)
    print("Feature generation passed")
    for name, frame in tables.items():
        print(f"{name}: {frame.height} rows, {len(frame.columns)} columns")
    print(f"Output: {args.output}")


if __name__ == "__main__":
    main()
