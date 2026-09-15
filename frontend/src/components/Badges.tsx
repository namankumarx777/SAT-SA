import React from "react";
import { RiskBand, PriorityLevel } from "../types";

export function RiskBandBadge({
  band,
  className = "",
}: {
  band: RiskBand | string;
  className?: string;
}) {
  const upper = (band || "LOW").toUpperCase();

  switch (upper) {
    case "CRITICAL":
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-medium tracking-wide uppercase border bg-[var(--risk-critical-bg)] text-[var(--risk-critical-text)] border-[var(--risk-critical-border)] ${className}`}
        >
          <span className="w-1.5 h-1.5 rounded-full bg-[var(--risk-critical-dot)]" />
          Critical
        </span>
      );
    case "HIGH":
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-medium tracking-wide uppercase border bg-[var(--risk-high-bg)] text-[var(--risk-high-text)] border-[var(--risk-high-border)] ${className}`}
        >
          <span className="w-1.5 h-1.5 rounded-full bg-[var(--risk-high-dot)]" />
          High
        </span>
      );
    case "MODERATE":
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-medium tracking-wide uppercase border bg-[var(--risk-moderate-bg)] text-[var(--risk-moderate-text)] border-[var(--risk-moderate-border)] ${className}`}
        >
          <span className="w-1.5 h-1.5 rounded-full bg-[var(--risk-moderate-dot)]" />
          Moderate
        </span>
      );
    case "LOW":
    default:
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-medium tracking-wide uppercase border bg-[var(--risk-low-bg)] text-[var(--risk-low-text)] border-[var(--risk-low-border)] ${className}`}
        >
          <span className="w-1.5 h-1.5 rounded-full bg-[var(--risk-low-dot)]" />
          Low
        </span>
      );
  }
}

export function PriorityBadge({
  priority,
  className = "",
}: {
  priority: PriorityLevel | string;
  className?: string;
}) {
  const upper = (priority || "LOW").toUpperCase();

  switch (upper) {
    case "HIGH":
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-medium border bg-[var(--priority-high-bg)] text-[var(--priority-high-text)] border-[var(--priority-high-border)] ${className}`}
        >
          <span className="w-1.5 h-1.5 rounded-full bg-[var(--risk-critical-dot)]" />
          High Priority
        </span>
      );
    case "MEDIUM":
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-medium border bg-[var(--priority-medium-bg)] text-[var(--priority-medium-text)] border-[var(--priority-medium-border)] ${className}`}
        >
          <span className="w-1.5 h-1.5 rounded-full bg-[var(--risk-moderate-dot)]" />
          Medium Priority
        </span>
      );
    case "LOW":
    default:
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-medium border bg-[var(--priority-low-bg)] text-[var(--priority-low-text)] border-[var(--priority-low-border)] ${className}`}
        >
          <span className="w-1.5 h-1.5 rounded-full bg-[var(--subtle)]" />
          Low Priority
        </span>
      );
  }
}

export function DetectorTypeBadge({
  detectorId,
  className = "",
}: {
  detectorId: string;
  className?: string;
}) {
  let label = `RULE ${detectorId}`;
  if (detectorId.startsWith("EG")) label = `GAP ${detectorId}`;
  else if (detectorId.startsWith("NS")) label = `BLINDSPOT ${detectorId}`;
  else if (detectorId.startsWith("PB")) label = `PEER ${detectorId}`;
  else if (detectorId === "AN001") label = `ANOMALY ${detectorId}`;

  return (
    <span
      className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-mono tracking-tight border bg-[var(--surface-secondary)] text-[var(--fg)] border-[var(--border)] ${className}`}
    >
      {label}
    </span>
  );
}

export function CorroborationBadge({
  level,
  className = "",
}: {
  level: string;
  className?: string;
}) {
  const isMulti =
    level.toLowerCase().includes("strong") ||
    level.toLowerCase().includes("multi");

  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium border ${
        isMulti
          ? "bg-[var(--surface-secondary)] text-[var(--fg)] border-[var(--border)]"
          : "bg-[var(--surface)] text-[var(--muted)] border-[var(--border-subtle)]"
      } ${className}`}
    >
      {isMulti && (
        <span className="w-1 h-1 rounded-full bg-[var(--fg)]" />
      )}
      {level}
    </span>
  );
}

export function EvidenceStrengthBadge({
  strength,
  className = "",
}: {
  strength: string | null | undefined;
  className?: string;
}) {
  const s = (strength || "Unannotated").toLowerCase();
  let label = "Unannotated";
  let style = "text-[var(--muted)] border-[var(--border-subtle)]";

  if (s === "high" || s.includes("strong")) {
    label = "Strong Evidence";
    style = "text-[var(--fg)] border-[var(--border)] bg-[var(--surface-secondary)]";
  } else if (s === "medium" || s.includes("moderate")) {
    label = "Moderate Evidence";
    style = "text-[var(--muted)] border-[var(--border-subtle)] bg-[var(--surface)]";
  } else if (s === "low") {
    label = "Relative / Low";
    style = "text-[var(--subtle)] border-[var(--border-subtle)] bg-[var(--surface)]";
  }

  return (
    <span
      className={`inline-flex items-center px-1.5 py-0.5 rounded text-[11px] font-mono border ${style} ${className}`}
    >
      {label}
    </span>
  );
}
