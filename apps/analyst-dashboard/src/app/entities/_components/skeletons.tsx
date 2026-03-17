// src/app/entities/_components/skeletons.tsx
"use client"

import * as React from "react"

function Row() {
  return (
    <div className="grid grid-cols-6 gap-3 px-4 py-3 border-b">
      <div className="h-4 w-40 rounded bg-muted" />
      <div className="h-4 w-24 rounded bg-muted" />
      <div className="h-4 w-16 rounded bg-muted" />
      <div className="h-4 w-10 rounded bg-muted" />
      <div className="h-4 w-28 rounded bg-muted" />
      <div className="h-4 w-10 rounded bg-muted" />
    </div>
  )
}

export function EntitiesTableSkeleton() {
  return (
    <div className="min-w-[900px]">
      <div className="border-b px-4 py-3">
        <div className="h-4 w-48 rounded bg-muted" />
      </div>
      {Array.from({ length: 8 }).map((_, i) => (
        <Row key={i} />
      ))}
    </div>
  )
}

export function EntityDetailSkeleton() {
  return (
    <div className="p-4">
      <div className="h-5 w-48 rounded bg-muted" />
      <div className="mt-2 flex gap-2">
        <div className="h-5 w-20 rounded bg-muted" />
        <div className="h-5 w-16 rounded bg-muted" />
      </div>

      <div className="mt-6 space-y-3">
        {Array.from({ length: 7 }).map((_, i) => (
          <div key={i} className="grid grid-cols-[140px_1fr] gap-3">
            <div className="h-4 w-24 rounded bg-muted" />
            <div className="h-4 w-full max-w-[260px] rounded bg-muted" />
          </div>
        ))}
      </div>
    </div>
  )
}
