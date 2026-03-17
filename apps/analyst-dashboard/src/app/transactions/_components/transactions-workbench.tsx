"use client"

import * as React from "react"
import { usePathname, useRouter, useSearchParams } from "next/navigation"
import { useQuery } from "@tanstack/react-query"

import { getTransactions } from "@/lib/api/transactions"
import { TransactionsFilters } from "@/app/transactions/_components/transactions-filters"
import { TransactionsTable } from "@/app/transactions/_components/transactions-table"
import { TransactionDetailPanel } from "@/app/transactions/_components/transaction-detail-panel"
import { TransactionsTableSkeleton } from "@/app/transactions/_components/skeletons"
import { Separator } from "@/components/ui/separator"

const DEFAULT_LIMIT = 25
const SELECTION_KEY = "safeflow.tx.selected"

function clampInt(n: number, min: number, max: number, fallback: number) {
  if (!Number.isFinite(n)) return fallback
  const v = Math.trunc(n)
  return Math.max(min, Math.min(max, v))
}

function useUrlState() {
  const sp = useSearchParams()
  const router = useRouter()
  const pathname = usePathname()

  const account_id = sp.get("account_id") ?? ""
  const customer_id = sp.get("customer_id") ?? ""
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
      router.replace(nextQs ? `${pathname}?${nextQs}` : pathname, { scroll: false })
    },
    [sp, router, pathname]
  )

  return { account_id, customer_id, offset, limit, setParams }
}

// ---------------------------------------------------------------------------
// Persist selectedId in sessionStorage so Next.js App Router remounts
// don't wipe the selection. sessionStorage is cleared when the tab closes.
// ---------------------------------------------------------------------------
function usePersistedSelection() {
  const [selectedId, _setSelectedId] = React.useState<number | null>(() => {
    if (typeof window === "undefined") return null
    try {
      const stored = sessionStorage.getItem(SELECTION_KEY)
      return stored ? Number(stored) : null
    } catch {
      return null
    }
  })

  const setSelectedId = React.useCallback((id: number | null) => {
    _setSelectedId(id)
    try {
      if (id === null) {
        sessionStorage.removeItem(SELECTION_KEY)
      } else {
        sessionStorage.setItem(SELECTION_KEY, String(id))
      }
    } catch {
      // sessionStorage not available — ignore
    }
  }, [])

  return [selectedId, setSelectedId] as const
}

export function TransactionsWorkbench() {
  const { account_id, customer_id, offset, limit, setParams } = useUrlState()
  const [selectedId, setSelectedId] = usePersistedSelection()

  const listQ = useQuery({
    queryKey: ["transactions.list", { account_id, customer_id, limit, offset }],
    queryFn: () =>
      getTransactions({
        account_id: account_id.trim() ? account_id.trim() : undefined,
        customer_id: customer_id.trim() ? customer_id.trim() : undefined,
        limit,
        offset,
      }),
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
    staleTime: 15_000,
  })

  const items = listQ.data?.items ?? []
  const count = listQ.data?.count

  const onSelect = React.useCallback((id: number) => setSelectedId(id), [setSelectedId])
  const onClearSelection = React.useCallback(() => setSelectedId(null), [setSelectedId])

  return (
    <div className="h-full min-h-0">
      <div className="mx-auto h-full w-full max-w-[1600px] px-6 py-6 flex min-h-0 flex-col">
        {/* Header */}
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="text-sm text-muted-foreground">SafeFlow · Analyst</div>
            <h1 className="text-2xl font-semibold tracking-tight">Transactions</h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Explore events, filter anomalies, and pivot into investigations.
            </p>
          </div>
          <div className="text-right text-xs text-muted-foreground">
            <div>Local API: {process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"}</div>
            <div>{listQ.isFetching ? "Refreshing…" : "Live"}</div>
          </div>
        </div>

        <Separator className="my-5" />

        <TransactionsFilters
          accountId={account_id}
          customerId={customer_id}
          onAccountIdChange={(v) => {
            setSelectedId(null)
            setParams({ account_id: v, offset: 0 })
          }}
          onCustomerIdChange={(v) => {
            setSelectedId(null)
            setParams({ customer_id: v, offset: 0 })
          }}
          onReset={() => {
            setSelectedId(null)
            setParams({ account_id: "", customer_id: "", offset: 0 })
          }}
        />

        <div className="mt-4 grid flex-1 min-h-0 gap-4 lg:grid-cols-[minmax(0,1fr)_420px]">
          {/* LEFT */}
          <div className="rounded-xl border bg-card flex min-h-0 flex-col overflow-hidden">
            <div className="flex items-center justify-between px-4 py-3">
              <div className="text-sm font-medium">Transaction Stream</div>
              <div className="text-xs text-muted-foreground">
                Showing {items.length} {typeof count === "number" ? `of ${count}` : ""} · Offset {offset}
              </div>
            </div>
            <Separator />

            <div className="flex-1 min-h-0 overflow-auto">
              {listQ.isLoading ? (
                <TransactionsTableSkeleton />
              ) : listQ.isError ? (
                <div className="px-4 py-10 text-sm">
                  <div className="font-medium">Couldn't load transactions</div>
                  <div className="mt-1 text-muted-foreground">
                    Make sure the API is running on <span className="font-mono">localhost:8000</span>.
                  </div>
                  <button
                    className="mt-4 rounded-md border px-3 py-2 text-xs hover:bg-muted"
                    onClick={() => listQ.refetch()}
                  >
                    Retry
                  </button>
                </div>
              ) : items.length === 0 ? (
                <div className="px-4 py-10 text-sm">
                  <div className="font-medium">No transactions match these filters</div>
                  <div className="mt-1 text-muted-foreground">
                    Clear filters or try a different account/customer.
                  </div>
                </div>
              ) : (
                <TransactionsTable
                  rows={items as any}
                  selectedId={selectedId}
                  onSelect={onSelect}
                  offset={offset}
                  limit={limit}
                  onPageChange={(nextOffset) => setParams({ offset: nextOffset })}
                  count={count}
                />
              )}
            </div>
          </div>

          {/* RIGHT — detail panel */}
          <div className="hidden lg:flex min-h-0 flex-col rounded-xl border bg-card overflow-hidden">
            <div className="flex items-center justify-between px-4 py-3">
              <div className="text-sm font-medium">Investigation</div>
              {selectedId ? (
                <button
                  className="rounded-md border px-2 py-1 text-xs hover:bg-muted"
                  onClick={onClearSelection}
                >
                  Clear
                </button>
              ) : null}
            </div>
            <Separator />

            <div className="flex-1 min-h-0 overflow-auto">
              {selectedId ? (
                <TransactionDetailPanel txId={selectedId} />
              ) : (
                <div className="px-4 py-10 text-sm text-muted-foreground">
                  Select a transaction to inspect details and raw fields.
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
