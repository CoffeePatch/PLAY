import { useState, useEffect } from "react"
import { generateUUID } from "../utils/uuid"
import { formatPaiseToRupees } from "../utils/formatting"
import { useBankAccounts } from "../hooks/useBankAccounts"
import { usePayoutSubmit } from "../hooks/usePayoutSubmit"
import { useToast } from "../context/ToastContext"

/**
 * Payout request form component
 * Handles form submission with idempotency key generation
 * @param {string} merchantId - Merchant ID for payout
 * @param {function} onPayoutSubmitted - Callback when payout is successfully submitted
 * @param {number} availableBalance - Available balance in paise
 */
export default function PayoutForm({
  merchantId,
  onPayoutSubmitted,
  availableBalance = 0,
}) {
  // Form state
  const [amountRupees, setAmountRupees] = useState("")
  const [selectedAccountId, setSelectedAccountId] = useState("")
  const [idempotencyKey, setIdempotencyKey] = useState("")

  // Hooks
  const { accounts, loading: accountsLoading } = useBankAccounts(merchantId)
  const { submit: submitPayout, submitting } = usePayoutSubmit()
  const toast = useToast()

  // Initialize idempotency key on mount
  useEffect(() => {
    setIdempotencyKey(generateUUID())
  }, [])

  // Set default account on load
  useEffect(() => {
    if (accounts.length === 0) {
      setSelectedAccountId("")
      return
    }

    const selectedAccountExists = accounts.some(
      (account) => String(account.id) === selectedAccountId
    )

    if (!selectedAccountExists) {
      const primaryAccount = accounts.find((acc) => acc.is_primary)
      setSelectedAccountId(String(primaryAccount?.id || accounts[0].id))
    }
  }, [accounts, selectedAccountId])

  useEffect(() => {
    setAmountRupees("")
    setIdempotencyKey(generateUUID())
    setSelectedAccountId("")
  }, [merchantId])

  const handleSubmit = async (e) => {
    e.preventDefault()

    // Validation
    if (!amountRupees || parseFloat(amountRupees) <= 0) {
      toast.error("Please enter a valid amount")
      return
    }

    if (!selectedAccountId) {
      toast.error("Please select a bank account")
      return
    }

    const amountPaise = Math.round(parseFloat(amountRupees) * 100)

    if (amountPaise > availableBalance) {
      toast.error("Insufficient funds for this payout")
      return
    }

    // Submit payout
    const result = await submitPayout({
      merchantId,
      bankAccountId: selectedAccountId,
      amountPaise,
      idempotencyKey,
    })

    if (result.success) {
      toast.success(`Payout submitted! ID: ${result.data.id}`)
      // Reset form
      setAmountRupees("")
      setSelectedAccountId(String(accounts[0]?.id || ""))
      setIdempotencyKey(generateUUID()) // New key for next payout
      // Notify parent
      if (onPayoutSubmitted) {
        onPayoutSubmitted(result.data)
      }
    } else {
      // Error toast already shown via error state, but explicitly show here
      if (result.errorCode === 409) {
        toast.warning(result.error, 6000)
      } else if (result.errorCode === 400) {
        toast.error(result.error, 6000)
      } else {
        toast.error(result.error, 6000)
      }
    }
  }

  if (accountsLoading) {
    return (
      <section className="rounded-2xl border border-stone-200 bg-white p-5 shadow-sm">
        <div className="h-96 flex items-center justify-center">
          <p className="text-stone-600">Loading form...</p>
        </div>
      </section>
    )
  }

  if (accounts.length === 0) {
    return (
      <section className="rounded-2xl border border-amber-200 bg-amber-50 p-5 shadow-sm">
        <h3 className="font-semibold text-amber-900">No Bank Accounts</h3>
        <p className="mt-2 text-sm text-amber-800">
          This merchant has no bank accounts configured. Please add one before requesting a payout.
        </p>
      </section>
    )
  }

  const maxAmount = availableBalance / 100

  return (
    <section className="rounded-2xl border border-stone-200 bg-white p-5 shadow-sm">
      <div className="mb-6">
        <h2 className="text-lg font-semibold text-stone-900">Request Payout</h2>
        <p className="mt-1 text-sm text-stone-600">
          Submit a payout request. An idempotency key is automatically generated to prevent duplicate submissions.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Amount Field */}
        <div>
          <label className="block text-sm font-medium text-stone-700 mb-2">
            Amount (₹)
          </label>
          <div className="relative">
            <span className="absolute left-3 top-2.5 text-stone-500 font-medium">₹</span>
            <input
              type="number"
              step="0.01"
              min="0.01"
              max={maxAmount}
              value={amountRupees}
              onChange={(e) => setAmountRupees(e.target.value)}
              placeholder="0.00"
              disabled={submitting}
              className="w-full pl-8 pr-3 py-2 text-sm rounded-lg border border-stone-300 focus:ring-2 focus:ring-orange-300 focus:border-transparent outline-none transition disabled:opacity-50 disabled:cursor-not-allowed"
            />
          </div>
          <p className="mt-2 text-xs text-stone-500">
            Available: <strong>{formatPaiseToRupees(availableBalance)}</strong>
          </p>
          {amountRupees && parseFloat(amountRupees) > maxAmount && (
            <p className="mt-2 text-xs text-red-600 font-medium">
              Amount exceeds available balance
            </p>
          )}
        </div>

        {/* Bank Account Dropdown */}
        <div>
          <label className="block text-sm font-medium text-stone-700 mb-2">
            Bank Account
          </label>
          <select
            value={selectedAccountId}
            onChange={(e) => setSelectedAccountId(e.target.value)}
            disabled={submitting}
            className="w-full px-3 py-2 text-sm rounded-lg border border-stone-300 focus:ring-2 focus:ring-orange-300 focus:border-transparent outline-none transition disabled:opacity-50 disabled:cursor-not-allowed bg-white"
          >
            <option value="">Select a bank account</option>
            {accounts.map((account) => (
              <option key={account.id} value={account.id}>
                {account.account_number} ({account.ifsc})
                {account.is_primary ? " • Primary" : ""}
              </option>
            ))}
          </select>
        </div>

        {/* Idempotency Key Display */}
        <div className="bg-stone-50 rounded-lg p-3 border border-stone-200">
          <p className="text-xs font-semibold uppercase text-stone-600 mb-1">Idempotency Key</p>
          <p className="text-xs font-mono text-stone-700 break-all">{idempotencyKey}</p>
          <p className="text-xs text-stone-500 mt-2">
            This key prevents duplicate payouts if your request is accidentally sent twice.
          </p>
        </div>

        {/* Submit Button */}
        <div className="flex gap-3 pt-2">
          <button
            type="submit"
            disabled={submitting || !amountRupees || !selectedAccountId}
            className="flex-1 rounded-lg bg-orange-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-orange-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
          >
            {submitting ? (
              <span className="flex items-center justify-center gap-2">
                <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                Submitting...
              </span>
            ) : (
              "Submit Payout"
            )}
          </button>
        </div>

        {/* Info Text */}
        <div className="bg-blue-50 rounded-lg p-3 border border-blue-200">
          <p className="text-xs text-blue-900">
            <strong>Note:</strong> Your payout will be submitted with an idempotency key to prevent duplicate requests. Each successful submission generates a new key automatically.
          </p>
        </div>
      </form>
    </section>
  )
}
