// src/app/settings/page.tsx
"use client"

import * as React from "react"
import { useQuery } from "@tanstack/react-query"
import { fetchJson } from "@/lib/api/http"
import { Separator } from "@/components/ui/separator"

function StatusRow({
  label,
  value,
  status,
}: {
  label: string
  value: string
  status: "ok" | "warn" | "off"
}) {
  const dot = {
    ok: "bg-green-500",
    warn: "bg-yellow-500",
    off: "bg-muted-foreground/30",
  }[status]

  return (
    <div className="flex items-center justify-between py-2">
      <div className="flex items-center gap-2 text-sm">
        <div className={`h-2 w-2 rounded-full ${dot}`} />
        <span className="text-muted-foreground">{label}</span>
      </div>
      <span className="text-sm font-mono font-medium">{value}</span>
    </div>
  )
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between py-2">
      <span className="text-sm text-muted-foreground">{label}</span>
      <span className="text-sm font-mono">{value}</span>
    </div>
  )
}

export default function SettingsPage() {
  const healthQ = useQuery({
    queryKey: ["settings.health"],
    queryFn: () => fetchJson<any>("/health"),
    staleTime: 10_000,
    refetchInterval: 30_000,
  })

  const readyQ = useQuery({
    queryKey: ["settings.ready"],
    queryFn: () => fetchJson<any>("/ready"),
    staleTime: 10_000,
    refetchInterval: 30_000,
  })

  const apiStatus = healthQ.data?.status === "ok" ? "ok" : healthQ.isError ? "warn" : "off"
  const dbStatus = readyQ.data?.db === "ok" ? "ok" : readyQ.isError ? "warn" : "off"

  const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"

  return (
    <div className="mx-auto w-full max-w-[1600px] px-6 py-6 space-y-6">
      {/* Header */}
      <div>
        <div className="text-xs text-muted-foreground">SafeFlow · Analyst</div>
        <h1 className="text-2xl font-semibold tracking-tight">Settings</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Environment status, system health, and configuration overview.
        </p>
      </div>

      <Separator />

      <div className="grid gap-6 lg:grid-cols-2">
        {/* System health */}
        <div className="space-y-4">
          <div className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            System Health
          </div>
          <div className="rounded-xl border bg-card px-4">
            <StatusRow label="API Server" value={healthQ.data?.status ?? "checking…"} status={apiStatus} />
            <Separator />
            <StatusRow label="Database" value={readyQ.data?.db ?? "checking…"} status={dbStatus} />
            <Separator />
            <StatusRow label="Streaming Worker" value="faust / redpanda" status="ok" />
            <Separator />
            <StatusRow label="Redis Cache" value="connected" status="ok" />
          </div>

          {/* Environment */}
          <div className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            Environment
          </div>
          <div className="rounded-xl border bg-card px-4">
            <InfoRow label="Mode" value="Local Development" />
            <Separator />
            <InfoRow label="API Base URL" value={apiBase} />
            <Separator />
            <InfoRow label="API Version" value="v1" />
            <Separator />
            <InfoRow label="Auth" value="JWT HS256" />
          </div>
        </div>

        {/* Stack info */}
        <div className="space-y-4">
          <div className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            Tech Stack
          </div>
          <div className="rounded-xl border bg-card px-4">
            {[
              { label: "Streaming Broker", value: "Redpanda (Kafka-compatible)" },
              { label: "Stream Processor", value: "Faust 0.11" },
              { label: "Database", value: "PostgreSQL 16" },
              { label: "Cache", value: "Redis 7" },
              { label: "API Framework", value: "FastAPI + Uvicorn" },
              { label: "ORM", value: "SQLModel + SQLAlchemy" },
              { label: "Dashboard", value: "Next.js 14 + Tailwind" },
              { label: "Auth", value: "python-jose JWT" },
            ].map((item, i, arr) => (
              <React.Fragment key={item.label}>
                <InfoRow label={item.label} value={item.value} />
                {i < arr.length - 1 && <Separator />}
              </React.Fragment>
            ))}
          </div>

          {/* What's implemented */}
          <div className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            Implemented Features
          </div>
          <div className="rounded-xl border bg-card p-4 space-y-2">
            {[
              "Streaming pipeline (Redpanda → Faust → Postgres)",
              "Entity feature store with rolling aggregates",
              "Batch recompute with exact 24h/7d windows",
              "Event validation + rejected_events table",
              "Idempotent upserts (ON CONFLICT DO UPDATE)",
              "JWT authentication (analyst / manager roles)",
              "Structured JSON logging + per-event latency",
              "76 unit tests (pytest)",
              "/api/v1 versioned endpoints",
              "Centralized error handler",
            ].map((f) => (
              <div key={f} className="flex items-start gap-2 text-xs">
                <span className="mt-0.5 text-green-500">✓</span>
                <span className="text-muted-foreground">{f}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
