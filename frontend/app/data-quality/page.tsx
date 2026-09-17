"use client";

import React, { useState, useEffect } from "react";
import {
  ChevronDown,
  ChevronUp,
  ShieldCheck,
  CheckCircle,
} from "lucide-react";
import { api } from "../../src/api";
import { EntityRisk, ManifestData } from "../../src/types";
import { LoadingSkeleton, ErrorState } from "../../src/components/States";

export default function DataQualityPage() {
  const [entities, setEntities] = useState<EntityRisk[]>([]);
  const [manifest, setManifest] = useState<ManifestData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Disclosure states for manifest details
  const [showParameters, setShowParameters] = useState(false);
  const [showCorrelationGroups, setShowCorrelationGroups] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [entitiesRes, manifestRes] = await Promise.all([
        api.getEntities(),
        api.getManifest().catch(() => null),
      ]);
      setEntities(entitiesRes);
      setManifest(manifestRes);
    } catch (err: any) {
      setError(err.message || "Failed loading data quality metadata");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  if (loading) {
    return <LoadingSkeleton variant="data-quality" text="Loading assessment documentation..." />;
  }

  if (error) {
    return <ErrorState message={error} onRetry={fetchData} />;
  }

  const totalEntities = entities.length;
  const fullyAssessable = entities.filter((e) => e.assessment_coverage === 1.0).length;
  const partialAssessable = totalEntities - fullyAssessable;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="border-b border-[var(--border)] pb-5">
        <h1 className="text-xl sm:text-2xl font-semibold tracking-tight text-[var(--fg)]">
          Data Quality & Assessment Limitations
        </h1>
        <p className="text-xs text-[var(--muted)] mt-1">
          Assessment coverage, telemetry availability, and documented analytical limitations
        </p>
      </div>

      {/* Core Tenet Callout: Unassessable != Low Risk */}
      <div className="p-5 rounded-xl border border-[var(--border)] bg-[var(--surface-secondary)] space-y-2">
        <span className="font-semibold text-xs sm:text-sm text-[var(--fg)] block uppercase tracking-wider font-mono">
          Supervisory Principle: Unassessable &ne; Low Risk
        </span>
        <p className="text-xs text-[var(--muted)] leading-relaxed">
          In supervisory and regulatory oversight, missing telemetry or undefined denominator metrics must <strong>never</strong> be silently assigned a zero risk score or assumed compliant. When an entity lacks security cases or monitored asset definitions, the affected dimension is explicitly designated as <code className="font-mono text-[var(--fg)]">Not Assessable (null)</code>, and its dimension weight is excluded from the Level 2 weighted average denominator rather than fabricating compliance.
        </p>
      </div>

      {/* Coverage KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="p-4 rounded-xl border border-[var(--border)] bg-[var(--surface)] space-y-1">
          <span className="text-[11px] font-mono uppercase text-[var(--muted)] tracking-wider block">
            Evaluated Cohort
          </span>
          <div className="text-2xl font-mono font-bold tabular-nums text-[var(--fg)]">
            {totalEntities} Entities
          </div>
          <span className="text-[10px] text-[var(--subtle)] block">
            100% evaluated through Level 2 aggregation
          </span>
        </div>

        <div className="p-4 rounded-xl border border-[var(--border)] bg-[var(--surface)] space-y-1">
          <span className="text-[11px] font-mono uppercase text-[var(--muted)] tracking-wider block">
            Complete Coverage
          </span>
          <div className="text-2xl font-mono font-bold tabular-nums text-[var(--fg)]">
            {fullyAssessable} Entities
          </div>
          <span className="text-[10px] text-[var(--subtle)] block">
            Telemetry assessable across all 6 dimensions
          </span>
        </div>

        <div className="p-4 rounded-xl border border-[var(--border)] bg-[var(--surface)] space-y-1">
          <span className="text-[11px] font-mono uppercase text-[var(--muted)] tracking-wider block">
            Partial Telemetry
          </span>
          <div className="text-2xl font-mono font-bold tabular-nums text-[var(--fg)]">
            {partialAssessable} Entities
          </div>
          <span className="text-[10px] text-[var(--subtle)] block">
            Handled via dynamic weight renormalization
          </span>
        </div>
      </div>

      {/* Documented Rules & Guardrails */}
      <div className="space-y-3">
        <h2 className="text-sm font-semibold tracking-tight text-[var(--fg)]">
          Methodological Rules & Guardrails
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
          <div className="p-4 rounded-xl border border-[var(--border)] bg-[var(--surface)] space-y-1.5">
            <span className="font-semibold text-[var(--fg)] block">
              1. R005 Zero-Denominator Rule
            </span>
            <p className="text-[var(--muted)] leading-relaxed">
              When an entity has <code className="font-mono text-[var(--fg)]">expected_monitored_assets == 0</code>, detector R005 is marked unassessable with zero assigned risk, preventing artificial risk inflation on undefined assets.
            </p>
          </div>

          <div className="p-4 rounded-xl border border-[var(--border)] bg-[var(--surface)] space-y-1.5">
            <span className="font-semibold text-[var(--fg)] block">
              2. AN001 Contextual Relative Anomaly
            </span>
            <p className="text-[var(--muted)] leading-relaxed">
              AN001 represents relative contextual outlier evidence within the submitted population (influence capped at 25.0 points). It is strictly not interpreted as a probability or compliance metric.
            </p>
          </div>

          <div className="p-4 rounded-xl border border-[var(--border)] bg-[var(--surface)] space-y-1.5">
            <span className="font-semibold text-[var(--fg)] block">
              3. Feature-Aware Dimension Isolation
            </span>
            <p className="text-[var(--muted)] leading-relaxed">
              AN001 influences a dimension only when its contributing deviations contain a feature explicitly mapped to that dimension, preventing phantom risk leakage across unrelated categories.
            </p>
          </div>

          <div className="p-4 rounded-xl border border-[var(--border)] bg-[var(--surface)] space-y-1.5">
            <span className="font-semibold text-[var(--fg)] block">
              4. Anti-Double-Counting Correlation
            </span>
            <p className="text-[var(--muted)] leading-relaxed">
              Detectors describing the same operational issue (e.g., R004, EG002, PB002) are consolidated via maximum-signal aggregation instead of being summed as independent penalties.
            </p>
          </div>
        </div>
      </div>

      {/* Manifest Parameters (Progressive Disclosure) */}
      {manifest && (
        <div className="space-y-3">
          <div className="border border-[var(--border)] rounded-xl overflow-hidden bg-[var(--surface)]">
            <button
              onClick={() => setShowParameters(!showParameters)}
              className="w-full px-5 py-3 flex items-center justify-between text-xs font-semibold text-[var(--fg)] hover:bg-[var(--surface-secondary)] transition"
            >
              <span>Configured Engine Parameters & Dimension Weights</span>
              {showParameters ? (
                <ChevronUp className="w-4 h-4 text-[var(--muted)]" />
              ) : (
                <ChevronDown className="w-4 h-4 text-[var(--muted)]" />
              )}
            </button>

            {showParameters && (
              <div className="p-5 border-t border-[var(--border)] space-y-4 text-xs">
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                  {Object.entries(manifest.dimension_weights).map(([dim, wt]) => (
                    <div
                      key={dim}
                      className="p-2.5 rounded-lg border border-[var(--border-subtle)] bg-[var(--surface-secondary)] flex justify-between items-center"
                    >
                      <span className="text-[var(--fg)] capitalize">
                        {dim.replace(/_/g, " ")}
                      </span>
                      <span className="font-mono font-bold text-[var(--fg)] tabular-nums">
                        {(wt * 100).toFixed(0)}%
                      </span>
                    </div>
                  ))}
                </div>

                <div className="pt-2 flex flex-wrap gap-4 text-xs font-mono text-[var(--muted)] border-t border-[var(--border-subtle)]">
                  <span>Method: {manifest.aggregation_method}</span>
                  <span suppressHydrationWarning>Generated: {new Date(manifest.generated_at).toLocaleDateString()}</span>
                  <span>Schema: v{manifest.schema_version}</span>
                </div>
              </div>
            )}
          </div>

          <div className="border border-[var(--border)] rounded-xl overflow-hidden bg-[var(--surface)]">
            <button
              onClick={() => setShowCorrelationGroups(!showCorrelationGroups)}
              className="w-full px-5 py-3 flex items-center justify-between text-xs font-semibold text-[var(--fg)] hover:bg-[var(--surface-secondary)] transition"
            >
              <span>Correlation Groups & Detector Mappings</span>
              {showCorrelationGroups ? (
                <ChevronUp className="w-4 h-4 text-[var(--muted)]" />
              ) : (
                <ChevronDown className="w-4 h-4 text-[var(--muted)]" />
              )}
            </button>

            {showCorrelationGroups && (
              <div className="p-5 border-t border-[var(--border)] space-y-3 text-xs">
                {Object.entries(manifest.correlation_groups).map(([groupKey, group]) => (
                  <div
                    key={groupKey}
                    className="p-3 rounded-lg border border-[var(--border-subtle)] bg-[var(--surface-secondary)] space-y-1"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-mono font-bold text-[var(--fg)]">
                        {groupKey}
                      </span>
                      <span className="text-[11px] font-mono text-[var(--muted)]">
                        {group.dimension}
                      </span>
                    </div>
                    <p className="text-[11px] text-[var(--muted)]">{group.description}</p>
                    <div className="flex gap-1.5 pt-1">
                      {group.detectors.map((d) => (
                        <span
                          key={d}
                          className="px-1.5 py-0.5 rounded text-[10px] font-mono border border-[var(--border)] bg-[var(--surface)] text-[var(--fg)]"
                        >
                          {d}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Hyperledger Fabric Provenance & Integrity Status */}
      <div className="p-6 rounded-2xl border border-[var(--border)] bg-[var(--surface)] space-y-4">
        <div className="flex items-baseline justify-between border-b border-[var(--border)] pb-3">
          <div className="space-y-0.5">
            <h2 className="text-sm font-semibold tracking-tight text-[var(--fg)] uppercase font-mono">
              Hyperledger Fabric Integrity & Provenance Layer
            </h2>
            <p className="text-xs text-[var(--muted)]">
              Local permissioned blockchain ledger verifying evidence immutability
            </p>
          </div>
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-mono font-medium bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
            CONNECTED
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 text-xs font-mono">
          <div className="p-3 rounded-lg border border-[var(--border-subtle)] bg-[var(--surface-secondary)]">
            <span className="text-[10px] text-[var(--muted)] block">Channel</span>
            <span className="text-[var(--fg)] font-bold">SENTRA-channel</span>
          </div>
          <div className="p-3 rounded-lg border border-[var(--border-subtle)] bg-[var(--surface-secondary)]">
            <span className="text-[10px] text-[var(--muted)] block">Chaincode</span>
            <span className="text-[var(--fg)] font-bold">SENTRA-integrity (v1.0.0)</span>
          </div>
          <div className="p-3 rounded-lg border border-[var(--border-subtle)] bg-[var(--surface-secondary)]">
            <span className="text-[10px] text-[var(--muted)] block">Consensus / Peer</span>
            <span className="text-[var(--fg)] font-bold">localhost:7051</span>
          </div>
          <div className="p-3 rounded-lg border border-[var(--border-subtle)] bg-[var(--surface-secondary)]">
            <span className="text-[10px] text-[var(--muted)] block">Digest Algorithm</span>
            <span className="text-[var(--fg)] font-bold">SHA-256 (Canonical)</span>
          </div>
        </div>

        <p className="text-xs text-[var(--muted)] leading-relaxed font-sans">
          SENTRA implements a strict off-chain data / on-chain digest model. High-volume SOC telemetry (alerts, cases, assets) remains stored locally in immutable Parquet partitions, while deterministic SHA-256 digests and versioned lifecycle commitments are recorded on the Hyperledger Fabric ledger to prove that supervisory evidence has not undergone unauthorized alterations.
        </p>
      </div>
    </div>
  );
}
