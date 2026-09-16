"use client";

import React, { useState, useEffect } from "react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
} from "recharts";
import { api } from "../../src/api";
import { EntityRisk, ReviewQueueItem, ManifestData } from "../../src/types";
import { LoadingSkeleton, ErrorState } from "../../src/components/States";

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="p-3 rounded-lg border border-[var(--border)] bg-[var(--bg)]/80 backdrop-blur-md shadow-xl text-xs font-mono space-y-1">
        <p className="font-medium text-[var(--muted)] uppercase tracking-wider text-[10px]">{label}</p>
        <div className="flex items-center gap-2 pt-0.5">
          <span 
            className="w-1.5 h-1.5 rounded-full" 
            style={{ backgroundColor: payload[0].payload?.fill || payload[0].color || "var(--fg)" }}
          />
          <span className="font-bold text-[var(--fg)] tabular-nums text-sm">
            {payload[0].value}
          </span>
        </div>
      </div>
    );
  }
  return null;
};

export default function AnalyticsPage() {
  const [entities, setEntities] = useState<EntityRisk[]>([]);
  const [queue, setQueue] = useState<ReviewQueueItem[]>([]);
  const [manifest, setManifest] = useState<ManifestData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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
      setManifest(manifestRes);
    } catch (err: any) {
      setError(err.message || "Failed loading analytics");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  if (loading) {
    return <LoadingSkeleton variant="analytics" text="Loading supervisory analytics..." />;
  }

  if (error) {
    return <ErrorState message={error} onRetry={fetchData} />;
  }

  // 1. Sector Risk Average
  const sectorRiskData = Object.entries(
    entities.reduce((acc, e) => {
      const sector = e.sector || "Energy";
      if (!acc[sector]) acc[sector] = { total: 0, count: 0 };
      acc[sector].total += e.overall_score;
      acc[sector].count += 1;
      return acc;
    }, {} as Record<string, { total: number; count: number }>),
  ).map(([sector, data]) => ({
    sector,
    avgScore: Number((data.total / data.count).toFixed(2)),
    count: data.count,
  }));

  // 2. Population Dimension Averages
  const dimensionAverages = [
    {
      dimension: "Escalation",
      avg:
        entities.reduce((sum, e) => sum + (e.escalation_score || 0), 0) /
        entities.length,
    },
    {
      dimension: "Investigation",
      avg:
        entities.reduce((sum, e) => sum + (e.investigation_score || 0), 0) /
        entities.length,
    },
    {
      dimension: "Remediation",
      avg:
        entities.reduce((sum, e) => sum + (e.remediation_score || 0), 0) /
        entities.length,
    },
    {
      dimension: "Monitoring",
      avg:
        entities.reduce((sum, e) => sum + (e.monitoring_score || 0), 0) /
        entities.length,
    },
    {
      dimension: "Operational Disc.",
      avg:
        entities.reduce(
          (sum, e) => sum + (e.operational_discipline_score || 0),
          0,
        ) / entities.length,
    },
    {
      dimension: "Cyber Resilience",
      avg:
        entities.reduce((sum, e) => sum + (e.cyber_resilience_score || 0), 0) /
        entities.length,
    },
  ].map((d) => ({
    ...d,
    avg: Number(d.avg.toFixed(1)),
  }));

  // 3. Risk Band Distribution
  const bandCounts = [
    { band: "LOW", count: entities.filter((e) => e.risk_band === "LOW").length },
    { band: "MODERATE", count: entities.filter((e) => e.risk_band === "MODERATE").length },
    { band: "HIGH", count: entities.filter((e) => e.risk_band === "HIGH").length },
    { band: "CRITICAL", count: entities.filter((e) => e.risk_band === "CRITICAL").length },
  ];

  // 4. Review Queue Urgency Breakdown
  const queueCounts = [
    { priority: "HIGH", count: queue.filter((q) => q.priority === "HIGH").length },
    { priority: "MEDIUM", count: queue.filter((q) => q.priority === "MEDIUM").length },
    { priority: "LOW", count: queue.filter((q) => q.priority === "LOW").length },
  ];



  return (
    <div className="space-y-6">
      {/* Sticky Header Container */}
      <div className="sticky top-0 z-20 bg-[var(--bg)] -mt-4 sm:-mt-6 lg:-mt-8 pt-4 sm:pt-6 lg:pt-8 pb-3 border-b border-[var(--border)]">
        <div>
          <h1 className="text-xl sm:text-2xl font-semibold tracking-tight text-[var(--fg)]">
            Supervisory Analytics
          </h1>
          <p className="text-xs text-[var(--muted)] mt-0.5">
            Comparative cohort analysis across evaluated Critical Sector Entities
          </p>
        </div>
      </div>

      {/* Synthetic Cohort Notice */}
      <div className="p-3 sm:p-3.5 rounded-xl border border-[var(--border)] bg-[var(--surface-secondary)] text-xs text-[var(--muted)] leading-relaxed shadow-xs">
        <span className="font-semibold text-[var(--fg)]">Cohort Context: </span>
        The demonstrator operates over a controlled cohort of 12 entities (5,000 alerts). The charts below illustrate comparative supervisory distributions rather than national statistical extrapolation.
      </div>

      {/* 4 Focused Visualizations (2x2 Grid) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 md:gap-12 py-4">
        {/* 1. Risk by Sector */}
        <div className="space-y-4">
          <div className="border-b border-[var(--border-subtle)] pb-2">
            <span className="text-[11px] font-mono uppercase text-[var(--muted)] tracking-wider block">
              Average Risk by Sector
            </span>
            <span className="text-[11px] text-[var(--subtle)]">
              Mean Level 2 score per infrastructure sector
            </span>
          </div>

          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={sectorRiskData} layout="vertical" margin={{ left: 24, right: 16 }}>
                <XAxis type="number" domain={[0, 100]} stroke="var(--muted)" fontSize={10} tickLine={false} axisLine={{ stroke: "var(--border)" }} />
                <YAxis type="category" dataKey="sector" stroke="var(--muted)" fontSize={11} tickLine={false} axisLine={false} width={100} />
                <Tooltip content={<CustomTooltip />} cursor={{ fill: "var(--surface-secondary)", opacity: 0.5 }} />
                <Bar dataKey="avgScore" fill="var(--fg)" radius={[0, 4, 4, 0]} maxBarSize={14} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* 2. Dimension Risk Averages */}
        <div className="space-y-4">
          <div className="border-b border-[var(--border-subtle)] pb-2">
            <span className="text-[11px] font-mono uppercase text-[var(--muted)] tracking-wider block">
              Population Dimension Averages
            </span>
            <span className="text-[11px] text-[var(--subtle)]">
              Mean score per operational dimension across 12 entities
            </span>
          </div>

          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={dimensionAverages} layout="vertical" margin={{ left: 24, right: 16 }}>
                <XAxis type="number" domain={[0, 100]} stroke="var(--muted)" fontSize={10} tickLine={false} axisLine={{ stroke: "var(--border)" }} />
                <YAxis type="category" dataKey="dimension" stroke="var(--muted)" fontSize={11} tickLine={false} axisLine={false} width={110} />
                <Tooltip content={<CustomTooltip />} cursor={{ fill: "var(--surface-secondary)", opacity: 0.5 }} />
                <Bar dataKey="avg" fill="var(--fg)" radius={[0, 4, 4, 0]} maxBarSize={14} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* 3. Risk Band Distribution */}
        <div className="space-y-4">
          <div className="border-b border-[var(--border-subtle)] pb-2">
            <span className="text-[11px] font-mono uppercase text-[var(--muted)] tracking-wider block">
              Risk Band Counts
            </span>
            <span className="text-[11px] text-[var(--subtle)]">
              Entity count by supervisory risk tier
            </span>
          </div>

          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={bandCounts} margin={{ left: 0, right: 16 }}>
                <XAxis dataKey="band" stroke="var(--muted)" fontSize={11} tickLine={false} axisLine={{ stroke: "var(--border)" }} />
                <YAxis type="number" stroke="var(--muted)" fontSize={10} tickLine={false} axisLine={false} allowDecimals={false} />
                <Tooltip content={<CustomTooltip />} cursor={{ fill: "var(--surface-secondary)", opacity: 0.5 }} />
                <Bar dataKey="count" radius={[4, 4, 0, 0]} maxBarSize={28}>
                  {bandCounts.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={
                        entry.band === "CRITICAL"
                          ? "var(--risk-critical-dot)"
                          : entry.band === "HIGH"
                          ? "var(--risk-high-dot)"
                          : entry.band === "MODERATE"
                          ? "var(--risk-moderate-dot)"
                          : "var(--risk-low-dot)"
                      }
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* 4. Review Queue Urgency Breakdown */}
        <div className="space-y-4">
          <div className="border-b border-[var(--border-subtle)] pb-2">
            <span className="text-[11px] font-mono uppercase text-[var(--muted)] tracking-wider block">
              Review Queue Urgency
            </span>
            <span className="text-[11px] text-[var(--subtle)]">
              Inspector triage distribution ({queue.length} total items)
            </span>
          </div>

          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={queueCounts} margin={{ left: 0, right: 16 }}>
                <XAxis dataKey="priority" stroke="var(--muted)" fontSize={11} tickLine={false} axisLine={{ stroke: "var(--border)" }} />
                <YAxis type="number" stroke="var(--muted)" fontSize={10} tickLine={false} axisLine={false} allowDecimals={false} />
                <Tooltip content={<CustomTooltip />} cursor={{ fill: "var(--surface-secondary)", opacity: 0.5 }} />
                <Bar dataKey="count" radius={[4, 4, 0, 0]} maxBarSize={28}>
                  {queueCounts.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={
                        entry.priority === "HIGH"
                          ? "var(--risk-high-dot)"
                          : entry.priority === "MEDIUM"
                          ? "var(--risk-moderate-dot)"
                          : "var(--muted)"
                      }
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
