// src/app/transactions/_components/skeletons.tsx
import * as React from "react"
import { Skeleton } from "@/components/ui/skeleton"

export function TransactionsTableSkeleton() {
  return (
    <div className="p-4">
      <div className="space-y-2">
        {Array.from({ length: 10 }).map((_, i) => (
          <div key={i} className="grid grid-cols-[180px_120px_140px_1fr_140px] gap-3">
            <Skeleton className="h-9" />
            <Skeleton className="h-9" />
            <Skeleton className="h-9" />
            <Skeleton className="h-9" />
            <Skeleton className="h-9" />
          </div>
        ))}
      </div>

      <div className="mt-6 flex items-center justify-between">
        <Skeleton className="h-8 w-44" />
        <div className="flex gap-2">
          <Skeleton className="h-8 w-20" />
          <Skeleton className="h-8 w-20" />
        </div>
      </div>
    </div>
  )
}

export function DetailSkeleton() {
  return (
    <div className="p-4">
      <div className="flex items-start justify-between">
        <div className="space-y-2">
          <Skeleton className="h-4 w-28" />
          <Skeleton className="h-6 w-44" />
        </div>
        <Skeleton className="h-8 w-28" />
      </div>

      <Skeleton className="mt-4 h-1 w-full" />

      <div className="mt-4 grid grid-cols-3 gap-2">
        <Skeleton className="h-14" />
        <Skeleton className="h-14" />
        <Skeleton className="h-14" />
      </div>

      <Skeleton className="mt-4 h-20 w-full" />
      <Skeleton className="mt-4 h-36 w-full" />
    </div>
  )
}
