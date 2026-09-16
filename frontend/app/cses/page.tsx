"use client";

import React, { useState, useEffect, useMemo } from "react";
import { useRouter } from "next/navigation";
import { Search, ArrowUpDown, ChevronUp, ChevronDown } from "lucide-react";
import { api } from "../../src/api";
import { EntityRisk } from "../../src/types";
import { LoadingSkeleton, ErrorState, EmptyState } from "../../src/components/States";
import { Select } from "../../src/components/Select";

type SortField =
  | "overall_score"
  | "entity_id"
  | "name"
  | "sector"
  | "escalation_score"
  | "investigation_score"
  | "remediation_score"
  | "monitoring_score"
  | "assessment_coverage";

// Apple-style minimal status indicator (dot + text label, no heavy pill container)
function AppleStatusIndicator({ band }: { band: string }) {
  const upper = (band || "LOW").toUpperCase();

  let dotColor = "bg-[var(--risk-low-dot)]";
  let label = "Low";

  if (upper === "CRITICAL") {
    dotColor = "bg-[var(--risk-critical-dot)]";
    label = "Critical";
  } else if (upper === "HIGH") {
    dotColor = "bg-[var(--risk-high-dot)]";
    label = "High";
  } else if (upper === "MODERATE" || upper === "MEDIUM") {
    dotColor = "bg-[var(--risk-moderate-dot)]";
    label = "Moderate";
  }

  return (
    <span className="inline-flex items-center gap-2 text-[13px] font-medium text-[var(--fg)] select-none">
      <span className={`w-2 h-2 rounded-full ${dotColor} shrink-0`} />
      <span>{label}</span>
    </span>
  );
}

export default function CSEListPage() {
  const router = useRouter();
  const [entities, setEntities] = useState<EntityRisk[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filter & Search states
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedBand, setSelectedBand] = useState<string>("ALL");
  const [selectedSector, setSelectedSector] = useState<string>("ALL");
  const [selectedCriticality, setSelectedCriticality] = useState<string>("ALL");

  // Sorting
  const [sortField, setSortField] = useState<SortField>("overall_score");
  const [sortAsc, setSortAsc] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getEntities();
      setEntities(res);
    } catch (err: any) {
      setError(err.message || "Failed loading CSE assessments");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const uniqueSectors = useMemo(() => {
    const s = new Set(entities.map((e) => e.sector).filter(Boolean));
    return Array.from(s) as string[];
  }, [entities]);

  const filteredAndSortedEntities = useMemo(() => {
    return entities
      .filter((e) => {
        if (selectedBand !== "ALL" && e.risk_band !== selectedBand) return false;
        if (selectedSector !== "ALL" && e.sector !== selectedSector) return false;
        if (selectedCriticality !== "ALL" && e.criticality !== selectedCriticality)
          return false;
        if (searchQuery.trim()) {
          const q = searchQuery.toLowerCase();
          const matchId = e.entity_id.toLowerCase().includes(q);
          const matchName = (e.name || "").toLowerCase().includes(q);
          const matchSector = (e.sector || "").toLowerCase().includes(q);
          if (!matchId && !matchName && !matchSector) return false;
        }
        return true;
      })
      .sort((a, b) => {
        let aVal: any = a[sortField];
        let bVal: any = b[sortField];

        if (aVal === null || aVal === undefined) aVal = -1;
        if (bVal === null || bVal === undefined) bVal = -1;

        if (typeof aVal === "string") {
          return sortAsc
            ? aVal.localeCompare(bVal)
            : bVal.localeCompare(aVal);
        }
        return sortAsc ? aVal - bVal : bVal - aVal;
      });
  }, [
    entities,
    selectedBand,
    selectedSector,
    selectedCriticality,
    searchQuery,
    sortField,
    sortAsc,
  ]);

  const toggleSort = (field: SortField) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(false);
    }
  };

  const renderSortIndicator = (field: SortField) => {
    if (sortField !== field) {
      return (
        <ArrowUpDown className="w-3 h-3 text-[var(--muted)] opacity-0 group-hover:opacity-50 transition-opacity shrink-0" />
      );
    }
    return sortAsc ? (
      <ChevronUp className="w-3.5 h-3.5 text-[var(--fg)] shrink-0" />
    ) : (
      <ChevronDown className="w-3.5 h-3.5 text-[var(--fg)] shrink-0" />
    );
  };

  const renderDimensionCell = (score: number | null) => {
    if (score === null) {
      return (
        <span className="text-[var(--subtle)] font-mono text-[13px] block text-center">
          —
        </span>
      );
    }
    return (
      <span className="font-mono text-[13.5px] tabular-nums text-[var(--fg)] block text-center">
        {score.toFixed(1)}
      </span>
    );
  };



  if (loading) {
    return <LoadingSkeleton variant="table" text="Loading CSE registry..." />;
  }

  if (error) {
    return <ErrorState message={error} onRetry={fetchData} />;
  }

  return (
    <div className="space-y-6 pb-12">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-3 pt-1">
        <div>
          <h1 className="text-xl sm:text-2xl font-semibold tracking-tight text-[var(--fg)]">
            CSE Assessments
          </h1>
          <p className="text-xs sm:text-sm text-[var(--muted)] mt-0.5">
            Standardized evaluation registry across all 12 monitored entities
          </p>
        </div>
      </div>

      {/* Filter / Search Bar in Rounded Container */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-2.5 sm:p-3 rounded-xl border border-[var(--border)] bg-[var(--surface)]">
        <div className="flex flex-wrap items-center gap-2">
          {/* Integrated Search */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-[var(--muted)]" />
            <input
              type="text"
              placeholder="Search by ID, name, sector..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-8 pr-2.5 h-[34px] text-xs rounded-lg border border-[var(--border)] bg-transparent text-[var(--fg)] placeholder:text-[var(--subtle)] focus:outline-none focus:border-[var(--muted)] w-56 sm:w-64 transition-colors"
            />
          </div>

          {/* Segmented Band Filters */}
          <div className="flex items-center h-[34px] rounded-lg border border-[var(--border)] bg-[var(--surface-secondary)] p-0.5 text-xs">
            {["ALL", "HIGH", "MODERATE", "LOW"].map((band) => (
              <button
                key={band}
                onClick={() => setSelectedBand(band)}
                className={`px-2.5 h-full rounded-md text-[11px] font-medium transition cursor-pointer ${
                  selectedBand === band
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

          <Select
            value={selectedCriticality}
            onChange={(val) => setSelectedCriticality(val)}
            options={[
              { value: "ALL", label: "All Criticality" },
              { value: "CRITICAL", label: "Critical" },
              { value: "HIGH", label: "High" },
              { value: "MEDIUM", label: "Medium" },
            ]}
          />
        </div>

        {/* Metadata count */}
        <div className="text-[11px] font-mono text-[var(--muted)] pr-1 select-none">
          {filteredAndSortedEntities.length} of {entities.length} entities
        </div>
      </div>

      {/* Table Section */}
      {filteredAndSortedEntities.length === 0 ? (
        <EmptyState
          title="No entities match criteria"
          description="Try resetting your filters or search query."
          onReset={() => {
            setSearchQuery("");
            setSelectedBand("ALL");
            setSelectedSector("ALL");
            setSelectedCriticality("ALL");
          }}
        />
      ) : (
        <div className="border border-[var(--border)] rounded-2xl overflow-hidden bg-[var(--surface)] shadow-xs">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-[13.5px]">
              <thead className="bg-[var(--surface-secondary)]/50 text-[var(--muted)] font-medium border-b border-[var(--border)]">
                <tr>
                  <th
                    onClick={() => toggleSort("entity_id")}
                    className="group px-5 py-3 text-[11px] font-semibold uppercase tracking-wider cursor-pointer hover:text-[var(--fg)] select-none whitespace-nowrap text-left align-middle"
                  >
                    <div className="flex items-center gap-1.5">
                      <span>Entity</span>
                      {renderSortIndicator("entity_id")}
                    </div>
                  </th>
                  <th
                    onClick={() => toggleSort("sector")}
                    className="group px-4 py-3 text-[11px] font-semibold uppercase tracking-wider text-center cursor-pointer hover:text-[var(--fg)] select-none whitespace-nowrap align-middle"
                  >
                    <div className="flex items-center justify-center gap-1.5">
                      <span>Sector</span>
                      {renderSortIndicator("sector")}
                    </div>
                  </th>
                  <th
                    onClick={() => toggleSort("overall_score")}
                    className="group px-4 py-3 text-[11px] font-semibold uppercase tracking-wider text-center cursor-pointer hover:text-[var(--fg)] select-none whitespace-nowrap align-middle"
                  >
                    <div className="flex items-center justify-center gap-1.5">
                      <span>Risk Score</span>
                      {renderSortIndicator("overall_score")}
                    </div>
                  </th>
                  <th className="px-4 py-3 text-[11px] font-semibold uppercase tracking-wider text-center select-none whitespace-nowrap align-middle">
                    Criticality
                  </th>
                  <th
                    onClick={() => toggleSort("escalation_score")}
                    className="group px-4 py-3 text-[11px] font-semibold uppercase tracking-wider text-center cursor-pointer hover:text-[var(--fg)] select-none whitespace-nowrap align-middle"
                  >
                    <div className="flex items-center justify-center gap-1.5">
                      <span>Escalation</span>
                      {renderSortIndicator("escalation_score")}
                    </div>
                  </th>
                  <th
                    onClick={() => toggleSort("investigation_score")}
                    className="group px-4 py-3 text-[11px] font-semibold uppercase tracking-wider text-center cursor-pointer hover:text-[var(--fg)] select-none whitespace-nowrap align-middle"
                  >
                    <div className="flex items-center justify-center gap-1.5">
                      <span>Investigation</span>
                      {renderSortIndicator("investigation_score")}
                    </div>
                  </th>
                  <th
                    onClick={() => toggleSort("remediation_score")}
                    className="group px-4 py-3 text-[11px] font-semibold uppercase tracking-wider text-center cursor-pointer hover:text-[var(--fg)] select-none whitespace-nowrap align-middle"
                  >
                    <div className="flex items-center justify-center gap-1.5">
                      <span>Remediation</span>
                      {renderSortIndicator("remediation_score")}
                    </div>
                  </th>
                  <th
                    onClick={() => toggleSort("monitoring_score")}
                    className="group px-4 py-3 text-[11px] font-semibold uppercase tracking-wider text-center cursor-pointer hover:text-[var(--fg)] select-none whitespace-nowrap align-middle"
                  >
                    <div className="flex items-center justify-center gap-1.5">
                      <span>Monitoring</span>
                      {renderSortIndicator("monitoring_score")}
                    </div>
                  </th>
                  <th
                    onClick={() => toggleSort("assessment_coverage")}
                    className="group px-5 py-3 text-[11px] font-semibold uppercase tracking-wider text-center cursor-pointer hover:text-[var(--fg)] select-none whitespace-nowrap align-middle"
                  >
                    <div className="flex items-center justify-center gap-1.5">
                      <span>Coverage</span>
                      {renderSortIndicator("assessment_coverage")}
                    </div>
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border-subtle)]">
                {filteredAndSortedEntities.map((e) => (
                  <tr
                    key={e.entity_id}
                    onClick={() => router.push(`/cses/${e.entity_id}`)}
                    className="hover:bg-[var(--surface-secondary)]/60 transition-colors duration-150 cursor-pointer group"
                  >
                    <td className="px-5 py-4 align-middle whitespace-nowrap">
                      <span className="font-semibold text-[14px] text-[var(--fg)] block tracking-tight">
                        {e.entity_id}
                      </span>
                      {e.name && (
                        <span className="text-[12.5px] text-[var(--muted)] block mt-0.5">
                          {e.name}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-4 text-center align-middle text-[13.5px] text-[var(--muted)] whitespace-nowrap">
                      {e.sector || "Energy"}
                    </td>
                    <td className="px-4 py-4 text-center align-middle font-mono font-semibold text-[14.5px] text-[var(--fg)] tabular-nums whitespace-nowrap">
                      {e.overall_score.toFixed(2)}
                    </td>
                    <td className="px-4 py-4 text-center align-middle whitespace-nowrap">
                      <div className="flex items-center justify-center">
                        <AppleStatusIndicator band={e.risk_band} />
                      </div>
                    </td>
                    <td className="px-4 py-4 text-center align-middle whitespace-nowrap">
                      {renderDimensionCell(e.escalation_score)}
                    </td>
                    <td className="px-4 py-4 text-center align-middle whitespace-nowrap">
                      {renderDimensionCell(e.investigation_score)}
                    </td>
                    <td className="px-4 py-4 text-center align-middle whitespace-nowrap">
                      {renderDimensionCell(e.remediation_score)}
                    </td>
                    <td className="px-4 py-4 text-center align-middle whitespace-nowrap">
                      {renderDimensionCell(e.monitoring_score)}
                    </td>
                    <td className="px-5 py-4 text-center align-middle font-mono text-[13px] text-[var(--muted)] tabular-nums whitespace-nowrap">
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
  );
}

