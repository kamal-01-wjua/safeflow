"use client"

import * as React from "react"
import { usePathname, useRouter, useSearchParams } from "next/navigation"
import { useQuery } from "@tanstack/react-query"

import { getAlerts, getAlertsSummary } from "@/lib/api/alerts"
import type { Severity } from "@/lib/api/alerts"

import { AlertsKpis } from "@/app/alerts/_components/alerts-kpis"
import { AlertsFilters } from "@/app/alerts/_components/alerts-filters"
import { AlertsTable } from "@/app/alerts/_components/alerts-table"
import { AlertDetailPanel } from "@/app/alerts/_components/alert-detail-panel"
import { AlertsTableSkeleton } from "@/app/alerts/_components/skeletons"
import { Separator } from "@/components/ui/separator"

const DEFAULT_LIMIT = 25

function clampInt(n: number, min: number, max: number, fallback: number) {
  if (!Number.isFinite(n)) return fallback
  const v = Math.trunc(n)
  return Math.max(min, Math.min(max, v))
}

function useUrlState() {
  const sp = useSearchParams()
  const router = useRouter()
  const pathname = usePathname()

  const selected = sp.get("selected")

  const severityRaw = (sp.get("severity") ?? "ALL") as Severity | "ALL"
  const severity = String(severityRaw).toUpperCase() as Severity | "ALL"

  const minRisk = clampInt(Number(sp.get("min_risk") ?? "0"), 0, 100, 0)
  const offset = clampInt(Number(sp.get("offset") ?? "0"), 0, 1_000_000, 0)
  const limit = clampInt(Number(sp.get("limit") ?? String(DEFAULT_LIMIT)), 1, 250, DEFAULT_LIMIT)

  const setParams = React.useCallback(
    (next: Partial<Record<string, string | number | null | undefined>>) => {
      const nextSp = new URLSearchParams(sp.toString())

      for (const [k, v] of Object.entries(next)) {
        if (v === null || v === undefined || v === "") nextSp.delete(k)
        else nextSp.set(k, String(v))
      }

      const nextQs = nextSp.toString()
      const currQs = sp.toString()
      if (nextQs === currQs) return

      router.replace(nextQs ? `${pathname}?${nextQs}` : pathname, { scroll: false })
    },
    [sp, router, pathname]
  )

  return {
    selectedId: selected ? Number(selected) : null,
    severity,
    minRisk,
    offset,
    limit,
    setParams,
  }
}

export function AlertsWorkbench() {
  const { selectedId, severity, minRisk, offset, limit, setParams } = useUrlState()

  const summaryQ = useQuery({
    queryKey: ["alerts.summary"],
    queryFn: getAlertsSummary,
    refetchInterval: 30_000,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
    staleTime: 10_000,
  })

  const listQ = useQuery({
    queryKey: ["alerts.list", { severity, minRisk, limit, offset }],
    queryFn: () =>
      getAlerts({
        severity: severity === "ALL" ? "ALL" : severity,
        min_risk: minRisk > 0 ? minRisk : undefined,
        limit,
        offset,
      }),
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
    staleTime: 5_000,
  })

  const items = listQ.data?.items ?? []
  const count = listQ.data?.count

  const onSelect = React.useCallback((id: number) => setParams({ selected: id }), [setParams])
  const onClearSelection = React.useCallback(() => setParams({ selected: null }), [setParams])

  return (
    <div className="h-full min-h-0">
      <div className="mx-auto h-full w-full max-w-[1600px] px-6 py-6 flex min-h-0 flex-col">
        {/* Header */}
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="text-sm text-muted-foreground">SafeFlow · Analyst</div>
            <h1 className="text-2xl font-semibold tracking-tight">Alerts</h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Triage suspicious activity, investigate drivers, and capture explainable risk signals.
            </p>
          </div>

          <div className="text-right text-xs text-muted-foreground">
            <div>API: {process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"}</div>
            <div>{summaryQ.isFetching ? "Refreshing KPIs…" : "Live"}</div>
          </div>
        </div>

        <Separator className="my-5" />

        {/* KPI row */}
        <AlertsKpis data={summaryQ.data} isLoading={summaryQ.isLoading} isError={summaryQ.isError} />

        <div className="mt-6">
          <AlertsFilters
            severity={severity}
            minRisk={minRisk}
            onSeverityChange={(s) => setParams({ severity: s, offset: 0, selected: null })}
            onMinRiskChange={(v) => setParams({ min_risk: v, offset: 0, selected: null })}
          />
        </div>

        <div className="mt-4 grid flex-1 min-h-0 gap-4 lg:grid-cols-[minmax(0,1fr)_420px]">
          {/* LEFT */}
          <div className="rounded-xl border bg-card flex min-h-0 flex-col overflow-hidden">
            <div className="flex items-center justify-between px-4 py-3">
              <div className="text-sm font-medium">Alert Queue</div>
              <div className="text-xs text-muted-foreground">
                Showing {items.length} {typeof count === "number" ? `of ${count}` : ""} · Offset {offset}
              </div>
            </div>
            <Separator />

            <div className="flex-1 min-h-0 overflow-auto">
              {listQ.isLoading ? (
                <AlertsTableSkeleton />
              ) : listQ.isError ? (
                <div className="px-4 py-10 text-sm">
                  <div className="font-medium">Couldn’t load alerts</div>
                  <div className="mt-1 text-muted-foreground">
                    Check that the API is running on <span className="font-mono">localhost:8000</span>.
                  </div>
                  <button
                    className="mt-4 rounded-md border px-3 py-2 text-xs hover:bg-muted"
                    onClick={() => listQ.refetch()}
                  >
                    Retry
                  </button>
                </div>
              ) : items.length === 0 ? (
                <div className="px-4 py-10 text-sm">
                  <div className="font-medium">No alerts match these filters</div>
                  <div className="mt-1 text-muted-foreground">Try lowering minimum risk or widening severity.</div>
                </div>
              ) : (
                <AlertsTable
                  rows={items}
                  selectedId={selectedId}
                  onSelect={onSelect}
                  offset={offset}
                  limit={limit}
                  onPageChange={(nextOffset) => setParams({ offset: nextOffset, selected: null })}
                  count={count}
                />
              )}
            </div>
          </div>

          {/* RIGHT (ONLY place details show now) */}
          <div className="hidden lg:flex min-h-0 flex-col rounded-xl border bg-card overflow-hidden">
            <div className="flex items-center justify-between px-4 py-3">
              <div className="text-sm font-medium">Investigation</div>
              {selectedId ? (
                <button className="rounded-md border px-2 py-1 text-xs hover:bg-muted" onClick={onClearSelection}>
                  Clear
                </button>
              ) : null}
            </div>
            <Separator />

            <div className="flex-1 min-h-0 overflow-auto">
              {selectedId ? (
                <AlertDetailPanel alertId={selectedId} />
              ) : (
                <div className="px-4 py-10 text-sm text-muted-foreground">
                  Select an alert to view evidence, transaction context, and rule-level explanations.
                </div>
              )}
            </div>
          </div>

          {/* ✅ Mobile sheet REMOVED */}
        </div>
      </div>
    </div>
  )
}
