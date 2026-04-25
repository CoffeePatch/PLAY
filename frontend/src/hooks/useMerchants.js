import { useCallback, useEffect, useState } from "react"

import { apiClient } from "../api/client"
import { API_ENDPOINTS } from "../utils/constants"

export const useMerchants = () => {
  const [merchants, setMerchants] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchMerchants = useCallback(async () => {
    try {
      setError(null)
      const response = await apiClient.get(API_ENDPOINTS.merchants)
      const payload = Array.isArray(response.data)
        ? response.data
        : response.data?.results || []
      setMerchants(payload)
    } catch (err) {
      setError(err.message || "Failed to fetch merchants")
      setMerchants([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchMerchants()
  }, [fetchMerchants])

  return {
    merchants,
    loading,
    error,
    refetch: fetchMerchants,
  }
}
