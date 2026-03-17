// src/lib/api/alerts.ts
import { fetchJson } from "@/lib/api/http"

export type Severity = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL" | (string & {})

export type AlertListItem = {
  id: number
  tenant_id: number
  transaction_id: number
  transaction_reference: string
  account_id: string
  vendor_code?: string | null
  employee_id?: string | null
  risk_score_0_999: number
  severity: Severity
  rule_score?: number | null
  ml_score?: number | null
  graph_score?: number | null
  triggered_rules: string[]
  graph_motifs?: string | null
  scored_at: string
  created_at: string
}

export type AlertsSummary = {
  total_alerts: number
  high_risk_alerts: number
  critical_alerts: number
  avg_risk_score: number
}

export type TransactionDirection = "DEBIT" | "CREDIT" | (string & {})
export type TransactionStatus = "PENDING" | "POSTED" | "REVERSED" | "CANCELLED" | (string & {})

export type TransactionResponse = {
  id: number
  tx_id: string
  account_id: string
  customer_id: string | null
  invoice_id: number | null
  tx_time: string
  booking_time: string | null
  amount: number
  currency: string
  direction: TransactionDirection
  status: TransactionStatus
  country_code: string | null
  merchant_category: string | null
  channel: string | null
  description: string | null
  created_at: string
  updated_at: string
}

export type RuleResult = Record<string, unknown>

export type AlertDetailResponse = {
  alert: AlertListItem
  transaction: TransactionResponse
  rule_results: RuleResult[]
}

// Handles all possible API response shapes:
// 1. { items: [...], count: N }  ← FastAPI paginated response (primary)
// 2. [...] ← raw array
// 3. { value: [...], Count: N } ← PowerShell ConvertTo-Json artifact
function normalizeListResponse(input: any): { items: AlertListItem[]; count?: number } {
  // Primary format: { items: [...], count: N }
  if (input && Array.isArray(input.items)) {
    return {
      items: input.items as AlertListItem[],
      count: typeof input.count === "number" ? input.count : undefined,
    }
  }
  // Raw array
  if (Array.isArray(input)) {
    return { items: input as AlertListItem[], count: input.length }
  }
  // PowerShell artifact: { value: [...], Count: N }
  if (input && Array.isArray(input.value)) {
    return {
      items: input.value as AlertListItem[],
      count: typeof input.Count === "number" ? input.Count : undefined,
    }
  }
  return { items: [], count: undefined }
}

export async function getAlertsSummary(): Promise<AlertsSummary> {
  return fetchJson<AlertsSummary>("/api/v1/alerts/summary")
}

export async function getAlerts(params: {
  min_risk?: number
  severity?: string
  limit?: number
  offset?: number
}): Promise<{ items: AlertListItem[]; count?: number }> {
  const sp = new URLSearchParams()
  if (typeof params.min_risk === "number" && params.min_risk > 0) sp.set("min_risk", String(params.min_risk))
  if (params.severity && params.severity !== "ALL") sp.set("severity", params.severity)
  if (typeof params.limit === "number") sp.set("limit", String(params.limit))
  if (typeof params.offset === "number") sp.set("offset", String(params.offset))
  const data = await fetchJson<any>(`/api/v1/alerts?${sp.toString()}`)
  return normalizeListResponse(data)
}

export async function getAlertDetail(alertId: number): Promise<AlertDetailResponse> {
  return fetchJson<AlertDetailResponse>(`/api/v1/alerts/${alertId}/detail`)
}
