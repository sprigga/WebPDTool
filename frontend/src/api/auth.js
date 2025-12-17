import apiClient from './client'

/**
 * User login
 * @param {string} username
 * @param {string} password
 * @returns {Promise}
 */
export function login(username, password) {
  return apiClient.post('/api/auth/login', {
    username,
    password
  })
}

/**
 * User logout
 * @returns {Promise}
 */
export function logout() {
  return apiClient.post('/api/auth/logout')
}

/**
 * Get current user info
 * @returns {Promise}
 */
export function getCurrentUser() {
  return apiClient.get('/api/auth/me')
}

/**
 * Refresh token
 * @returns {Promise}
 */
export function refreshToken() {
  return apiClient.post('/api/auth/refresh')
}
