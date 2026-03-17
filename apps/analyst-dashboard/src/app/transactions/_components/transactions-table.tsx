"use client"

import * as React from "react"
import { formatIsoAgo, formatIso, formatMoney } from "@/lib/format"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"

/**
 * Local type so you don't depend on a missing exported type.
 * This matches exactly what this table uses.
 */
type TxRow = {
  id: number
  timestamp?: string | null
  tx_time?: string | null
  created_at?: string | null
  currency?: string | null
  amount?: number | string | null
  direction?: string | null
  status?: string | null
  account_id?: string | null
  channel?: string | null
  country_code?: string | null
  transaction_reference?: string | null
  tx_id?: string | null
}

export function TransactionsTable({
  rows,
  selectedId,
  onSelect,
  offset,
  limit,
  onPageChange,
  count,
}: {
  rows: TxRow[]
  selectedId: number | null
  onSelect: (id: number) => void
  offset: number
  limit: number
  onPageChange: (nextOffset: number) => void
  count?: number
}) {
  const canPrev = offset > 0
  const canNext = typeof count === "number" ? offset + limit < count : rows.length === limit

  return (
    <TooltipProvider>
      <div className="overflow-hidden">
        <div className="overflow-auto">
          <Table className="text-sm">
            <TableHeader>
              <TableRow className="bg-muted/30">
                <TableHead className="w-[150px]">Time</TableHead>
                <TableHead className="min-w-[220px]">Reference</TableHead>
                <TableHead className="w-[170px] text-right">Amount</TableHead>
                <TableHead className="w-[110px]">Dir</TableHead>
                <TableHead className="w-[130px]">Status</TableHead>
                <TableHead className="min-w-[140px]">Account</TableHead>
                <TableHead className="min-w-[120px] hidden xl:table-cell">Channel</TableHead>
                <TableHead className="min-w-[90px] hidden xl:table-cell">Country</TableHead>
              </TableRow>
            </TableHeader>

            <TableBody>
              {rows.map((r) => {
                const active = selectedId === r.id
                const ts = r.timestamp || r.tx_time || r.created_at || ""
                const currency = r.currency || "MYR"
                const amount = typeof r.amount === "number" ? r.amount : Number(r.amount || 0)

                return (
                  <TableRow
                    key={r.id}
                    role="button"
                    tabIndex={0}
                    aria-selected={active}
                    className={[
                      "cursor-pointer",
                      active ? "bg-muted/40" : "hover:bg-muted/20",
                      "focus:outline-none focus:ring-1 focus:ring-inset focus:ring-muted-foreground/30",
                    ].join(" ")}
                    onClick={() => onSelect(r.id)} // ✅ FIX: use r.id (numeric DB id)
                    onKeyDown={(ev) => {
                      if (ev.key === "Enter" || ev.key === " ") {
                        ev.preventDefault()
                        onSelect(r.id)
                      }
                    }}
                  >
                    <TableCell className="text-xs">
                      <Tooltip>
                        <TooltipTrigger className="text-left">
                          <div className="font-medium">{ts ? formatIsoAgo(ts) : "—"}</div>
                          <div className="text-muted-foreground">timestamp</div>
                        </TooltipTrigger>
                        <TooltipContent>
                          <div className="text-xs">timestamp: {ts ? formatIso(ts) : "—"}</div>
                          <div className="text-xs">created_at: {r.created_at ? formatIso(r.created_at) : "—"}</div>
                        </TooltipContent>
                      </Tooltip>
                    </TableCell>

                    <TableCell className="font-mono text-xs">
                      {r.transaction_reference ?? r.tx_id ?? `TX-${r.id}`}
                    </TableCell>

                    <TableCell className="text-right font-medium tabular-nums">
                      {formatMoney(amount, currency)}
                    </TableCell>

                    <TableCell className="text-xs">{r.direction ?? "—"}</TableCell>
                    <TableCell className="text-xs">{r.status ?? "—"}</TableCell>

                    <TableCell className="text-xs">{r.account_id ?? "—"}</TableCell>

                    <TableCell className="hidden xl:table-cell text-xs">{r.channel ?? "—"}</TableCell>
                    <TableCell className="hidden xl:table-cell text-xs">{r.country_code ?? "—"}</TableCell>
                  </TableRow>
                )
              })}
            </TableBody>
          </Table>
        </div>

        <div className="flex items-center justify-between px-4 py-3">
          <div className="text-xs text-muted-foreground">
            Page offset: <span className="font-mono">{offset}</span> · limit: <span className="font-mono">{limit}</span>
          </div>

          <div className="flex gap-2">
            <button
              className="rounded-md border px-3 py-1.5 text-xs hover:bg-muted disabled:opacity-50"
              disabled={!canPrev}
              onClick={() => onPageChange(Math.max(0, offset - limit))}
            >
              Prev
            </button>
            <button
              className="rounded-md border px-3 py-1.5 text-xs hover:bg-muted disabled:opacity-50"
              disabled={!canNext}
              onClick={() => onPageChange(offset + limit)}
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </TooltipProvider>
  )
}
