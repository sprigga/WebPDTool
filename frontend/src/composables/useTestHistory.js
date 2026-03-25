// frontend/src/composables/useTestHistory.js
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { queryTestSessions } from '@/api/testResults'
import { formatDateKey } from '@/utils/dateHelpers'

export function useTestHistory() {
  const sessions = ref([])
  const loading = ref(false)
  const error = ref(null)

  // Group sessions by date for timeline view
  const sessionsByDate = computed(() => {
    const grouped = {}
    sessions.value.forEach(session => {
      const dateKey = formatDateKey(session.start_time)
      if (!dateKey) return
      if (!grouped[dateKey]) {
        grouped[dateKey] = []
      }
      grouped[dateKey].push(session)
    })
    return grouped
  })

  // Calculate daily statistics
  const dailyStats = computed(() => {
    const stats = {}
    Object.entries(sessionsByDate.value).forEach(([date, daySessions]) => {
      stats[date] = {
        total: daySessions.length,
        pass: daySessions.filter(s => s.final_result === 'PASS').length,
        fail: daySessions.filter(s => s.final_result === 'FAIL').length,
        abort: daySessions.filter(s => s.final_result === 'ABORT').length
      }
    })
    return stats
  })

  // Fetch sessions with date range and improved error handling
  const fetchSessions = async (params) => {
    loading.value = true
    error.value = null
    try {
      const data = await queryTestSessions(params)
      sessions.value = Array.isArray(data) ? data : []

      // User feedback for empty results (non-blocking)
      if (sessions.value.length === 0) {
        error.value = 'No sessions found for the selected criteria'
      }
    } catch (err) {
      // Extract meaningful error message from response
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to load sessions'
      error.value = errorMsg
      sessions.value = []
      ElMessage.error(errorMsg)
    } finally {
      loading.value = false
    }
  }

  return {
    sessions,
    sessionsByDate,
    dailyStats,
    loading,
    error,
    fetchSessions
  }
}
