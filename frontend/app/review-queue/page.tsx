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

  const highPriorityCount = queue.filter((q) => q.priority === "HIGH").length;
  const mediumPriorityCount = queue.filter((q) => q.priority === "MEDIUM").length;
  const lowPriorityCount = queue.filter((q) => q.priority === "LOW").length;

  if (loading) {
    return <LoadingSkeleton text="Loading supervisory review queue..." />;
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

          <div className="flex items-center gap-2 font-mono text-xs">
            <span className="text-[var(--risk-high-text)] font-semibold">
              {highPriorityCount} High
            </span>
            <span className="text-[var(--subtle)]">•</span>
            <span className="text-[var(--risk-moderate-text)] font-semibold">
              {mediumPriorityCount} Medium
            </span>
            <span className="text-[var(--subtle)]">•</span>
            <span className="text-[var(--muted)]">{lowPriorityCount} Low</span>
          </div>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center justify-between gap-3 p-2.5 sm:p-3 rounded-xl border border-[var(--border)] bg-[var(--surface)] shadow-xs">
          <div className="flex flex-wrap items-center gap-2">
            <div className="relative">
              <Search className="w-3 h-3 absolute left-2.5 top-2.5 text-[var(--muted)]" />
              <input
                type="text"
                placeholder="Search record, entity, reason..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-7 pr-2.5 py-1 text-xs rounded-md border border-[var(--border)] bg-[var(--surface-secondary)] text-[var(--fg)] placeholder:text-[var(--subtle)] focus:outline-none focus:border-[var(--muted)] w-56 sm:w-64"
              />
            </div>

            <div className="flex items-center rounded-md border border-[var(--border)] bg-[var(--surface-secondary)] p-0.5 text-xs">
              {["ALL", "HIGH", "MEDIUM", "LOW"].map((p) => (
                <button
                  key={p}
                  onClick={() => setPriorityFilter(p)}
                  className={`px-2.5 py-0.5 rounded text-[11px] font-medium transition cursor-pointer ${
                    priorityFilter === p
                      ? "bg-[var(--surface)] text-[var(--fg)] shadow-xs"
                      : "text-[var(--muted)] hover:text-[var(--fg)]"
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
        <div className="space-y-2">
          {filteredQueue.map((item) => {
            const firstFindingId =
              item.record_type === "FINDING" && item.record_id.startsWith("F-")
                ? item.record_id
                : parseFindingIds(item.supporting_finding_ids)[0] || null;

            return (
              <div
                key={`${item.rank}-${item.record_id}`}
                className="p-4 sm:p-5 rounded-xl border border-[var(--border)] bg-[var(--surface)] hover:border-[var(--muted)] transition-colors flex flex-col md:flex-row md:items-start justify-between gap-4 group"
              >
                {/* Left & Center: Rank Badge + Details */}
                <div className="flex items-start gap-3.5 flex-1 min-w-0">
                  {/* Rank Badge */}
                  <div className="w-8 h-8 rounded-lg border border-[var(--border)] bg-[var(--surface-secondary)] flex items-center justify-center font-mono text-xs font-bold text-[var(--muted)] shrink-0 select-none">
                    {String(item.rank).padStart(2, "0")}
                  </div>

                  {/* Body details */}
                  <div className="space-y-1.5 flex-1 min-w-0">
                    {/* Header line: Entity • Record ID • Type */}
                    <div className="flex flex-wrap items-center gap-2 text-xs">
                      <Link
                        href={`/cses/${item.entity_id}`}
                        className="font-mono font-bold text-[var(--fg)] hover:underline"
                      >
                        {item.entity_id}
                      </Link>
                      <span className="text-[var(--subtle)]">•</span>
                      <span className="font-mono text-[var(--muted)] font-medium">
                        {item.record_id}
                      </span>
                      <span className="text-[var(--subtle)]">•</span>
                      <span className="text-[10px] font-mono uppercase tracking-wider text-[var(--subtle)] px-1.5 py-0.5 rounded bg-[var(--surface-secondary)] border border-[var(--border-subtle)]">
                        {item.record_type}
                      </span>
                    </div>

                    {/* Reason Text */}
                    <p className="text-xs text-[var(--fg)] leading-relaxed">
                      {item.reason}
                    </p>

                    {/* Evidence & Context Badge */}
                    <div className="flex items-center gap-2 pt-0.5">
                      <EvidenceStrengthBadge strength={item.evidence_strength} />
                    </div>
                  </div>
                </div>

                {/* Right Side: Score, Priority Badge & Action */}
                <div className="flex items-center md:items-end justify-between md:justify-start md:flex-col gap-3 shrink-0 pt-2 md:pt-0 border-t md:border-t-0 border-[var(--border-subtle)] min-w-[160px] text-right">
                  {/* Score & Priority Stack */}
                  <div className="flex md:flex-col items-center md:items-end gap-2 md:gap-1.5">
                    <div className="font-mono text-base font-bold tabular-nums text-[var(--fg)] leading-none">
                      {item.priority_score.toFixed(1)}
                    </div>
                    <PriorityBadge priority={item.priority} />
                  </div>

                  {/* Action Buttons */}
                  <div className="flex items-center gap-2 pt-0 md:pt-1">
                    {firstFindingId && (
                      <button
                        onClick={() => setInspectedFindingId(firstFindingId)}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md border border-[var(--border)] bg-[var(--surface-secondary)] hover:bg-[var(--surface-tertiary)] hover:border-[var(--muted)] text-[var(--fg)] transition cursor-pointer"
                      >
                        <span>Inspect</span>
                        <ArrowRight className="w-3.5 h-3.5 text-[var(--muted)]" />
                      </button>
                    )}
                    <Link
                      href={`/cses/${item.entity_id}`}
                      className="p-1.5 rounded-md border border-transparent hover:border-[var(--border)] hover:bg-[var(--surface-secondary)] text-[var(--muted)] hover:text-[var(--fg)] transition"
                      title="Navigate to entity"
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
