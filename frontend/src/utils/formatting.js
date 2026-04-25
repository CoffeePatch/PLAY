/**
 * Format paise (smallest currency unit) to rupees with proper decimal places
 * @param {number} paise - Amount in paise
 * @returns {string} Formatted rupee amount
 */
export const formatPaiseToRupees = (paise) => {
  if (paise === null || paise === undefined) {
    return "₹0.00"
  }
  const rupees = paise / 100
  return `₹${rupees.toLocaleString("en-IN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`
}

/**
 * Format ISO date string to readable date with time
 * @param {string} dateString - ISO 8601 date string
 * @returns {string} Formatted date
 */
export const formatDate = (dateString) => {
  if (!dateString) return "-"
  const date = new Date(dateString)
  return date.toLocaleString("en-IN", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  })
}

/**
 * Format short date for ledger table
 * @param {string} dateString - ISO 8601 date string
 * @returns {string} Formatted short date
 */
export const formatShortDate = (dateString) => {
  if (!dateString) return "-"
  const date = new Date(dateString)
  return date.toLocaleDateString("en-IN", {
    month: "short",
    day: "numeric",
    year: "2-digit",
  })
}

/**
 * Truncate text to specified length with ellipsis
 * @param {string} text - Text to truncate
 * @param {number} maxLength - Maximum length
 * @returns {string} Truncated text
 */
export const truncateText = (text, maxLength = 32) => {
  if (!text || text.length <= maxLength) return text
  return `${text.substring(0, maxLength - 3)}...`
}
