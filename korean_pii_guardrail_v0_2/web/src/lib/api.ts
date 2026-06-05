import type {
  ApplyResponse,
  BatchResponse,
  DatasetRegistration,
  DatasetRun,
  DatasetRunRecord,
  DatasetSchema,
  DecryptLogResponse,
  HealthPayload,
  LogDetail,
  LogSummary,
  MetricsPayload,
  TraceResponse,
} from "@/types"

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ""

interface ApplyBody {
  text: string
  scan_stage?: string
  output_target?: string
  policy_profile?: string
  encrypted_raw_logging_key?: string
  encrypted_raw_key_hint?: string
}

interface BatchBody {
  lines: string
  limit?: number
  encrypted_raw_logging_key?: string
  encrypted_raw_key_hint?: string
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const isFormData = init?.body instanceof FormData
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      ...(!isFormData ? { "Content-Type": "application/json" } : {}),
      ...(init?.headers ?? {}),
    },
    ...init,
  })
  if (!response.ok) {
    const message = await response.text()
    throw new Error(message || `${response.status} ${response.statusText}`)
  }
  return (await response.json()) as T
}

export function getHealth(): Promise<HealthPayload> {
  return requestJson<HealthPayload>("/api/health")
}

export function getMetrics(): Promise<MetricsPayload> {
  return requestJson<MetricsPayload>("/api/metrics")
}

export async function getLogs(limit = 100): Promise<LogSummary[]> {
  const payload = await requestJson<{ records: LogSummary[]; raw_value_logged: false }>(
    `/api/logs?limit=${limit}`,
  )
  return payload.records
}

export function getLogDetail(requestId: string): Promise<LogDetail> {
  return requestJson<LogDetail>(`/api/logs/${encodeURIComponent(requestId)}`)
}

export function decryptLog(requestId: string, decryptKey: string): Promise<DecryptLogResponse> {
  return requestJson<DecryptLogResponse>(`/api/logs/${encodeURIComponent(requestId)}/decrypt`, {
    method: "POST",
    body: JSON.stringify({ decrypt_key: decryptKey }),
  })
}

export function applyGuardrail(body: ApplyBody): Promise<ApplyResponse> {
  return requestJson<ApplyResponse>("/api/pii/apply", {
    method: "POST",
    body: JSON.stringify({
      scan_stage: "input",
      output_target: "llm_input",
      policy_profile: "strict",
      ...body,
    }),
  })
}

export function traceGuardrail(text: string): Promise<TraceResponse> {
  return requestJson<TraceResponse>("/api/pii/trace", {
    method: "POST",
    body: JSON.stringify({ text, reveal_raw: false }),
  })
}

export function runBatch(body: BatchBody): Promise<BatchResponse> {
  return requestJson<BatchResponse>("/api/pii/batch", {
    method: "POST",
    body: JSON.stringify({
      limit: 200,
      ...body,
    }),
  })
}

export function uploadDataset(file: File): Promise<DatasetRegistration> {
  const form = new FormData()
  form.append("file", file)
  return requestJson<DatasetRegistration>("/api/datasets/upload", {
    method: "POST",
    body: form,
  })
}

export function registerLocalDataset(path: string): Promise<DatasetRegistration> {
  return requestJson<DatasetRegistration>("/api/datasets/register-local", {
    method: "POST",
    body: JSON.stringify({ path }),
  })
}

export function getDatasetSchema(datasetId: string): Promise<DatasetSchema> {
  return requestJson<DatasetSchema>(`/api/datasets/${encodeURIComponent(datasetId)}/schema`)
}

export function createDatasetRun(body: {
  dataset_id: string
  parser_preset: string
  text_columns: string[]
  id_column?: string | null
  row_limit: number
  retention_policy: string
}): Promise<DatasetRun> {
  return requestJson<DatasetRun>("/api/dataset-runs", {
    method: "POST",
    body: JSON.stringify(body),
  })
}

export async function getDatasetRuns(limit = 50): Promise<DatasetRun[]> {
  const payload = await requestJson<{ records: DatasetRun[]; raw_value_logged: false }>(
    `/api/dataset-runs?limit=${limit}`,
  )
  return payload.records
}

export function getDatasetRun(runId: string): Promise<DatasetRun> {
  return requestJson<DatasetRun>(`/api/dataset-runs/${encodeURIComponent(runId)}`)
}

export async function getDatasetRunRecords(runId: string, limit = 100): Promise<DatasetRunRecord[]> {
  const payload = await requestJson<{ records: DatasetRunRecord[]; raw_value_logged: false }>(
    `/api/dataset-runs/${encodeURIComponent(runId)}/records?limit=${limit}`,
  )
  return payload.records
}

export function cancelDatasetRun(runId: string): Promise<DatasetRun> {
  return requestJson<DatasetRun>(`/api/dataset-runs/${encodeURIComponent(runId)}/cancel`, {
    method: "POST",
  })
}
