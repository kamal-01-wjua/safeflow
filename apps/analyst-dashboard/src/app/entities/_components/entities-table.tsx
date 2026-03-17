// src/app/entities/_components/entities-table.tsx
"use client"

import * as React from "react"
import type { EntityItem } from "@/lib/api/entities"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { formatIsoAgo } from "@/lib/format"

function clamp(n: number, min: number, max: number) {
  return Math.max(min, Math.min(max, n))
}

function riskTone0to100(risk: number) {
  if (risk >= 80) return "destructive"
  if (risk >= 60) return "default"
  if (risk >= 30) return "secondary"
  return "outline"
}

function toSafeId(v: unknown): number | null {
  const n = typeof v === "number" ? v : Number(v)
  return Number.isFinite(n) ? n : null
}

export function EntitiesTable({
  rows,
  selectedId,
  onSelect,
  offset,
  limit,
  onPageChange,
  count,
}: {
  rows: EntityItem[]
  selectedId: number | null
  onSelect: (id: number) => void
  offset: number
  limit: number
  onPageChange: (nextOffset: number) => void
  count?: number
}) {
  const canPrev = offset > 0
  const canNext = typeof count === "number" ? offset + limit < count : rows.length === limit

  const start = rows.length > 0 ? offset + 1 : 0
  const end = rows.length > 0 ? offset + rows.length : 0

  return (
    <div className="w-full">
      <div className="w-full overflow-x-auto">
        <div className="min-w-[900px]">
          <table className="w-full text-sm">
            <thead className="sticky top-0 z-10 bg-card">
              <tr className="border-b text-xs text-muted-foreground">
                <th className="px-4 py-3 text-left font-medium">Name</th>
                <th className="px-4 py-3 text-left font-medium">Type</th>
                <th className="px-4 py-3 text-left font-medium">Risk</th>
                <th className="px-4 py-3 text-left font-medium">Country</th>
                <th className="px-4 py-3 text-left font-medium">Updated</th>
                <th className="px-4 py-3 text-left font-medium">ID</th>
              </tr>
            </thead>

            <tbody>
              {rows.map((e) => {
                const id = toSafeId(e.id)
                const isActive = id !== null && selectedId === id

                const name = String(e.name ?? e.entity_id ?? "Unknown")
                const type = String(e.type ?? "UNKNOWN").toUpperCase()

                const riskRaw =
                  typeof e.risk_score === "number" ? e.risk_score : Number(e.risk_score ?? 0)
                const risk = Number.isFinite(riskRaw) ? clamp(Math.round(riskRaw), 0, 100) : 0

                const country = String(e.country_code ?? "—").toUpperCase()
                const updated = typeof e.updated_at === "string" ? formatIsoAgo(e.updated_at) : "—"

                return (
                  <tr
                    key={id ?? `${name}-${type}`}
                    role="button"
                    tabIndex={0}
                    aria-selected={isActive}
                    className={[
                      "border-b cursor-pointer hover:bg-muted/50 focus:outline-none",
                      isActive ? "bg-muted/60 ring-1 ring-inset ring-muted-foreground/20" : "",
                      id === null ? "opacity-60 cursor-not-allowed" : "",
                    ].join(" ")}
                    onClick={() => {
                      if (id === null) return
                      onSelect(id)
                    }}
                    onKeyDown={(ev) => {
                      if (id === null) return
                      if (ev.key === "Enter" || ev.key === " ") {
                        ev.preventDefault()
                        onSelect(id)
                      }
                    }}
                  >
                    <td className="px-4 py-3 font-medium">{name}</td>

                    <td className="px-4 py-3">
                      <Badge variant="secondary" className="text-[11px]">
                        {type}
                      </Badge>
                    </td>

                    <td className="px-4 py-3">
                      <Badge variant={riskTone0to100(risk) as any} className="text-[11px]">
                        {risk}
                      </Badge>
                    </td>

                    <td className="px-4 py-3">{country}</td>
                    <td className="px-4 py-3 text-muted-foreground">{updated}</td>
                    <td className="px-4 py-3 text-muted-foreground">{id ?? "—"}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>

          <div className="flex items-center justify-between px-4 py-3">
            <div className="text-xs text-muted-foreground">
              {typeof count === "number" ? `Showing ${start}–${end} of ${count}` : `Offset ${offset} · Limit ${limit}`}
            </div>

            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => onPageChange(Math.max(0, offset - limit))}
                disabled={!canPrev}
              >
                Prev
              </Button>

              <Button
                variant="outline"
                size="sm"
                onClick={() => onPageChange(offset + limit)}
                disabled={!canNext}
              >
                Next
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
