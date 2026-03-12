// frontend/src/api/instruments.js
import apiClient from './client'

/**
 * Get all instruments
 * @param {boolean} enabledOnly - Return only enabled instruments
 * @returns {Promise}
 */
export function getInstruments(enabledOnly = false) {
  return apiClient.get('/api/instruments', {
    params: { enabled_only: enabledOnly }
  })
}

/**
 * Get instrument by ID
 * @param {string} instrumentId - Instrument ID (e.g. 'DAQ973A_1')
 * @returns {Promise}
 */
export function getInstrument(instrumentId) {
  return apiClient.get(`/api/instruments/${instrumentId}`)
}

/**
 * Create new instrument
 * @param {Object} data - Instrument data
 * @returns {Promise}
 */
export function createInstrument(data) {
  return apiClient.post('/api/instruments', data)
}

/**
 * Update instrument (partial update)
 * @param {string} instrumentId - Instrument ID
 * @param {Object} data - Updated instrument data
 * @returns {Promise}
 */
export function updateInstrument(instrumentId, data) {
  return apiClient.patch(`/api/instruments/${instrumentId}`, data)
}

/**
 * Delete instrument
 * @param {string} instrumentId - Instrument ID
 * @returns {Promise}
 */
export function deleteInstrument(instrumentId) {
  return apiClient.delete(`/api/instruments/${instrumentId}`)
}
