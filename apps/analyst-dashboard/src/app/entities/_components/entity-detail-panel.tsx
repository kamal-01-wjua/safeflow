// src/app/entities/_components/entity-detail-panel.tsx
"use client"

import * as React from "react"
import { useQuery } from "@tanstack/react-query"
import { getEntity, getEntityFeatures } from "@/lib/api/entities"
import { ApiError } from "@/lib/api/http"
import { formatIso } from "@/lib/format"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { EntityDetailSkeleton } from "@/app/entities/_components/skeletons"

function clamp(n: number, min: number, max: number) {
  return Math.max(min, Math.min(max, n))
}

function riskTone0to100(risk: number) {
  if (risk >= 80) return "destructive"
  if (risk >= 60) return "default"
  if (risk >= 30) return "secondary"
  return "outline"
}

function riskTone0to999(risk: number) {
  if (risk >= 800) return "destructive"
  if (risk >= 500) return "default"
  if (risk >= 200) return "secondary"
  return "outline"
}

function toDisplayString(v: unknown): string {
  if (v === null || v === undefined) return "—"
  if (typeof v === "string") return v
  if (typeof v === "number") return Number.isFinite(v) ? String(v) : "—"
  if (typeof v === "boolean") return v ? "Yes" : "No"
  try { return JSON.stringify(v) } catch { return String(v) }
}

function fmt(n: number, decimals = 2) {
  return n.toLocaleString("en-US", { minimumFractionDigits: decimals, maximumFractionDigits: decimals })
}

function FieldRow({ label, value, mono }: { label: string; value: unknown; mono?: boolean }) {
  const str = toDisplayString(value)
  const onCopy = React.useCallback(async () => {
    try { await navigator.clipboard.writeText(str === "—" ? "" : str) } catch {}
  }, [str])

  return (
    <div className="grid grid-cols-[140px_1fr_auto] gap-3 py-2">
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className={["text-sm break-words", mono ? "font-mono text-[12px]" : ""].join(" ")}>{str}</div>
      <Button type="button" variant="ghost" size="sm" className="h-7 px-2 text-xs"
        onClick={onCopy} disabled={str === "—"} title="Copy">
        Copy
      </Button>
    </div>
  )
}

// ── Stat tile used in the features grid ─────────────────────────────────────
function StatTile({
  label,
  value,
  sub,
  highlight,
}: {
  label: string
  value: string | number
  sub?: string
  highlight?: "danger" | "warn" | "ok" | "neutral"
}) {
  const bg =
    highlight === "danger" ? "bg-destructive/10 border-destructive/30" :
    highlight === "warn"   ? "bg-yellow-500/10 border-yellow-500/30" :
    highlight === "ok"     ? "bg-green-500/10 border-green-500/30" :
    "bg-muted/20 border-border"

  return (
    <div className={`rounded-lg border p-3 flex flex-col gap-1 ${bg}`}>
      <div className="text-[11px] text-muted-foreground leading-tight">{label}</div>
      <div className="text-lg font-semibold leading-tight">{value}</div>
      {sub && <div className="text-[11px] text-muted-foreground">{sub}</div>}
    </div>
  )
}

// ── Features section ─────────────────────────────────────────────────────────
function FeaturesSection({ entityId }: { entityId: number }) {
  const q = useQuery({
    queryKey: ["entities.features", entityId],
    queryFn: () => getEntityFeatures(entityId),
    refetchOnWindowFocus: false,
    staleTime: 15_000,
  })

  if (q.isLoading) {
    return (
      <div className="grid grid-cols-2 gap-2 animate-pulse">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="h-16 rounded-lg bg-muted/30" />
        ))}
      </div>
    )
  }

  if (q.isError || !q.data) {
    return (
      <div className="text-sm text-muted-foreground">
        Could not load feature data.{" "}
        <button className="underline" onClick={() => q.refetch()}>Retry</button>
      </div>
    )
  }

  const f = q.data
  const hasData = f.source === "entity_features"

  if (!hasData) {
    return (
      <div className="rounded-lg border bg-muted/20 px-4 py-3 text-sm text-muted-foreground">
        No streaming data yet for this entity. Send transactions with account_id matching
        this entity's ID to populate features.
      </div>
    )
  }

  const riskHighlight =
    f.latest_risk_score >= 800 ? "danger" :
    f.latest_risk_score >= 500 ? "warn" :
    f.latest_risk_score >= 200 ? "neutral" : "ok"

  const velocityHighlight = f.is_velocity_flagged ? "danger" : "ok"
  const consecutiveHighlight = f.consecutive_high_risk >= 5 ? "danger" :
    f.consecutive_high_risk >= 2 ? "warn" : "ok"

  return (
    <div className="space-y-3">
      {/* Source badge */}
      <div className="flex items-center gap-2">
        <div className="h-2 w-2 rounded-full bg-green-500" />
        <span className="text-[11px] text-muted-foreground">
          Live from streaming worker · last seen{" "}
          {f.last_seen_at ? formatIso(f.last_seen_at) : "—"}
        </span>
      </div>

      {/* Volume grid */}
      <div className="text-[11px] font-medium text-muted-foreground uppercase tracking-wide">
        Volume
      </div>
      <div className="grid grid-cols-3 gap-2">
        <StatTile label="Total Tx" value={f.tx_count_total.toLocaleString()} highlight="neutral" />
        <StatTile label="Last 24h" value={f.tx_count_24h.toLocaleString()}
          sub="approx" highlight={f.tx_count_24h > 20 ? "warn" : "neutral"} />
        <StatTile label="Last 7d" value={f.tx_count_7d.toLocaleString()}
          sub="approx" highlight="neutral" />
      </div>

      {/* Amount grid */}
      <div className="text-[11px] font-medium text-muted-foreground uppercase tracking-wide mt-1">
        Amounts
      </div>
      <div className="grid grid-cols-2 gap-2">
        <StatTile label="Avg Amount" value={`${fmt(f.amount_avg)}`} highlight="neutral" />
        <StatTile label="Max Amount" value={`${fmt(f.amount_max)}`} highlight="neutral" />
        <StatTile label="Total Amount" value={`${fmt(f.amount_total)}`} highlight="neutral" />
        <StatTile label="Last Amount" value={`${fmt(f.amount_last)}`} highlight="neutral" />
      </div>

      {/* Risk grid */}
      <div className="text-[11px] font-medium text-muted-foreground uppercase tracking-wide mt-1">
        Risk Signals
      </div>
      <div className="grid grid-cols-2 gap-2">
        <StatTile
          label="Latest Risk Score"
          value={f.latest_risk_score}
          sub="0–999 scale"
          highlight={riskHighlight}
        />
        <StatTile
          label="Avg Risk Score"
          value={fmt(f.risk_score_avg, 1)}
          sub="rolling avg"
          highlight="neutral"
        />
        <StatTile
          label="High-Risk Tx"
          value={f.high_risk_tx_count.toLocaleString()}
          sub={`of ${f.tx_count_total} total`}
          highlight={f.high_risk_tx_count > 10 ? "danger" : f.high_risk_tx_count > 3 ? "warn" : "ok"}
        />
        <StatTile
          label="Consecutive High-Risk"
          value={f.consecutive_high_risk}
          sub="resets on low-risk"
          highlight={consecutiveHighlight}
        />
      </div>

      {/* Flags */}
      <div className="text-[11px] font-medium text-muted-foreground uppercase tracking-wide mt-1">
        Flags
      </div>
      <div className="grid grid-cols-1 gap-2">
        <StatTile
          label="Velocity Flagged"
          value={f.is_velocity_flagged ? "YES — above threshold" : "No"}
          sub="> 20 tx in 24h window"
          highlight={velocityHighlight}
        />
      </div>

      {/* Temporal */}
      <div className="rounded-md border bg-muted/20 px-3 mt-1">
        <FieldRow label="first_seen_at" value={f.first_seen_at ? formatIso(f.first_seen_at) : null} />
        <FieldRow label="last_seen_at" value={f.last_seen_at ? formatIso(f.last_seen_at) : null} />
        <FieldRow label="account_id" value={f.account_id} mono />
      </div>
    </div>
  )
}

// ── Main panel body ───────────────────────────────────────────────────────────
function PanelBody({ entityId }: { entityId: number }) {
  const q = useQuery({
    queryKey: ["entities.detail", entityId],
    queryFn: () => getEntity(entityId),
    refetchOnWindowFocus: false,
    staleTime: 15_000,
  })

  if (q.isLoading) return <EntityDetailSkeleton />

  if (q.isError) {
    const err = q.error
    const isApi = err instanceof ApiError
    const title = isApi && err.status === 404 ? "Entity not found" : "Couldn't load entity"
    const subtitle = isApi
      ? `API error ${err.status}: ${err.message}`
      : "Try selecting it again or refresh."
    return (
      <div className="p-4 text-sm">
        <div className="font-medium">{title}</div>
        <div className="mt-1 text-muted-foreground">{subtitle}</div>
        <Button className="mt-4" variant="outline" size="sm" onClick={() => q.refetch()}>Retry</Button>
      </div>
    )
  }

  const e = q.data ?? ({} as any)
  const name = String(e?.name ?? e?.entity_id ?? `Entity #${entityId}`)
  const entityCode = e?.entity_id ?? null
  const type = String(e?.type ?? "UNKNOWN").toUpperCase()
  const riskRaw = typeof e?.risk_score === "number" ? e.risk_score : Number(e?.risk_score ?? 0)
  const risk = Number.isFinite(riskRaw) ? clamp(Math.round(riskRaw), 0, 100) : 0
  const created = typeof e?.created_at === "string" ? formatIso(e.created_at) : e?.created_at
  const updated = typeof e?.updated_at === "string" ? formatIso(e.updated_at) : e?.updated_at

  const KEY_FIELDS = new Set(["id","entity_id","name","type","risk_score","country_code","created_at","updated_at"])
  const extraEntries = Object.entries(e ?? {})
    .filter(([k]) => !KEY_FIELDS.has(k))
    .sort(([a], [b]) => a.localeCompare(b))

  return (
    <div className="p-4 space-y-0">
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="text-sm font-semibold truncate">{name}</div>
          <div className="mt-1 flex flex-wrap items-center gap-2">
            <Badge variant="secondary" className="text-[11px]">{type}</Badge>
            <Badge variant={riskTone0to100(risk) as any} className="text-[11px]">Risk {risk}</Badge>
            {entityCode && (
              <Badge variant="outline" className="text-[11px] font-mono">{String(entityCode)}</Badge>
            )}
          </div>
        </div>
        <div className="text-right text-[11px] text-muted-foreground">
          <div className="font-mono">#{entityId}</div>
        </div>
      </div>

      <Separator className="my-4" />

      {/* Key details */}
      <div className="text-xs font-medium text-muted-foreground mb-2">Key details</div>
      <div className="rounded-md border bg-muted/20 px-3">
        <FieldRow label="id" value={e?.id ?? entityId} mono />
        <FieldRow label="entity_id" value={entityCode} mono />
        <FieldRow label="country_code" value={e?.country_code ?? null} mono />
        <FieldRow label="created_at" value={created ?? null} />
        <FieldRow label="updated_at" value={updated ?? null} />
      </div>

      {/* ── Streaming Features ── */}
      <Separator className="my-4" />
      <div className="text-xs font-medium text-muted-foreground mb-3">
        Streaming Features{" "}
        <span className="ml-1 text-[10px] bg-green-500/20 text-green-700 dark:text-green-400 px-1.5 py-0.5 rounded-full">
          LIVE
        </span>
      </div>
      <FeaturesSection entityId={entityId} />

      {/* Extra fields */}
      {extraEntries.length > 0 && (
        <>
          <Separator className="my-4" />
          <div className="flex items-center justify-between mb-2">
            <div className="text-xs font-medium text-muted-foreground">All fields</div>
            <div className="text-[11px] text-muted-foreground">{extraEntries.length} extra</div>
          </div>
          <div className="rounded-md border bg-card px-3">
            {extraEntries.map(([k, v]) => <FieldRow key={k} label={k} value={v} />)}
          </div>
        </>
      )}

      {/* Raw JSON */}
      <Separator className="my-4" />
      <details className="rounded-md border bg-muted/20 p-3">
        <summary className="cursor-pointer text-xs font-medium text-muted-foreground select-none">
          Raw JSON
        </summary>
        <div className="mt-3 rounded-md border bg-muted/30 p-3 text-xs font-mono whitespace-pre-wrap break-words">
          {JSON.stringify(e ?? {}, null, 2)}
        </div>
      </details>
    </div>
  )
}

export function EntityDetailPanel({
  entityId,
  mobile,
  onClose,
}: {
  entityId?: number
  mobile?: boolean
  onClose?: () => void
}) {
  if (mobile) return null  // mobile sheet removed per earlier decision
  if (!entityId) return null
  return <PanelBody entityId={entityId} />
}
