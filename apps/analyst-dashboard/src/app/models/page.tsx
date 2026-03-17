// src/app/models/page.tsx
"use client"

import * as React from "react"
import { useQuery } from "@tanstack/react-query"
import { fetchJson } from "@/lib/api/http"
import { Separator } from "@/components/ui/separator"

function StatCard({
  label,
  value,
  sub,
  highlight,
}: {
  label: string
  value: string | number
  sub?: string
  highlight?: boolean
}) {
  return (
    <div className={`rounded-xl border p-4 ${highlight ? "bg-blue-500/5 border-blue-500/20" : "bg-card"}`}>
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="mt-1 text-2xl font-semibold tabular-nums">{value}</div>
      {sub && <div className="mt-0.5 text-xs text-muted-foreground">{sub}</div>}
    </div>
  )
}

function SeverityBar({
  label,
  count,
  total,
  color,
}: {
  label: string
  count: number
  total: number
  color: string
}) {
  const pct = total > 0 ? Math.round((count / total) * 100) : 0
  return (
    <div>
      <div className="flex items-center justify-between text-xs mb-1">
        <span className="text-muted-foreground">{label}</span>
        <span className="font-mono font-medium">{count.toLocaleString()} ({pct}%)</span>
      </div>
      <div className="h-2 rounded-full bg-muted overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}

export default function ModelsPage() {
  const alertsQ = useQuery({
    queryKey: ["models.alert-summary"],
    queryFn: () => fetchJson<any>("/api/v1/alerts/summary"),
    staleTime: 30_000,
  })

  const entitiesQ = useQuery({
    queryKey: ["models.entities"],
    queryFn: () => fetchJson<any>("/api/v1/entities/?limit=500"),
    staleTime: 60_000,
  })

  const summary = alertsQ.data
  const entityItems = entitiesQ.data?.items ?? []

  // Compute risk distribution from entities
  const riskBands = React.useMemo(() => {
    const low = entityItems.filter((e: any) => (e.risk_score ?? 0) < 30).length
    const med = entityItems.filter((e: any) => (e.risk_score ?? 0) >= 30 && (e.risk_score ?? 0) < 60).length
    const high = entityItems.filter((e: any) => (e.risk_score ?? 0) >= 60 && (e.risk_score ?? 0) < 80).length
    const crit = entityItems.filter((e: any) => (e.risk_score ?? 0) >= 80).length
    return { low, med, high, crit, total: entityItems.length }
  }, [entityItems])

  const total = summary?.total_alerts ?? 0
  const highRisk = summary?.high_risk_alerts ?? 0
  const critical = summary?.critical_alerts ?? 0
  const avgScore = summary?.avg_risk_score ? Math.round(summary.avg_risk_score) : 0
  const lowRisk = total - highRisk

  return (
    <div className="mx-auto w-full max-w-[1600px] px-6 py-6 space-y-6">
      {/* Header */}
      <div>
        <div className="text-xs text-muted-foreground">SafeFlow · Analyst</div>
        <h1 className="text-2xl font-semibold tracking-tight">Models</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Pipeline signal coverage, score distributions, and scoring engine status.
        </p>
      </div>

      <Separator />

      {/* Scoring engine status */}
      <div>
        <div className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-3">
          Scoring Engine Status
        </div>
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          <StatCard label="Rule Engine" value="Active" sub="deterministic rules" highlight />
          <StatCard label="ML Engine" value="Dummy" sub="xgboost not installed" />
          <StatCard label="Graph Engine" value="Active" sub="motif detection" highlight />
          <StatCard label="Fusion" value="Active" sub="weighted combination" highlight />
        </div>
      </div>

      <Separator />

      {/* Alert score distribution */}
      <div className="grid gap-6 lg:grid-cols-2">
        <div>
          <div className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-3">
            Alert Score Distribution
          </div>
          <div className="grid grid-cols-2 gap-3 mb-4">
            <StatCard label="Total Alerts" value={total.toLocaleString()} sub="all time" />
            <StatCard label="Avg Risk Score" value={avgScore} sub="0–999 scale" />
          </div>
          <div className="rounded-xl border bg-card p-4 space-y-4">
            <SeverityBar
              label="LOW (< 200)"
              count={lowRisk}
              total={total}
              color="bg-green-500"
            />
            <SeverityBar
              label="HIGH (≥ 700)"
              count={highRisk}
              total={total}
              color="bg-orange-500"
            />
            <SeverityBar
              label="CRITICAL (≥ 850)"
              count={critical}
              total={total}
              color="bg-red-500"
            />
          </div>
        </div>

        {/* Entity risk distribution */}
        <div>
          <div className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-3">
            Entity Risk Distribution (0–100 scale)
          </div>
          <div className="grid grid-cols-2 gap-3 mb-4">
            <StatCard label="Total Entities" value={riskBands.total} sub="in system" />
            <StatCard
              label="High Risk Entities"
              value={riskBands.high + riskBands.crit}
              sub="score ≥ 60"
            />
          </div>
          <div className="rounded-xl border bg-card p-4 space-y-4">
            <SeverityBar
              label="LOW (0–29)"
              count={riskBands.low}
              total={riskBands.total}
              color="bg-green-500"
            />
            <SeverityBar
              label="MEDIUM (30–59)"
              count={riskBands.med}
              total={riskBands.total}
              color="bg-yellow-500"
            />
            <SeverityBar
              label="HIGH (60–79)"
              count={riskBands.high}
              total={riskBands.total}
              color="bg-orange-500"
            />
            <SeverityBar
              label="CRITICAL (80–100)"
              count={riskBands.crit}
              total={riskBands.total}
              color="bg-red-500"
            />
          </div>
        </div>
      </div>

      <Separator />

      {/* Scoring pipeline architecture */}
      <div>
        <div className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-3">
          Scoring Pipeline Architecture
        </div>
        <div className="rounded-xl border bg-card p-4">
          <div className="flex items-center gap-2 flex-wrap text-xs">
            {[
              { label: "Redpanda", desc: "Kafka-compatible broker" },
              { label: "→" },
              { label: "Faust Worker", desc: "Stream processor" },
              { label: "→" },
              { label: "Rule Engine", desc: "Deterministic rules" },
              { label: "+" },
              { label: "ML Engine", desc: "XGBoost (dummy)" },
              { label: "+" },
              { label: "Graph Engine", desc: "Motif detection" },
              { label: "→" },
              { label: "Fusion Score", desc: "0–999 weighted" },
              { label: "→" },
              { label: "Postgres", desc: "alerts + entity_features" },
            ].map((item, i) =>
              item.desc ? (
                <div key={i} className="rounded-lg border bg-muted/30 px-3 py-2 text-center">
                  <div className="font-medium text-foreground">{item.label}</div>
                  <div className="text-muted-foreground">{item.desc}</div>
                </div>
              ) : (
                <div key={i} className="text-muted-foreground font-mono text-base px-1">
                  {item.label}
                </div>
              )
            )}
          </div>
        </div>
      </div>

      {/* Roadmap note */}
      <div className="rounded-xl border bg-muted/20 p-4">
        <div className="text-xs font-medium text-muted-foreground mb-1">Coming in future phases</div>
        <div className="text-sm text-muted-foreground">
          Real XGBoost model trained on synthetic data · SHAP feature importance · Rule coverage analysis ·
          Score drift detection · MLflow experiment tracking
        </div>
      </div>
    </div>
  )
}
