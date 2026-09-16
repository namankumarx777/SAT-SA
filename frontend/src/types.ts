export type RiskBand = "LOW" | "MODERATE" | "HIGH" | "CRITICAL";
export type PriorityLevel = "HIGH" | "MEDIUM" | "LOW";
export type RecordType = "ENTITY" | "FINDING" | "CASE" | "ALERT" | "ASSET";

export type IntegrityState = "VERIFIED" | "MISMATCH" | "NOT_REGISTERED" | "UNAVAILABLE";

export interface BlockchainStatus {
  status: string;
  network: string;
  channel: string;
  chaincode: string;
  chaincode_version: string;
  peer_endpoint: string;
  is_connected: boolean;
  total_records: number;
  mode: string;
}

export interface VerificationResult {
  recordId: string;
  status: IntegrityState;
  localHash: string;
  ledgerHash?: string | null;
  recordType?: string | null;
  entityId?: string | null;
  txId?: string | null;
  version?: number | null;
  timestamp?: string | null;
  message: string;
}

export interface LedgerRecord {
  recordId: string;
  recordType: string;
  entityId: string;
  contentHash?: string | null;
  findingHash?: string | null;
  manifestHash?: string | null;
  findingId?: string | null;
  sourcePhase?: string | null;
  detectorId?: string | null;
  period?: string | null;
  createdAt: string;
  registeredBy: string;
  version: number;
}

export interface LedgerHistoryEntry {
  txId: string;
  timestamp: string;
  isDelete: boolean;
  record?: LedgerRecord | null;
}

export interface EntityRisk {
  entity_id: string;
  name?: string;
  sector?: string;
  size?: string;
  criticality?: string;
  escalation_score: number | null;
  investigation_score: number | null;
  remediation_score: number | null;
  monitoring_score: number | null;
  operational_discipline_score: number | null;
  cyber_resilience_score: number | null;
  overall_score: number;
  risk_band: RiskBand;
  assessment_coverage: number;
  assessable_dimensions: number;
  total_dimensions: number;
  evidence_strength_summary: string;
  corroboration_summary: string;
  top_risk_dimension: string;
  top_reason: string;
  supporting_finding_count: number;
}

export interface RiskContribution {
  id: string;
  entity_id: string;
  dimension: string;
  source_phase: string;
  detector_id: string;
  signal_name: string;
  raw_value: number | string | null;
  normalized_value: number;
  weight: number;
  contribution: number;
  severity: string;
  evidence_strength: string | null;
  assessment_strength: string;
  corroboration_group: string;
  supporting_finding_ids: string[];
  rationale: string;
}

export interface ReviewQueueItem {
  rank: number;
  entity_id: string;
  record_type: RecordType;
  record_id: string;
  priority: PriorityLevel;
  priority_score: number;
  reason: string;
  supporting_finding_ids: string[];
  evidence_strength: string | null;
  escalation_flags: string[];
  status: string;
}

export function parseFindingIds(raw: any): string[] {
  if (!raw) return [];
  if (Array.isArray(raw)) return raw;
  if (typeof raw === "string") {
    try {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed)) return parsed;
    } catch {
      if (raw.startsWith("F-")) return [raw];
    }
  }
  return [];
}

export interface StandardizedEvidence {
  id: string;
  finding_id: string;
  source_type: string;
  source_id: string;
  entity_id: string;
  field: string;
  value: any;
  reason: string;
}

export interface StandardizedFinding {
  id: string;
  rule_id: string;
  entity_id: string;
  source_phase: string;
  finding_type: string;
  severity: string;
  confidence: string;
  evidence_strength: string | null;
  confidence_type: string | null;
  title: string;
  summary: string;
  rationale: string;
  status: string;
  created_at: string;
  metric_name?: string | null;
  observed_value?: number | string | null;
  expected_value?: number | string | null;
  threshold?: number | string | null;
  population_size?: number | null;
  absolute_gap?: number | null;
  relative_gap?: number | null;
  baseline_method?: string | null;
  baseline_type?: string | null;
  baseline_value?: number | null;
  reference_value?: number | null;
  gap_value?: number | null;
  gap_direction?: string | null;
  anomaly_score?: number | null;
  anomaly_rank?: number | null;
  contributing_deviations?: any[] | null;
}

export interface FindingDetailResponse {
  finding: StandardizedFinding;
  evidence: StandardizedEvidence[];
}

export interface ManifestData {
  stage: string;
  schema_version: string;
  dataset_id: string;
  generated_at: string;
  input_paths: Record<string, string>;
  input_phase_counts: Record<string, number>;
  dimensions: string[];
  dimension_weights: Record<string, number>;
  dimensions_config?: Array<{
    key: string;
    field: string;
    weight: number;
    description: string;
  }>;
  risk_band_thresholds: Record<string, [number, number]>;
  priority_thresholds: Record<string, number>;
  correlation_groups: Record<
    string,
    {
      dimension: string;
      detectors: string[];
      relevant_features: string[];
      description: string;
    }
  >;
  an001_configuration: {
    maximum_influence: number;
    methodology: string;
    feature_to_dimension_mapping: string;
    contextual_nature: string;
  };
  normalization_methods: Record<string, string>;
  aggregation_method: string;
  dimension_assessability_rule: string;
  r005_denominator_handling: string;
  priority_method: string;
  coverage_method: string;
  detectors_consumed: string[];
  detectors_excluded: string[];
  row_counts: {
    entity_risk: number;
    risk_contributions: number;
    review_queue: number;
  };
}

export interface DimensionConfig {
  key: string;
  field: string;
  weight: number;
  description: string;
}

export interface RiskBandThresholds {
  moderate: number;
  high: number;
  critical: number;
}

export const FALLBACK_DIMENSION_CONFIG: DimensionConfig[] = [
  {
    key: "Escalation",
    field: "escalation_score",
    weight: 0.25,
    description: "Unescalated critical security cases & escalation execution gaps",
  },
  {
    key: "Investigation",
    field: "investigation_score",
    weight: 0.2,
    description: "Investigation duration, rapid closure prevalence, & uninvestigated alerts",
  },
  {
    key: "Remediation",
    field: "remediation_score",
    weight: 0.2,
    description: "Asset vulnerability remediation execution & multi-phase gaps",
  },
  {
    key: "Monitoring",
    field: "monitoring_score",
    weight: 0.15,
    description: "Critical asset monitoring coverage & negative-space blindspots",
  },
  {
    key: "Operational Discipline",
    field: "operational_discipline_score",
    weight: 0.1,
    description: "Alert triage activity stability & baseline operational discipline",
  },
  {
    key: "Cyber Resilience",
    field: "cyber_resilience_score",
    weight: 0.1,
    description: "Contextual multivariate anomaly profile (AN001, capped influence)",
  },
];

export const FALLBACK_RISK_BAND_THRESHOLDS: RiskBandThresholds = {
  moderate: 25,
  high: 50,
  critical: 75,
};

export function dimensionConfigFromManifest(
  manifest?: ManifestData | null,
): DimensionConfig[] {
  const configured = manifest?.dimensions_config;
  if (configured && configured.length === 6) return configured;
  return FALLBACK_DIMENSION_CONFIG;
}

export function riskBandThresholdsFromManifest(
  manifest?: ManifestData | null,
): RiskBandThresholds {
  const raw = manifest?.risk_band_thresholds;
  if (!raw) return FALLBACK_RISK_BAND_THRESHOLDS;
  const moderate = Number(raw.MODERATE?.[0]);
  const high = Number(raw.HIGH?.[0]);
  const critical = Number(raw.CRITICAL?.[0]);
  if ([moderate, high, critical].some(Number.isNaN)) return FALLBACK_RISK_BAND_THRESHOLDS;
  return { moderate, high, critical };
}

export function bandRangeLabel(band: RiskBand, t: RiskBandThresholds): string {
  switch (band) {
    case "CRITICAL":
      return `Score \u2265 ${t.critical.toFixed(1)}`;
    case "HIGH":
      return `Score ${t.high.toFixed(1)}\u2013${(t.critical - 0.1).toFixed(1)}`;
    case "MODERATE":
      return `Score ${t.moderate.toFixed(1)}\u2013${(t.high - 0.1).toFixed(1)}`;
    case "LOW":
      return `Score ${"0.0"}\u2013${(t.moderate - 0.1).toFixed(1)}`;
  }
}
