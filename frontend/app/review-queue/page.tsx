"use client";

import React, { useState, useEffect, useMemo } from "react";
import Link from "next/link";
import {
  Search,
  ArrowRight,
  Info,
  FileText,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { api } from "../../src/api";
import { ReviewQueueItem, parseFindingIds } from "../../src/types";
import {
  PriorityBadge,
  DetectorTypeBadge,
  EvidenceStrengthBadge,
} from "../../src/components/Badges";
import { FindingDetailDrawer } from "../../src/components/FindingDetailDrawer";
import { LoadingSkeleton, ErrorState, EmptyState } from "../../src/components/States";
import { Select } from "../../src/components/Select";

export default function ReviewQueuePage() {
  const [queue, setQueue] = useState<ReviewQueueItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState("");
  const [priorityFilter, setPriorityFilter] = useState<string>("ALL");
  const [recordTypeFilter, setRecordTypeFilter] = useState<string>("ALL");

  // Selected finding for drawer inspection
  const [inspectedFindingId, setInspectedFindingId] = useState<string | null>(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getReviewQueue();
      setQueue(res);
    } catch (err: any) {
      setError(err.message || "Failed loading review queue");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const filteredQueue = useMemo(() => {
    return queue.filter((item) => {
      if (priorityFilter !== "ALL" && item.priority !== priorityFilter) return false;
      if (recordTypeFilter !== "ALL" && item.record_type !== recordTypeFilter)
        return false;
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchId = item.record_id.toLowerCase().includes(q);
        const matchEntity = item.entity_id.toLowerCase().includes(q);
        const matchReason = item.reason.toLowerCase().includes(q);
        if (!matchId && !matchEntity && !matchReason) return false;
      }
      return true;
    });
  }, [queue, priorityFilter, recordTypeFilter, searchQuery]);



  if (loading) {
    return <LoadingSkeleton variant="queue" text="Loading supervisory review queue..." />;
  }

  if (error) {
    return <ErrorState message={error} onRetry={fetchData} />;
  }

  return (
    <div className="space-y-6">
      {/* Sticky Header and Controls Container */}
      <div className="sticky top-0 z-20 bg-[var(--bg)] -mt-4 sm:-mt-6 lg:-mt-8 pt-4 sm:pt-6 lg:pt-8 pb-3 space-y-3.5 border-b border-[var(--border)]">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-3">
          <div>
            <h1 className="text-xl sm:text-2xl font-semibold tracking-tight text-[var(--fg)]">
              Supervisory Review Queue
            </h1>
            <p className="text-xs text-[var(--muted)] mt-0.5">
              What should be inspected first?
            </p>
          </div>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center justify-between gap-3 p-2.5 sm:p-3 rounded-xl border border-[var(--border)] bg-[var(--surface)]">
          <div className="flex flex-wrap items-center gap-2">
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-[var(--muted)]" />
              <input
                type="text"
                placeholder="Search record, entity, reason..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-8 pr-2.5 h-[34px] text-xs rounded-lg border border-[var(--border)] bg-transparent text-[var(--fg)] placeholder:text-[var(--subtle)] focus:outline-none focus:border-[var(--muted)] w-56 sm:w-64 transition-colors"
              />
            </div>

            <div className="flex items-center h-[34px] rounded-lg border border-[var(--border)] bg-[var(--surface-secondary)] p-0.5 text-xs">
              {["ALL", "HIGH", "MEDIUM", "LOW"].map((p) => (
                <button
                  key={p}
                  onClick={() => setPriorityFilter(p)}
                  className={`px-2.5 h-full rounded-md text-[11px] font-medium transition cursor-pointer ${
                    priorityFilter === p
                      ? "bg-[var(--surface)] text-[var(--fg)] border border-[var(--border-subtle)] shadow-xs"
                      : "text-[var(--muted)] hover-subtle"
                  }`}
                >
                  {p}
                </button>
              ))}
            </div>

            <Select
              value={recordTypeFilter}
              onChange={(val) => setRecordTypeFilter(val)}
              options={[
                { value: "ALL", label: "All Types" },
                { value: "FINDING", label: "Findings" },
                { value: "ENTITY", label: "Entities" },
                { value: "ASSET", label: "Assets" },
              ]}
            />
          </div>

          <div className="text-[11px] font-mono text-[var(--muted)]">
            {filteredQueue.length} queue item{filteredQueue.length !== 1 ? "s" : ""}
          </div>
        </div>
      </div>

      {/* Tenet Callout: Review Priority != Risk Score */}
      <div className="p-3 sm:p-3.5 rounded-xl border border-[var(--border)] bg-[var(--surface-secondary)] text-xs space-y-1">
        <span className="font-semibold text-[var(--fg)] block">
          Review priority is distinct from entity risk.
        </span>
        <p className="text-[var(--muted)] leading-relaxed text-[11px] sm:text-xs">
          Entity risk calculates the cumulative score across an organization. Review priority is an inspector triage mechanism designed to elevate actionable execution gaps (Phase 6), unmonitored critical asset blindspots (Phase 7), and multi-phase corroborated issues before routine single-rule alarms.
        </p>
      </div>

      {/* Work Queue List */}
      {filteredQueue.length === 0 ? (
        <EmptyState
          title="No queue items match filter"
          description="Adjust your search query or reset priority filter."
          onReset={() => {
            setSearchQuery("");
            setPriorityFilter("ALL");
            setRecordTypeFilter("ALL");
          }}
        />
      ) : (
        <div className="space-y-3.5">
          {filteredQueue.map((item) => {
            const firstFindingId =
              item.record_type === "FINDING" && item.record_id.startsWith("F-")
                ? item.record_id
                : parseFindingIds(item.supporting_finding_ids)[0] || null;

            // Parse structured reason for clean typographic hierarchy
            const colonIdx = item.reason.indexOf(":");
            let title = item.reason;
            let category: string | null = null;
            if (colonIdx !== -1) {
              const rawCategory = item.reason.slice(0, colonIdx).trim();
              title = item.reason.slice(colonIdx + 1).trim();
              category = rawCategory.replace(/\s*\(([^)]+)\)/, " · $1");
            }

            return (
              <div
                key={`${item.rank}-${item.record_id}`}
                className="p-5 sm:p-6 rounded-[18px] border border-[var(--border)] bg-[var(--surface)] hover:border-[var(--muted)]/40 hover:shadow-[0_4px_20px_rgba(0,0,0,0.03)] transition-all duration-200 flex flex-col md:flex-row md:items-center justify-between gap-5 group"
              >
                {/* Left & Center: Rank + Typographic Hierarchy */}
                <div className="flex items-start gap-4 flex-1 min-w-0">
                  {/* Subtle Rank Number */}
                  <span className="font-mono text-xs font-medium text-[var(--muted)] shrink-0 pt-0.5 select-none w-5">
                    {String(item.rank).padStart(2, "0")}
                  </span>

                  {/* Body Content */}
                  <div className="space-y-1.5 flex-1 min-w-0">
                    {/* 1. Top Metadata Line: CSE-011 · Finding */}
                    <div className="flex flex-wrap items-center gap-2 text-xs text-[var(--muted)]">
                      <Link
                        href={`/cses/${item.entity_id}`}
                        className="font-medium text-[var(--fg)] hover:underline hover:opacity-80 transition"
                      >
                        {item.entity_id}
                      </Link>
                      <span className="text-[var(--subtle)]">·</span>
                      <span className="capitalize text-[var(--muted)]">
                        {item.record_type.toLowerCase()}
                      </span>
                      {item.record_id && item.record_id !== item.entity_id && (
                        <>
                          <span className="text-[var(--subtle)]">·</span>
                          <span
                            className="font-mono text-[11px] text-[var(--muted)] opacity-50 truncate max-w-[160px]"
                            title={item.record_id}
                          >
                            {item.record_id}
                          </span>
                        </>
                      )}
                    </div>

                    {/* 2. Main Finding Focus */}
                    <h3 className="text-[15px] sm:text-[16px] font-semibold text-[var(--fg)] tracking-[-0.01em] leading-snug">
                      {title}
                    </h3>

                    {/* 3. Secondary Metadata & Evidence */}
                    <div className="flex flex-wrap items-center gap-2 text-[13px] text-[var(--muted)] pt-0.5">
                      {category && <span>{category}</span>}
                      {category && item.evidence_strength && (
                        <span className="text-[var(--subtle)]">·</span>
                      )}
                      {item.evidence_strength && (
                        <span className="text-[var(--muted)]">
                          {item.evidence_strength} evidence
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Right Side: Score, Minimal Priority & Clean Action */}
                <div className="flex items-center md:items-end justify-between md:justify-center md:flex-col gap-4 shrink-0 pt-3 md:pt-0 border-t md:border-t-0 border-[var(--border-subtle)] md:min-w-[140px] text-right">
                  {/* Score & Minimal Priority Indicator */}
                  <div className="flex md:flex-col items-center md:items-end gap-2.5 md:gap-1">
                    <span className="font-mono text-[22px] sm:text-[24px] font-bold tracking-tight text-[var(--fg)] tabular-nums leading-none">
                      {item.priority_score.toFixed(1)}
                    </span>
                    {item.priority === "HIGH" ? (
                      <div className="flex items-center gap-1.5 text-xs font-medium text-[var(--risk-high-text)]">
                        <span className="w-1.5 h-1.5 rounded-full bg-[var(--risk-high-dot)] shrink-0" />
                        <span>High priority</span>
                      </div>
                    ) : item.priority === "MEDIUM" ? (
                      <div className="flex items-center gap-1.5 text-xs font-medium text-[var(--risk-moderate-text)]">
                        <span className="w-1.5 h-1.5 rounded-full bg-[var(--risk-moderate-dot)] shrink-0" />
                        <span>Medium priority</span>
                      </div>
                    ) : (
                      <div className="flex items-center gap-1.5 text-xs font-medium text-[var(--risk-low-text)]">
                        <span className="w-1.5 h-1.5 rounded-full bg-[var(--risk-low-dot)] shrink-0" />
                        <span>Low priority</span>
                      </div>
                    )}
                  </div>

                  {/* Action Buttons: Inspect & Direct Page Navigation Arrow */}
                  <div className="flex items-center gap-2 pt-0 md:pt-1">
                    {firstFindingId ? (
                      <button
                        onClick={() => setInspectedFindingId(firstFindingId)}
                        className="inline-flex items-center px-3.5 py-1.5 rounded-lg text-xs font-medium border border-[var(--border)] bg-[var(--surface-secondary)] hover-subtle text-[var(--fg)] transition-colors cursor-pointer press-effect"
                      >
                        Inspect
                      </button>
                    ) : (
                      <Link
                        href={`/cses/${item.entity_id}`}
                        className="inline-flex items-center px-3.5 py-1.5 rounded-lg text-xs font-medium border border-[var(--border)] bg-[var(--surface-secondary)] hover-subtle text-[var(--fg)] transition-colors cursor-pointer press-effect"
                      >
                        View entity
                      </Link>
                    )}

                    {/* Arrow Button to Open CSE Entity Page */}
                    <Link
                      href={`/cses/${item.entity_id}`}
                      className="inline-flex items-center justify-center p-1.5 rounded-lg border border-[var(--border)] bg-[var(--surface-secondary)] hover-subtle text-[var(--muted)] hover:text-[var(--fg)] transition-colors cursor-pointer press-effect"
                      title={`Open ${item.entity_id} Assessment Page`}
                    >
                      <ArrowRight className="w-4 h-4" />
                    </Link>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Slide-Over Finding Inspector */}
      <FindingDetailDrawer
        findingId={inspectedFindingId}
        onClose={() => setInspectedFindingId(null)}
      />
    </div>
  );
}
