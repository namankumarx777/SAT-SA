"use client";

import React, { useState, useEffect, useMemo } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Search, ArrowUpDown } from "lucide-react";
import { api } from "../../src/api";
import { EntityRisk } from "../../src/types";
import { RiskBandBadge } from "../../src/components/Badges";
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

  const renderDimensionCell = (score: number | null) => {
    if (score === null) {
      return (
        <span className="text-[var(--subtle)] font-mono text-[11px] italic">
          —
        </span>
      );
    }
    return (
      <span className="font-mono text-xs tabular-nums text-[var(--fg)]">
        {score.toFixed(1)}
      </span>
    );
  };

  if (loading) {
    return <LoadingSkeleton text="Loading CSE registry..." />;
  }

  if (error) {
    return <ErrorState message={error} onRetry={fetchData} />;
  }

  return (
    <div className="space-y-6">
      {/* Sticky Header and Controls Container */}
      <div className="sticky top-0 z-20 bg-[var(--bg)] -mt-4 sm:-mt-6 lg:-mt-8 pt-4 sm:pt-6 lg:pt-8 pb-3 space-y-3.5 border-b border-[var(--border)]">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-2">
          <div>
            <h1 className="text-xl sm:text-2xl font-semibold tracking-tight text-[var(--fg)]">
              CSE Assessments
            </h1>
            <p className="text-xs text-[var(--muted)] mt-0.5">
              Standardized evaluation registry across all 12 monitored entities
            </p>
          </div>
        </div>

        {/* Filter and Search Bar */}
        <div className="flex flex-wrap items-center justify-between gap-3 p-2.5 sm:p-3 rounded-xl border border-[var(--border)] bg-[var(--surface)] shadow-xs">
          <div className="flex flex-wrap items-center gap-2">
            <div className="relative">
              <Search className="w-3 h-3 absolute left-2.5 top-2.5 text-[var(--muted)]" />
              <input
                type="text"
                placeholder="Search by ID, name, sector..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-7 pr-2.5 py-1 text-xs rounded-md border border-[var(--border)] bg-[var(--surface-secondary)] text-[var(--fg)] placeholder:text-[var(--subtle)] focus:outline-none focus:border-[var(--muted)] w-52 sm:w-64"
              />
            </div>

            <Select
              value={selectedBand}
              onChange={(val) => setSelectedBand(val)}
              options={[
                { value: "ALL", label: "All Bands" },
                { value: "HIGH", label: "High" },
                { value: "MODERATE", label: "Moderate" },
                { value: "LOW", label: "Low" },
              ]}
            />

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

          <span className="text-xs font-mono text-[var(--muted)]">
            {filteredAndSortedEntities.length} of {entities.length} entities
          </span>
        </div>
      </div>

      {/* Table */}
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
        <div className="border border-[var(--border)] rounded-xl overflow-hidden bg-[var(--surface)]">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-[var(--surface-secondary)] text-[var(--muted)] font-medium border-b border-[var(--border)]">
                <tr>
                  <th
                    onClick={() => toggleSort("entity_id")}
                    className="px-4 py-2.5 font-mono text-[10px] uppercase cursor-pointer hover:text-[var(--fg)]"
                  >
                    Entity
                  </th>
                  <th
                    onClick={() => toggleSort("sector")}
                    className="px-4 py-2.5 font-mono text-[10px] uppercase cursor-pointer hover:text-[var(--fg)]"
                  >
                    Sector
                  </th>
                  <th
                    onClick={() => toggleSort("overall_score")}
                    className="px-4 py-2.5 font-mono text-[10px] uppercase text-right cursor-pointer hover:text-[var(--fg)]"
                  >
                    Risk Score
                  </th>
                  <th className="px-4 py-2.5 font-mono text-[10px] uppercase">Band</th>
                  <th
                    onClick={() => toggleSort("escalation_score")}
                    className="px-4 py-2.5 font-mono text-[10px] uppercase text-right cursor-pointer hover:text-[var(--fg)]"
                  >
                    Escalation
                  </th>
                  <th
                    onClick={() => toggleSort("investigation_score")}
                    className="px-4 py-2.5 font-mono text-[10px] uppercase text-right cursor-pointer hover:text-[var(--fg)]"
                  >
                    Investigation
                  </th>
                  <th
                    onClick={() => toggleSort("remediation_score")}
                    className="px-4 py-2.5 font-mono text-[10px] uppercase text-right cursor-pointer hover:text-[var(--fg)]"
                  >
                    Remediation
                  </th>
                  <th
                    onClick={() => toggleSort("monitoring_score")}
                    className="px-4 py-2.5 font-mono text-[10px] uppercase text-right cursor-pointer hover:text-[var(--fg)]"
                  >
                    Monitoring
                  </th>
                  <th
                    onClick={() => toggleSort("assessment_coverage")}
                    className="px-4 py-2.5 font-mono text-[10px] uppercase text-right cursor-pointer hover:text-[var(--fg)]"
                  >
                    Coverage
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border-subtle)]">
                {filteredAndSortedEntities.map((e) => (
                  <tr
                    key={e.entity_id}
                    onClick={() => router.push(`/cses/${e.entity_id}`)}
                    className="hover:bg-[var(--surface-secondary)] transition cursor-pointer group"
                  >
                    <td className="px-4 py-3">
                      <span className="font-mono font-semibold text-[var(--fg)] block">
                        {e.entity_id}
                      </span>
                      {e.name && (
                        <span className="text-[11px] text-[var(--muted)] block mt-0.5">
                          {e.name}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-[var(--muted)]">
                      {e.sector || "Energy"}
                    </td>
                    <td className="px-4 py-3 text-right font-mono font-bold text-sm text-[var(--fg)] tabular-nums">
                      {e.overall_score.toFixed(2)}
                    </td>
                    <td className="px-4 py-3">
                      <RiskBandBadge band={e.risk_band} />
                    </td>
                    <td className="px-4 py-3 text-right">
                      {renderDimensionCell(e.escalation_score)}
                    </td>
                    <td className="px-4 py-3 text-right">
                      {renderDimensionCell(e.investigation_score)}
                    </td>
                    <td className="px-4 py-3 text-right">
                      {renderDimensionCell(e.remediation_score)}
                    </td>
                    <td className="px-4 py-3 text-right">
                      {renderDimensionCell(e.monitoring_score)}
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
  );
}
