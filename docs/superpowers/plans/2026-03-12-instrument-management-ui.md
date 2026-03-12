# Instrument Management UI Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a complete CRUD interface for instrument configuration management, matching the existing UI patterns in the WebPDTool application.

**Architecture:** Follow the established Vue 3 + Element Plus + Pinia pattern used by `UserManage.vue` and `ProjectManage.vue`. The backend API (`/api/instruments`) already exists with full CRUD support.

**Tech Stack:** Vue 3 (Composition API), Element Plus, Pinia, Axios, Vite

---

## Chunk 1: Frontend API Client Module

### Task 1: Create Instrument API Client

**Files:**
- Create: `frontend/src/api/instruments.js`

- [ ] **Step 1: Create the instruments API client file**

```javascript
// frontend/src/api/instruments.js
import apiClient from './client'

/**
 * Get all instruments
 * @param {boolean} enabledOnly - Return only enabled instruments
 * @returns {Promise}
 */
export function getInstruments(enabledOnly = false) {
  return apiClient.get('/api/instruments', {
    params: { enabled_only: enabledOnly }
  })
}

/**
 * Get instrument by ID
 * @param {string} instrumentId - Instrument ID (e.g. 'DAQ973A_1')
 * @returns {Promise}
 */
export function getInstrument(instrumentId) {
  return apiClient.get(`/api/instruments/${instrumentId}`)
}

/**
 * Create new instrument
 * @param {Object} data - Instrument data
 * @returns {Promise}
 */
export function createInstrument(data) {
  return apiClient.post('/api/instruments', data)
}

/**
 * Update instrument (partial update)
 * @param {string} instrumentId - Instrument ID
 * @param {Object} data - Updated instrument data
 * @returns {Promise}
 */
export function updateInstrument(instrumentId, data) {
  return apiClient.patch(`/api/instruments/${instrumentId}`, data)
}

/**
 * Delete instrument
 * @param {string} instrumentId - Instrument ID
 * @returns {Promise}
 */
export function deleteInstrument(instrumentId) {
  return apiClient.delete(`/api/instruments/${instrumentId}`)
}
```

- [ ] **Step 2: Verify file created correctly**

Run: `ls -la frontend/src/api/instruments.js`
Expected: File exists with content above

- [ ] **Step 3: Commit**

```bash
git add frontend/src/api/instruments.js
git commit -m "feat: add instruments API client module"
```

---

## Chunk 2: Pinia Store for Instruments

### Task 2: Create Instrument Store

**Files:**
- Create: `frontend/src/stores/instruments.js`

- [ ] **Step 1: Create the Pinia store file**

```javascript
// frontend/src/stores/instruments.js
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getInstruments, createInstrument, updateInstrument, deleteInstrument } from '@/api/instruments'

export const useInstrumentsStore = defineStore('instruments', () => {
  const instruments = ref([])
  const loading = ref(false)

  async function fetchInstruments(enabledOnly = false) {
    try {
      loading.value = true
      const data = await getInstruments(enabledOnly)
      instruments.value = data
      return data
    } catch (error) {
      console.error('Failed to fetch instruments:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  async function addInstrument(instrumentData) {
    try {
      loading.value = true
      await createInstrument(instrumentData)
      await fetchInstruments()
    } catch (error) {
      console.error('Failed to add instrument:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  async function modifyInstrument(instrumentId, instrumentData) {
    try {
      loading.value = true
      await updateInstrument(instrumentId, instrumentData)
      await fetchInstruments()
    } catch (error) {
      console.error('Failed to modify instrument:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  async function removeInstrument(instrumentId) {
    try {
      loading.value = true
      await deleteInstrument(instrumentId)
      await fetchInstruments()
    } catch (error) {
      console.error('Failed to remove instrument:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  return {
    instruments,
    loading,
    fetchInstruments,
    addInstrument,
    modifyInstrument,
    removeInstrument
  }
})
```

- [ ] **Step 2: Verify file created correctly**

Run: `ls -la frontend/src/stores/instruments.js`
Expected: File exists with content above

- [ ] **Step 3: Commit**

```bash
git add frontend/src/stores/instruments.js
git commit -m "feat: add instruments Pinia store"
```

---

## Chunk 3: Router Configuration

### Task 3: Add Instrument Management Route

**Files:**
- Modify: `frontend/src/router/index.js`

- [ ] **Step 1: Add instruments route to router**

Insert the following route object in the routes array (after `/users` route):

```javascript
  {
    path: '/instruments',
    name: 'InstrumentManage',
    component: () => import('@/views/InstrumentManage.vue'),
    meta: { requiresAuth: true }
  }
```

Insert at line 66 (after the `/users` route).

- [ ] **Step 2: Verify router syntax**

Run: `cd frontend && npm run build -- --mode development 2>&1 | head -20`
Expected: No syntax errors, build starts

- [ ] **Step 3: Commit**

```bash
git add frontend/src/router/index.js
git commit -m "feat: add instruments management route"
```

---

## Chunk 4: Navigation Bar Update

### Task 4: Add Instruments Button to Navigation Bar

**Files:**
- Modify: `frontend/src/components/AppNavBar.vue`

- [ ] **Step 1: Add instruments button to nav-buttons section**

Add the following button in the nav-buttons div (after "使用者管理" button):

```vue
          <el-button :type="buttonType('instruments')" size="default" :disabled="isCurrent('instruments')" @click="navigateTo('/instruments')">
            儀器管理
          </el-button>
```

Insert at line 20 (after the users button).

- [ ] **Step 2: Verify button renders**

The button should appear in the navigation bar with proper styling.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/AppNavBar.vue
git commit -m "feat: add instruments management button to navigation"
```

---

## Chunk 5: Instrument Management View Component

### Task 5: Create InstrumentManage.vue Component

**Files:**
- Create: `frontend/src/views/InstrumentManage.vue`

- [ ] **Step 1: Create the InstrumentManage.vue component**

```vue
<template>
  <div class="instrument-manage-container">
    <AppNavBar current-page="instruments" />

    <el-alert
      v-if="!isAdmin"
      title="僅供查看"
      description="您沒有管理權限，無法新增、編輯或刪除儀器設定"
      type="info"
      :closable="false"
      style="margin-bottom: 20px"
    />

    <el-card>
      <template #header>
        <div class="card-header">
          <h2>儀器管理</h2>
          <el-button
            v-if="isAdmin"
            type="primary"
            :icon="Plus"
            @click="handleAddInstrument"
          >
            新增儀器
          </el-button>
        </div>
      </template>

      <!-- Instruments Table -->
      <div v-if="instrumentsStore.instruments.length === 0 && !loading" class="empty-state">
        <el-empty description="尚無儀器資料，點擊「新增儀器」開始建立" />
      </div>
      <el-table
        v-else
        v-loading="loading"
        :data="instrumentsStore.instruments"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="instrument_id" label="儀器ID" width="150" fixed="left" />

        <el-table-column prop="name" label="儀器名稱" min-width="150" />

        <el-table-column prop="instrument_type" label="儀器類型" width="130">
          <template #default="{ row }">
            <el-tag size="small" type="info">{{ row.instrument_type }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column label="連線類型" width="130">
          <template #default="{ row }">
            <el-tag :type="getConnTypeColor(row.conn_type)" size="small">
              {{ getConnTypeLabel(row.conn_type) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="連線參數" min-width="200">
          <template #default="{ row }">
            <el-text size="small" type="info">{{ formatConnParams(row.conn_params) }}</el-text>
          </template>
        </el-table-column>

        <el-table-column label="狀態" width="80">
          <template #default="{ row }">
            <el-tag :type="row.enabled ? 'success' : 'info'" size="small">
              {{ row.enabled ? '啟用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="description" label="描述" min-width="150" show-overflow-tooltip />

        <el-table-column prop="created_at" label="建立時間" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-tooltip content="需要管理員權限" :disabled="isAdmin">
              <span>
                <el-button
                  size="small"
                  :disabled="!isAdmin"
                  @click="handleEditInstrument(row)"
                >
                  編輯
                </el-button>
              </span>
            </el-tooltip>
            <el-tooltip content="需要管理員權限" :disabled="isAdmin">
              <span>
                <el-button
                  size="small"
                  type="danger"
                  :disabled="!isAdmin"
                  @click="handleDeleteInstrument(row)"
                >
                  刪除
                </el-button>
              </span>
            </el-tooltip>
          </template>
        </el-table-column>
      </el-table>

      <div class="table-footer">
        <el-text>共 {{ instrumentsStore.instruments.length }} 個儀器</el-text>
      </div>
    </el-card>

    <!-- Instrument Create/Edit Dialog -->
    <el-dialog
      v-model="showInstrumentDialog"
      :title="editingInstrument.id ? '編輯儀器' : '新增儀器'"
      width="700px"
    >
      <el-form
        ref="instrumentFormRef"
        :model="editingInstrument"
        :rules="instrumentFormRules"
        label-width="120px"
      >
        <el-form-item label="儀器ID" prop="instrument_id">
          <el-input
            v-model="editingInstrument.instrument_id"
            placeholder="例如: DAQ973A_1"
            :disabled="!!editingInstrument.id"
          />
          <el-text size="small" type="info">唯一識別碼，建立後無法修改</el-text>
        </el-form-item>

        <el-form-item label="儀器名稱" prop="name">
          <el-input
            v-model="editingInstrument.name"
            placeholder="請輸入儀器名稱"
          />
        </el-form-item>

        <el-form-item label="儀器類型" prop="instrument_type">
          <el-select v-model="editingInstrument.instrument_type" placeholder="請選擇儀器類型" style="width: 100%" filterable>
            <el-option label="DAQ973A" value="DAQ973A" />
            <el-option label="DAQ6510" value="DAQ6510" />
            <el-option label="34970A" value="34970A" />
            <el-option label="2260B" value="2260B" />
            <el-option label="IT6723C" value="IT6723C" />
            <el-option label="Model2306" value="Model2306" />
            <el-option label="Model2303" value="Model2303" />
            <el-option label="MT8872A" value="MT8872A" />
            <el-option label="CMW100" value="CMW100" />
            <el-option label="SMCV100B" value="SMCV100B" />
            <el-option label="N5182A" value="N5182A" />
            <el-option label="APS7050" value="APS7050" />
            <el-option label="PSW3072" value="PSW3072" />
            <el-option label="Keithley2015" value="Keithley2015" />
            <el-option label="MDO34" value="MDO34" />
            <el-option label="AnalogDiscovery2" value="AnalogDiscovery2" />
            <el-option label="PeakCAN" value="PeakCAN" />
            <el-option label="ConsoleCommand" value="ConsoleCommand" />
            <el-option label="ComPortCommand" value="ComPortCommand" />
            <el-option label="TCPIPCommand" value="TCPIPCommand" />
            <el-option label="WaitTest" value="WaitTest" />
          </el-select>
        </el-form-item>

        <el-form-item label="連線類型" prop="conn_type">
          <el-select v-model="editingInstrument.conn_type" placeholder="請選擇連線類型" style="width: 100%">
            <el-option label="VISA" value="VISA" />
            <el-option label="SERIAL" value="SERIAL" />
            <el-option label="TCPIP_SOCKET" value="TCPIP_SOCKET" />
            <el-option label="GPIB" value="GPIB" />
            <el-option label="LOCAL" value="LOCAL" />
          </el-select>
        </el-form-item>

        <!-- Dynamic connection parameters based on conn_type -->
        <template v-if="editingInstrument.conn_type === 'VISA'">
          <el-form-item label="VISA位址" prop="conn_params.address">
            <el-input
              v-model="editingInstrument.conn_params.address"
              placeholder="例如: TCPIP0::192.168.1.100::inst0::INSTR"
            />
            <el-text size="small" type="info">VISA資源字串</el-text>
          </el-form-item>
        </template>

        <template v-if="editingInstrument.conn_type === 'SERIAL'">
          <el-form-item label="連線埠" prop="conn_params.port">
            <el-input
              v-model="editingInstrument.conn_params.port"
              placeholder="例如: /dev/ttyUSB0 或 COM3"
            />
          </el-form-item>
          <el-form-item label="鮑率" prop="conn_params.baudrate">
            <el-select v-model="editingInstrument.conn_params.baudrate" placeholder="請選擇鮑率" style="width: 100%">
              <el-option label="9600" :value="9600" />
              <el-option label="19200" :value="19200" />
              <el-option label="38400" :value="38400" />
              <el-option label="57600" :value="57600" />
              <el-option label="115200" :value="115200" />
            </el-select>
          </el-form-item>
          <el-form-item label="資料位元">
            <el-input-number v-model="editingInstrument.conn_params.databits" :min="5" :max="8" :value="8" />
          </el-form-item>
          <el-form-item label="停止位元">
            <el-input-number v-model="editingInstrument.conn_params.stopbits" :min="1" :max="2" :value="1" />
          </el-form-item>
          <el-form-item label="同位檢查">
            <el-select v-model="editingInstrument.conn_params.parity" style="width: 100%">
              <el-option label="None" value="N" />
              <el-option label="Odd" value="O" />
              <el-option label="Even" value="E" />
            </el-select>
          </el-form-item>
        </template>

        <template v-if="editingInstrument.conn_type === 'TCPIP_SOCKET'">
          <el-form-item label="IP位址" prop="conn_params.host">
            <el-input
              v-model="editingInstrument.conn_params.host"
              placeholder="例如: 192.168.1.100"
            />
          </el-form-item>
          <el-form-item label="連線埠" prop="conn_params.port">
            <el-input-number v-model="editingInstrument.conn_params.port" :min="1" :max="65535" />
          </el-form-item>
        </template>

        <template v-if="editingInstrument.conn_type === 'GPIB'">
          <el-form-item label="GPIB位址" prop="conn_params.address">
            <el-input
              v-model="editingInstrument.conn_params.address"
              placeholder="例如: GPIB0::10::INSTR"
            />
          </el-form-item>
        </template>

        <template v-if="editingInstrument.conn_type === 'LOCAL'">
          <el-form-item label="本地指令">
            <el-input
              v-model="editingInstrument.conn_params.command"
              type="textarea"
              placeholder="本地執行的指令或腳本路徑"
            />
          </el-form-item>
        </template>

        <el-form-item label="描述">
          <el-input
            v-model="editingInstrument.description"
            type="textarea"
            :rows="3"
            placeholder="請輸入儀器描述(選填)"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="狀態">
          <el-switch
            v-model="editingInstrument.enabled"
            active-text="啟用"
            inactive-text="停用"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showInstrumentDialog = false">取消</el-button>
        <el-button
          type="primary"
          :loading="saving"
          @click="handleSaveInstrument"
        >
          儲存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useInstrumentsStore } from '@/stores/instruments'
import { useAuthStore } from '@/stores/auth'
import { createInstrument, updateInstrument, deleteInstrument } from '@/api/instruments'
import AppNavBar from '@/components/AppNavBar.vue'

const authStore = useAuthStore()
const instrumentsStore = useInstrumentsStore()

// State
const loading = ref(false)
const saving = ref(false)

// Computed
const currentUser = computed(() => authStore.user)
const isAdmin = computed(() => currentUser.value?.role === 'admin')

// Dialog state
const showInstrumentDialog = ref(false)
const instrumentFormRef = ref(null)

// Form data
const editingInstrument = reactive({
  id: null,
  instrument_id: '',
  name: '',
  instrument_type: '',
  conn_type: 'VISA',
  conn_params: {},
  description: '',
  enabled: true
})

// Connection type options
const connTypeOptions = [
  { label: 'VISA', value: 'VISA' },
  { label: 'SERIAL', value: 'SERIAL' },
  { label: 'TCPIP_SOCKET', value: 'TCPIP_SOCKET' },
  { label: 'GPIB', value: 'GPIB' },
  { label: 'LOCAL', value: 'LOCAL' }
]

// Form validation rules
const instrumentFormRules = {
  instrument_id: [
    { required: true, message: '請輸入儀器ID', trigger: 'blur' },
    { min: 2, max: 64, message: '儀器ID長度在 2 到 64 個字元', trigger: 'blur' },
    {
      pattern: /^[a-zA-Z0-9_-]+$/,
      message: '只能包含字母、數字、底線和破折號',
      trigger: 'blur'
    }
  ],
  name: [
    { required: true, message: '請輸入儀器名稱', trigger: 'blur' },
    { min: 2, max: 128, message: '儀器名稱長度在 2 到 128 個字元', trigger: 'blur' }
  ],
  instrument_type: [
    { required: true, message: '請選擇儀器類型', trigger: 'change' }
  ],
  conn_type: [
    { required: true, message: '請選擇連線類型', trigger: 'change' }
  ]
}

// Watch for conn_type changes to reset conn_params
const handleConnTypeChange = (newConnType) => {
  // Reset conn_params based on connection type
  switch (newConnType) {
    case 'VISA':
      editingInstrument.conn_params = { address: '' }
      break
    case 'SERIAL':
      editingInstrument.conn_params = { port: '', baudrate: 9600, databits: 8, stopbits: 1, parity: 'N' }
      break
    case 'TCPIP_SOCKET':
      editingInstrument.conn_params = { host: '', port: 5025 }
      break
    case 'GPIB':
      editingInstrument.conn_params = { address: '' }
      break
    case 'LOCAL':
      editingInstrument.conn_params = { command: '' }
      break
    default:
      editingInstrument.conn_params = {}
  }
}

// Helper functions
const getConnTypeColor = (connType) => {
  const colors = {
    VISA: 'primary',
    SERIAL: 'success',
    TCPIP_SOCKET: 'warning',
    GPIB: 'danger',
    LOCAL: 'info'
  }
  return colors[connType] || 'info'
}

const getConnTypeLabel = (connType) => {
  const labels = {
    VISA: 'VISA',
    SERIAL: '序列埠',
    TCPIP_SOCKET: 'TCP/IP',
    GPIB: 'GPIB',
    LOCAL: '本地'
  }
  return labels[connType] || connType
}

const formatConnParams = (params) => {
  if (!params) return '-'
  const formatted = []
  if (params.address) formatted.push(`addr: ${params.address}`)
  if (params.host) formatted.push(`host: ${params.host}`)
  if (params.port) formatted.push(`port: ${params.port}`)
  if (params.baudrate) formatted.push(`baud: ${params.baudrate}`)
  if (params.command) formatted.push(`cmd: ${params.command}`)
  return formatted.length > 0 ? formatted.join(', ') : '-'
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleString('zh-TW', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Handlers
const handleAddInstrument = () => {
  Object.assign(editingInstrument, {
    id: null,
    instrument_id: '',
    name: '',
    instrument_type: '',
    conn_type: 'VISA',
    conn_params: { address: '' },
    description: '',
    enabled: true
  })
  showInstrumentDialog.value = true
}

const handleEditInstrument = (row) => {
  Object.assign(editingInstrument, {
    id: row.id,
    instrument_id: row.instrument_id,
    name: row.name,
    instrument_type: row.instrument_type,
    conn_type: row.conn_type,
    conn_params: { ...row.conn_params },
    description: row.description || '',
    enabled: row.enabled
  })
  showInstrumentDialog.value = true
}

const handleDeleteInstrument = async (row) => {
  try {
    await ElMessageBox.confirm(
      `確定要刪除儀器 "${row.name}" 嗎？此操作無法復原。`,
      '確認刪除',
      {
        confirmButtonText: '確定',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger'
      }
    )

    loading.value = true
    await deleteInstrument(row.instrument_id)
    ElMessage.success('儀器刪除成功')
    await instrumentsStore.fetchInstruments()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Delete instrument failed:', error)
      const message = error.response?.data?.detail || '刪除失敗'
      ElMessage.error(message)
    }
  } finally {
    loading.value = false
  }
}

const handleSaveInstrument = async () => {
  if (!instrumentFormRef.value) return

  await instrumentFormRef.value.validate(async (valid) => {
    if (!valid) return

    saving.value = true
    try {
      const instrumentData = {
        instrument_id: editingInstrument.instrument_id,
        name: editingInstrument.name,
        instrument_type: editingInstrument.instrument_type,
        conn_type: editingInstrument.conn_type,
        conn_params: editingInstrument.conn_params,
        enabled: editingInstrument.enabled,
        description: editingInstrument.description || null
      }

      if (editingInstrument.id) {
        // Update existing instrument (use PATCH, exclude instrument_id)
        const { instrument_id, ...updateData } = instrumentData
        await updateInstrument(editingInstrument.instrument_id, updateData)
        ElMessage.success('儀器更新成功')
      } else {
        // Create new instrument
        await createInstrument(instrumentData)
        ElMessage.success('儀器建立成功')
      }

      showInstrumentDialog.value = false
      loading.value = true
      try {
        await instrumentsStore.fetchInstruments()
      } finally {
        loading.value = false
      }
    } catch (error) {
      console.error('Save instrument failed:', error)
      const message = error.response?.data?.detail || '操作失敗'
      ElMessage.error(message)
    } finally {
      saving.value = false
    }
  })
}

onMounted(async () => {
  loading.value = true
  try {
    await instrumentsStore.fetchInstruments()
  } catch (error) {
    console.error('Failed to load instruments:', error)
    ElMessage.error('載入儀器列表失敗')
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.instrument-manage-container {
  padding: 20px;
  min-height: calc(100vh - 40px);
  display: flex;
  flex-direction: column;
  gap: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h2 {
  margin: 0;
  font-size: 20px;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
}

.table-footer {
  margin-top: 16px;
  text-align: right;
}

/* Main card stretches to fill space */
.instrument-manage-container > .el-card:last-of-type {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.instrument-manage-container > .el-card:last-of-type :deep(.el-card__body) {
  flex: 1;
  overflow: auto;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .instrument-manage-container {
    padding: 10px;
  }
}

/* Improve table action column spacing */
:deep(.el-table .el-button + .el-button) {
  margin-left: 4px;
}
</style>
```

- [ ] **Step 2: Verify file created correctly**

Run: `ls -la frontend/src/views/InstrumentManage.vue`
Expected: File exists with content above

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/InstrumentManage.vue
git commit -m "feat: add instrument management UI with CRUD operations"
```

---

## Chunk 6: Testing and Verification

### Task 6: Manual Testing

**Files:**
- None (runtime verification)

- [ ] **Step 1: Start frontend dev server**

Run: `cd frontend && npm run dev`
Expected: Server starts on http://localhost:5173

- [ ] **Step 2: Navigate to instruments page**

Open browser to http://localhost:5173/instruments
Expected: Page loads with instruments table

- [ ] **Step 3: Test create operation**

1. Click "新增儀器" button
2. Fill form with test data:
   - 儀器ID: `TEST_INSTRUMENT_1`
   - 儀器名稱: `測試儀器`
   - 儀器類型: `DAQ973A`
   - 連線類型: `TCPIP_SOCKET`
   - IP位址: `192.168.1.100`
   - 連線埠: `5025`
3. Click "儲存"
Expected: Success message, instrument appears in table

- [ ] **Step 4: Test read operation**

Expected: Created instrument appears in table with all fields displayed correctly

- [ ] **Step 5: Test update operation**

1. Click "編輯" on the test instrument
2. Modify 儀器名稱 to `測試儀器 (已更新)`
3. Click "儲存"
Expected: Success message, instrument name updated in table

- [ ] **Step 6: Test delete operation**

1. Click "刪除" on the test instrument
2. Confirm deletion
Expected: Success message, instrument removed from table

- [ ] **Step 7: Test permission control**

1. Login as non-admin user (engineer or operator)
2. Navigate to /instruments
Expected: Alert shown "僅供查看", buttons disabled

- [ ] **Step 8: Test conn_type parameter switching**

1. Click "新增儀器"
2. Switch between different 連線類型 options
Expected: Form fields change dynamically based on selected type

- [ ] **Step 9: Verify backend API still works**

Run: `curl -X GET http://localhost:9100/api/instruments`
Expected: JSON array of instruments returned

---

## Chunk 7: Documentation Update

### Task 7: Update CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Add instrument management section to CLAUDE.md**

Add the following section after "User Management" section:

```markdown
## Managing Instruments

Instrument management allows administrators to configure test instrument connections used during testing.

**File Locations:**
- Backend API: `backend/app/api/instruments.py` - Instrument CRUD endpoints
- Backend Schemas: `backend/app/schemas/instrument.py` - Instrument data validation schemas
- Backend Models: `backend/app/models/instrument.py` - Instrument ORM model
- Backend Repository: `backend/app/repositories/instrument_repository.py` - Database operations
- Frontend View: `frontend/src/views/InstrumentManage.vue` - Instrument management UI
- Frontend Store: `frontend/src/stores/instruments.js` - Instrument state management
- Frontend API: `frontend/src/api/instruments.js` - Instrument API client functions

**Instrument Connection Types:**
- `VISA` - VISA resource string (e.g., TCPIP0::192.168.1.100::inst0::INSTR)
- `SERIAL` - Serial port (port, baudrate, databits, stopbits, parity)
- `TCPIP_SOCKET` - TCP/IP socket connection (host, port)
- `GPIB` - GPIB interface (address)
- `LOCAL` - Local command execution

**API Endpoints Summary:**
- `GET /api/instruments` - List instruments (optional: enabled_only=true)
- `GET /api/instruments/{instrument_id}` - Get specific instrument
- `POST /api/instruments` - Create new instrument (admin only)
- `PATCH /api/instruments/{instrument_id}` - Update instrument (admin only; instrument_id excluded)
- `DELETE /api/instruments/{instrument_id}` - Delete instrument (admin only)

**Supported Instrument Types:**
- DAQ973A, DAQ6510, 34970A, 2260B, IT6723C, Model2306, Model2303
- MT8872A, CMW100, SMCV100B, N5182A, APS7050, PSW3072
- Keithley2015, MDO34, AnalogDiscovery2, PeakCAN
- ConsoleCommand, ComPortCommand, TCPIPCommand, WaitTest
```

Insert at appropriate location in CLAUDE.md (after User Management section).

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: add instrument management documentation"
```

---

## Completion Checklist

- [ ] All chunks completed
- [ ] All tests pass
- [ ] Code follows existing patterns
- [ ] Documentation updated
- [ ] No console errors in browser
- [ ] API calls successful
- [ ] Responsive design works
- [ ] Chinese labels consistent with other pages

## Notes for Implementation

1. **Backend API Already Exists**: The `/api/instruments` endpoints are already implemented. Do NOT modify backend code.

2. **Connection Parameters (conn_params)**: This is a JSON field in the database. The frontend must handle different parameter structures based on `conn_type`:
   - VISA: `{ "address": "TCPIP0::192.168.1.100::inst0::INSTR" }`
   - SERIAL: `{ "port": "/dev/ttyUSB0", "baudrate": 9600, "databits": 8, "stopbits": 1, "parity": "N" }`
   - TCPIP_SOCKET: `{ "host": "192.168.1.100", "port": 5025 }`
   - GPIB: `{ "address": "GPIB0::10::INSTR" }`
   - LOCAL: `{ "command": "/path/to/script" }`

3. **Permission Control**: Only admin users can create, edit, or delete instruments. Non-admin users get read-only view.

4. **Instrument ID is Immutable**: The `instrument_id` field is the unique logical key and cannot be changed after creation. The update form should disable this field.

5. **PATCH vs PUT**: The backend uses PATCH for updates, so only send changed fields. Do NOT include `instrument_id` in update payload.

6. **Error Handling**: Use ElMessage for displaying success/error messages consistent with other pages.

7. **Consistent Styling**: Follow the exact CSS patterns from UserManage.vue and ProjectManage.vue for layout and responsive design.
