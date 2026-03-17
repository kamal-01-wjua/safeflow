"use client"

import * as React from "react"
import type { Severity } from "@/lib/api/alerts"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Slider } from "@/components/ui/slider"
import { Button } from "@/components/ui/button"

function clamp(n: number, a: number, b: number) {
  return Math.max(a, Math.min(b, n))
}

export function AlertsFilters({
  severity,
  minRisk,
  onSeverityChange,
  onMinRiskChange,
}: {
  severity: Severity | "ALL"
  minRisk: number
  onSeverityChange: (v: Severity | "ALL") => void
  onMinRiskChange: (v: number) => void
}) {
  // local input string so user can type freely
  const [localMin, setLocalMin] = React.useState<string>(String(minRisk ?? 0))

  // when URL/state minRisk changes from outside, sync the input
  React.useEffect(() => {
    setLocalMin(String(minRisk ?? 0))
  }, [minRisk])

  // debounce typing => only commit if value actually changed
  React.useEffect(() => {
    const t = setTimeout(() => {
      const n = Number(localMin)
      if (!Number.isFinite(n)) return

      const clamped = clamp(n, 0, 999)
      if (clamped !== (minRisk ?? 0)) onMinRiskChange(clamped)
    }, 250)

    return () => clearTimeout(t)
  }, [localMin, minRisk, onMinRiskChange])

  const sliderValue = [clamp(Number(localMin) || 0, 0, 999)]

  return (
    <div className="flex flex-col gap-3 rounded-xl border bg-card p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-3">
          <div className="text-sm font-medium">Filters</div>
          <Badge variant="secondary" className="text-[11px]">
            v1 Analyst
          </Badge>
        </div>

        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <div className="w-full sm:w-[180px]">
            <Select value={severity} onValueChange={(v) => onSeverityChange(v as any)}>
              <SelectTrigger>
                <SelectValue placeholder="Severity" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ALL">All severities</SelectItem>
                <SelectItem value="CRITICAL">CRITICAL</SelectItem>
                <SelectItem value="HIGH">HIGH</SelectItem>
                <SelectItem value="MEDIUM">MEDIUM</SelectItem>
                <SelectItem value="LOW">LOW</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center gap-2">
            <div className="w-full sm:w-[140px]">
              <Input
                value={localMin}
                onChange={(e) => setLocalMin(e.target.value)}
                inputMode="numeric"
                placeholder="Min risk"
              />
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setLocalMin("0")
                onMinRiskChange(0)
              }}
            >
              Reset
            </Button>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="w-[70px] text-xs text-muted-foreground">Min risk</div>

        <div className="flex-1">
          <Slider
            value={sliderValue}
            min={0}
            max={999}
            step={1}
            onValueChange={(v) => {
              const n = clamp(v?.[0] ?? 0, 0, 999)
              setLocalMin(String(n))

              // IMPORTANT: prevent spam—only commit if it actually changed
              if (n !== (minRisk ?? 0)) onMinRiskChange(n)
            }}
          />
          <div className="mt-1 flex justify-between text-[11px] text-muted-foreground">
            <span>0</span>
            <span>999</span>
          </div>
        </div>
      </div>
    </div>
  )
}
