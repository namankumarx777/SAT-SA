import React from "react";
import { AlertCircle, RotateCcw } from "lucide-react";

export function LoadingSkeleton({
  text = "Loading supervisory assessment...",
}: {
  text?: string;
}) {
  return (
    <div className="space-y-6 animate-pulse py-4">
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <div className="h-4 w-32 bg-[var(--surface-secondary)] rounded" />
          <div className="h-7 w-64 bg-[var(--surface-secondary)] rounded" />
        </div>
        <div className="h-8 w-24 bg-[var(--surface-secondary)] rounded" />
      </div>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {[1, 2, 3, 4, 5].map((i) => (
          <div
            key={i}
            className="p-4 rounded-xl border border-[var(--border)] bg-[var(--surface)] space-y-2"
          >
            <div className="h-3 w-20 bg-[var(--surface-secondary)] rounded" />
            <div className="h-8 w-16 bg-[var(--surface-secondary)] rounded" />
          </div>
        ))}
      </div>

      <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-6 space-y-4">
        <div className="h-4 w-48 bg-[var(--surface-secondary)] rounded" />
        <div className="space-y-2">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div
              key={i}
              className="h-10 w-full bg-[var(--surface-secondary)] rounded"
            />
          ))}
        </div>
      </div>

      <p className="text-xs text-[var(--muted)] font-mono text-center">{text}</p>
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
        {message || "The local assessment engine may be unavailable or offline."} Check that the local SAT-SA backend is running.
      </p>

      {onRetry && (
        <div className="pt-2">
          <button
            onClick={onRetry}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium border border-[var(--border)] bg-[var(--surface-secondary)] hover:bg-[var(--surface-tertiary)] text-[var(--fg)] transition"
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
          className="mt-3 inline-flex items-center text-xs font-medium text-[var(--fg)] hover:underline"
        >
          Reset active filters &rarr;
        </button>
      )}
    </div>
  );
}
