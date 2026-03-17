"use client"

import * as React from "react"
import { usePathname, useRouter, useSearchParams } from "next/navigation"
import { useQuery } from "@tanstack/react-query"
import { Search, SlidersHorizontal, RotateCcw, ArrowDownLeft, ArrowUpRight } from "lucide-react"
import { getTransactions } from "@/lib/api/transactions"
import { getTransaction } from "@/lib/api/transactions"
import { cn } from "@/lib/utils"
import { Separator } from "@/components/ui/separator"

const SELECTION_KEY = "safeflow.tx.selected"

// ── Status Badge ──────────────────────────────────────────────────────────────
function StatusBadge({ status }: { status: string }) {
  const map: Record<string, string> = {
    POSTED:    "bg-emerald-100 text-emerald-700 border border-emerald-200",
    PENDING:   "bg-yellow-100 text-yellow-700 border border-yellow-200",
    REVERSED:  "bg-red-100 text-red-700 border border-red-200",
    CANCELLED: "bg-slate-100 text-slate-600 border border-slate-200",
  }
  return (
    <span className={cn("inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide", map[status] ?? "bg-slate-100 text-slate-600 border border-slate-200")}>
      {status}
    </span>
  )
}

// ── Direction Badge ───────────────────────────────────────────────────────────
function DirectionBadge({ direction }: { direction: string }) {
  const isDebit = direction === "DEBIT" || direction === "DR" || direction === "OUT"
  return (
    <span className={cn(
      "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-bold uppercase",
      isDebit ? "bg-red-50 text-red-600" : "bg-emerald-50 text-emerald-600"
    )}>
      {isDebit
        ? <ArrowUpRight className="h-2.5 w-2.5" />
        : <ArrowDownLeft className="h-2.5 w-2.5" />}
      {direction}
    </span>
  )
}

function usePersistedSelection() {
  const [selectedId, _set] = React.useState<number | null>(() => {
    if (typeof window === "undefined") return null
    try { const s = sessionStorage.getItem(SELECTION_KEY); return s ? Number(s) : null } catch { return null }
  })
  const set = React.useCallback((id: number | null) => {
    _set(id)
    try { id === null ? sessionStorage.removeItem(SELECTION_KEY) : sessionStorage.setItem(SELECTION_KEY, String(id)) } catch {}
  }, [])
  return [selectedId, set] as const
}

export function TransactionsWorkbench() {
  const sp = useSearchParams()
  const router = useRouter()
  const pathname = usePathname()
  const [selectedId, setSelectedId] = usePersistedSelection()

  const account_id = sp.get("account_id") ?? ""
  const customer_id = sp.get("customer_id") ?? ""
  const offset = Number(sp.get("offset") ?? "0")
  const limit = 25

  const setParams = (next: Record<string, string | number | null>) => {
    const nextSp = new URLSearchParams(sp.toString())
    for (const [k, v] of Object.entries(next)) {
      if (v === null || v === "" || v === 0 && k === "offset") { if (k !== "offset" || v !== 0) nextSp.delete(k); else nextSp.delete(k) }
      else nextSp.set(k, String(v))
    }
    router.replace(nextSp.toString() ? `${pathname}?${nextSp.toString()}` : pathname, { scroll: false })
  }

  const listQ = useQuery({
    queryKey: ["tx.list", { account_id, customer_id, limit, offset }],
    queryFn: () => getTransactions({
      account_id: account_id.trim() || undefined,
      customer_id: customer_id.trim() || undefined,
      limit,
      offset,
    }),
    staleTime: 15_000,
    refetchOnWindowFocus: false,
  })

  const detailQ = useQuery({
    queryKey: ["tx.detail", selectedId],
    queryFn: () => getTransaction(selectedId!),
    enabled: !!selectedId,
    staleTime: 60_000,
    refetchOnWindowFocus: false,
  })

  const items = listQ.data?.items ?? []
  const count = listQ.data?.count

  return (
    <div className="mx-auto w-full max-w-[1400px] px-6 py-6 space-y-5">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-slate-900 tracking-tight">Transactions</h1>
        <p className="text-sm text-slate-500 mt-0.5">Explore events, filter anomalies, and pivot into investigations.</p>
      </div>

      {/* Filters */}
      <div className="rounded-xl border border-slate-200 bg-white px-4 py-3">
        <div className="flex flex-wrap items-center gap-3">
          <SlidersHorizontal className="h-4 w-4 text-slate-400 shrink-0" />
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Filters</span>
          <Separator orientation="vertical" className="h-4" />

          <div className="relative">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400" />
            <input
              value={account_id}
              onChange={(e) => { setSelectedId(null); setParams({ account_id: e.target.value, offset: 0 }) }}
              placeholder="Account ID..."
              className="rounded-lg border border-slate-200 bg-white pl-8 pr-3 py-1.5 text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400 w-44"
            />
          </div>

          <input
            value={customer_id}
            onChange={(e) => { setSelectedId(null); setParams({ customer_id: e.target.value, offset: 0 }) }}
            placeholder="Customer ID (optional)"
            className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400 w-52"
          />

          <button
            onClick={() => { setSelectedId(null); setParams({ account_id: null, customer_id: null, offset: 0 }) }}
            className="ml-auto flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-[11px] font-medium text-slate-500 hover:bg-slate-100 transition-colors"
          >
            <RotateCcw className="h-3 w-3" />
            Reset
          </button>
        </div>
      </div>

      {/* Table + Detail */}
      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_360px]">
        {/* Table */}
        <div className="rounded-xl border border-slate-200 bg-white overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100">
            <span className="text-sm font-semibold text-slate-800">Transaction Stream</span>
            <span className="text-xs text-slate-400">
              {listQ.isFetching ? "Refreshing..." : `${items.length}${count ? ` of ${count}` : ""} · Offset ${offset}`}
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100 bg-slate-50">
                  <th className="text-left px-4 py-2.5 text-[11px] font-semibold text-slate-500 uppercase tracking-wide">Time</th>
                  <th className="text-left px-4 py-2.5 text-[11px] font-semibold text-slate-500 uppercase tracking-wide">Reference</th>
                  <th className="text-right px-4 py-2.5 text-[11px] font-semibold text-slate-500 uppercase tracking-wide">Amount</th>
                  <th className="text-left px-4 py-2.5 text-[11px] font-semibold text-slate-500 uppercase tracking-wide">Dir</th>
                  <th className="text-left px-4 py-2.5 text-[11px] font-semibold text-slate-500 uppercase tracking-wide">Status</th>
                  <th className="text-left px-4 py-2.5 text-[11px] font-semibold text-slate-500 uppercase tracking-wide hidden xl:table-cell">Account</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {listQ.isLoading ? (
                  Array.from({ length: 10 }).map((_, i) => (
                    <tr key={i}>
                      {Array.from({ length: 6 }).map((_, j) => (
                        <td key={j} className="px-4 py-3">
                          <div className="h-3 rounded bg-slate-100 animate-pulse" />
                        </td>
                      ))}
                    </tr>
                  ))
                ) : items.map((t: any) => (
                  <tr
                    key={t.id}
                    onClick={() => setSelectedId(t.id === selectedId ? null : t.id)}
                    className={cn(
                      "cursor-pointer transition-colors",
                      selectedId === t.id
                        ? "bg-blue-50 border-l-2 border-l-blue-500"
                        : "hover:bg-slate-50"
                    )}
                  >
                    <td className="px-4 py-3">
                      <div className="text-xs text-slate-600">
                        {t.timestamp ? new Date(t.timestamp).toLocaleDateString() : "—"}
                      </div>
                      <div className="text-[10px] text-slate-400">
                        {t.timestamp ? new Date(t.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : ""}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="font-mono text-xs text-slate-700 truncate max-w-[140px]">
                        {t.transaction_reference ?? t.tx_id ?? `TX-${t.id}`}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <span className="font-semibold tabular-nums text-slate-800 text-sm">
                        {t.currency} {Number(t.amount).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <DirectionBadge direction={t.direction} />
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge status={t.status} />
                    </td>
                    <td className="px-4 py-3 hidden xl:table-cell">
                      <span className="font-mono text-xs text-slate-600">{t.account_id ?? "—"}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="flex items-center justify-between px-4 py-3 border-t border-slate-100">
            <span className="text-xs text-slate-400">Showing {items.length} records</span>
            <div className="flex gap-2">
              <button
                disabled={offset === 0}
                onClick={() => setParams({ offset: Math.max(0, offset - limit) })}
                className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                Previous
              </button>
              <button
                disabled={items.length < limit}
                onClick={() => setParams({ offset: offset + limit })}
                className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                Next
              </button>
            </div>
          </div>
        </div>

        {/* Detail Panel */}
        <div className="rounded-xl border border-slate-200 bg-white overflow-hidden">
          <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between">
            <span className="text-sm font-semibold text-slate-800">Investigation</span>
            {selectedId && (
              <button onClick={() => setSelectedId(null)} className="text-xs text-slate-400 hover:text-slate-600 transition-colors">Clear</button>
            )}
          </div>

          {!selectedId ? (
            <div className="flex flex-col items-center justify-center py-12 text-center px-4">
              <div className="rounded-full bg-slate-100 p-4 mb-3">
                <ArrowLeftRight className="h-6 w-6 text-slate-400" />
              </div>
              <div className="text-sm font-medium text-slate-600">No transaction selected</div>
              <div className="text-xs text-slate-400 mt-1">Click any row to inspect details</div>
            </div>
          ) : detailQ.isLoading ? (
            <div className="p-4 space-y-3">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="h-4 rounded bg-slate-100 animate-pulse" />
              ))}
            </div>
          ) : detailQ.data ? (
            <div className="p-4 space-y-4">
              {/* Amount header */}
              <div className="flex items-start justify-between">
                <div>
                  <div className="text-xs text-slate-400 mb-1">Transaction #{detailQ.data.id}</div>
                  <div className="flex flex-wrap gap-1.5">
                    <DirectionBadge direction={detailQ.data.direction} />
                    <StatusBadge status={detailQ.data.status} />
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-lg font-bold text-slate-900 tabular-nums">
                    {detailQ.data.currency} {Number(detailQ.data.amount).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </div>
                </div>
              </div>

              <Separator />

              {/* Fields */}
              <div className="space-y-2">
                {[
                  { label: "Reference", value: detailQ.data.transaction_reference ?? detailQ.data.tx_id },
                  { label: "Account", value: detailQ.data.account_id },
                  { label: "Currency", value: detailQ.data.currency },
                  { label: "Channel", value: (detailQ.data as any).channel ?? "—" },
                  { label: "Country", value: (detailQ.data as any).country_code ?? "—" },
                  { label: "Category", value: (detailQ.data as any).merchant_category ?? "—" },
                ].map((f) => (
                  <div key={f.label} className="flex items-center justify-between text-xs">
                    <span className="text-slate-400">{f.label}</span>
                    <span className="font-mono font-medium text-slate-700 text-right max-w-[180px] truncate">{f.value ?? "—"}</span>
                  </div>
                ))}
              </div>

              {(detailQ.data as any).description && (
                <>
                  <Separator />
                  <div>
                    <div className="text-xs text-slate-400 mb-1">Description</div>
                    <div className="rounded-lg bg-slate-50 border border-slate-100 px-3 py-2 text-xs text-slate-600 leading-relaxed">
                      {(detailQ.data as any).description}
                    </div>
                  </div>
                </>
              )}
            </div>
          ) : null}
        </div>
      </div>
    </div>
  )
}

// need this for the no-icon import in detail panel
import { ArrowLeftRight } from "lucide-react"
