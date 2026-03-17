"use client"

import * as React from "react"
import { useQuery } from "@tanstack/react-query"

import { getAlertDetail } from "@/lib/api/alerts"
import { formatIso } from "@/lib/format"
import { formatMoney } from "@/lib/format"
import { ruleMeta } from "@/lib/rules"

import { SeverityPill } from "@/components/risk/severity-pill"
import { RiskScoreBadge } from "@/components/risk/risk-score-badge"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet"
import { DetailSkeleton } from "@/app/alerts/_components/skeletons"

function clamp(n: number, min: number, max: number) {
  return Math.max(min, Math.min(max, n))
}

function ScoreBar({ value, max = 999 }: { value: number; max?: number }) {
  const pct = clamp((value / max) * 100, 0, 100)
  return (
    <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-muted">
      <div className="h-full bg-foreground/70" style={{ width: `${pct}%` }} />
    </div>
  )
}

function RuleChip({ code }: { code: string }) {
  const meta = ruleMeta(code)
  const variant = meta.tone === "danger" ? "destructive" : meta.tone === "warning" ? "secondary" : "outline"
  return (
    <Badge variant={variant} className="text-[11px]">
      {meta.label}
    </Badge>
  )
}

function KV({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="rounded-md bg-muted/30 p-2">
      <div className="text-[11px] text-muted-foreground">{label}</div>
      <div className="mt-1 text-xs font-medium">{value}</div>
    </div>
  )
}

function PanelBody({ alertId }: { alertId: number }) {
  const q = useQuery({
    queryKey: ["alerts.detail", alertId],
    queryFn: () => getAlertDetail(alertId),
    enabled: Number.isFinite(alertId),
  })

  if (q.isLoading) return <DetailSkeleton />
  if (q.isError) {
    return (
      <div className="px-4 py-8 text-sm">
        <div className="font-medium">Couldn’t load alert detail</div>
        <div className="mt-1 text-muted-foreground">Try again, or verify the ID exists.</div>
        <Button className="mt-4" variant="outline" size="sm" onClick={() => q.refetch()}>
          Retry
        </Button>
      </div>
    )
  }

  const data = q.data
  if (!data) return null

  const a = data.alert
  const t = data.transaction

  const ref = a.transaction_reference ?? t.description ?? `Alert ${a.id}`

  return (
    <div className="px-4 py-4">
      {/* Summary */}
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="text-xs text-muted-foreground">Alert #{a.id}</div>

          <div className="mt-1 flex flex-wrap items-center gap-2">
            <SeverityPill severity={a.severity} />
            <div className="text-xs text-muted-foreground">scored {formatIso(a.scored_at)}</div>
          </div>

          <div className="mt-2 truncate font-mono text-xs text-muted-foreground">{ref}</div>
        </div>

        <div className="shrink-0 text-right">
          <RiskScoreBadge score={a.risk_score_0_999} />
          <ScoreBar value={a.risk_score_0_999} />
        </div>
      </div>

      <Separator className="my-4" />

      {/* Signals */}
      <div>
        <div className="text-xs font-medium text-muted-foreground">Signal breakdown</div>
        <div className="mt-2 grid grid-cols-3 gap-2 text-xs">
          <div className="rounded-md border p-2">
            <div className="text-muted-foreground">Rule</div>
            <div className="mt-1 font-semibold tabular-nums">{a.rule_score ?? "—"}</div>
          </div>
          <div className="rounded-md border p-2">
            <div className="text-muted-foreground">ML</div>
            <div className="mt-1 font-semibold tabular-nums">{a.ml_score ?? "—"}</div>
          </div>
          <div className="rounded-md border p-2">
            <div className="text-muted-foreground">Graph</div>
            <div className="mt-1 font-semibold tabular-nums">{a.graph_score ?? "—"}</div>
          </div>
        </div>
      </div>

      {/* Triggered rules */}
      <div className="mt-4">
        <div className="text-xs font-medium text-muted-foreground">Triggered rules</div>
        <div className="mt-2 flex flex-wrap gap-2">
          {a.triggered_rules?.length ? (
            a.triggered_rules.map((r) => <RuleChip key={r} code={r} />)
          ) : (
            <div className="text-xs text-muted-foreground">No triggered rules recorded.</div>
          )}
        </div>
      </div>

      {/* Graph motifs */}
      <div className="mt-4">
        <div className="text-xs font-medium text-muted-foreground">Graph context</div>
        <div className="mt-2 rounded-md border bg-muted/20 p-3 text-xs leading-relaxed">
          {a.graph_motifs ? a.graph_motifs : "No graph motifs available yet."}
        </div>
      </div>

      <Separator className="my-4" />

      {/* Transaction */}
      <div>
        <div className="flex items-center justify-between">
          <div className="text-xs font-medium text-muted-foreground">Transaction</div>
          <div className="text-sm font-semibold tabular-nums">{formatMoney(t.amount, t.currency)}</div>
        </div>

        <div className="mt-2 space-y-2 rounded-lg border p-3">
          <div className="flex items-center justify-between gap-3">
            <div className="min-w-0 font-mono text-xs text-muted-foreground truncate">
              {t.description ?? a.transaction_reference ?? `tx_id=${t.tx_id}`}
            </div>
            <div className="shrink-0 rounded-md border bg-muted/20 px-2 py-1 text-[11px] text-muted-foreground">
              internal_tx_id={t.id}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <KV label="Account" value={t.account_id} />
            <KV label="Direction / Status" value={`${t.direction} · ${t.status}`} />
          </div>

          <div className="grid grid-cols-2 gap-2">
            <KV label="tx_time" value={formatIso(t.tx_time)} />
            <KV label="booking_time" value={t.booking_time ? formatIso(t.booking_time) : "—"} />
          </div>

          <div className="grid grid-cols-3 gap-2">
            <KV label="Country" value={t.country_code ?? "—"} />
            <KV label="Category" value={t.merchant_category ?? "—"} />
            <KV label="Channel" value={t.channel ?? "—"} />
          </div>

          <div className="grid grid-cols-3 gap-2">
            <KV label="Customer" value={t.customer_id ?? "—"} />
            <KV label="Invoice" value={t.invoice_id ?? "—"} />
            <KV label="Vendor / Employee" value={a.vendor_code ?? a.employee_id ?? "—"} />
          </div>
        </div>
      </div>

      {/* Rule results */}
      <div className="mt-4">
        <div className="text-xs font-medium text-muted-foreground">Rule results</div>
        <div className="mt-2 rounded-md border p-3 text-xs">
          {data.rule_results?.length ? (
            <details>
              <summary className="cursor-pointer select-none text-xs font-medium">
                View raw rule_results ({data.rule_results.length})
              </summary>
              <pre className="mt-3 max-h-[260px] overflow-auto whitespace-pre-wrap break-words rounded-md bg-muted/20 p-3">
                {JSON.stringify(data.rule_results, null, 2)}
              </pre>
            </details>
          ) : (
            <div className="text-muted-foreground">
              No rule_results returned yet (fine for now — we’ll format once populated).
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export function AlertDetailPanel({
  alertId,
  mobile,
  onClose,
}: {
  alertId?: number
  mobile?: boolean
  onClose?: () => void
}) {
  if (!mobile) {
    if (!alertId) return null
    return <PanelBody alertId={alertId} />
  }

  const open = typeof alertId === "number" && Number.isFinite(alertId)

  return (
    <Sheet
      open={open}
      onOpenChange={(v) => {
        if (!v) onClose?.()
      }}
    >
      <SheetContent side="right" className="w-full sm:max-w-[520px] p-0">
        <SheetHeader className="px-4 py-3">
          <div className="flex items-center justify-between">
            <SheetTitle>Alert investigation</SheetTitle>
            <Button variant="outline" size="sm" onClick={() => onClose?.()}>
              Close
            </Button>
          </div>
        </SheetHeader>
        <Separator />
        {open ? <PanelBody alertId={alertId!} /> : null}
      </SheetContent>
    </Sheet>
  )
}
