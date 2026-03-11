# 04 - 前端結構

## 目錄結構

```
frontend/
├── src/
│   ├── main.js                      # 應用入口
│   ├── App.vue                      # 根元件
│   │
│   ├── views/                       # 頁面級元件 (10 個)
│   │   ├── Login.vue                # 登入頁
│   │   ├── TestMain.vue             # 測試執行 (核心 UI)
│   │   ├── TestPlanManage.vue       # 測試計劃管理
│   │   ├── ProjectManage.vue        # 專案管理
│   │   ├── UserManage.vue           # 使用者管理 (管理員)
│   │   ├── TestResults.vue          # 結果查詢
│   │   ├── TestHistory.vue          # 歷史記錄
│   │   ├── ReportAnalysis.vue       # 報表分析 (ECharts)
│   │   ├── TestExecution.vue        # 執行監控
│   │   └── SystemConfig.vue         # 系統配置
│   │
│   ├── components/                  # 可複用元件
│   │   ├── (業務相關的小元件)
│   │   └── ...
│   │
│   ├── stores/                      # Pinia 全域性狀態 (3 個)
│   │   ├── auth.js                  # 認證狀態
│   │   ├── project.js               # 專案選擇
│   │   └── users.js                 # 使用者列表
│   │
│   ├── api/                         # API 用戶端
│   │   ├── client.js                # 全域性 axios 配置
│   │   ├── auth.js                  # 認證 api
│   │   ├── users.js                 # 使用者 api
│   │   ├── projects.js              # 專案 api
│   │   ├── tests.js                 # 測試 api
│   │   ├── measurements.js          # 測量 api
│   │   └── results.js               # 結果 api
│   │
│   ├── router/                      # Vue Router 配置
│   │   └── index.js
│   │
│   ├── composables/                 # 可複用邏輯 (hooks)
│   │   └── (業務邏輯函式)
│   │
│   ├── utils/                       # 工具函式
│   │   └── (格式化、驗證等)
│   │
│   ├── assets/                      # 靜態資源
│   │   ├── (樣式表)
│   │   └── (圖片等)
│   │
│   └── plugins/                     # 第三方插件
│       └── (Element Plus 等)
│
├── index.html                       # HTML 入口
├── vite.config.js                   # Vite 配置
├── package.json                     # 依賴管理
├── Dockerfile                       # Docker 構建
├── nginx.conf                       # Nginx 配置
└── .env                             # 環境變數
```

## 核心技術棧

```javascript
// Vue 3 + Composition API
import { ref, computed, onMounted } from 'vue'

// Pinia 狀態管理
import { defineStore } from 'pinia'

// Axios HTTP 用戶端
import axios from 'axios'

// Element Plus UI 元件
import { ElMessage, ElMessageBox } from 'element-plus'

// ECharts 資料可視化
import { use } from 'echarts/core'
import { BarChart, LineChart } from 'echarts/charts'

// Vue Router 路由
import { useRouter } from 'vue-router'
```

## View 元件詳解

### 1. Login.vue (未認證使用者)

**功能:**
- 使用者名稱/密碼表單
- 表單驗證
- JWT token 獲取

**關鍵邏輯:**
```javascript
async function handleLogin() {
  const response = await apiLogin(username.value, password.value)
  authStore.login(response.access_token, response.user)
  router.push('/test-main')
}
```

### 2. TestMain.vue (核心測試 UI - PDTool4 克隆)

**功能:**
- 選擇專案/工站/序列號
- 啟動測試 session
- 實時監控 test items
- 顯示實時結果 (PASS/FAIL/ERROR)
- runAllTest 模式選項
- 錯誤彙總顯示

**關鍵特性:**
```javascript
// 實時更新
onMounted(async () => {
  startTestSession()
  // 定期查詢執行狀態
  setInterval(queryStatus, 1000)
})

// 錯誤收集 (runAllTest 模式)
if (runAllTest) {
  errors.push(error)
  continue  // 繼續下一項
} else {
  break     // 停止
}

// UI 顯示
├─ 測試進度條
├─ 當前專案/工站/產品 SN
├─ Test Items 列表
│   ├─ Item 號
│   ├─ Item 名稱
│   ├─ 測試狀態 (PENDING/RUNNING/PASS/FAIL)
│   └─ 測量值
├─ runAllTest 開關
└─ 錯誤彙總 (底部)
```

### 3. TestPlanManage.vue (測試計劃 CRUD)

**功能:**
- 列表展示 test plans
- 新建/編輯 test plan
- CSV 檔案匯入
- 刪除 test plan
- 引數編輯

**表單欄位:**
```
- Item 號 (item_no)
- Item 名稱 (item_name)
- 測試型別 (test_type: PowerRead/PowerSet/...)
- 下限值 (lower_limit)
- 上限值 (upper_limit)
- 期望值 (expected_value)
- 限制型別 (limit_type: lower/upper/both/...)
- 值型別 (value_type: string/integer/float)
- 測量引數 (parameters JSON)
```

**CSV 匯入:**
```javascript
handleImport() {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('project_id', projectId)
  formData.append('station_id', stationId)

  await apiImportTestPlan(formData)
  ElMessage.success('匯入成功')
}
```

### 4. ProjectManage.vue (專案和工站管理)

**功能:**
- 建立/編輯/刪除專案
- 管理工站
- 關聯工站和專案

**UI 層次:**
```
Projects
├─ Project 1
│  ├─ Station A
│  │  └─ test_plans
│  └─ Station B
│     └─ test_plans
└─ Project 2
   └─ Stations...
```

### 5. UserManage.vue (使用者 CRUD - 管理員)

**功能:**
- 列表使用者 (分頁)
- 建立新使用者
- 編輯使用者資訊
- 重置密碼
- 刪除使用者
- 啟用/禁用賬戶

**欄位:**
```
- 使用者名稱 (username)
- 密碼 (password)
- 全名 (full_name)
- 郵箱 (email)
- 角色 (role: ADMIN/ENGINEER/OPERATOR)
- 啟用狀態 (is_active)
```

**角色限制:**
```javascript
// 其他管理員可管理所有使用者
// 不能刪除自己
const canDelete = (user) => user.id !== currentUser.id && isAdmin
```

### 6. TestResults.vue (結果查詢)

**功能:**
- 搜尋/過濾測試結果
- 分頁展示
- 匯出 CSV/PDF
- 檢視細節

**搜尋欄位:**
```
- 專案 (project_id)
- 工站 (station_id)
- 序列號 (serial_number)
- 時間範圍 (date_range)
- 結果狀態 (validation_result: PASS/FAIL)
- Item 號 (item_no)
```

### 7. TestHistory.vue (歷史 session)

**功能:**
- 列表過去的 test sessions
- 顯示執行時間、結果統計
- 檢視詳細結果

**展示:**
```
Sessions List
├─ Session 1
│  ├─ 專案/工站
│  ├─ 序列號
│  ├─ 開始/結束時間
│  ├─ 最終結果 (PASS/FAIL/ABORT)
│  └─ 統計 (PASS 數/FAIL 數)
└─ Session 2
   └─ ...
```

### 8. ReportAnalysis.vue (報表和圖表)

**功能:**
- ECharts 資料可視化
- 合格率統計
- 趨勢分析
- 專案/模組排行

**圖表型別:**
```javascript
// 柱狀圖：專案合格率
BarChart data = {
  categories: ['Project1', 'Project2', ...],
  passRate: [95, 87, ...],
  failRate: [5, 13, ...]
}

// 折線圖：合格率趨勢
LineChart data = {
  dates: ['2026-01-01', ...],
  passRate: [92, 93, 95, ...]
}

// 餅圖：整體結果分佈
PieChart data = {
  PASS: 8540,
  FAIL: 324
}
```

### 9. TestExecution.vue (執行監控)

**功能:**
- 實時 test session 進度
- 控制按鈕 (Pause/Resume/Abort)
- 當前 item 顯示
- 日誌輸出

### 10. SystemConfig.vue (系統配置)

**功能:**
- 硬體配置管理
- 日誌級別設定
- 超時引數配置
- Redis 日誌開關

## Pinia 狀態管理

### auth.js (認證狀態)

```javascript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as apiLogin } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  // 狀態
  const token = ref(localStorage.getItem('token') || null)
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))

  // 計算屬性
  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'ADMIN')
  const isEngineer = computed(() => user.value?.role === 'ENGINEER')

  // 方法
  async function login(username, password) {
    const response = await apiLogin(username, password)
    token.value = response.access_token
    user.value = response.user

    // 持久化到 localStorage
    localStorage.setItem('token', response.access_token)
    localStorage.setItem('user', JSON.stringify(response.user))
  }

  async function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  return { token, user, isAuthenticated, isAdmin, login, logout }
})
```

### project.js (專案選擇)

```javascript
export const useProjectStore = defineStore('project', () => {
  const projects = ref([])
  const currentProject = ref(null)
  const currentStation = ref(null)

  async function fetchProjects() {
    const response = await apiGetProjects()
    projects.value = response
  }

  function setCurrentProject(project) {
    currentProject.value = project
    currentStation.value = null  // 重置工站
  }

  return {
    projects,
    currentProject,
    currentStation,
    fetchProjects,
    setCurrentProject
  }
})
```

### users.js (使用者列表)

```javascript
export const useUsersStore = defineStore('users', () => {
  const users = ref([])

  async function fetchUsers(filters = {}) {
    const response = await apiGetUsers(filters)
    users.value = response
  }

  async function createUser(userData) {
    const response = await apiCreateUser(userData)
    users.value.push(response)
  }

  async function updateUser(id, userData) {
    const response = await apiUpdateUser(id, userData)
    const index = users.value.findIndex(u => u.id === id)
    users.value[index] = response
  }

  async function deleteUser(id) {
    await apiDeleteUser(id)
    users.value = users.value.filter(u => u.id !== id)
  }

  return { users, fetchUsers, createUser, updateUser, deleteUser }
})
```

## API 用戶端設計

### client.js (全域性配置)

```javascript
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

// 建立 axios 例項
const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:9100'
})

// 請求攔截器 - 新增 JWT
client.interceptors.request.use(config => {
  const authStore = useAuthStore()
  if (authStore.token) {
    config.headers.Authorization = `Bearer ${authStore.token}`
  }
  return config
})

// 響應攔截器 - 錯誤處理
client.interceptors.response.use(
  response => response.data,
  error => {
    // 401: 認證失敗
    if (error.response?.status === 401) {
      useAuthStore().logout()
      location.href = '/login'
    }

    // 顯示錯誤訊息
    const message = error.response?.data?.detail || '請求失敗'
    ElMessage.error(message)

    throw error
  }
)

export default client
```

### tests.js (測試 API 用戶端)

```javascript
import client from './client'

// 啟動測試 session
export async function startTestSession(data) {
  return client.post('/api/tests/sessions/start', data)
}

// 獲取 session 狀態
export async function getSessionStatus(sessionId) {
  return client.get(`/api/tests/sessions/${sessionId}/status`)
}

// 獲取 session 結果
export async function getSessionResults(sessionId) {
  return client.get(`/api/tests/sessions/${sessionId}/results`)
}

// 暫停 session
export async function pauseSession(sessionId) {
  return client.post(`/api/tests/sessions/${sessionId}/pause`)
}

// 中止 session
export async function abortSession(sessionId) {
  return client.post(`/api/tests/sessions/${sessionId}/abort`)
}
```

## Router 配置

### router/index.js

```javascript
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    redirect: '/test-main'
  },
  {
    path: '/test-main',
    component: () => import('@/views/TestMain.vue')
  },
  {
    path: '/test-plan-manage',
    component: () => import('@/views/TestPlanManage.vue')
  },
  {
    path: '/project-manage',
    component: () => import('@/views/ProjectManage.vue')
  },
  {
    path: '/user-manage',
    component: () => import('@/views/UserManage.vue'),
    meta: { requiredRole: 'ADMIN' }
  },
  {
    path: '/test-results',
    component: () => import('@/views/TestResults.vue')
  },
  {
    path: '/test-history',
    component: () => import('@/views/TestHistory.vue')
  },
  {
    path: '/report-analysis',
    component: () => import('@/views/ReportAnalysis.vue')
  },
  {
    path: '/test-execution',
    component: () => import('@/views/TestExecution.vue')
  },
  {
    path: '/system-config',
    component: () => import('@/views/SystemConfig.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守衛
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  // 檢查認證
  if (to.meta.requiresAuth !== false && !authStore.isAuthenticated) {
    next('/login')
    return
  }

  // 檢查角色
  if (to.meta.requiredRole && authStore.user?.role !== to.meta.requiredRole) {
    next('/test-main')
    return
  }

  next()
})

export default router
```

## Element Plus 元件使用

```vue
<template>
  <!-- 按鈕 -->
  <el-button type="primary" @click="handleStart">開始測試</el-button>
  <el-button type="danger">停止</el-button>

  <!-- 表格 -->
  <el-table :data="tableData" stripe border>
    <el-table-column prop="item_no" label="項號" />
    <el-table-column prop="item_name" label="項名稱" />
    <el-table-column prop="result" label="結果">
      <template #default="{ row }">
        <el-tag :type="row.result === 'PASS' ? 'success' : 'danger'">
          {{ row.result }}
        </el-tag>
      </template>
    </el-table-column>
  </el-table>

  <!-- 表單 -->
  <el-form :model="form" label-width="100px">
    <el-form-item label="專案" prop="project_id">
      <el-select v-model="form.project_id" placeholder="選擇專案">
        <el-option label="Project1" value="1" />
      </el-select>
    </el-form-item>
  </el-form>

  <!-- 訊息 -->
  <el-message-box("刪除確認", "...", "warning")
  <el-message.success("成功")
</template>
```

## 樣式組織

```scss
// 全域性樣式 (assets/style.scss)
$primary-color: #409eff
$danger-color: #f56c6c
$success-color: #67c23a

// BEM 命名規範
.test-main
  .test-main__header
    .test-main__header-title
  .test-main__body
    .test-main__item-list
      .test-main__item
        &.pass
          color: $success-color
        &.fail
          color: $danger-color
```

## 關鍵設計模式

### 1. Composition API 使用

```javascript
import { ref, computed, onMounted } from 'vue'

export default {
  setup() {
    // 響應式狀態
    const count = ref(0)

    // 計算屬性
    const doubled = computed(() => count.value * 2)

    // 生命週期鉤子
    onMounted(() => {
      // 初始化邏輯
    })

    return { count, doubled }
  }
}
```

### 2. 非同步資料載入

```javascript
const loading = ref(false)
const data = ref(null)

async function fetch() {
  loading.value = true
  try {
    data.value = await api.getData()
  } finally {
    loading.value = false
  }
}
```

### 3. 表單驗證

```javascript
const formRef = ref(null)
const form = ref({...})

async function submitForm() {
  await formRef.value.validate()
  await apiSubmit(form.value)
}
```

## 效能優化

1. **路由懶載入** - 使用動態 import()
2. **元件分割** - 獨立小元件便於複用
3. **狀態快取** - Pinia 持久化 localStorage
4. **API 快取** - 避免重複請求
5. **虛擬滾動** - 大列表效能

## 下一步

- **瞭解 API**: [06-api-endpoints.md](06-api-endpoints.md)
- **學習資料庫**: [05-database-schema.md](05-database-schema.md)
- **開發指南**: [10-development-guide.md](10-development-guide.md)
