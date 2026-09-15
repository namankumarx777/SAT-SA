from __future__ import annotations

from pathlib import Path

import polars as pl

FEATURE_TABLES = ("alert_features", "case_features", "asset_features", "entity_features", "entity_month_features")


def load_feature_bundle(input_dir: str | Path) -> dict[str, pl.DataFrame]:
    """Load all required Phase 4 feature tables from a feature output directory."""
    directory = Path(input_dir)
    if not directory.is_dir():
        raise ValueError(f"Feature input directory not found: {directory}")
    bundle: dict[str, pl.DataFrame] = {}
    missing: list[str] = []
    for name in FEATURE_TABLES:
        path = directory / f"{name}.parquet"
        if not path.is_file():
            missing.append(name)
        else:
            bundle[name] = pl.read_parquet(path)
    if missing:
        raise ValueError(f"Feature dataset is missing: {', '.join(missing)}")
    return bundle