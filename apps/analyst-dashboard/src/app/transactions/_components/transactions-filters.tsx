// src/app/transactions/_components/transactions-filters.tsx
"use client"

import * as React from "react"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"

export function TransactionsFilters({
  accountId,
  customerId,
  onAccountIdChange,
  onCustomerIdChange,
  onReset,
}: {
  accountId: string
  customerId: string
  onAccountIdChange: (v: string) => void
  onCustomerIdChange: (v: string) => void
  onReset: () => void
}) {
  const [a, setA] = React.useState(accountId ?? "")
  const [c, setC] = React.useState(customerId ?? "")

  React.useEffect(() => setA(accountId ?? ""), [accountId])
  React.useEffect(() => setC(customerId ?? ""), [customerId])

  // debounce typing
  React.useEffect(() => {
    const t = setTimeout(() => onAccountIdChange(a.trim()), 250)
    return () => clearTimeout(t)
  }, [a, onAccountIdChange])

  React.useEffect(() => {
    const t = setTimeout(() => onCustomerIdChange(c.trim()), 250)
    return () => clearTimeout(t)
  }, [c, onCustomerIdChange])

  return (
    <div className="flex flex-col gap-3 rounded-xl border bg-card p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-3">
          <div className="text-sm font-medium">Filters</div>
          <Badge variant="secondary" className="text-[11px]">v1 Analyst</Badge>
        </div>

        <Button variant="ghost" size="sm" onClick={onReset}>
          Reset
        </Button>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <div className="space-y-1">
          <div className="text-xs text-muted-foreground">Account ID</div>
          <Input value={a} onChange={(e) => setA(e.target.value)} placeholder="e.g. ACC-001" />
        </div>

        <div className="space-y-1">
          <div className="text-xs text-muted-foreground">Customer ID</div>
          <Input value={c} onChange={(e) => setC(e.target.value)} placeholder="optional" />
        </div>
      </div>
    </div>
  )
}
