// src/app/entities/_components/entities-filters.tsx
"use client"

import * as React from "react"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Slider } from "@/components/ui/slider"
import { Button } from "@/components/ui/button"

function clampInt(n: number, min: number, max: number, fallback: number) {
  if (!Number.isFinite(n)) return fallback
  const v = Math.trunc(n)
  return Math.max(min, Math.min(max, v))
}

export function EntitiesFilters({
  q,
  type,
  minRisk,
  onQueryChange,
  onTypeChange,
  onMinRiskChange,
  onReset,
}: {
  q: string
  type: string
  minRisk: number
  onQueryChange: (v: string) => void
  onTypeChange: (v: string) => void
  onMinRiskChange: (v: number) => void
  onReset: () => void
}) {
  const safeMinRisk = clampInt(minRisk ?? 0, 0, 100, 0)

  const [localMin, setLocalMin] = React.useState<string>(String(safeMinRisk))
  const fromSliderRef = React.useRef(false)

  // keep input in sync when parent changes (e.g., reset / URL change)
  React.useEffect(() => {
    setLocalMin(String(safeMinRisk))
  }, [safeMinRisk])

  // Debounced text-input -> parent update (ONLY if value actually changes)
  React.useEffect(() => {
    // if it came from slider, we already pushed the change immediately
    if (fromSliderRef.current) {
      fromSliderRef.current = false
      return
    }

    const t = setTimeout(() => {
      const n = clampInt(Number(localMin), 0, 100, safeMinRisk)

      // ✅ Critical: don't fire if no real change (prevents clearing selected)
      if (n === safeMinRisk) return

      onMinRiskChange(n)
    }, 250)

    return () => clearTimeout(t)
  }, [localMin, safeMinRisk, onMinRiskChange])

  const sliderValue = [clampInt(Number(localMin), 0, 100, safeMinRisk)]

  return (
    <div className="flex flex-col gap-3 rounded-xl border bg-card p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-3">
          <div className="text-sm font-medium">Filters</div>
          <Badge variant="secondary" className="text-[11px]">
            v1 Analyst
          </Badge>
        </div>

        <Button variant="ghost" size="sm" onClick={onReset}>
          Reset
        </Button>
      </div>

      <div className="grid gap-3 md:grid-cols-3">
        <div className="md:col-span-1">
          <div className="mb-1 text-xs text-muted-foreground">Search</div>
          <Input value={q} onChange={(e) => onQueryChange(e.target.value)} placeholder="Name / ID / keyword" />
        </div>

        <div className="md:col-span-1">
          <div className="mb-1 text-xs text-muted-foreground">Type</div>
          <Select value={type} onValueChange={onTypeChange}>
            <SelectTrigger>
              <SelectValue placeholder="Entity type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">All types</SelectItem>
              <SelectItem value="PERSON">PERSON</SelectItem>
              <SelectItem value="ACCOUNT">ACCOUNT</SelectItem>
              <SelectItem value="MERCHANT">MERCHANT</SelectItem>
              <SelectItem value="VENDOR">VENDOR</SelectItem>
              <SelectItem value="EMPLOYEE">EMPLOYEE</SelectItem>
              <SelectItem value="COMPANY">COMPANY</SelectItem>
              <SelectItem value="UNKNOWN">UNKNOWN</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="md:col-span-1">
          <div className="mb-1 text-xs text-muted-foreground">Min risk</div>
          <div className="flex items-center gap-2">
            <Input
              className="w-[120px]"
              value={localMin}
              onChange={(e) => setLocalMin(e.target.value)}
              inputMode="numeric"
              placeholder="0"
            />

            <div className="flex-1">
              <Slider
                value={sliderValue}
                min={0}
                max={100}
                step={1}
                onValueChange={(v) => {
                  const n = clampInt(v?.[0] ?? 0, 0, 100, safeMinRisk)
                  fromSliderRef.current = true
                  setLocalMin(String(n))

                  // ✅ only push if changed
                  if (n !== safeMinRisk) onMinRiskChange(n)
                }}
              />
              <div className="mt-1 flex justify-between text-[11px] text-muted-foreground">
                <span>0</span>
                <span>100</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
