// src/app/page.tsx
import Link from "next/link"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

export default function HomePage() {
  return (
    <div className="mx-auto w-full max-w-[1200px] px-6 py-10">
      <div className="text-sm text-muted-foreground">SafeFlow · Analyst</div>
      <h1 className="mt-2 text-3xl font-semibold tracking-tight">Risk Workbench</h1>
      <p className="mt-2 text-muted-foreground">
        Triage alerts, investigate context, and build auditable cases — powered by explainable risk signals.
      </p>

      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Card className="rounded-xl">
          <CardHeader>
            <CardTitle className="text-base">Alerts</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="text-sm text-muted-foreground">
              KPI overview → filter & triage → investigation panel with rule + ML + graph context.
            </div>
            <Button asChild>
              <Link href="/alerts">Open Alerts</Link>
            </Button>
          </CardContent>
        </Card>

        <Card className="rounded-xl">
          <CardHeader>
            <CardTitle className="text-base">Transactions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="text-sm text-muted-foreground">
              Dense table + filters. Drill into event context and linked alerts.
            </div>
            <Button asChild variant="outline">
              <Link href="/transactions">Open Transactions</Link>
            </Button>
          </CardContent>
        </Card>

        <Card className="rounded-xl">
          <CardHeader>
            <CardTitle className="text-base">Cases</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="text-sm text-muted-foreground">
              Investigation tracking, notes, evidence, timeline, and audit trail.
            </div>
            <Button asChild variant="outline">
              <Link href="/cases">Open Cases</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
