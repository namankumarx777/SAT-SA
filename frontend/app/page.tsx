"use client";

import React, { useState, useEffect, useMemo } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Search, ArrowRight } from "lucide-react";
import { api } from "../src/api";
import {
  EntityRisk,
  ReviewQueueItem,
  bandRangeLabel,
  riskBandThresholdsFromManifest,
} from "../src/types";
import { RiskBandBadge } from "../src/components/Badges";
import { LoadingSkeleton, ErrorState, EmptyState } from "../src/components/States";
import { Select } from "../src/components/Select";

export default function OverviewPage() {
  const router = useRouter();
  const [entities, setEntities] = useState<EntityRisk[]>([]);
  const [queue, setQueue] = useState<ReviewQueueItem[]>([]);
  const [bandThresholds, setBandThresholds] = useState<ReturnType<typeof riskBandThresholdsFromManifest> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filter states
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedBand, setSelectedBand] = useState<string>("ALL");
  const [selectedSector, setSelectedSector] = useState<string>("ALL");

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [entitiesRes, queueRes, manifestRes] = await Promise.all([
        api.getEntities(),
        api.getReviewQueue(),
        api.getManifest().catch(() => null),
      ]);
      setEntities(entitiesRes);
      setQueue(queueRes);
      setBandThresholds(riskBandThresholdsFromManifest(manifestRes));
    } catch (err: any) {
      setError(err.message || "Failed loading supervisory overview");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Compute metrics from API response
  const totalEntities = entities.length;
  const criticalEntities = entities.filter((e) => e.risk_band === "CRITICAL").length;
  const highRiskEntities = entities.filter((e) => e.risk_band === "HIGH").length;
  const moderateEntities = entities.filter((e) => e.risk_band === "MODERATE").length;
  const lowEntities = entities.filter((e) => e.risk_band === "LOW").length;
  const avgCoverage =
    entities.length > 0
      ? (
        (entities.reduce((sum, e) => sum + e.assessment_coverage, 0) /
          entities.length) *
        100
      ).toFixed(0)
      : "100";

  const uniqueSectors = useMemo(() => {
    const s = new Set(entities.map((e) => e.sector).filter(Boolean));
    return Array.from(s) as string[];
  }, [entities]);

  const filteredEntities = useMemo(() => {
    return entities
      .filter((e) => {
        if (selectedBand !== "ALL" && e.risk_band !== selectedBand) return false;
        if (selectedSector !== "ALL" && e.sector !== selectedSector) return false;
        if (searchQuery.trim()) {
          const q = searchQuery.toLowerCase();
          const matchId = e.entity_id.toLowerCase().includes(q);
          const matchName = (e.name || "").toLowerCase().includes(q);
          const matchSector = (e.sector || "").toLowerCase().includes(q);
          if (!matchId && !matchName && !matchSector) return false;
        }
        return true;
      })
      .sort((a, b) => b.overall_score - a.overall_score);
  }, [entities, selectedBand, selectedSector, searchQuery]);

  if (loading) {
    return <LoadingSkeleton variant="overview" text="Loading supervisory overview..." />;
  }

  if (error) {
    return <ErrorState message={error} onRetry={fetchData} />;
  }

  return (
    <div className="space-y-8">
      {/* Briefing Surface Header */}
      <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-3 border-b border-[var(--border)] pb-5">
        <div>
          <h1 className="text-xl sm:text-2xl font-semibold tracking-tight text-[var(--fg)]">
            Supervisory Overview
          </h1>
          <p className="text-xs text-[var(--muted)] mt-1">
            Current assessment across submitted CSE telemetry
          </p>
        </div>
      </div>

      {/* KPI Metric Cards in Rounded Containers */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3.5 sm:gap-4">
        {/* 1. Assessed CSEs */}
        <div className="p-4 sm:p-5 rounded-2xl border border-[var(--border)] bg-[var(--surface-secondary)] space-y-2 hover:border-[var(--muted)]/40 transition-colors">
          <span className="text-[11px] font-mono text-[var(--muted)] uppercase tracking-wider block">
            Assessed CSEs
          </span>
          <div className="text-2xl sm:text-3xl font-bold font-mono tabular-nums text-[var(--fg)]">
            {totalEntities}
          </div>
          <span className="text-[11px] text-[var(--subtle)] block">
            Monitored entities
          </span>
        </div>

        {/* 2. High Risk */}
        <div className="p-4 sm:p-5 rounded-2xl border border-[var(--border)] bg-[var(--surface-secondary)] space-y-2 hover:border-[var(--muted)]/40 transition-colors">
          <div className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-[var(--risk-high-dot)]" />
            <span className="text-[11px] font-mono text-[var(--risk-high-text)] uppercase tracking-wider block">
              High Risk
            </span>
          </div>
          <div className="text-2xl sm:text-3xl font-bold font-mono tabular-nums text-[var(--risk-high-text)]">
            {highRiskEntities}
          </div>
          <span className="text-[11px] text-[var(--muted)] block">
            {bandThresholds ? bandRangeLabel("HIGH", bandThresholds) : "Score 50.0–74.9"}
          </span>
        </div>

        {/* 3. Critical */}
        <div className="p-4 sm:p-5 rounded-2xl border border-[var(--border)] bg-[var(--surface-secondary)] space-y-2 hover:border-[var(--muted)]/40 transition-colors">
          <span className="text-[11px] font-mono text-[var(--muted)] uppercase tracking-wider block">
            Critical
          </span>
          <div className="text-2xl sm:text-3xl font-bold font-mono tabular-nums text-[var(--fg)]">
            {criticalEntities}
          </div>
          <span className="text-[11px] text-[var(--subtle)] block">
            {bandThresholds ? bandRangeLabel("CRITICAL", bandThresholds) : "Score \u2265 75.0"}
          </span>
        </div>

        {/* 4. Review Items */}
        <div className="p-4 sm:p-5 rounded-2xl border border-[var(--border)] bg-[var(--surface-secondary)] space-y-2 hover:border-[var(--muted)]/40 transition-colors">
          <span className="text-[11px] font-mono text-[var(--muted)] uppercase tracking-wider block">
            Review Items
          </span>
          <div className="text-2xl sm:text-3xl font-bold font-mono tabular-nums text-[var(--fg)]">
            {queue.length}
          </div>
          <span className="text-[11px] text-[var(--subtle)] block">
            Prioritized inspection queue
          </span>
        </div>

        {/* 5. Coverage */}
        <div className="p-4 sm:p-5 rounded-2xl border border-[var(--border)] bg-[var(--surface-secondary)] space-y-2 hover:border-[var(--muted)]/40 transition-colors col-span-2 sm:col-span-1">
          <span className="text-[11px] font-mono text-[var(--muted)] uppercase tracking-wider block">
            Coverage
          </span>
          <div className="text-2xl sm:text-3xl font-bold font-mono tabular-nums text-[var(--fg)]">
            {avgCoverage}%
          </div>
          <span className="text-[11px] text-[var(--subtle)] block">
            Dimensional completeness
          </span>
        </div>
      </div>

      {/* Minimal Horizontal Risk Distribution */}
      <div className="py-4 space-y-4">
        <div className="flex items-center justify-between text-xs border-b border-[var(--border-subtle)] pb-2">
          <span className="font-mono text-[11px] uppercase tracking-wider text-[var(--muted)]">
            Risk Distribution
          </span>
          <span className="text-[11px] text-[var(--subtle)] font-mono">
            {totalEntities} Cohort Entities
          </span>
        </div>

        {/* Clean segment bar with animated width */}
        <div className="w-full h-1.5 rounded-full bg-[var(--border-subtle)] overflow-hidden flex">
          <div
            style={{ width: `${(lowEntities / totalEntities) * 100}%` }}
            className="bg-[var(--risk-low-dot)] transition-all duration-700 ease-out"
            title={`LOW: ${lowEntities}`}
          />
          <div
            style={{ width: `${(moderateEntities / totalEntities) * 100}%` }}
            className="bg-[var(--risk-moderate-dot)] transition-all duration-700 ease-out delay-75"
            title={`MODERATE: ${moderateEntities}`}
          />
          <div
            style={{ width: `${(highRiskEntities / totalEntities) * 100}%` }}
            className="bg-[var(--risk-high-dot)] transition-all duration-700 ease-out delay-150"
            title={`HIGH: ${highRiskEntities}`}
          />
          <div
            style={{ width: `${(criticalEntities / totalEntities) * 100}%` }}
            className="bg-[var(--risk-critical-dot)] transition-all duration-700 ease-out delay-200"
            title={`CRITICAL: ${criticalEntities}`}
          />
        </div>

        {/* Understated Legend */}
        <div className="flex flex-wrap items-center gap-6 text-[11px] font-mono pt-1 text-[var(--muted)]">
          <div className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-[var(--risk-low-dot)]" />
            <span>LOW</span>
            <span className="text-[var(--fg)] font-semibold">{lowEntities}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-[var(--risk-moderate-dot)]" />
            <span>MODERATE</span>
            <span className="text-[var(--fg)] font-semibold">{moderateEntities}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-[var(--risk-high-dot)]" />
            <span>HIGH</span>
            <span className="text-[var(--fg)] font-semibold">{highRiskEntities}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-[var(--risk-critical-dot)]" />
            <span>CRITICAL</span>
            <span className="text-[var(--fg)] font-semibold">{criticalEntities}</span>
          </div>
        </div>
      </div>

      {/* Ranked CSE Data Table */}
      <div className="space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h2 className="text-sm font-semibold text-[var(--fg)] tracking-tight">
              CSE Risk Ranking
            </h2>
            <p className="text-xs text-[var(--muted)]">
              Select an entity to inspect dimensional breakdown and evidence
            </p>
          </div>

          {/* Unified Search & Filters */}
          <div className="flex flex-wrap items-center gap-2">
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-[var(--muted)]" />
              <input
                type="text"
                placeholder="Search entity..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-8 pr-2.5 h-[34px] text-xs rounded-lg border border-[var(--border)] bg-transparent text-[var(--fg)] placeholder:text-[var(--subtle)] focus:outline-none focus:border-[var(--muted)] w-56 sm:w-64 transition-colors"
              />
            </div>

            <div className="flex items-center h-[34px] rounded-lg border border-[var(--border)] bg-[var(--surface-secondary)] p-0.5 text-xs">
              {["ALL", "HIGH", "MODERATE", "LOW"].map((band) => (
                <button
                  key={band}
                  onClick={() => setSelectedBand(band)}
                  className={`px-2.5 h-full rounded-md text-[11px] font-medium transition cursor-pointer ${selectedBand === band
                    ? "bg-[var(--surface)] text-[var(--fg)] border border-[var(--border-subtle)] shadow-xs"
                    : "text-[var(--muted)] hover-subtle"
                    }`}
                >
                  {band}
                </button>
              ))}
            </div>

            {uniqueSectors.length > 0 && (
              <Select
                value={selectedSector}
                onChange={(val) => setSelectedSector(val)}
                options={[
                  { value: "ALL", label: "All Sectors" },
                  ...uniqueSectors.map((s) => ({ value: s, label: s })),
                ]}
              />
            )}
          </div>
        </div>

        {/* Table Container */}
        {filteredEntities.length === 0 ? (
          <EmptyState
            title="No entities match filter"
            description="Adjust or reset search query."
            onReset={() => {
              setSearchQuery("");
              setSelectedBand("ALL");
              setSelectedSector("ALL");
            }}
          />
        ) : (
          <div className="border border-[var(--border)] rounded overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-[var(--surface-secondary)] text-[var(--muted)] font-medium border-b border-[var(--border-subtle)]">
                  <tr>
                    <th className="px-4 py-2.5 font-mono text-[10px] uppercase">Entity</th>
                    <th className="px-4 py-2.5 font-mono text-[10px] uppercase">Sector</th>
                    <th className="px-4 py-2.5 font-mono text-[10px] uppercase">Criticality</th>
                    <th className="px-4 py-2.5 font-mono text-[10px] uppercase text-right">Risk Score</th>
                    <th className="px-4 py-2.5 font-mono text-[10px] uppercase">Band</th>
                    <th className="px-4 py-2.5 font-mono text-[10px] uppercase">Top Dimension</th>
                    <th className="px-4 py-2.5 font-mono text-[10px] uppercase text-right">Coverage</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--border-subtle)]">
                  {filteredEntities.map((e) => (
                    <tr
                      key={e.entity_id}
                      onClick={() => router.push(`/cses/${e.entity_id}`)}
                      className="hover-subtle cursor-pointer group"
                    >
                      <td className="px-4 py-3">
                        <div className="font-mono font-semibold text-[var(--fg)] group-hover:text-[var(--fg)]">
                          {e.entity_id}
                        </div>
                        {e.name && (
                          <div className="text-[11px] text-[var(--muted)] mt-0.5">
                            {e.name}
                          </div>
                        )}
                      </td>
                      <td className="px-4 py-3 text-[var(--muted)]">
                        {e.sector || "Energy"}
                      </td>
                      <td className="px-4 py-3 text-[var(--muted)]">
                        {e.criticality || "MEDIUM"}
                      </td>
                      <td className="px-4 py-3 text-right font-mono font-bold text-sm text-[var(--fg)] tabular-nums">
                        {e.overall_score.toFixed(2)}
                      </td>
                      <td className="px-4 py-3">
                        <RiskBandBadge band={e.risk_band} />
                      </td>
                      <td className="px-4 py-3 font-mono text-[11px] text-[var(--muted)]">
                        {e.top_risk_dimension || "—"}
                      </td>
                      <td className="px-4 py-3 text-right font-mono text-[11px] text-[var(--muted)] tabular-nums">
                        {(e.assessment_coverage * 100).toFixed(0)}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}