// src/components/shell/app-shell.tsx
"use client"

import * as React from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { useQuery } from "@tanstack/react-query"
import { fetchJson } from "@/lib/api/http"
import {
  Bell, ArrowLeftRight, Building2, FolderOpen,
  BarChart3, Settings, Shield, Activity, ChevronRight,
  Menu, Database, Cpu, Lock,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet"

type NavItem = {
  title: string
  href: string
  icon: React.ReactNode
  badge?: string
  badgeColor?: string
}

const NAV: NavItem[] = [
  { title: "Alerts", href: "/alerts", icon: <Bell className="h-4 w-4" />, badge: "Live", badgeColor: "text-emerald-400 border-emerald-400/30 bg-emerald-400/10" },
  { title: "Transactions", href: "/transactions", icon: <ArrowLeftRight className="h-4 w-4" /> },
  { title: "Entities", href: "/entities", icon: <Building2 className="h-4 w-4" /> },
  { title: "Cases", href: "/cases", icon: <FolderOpen className="h-4 w-4" /> },
  { title: "Models", href: "/models", icon: <BarChart3 className="h-4 w-4" /> },
  { title: "Settings", href: "/settings", icon: <Settings className="h-4 w-4" /> },
]

function NavLink({ item }: { item: NavItem }) {
  const pathname = usePathname()
  const active = pathname === item.href || pathname?.startsWith(item.href + "/")

  return (
    <Link
      href={item.href}
      className={cn(
        "group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-150",
        active
          ? "bg-blue-600 text-white shadow-lg shadow-blue-600/25"
          : "text-slate-400 hover:bg-slate-800/80 hover:text-slate-100"
      )}
    >
      <span className={cn("shrink-0", active ? "text-white" : "text-slate-500 group-hover:text-slate-300")}>
        {item.icon}
      </span>
      <span className="flex-1 truncate">{item.title}</span>
      {item.badge && (
        <span className={cn("rounded-full border px-1.5 py-0.5 text-[10px] font-semibold tracking-wide", item.badgeColor)}>
          {item.badge}
        </span>
      )}
      {active && <ChevronRight className="h-3 w-3 opacity-50" />}
    </Link>
  )
}

function Sidebar() {
  return (
    <div className="flex h-full flex-col bg-slate-950">
      {/* Logo */}
      <div className="flex items-center gap-3 px-4 py-5 border-b border-slate-800/50">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-blue-600 shadow-lg shadow-blue-600/30">
          <Shield className="h-4 w-4 text-white" />
        </div>
        <div>
          <div className="text-[13px] font-bold tracking-tight text-white">SafeFlow</div>
          <div className="text-[10px] text-slate-500 tracking-widest uppercase">Risk Workbench</div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-2 py-4 space-y-0.5 overflow-y-auto">
        <div className="mb-2 px-3 text-[10px] font-semibold uppercase tracking-widest text-slate-600">
          Navigation
        </div>
        {NAV.map((item) => (
          <NavLink key={item.href} item={item} />
        ))}
      </nav>

      {/* Footer */}
      <div className="border-t border-slate-800/50 px-3 py-3">
        <div className="flex items-center gap-2 rounded-lg px-2 py-2">
          <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-slate-800 text-xs font-bold text-slate-300">
            A
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-xs font-medium text-slate-300 truncate">Analyst</div>
            <div className="text-[10px] text-slate-600">Local dev · v1</div>
          </div>
          <div className="h-2 w-2 rounded-full bg-emerald-400 shadow-sm shadow-emerald-400/50" title="Online" />
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
    <div className="flex h-full flex-col bg-white border-l border-slate-100">
      <div className="px-4 py-4 border-b border-slate-100">
        <div className="text-[10px] font-semibold uppercase tracking-widest text-slate-400">System</div>
        <div className="mt-0.5 text-sm font-semibold text-slate-800">Live Monitor</div>
      </div>

      <div className="flex-1 overflow-y-auto px-3 py-3 space-y-3">
        {/* API Status */}
        <div className="rounded-xl border border-slate-100 bg-slate-50 p-3">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-1.5">
              <Activity className="h-3.5 w-3.5 text-slate-400" />
              <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wide">API Status</span>
            </div>
            <div className={cn(
              "flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-semibold border",
              isApiOk ? "bg-emerald-50 text-emerald-700 border-emerald-200" : "bg-red-50 text-red-700 border-red-200"
            )}>
              <div className={cn("h-1.5 w-1.5 rounded-full", isApiOk ? "bg-emerald-500 animate-pulse" : "bg-red-500")} />
              {healthQ.isLoading ? "Checking..." : isApiOk ? "Online" : "Offline"}
            </div>
          </div>
          <div className="text-[10px] text-slate-400 font-mono">http://localhost:8000</div>
        </div>

        {/* Alert Summary */}
        {summary && (
          <div className="rounded-xl border border-slate-100 bg-slate-50 p-3">
            <div className="flex items-center gap-1.5 mb-3">
              <Bell className="h-3.5 w-3.5 text-slate-400" />
              <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wide">Alert Summary</span>
            </div>
            <div className="grid grid-cols-2 gap-2">
              {[
                { label: "Total", value: summary.total_alerts?.toLocaleString(), color: "text-slate-800", border: "border-slate-100" },
                { label: "High Risk", value: summary.high_risk_alerts?.toLocaleString(), color: "text-orange-600", border: "border-orange-100" },
                { label: "Critical", value: summary.critical_alerts?.toLocaleString(), color: "text-red-600", border: "border-red-100" },
                { label: "Avg Score", value: summary.avg_risk_score ? Math.round(summary.avg_risk_score) : "—", color: "text-blue-600", border: "border-blue-100" },
              ].map((s) => (
                <div key={s.label} className={cn("rounded-lg bg-white border p-2", s.border)}>
                  <div className="text-[10px] text-slate-400 mb-0.5">{s.label}</div>
                  <div className={cn("text-sm font-bold tabular-nums leading-none", s.color)}>{s.value ?? "—"}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Pipeline */}
        <div className="rounded-xl border border-slate-100 bg-slate-50 p-3">
          <div className="flex items-center gap-1.5 mb-3">
            <Cpu className="h-3.5 w-3.5 text-slate-400" />
            <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wide">Pipeline</span>
          </div>
          <div className="space-y-2">
            {[
              { label: "Broker", value: "Redpanda", dot: "bg-emerald-400" },
              { label: "Worker", value: "Faust", dot: "bg-emerald-400" },
              { label: "DB", value: "Postgres 16", dot: "bg-emerald-400" },
              { label: "Auth", value: "JWT v1", dot: "bg-blue-400" },
            ].map((item) => (
              <div key={item.label} className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-[11px] text-slate-500">
                  <div className={cn("h-1.5 w-1.5 rounded-full", item.dot)} />
                  {item.label}
                </div>
                <span className="text-[11px] font-mono font-medium text-slate-700">{item.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="border-t border-slate-100 px-4 py-3">
        <div className="text-[10px] text-slate-400 font-mono">SafeFlow · v1 · Data Eng</div>
      </div>
    </div>
  )
}

function TopBar() {
  const pathname = usePathname()
  const currentPage = NAV.find((x) => pathname?.startsWith(x.href))

  return (
    <div className="sticky top-0 z-20 flex h-12 items-center justify-between border-b border-slate-100 bg-white/95 backdrop-blur-sm px-6">
      <div className="flex items-center gap-2 text-sm">
        <span className="text-slate-400 text-xs font-medium">SafeFlow</span>
        <ChevronRight className="h-3 w-3 text-slate-300" />
        <span className="font-semibold text-slate-800">{currentPage?.title ?? "Workspace"}</span>
      </div>
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-1 text-[11px] font-semibold text-emerald-700">
          <div className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
          Live
        </div>
        <div className="hidden sm:block text-[11px] font-mono text-slate-400">api:8000</div>
      </div>
    </div>
  )
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  if (pathname === "/") return <>{children}</>

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Desktop */}
      <div className="hidden lg:grid lg:grid-cols-[240px_minmax(0,1fr)_240px] min-h-screen">
        <aside className="sticky top-0 h-screen overflow-hidden">
          <Sidebar />
        </aside>
        <div className="min-w-0 flex flex-col bg-white min-h-screen">
          <TopBar />
          <main className="flex-1 min-w-0">{children}</main>
        </div>
        <aside className="sticky top-0 h-screen overflow-hidden">
          <RightRail />
        </aside>
      </div>

      {/* Mobile */}
      <div className="lg:hidden">
        <div className="sticky top-0 z-20 flex items-center justify-between border-b border-slate-200 bg-white px-4 py-3">
          <Sheet>
            <SheetTrigger asChild>
              <Button variant="outline" size="sm" className="h-8 w-8 p-0 border-slate-200">
                <Menu className="h-4 w-4" />
              </Button>
            </SheetTrigger>
            <SheetContent side="left" className="p-0 w-64 border-0">
              <Sidebar />
            </SheetContent>
          </Sheet>
          <div className="flex items-center gap-2">
            <Shield className="h-4 w-4 text-blue-600" />
            <span className="text-sm font-bold text-slate-800">SafeFlow</span>
          </div>
          <div className="h-2 w-2 rounded-full bg-emerald-500" />
        </div>
        <main>{children}</main>
      </div>
    </div>
  )
}
