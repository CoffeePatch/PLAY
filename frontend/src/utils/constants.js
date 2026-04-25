/**
 * Ledger entry types - used for display and filtering
 */
export const LEDGER_TYPES = {
  CREDIT: "CREDIT",
  DEBIT: "DEBIT",
  HOLD: "HOLD",
  RELEASE: "RELEASE",
}

/**
 * Color scheme for ledger entry types
 * Returns Tailwind classes for each type
 */
export const LEDGER_TYPE_COLORS = {
  [LEDGER_TYPES.CREDIT]: {
    bg: "bg-green-50",
    text: "text-green-900",
    badge: "bg-green-100 text-green-800",
    icon: "✓",
  },
  [LEDGER_TYPES.DEBIT]: {
    bg: "bg-red-50",
    text: "text-red-900",
    badge: "bg-red-100 text-red-800",
    icon: "−",
  },
  [LEDGER_TYPES.HOLD]: {
    bg: "bg-amber-50",
    text: "text-amber-900",
    badge: "bg-amber-100 text-amber-800",
    icon: "⏸",
  },
  [LEDGER_TYPES.RELEASE]: {
    bg: "bg-blue-50",
    text: "text-blue-900",
    badge: "bg-blue-100 text-blue-800",
    icon: "↻",
  },
}

/**
 * Get color scheme for a ledger type
 * @param {string} type - Ledger entry type
 * @returns {object} Color scheme with bg, text, badge, icon
 */
export const getColorScheme = (type) => {
  return LEDGER_TYPE_COLORS[type] || LEDGER_TYPE_COLORS.CREDIT
}

/**
 * Payout status colors for future use in Task 4.4
 */
export const PAYOUT_STATUS_COLORS = {
  PENDING: {
    badge: "bg-yellow-100 text-yellow-800",
    text: "text-yellow-900",
    icon: "⏳",
  },
  PROCESSING: {
    badge: "bg-blue-100 text-blue-800",
    text: "text-blue-900",
    icon: "⚙️",
  },
  COMPLETED: {
    badge: "bg-green-100 text-green-800",
    text: "text-green-900",
    icon: "✓",
  },
  FAILED: {
    badge: "bg-red-100 text-red-800",
    text: "text-red-900",
    icon: "✕",
  },
}

/**
 * API Endpoints
 */
export const API_ENDPOINTS = {
  merchants: "/merchants",
  balance: (merchantId) => `/merchants/${merchantId}/balance`,
  bankAccounts: (merchantId) => `/merchants/${merchantId}/bank-accounts`,
  ledger: (merchantId) => `/merchants/${merchantId}/ledger`,
  payouts: (merchantId) => `/merchants/${merchantId}/payouts`,
  payoutCreate: "/payouts/",
}

/**
 * Polling intervals (in milliseconds)
 */
export const POLLING_INTERVALS = {
  balance: 5000, // 5 seconds for balance
  ledger: 10000, // 10 seconds for ledger
  payouts: 5000, // 5 seconds for payout history
}

/**
 * Pagination defaults
 */
export const PAGINATION = {
  defaultPageSize: 10,
  pageSizeOptions: [10, 25, 50],
}
