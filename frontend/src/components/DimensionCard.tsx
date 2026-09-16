import React from "react";
import { FALLBACK_RISK_BAND_THRESHOLDS, RiskBandThresholds } from "../types";

interface DimensionCardProps {
  dimension: string;
  score: number | null;
  weight: number;
  description?: string;
  thresholds?: RiskBandThresholds;
  isSelected?: boolean;
  onClick?: () => void;
}

export function DimensionCard({
  dimension,
  score,
  weight,
  description,
  thresholds = FALLBACK_RISK_BAND_THRESHOLDS,
  isSelected = false,
  onClick,
}: DimensionCardProps) {
  const isAssessable = score !== null;

  return (
    <div 
      onClick={onClick}
      className={`p-4 rounded-xl border transition-colors ${
        onClick ? "cursor-pointer press-effect" : ""
      } ${
        isSelected 
          ? "border-[var(--fg)] bg-[var(--surface-secondary)]" 
          : "border-[var(--border)] bg-[var(--surface)] hover:bg-[var(--surface-secondary)]"
      }`}
    >
      <div className="flex items-baseline justify-between gap-2">
        <div>
          <span className="text-[11px] font-mono text-[var(--muted)] tracking-wider uppercase">
            {(weight * 100).toFixed(0)}% Weight
          </span>
          <h3 className="font-semibold text-sm text-[var(--fg)] tracking-tight mt-0.5">
            {dimension}
          </h3>
        </div>

        {isAssessable ? (
          <div className="text-right">
            <span className="font-mono text-xl font-bold tabular-nums text-[var(--fg)]">
              {score.toFixed(1)}
            </span>
            <span className="text-[11px] text-[var(--muted)] font-mono ml-0.5">
              /100
            </span>
          </div>
        ) : (
          <span className="text-xs font-mono text-[var(--muted)] px-2 py-0.5 rounded bg-[var(--surface-secondary)] border border-[var(--border)]">
            Not Assessable
          </span>
        )}
      </div>

      {/* Restrained Progress Bar */}
      <div className="w-full bg-[var(--surface-secondary)] rounded-full h-1 mt-3 overflow-hidden">
        {isAssessable ? (
          <div
            className={`h-full rounded-full transition-all duration-500 ${
              score >= thresholds.critical
                ? "bg-[var(--risk-critical-dot)]"
                : score >= thresholds.high
                ? "bg-[var(--risk-high-dot)]"
                : score >= thresholds.moderate
                ? "bg-[var(--risk-moderate-dot)]"
                : "bg-[var(--fg)]"
            }`}
            style={{ width: `${Math.min(100, Math.max(0, score))}%` }}
          />
        ) : (
          <div className="h-full w-full bg-[var(--border)] opacity-40" />
        )}
      </div>

      {/* Description or Unassessable status */}
      <div className="mt-2.5 text-xs text-[var(--muted)] leading-relaxed">
        {isAssessable ? (
          <p className="line-clamp-2 text-[11px]">{description}</p>
        ) : (
          <p className="text-[11px] text-[var(--subtle)] italic">
            Telemetry insufficient to establish baseline. Dimension excluded from denominator.
          </p>
        )}
      </div>
    </div>
  );
}
