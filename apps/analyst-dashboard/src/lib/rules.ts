// src/lib/rules.ts
export type RuleMeta = {
  label: string
  category: "Amount" | "Time" | "Behavior" | "Counterparty" | "Geo" | "Other"
  tone?: "neutral" | "warning" | "danger"
}

const RULES: Record<string, RuleMeta> = {
  R_HIGH_AMOUNT_10K: { label: "High amount ≥ 10,000", category: "Amount", tone: "danger" },
  R_WEEKEND_DEBIT: { label: "Weekend debit", category: "Time", tone: "warning" },
  R_LARGE_NIGHT_TXN: { label: "Large transaction at night", category: "Time", tone: "warning" },
}

export function ruleMeta(code: string): RuleMeta {
  return RULES[code] ?? { label: code, category: "Other", tone: "neutral" }
}
