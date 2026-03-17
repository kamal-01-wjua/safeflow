import type { Metadata } from "next"
import "./globals.css"

import { QueryProvider } from "@/components/providers/query-provider"
import { AppShell } from "@/components/shell/app-shell"

export const metadata: Metadata = {
  title: "SafeFlow · Analyst",
  description: "Enterprise risk & fraud intelligence workbench.",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="h-full">
      {/* ✅ allow the app to scroll inside the shell (don’t lock body) */}
      <body className="h-full min-h-screen overflow-y-auto">
        <QueryProvider>
          <AppShell>{children}</AppShell>
        </QueryProvider>
      </body>
    </html>
  )
}
