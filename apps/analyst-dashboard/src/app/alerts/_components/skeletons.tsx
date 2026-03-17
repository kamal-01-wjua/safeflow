import * as React from "react"
import { Skeleton } from "@/components/ui/skeleton"

export function AlertsTableSkeleton() {
  return (
    <div className="p-4">
      {/* header */}
      <div className="mb-3 grid grid-cols-[150px_140px_110px_180px_160px_100px_120px] gap-3">
        <Skeleton className="h-4" />
        <Skeleton className="h-4" />
        <Skeleton className="h-4" />
        <Skeleton className="h-4" />
        <Skeleton className="h-4" />
        <Skeleton className="h-4" />
        <Skeleton className="h-4" />
      </div>

      {/* rows */}
      <div className="space-y-2">
        {Array.from({ length: 10 }).map((_, i) => (
          <div key={i} className="grid grid-cols-[150px_140px_110px_180px_160px_100px_120px] gap-3">
            <Skeleton className="h-10" />
            <Skeleton className="h-10" />
            <Skeleton className="h-10" />
            <Skeleton className="h-10" />
            <Skeleton className="h-10" />
            <Skeleton className="h-10" />
            <Skeleton className="h-10" />
          </div>
        ))}
      </div>

      {/* pager */}
      <div className="mt-6 flex items-center justify-between">
        <Skeleton className="h-8 w-52" />
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
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-2">
          <Skeleton className="h-4 w-28" />
          <Skeleton className="h-6 w-44" />
          <Skeleton className="h-4 w-36" />
        </div>
        <Skeleton className="h-9 w-28" />
      </div>

      <Skeleton className="mt-5 h-px w-full" />

      <div className="mt-4">
        <Skeleton className="h-4 w-28" />
        <div className="mt-2 grid grid-cols-3 gap-2">
          <Skeleton className="h-14" />
          <Skeleton className="h-14" />
          <Skeleton className="h-14" />
        </div>
      </div>

      <div className="mt-5">
        <Skeleton className="h-4 w-28" />
        <Skeleton className="mt-2 h-10 w-full" />
      </div>

      <div className="mt-5">
        <Skeleton className="h-4 w-28" />
        <Skeleton className="mt-2 h-28 w-full" />
      </div>

      <div className="mt-5">
        <Skeleton className="h-4 w-28" />
        <Skeleton className="mt-2 h-36 w-full" />
      </div>
    </div>
  )
}
