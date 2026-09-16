import React from "react";
import { AlertCircle, RotateCcw } from "lucide-react";

export function SkeletonBlock({
  className = "h-4 w-full",
}: {
  className?: string;
}) {
  return <div className={`skeleton-shimmer rounded-md ${className}`} />;
}

export function OverviewSkeleton() {
  return (
    <div className="space-y-8 animate-fade-in py-2">
      {/* Header & National Context */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-2">
          <SkeletonBlock className="h-4 w-36" />
          <SkeletonBlock className="h-8 w-72" />
          <SkeletonBlock className="h-4 w-96 max-w-full" />
        </div>
        <div className="flex items-center gap-2">
          <SkeletonBlock className="h-9 w-32 rounded-lg" />
          <SkeletonBlock className="h-9 w-28 rounded-lg" />
        </div>
      </div>

      {/* 5 Executive KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 sm:gap-4">
        {[1, 2, 3, 4, 5].map((i) => (
          <div
            key={i}
            className="p-4 rounded-xl border border-[var(--border)] bg-[var(--surface)] space-y-2.5 shadow-sm"
          >
            <div className="flex items-center justify-between">
              <SkeletonBlock className="h-3 w-20" />
              <SkeletonBlock className="h-3.5 w-3.5 rounded-full" />
            </div>
            <SkeletonBlock className="h-7 w-16" />
            <SkeletonBlock className="h-2.5 w-24" />
          </div>
        ))}
      </div>

      {/* 2-Column Risk Distribution & Quick Insights */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 p-6 rounded-2xl border border-[var(--border)] bg-[var(--surface)] space-y-4 shadow-sm">
          <div className="flex items-center justify-between border-b border-[var(--border)] pb-3">
            <SkeletonBlock className="h-4 w-48" />
            <SkeletonBlock className="h-4 w-28" />
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
            {[1, 2, 3, 4].map((i) => (
              <div
                key={i}
                className="p-3 rounded-lg border border-[var(--border)] bg-[var(--surface-secondary)] space-y-2"
              >
                <SkeletonBlock className="h-3 w-16" />
                <SkeletonBlock className="h-6 w-12" />
              </div>
            ))}
          </div>
          <SkeletonBlock className="h-24 w-full rounded-xl" />
        </div>

        <div className="p-6 rounded-2xl border border-[var(--border)] bg-[var(--surface)] space-y-4 shadow-sm">
          <div className="flex items-center justify-between border-b border-[var(--border)] pb-3">
            <SkeletonBlock className="h-4 w-36" />
            <SkeletonBlock className="h-3.5 w-16" />
          </div>
          <div className="space-y-3 pt-1">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="flex items-center justify-between gap-2">
                <SkeletonBlock className="h-4 w-32" />
                <SkeletonBlock className="h-4 w-12" />
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Ranked Entity Table */}
      <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-6 space-y-4 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[var(--border)] pb-4">
          <div className="space-y-1">
            <SkeletonBlock className="h-5 w-44" />
            <SkeletonBlock className="h-3 w-64" />
          </div>
          <div className="flex items-center gap-2">
            <SkeletonBlock className="h-9 w-48 rounded-lg" />
            <SkeletonBlock className="h-9 w-24 rounded-lg" />
          </div>
        </div>

        <div className="space-y-2 pt-2">
          <SkeletonBlock className="h-8 w-full rounded-md" />
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <SkeletonBlock key={i} className="h-14 w-full rounded-lg" />
          ))}
        </div>
      </div>
    </div>
  );
}

export function CSERegistrySkeleton() {
  return (
    <div className="space-y-6 animate-fade-in py-1">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-3">
        <div className="space-y-1">
          <SkeletonBlock className="h-7 w-60 rounded-lg" />
          <SkeletonBlock className="h-3.5 w-80 max-w-full rounded" />
        </div>
        <div className="flex items-center gap-2">
          <SkeletonBlock className="h-4 w-16 rounded" />
          <SkeletonBlock className="h-4 w-20 rounded" />
          <SkeletonBlock className="h-4 w-16 rounded" />
        </div>
      </div>

      {/* Floating Filter Toolbar */}
      <div className="p-2.5 sm:p-3 rounded-xl border border-[var(--border)] bg-[var(--surface)] shadow-xs flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2">
          <SkeletonBlock className="h-8 w-60 rounded-md" />
          <SkeletonBlock className="h-8 w-48 rounded-md" />
          <SkeletonBlock className="h-8 w-28 rounded-lg" />
          <SkeletonBlock className="h-8 w-32 rounded-lg" />
        </div>
        <SkeletonBlock className="h-4 w-24 rounded mr-1" />
      </div>

      {/* Registry Table */}
      <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] shadow-xs overflow-hidden">
        <div className="p-4 border-b border-[var(--border)] bg-[var(--surface-secondary)]/50">
          <SkeletonBlock className="h-4 w-full rounded" />
        </div>
        <div className="divide-y divide-[var(--border-subtle)]">
          {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
            <div key={i} className="flex items-center justify-between gap-4 px-5 py-4">
              <div className="space-y-1.5 w-32">
                <SkeletonBlock className="h-4 w-20 rounded" />
                <SkeletonBlock className="h-3 w-28 rounded" />
              </div>
              <SkeletonBlock className="h-4 w-20 rounded" />
              <SkeletonBlock className="h-5 w-16 rounded ml-auto" />
              <div className="flex items-center gap-2 w-24">
                <SkeletonBlock className="h-2 w-2 rounded-full" />
                <SkeletonBlock className="h-4 w-16 rounded" />
              </div>
              <div className="hidden md:flex items-center gap-8 justify-end">
                <SkeletonBlock className="h-4 w-10 rounded" />
                <SkeletonBlock className="h-4 w-10 rounded" />
                <SkeletonBlock className="h-4 w-10 rounded" />
                <SkeletonBlock className="h-4 w-10 rounded" />
                <SkeletonBlock className="h-4 w-12 rounded" />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export function CSEDetailSkeleton() {
  return (
    <div className="space-y-8 animate-fade-in py-2">
      {/* Top Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-4">
          <SkeletonBlock className="h-4 w-28" />
          <SkeletonBlock className="h-4 w-24" />
        </div>
        <div className="flex items-center gap-2">
          <SkeletonBlock className="h-8 w-32 rounded-lg" />
          <SkeletonBlock className="h-8 w-28 rounded-lg" />
        </div>
      </div>

      {/* Identity & Risk Hero Card */}
      <div className="p-6 sm:p-8 rounded-2xl border border-[var(--border)] bg-[var(--surface)] shadow-sm">
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-6">
          <div className="space-y-2 flex-1">
            <div className="flex items-center gap-2">
              <SkeletonBlock className="h-3.5 w-20" />
              <SkeletonBlock className="h-3.5 w-24" />
              <SkeletonBlock className="h-3.5 w-28" />
            </div>
            <SkeletonBlock className="h-9 w-72 max-w-full" />
            <SkeletonBlock className="h-4 w-60 pt-1" />
          </div>

          <div className="p-5 rounded-xl border border-[var(--border)] bg-[var(--surface-secondary)] min-w-[200px] space-y-2 text-right">
            <SkeletonBlock className="h-3 w-28 ml-auto" />
            <SkeletonBlock className="h-10 w-24 ml-auto" />
            <SkeletonBlock className="h-5 w-20 rounded-full ml-auto" />
          </div>
        </div>
      </div>

      {/* "Why This Entity Is Flagged" Box */}
      <div className="p-6 sm:p-8 rounded-2xl border border-[var(--border)] bg-[var(--surface)] space-y-4 shadow-sm">
        <div className="flex items-center justify-between border-b border-[var(--border)] pb-3">
          <SkeletonBlock className="h-4 w-48" />
          <SkeletonBlock className="h-3.5 w-36" />
        </div>
        <div className="space-y-3 pt-1">
          <SkeletonBlock className="h-6 w-40" />
          <SkeletonBlock className="h-4 w-full" />
          <SkeletonBlock className="h-16 w-full rounded-xl" />
        </div>
      </div>

      {/* 6 Dimension Grid Cards */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <SkeletonBlock className="h-4 w-44" />
          <SkeletonBlock className="h-3 w-32" />
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div
              key={i}
              className="p-5 rounded-xl border border-[var(--border)] bg-[var(--surface)] space-y-3 shadow-sm"
            >
              <div className="flex items-center justify-between">
                <SkeletonBlock className="h-4 w-28" />
                <SkeletonBlock className="h-3.5 w-10" />
              </div>
              <SkeletonBlock className="h-7 w-20" />
              <SkeletonBlock className="h-2 w-full rounded-full" />
              <SkeletonBlock className="h-3.5 w-40" />
            </div>
          ))}
        </div>
      </div>

      {/* Visual Risk Profile Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="p-6 rounded-2xl border border-[var(--border)] bg-[var(--surface)] space-y-4 shadow-sm">
          <SkeletonBlock className="h-4 w-40" />
          <SkeletonBlock className="h-56 w-full rounded-xl" />
        </div>
        <div className="p-6 rounded-2xl border border-[var(--border)] bg-[var(--surface)] space-y-4 shadow-sm">
          <SkeletonBlock className="h-4 w-40" />
          <SkeletonBlock className="h-56 w-full rounded-xl" />
        </div>
      </div>

      {/* Risk Contributions Table */}
      <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-6 space-y-4 shadow-sm">
        <div className="flex items-center justify-between border-b border-[var(--border)] pb-3">
          <SkeletonBlock className="h-4 w-48" />
          <SkeletonBlock className="h-3.5 w-24" />
        </div>
        <div className="space-y-2 pt-1">
          <SkeletonBlock className="h-8 w-full rounded-md" />
          {[1, 2, 3, 4, 5].map((i) => (
            <SkeletonBlock key={i} className="h-12 w-full rounded-lg" />
          ))}
        </div>
      </div>
    </div>
  );
}

export function ReviewQueueSkeleton() {
  return (
    <div className="space-y-8 animate-fade-in py-2">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <SkeletonBlock className="h-4 w-32" />
            <SkeletonBlock className="h-4 w-20 rounded-full" />
          </div>
          <SkeletonBlock className="h-8 w-64" />
          <SkeletonBlock className="h-4 w-96 max-w-full" />
        </div>
      </div>

      {/* Triage Callout Box */}
      <div className="p-4 rounded-xl border border-[var(--border)] bg-[var(--surface-secondary)] space-y-2">
        <SkeletonBlock className="h-4 w-48" />
        <SkeletonBlock className="h-3.5 w-full" />
      </div>

      {/* Tabs & Filter */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <SkeletonBlock className="h-9 w-20 rounded-lg" />
          <SkeletonBlock className="h-9 w-20 rounded-lg" />
          <SkeletonBlock className="h-9 w-20 rounded-lg" />
          <SkeletonBlock className="h-9 w-20 rounded-lg" />
        </div>
        <SkeletonBlock className="h-9 w-64 rounded-lg" />
      </div>

      {/* Queue Cards */}
      <div className="space-y-3.5">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <div
            key={i}
            className="p-5 sm:p-6 rounded-[18px] border border-[var(--border)] bg-[var(--surface)] flex flex-col md:flex-row md:items-center justify-between gap-5 shadow-xs"
          >
            <div className="flex items-start gap-4 flex-1">
              <SkeletonBlock className="h-4 w-5 rounded shrink-0" />
              <div className="space-y-2 flex-1">
                <SkeletonBlock className="h-3.5 w-36 rounded" />
                <SkeletonBlock className="h-5 w-4/5 rounded" />
                <SkeletonBlock className="h-3.5 w-48 rounded" />
              </div>
            </div>
            <div className="flex md:flex-col items-center md:items-end justify-between md:justify-center gap-3 shrink-0">
              <SkeletonBlock className="h-7 w-16 rounded" />
              <SkeletonBlock className="h-7 w-20 rounded-full" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export function AnalyticsSkeleton() {
  return (
    <div className="space-y-8 animate-fade-in py-2">
      <div className="space-y-2">
        <SkeletonBlock className="h-4 w-32" />
        <SkeletonBlock className="h-8 w-60" />
        <SkeletonBlock className="h-4 w-80 max-w-full" />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="p-5 rounded-xl border border-[var(--border)] bg-[var(--surface)] space-y-2 shadow-sm">
            <SkeletonBlock className="h-3 w-28" />
            <SkeletonBlock className="h-7 w-20" />
            <SkeletonBlock className="h-3 w-36" />
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="p-6 rounded-2xl border border-[var(--border)] bg-[var(--surface)] space-y-4 shadow-sm">
          <SkeletonBlock className="h-4 w-48" />
          <SkeletonBlock className="h-64 w-full rounded-xl" />
        </div>
        <div className="p-6 rounded-2xl border border-[var(--border)] bg-[var(--surface)] space-y-4 shadow-sm">
          <SkeletonBlock className="h-4 w-48" />
          <SkeletonBlock className="h-64 w-full rounded-xl" />
        </div>
      </div>
    </div>
  );
}

export function DataQualitySkeleton() {
  return (
    <div className="space-y-8 animate-fade-in py-2">
      <div className="space-y-2">
        <SkeletonBlock className="h-4 w-36" />
        <SkeletonBlock className="h-8 w-64" />
        <SkeletonBlock className="h-4 w-80 max-w-full" />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="p-5 rounded-xl border border-[var(--border)] bg-[var(--surface)] space-y-2 shadow-sm">
            <SkeletonBlock className="h-3 w-32" />
            <SkeletonBlock className="h-7 w-20" />
            <SkeletonBlock className="h-3 w-40" />
          </div>
        ))}
      </div>

      <div className="p-6 rounded-2xl border border-[var(--border)] bg-[var(--surface)] space-y-4 shadow-sm">
        <SkeletonBlock className="h-4 w-44" />
        <div className="space-y-2">
          {[1, 2, 3, 4, 5].map((i) => (
            <SkeletonBlock key={i} className="h-10 w-full rounded-lg" />
          ))}
        </div>
      </div>
    </div>
  );
}

export function LoadingSkeleton({
  text = "Loading supervisory assessment...",
  variant = "default",
}: {
  text?: string;
  variant?: "default" | "overview" | "detail" | "table" | "queue" | "analytics" | "data-quality";
}) {
  if (variant === "overview") return <OverviewSkeleton />;
  if (variant === "detail") return <CSEDetailSkeleton />;
  if (variant === "table") return <CSERegistrySkeleton />;
  if (variant === "queue") return <ReviewQueueSkeleton />;
  if (variant === "analytics") return <AnalyticsSkeleton />;
  if (variant === "data-quality") return <DataQualitySkeleton />;

  return (
    <div className="space-y-6 py-4 animate-fade-in">
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <SkeletonBlock className="h-4 w-32" />
          <SkeletonBlock className="h-7 w-64" />
        </div>
        <SkeletonBlock className="h-8 w-24 rounded-lg" />
      </div>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {[1, 2, 3, 4, 5].map((i) => (
          <div
            key={i}
            className="p-4 rounded-xl border border-[var(--border)] bg-[var(--surface)] space-y-2 shadow-sm"
          >
            <SkeletonBlock className="h-3 w-20" />
            <SkeletonBlock className="h-8 w-16" />
          </div>
        ))}
      </div>

      <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-6 space-y-4 shadow-sm">
        <SkeletonBlock className="h-4 w-48" />
        <div className="space-y-2">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <SkeletonBlock
              key={i}
              className="h-10 w-full rounded-md"
            />
          ))}
        </div>
      </div>

      {text && <p className="text-xs text-[var(--muted)] font-mono text-center pt-2">{text}</p>}
    </div>
  );
}

export function ErrorState({
  message,
  onRetry,
}: {
  message: string;
  onRetry?: () => void;
}) {
  return (
    <div className="p-6 rounded-xl border border-[var(--border)] bg-[var(--surface)] space-y-3 max-w-lg my-8 mx-auto">
      <div className="flex items-center gap-2 text-sm font-medium text-[var(--fg)]">
        <AlertCircle className="w-4 h-4 text-[var(--risk-critical-dot)] shrink-0" />
        <span>Unable to load supervisory assessment</span>
      </div>

      <p className="text-xs text-[var(--muted)] leading-relaxed">
        {message || "The local assessment engine may be unavailable or offline."} Check that the local SENTRA backend is running.
      </p>

      {onRetry && (
        <div className="pt-2">
          <button
            onClick={onRetry}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium border border-[var(--border)] bg-[var(--surface-secondary)] hover:bg-[var(--surface-tertiary)] text-[var(--fg)] transition cursor-pointer"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Retry connection</span>
          </button>
        </div>
      )}
    </div>
  );
}

export function EmptyState({
  title = "No records found",
  description = "No items match the active filters.",
  onReset,
}: {
  title?: string;
  description?: string;
  onReset?: () => void;
}) {
  return (
    <div className="p-8 text-center rounded-xl border border-[var(--border)] bg-[var(--surface)] space-y-2 max-w-md mx-auto my-6">
      <p className="text-sm font-medium text-[var(--fg)]">{title}</p>
      <p className="text-xs text-[var(--muted)]">{description}</p>
      {onReset && (
        <button
          onClick={onReset}
          className="mt-3 inline-flex items-center text-xs font-medium text-[var(--fg)] hover:underline cursor-pointer"
        >
          Reset active filters &rarr;
        </button>
      )}
    </div>
  );
}
