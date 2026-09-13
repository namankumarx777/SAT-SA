from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import polars as pl

from app.ingestion.models import (
    DATASET_NAMES,
    IngestionResult,
    Manifest,
    QualityIssue,
    QualityReport,
    SourceFile,
)
from app.ingestion.normalizers import normalize_frame
from app.ingestion.readers import ReaderError, read_table
from app.ingestion.reports import build_report, human_summary
from app.ingestion.validators import validate_bundle

DEFAULT_PROCESSED_DIR = Path(__file__).resolve().parents[3] / "data" / "processed"


class IngestionValidationError(ValueError):
    def __init__(self, report: QualityReport) -> None:
        super().__init__(report.summary)
        self.report = report


def _dataset_name(path: Path, explicit: str | None = None) -> str:
    if explicit:
        if explicit not in DATASET_NAMES:
            raise ValueError(f"Unsupported dataset type: {explicit}")
        return explicit
    stem = path.stem.lower()
    for name in DATASET_NAMES:
        if stem in {name, name.rstrip("s"), f"{name}_data"}:
            return name
    raise ValueError(f"Cannot infer dataset type from filename: {path.name}; use --type")


def _source_files(input_path: Path, dataset_type: str | None) -> tuple[list[tuple[Path, str]], list[QualityIssue]]:
    issues: list[QualityIssue] = []
    if input_path.is_file():
        try:
            return [(input_path, _dataset_name(input_path, dataset_type))], issues
        except (ValueError, ReaderError) as exc:
            issues.append(QualityIssue(dataset="input", error_type="STRUCTURE", message=str(exc)))
            return [], issues
    if not input_path.is_dir():
        issues.append(QualityIssue(dataset="input", error_type="UNREADABLE_FILE", message=f"Input path not found: {input_path}"))
        return [], issues
    sources: list[tuple[Path, str]] = []
    for name in DATASET_NAMES:
        matches = sorted(path for path in input_path.iterdir() if path.is_file() and path.stem.lower() == name and path.suffix.lower() in {".csv", ".json", ".parquet"})
        if not matches:
            issues.append(QualityIssue(dataset=name, error_type="MISSING_REQUIRED_TABLE", message=f"Dataset package is missing {name}.csv, {name}.json, or {name}.parquet"))
        else:
            sources.append((matches[0], name))
            if len(matches) > 1:
                issues.append(QualityIssue(dataset=name, error_type="DUPLICATE_INPUT_FILE", message=f"Multiple source files found; using {matches[0].name}"))
    return sources, issues


def _prepare(input_path: Path, dataset_type: str | None = None) -> tuple[dict[str, pl.DataFrame], list[Path], QualityReport]:
    sources, issues = _source_files(input_path, dataset_type)
    bundle: dict[str, pl.DataFrame] = {}
    source_paths: list[Path] = []
    for path, dataset in sources:
        source_paths.append(path)
        try:
            raw = read_table(path)
            normalized = normalize_frame(raw, dataset)
            bundle[dataset] = normalized.frame
            issues.extend(normalized.issues)
        except ReaderError as exc:
            issues.append(QualityIssue(dataset=dataset, error_type="READ_ERROR", message=str(exc)))
        except Exception as exc:
            issues.append(QualityIssue(dataset=dataset, error_type="NORMALIZATION_ERROR", message=str(exc)))
    issues.extend(validate_bundle(bundle))
    report = build_report(len(source_paths), {name: frame.height for name, frame in bundle.items()}, issues)
    return bundle, source_paths, report


def validate_dataset(input_path: str | Path, dataset_type: str | None = None) -> QualityReport:
    """Read, normalize, and validate a file or five-table dataset directory."""
    _, _, report = _prepare(Path(input_path), dataset_type)
    return report


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _source_manifest(paths: Iterable[Path]) -> list[SourceFile]:
    return [SourceFile(filename=path.name, size=path.stat().st_size, sha256=_sha256(path)) for path in paths]


def write_canonical_dataset(bundle: dict[str, pl.DataFrame], output_dir: Path) -> None:
    """Write validated canonical frames without replacing an existing run."""
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"Output directory is not empty: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in bundle.items():
        frame.write_parquet(output_dir / f"{name}.parquet")


def create_manifest(dataset_id: str, source_paths: list[Path], bundle: dict[str, pl.DataFrame], output_dir: Path) -> Manifest:
    manifest = Manifest(
        dataset_id=dataset_id,
        ingested_at=datetime.now(timezone.utc),
        source_files=_source_manifest(source_paths),
        row_counts={name: frame.height for name, frame in bundle.items()},
        output_location=dataset_id,
    )
    (output_dir / "manifest.json").write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
    return manifest


def ingest_dataset(input_path: str | Path, output_root: str | Path = DEFAULT_PROCESSED_DIR, dataset_type: str | None = None) -> IngestionResult:
    """Validate and commit a dataset atomically to a unique processed run directory."""
    bundle, source_paths, report = _prepare(Path(input_path), dataset_type)
    if report.status != "passed":
        raise IngestionValidationError(report)
    source_hash = hashlib.sha256("".join(item.sha256 for item in _source_manifest(source_paths)).encode()).hexdigest()[:12]
    dataset_id = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{source_hash}"
    root = Path(output_root)
    output_dir = root / dataset_id
    root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=root, prefix=f".{dataset_id}-") as temporary:
        temporary_dir = Path(temporary)
        write_canonical_dataset(bundle, temporary_dir)
        manifest = create_manifest(dataset_id, source_paths, bundle, temporary_dir)
        output_dir.parent.mkdir(parents=True, exist_ok=True)
        temporary_dir.replace(output_dir)
    return IngestionResult(
        dataset_id=dataset_id,
        row_counts=report.rows,
        validation_status="passed",
        output_location=dataset_id,
        manifest=manifest,
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate and ingest SAT-SA CSE submissions.")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--type", dest="dataset_type", choices=DATASET_NAMES)
    parser.add_argument("--output", type=Path, default=DEFAULT_PROCESSED_DIR)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    try:
        report = validate_dataset(args.input, args.dataset_type)
        print(human_summary(report))
        if report.status == "failed":
            raise SystemExit(1)
        result = ingest_dataset(args.input, args.output, args.dataset_type)
        print(f"Imported dataset: {result.dataset_id}")
        print(f"Output location: {result.output_location}")
    except IngestionValidationError as exc:
        print(human_summary(exc.report))
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
