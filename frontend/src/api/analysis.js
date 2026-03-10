// frontend/src/api/analysis.js
import apiClient from './client'

/**
 * Fetch descriptive statistics for a test plan script in a date range.
 *
 * @param {Object} params
 * @param {number} params.station_id      - Required
 * @param {string} params.test_plan_name  - Required (script/plan name)
 * @param {string} [params.date_from]     - YYYY-MM-DD
 * @param {string} [params.date_to]       - YYYY-MM-DD
 */
export function getAnalysis(params) {
  return apiClient.get('/api/measurement-results/analysis', { params })
}
