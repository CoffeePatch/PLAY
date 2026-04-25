import { useState, useEffect, useCallback, useRef } from "react"
import { apiClient } from "../api/client"
import { API_ENDPOINTS, POLLING_INTERVALS, PAGINATION } from "../utils/constants"

/**
 * Custom hook for fetching merchant ledger with pagination and polling
 * @param {string} merchantId - Merchant ID to fetch ledger for
 * @param {number} pageSize - Items per page (default: 10)
 * @param {number} pollInterval - Polling interval in milliseconds (default: 10000ms)
 * @param {boolean} enabled - Whether to enable polling (default: true)
 * @returns {object} Ledger data, pagination state, and control functions
 */
export const useLedger = (
  merchantId,
  pageSize = PAGINATION.defaultPageSize,
  pollInterval = POLLING_INTERVALS.ledger,
  enabled = true
) => {
  const [entries, setEntries] = useState([])
  const [currentPage, setCurrentPage] = useState(1)
  const [totalCount, setTotalCount] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const pollIntervalRef = useRef(null)

  const totalPages = Math.ceil(totalCount / pageSize)

  const fetchLedger = useCallback(async (page = 1) => {
    if (!merchantId || !enabled) {
      setLoading(false)
      return
    }

    try {
      setError(null)
      const response = await apiClient.get(API_ENDPOINTS.ledger(merchantId), {
        params: {
          page,
          page_size: pageSize,
        },
      })

      // Handle paginated response
      if (response.data.results) {
        setEntries(response.data.results)
        setTotalCount(response.data.count || 0)
      } else if (Array.isArray(response.data)) {
        // Handle non-paginated response
        setEntries(response.data)
        setTotalCount(response.data.length)
      }

      setCurrentPage(page)
      setLoading(false)
    } catch (err) {
      console.error("Failed to fetch ledger:", err)
      setError(err.message || "Failed to fetch ledger")
      setLoading(false)
    }
  }, [merchantId, pageSize, enabled])

  // Initial fetch
  useEffect(() => {
    if (enabled && merchantId) {
      setLoading(true)
      fetchLedger(1)
    } else {
      setEntries([])
      setCurrentPage(1)
      setTotalCount(0)
      setError(null)
      setLoading(false)
    }
  }, [merchantId, enabled, fetchLedger])

  // Setup polling (only for current page)
  useEffect(() => {
    if (!enabled || !merchantId) return

    // Clear existing interval
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current)
    }

    // Set up new interval for current page only
    pollIntervalRef.current = setInterval(() => {
      fetchLedger(currentPage)
    }, pollInterval)

    // Cleanup
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current)
      }
    }
  }, [merchantId, currentPage, pollInterval, enabled, fetchLedger])

  const goToPage = useCallback(
    (page) => {
      const validPage = Math.max(1, Math.min(page, totalPages || 1))
      fetchLedger(validPage)
    },
    [totalPages, fetchLedger]
  )

  const nextPage = useCallback(() => {
    goToPage(currentPage + 1)
  }, [currentPage, goToPage])

  const prevPage = useCallback(() => {
    goToPage(currentPage - 1)
  }, [currentPage, goToPage])

  const refetch = useCallback(() => {
    fetchLedger(currentPage)
  }, [currentPage, fetchLedger])

  return {
    entries,
    currentPage,
    totalPages,
    totalCount,
    pageSize,
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
