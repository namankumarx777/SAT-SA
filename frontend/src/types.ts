export type RiskBand = "LOW" | "MODERATE" | "HIGH" | "CRITICAL";
export type PriorityLevel = "HIGH" | "MEDIUM" | "LOW";
export type RecordType = "ENTITY" | "FINDING" | "CASE" | "ALERT" | "ASSET";

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
