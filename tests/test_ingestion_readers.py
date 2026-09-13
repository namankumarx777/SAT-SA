from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

from app.ingestion.readers import ReaderError, detect_format, read_table


def test_readers_support_csv_json_and_parquet(tmp_path: Path) -> None:
    frame = pl.DataFrame({"id": ["A-1", "A-2"], "value": [1, 2]})
    paths = {
        "csv": tmp_path / "alerts.csv",
        "json": tmp_path / "alerts.json",
        "parquet": tmp_path / "alerts.parquet",
    }
    frame.write_csv(paths["csv"])
    frame.write_json(paths["json"])
    frame.write_parquet(paths["parquet"])
    for kind, path in paths.items():
        assert detect_format(path) == f".{kind}"
        assert read_table(path).equals(frame)


def test_unsupported_format_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "alerts.xlsx"
    path.write_text("not supported", encoding="utf-8")
    with pytest.raises(ReaderError, match="Unsupported file format"):
        read_table(path)


def test_phase2_parquet_files_are_readable(phase2_dir: Path) -> None:
    assert read_table(phase2_dir / "alerts.parquet").height == 500
