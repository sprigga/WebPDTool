import apiClient from './client'

/**
 * Get all projects
 * @param {number} skip - Number of records to skip
 * @param {number} limit - Maximum records to return
 * @returns {Promise}
 */
export function getProjects(skip = 0, limit = 100) {
  return apiClient.get('/api/projects', {
    params: { skip, limit }
  })
}

/**
 * Get project by ID
 * @param {number} id - Project ID
 * @returns {Promise}
 */
export function getProject(id) {
  return apiClient.get(`/api/projects/${id}`)
}

/**
 * Create new project
 * @param {Object} data - Project data
 * @returns {Promise}
 */
export function createProject(data) {
  return apiClient.post('/api/projects', data)
}

/**
 * Update project
 * @param {number} id - Project ID
 * @param {Object} data - Updated project data
 * @returns {Promise}
 */
export function updateProject(id, data) {
  return apiClient.put(`/api/projects/${id}`, data)
}

/**
 * Delete project
 * @param {number} id - Project ID
 * @returns {Promise}
 */
export function deleteProject(id) {
  return apiClient.delete(`/api/projects/${id}`)
}

/**
 * Get project stations
 * @param {number} projectId - Project ID
 * @returns {Promise}
 */
export function getProjectStations(projectId) {
  return apiClient.get(`/api/projects/${projectId}/stations`)
}

/**
 * Get station by ID
 * @param {number} id - Station ID
 * @returns {Promise}
 */
export function getStation(id) {
  return apiClient.get(`/api/stations/${id}`)
}

/**
 * Create new station
 * @param {Object} data - Station data
 * @returns {Promise}
 */
export function createStation(data) {
  return apiClient.post('/api/stations', data)
}

/**
 * Update station
 * @param {number} id - Station ID
 * @param {Object} data - Updated station data
 * @returns {Promise}
 */
export function updateStation(id, data) {
  return apiClient.put(`/api/stations/${id}`, data)
}

/**
 * Delete station
 * @param {number} id - Station ID
 * @returns {Promise}
 */
export function deleteStation(id) {
  return apiClient.delete(`/api/stations/${id}`)
}
