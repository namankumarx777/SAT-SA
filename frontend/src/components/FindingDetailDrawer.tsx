"use client";

import React, { useState, useEffect } from "react";
import { X, Layers, Database, ArrowRight } from "lucide-react";
import { api } from "../api";
import { FindingDetailResponse } from "../types";
import { DetectorTypeBadge, EvidenceStrengthBadge, PriorityBadge } from "./Badges";

interface FindingDetailDrawerProps {
  findingId: string | null;
  onClose: () => void;
}

export function FindingDetailDrawer({
  findingId,
  onClose,
}: FindingDetailDrawerProps) {
  const [data, setData] = useState<FindingDetailResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!findingId) {
      setData(null);
      return;
    }

    let isMounted = true;
    setLoading(true);
    setError(null);

    api
      .getFindingDetail(findingId)
      .then((res) => {
        if (isMounted) setData(res);
      })
      .catch((err) => {
        if (isMounted) setError(err.message || "Failed loading finding detail");
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [findingId]);

  // Handle Escape key to close
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  if (!findingId) return null;

  return (
    <div
      className="fixed inset-0 z-50 overflow-hidden bg-black/40 backdrop-blur-xs flex justify-end transition-opacity duration-200"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
      aria-modal="true"
      role="dialog"
    >
      <div className="w-full max-w-2xl bg-[var(--surface)] border-l border-[var(--border)] h-full flex flex-col shadow-2xl transition-transform duration-250 ease-out">
        {/* Drawer Header */}
        <div className="px-6 py-4 border-b border-[var(--border)] flex items-center justify-between bg-[var(--surface)]">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-semibold text-[var(--muted)]">
                {findingId}
              </span>
              {data?.finding && (
                <DetectorTypeBadge detectorId={data.finding.rule_id} />
              )}
            </div>
            <h2 className="text-base font-semibold text-[var(--fg)] tracking-tight">
              {data?.finding?.title || "Supervisory Finding Inspector"}
            </h2>
          </div>
          <button
            onClick={onClose}
            aria-label="Close inspector"
            className="p-1.5 rounded-md text-[var(--muted)] hover:text-[var(--fg)] hover:bg-[var(--surface-secondary)] transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Drawer Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 text-sm">
          {loading && (
            <div className="py-12 space-y-3 text-center">
              <div className="w-6 h-6 border-2 border-[var(--fg)] border-t-transparent rounded-full animate-spin mx-auto" />
              <p className="text-xs text-[var(--muted)] font-mono">
                Resolving evidence chain...
              </p>
            </div>
          )}

          {error && (
            <div className="p-4 rounded-lg border border-[var(--risk-critical-border)] bg-[var(--risk-critical-bg)] text-xs text-[var(--risk-critical-text)]">
              <span className="font-semibold block">Error loading finding detail</span>
              <span>{error}</span>
            </div>
          )}

          {data && !loading && (
            <>
              {/* Finding Metadata Row */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                <div className="p-3 rounded-lg border border-[var(--border)] bg-[var(--surface-secondary)]">
                  <span className="text-[10px] uppercase font-mono text-[var(--muted)] block">
                    Source Phase
                  </span>
                  <span className="font-semibold text-xs text-[var(--fg)] mt-0.5 block uppercase">
                    {data.finding.source_phase}
                  </span>
                </div>

                <div className="p-3 rounded-lg border border-[var(--border)] bg-[var(--surface-secondary)]">
                  <span className="text-[10px] uppercase font-mono text-[var(--muted)] block">
                    Severity
                  </span>
                  <span className="font-semibold text-xs text-[var(--fg)] mt-0.5 block">
                    {data.finding.severity}
                  </span>
                </div>

                <div className="p-3 rounded-lg border border-[var(--border)] bg-[var(--surface-secondary)]">
                  <span className="text-[10px] uppercase font-mono text-[var(--muted)] block">
                    Evidence Strength
                  </span>
                  <div className="mt-0.5">
                    <EvidenceStrengthBadge strength={data.finding.evidence_strength} />
                  </div>
                </div>

                <div className="p-3 rounded-lg border border-[var(--border)] bg-[var(--surface-secondary)]">
                  <span className="text-[10px] uppercase font-mono text-[var(--muted)] block">
                    Entity ID
                  </span>
                  <span className="font-mono text-xs font-semibold text-[var(--fg)] mt-0.5 block">
                    {data.finding.entity_id}
                  </span>
                </div>
              </div>

              {/* Observed vs Expected Quantitative Metrics */}
              {(data.finding.observed_value !== undefined ||
                data.finding.expected_value !== undefined ||
                data.finding.gap_value !== undefined ||
                data.finding.anomaly_score !== undefined) && (
                <div className="p-4 rounded-xl border border-[var(--border)] bg-[var(--surface-secondary)] space-y-3">
                  <span className="text-[11px] font-mono uppercase text-[var(--muted)] tracking-wider block">
                    Quantitative Deviation
                  </span>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                    {data.finding.observed_value !== undefined && (
                      <div>
                        <span className="text-[10px] text-[var(--muted)] block">
                          Observed
                        </span>
                        <span className="font-mono text-base font-bold text-[var(--fg)] tabular-nums">
                          {String(data.finding.observed_value)}
                        </span>
                      </div>
                    )}
                    {data.finding.expected_value !== undefined && (
                      <div>
                        <span className="text-[10px] text-[var(--muted)] block">
                          Expected / Baseline
                        </span>
                        <span className="font-mono text-base font-bold text-[var(--fg)] tabular-nums">
                          {String(data.finding.expected_value)}
                        </span>
                      </div>
                    )}
                    {data.finding.gap_value !== undefined && (
                      <div>
                        <span className="text-[10px] text-[var(--muted)] block">
                          Execution Gap
                        </span>
                        <span className="font-mono text-base font-bold text-[var(--risk-high-text)] tabular-nums">
                          {String(data.finding.gap_value)}
                        </span>
                      </div>
                    )}
                    {data.finding.anomaly_rank !== undefined && (
                      <div>
                        <span className="text-[10px] text-[var(--muted)] block">
                          Anomaly Rank
                        </span>
                        <span className="font-mono text-base font-bold text-[var(--fg)] tabular-nums">
                          #{data.finding.anomaly_rank}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Summary & Rationale */}
              <div className="space-y-2">
                <span className="text-[11px] font-mono uppercase text-[var(--muted)] tracking-wider block">
                  Why This Matters
                </span>
                <p className="text-[var(--fg)] text-xs leading-relaxed font-normal">
                  {data.finding.summary}
                </p>
                {data.finding.rationale && (
                  <p className="text-[11px] text-[var(--muted)] leading-relaxed pt-2 border-t border-[var(--border-subtle)]">
                    {data.finding.rationale}
                  </p>
                )}
              </div>

              {/* Supporting Evidence Chain */}
              <div className="space-y-2.5">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-mono uppercase text-[var(--muted)] tracking-wider">
                    Supporting Evidence ({data.evidence.length})
                  </span>
                  <span className="text-[10px] text-[var(--subtle)] font-mono">
                    Deterministic Source Records
                  </span>
                </div>

                {data.evidence.length === 0 ? (
                  <div className="p-4 rounded-lg border border-[var(--border)] bg-[var(--surface-secondary)] text-center text-xs text-[var(--muted)]">
                    No granular evidence records attached to this cohort-level finding.
                  </div>
                ) : (
                  <div className="border border-[var(--border)] rounded-lg overflow-hidden">
                    <div className="overflow-x-auto max-h-72">
                      <table className="w-full text-left text-xs">
                        <thead className="bg-[var(--surface-secondary)] text-[var(--muted)] font-medium sticky top-0 border-b border-[var(--border)]">
                          <tr>
                            <th className="px-3 py-2 font-mono text-[10px] uppercase">Source</th>
                            <th className="px-3 py-2 font-mono text-[10px] uppercase">Record ID</th>
                            <th className="px-3 py-2 font-mono text-[10px] uppercase">Field</th>
                            <th className="px-3 py-2 font-mono text-[10px] uppercase">Value</th>
                            <th className="px-3 py-2 text-[10px] uppercase">Reason</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-[var(--border-subtle)]">
                          {data.evidence.map((ev, i) => (
                            <tr key={ev.id || i} className="hover:bg-[var(--surface-secondary)] transition">
                              <td className="px-3 py-2 font-mono text-[11px] text-[var(--muted)]">
                                {ev.source_type}
                              </td>
                              <td className="px-3 py-2 font-mono text-[11px] font-medium text-[var(--fg)]">
                                {ev.source_id}
                              </td>
                              <td className="px-3 py-2 font-mono text-[11px] text-[var(--muted)]">
                                {ev.field}
                              </td>
                              <td className="px-3 py-2 font-mono text-[11px] font-bold text-[var(--fg)] tabular-nums">
                                {String(ev.value ?? "—")}
                              </td>
                              <td className="px-3 py-2 text-[11px] text-[var(--fg)] leading-snug">
                                {ev.reason || "Supports threshold violation"}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            </>
          )}
        </div>

        {/* Drawer Footer */}
        <div className="px-6 py-3 border-t border-[var(--border)] bg-[var(--surface)] flex items-center justify-between text-xs text-[var(--muted)]">
          <span className="font-mono text-[11px]">Traceable Evidence Verification</span>
          <button
            onClick={onClose}
            className="px-3 py-1.5 rounded-md text-xs font-medium border border-[var(--border)] bg-[var(--surface-secondary)] hover:bg-[var(--surface-tertiary)] text-[var(--fg)] transition"
          >
            Close Inspector
          </button>
        </div>
      </div>
    </div>
  );
}
