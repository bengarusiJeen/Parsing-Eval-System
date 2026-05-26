/* client.ts — base fetch wrapper used by all API modules.
   Paths are relative so Vite's dev-server proxy (`/api → :5000`) handles routing. */

export class ApiError extends Error {
  status: number
  body?: unknown
  constructor(message: string, status: number, body?: unknown) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.body = body
  }
}

async function parseBody(res: Response): Promise<unknown> {
  const text = await res.text()
  if (!text) return null
  try { return JSON.parse(text) } catch { return text }
}

export async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(path)
  const body = await parseBody(res)
  if (!res.ok) {
    throw new ApiError(`GET ${path} failed (${res.status})`, res.status, body)
  }
  return body as T
}

export async function apiPost<T>(path: string, payload: unknown): Promise<T> {
  const res = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  const body = await parseBody(res)
  if (!res.ok) {
    throw new ApiError(`POST ${path} failed (${res.status})`, res.status, body)
  }
  return body as T
}

export async function apiPatch<T>(path: string, payload: unknown): Promise<T> {
  const res = await fetch(path, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  const body = await parseBody(res)
  if (!res.ok) {
    throw new ApiError(`PATCH ${path} failed (${res.status})`, res.status, body)
  }
  return body as T
}
