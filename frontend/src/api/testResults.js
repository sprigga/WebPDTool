import apiClient from './client'

export const queryTestSessions = (params = {}) => {
  return apiClient.get('/api/tests/sessions', { params })
}

export const getSessionWithResults = (sessionId) => {
  return apiClient.get(`/api/tests/sessions/${sessionId}/results`)
}

export const deleteTestSessions = (sessionIds) => {
  return apiClient.delete('/api/tests/sessions', { data: { session_ids: sessionIds } })
}

export const exportTestResults = (params = {}) => {
  return apiClient.get('/api/tests/sessions/export', {
    params,
    responseType: 'blob'
  })
}
