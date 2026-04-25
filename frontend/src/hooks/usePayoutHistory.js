import { useState, useEffect, useCallback, useRef } from "react"
import { apiClient } from "../api/client"
import { API_ENDPOINTS, POLLING_INTERVALS, PAGINATION } from "../utils/constants"

/**
 * Custom hook for fetching payout history with polling
 * @param {string} merchantId - Merchant ID to fetch payouts for
 * @param {number} pageSize - Items per page
 * @param {number} pollInterval - Polling interval in milliseconds
 * @param {boolean} enabled - Whether to enable polling
 * @returns {object} Payout history data and pagination controls
 */
export const usePayoutHistory = (
  merchantId,
  pageSize = PAGINATION.defaultPageSize,
  pollInterval = POLLING_INTERVALS.payouts,
  enabled = true
) => {
  const [payouts, setPayouts] = useState([])
  const [currentPage, setCurrentPage] = useState(1)
  const [totalCount, setTotalCount] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const pollIntervalRef = useRef(null)

  const totalPages = Math.ceil(totalCount / pageSize)

  const fetchPayouts = useCallback(
    async (page = 1) => {
      if (!merchantId || !enabled) {
        setLoading(false)
        return
      }

      try {
        setError(null)
        const response = await apiClient.get(API_ENDPOINTS.payouts(merchantId), {
          params: {
            page,
            page_size: pageSize,
          },
        })

        if (response.data.results) {
          setPayouts(response.data.results)
          setTotalCount(response.data.count || 0)
        } else if (Array.isArray(response.data)) {
          setPayouts(response.data)
          setTotalCount(response.data.length)
        }

        setCurrentPage(page)
        setLoading(false)
      } catch (err) {
        console.error("Failed to fetch payout history:", err)
        setError(err.message || "Failed to fetch payout history")
        setLoading(false)
      }
    },
    [merchantId, pageSize, enabled]
  )

  // Initial fetch
  useEffect(() => {
    if (enabled && merchantId) {
      setLoading(true)
      fetchPayouts(1)
    } else {
      setPayouts([])
      setCurrentPage(1)
      setTotalCount(0)
      setError(null)
      setLoading(false)
    }
  }, [merchantId, enabled, fetchPayouts])

  // Setup polling
  useEffect(() => {
    if (!enabled || !merchantId) return

    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current)
    }

    pollIntervalRef.current = setInterval(() => {
      fetchPayouts(currentPage)
    }, pollInterval)

    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current)
      }
    }
  }, [merchantId, currentPage, pollInterval, enabled, fetchPayouts])

  const goToPage = useCallback(
    (page) => {
      const validPage = Math.max(1, Math.min(page, totalPages || 1))
      fetchPayouts(validPage)
    },
    [totalPages, fetchPayouts]
  )

  const nextPage = useCallback(() => {
    goToPage(currentPage + 1)
  }, [currentPage, goToPage])

  const prevPage = useCallback(() => {
    goToPage(currentPage - 1)
  }, [currentPage, goToPage])

  const refetch = useCallback(() => {
    fetchPayouts(currentPage)
  }, [currentPage, fetchPayouts])

  return {
    payouts,
    currentPage,
    totalPages,
    totalCount,
    loading,
    error,
    goToPage,
    nextPage,
    prevPage,
    refetch,
    hasNextPage: currentPage < totalPages,
    hasPrevPage: currentPage > 1,
  }
}
