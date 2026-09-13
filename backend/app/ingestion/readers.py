from __future__ import annotations

from pathlib import Path
from typing import Protocol

import polars as pl


SUPPORTED_EXTENSIONS = {".csv", ".json", ".parquet"}


class Reader(Protocol):
    def read(self, path: Path) -> pl.DataFrame:
        ...


class CSVReader:
    def read(self, path: Path) -> pl.DataFrame:
        return pl.read_csv(path, try_parse_dates=False)


class JSONReader:
    def read(self, path: Path) -> pl.DataFrame:
        return pl.read_json(path)


class ParquetReader:
    def read(self, path: Path) -> pl.DataFrame:
        return pl.read_parquet(path)


class ReaderError(ValueError):
    """Raised when a supported input cannot be read."""


def detect_format(path: Path) -> str:
    extension = path.suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise ReaderError(f"Unsupported file format: {extension or '<none>'}")
    return extension


def reader_for(path: Path) -> Reader:
    readers: dict[str, Reader] = {
        ".csv": CSVReader(),
        ".json": JSONReader(),
        ".parquet": ParquetReader(),
    }
    return readers[detect_format(path)]


def read_table(path: Path) -> pl.DataFrame:
    if not path.is_file():
        raise ReaderError(f"Input file not found: {path.name}")
    try:
        return reader_for(path).read(path)
    except ReaderError:
        raise
    except Exception as exc:
        raise ReaderError(f"Unable to read {path.name}: {exc}") from exc
