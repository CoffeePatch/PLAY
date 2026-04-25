import { useState, useEffect, useCallback, useRef } from "react"
import { apiClient } from "../api/client"
import { API_ENDPOINTS, POLLING_INTERVALS } from "../utils/constants"

/**
 * Custom hook for fetching merchant balance with polling support
 * @param {string} merchantId - Merchant ID to fetch balance for
 * @param {number} pollInterval - Polling interval in milliseconds (default: 5000ms)
 * @param {boolean} enabled - Whether to enable polling (default: true)
 * @returns {object} Balance data and loading/error states
 */
export const useBalance = (
  merchantId,
  pollInterval = POLLING_INTERVALS.balance,
  enabled = true
) => {
  const [balance, setBalance] = useState({
    available_paise: 0,
    held_paise: 0,
    total_paise: 0,
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const pollIntervalRef = useRef(null)

  const fetchBalance = useCallback(async () => {
    if (!merchantId || !enabled) {
      setLoading(false)
      return
    }

    try {
      setError(null)
      const response = await apiClient.get(API_ENDPOINTS.balance(merchantId))
      setBalance(response.data)
      setLoading(false)
    } catch (err) {
      console.error("Failed to fetch balance:", err)
      setError(err.message || "Failed to fetch balance")
      setLoading(false)
    }
  }, [merchantId, enabled])

  // Initial fetch
  useEffect(() => {
    if (enabled && merchantId) {
      setLoading(true)
      fetchBalance()
    } else {
      setBalance({
        available_paise: 0,
        held_paise: 0,
        total_paise: 0,
      })
      setError(null)
      setLoading(false)
    }
  }, [merchantId, enabled, fetchBalance])

  // Setup polling
  useEffect(() => {
    if (!enabled || !merchantId) return

    // Clear existing interval
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current)
    }

    // Set up new interval
    pollIntervalRef.current = setInterval(() => {
      fetchBalance()
    }, pollInterval)

    // Cleanup
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current)
      }
    }
  }, [merchantId, pollInterval, enabled, fetchBalance])

  const refetch = useCallback(() => {
    fetchBalance()
  }, [fetchBalance])

  return {
    balance,
    loading,
    error,
    refetch,
  }
}
