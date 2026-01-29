import request from '@/utils/request'

/**
 * Get all stations for a project
 * @param {number} projectId - Project ID
 * @returns {Promise<Array>} List of stations
 */
export function getProjectStations(projectId) {
  return request({
    url: `/api/projects/${projectId}/stations`,
    method: 'get'
  })
}

/**
 * Create new station
 * @param {Object} data - Station data
 * @returns {Promise<Object>} Created station
 */
export function createStation(data) {
  return request({
    url: '/api/stations',
    method: 'post',
    data
  })
}

/**
 * Update station
 * @param {number} id - Station ID
 * @param {Object} data - Updated station data
 * @returns {Promise<Object>} Updated station
 */
export function updateStation(id, data) {
  return request({
    url: `/api/stations/${id}`,
    method: 'put',
    data
  })
}

/**
 * Delete station
 * @param {number} id - Station ID
 * @returns {Promise<void>}
 */
export function deleteStation(id) {
  return request({
    url: `/api/stations/${id}`,
    method: 'delete'
  })
}
