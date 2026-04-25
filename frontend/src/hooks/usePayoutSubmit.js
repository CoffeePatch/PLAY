import { useState, useCallback } from "react"
import { apiClient } from "../api/client"
import { API_ENDPOINTS } from "../utils/constants"

/**
 * Custom hook for submitting payout requests with idempotency
 * Handles error responses (409 Conflict, 400 Bad Request, etc.)
 * @returns {object} Submit function and loading/error states
 */
export const usePayoutSubmit = () => {
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)

  const submit = useCallback(
    async ({ merchantId, bankAccountId, amountPaise, idempotencyKey }) => {
      if (!merchantId || !bankAccountId || !amountPaise || !idempotencyKey) {
        throw new Error("merchantId, bankAccountId, amountPaise and idempotencyKey are required")
      }

      try {
        setSubmitting(true)
        setError(null)

        const response = await apiClient.post(
          API_ENDPOINTS.payoutCreate,
          {
            bank_account_id: Number(bankAccountId),
            amount_paise: Number(amountPaise),
          },
          {
          headers: {
            "Idempotency-Key": idempotencyKey,
            "X-Merchant-Id": merchantId,
          },
          }
        )

        setSubmitting(false)
        return {
          success: true,
          data: response.data,
          status: response.status,
        }
      } catch (err) {
        const errorResponse = err.response

        let errorMessage = "Failed to submit payout"
        let errorCode = "unknown"

        if (errorResponse) {
          errorCode = errorResponse.status

          // Handle specific error cases
          if (errorResponse.status === 400) {
            // Could be validation error or insufficient funds
            const data = errorResponse.data
            if (data?.detail) {
              errorMessage = data.detail
            } else if (data?.error) {
              errorMessage = data.error
            } else if (typeof data === "string") {
              errorMessage = data
            } else {
              errorMessage = "Invalid payout request (insufficient funds or invalid data)"
            }
          } else if (errorResponse.status === 409) {
            errorMessage = "Request already in progress. Please wait."
          } else if (errorResponse.status === 404) {
            errorMessage = "Merchant or bank account not found"
          } else if (errorResponse.status === 422) {
            // Validation error
            const data = errorResponse.data
            if (data?.detail && Array.isArray(data.detail)) {
              errorMessage = data.detail.map((d) => d.msg).join(", ")
            } else {
              errorMessage = "Validation error"
            }
          } else if (errorResponse.status >= 500) {
            errorMessage = "Server error. Please try again later."
          }
        }

        setSubmitting(false)
        setError(errorMessage)

        return {
          success: false,
          error: errorMessage,
          errorCode,
          status: errorResponse?.status,
        }
      }
    },
    []
  )

  const clearError = useCallback(() => {
    setError(null)
  }, [])

  return {
    submit,
    submitting,
    error,
    clearError,
  }
}
