from __future__ import annotations

from collections.abc import Iterable

from app.ingestion.models import QualityIssue, QualityReport


def build_report(files: int, rows: dict[str, int], issues: Iterable[QualityIssue]) -> QualityReport:
    """Build the machine-readable report shared by CLI, API, and tests."""
    issue_list = list(issues)
    errors = sum(issue.severity == "error" for issue in issue_list)
    warnings = sum(issue.severity == "warning" for issue in issue_list)
    status = "passed" if errors == 0 else "failed"
    summary = f"Validation {status}: {errors} error(s), {warnings} warning(s), {sum(rows.values())} row(s) across {files} file(s)."
    return QualityReport(
        status=status,
        files=files,
        rows=rows,
        errors=errors,
        warnings=warnings,
        issues=issue_list,
        summary=summary,
    )


def human_summary(report: QualityReport) -> str:
    """Render a concise human-readable validation summary."""
    lines = [report.summary]
    for dataset, count in report.rows.items():
        lines.append(f"- {dataset}: {count} rows")
    for issue in report.issues:
        location = f" {issue.field}" if issue.field else ""
        lines.append(f"- {issue.severity.upper()} [{issue.dataset}{location}] {issue.message}")
    return "\n".join(lines)
