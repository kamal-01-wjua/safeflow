// src/components/risk/severity-pill.tsx
import * as React from "react"
import { Badge } from "@/components/ui/badge"
import type { Severity } from "@/lib/api/alerts"

function normalize(s: string) {
  return s?.toUpperCase?.() ?? String(s)
}

export function SeverityPill({ severity }: { severity: Severity }) {
  const s = normalize(severity)

  const variant =
    s === "CRITICAL"
      ? "destructive"
      : s === "HIGH"
      ? "default"
      : s === "MEDIUM"
      ? "secondary"
      : "outline"

  return (
    <Badge variant={variant} className="h-6 px-2 text-[11px] tracking-wide">
      {s}
    </Badge>
  )
}
