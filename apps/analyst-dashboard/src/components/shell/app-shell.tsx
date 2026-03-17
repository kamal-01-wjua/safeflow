// src/components/shell/app-shell.tsx
"use client"

import * as React from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { useQuery } from "@tanstack/react-query"
import { fetchJson } from "@/lib/api/http"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet"

type NavItem = {
  title: string
  href: string
  badge?: string
}

const NAV: NavItem[] = [
  { title: "Alerts", href: "/alerts", badge: "Live" },
  { title: "Transactions", href: "/transactions" },
  { title: "Entities", href: "/entities" },
  { title: "Cases", href: "/cases" },
  { title: "Models", href: "/models" },
  { title: "Settings", href: "/settings" },
]

function NavLink({ item }: { item: NavItem }) {
  const pathname = usePathname()
  const active = pathname === item.href || pathname?.startsWith(item.href + "/")

  return (
    <Link
      href={item.href}
      className={cn(
        "group flex items-center justify-between rounded-lg px-3 py-2 text-sm transition-colors",
        active
          ? "bg-muted text-foreground"
          : "text-muted-foreground hover:bg-muted hover:text-foreground"
      )}
    >
      <span className="flex items-center gap-2">
        <span
          className={cn(
            "h-2 w-2 rounded-full",
            active
              ? "bg-foreground"
              : "bg-muted-foreground/40 group-hover:bg-foreground/70"
          )}
        />
        {item.title}
      </span>
      {item.badge ? (
        <span className="rounded-full border px-2 py-0.5 text-[11px] text-muted-foreground">
          {item.badge}
        </span>
      ) : null}
    </Link>
  )
}

function Sidebar() {
  return (
    <div className="flex h-full flex-col">
      <div className="px-4 py-4">
        <div className="text-xs text-muted-foreground">SafeFlow · Analyst</div>
        <div className="mt-1 flex items-center justify-between">
          <div className="text-sm font-semibold tracking-tight">Risk Workbench</div>
          <span className="rounded-md border px-2 py-0.5 text-[11px] text-muted-foreground">
            v1
          </span>
        </div>
      </div>

      <Separator />

      <div className="flex-1 space-y-1 px-3 py-3">
        {NAV.map((item) => (
          <NavLink key={item.href} item={item} />
        ))}
      </div>

      <Separator />

      <div className="px-4 py-4">
        <div className="text-xs text-muted-foreground">Environment</div>
        <div className="mt-1 text-xs">
          <span className="rounded-md border px-2 py-1 text-muted-foreground">Local Dev</span>
        </div>
      </div>
    </div>
  )
}

function RightRail() {
  const healthQ = useQuery({
    queryKey: ["shell.health"],
    queryFn: () => fetchJson<any>("/health"),
    staleTime: 15_000,
    refetchInterval: 30_000,
  })

  const alertsQ = useQuery({
    queryKey: ["shell.alerts-summary"],
    queryFn: () => fetchJson<any>("/api/v1/alerts/summary"),
    staleTime: 30_000,
    refetchInterval: 60_000,
  })

  const isApiOk = healthQ.data?.status === "ok"
  const summary = alertsQ.data

  return (
    <div className="flex h-full flex-col">
      <div className="px-4 py-4">
        <div className="text-xs text-muted-foreground">Workspace</div>
        <div className="mt-1 text-sm font-semibold tracking-tight">System</div>
      </div>

      <Separator />

      <div className="flex-1 space-y-3 px-4 py-4 overflow-y-auto">
        {/* API Status */}
        <div className="rounded-xl border bg-card p-3 space-y-2">
          <div className="text-xs font-medium text-muted-foreground">API Status</div>
          <div className="flex items-center gap-2">
            <div
              className={`h-2 w-2 rounded-full ${
                healthQ.isLoading
                  ? "bg-yellow-500"
                  : isApiOk
                  ? "bg-green-500"
                  : "bg-red-500"
              }`}
            />
            <span className="text-xs">
              {healthQ.isLoading ? "Checking…" : isApiOk ? "Online" : "Offline"}
            </span>
          </div>
          <div className="text-[11px] text-muted-foreground font-mono">
            {process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"}
          </div>
        </div>

        {/* Live alert stats */}
        {summary && (
          <div className="rounded-xl border bg-card p-3 space-y-2">
            <div className="text-xs font-medium text-muted-foreground">Alert Summary</div>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <div className="text-[11px] text-muted-foreground">Total</div>
                <div className="text-sm font-semibold tabular-nums">
                  {summary.total_alerts?.toLocaleString() ?? "—"}
                </div>
              </div>
              <div>
                <div className="text-[11px] text-muted-foreground">High Risk</div>
                <div className="text-sm font-semibold tabular-nums text-orange-500">
                  {summary.high_risk_alerts?.toLocaleString() ?? "—"}
                </div>
              </div>
              <div>
                <div className="text-[11px] text-muted-foreground">Critical</div>
                <div className="text-sm font-semibold tabular-nums text-red-500">
                  {summary.critical_alerts?.toLocaleString() ?? "—"}
                </div>
              </div>
              <div>
                <div className="text-[11px] text-muted-foreground">Avg Score</div>
                <div className="text-sm font-semibold tabular-nums">
                  {summary.avg_risk_score ? Math.round(summary.avg_risk_score) : "—"}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Pipeline info */}
        <div className="rounded-xl border bg-card p-3 space-y-2">
          <div className="text-xs font-medium text-muted-foreground">Pipeline</div>
          <div className="space-y-1.5">
            {[
              { label: "Broker", value: "Redpanda" },
              { label: "Worker", value: "Faust" },
              { label: "DB", value: "Postgres 16" },
              { label: "Auth", value: "JWT v1" },
            ].map((item) => (
              <div key={item.label} className="flex items-center justify-between">
                <span className="text-[11px] text-muted-foreground">{item.label}</span>
                <span className="text-[11px] font-mono">{item.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <Separator />
      <div className="px-4 py-3 text-[11px] text-muted-foreground">SafeFlow · v1 · Data Eng</div>
    </div>
  )
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const isHome = pathname === "/"
  if (isHome) return <>{children}</>

  return (
    <div className="min-h-screen bg-background">
      {/* Desktop */}
      <div className="hidden lg:grid lg:grid-cols-[220px_minmax(0,1fr)_260px]">
        <aside className="sticky top-0 h-screen border-r bg-card overflow-y-auto">
          <Sidebar />
        </aside>

        <div className="min-w-0">
          <div className="sticky top-0 z-20 border-b bg-background/90 backdrop-blur">
            <div className="mx-auto flex w-full max-w-[1600px] items-center justify-between px-6 py-3">
              <div className="text-sm font-medium">
                {NAV.find((x) => pathname?.startsWith(x.href))?.title ?? "Workspace"}
              </div>
              <div className="text-xs text-muted-foreground font-mono">
                {process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"}
              </div>
            </div>
          </div>
          <main className="min-w-0">{children}</main>
        </div>

        <aside className="sticky top-0 h-screen border-l bg-card overflow-y-auto">
          <RightRail />
        </aside>
      </div>

      {/* Mobile */}
      <div className="lg:hidden">
        <div className="sticky top-0 z-20 border-b bg-background/90 backdrop-blur">
          <div className="flex items-center justify-between px-4 py-3">
            <Sheet>
              <SheetTrigger asChild>
                <Button variant="outline" size="sm">Menu</Button>
              </SheetTrigger>
              <SheetContent side="left" className="p-0">
                <Sidebar />
              </SheetContent>
            </Sheet>
            <div className="text-sm font-medium">SafeFlow</div>
            <div className="text-xs text-muted-foreground">Local</div>
          </div>
        </div>
        <main>{children}</main>
      </div>
    </div>
  )
}
