/**
 * Test Execution API client
 */
import apiClient from './client'

/**
 * Create a new test session
 * @param {Object} sessionData - Test session data { serial_number, station_id }
 * @returns {Promise} Created test session
 */
export const createTestSession = (sessionData) => {
  return apiClient.post('/api/tests/sessions', sessionData)
}

/**
 * Get test session by ID
 * @param {number} sessionId - Test session ID
 * @returns {Promise} Test session
 */
export const getTestSession = (sessionId) => {
  return apiClient.get(`/api/tests/sessions/${sessionId}`)
}

/**
 * Get test session status with progress
 * @param {number} sessionId - Test session ID
 * @returns {Promise} Test session status
 */
export const getTestSessionStatus = (sessionId) => {
  return apiClient.get(`/api/tests/sessions/${sessionId}/status`)
}

/**
 * Upload a single test result
 * @param {number} sessionId - Test session ID
 * @param {Object} resultData - Test result data
 * @returns {Promise} Created test result
 */
export const createTestResult = (sessionId, resultData) => {
  return apiClient.post(`/api/tests/sessions/${sessionId}/results`, resultData)
}

/**
 * Batch upload multiple test results
 * @param {number} sessionId - Test session ID
 * @param {Array} results - Array of test result data
 * @returns {Promise} Batch upload response
 */
export const createTestResultsBatch = (sessionId, results) => {
  return apiClient.post(`/api/tests/sessions/${sessionId}/results/batch`, {
    session_id: sessionId,
    results
  })
}

/**
 * Complete a test session
 * @param {number} sessionId - Test session ID
 * @param {Object} completeData - Test completion data
 * @returns {Promise} Updated test session
 */
export const completeTestSession = (sessionId, completeData) => {
  return apiClient.post(`/api/tests/sessions/${sessionId}/complete`, completeData)
}

/**
 * Get all results for a test session
 * @param {number} sessionId - Test session ID
 * @returns {Promise} Array of test results
 */
export const getSessionResults = (sessionId) => {
  return apiClient.get(`/api/tests/sessions/${sessionId}/results`)
}

/**
 * List test sessions with optional filters
 * @param {Object} params - Query parameters { station_id, serial_number, limit, offset }
 * @returns {Promise} Array of test sessions
 */
export const listTestSessions = (params = {}) => {
  return apiClient.get('/api/tests/sessions', { params })
}

/**
 * Start test execution for a session
 * @param {number} sessionId - Test session ID
 * @returns {Promise} Test execution status
 */
export const startTestExecution = (sessionId) => {
  return apiClient.post(`/api/tests/sessions/${sessionId}/start`)
}

/**
 * Stop a running test session
 * @param {number} sessionId - Test session ID
 * @returns {Promise} Stop status
 */
export const stopTestExecution = (sessionId) => {
  return apiClient.post(`/api/tests/sessions/${sessionId}/stop`)
}

/**
 * Get instrument status
 * @returns {Promise} Instrument status information
 */
export const getInstrumentStatus = () => {
  return apiClient.get('/api/tests/instruments/status')
}

/**
 * Reset an instrument
 * @param {string} instrumentId - Instrument ID
 * @returns {Promise} Reset status
 */
export const resetInstrument = (instrumentId) => {
  return apiClient.post(`/api/tests/instruments/${instrumentId}/reset`)
}
