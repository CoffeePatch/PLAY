import { useState, useEffect, useCallback } from "react"
import { apiClient } from "../api/client"
import { API_ENDPOINTS } from "../utils/constants"

/**
 * Custom hook for fetching merchant's bank accounts
 * @param {string} merchantId - Merchant ID to fetch accounts for
 * @param {boolean} enabled - Whether to enable fetching (default: true)
 * @returns {object} Bank accounts list and loading/error states
 */
export const useBankAccounts = (merchantId, enabled = true) => {
  const [accounts, setAccounts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchAccounts = useCallback(async () => {
    if (!merchantId || !enabled) {
      setAccounts([])
      setLoading(false)
      return
    }

    try {
      setError(null)
      setLoading(true)
      const response = await apiClient.get(API_ENDPOINTS.bankAccounts(merchantId))
      setAccounts(
        Array.isArray(response.data) ? response.data : response.data?.results || []
      )
      setLoading(false)
    } catch (err) {
      console.error("Failed to fetch bank accounts:", err)
      setError(err.message || "Failed to fetch bank accounts")
      setLoading(false)
    }
  }, [merchantId, enabled])

  useEffect(() => {
    if (enabled && merchantId) {
      fetchAccounts()
    } else {
      setAccounts([])
      setError(null)
      setLoading(false)
    }
  }, [merchantId, enabled, fetchAccounts])

  const refetch = useCallback(() => {
    fetchAccounts()
  }, [fetchAccounts])

  return {
    accounts,
    loading,
    error,
    refetch,
  }
}
