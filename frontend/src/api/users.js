import apiClient from './client'

/**
 * Get all users
 * @param {number} offset - Number of records to skip
 * @param {number} limit - Maximum records to return
 * @returns {Promise}
 */
export function getUsers(offset = 0, limit = 100) {
  return apiClient.get('/api/users', {
    params: { offset, limit }
  })
}

/**
 * Get user by ID
 * @param {number} id - User ID
 * @returns {Promise}
 */
export function getUser(id) {
  return apiClient.get(`/api/users/${id}`)
}

/**
 * Create new user
 * @param {Object} data - User data
 * @returns {Promise}
 */
export function createUser(data) {
  return apiClient.post('/api/users', data)
}

/**
 * Update user
 * @param {number} id - User ID
 * @param {Object} data - Updated user data
 * @returns {Promise}
 */
export function updateUser(id, data) {
  return apiClient.put(`/api/users/${id}`, data)
}

/**
 * Change user password
 * @param {number} id - User ID
 * @param {string} newPassword - New password
 * @returns {Promise}
 */
export function changeUserPassword(id, newPassword) {
  return apiClient.put(`/api/users/${id}/password`, { new_password: newPassword })
}

/**
 * Delete user
 * @param {number} id - User ID
 * @returns {Promise}
 */
export function deleteUser(id) {
  return apiClient.delete(`/api/users/${id}`)
}
