import * as React from "react"
import type { AlertsSummary } from "@/lib/api/alerts"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"

function formatNumber(n: number) {
  return new Intl.NumberFormat(undefined, { maximumFractionDigits: 0 }).format(n)
}

function KpiCard({
  label,
  value,
  hint,
  loading,
  error,
}: {
  label: string
  value?: string
  hint?: string
  loading?: boolean
  error?: boolean
}) {
  return (
    <Card className="rounded-xl">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="text-xs font-medium text-muted-foreground">{label}</div>
          {error ? (
            <div className="text-[11px] text-destructive">API error</div>
          ) : null}
        </div>
      </CardHeader>

      <CardContent className="space-y-1">
        {loading ? (
          <div className="space-y-2">
            <Skeleton className="h-8 w-24" />
            <Skeleton className="h-3 w-28" />
          </div>
        ) : (
          <>
            <div className="text-2xl font-semibold tabular-nums tracking-tight">{value ?? "—"}</div>
            <div className="text-xs text-muted-foreground">{hint ?? ""}</div>
          </>
        )}
      </CardContent>
    </Card>
  )
}

export function AlertsKpis({
  data,
  isLoading,
  isError,
}: {
  data?: AlertsSummary
  isLoading: boolean
  isError: boolean
}) {
  const total = data?.total_alerts
  const high = data?.high_risk_alerts
  const critical = data?.critical_alerts
  const avg = data?.avg_risk_score

  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      <KpiCard
        label="Total alerts"
        value={isError ? "—" : typeof total === "number" ? formatNumber(total) : "—"}
        hint="All severities"
        loading={isLoading}
        error={isError}
      />
      <KpiCard
        label="High risk"
        value={isError ? "—" : typeof high === "number" ? formatNumber(high) : "—"}
        hint="Severity = HIGH"
        loading={isLoading}
        error={isError}
      />
      <KpiCard
        label="Critical"
        value={isError ? "—" : typeof critical === "number" ? formatNumber(critical) : "—"}
        hint="Severity = CRITICAL"
        loading={isLoading}
        error={isError}
      />
      <KpiCard
        label="Average risk"
        value={isError ? "—" : typeof avg === "number" ? formatNumber(Math.round(avg)) : "—"}
        hint="Fusion score (0–999)"
        loading={isLoading}
        error={isError}
      />
    </div>
  )
}
