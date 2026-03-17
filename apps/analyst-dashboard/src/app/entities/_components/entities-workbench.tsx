// src/app/entities/_components/entities-workbench.tsx
"use client"

import * as React from "react"
import { usePathname, useRouter, useSearchParams } from "next/navigation"
import { useQuery } from "@tanstack/react-query"

import { getEntities } from "@/lib/api/entities"
import type { EntityItem } from "@/lib/api/entities"
import { ApiError } from "@/lib/api/http"

import { EntitiesFilters } from "@/app/entities/_components/entities-filters"
import { EntitiesTable } from "@/app/entities/_components/entities-table"
import { EntityDetailPanel } from "@/app/entities/_components/entity-detail-panel"
import { EntitiesTableSkeleton } from "@/app/entities/_components/skeletons"
import { Separator } from "@/components/ui/separator"
import { Button } from "@/components/ui/button"

const DEFAULT_LIMIT = 25

function clampInt(n: number, min: number, max: number, fallback: number) {
  if (!Number.isFinite(n)) return fallback
  const v = Math.trunc(n)
  return Math.max(min, Math.min(max, v))
}

function useUrlState() {
  const sp = useSearchParams()
  const router = useRouter()
  const pathname = usePathname()

  const selected = sp.get("selected")
  const q = sp.get("q") ?? ""
  const type = (sp.get("type") || "ALL").toUpperCase()

  const minRisk = clampInt(Number(sp.get("min_risk") ?? "0"), 0, 100, 0)
  const offset = clampInt(Number(sp.get("offset") ?? "0"), 0, 1_000_000, 0)
  const limit = clampInt(Number(sp.get("limit") ?? String(DEFAULT_LIMIT)), 1, 250, DEFAULT_LIMIT)

  const setParams = React.useCallback(
    (next: Partial<Record<string, string | number | null | undefined>>) => {
      const nextSp = new URLSearchParams(sp.toString())
      for (const [k, v] of Object.entries(next)) {
        if (v === null || v === undefined || v === "") nextSp.delete(k)
        else nextSp.set(k, String(v))
      }

      const nextQs = nextSp.toString()
      const currQs = sp.toString()
      if (nextQs === currQs) return

      const url = nextQs ? `${pathname}?${nextQs}` : pathname
      router.replace(url, { scroll: false })
    },
    [sp, router, pathname]
  )

  return {
    selectedId: selected ? Number(selected) : null,
    q,
    type,
    minRisk,
    offset,
    limit,
    setParams,
  }
}

export function EntitiesWorkbench() {
  const { selectedId, q, type, minRisk, offset, limit, setParams } = useUrlState()

  const listQ = useQuery({
    queryKey: ["entities.list", { q, type, minRisk, limit, offset }],
    queryFn: () =>
      getEntities({
        q: q.trim() ? q.trim() : undefined,
        type: type !== "ALL" ? type : undefined,
        min_risk: minRisk > 0 ? minRisk : undefined,
        limit,
        offset,
      }),
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
    staleTime: 10_000,
  })

  const items = (listQ.data?.items ?? []) as EntityItem[]
  const count = listQ.data?.count

  const onSelect = React.useCallback((id: number) => setParams({ selected: id }), [setParams])
  const onClearSelection = React.useCallback(() => setParams({ selected: null }), [setParams])

  const errorHint = React.useMemo(() => {
    const err = listQ.error
    if (!err) return null
    if (err instanceof ApiError) return `API error ${err.status}: ${err.message}`
    if (err instanceof Error) return err.message
    return String(err)
  }, [listQ.error])

  return (
    <div className="h-full min-h-0">
      <div className="mx-auto h-full w-full max-w-[1600px] px-6 py-6 flex min-h-0 flex-col">
        {/* Header */}
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="text-sm text-muted-foreground">SafeFlow · Analyst</div>
            <h1 className="text-2xl font-semibold tracking-tight">Entities</h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Entity 360: vendors, employees, accounts — with risk context and linked activity.
            </p>
          </div>

          <div className="text-right text-xs text-muted-foreground">
            <div>API: {process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"}</div>
            <div>{listQ.isFetching ? "Refreshing…" : "Live"}</div>
          </div>
        </div>

        <Separator className="my-5" />

        <EntitiesFilters
          q={q}
          type={type}
          minRisk={minRisk}
          onQueryChange={(v) => setParams({ q: v, offset: 0, selected: null })}
          onTypeChange={(v) => setParams({ type: v, offset: 0, selected: null })}
          onMinRiskChange={(v) => setParams({ min_risk: v, offset: 0, selected: null })}
          onReset={() => setParams({ q: "", type: "ALL", min_risk: 0, offset: 0, selected: null })}
        />

        <div className="mt-4 grid flex-1 min-h-0 gap-4 lg:grid-cols-[minmax(0,1fr)_420px]">
          {/* LEFT */}
          <div className="rounded-xl border bg-card flex min-h-0 flex-col overflow-hidden">
            <div className="flex items-center justify-between px-4 py-3">
              <div className="text-sm font-medium">Entity Results</div>
              <div className="text-xs text-muted-foreground">
                Showing {items.length} {typeof count === "number" ? `of ${count}` : ""} · Offset {offset}
              </div>
            </div>
            <Separator />

            <div className="flex-1 min-h-0 overflow-auto">
              {listQ.isLoading ? (
                <EntitiesTableSkeleton />
              ) : listQ.isError ? (
                <div className="px-4 py-10 text-sm">
                  <div className="font-medium">Couldn’t load entities</div>
                  <div className="mt-1 text-muted-foreground">{errorHint ?? "Unknown error"}</div>
                  <div className="mt-4">
                    <Button variant="outline" size="sm" onClick={() => listQ.refetch()}>
                      Retry
                    </Button>
                  </div>
                </div>
              ) : items.length === 0 ? (
                <div className="px-4 py-10 text-sm">
                  <div className="font-medium">No entities match these filters</div>
                  <div className="mt-1 text-muted-foreground">Try a wider search or lower minimum risk.</div>
                </div>
              ) : (
                <EntitiesTable
                  rows={items}
                  selectedId={selectedId}
                  onSelect={onSelect}
                  offset={offset}
                  limit={limit}
                  onPageChange={(nextOffset) => setParams({ offset: nextOffset, selected: null })}
                  count={count}
                />
              )}
            </div>
          </div>

          {/* RIGHT (ONLY place details appear) */}
          <div className="hidden lg:flex min-h-0 flex-col rounded-xl border bg-card overflow-hidden">
            <div className="flex items-center justify-between px-4 py-3">
              <div className="text-sm font-medium">Entity 360</div>
              {selectedId ? (
                <Button variant="outline" size="sm" onClick={onClearSelection}>
                  Clear
                </Button>
              ) : null}
            </div>
            <Separator />

            <div className="flex-1 min-h-0 overflow-auto">
              {selectedId ? (
                <EntityDetailPanel entityId={selectedId} />
              ) : (
                <div className="px-4 py-10 text-sm text-muted-foreground">
                  Select an entity to view profile fields, risk summary, and linked activity.
                </div>
              )}
            </div>
          </div>

          {/* NOTE: NO mobile sheet rendered anywhere */}
        </div>
      </div>
    </div>
  )
}
