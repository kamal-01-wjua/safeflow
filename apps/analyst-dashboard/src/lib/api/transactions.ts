// src/lib/api/transactions.ts
import { fetchJson } from "@/lib/api/http"

export type TransactionDirection = "DEBIT" | "CREDIT" | (string & {})
export type TransactionStatus = "PENDING" | "POSTED" | "REVERSED" | "CANCELLED" | (string & {})

export type TransactionItem = {
  id: number
  tenant_id?: number | null
  transaction_reference?: string | null
  tx_id?: string | null
  account_id: string
  counterparty_account?: string | null
  customer_id?: string | null
  invoice_id?: number | null
  timestamp?: string | null
  tx_time?: string | null
  amount: number
  currency: string
  direction: TransactionDirection
  status: TransactionStatus
  country_code?: string | null
  merchant_category?: string | null
  channel?: string | null
  description?: string | null
  created_at: string
  updated_at: string
}

export type TransactionsListResponse = { items: TransactionItem[]; count?: number }

function normalizeItem(raw: any): TransactionItem {
  return {
    ...raw,
    // amount: API returns string decimal, normalize to number
    amount: typeof raw.amount === "string" ? parseFloat(raw.amount) : (raw.amount ?? 0),
    // normalize timestamp fields — API returns "timestamp", panel uses both
    tx_time: raw.tx_time ?? raw.timestamp ?? null,
    timestamp: raw.timestamp ?? raw.tx_time ?? null,
    // normalize id fields — API returns transaction_reference, panel uses tx_id
    tx_id: raw.tx_id ?? raw.transaction_reference ?? String(raw.id),
    transaction_reference: raw.transaction_reference ?? raw.tx_id ?? null,
  }
}

function normalizeListResponse(input: any): TransactionsListResponse {
  // { items, count } — /api/v1 envelope format
  if (input && Array.isArray(input.items)) {
    const count = typeof input.count === "number" ? input.count : input.items.length
    return { items: input.items.map(normalizeItem), count }
  }
  // { value, Count } — legacy /transactions/ format (current)
  if (input && Array.isArray(input.value)) {
    const count = typeof input.Count === "number" ? input.Count : input.value.length
    return { items: input.value.map(normalizeItem), count }
  }
  // raw array fallback
  if (Array.isArray(input)) {
    return { items: input.map(normalizeItem), count: input.length }
  }
  return { items: [], count: undefined }
}

export async function getTransactions(params: {
  account_id?: string
  customer_id?: string
  limit?: number
  offset?: number
}): Promise<TransactionsListResponse> {
  const sp = new URLSearchParams()
  const account = params.account_id?.trim()
  const customer = params.customer_id?.trim()
  if (account) sp.set("account_id", account)
  if (customer) sp.set("customer_id", customer)
  if (typeof params.limit === "number") sp.set("limit", String(params.limit))
  if (typeof params.offset === "number") sp.set("offset", String(params.offset))
  const qs = sp.toString()
  const data = await fetchJson<any>(`/transactions/${qs ? `?${qs}` : ""}`)
  return normalizeListResponse(data)
}

export async function getTransaction(id: number): Promise<TransactionItem> {
  const raw = await fetchJson<any>(`/transactions/${id}`)
  return normalizeItem(raw)
}
