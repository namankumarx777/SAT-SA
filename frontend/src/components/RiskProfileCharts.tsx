"use client";

import React from "react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
} from "recharts";
import { FALLBACK_RISK_BAND_THRESHOLDS, RiskBandThresholds } from "../types";

interface DimensionScoreItem {
  dimension: string;
  score: number | null;
  weight: number;
}

export function RiskDimensionBarChart({
  data,
  thresholds = FALLBACK_RISK_BAND_THRESHOLDS,
}: {
  data: DimensionScoreItem[];
  thresholds?: RiskBandThresholds;
}) {
  const chartData = data.map((d) => ({
    dimension: d.dimension,
    score: d.score !== null ? d.score : 0,
    isAssessable: d.score !== null,
    weight: `${(d.weight * 100).toFixed(0)}%`,
  }));

const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const item = payload[0].payload;
    return (
      <div className="p-3 rounded-lg border border-[var(--border)] bg-[var(--bg)]/80 backdrop-blur-md shadow-xl text-xs space-y-1 font-mono">
        <p className="font-medium text-[var(--muted)] uppercase tracking-wider text-[10px]">{item.dimension}</p>
        <div className="flex items-center justify-between gap-4 pt-0.5">
          <p className="text-[var(--muted)]">Score:</p>
          {item.isAssessable ? (
            <span className="font-bold text-[var(--fg)] tabular-nums text-sm">
              {item.score.toFixed(1)} <span className="text-[10px] text-[var(--muted)] font-normal">/ 100</span>
            </span>
          ) : (
            <span className="italic text-[var(--muted)]">N/A</span>
          )}
        </div>
        <p className="text-[var(--subtle)] text-[10px]">Weight: {item.weight}</p>
      </div>
    );
  }
  return null;
};

  return (
    <div className="w-full h-64">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={chartData}
          layout="vertical"
          margin={{ top: 8, right: 24, left: 32, bottom: 8 }}
        >
          <XAxis
            type="number"
            domain={[0, 100]}
            stroke="var(--muted)"
            fontSize={10}
            tickLine={false}
            axisLine={{ stroke: "var(--border)" }}
            tickFormatter={(v) => `${v}`}
          />
          <YAxis
            type="category"
            dataKey="dimension"
            stroke="var(--muted)"
            fontSize={11}
            tickLine={false}
            axisLine={false}
            width={120}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: "var(--surface-secondary)", opacity: 0.5 }} />
          <Bar dataKey="score" radius={[0, 4, 4, 0]} maxBarSize={16}>
            {chartData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={
                  !entry.isAssessable
                    ? "var(--border)"
                    : entry.score >= thresholds.critical
                    ? "var(--risk-critical-dot)"
                    : entry.score >= thresholds.high
                    ? "var(--risk-high-dot)"
                    : entry.score >= thresholds.moderate
                    ? "var(--risk-moderate-dot)"
                    : "var(--fg)"
                }
                opacity={entry.isAssessable ? 0.9 : 0.4}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
