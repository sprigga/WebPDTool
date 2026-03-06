import apiClient from './client'

export const queryTestSessions = (params = {}) => {
  return apiClient.get('/api/tests/sessions', { params })
}

export const getSessionWithResults = (sessionId) => {
  return apiClient.get(`/api/tests/sessions/${sessionId}/results`)
}

export const exportTestResults = (params = {}) => {
  return apiClient.get('/api/tests/sessions/export', {
    params,
    responseType: 'blob'
  })
}
