// src/lib/api/http.ts
export class ApiError extends Error {
  status: number
  url: string
  body?: unknown

  constructor(message: string, opts: { status: number; url: string; body?: unknown }) {
    super(message)
    this.name = "ApiError"
    this.status = opts.status
    this.url = opts.url
    this.body = opts.body
  }
}

function getBaseUrl() {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL
  if (!base) return "http://localhost:8000"
  return base.replace(/\/$/, "")
}

export async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${getBaseUrl()}${path.startsWith("/") ? path : `/${path}`}`

  const res = await fetch(url, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  })

  let body: unknown = undefined
  const text = await res.text()
  try {
    body = text ? JSON.parse(text) : undefined
  } catch {
    body = text
  }

  if (!res.ok) {
    const msg = typeof body === "object" && body && "detail" in (body as any)
      ? String((body as any).detail)
      : `Request failed: ${res.status}`
    throw new ApiError(msg, { status: res.status, url, body })
  }

  return body as T
}
