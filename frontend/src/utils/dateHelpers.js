// frontend/src/utils/dateHelpers.js
/**
 * Normalize date string to Asia/Taipei timezone
 * Handles timestamps with or without timezone information
 */
export function normalizeTaipeiDate(dateStr) {
  if (!dateStr) return null
  // Check if already has timezone suffix (Z, +08:00, etc.)
  if (/[Zz]|[+-]\d{2}:?\d{2}$/.test(dateStr)) {
    return dateStr
  }
  // Assume Asia/Taipei timezone if no timezone info
  return dateStr + '+08:00'
}

/**
 * Format date for display (YYYY-MM-DD format for grouping)
 */
export function formatDateKey(dateStr) {
  const normalized = normalizeTaipeiDate(dateStr)
  if (!normalized) return null
  const date = new Date(normalized)
  // Use local date parts to avoid UTC conversion bug
  // toISOString() converts to UTC, which causes dates near midnight to show wrong day
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}
