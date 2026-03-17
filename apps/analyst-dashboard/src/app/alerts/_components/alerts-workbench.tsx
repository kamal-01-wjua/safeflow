"use client"

import * as React from "react"
import { usePathname, useRouter, useSearchParams } from "next/navigation"
import { useQuery } from "@tanstack/react-query"
import {
  AlertTriangle, TrendingUp, ShieldAlert, Activity,
  Filter, RotateCcw, Search, ChevronRight, Building2,
  User, Briefcase,
} from "lucide-react"
import { getAlerts, getAlertsSummary, getAlertDetail, type AlertListItem } from "@/lib/api/alerts"
import { Separator } from "@/components/ui/separator"
import { cn } from "@/lib/utils"

// ── Skeleton rows with fixed widths (no Math.random - avoids hydration error) ─
const SKELETON_WIDTHS = [
  ["w-16", "w-24", "w-12", "w-32", "w-20"],
  ["w-14", "w-20", "w-16", "w-28", "w-24"],
  ["w-18", "w-28", "w-12", "w-36", "w-16"],
  ["w-16", "w-24", "w-14", "w-30", "w-20"],
  ["w-12", "w-20", "w-16", "w-28", "w-18"],
  ["w-20", "w-24", "w-12", "w-32", "w-24"],
  ["w-14", "w-28", "w-14", "w-28", "w-20"],
  ["w-16", "w-20", "w-16", "w-36", "w-16"],
]

// ── KPI Card ──────────────────────────────────────────────────────────────────
function KpiCard({ label, value, sub, borderColor, icon }: {
  label: string; value: string | number; sub?: string
  borderColor: string; icon: React.ReactNode
}) {
  return (
    <div className={cn("rounded-xl border-l-4 border border-slate-200 bg-white p-4 flex items-start gap-3", borderColor)}>
      <div className="mt-0.5 rounded-lg bg-slate-50 p-2 border border-slate-100">{icon}</div>
      <div className="min-w-0">
        <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wide">{label}</div>
        <div className="mt-0.5 text-2xl font-bold tabular-nums text-slate-900 leading-none">{value}</div>
        {sub && <div className="mt-1 text-[11px] text-slate-400">{sub}</div>}
      </div>
    </div>
  )
}

// ── Severity Badge ────────────────────────────────────────────────────────────
function SeverityBadge({ severity }: { severity: string }) {
  const map: Record<string, string> = {
    CRITICAL: "bg-red-100 text-red-700 border-red-200",
    HIGH:     "bg-orange-100 text-orange-700 border-orange-200",
    MEDIUM:   "bg-yellow-100 text-yellow-700 border-yellow-200",
    LOW:      "bg-emerald-100 text-emerald-700 border-emerald-200",
  }
  return (
    <span className={cn("inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide", map[severity] ?? "bg-slate-100 text-slate-600 border-slate-200")}>
      {severity}
    </span>
  )
}

// ── Risk Bar ──────────────────────────────────────────────────────────────────
function RiskBar({ score }: { score: number }) {
  const pct = Math.round(Math.min(100, (score / 999) * 100))
  const color = score >= 850 ? "bg-red-500" : score >= 700 ? "bg-orange-500" : score >= 400 ? "bg-yellow-400" : "bg-emerald-500"
  return (
    <div className="flex items-center gap-2 min-w-[100px]">
      <span className="w-9 text-right text-xs font-mono font-bold text-slate-700 shrink-0">{score}</span>
      <div className="flex-1 h-1.5 rounded-full bg-slate-100 overflow-hidden">
        <div className={cn("h-full rounded-full", color)} style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

// ── Entity icon ───────────────────────────────────────────────────────────────
function EntityIcon({ vendorCode, employeeId }: { vendorCode?: string | null; employeeId?: string | null }) {
  if (vendorCode) return <Briefcase className="h-3 w-3 text-amber-500" />
  if (employeeId) return <User className="h-3 w-3 text-blue-500" />
  return <Building2 className="h-3 w-3 text-slate-400" />
}

// ── Detail Panel ──────────────────────────────────────────────────────────────
function AlertDetailPanel({ alertId }: { alertId: number }) {
  const q = useQuery({
    queryKey: ["alert.detail", alertId],
    queryFn: () => getAlertDetail(alertId),
    staleTime: 60_000,
  })

  if (q.isLoading) return (
    <div className="p-4 space-y-3">
      {[1,2,3,4,5].map(i => <div key={i} className="h-4 rounded bg-slate-100 animate-pulse" />)}
    </div>
  )
  if (q.isError || !q.data) return (
    <div className="p-4 text-sm text-slate-500">Could not load alert detail.</div>
  )

  const { alert, transaction, rule_results } = q.data

  return (
    <div className="p-4 space-y-4 overflow-y-auto max-h-[600px]">
      {/* Risk header */}
      <div className="flex items-start justify-between gap-2">
        <div>
          <div className="text-xs text-slate-400 mb-1">Alert #{alert.id}</div>
          <SeverityBadge severity={alert.severity} />
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold tabular-nums text-slate-900">{alert.risk_score_0_999}</div>
          <div className="text-[10px] text-slate-400">Fusion score</div>
        </div>
      </div>

      {/* Score breakdown */}
      <div className="grid grid-cols-3 gap-2">
        {[
          { label: "Rules", value: alert.rule_score },
          { label: "ML", value: alert.ml_score },
          { label: "Graph", value: alert.graph_score },
        ].map(s => (
          <div key={s.label} className="rounded-lg border border-slate-100 bg-slate-50 p-2 text-center">
            <div className="text-[10px] text-slate-400">{s.label}</div>
            <div className="text-sm font-bold tabular-nums text-slate-700">{s.value ?? "—"}</div>
          </div>
        ))}
      </div>

      <Separator />

      {/* Transaction */}
      <div>
        <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-400 mb-2">Transaction</div>
        <div className="space-y-1.5">
          {[
            { label: "Reference", value: transaction.tx_id },
            { label: "Amount", value: `${transaction.currency} ${Number(transaction.amount).toLocaleString(undefined, { minimumFractionDigits: 2 })}` },
            { label: "Direction", value: transaction.direction },
            { label: "Status", value: transaction.status },
            { label: "Account", value: transaction.account_id },
            { label: "Channel", value: transaction.channel ?? "—" },
          ].map(f => (
            <div key={f.label} className="flex items-center justify-between text-xs">
              <span className="text-slate-400">{f.label}</span>
              <span className="font-mono font-medium text-slate-700 max-w-[160px] truncate text-right">{f.value ?? "—"}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Triggered rules */}
      {alert.triggered_rules?.length > 0 && (
        <>
          <Separator />
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-400 mb-2">
              Triggered Rules ({alert.triggered_rules.length})
            </div>
            <div className="flex flex-wrap gap-1">
              {alert.triggered_rules.map((r, i) => (
                <span key={i} className="rounded-full bg-orange-50 border border-orange-200 px-2 py-0.5 text-[10px] font-medium text-orange-700">
                  {r}
                </span>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  )
}

// ── Main Workbench ────────────────────────────────────────────────────────────
export function AlertsWorkbench() {
  const sp = useSearchParams()
  const router = useRouter()
  const pathname = usePathname()

  const severity = sp.get("severity") ?? "ALL"
  const offset = Number(sp.get("offset") ?? "0")
  const search = sp.get("search") ?? ""
  const limit = 25
  const [selectedId, setSelectedId] = React.useState<number | null>(null)

  const summaryQ = useQuery({
    queryKey: ["alerts.summary"],
    queryFn: getAlertsSummary,
    staleTime: 30_000,
  })

  const listQ = useQuery({
    queryKey: ["alerts.list", { severity, offset, limit }],
    queryFn: () => getAlerts({
      severity: severity !== "ALL" ? severity : undefined,
      limit,
      offset,
    }),
    staleTime: 10_000,
    refetchOnWindowFocus: false,
  })

  // ✅ Correctly extract items from {items, count} envelope
  const alerts: AlertListItem[] = listQ.data?.items ?? []
  const count = listQ.data?.count
  const summary = summaryQ.data

  // Client-side search filter
  const filtered = search
    ? alerts.filter(a =>
        a.transaction_reference?.toLowerCase().includes(search.toLowerCase()) ||
        a.account_id?.toLowerCase().includes(search.toLowerCase())
      )
    : alerts

  const setParams = (next: Record<string, string | number | null>) => {
    const nextSp = new URLSearchParams(sp.toString())
    for (const [k, v] of Object.entries(next)) {
      if (v === null || v === "") nextSp.delete(k)
      else nextSp.set(k, String(v))
    }
    router.replace(`${pathname}?${nextSp.toString()}`, { scroll: false })
  }

  return (
    <div className="mx-auto w-full max-w-[1400px] px-6 py-6 space-y-5">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-slate-900 tracking-tight">Alerts</h1>
        <p className="text-sm text-slate-500 mt-0.5">Triage suspicious activity and investigate risk signals.</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <KpiCard label="Total Alerts" value={summary?.total_alerts?.toLocaleString() ?? "—"} sub="All severities" borderColor="border-l-slate-400" icon={<Activity className="h-4 w-4 text-slate-500" />} />
        <KpiCard label="High Risk" value={summary?.high_risk_alerts?.toLocaleString() ?? "—"} sub="Score ≥ 700" borderColor="border-l-orange-400" icon={<AlertTriangle className="h-4 w-4 text-orange-500" />} />
        <KpiCard label="Critical" value={summary?.critical_alerts?.toLocaleString() ?? "—"} sub="Score ≥ 850" borderColor="border-l-red-400" icon={<ShieldAlert className="h-4 w-4 text-red-500" />} />
        <KpiCard label="Avg Score" value={summary?.avg_risk_score ? Math.round(summary.avg_risk_score) : "—"} sub="Fusion 0–999" borderColor="border-l-blue-400" icon={<TrendingUp className="h-4 w-4 text-blue-500" />} />
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3 rounded-xl border border-slate-200 bg-white px-4 py-3">
        <Filter className="h-4 w-4 text-slate-400 shrink-0" />
        <span className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Filter</span>
        <Separator orientation="vertical" className="h-4" />

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400" />
          <input
            value={search}
            onChange={e => setParams({ search: e.target.value, offset: 0 })}
            placeholder="Ref or account..."
            className="rounded-lg border border-slate-200 bg-white pl-8 pr-3 py-1.5 text-sm placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400 w-44"
          />
        </div>

        {/* Severity buttons */}
        <div className="flex gap-1">
          {["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW"].map(s => (
            <button
              key={s}
              onClick={() => setParams({ severity: s, offset: 0 })}
              className={cn(
                "rounded-lg px-2.5 py-1 text-[11px] font-bold transition-all",
                severity === s ? "bg-blue-600 text-white shadow-sm" : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              )}
            >
              {s}
            </button>
          ))}
        </div>

        <button
          onClick={() => setParams({ severity: "ALL", search: null, offset: 0 })}
          className="ml-auto flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-[11px] font-medium text-slate-500 hover:bg-slate-100 transition-colors"
        >
          <RotateCcw className="h-3 w-3" />
          Reset
        </button>
      </div>

      {/* Table + Panel */}
      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_360px]">
        {/* Table */}
        <div className="rounded-xl border border-slate-200 bg-white overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100">
            <span className="text-sm font-semibold text-slate-800">Alert Queue</span>
            <span className="text-xs text-slate-400">
              {listQ.isFetching ? "Refreshing..." : `${filtered.length} alerts · Offset ${offset}`}
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100 bg-slate-50">
                  {["Time", "Risk", "Severity", "Transaction", "Account", "Entity"].map(h => (
                    <th key={h} className="text-left px-4 py-2.5 text-[11px] font-semibold text-slate-500 uppercase tracking-wide whitespace-nowrap">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {listQ.isLoading
                  ? SKELETON_WIDTHS.map((widths, i) => (
                      <tr key={i}>
                        {widths.map((w, j) => (
                          <td key={j} className="px-4 py-3">
                            <div className={cn("h-3 rounded bg-slate-100 animate-pulse", w)} />
                          </td>
                        ))}
                      </tr>
                    ))
                  : filtered.map(a => (
                      <tr
                        key={a.id}
                        onClick={() => setSelectedId(a.id === selectedId ? null : a.id)}
                        className={cn(
                          "cursor-pointer transition-colors group",
                          selectedId === a.id
                            ? "bg-blue-50 border-l-2 border-l-blue-500"
                            : "hover:bg-slate-50"
                        )}
                      >
                        <td className="px-4 py-3 whitespace-nowrap">
                          <div className="text-xs text-slate-600">
                            {a.scored_at ? new Date(a.scored_at).toLocaleDateString() : "—"}
                          </div>
                          <div className="text-[10px] text-slate-400">
                            {a.scored_at ? new Date(a.scored_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : ""}
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <RiskBar score={a.risk_score_0_999} />
                        </td>
                        <td className="px-4 py-3">
                          <SeverityBadge severity={a.severity} />
                        </td>
                        <td className="px-4 py-3">
                          <div className="text-xs font-mono text-slate-700 truncate max-w-[130px]">{a.transaction_reference}</div>
                          <div className="text-[10px] text-slate-400">#{a.transaction_id}</div>
                        </td>
                        <td className="px-4 py-3">
                          <div className="text-xs font-mono text-slate-700">{a.account_id ?? "—"}</div>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-1.5">
                            <EntityIcon vendorCode={a.vendor_code} employeeId={a.employee_id} />
                            <span className="text-xs text-slate-500 truncate max-w-[80px]">
                              {a.vendor_code ?? a.employee_id ?? "—"}
                            </span>
                          </div>
                        </td>
                      </tr>
                    ))
                }
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="flex items-center justify-between px-4 py-3 border-t border-slate-100">
            <span className="text-xs text-slate-400">{count ? `${count.toLocaleString()} total` : `${alerts.length} loaded`}</span>
            <div className="flex gap-2">
              <button
                disabled={offset === 0}
                onClick={() => setParams({ offset: Math.max(0, offset - limit) })}
                className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                Previous
              </button>
              <button
                disabled={filtered.length < limit}
                onClick={() => setParams({ offset: offset + limit })}
                className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                Next
              </button>
            </div>
          </div>
        </div>

        {/* Investigation Panel */}
        <div className="rounded-xl border border-slate-200 bg-white overflow-hidden">
          <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between">
            <span className="text-sm font-semibold text-slate-800">Investigation</span>
            {selectedId && (
              <button onClick={() => setSelectedId(null)} className="text-xs text-slate-400 hover:text-slate-600 transition-colors">
                Clear
              </button>
            )}
          </div>

          {selectedId
            ? <AlertDetailPanel alertId={selectedId} />
            : (
              <div className="flex flex-col items-center justify-center py-14 text-center px-4">
                <div className="rounded-full bg-slate-100 p-4 mb-3">
                  <ShieldAlert className="h-6 w-6 text-slate-400" />
                </div>
                <div className="text-sm font-semibold text-slate-600">No alert selected</div>
                <div className="text-xs text-slate-400 mt-1 max-w-[200px]">
                  Click any row to view risk breakdown, transaction detail, and triggered rules
                </div>
              </div>
            )
          }
        </div>
      </div>
    </div>
  )
}
