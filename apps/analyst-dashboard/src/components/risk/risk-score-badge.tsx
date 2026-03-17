// src/components/risk/risk-score-badge.tsx
import * as React from "react"

function clamp(n: number, a: number, b: number) {
  return Math.max(a, Math.min(b, n))
}

export function RiskScoreBadge({ score }: { score: number }) {
  const s = clamp(score ?? 0, 0, 999)
  const pct = (s / 999) * 100

  const tone =
    s >= 850 ? "border-destructive/40 bg-destructive/10" :
    s >= 650 ? "border-amber-500/40 bg-amber-500/10" :
    s >= 350 ? "border-sky-500/40 bg-sky-500/10" :
    "border-muted-foreground/20 bg-muted/40"

  return (
    <div className={`flex items-center gap-2 rounded-md border px-2 py-1 ${tone}`}>
      <div className="text-xs font-semibold tabular-nums">{s}</div>
      <div className="h-1.5 w-16 overflow-hidden rounded bg-muted">
        <div className="h-full bg-foreground/70" style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}
