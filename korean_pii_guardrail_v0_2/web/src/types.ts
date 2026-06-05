export type ConsoleView =
  | "overview"
  | "scanner"
  | "logs"
  | "trace"
  | "batch"
  | "datasets"
  | "settings"

export interface RealDataConfig {
  allowed_roots: string[]
  upload_max_bytes: number
  raw_retention_enabled: boolean
  real_ner_required: boolean
  parser_presets: string[]
  default_row_limit: number
  max_row_limit: number
}

export interface HealthPayload {
  status: string
  version: string
  loaded_profiles: string[]
  ner_enabled: boolean
  ner_mode: string
  db_path: string
  raw_value_logged: false
  real_data?: RealDataConfig
}

export interface PublicSpan {
  start: number
  end: number
  span_length: number
  entity_type: string
  score: number
  risk_level: string
  action: string
  suffix?: string | null
  is_composite: boolean
  sources: string[]
  detector_ids: string[]
  reason_codes: string[]
  value_hash?: string | null
  raw_value_logged: false
}

export interface AuditEvent {
  event_type: string
  entity_type: string
  score: number
  risk_level: string
  action: string
  value_hash?: string | null
  span_length?: number | null
  reason_codes: string[]
  raw_value_logged: false
}

export interface ResponseMetrics {
  latency_ms: number
  detected_span_count: number
  masked_span_count: number
}

export interface LogSummary {
  request_id: string
  created_at: string
  text_length: number
  blocked: boolean
  latency_ms: number
  detected_span_count: number
  masked_span_count: number
  policy_profile: string
  output_target: string
  entity_counts: Record<string, number>
  risk_counts: Record<string, number>
  action_counts: Record<string, number>
  encrypted_raw_available: boolean
  encrypted_raw_key_hint?: string | null
  raw_value_logged: false
  idx?: number
}

export interface LogDetail extends LogSummary {
  masked_text: string | null
  spans: PublicSpan[]
  audit_events: AuditEvent[]
}

export interface ApplyResponse {
  request_id: string
  blocked: boolean
  masked_text: string | null
  spans: PublicSpan[]
  audit_events: AuditEvent[]
  metrics: ResponseMetrics
  policy_profile: string
  output_target: string
  raw_value_logged: false
  summary: LogSummary
  encrypted_raw_available: boolean
  encrypted_raw_key_hint?: string | null
}

export interface DecryptLogResponse {
  request_id: string
  decrypted_text: string
  encrypted_raw_available: true
  raw_value_logged: false
}

export interface MetricsPayload {
  total_requests: number
  blocked_requests: number
  block_rate: number
  detected_span_count: number
  masked_span_count: number
  average_latency_ms: number
  entity_counts: Record<string, number>
  risk_counts: Record<string, number>
  action_counts: Record<string, number>
  raw_value_logged: false
}

export interface TraceStageSpan {
  type: string
  value: string
  start: number
  end: number
  score: number
  risk: string
  action: string
  suffix: string
  is_composite: boolean
  sources: string[]
  detector_ids: string[]
  reason_codes: string[]
}

export interface TraceStage {
  module: string
  title: string
  span_count: number
  summary: string
  what_it_did: string[]
  spans: TraceStageSpan[]
  detail: Record<string, unknown>
}

export interface TraceResponse {
  request_id: string
  raw_len: number
  normalized_changed: boolean
  blocked: boolean
  audit_event_count: number
  total_latency_ms: number
  masked_text: string | null
  reveal_raw: false
  raw_value_logged: false
  stages: TraceStage[]
}

export interface BatchResponse {
  n: number
  records: LogSummary[]
  aggregate: MetricsPayload
  raw_value_logged: false
}

export interface DatasetRegistration {
  dataset_id: string
  source_kind: "upload" | "local"
  display_name: string
  size_bytes: number
  raw_path_returned: false
  raw_value_logged: false
}

export interface DatasetSchema {
  dataset_id: string
  source_kind: string
  display_name: string
  file_type: string
  columns: string[]
  row_count_estimate: number
  encoding_candidates: string[]
  parser_presets: string[]
  raw_preview_returned: false
  raw_value_logged: false
}

export interface DatasetRun {
  run_id: string
  created_at: string
  completed_at: string | null
  status: "queued" | "running" | "completed" | "failed" | "cancelled"
  dataset_id: string
  dataset_label: string
  source_kind: string
  parser_preset: string
  row_limit: number
  retention_policy: string
  text_columns: string[]
  id_column: string | null
  ner_mode: string
  records_processed: number
  records_failed: number
  blocked_count: number
  detected_span_count: number
  masked_span_count: number
  average_latency_ms: number
  entity_counts: Record<string, number>
  risk_counts: Record<string, number>
  action_counts: Record<string, number>
  error_code: string | null
  error_message: string | null
  raw_value_logged: false
}

export interface DatasetRunRecord {
  run_id: string
  row_index: number
  row_id_hash: string
  masked_text: string
  blocked: boolean
  latency_ms: number
  detected_span_count: number
  masked_span_count: number
  entity_counts: Record<string, number>
  risk_counts: Record<string, number>
  action_counts: Record<string, number>
  spans: PublicSpan[]
  error_code: string | null
  raw_value_logged: false
}
