// src/components/shell/page-header.tsx
import * as React from "react"
import { Separator } from "@/components/ui/separator"

export function PageHeader({
  eyebrow,
  title,
  subtitle,
  right,
}: {
  eyebrow?: string
  title: string
  subtitle?: string
  right?: React.ReactNode
}) {
  return (
    <div>
      <div className="flex items-start justify-between gap-4">
        <div>
          {eyebrow ? <div className="text-sm text-muted-foreground">{eyebrow}</div> : null}
          <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
          {subtitle ? <p className="mt-1 text-sm text-muted-foreground">{subtitle}</p> : null}
        </div>
        {right ? <div className="shrink-0">{right}</div> : null}
      </div>

      <Separator className="my-5" />
    </div>
  )
}
