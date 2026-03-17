// src/lib/api/entities.ts
import { fetchJson } from "@/lib/api/http"

export type EntityType =
  | "PERSON"
  | "ACCOUNT"
  | "MERCHANT"
  | "VENDOR"
  | "EMPLOYEE"
  | "COMPANY"
  | "UNKNOWN"
  | (string & {})

export type EntityItem = {
  id: number
  entity_id?: string | null
  name?: string | null
  type?: EntityType | null
  risk_score?: number | null
  country_code?: string | null
  created_at?: string
  updated_at?: string
  [key: string]: unknown
}

export type EntityFeatures = {
  entity_id: string | null
  account_id: string | null
  tx_count_total: number
  tx_count_24h: number
  tx_count_7d: number
  amount_total: number
  amount_avg: number
  amount_max: number
  amount_last: number
  latest_risk_score: number
  risk_score_avg: number
  high_risk_tx_count: number
  is_velocity_flagged: boolean
  consecutive_high_risk: number
  first_seen_at: string | null
  last_seen_at: string | null
  source: "entity_features" | "entity_only"
}

function normalizeListResponse(input: any): { items: EntityItem[]; count?: number } {
  if (Array.isArray(input)) return { items: input as EntityItem[], count: input.length }

  if (input && Array.isArray(input.items)) {
    const count = typeof input.count === "number" ? input.count : input.items.length
    return { items: input.items as EntityItem[], count }
  }

  if (input && Array.isArray(input.value)) {
    const count = typeof input.Count === "number" ? input.Count : undefined
    return { items: input.value as EntityItem[], count }
  }

  return { items: [], count: undefined }
}

export async function getEntities(params: {
  q?: string
  type?: string
  min_risk?: number
  limit?: number
  offset?: number
}) {
  const sp = new URLSearchParams()
  if (params.q) sp.set("q", params.q)
  if (params.type) sp.set("type", params.type)
  if (typeof params.min_risk === "number") sp.set("min_risk", String(params.min_risk))
  if (typeof params.limit === "number") sp.set("limit", String(params.limit))
  if (typeof params.offset === "number") sp.set("offset", String(params.offset))

  const data = await fetchJson<any>(`/entities/?${sp.toString()}`)
  return normalizeListResponse(data)
}

export async function getEntity(id: number): Promise<EntityItem> {
  return fetchJson<EntityItem>(`/entities/${id}`)
}

export async function getEntityFeatures(id: number): Promise<EntityFeatures> {
  return fetchJson<EntityFeatures>(`/entities/${id}/features`)
}
