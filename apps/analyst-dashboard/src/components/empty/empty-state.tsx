// src/components/empty/empty-state.tsx
import * as React from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export function EmptyState({
  title,
  description,
  children,
}: {
  title: string
  description?: string
  children?: React.ReactNode
}) {
  return (
    <Card className="rounded-xl">
      <CardHeader className="pb-2">
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {description ? <div className="text-sm text-muted-foreground">{description}</div> : null}
        {children ? <div className="pt-1">{children}</div> : null}
      </CardContent>
    </Card>
  )
}
