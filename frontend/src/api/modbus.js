// frontend/src/api/modbus.js
import apiClient from './client'

const BASE_URL = '/api/modbus'

/**
 * Modbus Configuration API
 */
export const modbusApi = {
  /**
   * Get all Modbus configurations
   */
  getConfigs: () => {
    return apiClient.get(`${BASE_URL}/configs`)
  },

  /**
   * Get specific Modbus configuration
   */
  getConfig: (configId) => {
    return apiClient.get(`${BASE_URL}/configs/${configId}`)
  },

  /**
   * Get Modbus configuration for a station
   */
  getStationConfig: (stationId) => {
    return apiClient.get(`${BASE_URL}/stations/${stationId}/config`)
  },

  /**
   * Create Modbus configuration
   */
  createConfig: (data) => {
    return apiClient.post(`${BASE_URL}/configs`, data)
  },

  /**
   * Update Modbus configuration
   */
  updateConfig: (configId, data) => {
    return apiClient.put(`${BASE_URL}/configs/${configId}`, data)
  },

  /**
   * Delete Modbus configuration
   */
  deleteConfig: (configId) => {
    return apiClient.delete(`${BASE_URL}/configs/${configId}`)
  },

  /**
   * Get all Modbus listener statuses
   */
  getAllStatuses: () => {
    return apiClient.get(`${BASE_URL}/status`)
  },

  /**
   * Get Modbus listener status for a station
   */
  getStatus: (stationId) => {
    return apiClient.get(`${BASE_URL}/status/${stationId}`)
  },

  /**
   * WebSocket connection for real-time events
   */
  connectWebSocket: (stationId) => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const wsUrl = `${protocol}//${host}/api/modbus/ws/${stationId}`
    return new WebSocket(wsUrl)
  }
}
