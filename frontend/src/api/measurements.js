/**
 * Measurement API client
 * Handles test parameter templates and validation
 */
import apiClient from './client'

/**
 * Get all measurement templates
 * @returns {Promise<{templates: Object, test_types: string[]}>} All measurement templates with test types list
 */
export const getMeasurementTemplates = () => {
  return apiClient.get('/api/measurements/templates')
}

/**
 * Get specific test type template
 * @param {string} testType - Test type name (PowerRead, PowerSet, etc.)
 * @returns {Promise<{test_type: string, switch_modes: Object}>} Test type templates
 */
export const getTestTypeTemplate = (testType) => {
  return apiClient.get(`/api/measurements/templates/${testType}`)
}

/**
 * Validate measurement parameters against template
 * @param {string} testType - Test type
 * @param {string} switchMode - Switch mode (optional)
 * @param {Object} parameters - Parameters to validate
 * @returns {Promise<{valid: boolean, missing_params: string[], invalid_params: string[], suggestions: string[]}>} Validation result
 */
export const validateMeasurementParams = (testType, switchMode, parameters) => {
  return apiClient.post('/api/measurements/validate-params', {
    test_type: testType,
    switch_mode: switchMode,
    parameters
  })
}

/**
 * Get available instruments list
 * @returns {Promise} Available instruments configuration
 */
export const getAvailableInstruments = () => {
  return apiClient.get('/api/measurements/instruments/available')
}

/**
 * Get current instrument status
 * @returns {Promise} Instrument status list
 */
export const getInstrumentStatus = () => {
  return apiClient.get('/api/measurements/instruments')
}
