// src/lib/format.ts
import { formatDistanceToNowStrict } from "date-fns"

export function formatMoney(amount: number, currency: string) {
  try {
    return new Intl.NumberFormat(undefined, {
      style: "currency",
      currency,
      maximumFractionDigits: 2,
    }).format(amount)
  } catch {
    return `${amount.toFixed(2)} ${currency}`
  }
}

export function formatIsoAgo(iso: string) {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return formatDistanceToNowStrict(d, { addSuffix: true })
}

export function formatIso(iso: string) {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleString()
}
