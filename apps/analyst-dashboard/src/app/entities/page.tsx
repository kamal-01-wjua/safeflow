"use client"

import * as React from "react"
import { useQuery } from "@tanstack/react-query"
import { fetchJson } from "@/lib/api/http"
import {
  User, Building2, Briefcase, CreditCard, Store, Users,
  Search, SlidersHorizontal, RotateCcw, ChevronRight,
} from "lucide-react"
import { cn } from "@/lib/utils"

// ── Entity type config ────────────────────────────────────────────────────────
const ENTITY_TYPE_CONFIG: Record<string, { icon: React.ReactNode; color: string; bg: string }> = {
  PERSON:   { icon: <User className="h-3.5 w-3.5" />,       color: "text-blue-700",   bg: "bg-blue-50 border-blue-200" },
  COMPANY:  { icon: <Building2 className="h-3.5 w-3.5" />,   color: "text-purple-700", bg: "bg-purple-50 border-purple-200" },
  VENDOR:   { icon: <Briefcase className="h-3.5 w-3.5" />,   color: "text-amber-700",  bg: "bg-amber-50 border-amber-200" },
  ACCOUNT:  { icon: <CreditCard className="h-3.5 w-3.5" />,  color: "text-emerald-700",bg: "bg-emerald-50 border-emerald-200" },
  MERCHANT: { icon: <Store className="h-3.5 w-3.5" />,       color: "text-rose-700",   bg: "bg-rose-50 border-rose-200" },
  EMPLOYEE: { icon: <Users className="h-3.5 w-3.5" />,       color: "text-cyan-700",   bg: "bg-cyan-50 border-cyan-200" },
}

function EntityTypeBadge({ type }: { type: string }) {
  const config = ENTITY_TYPE_CONFIG[type] ?? { icon: <Building2 className="h-3.5 w-3.5" />, color: "text-slate-700", bg: "bg-slate-100 border-slate-200" }
  return (
    <span className={cn("inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-semibold", config.color, config.bg)}>
      {config.icon}
      {type}
    </span>
  )
}

function RiskPill({ score }: { score: number }) {
  if (score === 0 || score === null || score === undefined) return <span className="text-xs text-slate-400">—</span>
  const color = score >= 80 ? "bg-red-500 text-white" : score >= 60 ? "bg-orange-500 text-white" : score >= 30 ? "bg-yellow-500 text-white" : "bg-emerald-500 text-white"
  return (
    <span className={cn("inline-flex items-center justify-center rounded-full h-6 min-w-[1.5rem] px-1.5 text-[11px] font-bold tabular-nums", color)}>
      {score}
    </span>
  )
}

export default function EntitiesPage() {
  const [search, setSearch] = React.useState("")
  const [typeFilter, setTypeFilter] = React.useState("ALL")
  const [minRisk, setMinRisk] = React.useState(0)
  const [selectedId, setSelectedId] = React.useState<number | null>(null)

  const entitiesQ = useQuery({
    queryKey: ["entities.list"],
    queryFn: () => fetchJson<any>("/api/v1/entities/?limit=100"),
    staleTime: 30_000,
  })

  const selectedQ = useQuery({
    queryKey: ["entities.detail", selectedId],
    queryFn: () => fetchJson<any>(`/api/v1/entities/${selectedId}`),
    enabled: !!selectedId,
    staleTime: 60_000,
  })

  const featuresQ = useQuery({
    queryKey: ["entities.features", selectedId],
    queryFn: () => fetchJson<any>(`/api/v1/entities/${selectedId}/features`),
    enabled: !!selectedId,
    staleTime: 60_000,
  })

  const items: any[] = entitiesQ.data?.items ?? []
  const types = ["ALL", ...Array.from(new Set(items.map((e) => e.type))).sort()]

  const filtered = items.filter((e) => {
    if (typeFilter !== "ALL" && e.type !== typeFilter) return false
    if (minRisk > 0 && (e.risk_score ?? 0) < minRisk) return false
    if (search && !e.name?.toLowerCase().includes(search.toLowerCase()) && !e.entity_id?.toLowerCase().includes(search.toLowerCase())) return false
    return true
  })

  const selected = selectedQ.data
  const features = featuresQ.data

  return (
    <div className="mx-auto w-full max-w-[1400px] px-6 py-6 space-y-5">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-slate-900 tracking-tight">Entities</h1>
        <p className="text-sm text-slate-500 mt-0.5">Entity 360 — vendors, employees, accounts with risk context.</p>
      </div>

      {/* Filters */}
      <div className="rounded-xl border border-slate-200 bg-white px-4 py-3 space-y-3">
        <div className="flex items-center gap-3">
          <SlidersHorizontal className="h-4 w-4 text-slate-400 shrink-0" />
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Filters</span>
          <button
            onClick={() => { setSearch(""); setTypeFilter("ALL"); setMinRisk(0) }}
            className="ml-auto flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-[11px] font-medium text-slate-500 hover:bg-slate-100 transition-colors"
          >
            <RotateCcw className="h-3 w-3" />
            Reset
          </button>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search name or ID..."
              className="rounded-lg border border-slate-200 bg-white pl-8 pr-3 py-1.5 text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400 w-52"
            />
          </div>

          {/* Type filter */}
          <div className="flex flex-wrap gap-1">
            {types.map((t) => {
              const config = t !== "ALL" ? ENTITY_TYPE_CONFIG[t] : null
              return (
                <button
                  key={t}
                  onClick={() => setTypeFilter(t)}
                  className={cn(
                    "inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-[11px] font-semibold border transition-all",
                    typeFilter === t
                      ? "bg-blue-600 text-white border-blue-600 shadow-sm"
                      : "bg-white text-slate-600 border-slate-200 hover:border-slate-300 hover:bg-slate-50"
                  )}
                >
                  {config && <span className={typeFilter === t ? "text-white" : config.color}>{config.icon}</span>}
                  {t}
                </button>
              )
            })}
          </div>
        </div>
      </div>

      {/* Table + Detail */}
      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_360px]">
        {/* Table */}
        <div className="rounded-xl border border-slate-200 bg-white overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100">
            <span className="text-sm font-semibold text-slate-800">Entity Results</span>
            <span className="text-xs text-slate-400">{filtered.length} of {items.length}</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100 bg-slate-50">
                  <th className="text-left px-4 py-2.5 text-[11px] font-semibold text-slate-500 uppercase tracking-wide">Name</th>
                  <th className="text-left px-4 py-2.5 text-[11px] font-semibold text-slate-500 uppercase tracking-wide">Type</th>
                  <th className="text-left px-4 py-2.5 text-[11px] font-semibold text-slate-500 uppercase tracking-wide">Risk</th>
                  <th className="text-left px-4 py-2.5 text-[11px] font-semibold text-slate-500 uppercase tracking-wide hidden xl:table-cell">Updated</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {entitiesQ.isLoading ? (
                  Array.from({ length: 8 }).map((_, i) => (
                    <tr key={i}>
                      {Array.from({ length: 4 }).map((_, j) => (
                        <td key={j} className="px-4 py-3">
                          <div className="h-3 rounded bg-slate-100 animate-pulse" />
                        </td>
                      ))}
                    </tr>
                  ))
                ) : filtered.map((e) => (
                  <tr
                    key={e.id}
                    onClick={() => setSelectedId(e.id === selectedId ? null : e.id)}
                    className={cn(
                      "cursor-pointer transition-colors",
                      selectedId === e.id
                        ? "bg-blue-50 border-l-2 border-l-blue-500"
                        : "hover:bg-slate-50"
                    )}
                  >
                    <td className="px-4 py-3">
                      <div className="font-medium text-slate-800 text-sm">{e.name}</div>
                      <div className="text-[10px] text-slate-400 font-mono mt-0.5">{e.entity_id}</div>
                    </td>
                    <td className="px-4 py-3">
                      <EntityTypeBadge type={e.type} />
                    </td>
                    <td className="px-4 py-3">
                      <RiskPill score={e.risk_score} />
                    </td>
                    <td className="px-4 py-3 hidden xl:table-cell">
                      <span className="text-xs text-slate-400">
                        {e.updated_at ? new Date(e.updated_at).toLocaleDateString() : "—"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Entity 360 Panel */}
        <div className="rounded-xl border border-slate-200 bg-white overflow-hidden">
          <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between">
            <span className="text-sm font-semibold text-slate-800">Entity 360</span>
            {selectedId && (
              <button onClick={() => setSelectedId(null)} className="text-xs text-slate-400 hover:text-slate-600 transition-colors">
                Clear
              </button>
            )}
          </div>

          {!selectedId ? (
            <div className="flex flex-col items-center justify-center py-12 text-center px-4">
              <div className="rounded-full bg-slate-100 p-4 mb-3">
                <Building2 className="h-6 w-6 text-slate-400" />
              </div>
              <div className="text-sm font-medium text-slate-600">No entity selected</div>
              <div className="text-xs text-slate-400 mt-1">Click any row to view profile, risk summary, and features</div>
            </div>
          ) : (
            <div className="p-4 space-y-4 overflow-y-auto max-h-[600px]">
              {selectedQ.isLoading ? (
                <div className="space-y-2">
                  {Array.from({ length: 4 }).map((_, i) => (
                    <div key={i} className="h-4 rounded bg-slate-100 animate-pulse" />
                  ))}
                </div>
              ) : selected ? (
                <>
                  {/* Profile */}
                  <div>
                    <div className="flex items-start gap-3">
                      <div className={cn("rounded-xl p-2.5 border", ENTITY_TYPE_CONFIG[selected.type]?.bg ?? "bg-slate-100 border-slate-200")}>
                        <span className={ENTITY_TYPE_CONFIG[selected.type]?.color ?? "text-slate-600"}>
                          {ENTITY_TYPE_CONFIG[selected.type]?.icon ?? <Building2 className="h-4 w-4" />}
                        </span>
                      </div>
                      <div>
                        <div className="font-semibold text-slate-900">{selected.name}</div>
                        <div className="text-xs text-slate-400 font-mono">{selected.entity_id}</div>
                        <EntityTypeBadge type={selected.type} />
                      </div>
                      <div className="ml-auto">
                        <RiskPill score={selected.risk_score} />
                      </div>
                    </div>
                  </div>

                  {/* Features */}
                  {features && (
                    <div>
                      <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-400 mb-2">Live Features</div>
                      <div className="grid grid-cols-2 gap-2">
                        {[
                          { label: "TX Total", value: features.tx_count_total?.toLocaleString() },
                          { label: "TX 24h", value: features.tx_count_24h },
                          { label: "TX 7d", value: features.tx_count_7d },
                          { label: "Avg Amount", value: features.amount_avg ? `${Number(features.amount_avg).toFixed(0)}` : "—" },
                          { label: "Max Amount", value: features.amount_max ? `${Number(features.amount_max).toFixed(0)}` : "—" },
                          { label: "High Risk TX", value: features.high_risk_tx_count },
                        ].map((f) => (
                          <div key={f.label} className="rounded-lg border border-slate-100 bg-slate-50 p-2">
                            <div className="text-[10px] text-slate-400">{f.label}</div>
                            <div className="text-sm font-bold text-slate-800 tabular-nums">{f.value ?? "—"}</div>
                          </div>
                        ))}
                      </div>
                      {features.is_velocity_flagged && (
                        <div className="mt-2 rounded-lg border border-orange-200 bg-orange-50 px-3 py-2 flex items-center gap-2">
                          <span className="h-2 w-2 rounded-full bg-orange-500" />
                          <span className="text-xs font-semibold text-orange-700">Velocity Flagged</span>
                        </div>
                      )}
                    </div>
                  )}
                </>
              ) : null}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
