// src/app/cases/page.tsx
"use client"

import * as React from "react"
import { useQuery } from "@tanstack/react-query"
import { fetchJson } from "@/lib/api/http"
import { Separator } from "@/components/ui/separator"
import { Badge } from "@/components/ui/badge"

function StatCard({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div className="rounded-xl border bg-card p-4">
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="mt-1 text-2xl font-semibold tabular-nums">{value}</div>
      {sub && <div className="mt-0.5 text-xs text-muted-foreground">{sub}</div>}
    </div>
  )
}

function RoadmapItem({
  phase,
  title,
  description,
  status,
}: {
  phase: string
  title: string
  description: string
  status: "done" | "next" | "future"
}) {
  const colors = {
    done: "bg-green-500/10 text-green-700 dark:text-green-400 border-green-500/20",
    next: "bg-blue-500/10 text-blue-700 dark:text-blue-400 border-blue-500/20",
    future: "bg-muted/50 text-muted-foreground border-border",
  }
  const labels = { done: "Built", next: "Next", future: "Planned" }

  return (
    <div className="flex gap-4">
      <div className="flex flex-col items-center">
        <div
          className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full border text-xs font-mono font-medium ${colors[status]}`}
        >
          {phase}
        </div>
        <div className="mt-1 w-px flex-1 bg-border" />
      </div>
      <div className="pb-6 pt-1">
        <div className="flex items-center gap-2">
          <div className="text-sm font-medium">{title}</div>
          <span className={`rounded-full border px-2 py-0.5 text-[10px] font-medium ${colors[status]}`}>
            {labels[status]}
          </span>
        </div>
        <div className="mt-1 text-xs text-muted-foreground leading-relaxed">{description}</div>
      </div>
    </div>
  )
}

export default function CasesPage() {
  const alertsQ = useQuery({
    queryKey: ["cases.alert-summary"],
    queryFn: () => fetchJson<any>("/api/v1/alerts/summary"),
    staleTime: 30_000,
  })

  const summary = alertsQ.data

  return (
    <div className="mx-auto w-full max-w-[1600px] px-6 py-6 space-y-6">
      {/* Header */}
      <div>
        <div className="text-xs text-muted-foreground">SafeFlow · Analyst</div>
        <h1 className="text-2xl font-semibold tracking-tight">Cases</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Investigation management — link alerts to cases, assign owners, track resolution.
        </p>
      </div>

      <Separator />

      {/* Live alert stats — data that will feed cases */}
      <div>
        <div className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-3">
          Alert Pool — Ready for Case Creation
        </div>
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          <StatCard
            label="Total Alerts"
            value={summary?.total_alerts?.toLocaleString() ?? "—"}
            sub="awaiting triage"
          />
          <StatCard
            label="High Risk"
            value={summary?.high_risk_alerts?.toLocaleString() ?? "—"}
            sub="score ≥ 700"
          />
          <StatCard
            label="Critical"
            value={summary?.critical_alerts?.toLocaleString() ?? "—"}
            sub="score ≥ 850"
          />
          <StatCard
            label="Avg Risk Score"
            value={summary?.avg_risk_score ? Math.round(summary.avg_risk_score) : "—"}
            sub="0–999 scale"
          />
        </div>
      </div>

      <Separator />

      {/* Two column layout */}
      <div className="grid gap-6 lg:grid-cols-[1fr_380px]">
        {/* Roadmap */}
        <div>
          <div className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-4">
            Implementation Roadmap
          </div>
          <div>
            <RoadmapItem
              phase="1"
              title="Streaming Pipeline + Feature Store"
              description="Redpanda → Faust worker → entity_features table. 10k+ events/run, ~20ms latency per event, structured JSON logs."
              status="done"
            />
            <RoadmapItem
              phase="2"
              title="Schema Upgrade + Idempotency"
              description="Foreign keys, unique constraints, ON CONFLICT DO UPDATE, updated_at triggers. Postgres 16."
              status="done"
            />
            <RoadmapItem
              phase="3"
              title="Batch Processing"
              description="Daily recompute of entity_daily_summary, exact 24h/7d windows, entity risk score sync."
              status="done"
            />
            <RoadmapItem
              phase="4"
              title="Data Validation + Rejection"
              description="Pydantic validator with 7 rejection codes, rejected_events table, bad events never reach DB."
              status="done"
            />
            <RoadmapItem
              phase="5"
              title="JWT Auth + API Versioning"
              description="HS256 JWT, analyst/manager roles, /api/v1 prefix, centralized error handler."
              status="done"
            />
            <RoadmapItem
              phase="6"
              title="Case Management"
              description="cases table, alert→case linking, owner assignment, status workflow (Open→In Review→Closed), activity log."
              status="next"
            />
            <RoadmapItem
              phase="7"
              title="Audit Trail + Export"
              description="Audit log for all case actions, CSV/PDF export, compliance-ready timelines."
              status="future"
            />
          </div>
        </div>

        {/* Data model preview */}
        <div className="space-y-4">
          <div className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            Planned Data Model
          </div>
          <div className="rounded-xl border bg-card p-4 font-mono text-xs space-y-1 text-muted-foreground">
            <div className="text-foreground font-semibold mb-2">cases</div>
            <div><span className="text-blue-500">id</span> serial primary key</div>
            <div><span className="text-blue-500">tenant_id</span> integer</div>
            <div><span className="text-blue-500">title</span> varchar</div>
            <div><span className="text-blue-500">status</span> open|review|closed</div>
            <div><span className="text-blue-500">priority</span> low|medium|high|critical</div>
            <div><span className="text-blue-500">owner_id</span> varchar</div>
            <div><span className="text-blue-500">created_at</span> timestamptz</div>
            <div><span className="text-blue-500">closed_at</span> timestamptz</div>
          </div>

          <div className="rounded-xl border bg-card p-4 font-mono text-xs space-y-1 text-muted-foreground">
            <div className="text-foreground font-semibold mb-2">case_alerts (link table)</div>
            <div><span className="text-blue-500">case_id</span> → cases.id</div>
            <div><span className="text-blue-500">alert_id</span> → alerts.id</div>
            <div><span className="text-blue-500">linked_at</span> timestamptz</div>
            <div><span className="text-blue-500">linked_by</span> varchar</div>
          </div>

          <div className="rounded-xl border bg-card p-4 font-mono text-xs space-y-1 text-muted-foreground">
            <div className="text-foreground font-semibold mb-2">case_activity</div>
            <div><span className="text-blue-500">case_id</span> → cases.id</div>
            <div><span className="text-blue-500">actor</span> varchar</div>
            <div><span className="text-blue-500">action</span> varchar</div>
            <div><span className="text-blue-500">note</span> text</div>
            <div><span className="text-blue-500">performed_at</span> timestamptz</div>
          </div>
        </div>
      </div>
    </div>
  )
}
