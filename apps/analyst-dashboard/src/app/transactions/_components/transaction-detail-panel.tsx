"use client"

import * as React from "react"
import { useQuery } from "@tanstack/react-query"
import { getTransaction } from "@/lib/api/transactions"
import { formatIso, formatMoney } from "@/lib/format"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { DetailSkeleton } from "@/app/transactions/_components/skeletons"

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-4 text-xs">
      <div className="text-muted-foreground">{label}</div>
      <div className="font-medium text-right break-words">{value}</div>
    </div>
  )
}

function PanelBody({ txId }: { txId: number }) {
  const q = useQuery({
    queryKey: ["transactions.detail", txId],
    queryFn: () => getTransaction(txId),
    enabled: Number.isFinite(txId) && txId > 0,
    staleTime: 60_000,          // don't refetch for 60s
    gcTime: 5 * 60_000,         // keep in cache for 5 min
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
    retry: 1,
  })

  // ✅ Only show skeleton on the very first load (no data yet)
  // Don't show skeleton on background refetches — that causes the flash
  if (q.isLoading && !q.data) return <DetailSkeleton />

  if (q.isError && !q.data) {
    return (
      <div className="px-4 py-8 text-sm">
        <div className="font-medium">Couldn't load transaction detail</div>
        <div className="mt-1 text-muted-foreground">Try again, or verify the ID exists.</div>
        <button
          className="mt-4 rounded-md border px-3 py-2 text-xs hover:bg-muted"
          onClick={() => q.refetch()}
        >
          Retry
        </button>
      </div>
    )
  }

  const t = q.data
  if (!t) return null

  return (
    <div className="px-4 py-4">
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-xs text-muted-foreground">Transaction #{t.id}</div>
          <div className="mt-1 flex flex-wrap items-center gap-2">
            <Badge variant="secondary" className="text-[11px]">{t.direction}</Badge>
            <Badge variant="outline" className="text-[11px]">{t.status}</Badge>
            <div className="text-xs text-muted-foreground">
              {formatIso(t.timestamp ?? t.tx_time ?? "")}
            </div>
          </div>
        </div>

        <div className="text-right">
          <div className="text-sm font-semibold tabular-nums">
            {formatMoney(Number(t.amount), t.currency)}
          </div>
          <div className="text-xs text-muted-foreground">{t.currency}</div>
        </div>
      </div>

      <Separator className="my-4" />

      {/* Core fields */}
      <div className="space-y-2">
        <Row
          label="Reference"
          value={
            <span className="font-mono text-xs">
              {t.transaction_reference ?? t.tx_id ?? "—"}
            </span>
          }
        />
        <Row
          label="Account"
          value={<span className="font-mono text-xs">{t.account_id}</span>}
        />
        <Row
          label="TX ID"
          value={
            <span className="font-mono text-xs">
              {t.tx_id ?? t.transaction_reference ?? String(t.id)}
            </span>
          }
        />
        <Row label="Customer" value={t.customer_id ?? "—"} />
        <Row label="Channel" value={(t as any).channel ?? "—"} />
        <Row label="Country" value={(t as any).country_code ?? "—"} />
        <Row label="Category" value={(t as any).merchant_category ?? "—"} />
        <Row
          label="Booked"
          value={
            (t as any).booking_time
              ? formatIso((t as any).booking_time)
              : "—"
          }
        />
      </div>

      <Separator className="my-4" />

      <div className="text-xs font-medium text-muted-foreground">Description</div>
      <div className="mt-2 rounded-md border bg-muted/20 p-3 text-xs leading-relaxed">
        {(t as any).description ?? "—"}
      </div>

      {/* Raw JSON for debugging */}
      <Separator className="my-4" />
      <details className="rounded-md border bg-muted/20 p-3">
        <summary className="cursor-pointer text-xs font-medium text-muted-foreground select-none">
          Raw JSON
        </summary>
        <div className="mt-3 text-xs font-mono whitespace-pre-wrap break-words">
          {JSON.stringify(t, null, 2)}
        </div>
      </details>
    </div>
  )
}

export function TransactionDetailPanel({
  txId,
  mobile,
  onClose,
}: {
  txId?: number
  mobile?: boolean
  onClose?: () => void
}) {
  // Mobile sheet removed per earlier decision — only show in right panel
  if (mobile) return null

  if (!txId || !Number.isFinite(txId) || txId <= 0) return null

  return <PanelBody txId={txId} />
}
