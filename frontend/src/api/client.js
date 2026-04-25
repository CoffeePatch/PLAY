import axios from "axios"

import { env } from "../config/env"

export const apiClient = axios.create({
  baseURL: env.apiBaseUrl,
  timeout: env.apiTimeoutMs,
})

apiClient.interceptors.request.use(
  (config) => {
    config.headers = config.headers ?? {}
    config.headers["X-Client"] = "playto-dashboard"
    return config
  },
  (error) => Promise.reject(error)
)

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      console.error("API error", {
        status: error.response.status,
        data: error.response.data,
      })
    }
    return Promise.reject(error)
  }
)
