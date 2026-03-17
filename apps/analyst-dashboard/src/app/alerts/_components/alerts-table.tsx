"use client"

import * as React from "react"
import type { AlertListItem } from "@/lib/api/alerts"
import { formatIsoAgo, formatIso } from "@/lib/format"
import { SeverityPill } from "@/components/risk/severity-pill"
import { RiskScoreBadge } from "@/components/risk/risk-score-badge"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"

type SortKey = "scored_at" | "risk_score_0_999"
type SortDir = "asc" | "desc"

function nextSort(currentKey: SortKey, currentDir: SortDir, key: SortKey): SortDir {
  if (currentKey !== key) return "desc"
  return currentDir === "desc" ? "asc" : "desc"
}

function sortRows(rows: AlertListItem[], key: SortKey, dir: SortDir) {
  const copy = [...rows]
  copy.sort((a, b) => {
    const av =
      key === "scored_at"
        ? new Date(a.scored_at).getTime()
        : Number(a.risk_score_0_999 ?? 0)
    const bv =
      key === "scored_at"
        ? new Date(b.scored_at).getTime()
        : Number(b.risk_score_0_999 ?? 0)

    const diff = av - bv
    return dir === "asc" ? diff : -diff
  })
  return copy
}

function SortIcon({ active, dir }: { active: boolean; dir: SortDir }) {
  return (
    <span className="ml-1 inline-flex select-none text-[10px] text-muted-foreground">
      {active ? (dir === "asc" ? "▲" : "▼") : "↕"}
    </span>
  )
}

export function AlertsTable({
  rows,
  selectedId,
  onSelect,
  offset,
  limit,
  onPageChange,
  count,
}: {
  rows: AlertListItem[]
  selectedId: number | null
  onSelect: (id: number) => void
  offset: number
  limit: number
  onPageChange: (nextOffset: number) => void
  count?: number
}) {
  const [sortKey, setSortKey] = React.useState<SortKey>("scored_at")
  const [sortDir, setSortDir] = React.useState<SortDir>("desc")

  const canPrev = offset > 0
  const canNext = typeof count === "number" ? offset + limit < count : rows.length === limit

  const sorted = React.useMemo(() => sortRows(rows, sortKey, sortDir), [rows, sortKey, sortDir])

  const rangeStart = count ? Math.min(offset + 1, count) : offset + 1
  const rangeEnd = count
    ? Math.min(offset + rows.length, count)
    : offset + rows.length

  function onHeaderSort(key: SortKey) {
    const nd = nextSort(sortKey, sortDir, key)
    if (sortKey !== key) setSortKey(key)
    setSortDir(nd)
  }

  return (
    <TooltipProvider>
      <div className="overflow-hidden">
        <div className="max-h-[620px] overflow-auto">
          <Table className="text-sm">
            <TableHeader className="sticky top-0 z-10 bg-background">
              <TableRow className="bg-muted/30">
                <TableHead className="w-[170px]">
                  <button
                    className="inline-flex items-center font-medium"
                    onClick={() => onHeaderSort("scored_at")}
                    type="button"
                  >
                    Time
                    <SortIcon active={sortKey === "scored_at"} dir={sortDir} />
                  </button>
                </TableHead>

                <TableHead className="w-[150px]">
                  <button
                    className="inline-flex items-center font-medium"
                    onClick={() => onHeaderSort("risk_score_0_999")}
                    type="button"
                  >
                    Risk
                    <SortIcon active={sortKey === "risk_score_0_999"} dir={sortDir} />
                  </button>
                </TableHead>

                <TableHead className="w-[120px]">Severity</TableHead>
                <TableHead className="min-w-[220px]">Transaction</TableHead>
                <TableHead className="min-w-[190px]">Account</TableHead>

                {/* These do not exist in list payload today — we keep them but make it clear */}
                <TableHead className="w-[110px] hidden xl:table-cell">
                  <Tooltip>
                    <TooltipTrigger className="text-left">Dir</TooltipTrigger>
                    <TooltipContent>Direction is available in the Investigation panel (detail endpoint).</TooltipContent>
                  </Tooltip>
                </TableHead>
                <TableHead className="w-[130px] hidden xl:table-cell">
                  <Tooltip>
                    <TooltipTrigger className="text-left">Status</TooltipTrigger>
                    <TooltipContent>Status is available in the Investigation panel (detail endpoint).</TooltipContent>
                  </Tooltip>
                </TableHead>

                <TableHead className="min-w-[160px] hidden 2xl:table-cell">Entity</TableHead>
                <TableHead className="min-w-[190px] hidden 2xl:table-cell">Signals</TableHead>
              </TableRow>
            </TableHeader>

            <TableBody>
              {sorted.map((r) => {
                const active = selectedId === r.id
                const entity = r.vendor_code ?? r.employee_id ?? "—"

                return (
                  <TableRow
                    key={r.id}
                    className={[
                      "cursor-pointer",
                      active ? "bg-muted/50" : "hover:bg-muted/25",
                    ].join(" ")}
                    onClick={() => onSelect(r.id)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault()
                        onSelect(r.id)
                      }
                    }}
                    tabIndex={0}
                    aria-selected={active}
                  >
                    <TableCell className="text-xs">
                      <div className="flex items-start gap-2">
                        <div className={active ? "mt-1 h-2 w-2 rounded-full bg-foreground" : "mt-1 h-2 w-2 rounded-full bg-muted-foreground/40"} />
                        <Tooltip>
                          <TooltipTrigger className="text-left">
                            <div className="font-medium">{formatIsoAgo(r.scored_at)}</div>
                            <div className="text-muted-foreground">scored</div>
                          </TooltipTrigger>
                          <TooltipContent>
                            <div className="text-xs">scored_at: {formatIso(r.scored_at)}</div>
                            <div className="text-xs">created_at: {formatIso(r.created_at)}</div>
                          </TooltipContent>
                        </Tooltip>
                      </div>
                    </TableCell>

                    <TableCell>
                      <div className="flex items-center gap-2">
                        <RiskScoreBadge score={r.risk_score_0_999} />
                        <div className="hidden md:block text-xs text-muted-foreground tabular-nums">
                          #{r.id}
                        </div>
                      </div>
                    </TableCell>

                    <TableCell>
                      <SeverityPill severity={r.severity} />
                    </TableCell>

                    <TableCell>
                      <div className="font-mono text-xs">{r.transaction_reference}</div>
                      <div className="text-xs text-muted-foreground">
                        tx_internal={r.transaction_id}
                      </div>
                    </TableCell>

                    <TableCell>
                      <div className="text-sm font-medium">{r.account_id ?? "—"}</div>
                      <div className="text-xs text-muted-foreground">
                        vendor={r.vendor_code ?? "—"} · emp={r.employee_id ?? "—"}
                      </div>
                    </TableCell>

                    <TableCell className="hidden xl:table-cell text-xs text-muted-foreground">—</TableCell>
                    <TableCell className="hidden xl:table-cell text-xs text-muted-foreground">—</TableCell>

                    <TableCell className="hidden 2xl:table-cell text-xs">{entity}</TableCell>

                    <TableCell className="hidden 2xl:table-cell text-xs">
                      <Tooltip>
                        <TooltipTrigger className="text-left">
                          <div className="flex flex-wrap gap-2">
                            <span className="rounded-md border bg-muted/20 px-2 py-1 tabular-nums">
                              rule {r.rule_score ?? "—"}
                            </span>
                            <span className="rounded-md border bg-muted/20 px-2 py-1 tabular-nums">
                              ml {r.ml_score ?? "—"}
                            </span>
                            <span className="rounded-md border bg-muted/20 px-2 py-1 tabular-nums">
                              graph {r.graph_score ?? "—"}
                            </span>
                          </div>
                        </TooltipTrigger>
                        <TooltipContent>
                          Signal breakdown from the alert list payload (not re-fetched per row).
                        </TooltipContent>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                )
              })}
            </TableBody>
          </Table>
        </div>

        <Separator />

        <div className="flex items-center justify-between px-4 py-3">
          <div className="text-xs text-muted-foreground">
            Showing{" "}
            <span className="font-mono">{rangeStart}</span>–<span className="font-mono">{rangeEnd}</span>
            {typeof count === "number" ? (
              <>
                {" "}
                of <span className="font-mono">{count}</span>
              </>
            ) : null}
            {" "}
            · offset <span className="font-mono">{offset}</span> · limit <span className="font-mono">{limit}</span>
            {" "}
            · sort <span className="font-mono">{sortKey}</span> <span className="font-mono">{sortDir}</span>
          </div>

          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={!canPrev}
              onClick={() => onPageChange(Math.max(0, offset - limit))}
            >
              Prev
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={!canNext}
              onClick={() => onPageChange(offset + limit)}
            >
              Next
            </Button>
          </div>
        </div>
      </div>
    </TooltipProvider>
  )
}
