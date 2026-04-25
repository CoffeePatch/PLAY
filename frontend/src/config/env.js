const apiTimeout = Number.parseInt(import.meta.env.VITE_API_TIMEOUT_MS ?? "10000", 10)

export const env = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1",
  apiTimeoutMs: Number.isFinite(apiTimeout) ? apiTimeout : 10000,
}
