import axios from 'axios'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

// 修改: 使用空字串作為 baseURL,讓請求通過 Vite proxy
// Vite 會將 /api/* 請求代理到 http://localhost:9100
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore()
    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
apiClient.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    if (error.response) {
      const { status, data } = error.response

      switch (status) {
        case 401:
          ElMessage.error('未授權，請重新登入')
          const authStore = useAuthStore()
          authStore.logout()
          window.location.href = '/login'
          break
        case 403:
          ElMessage.error('權限不足')
          break
        case 404:
          ElMessage.error('請求的資源不存在')
          break
        case 500:
          ElMessage.error('伺服器錯誤')
          break
        default:
          ElMessage.error(data.detail || '請求失敗')
      }
    } else if (error.request) {
      ElMessage.error('網路錯誤，請檢查連線')
    } else {
      ElMessage.error('請求配置錯誤')
    }

    return Promise.reject(error)
  }
)

export default apiClient
