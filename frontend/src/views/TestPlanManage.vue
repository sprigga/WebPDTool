<template>
  <div class="testplan-manage-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <h2>測試計劃管理</h2>
          <div class="header-actions">
            <el-button
              type="primary"
              :icon="Upload"
              @click="handleShowUploadDialog"
            >
              上傳 CSV
            </el-button>
            <el-button
              type="success"
              :icon="Plus"
              :disabled="!selectedProject || !selectedStation"
              @click="handleAddItem"
            >
              新增項目
            </el-button>
            <el-button
              v-if="selectedItems.length > 0"
              type="danger"
              :icon="Delete"
              @click="handleBulkDelete"
            >
              刪除選中 ({{ selectedItems.length }})
            </el-button>
          </div>
        </div>
      </template>

      <!-- Project and Station Selection -->
      <el-card class="filter-card" shadow="never">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="選擇專案">
              <el-select
                v-model="selectedProjectId"
                placeholder="請選擇專案"
                style="width: 100%"
                filterable
                clearable
                @change="handleProjectSelect"
              >
                <el-option
                  v-for="project in projectStore.projects"
                  :key="project.id"
                  :label="`${project.project_code} - ${project.project_name}`"
                  :value="project.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="選擇站別">
              <el-select
                v-model="selectedStationId"
                placeholder="請選擇站別"
                style="width: 100%"
                filterable
                clearable
                :disabled="!selectedProjectId"
                @change="handleStationSelect"
              >
                <el-option
                  v-for="station in filteredStations"
                  :key="station.id"
                  :label="`${station.station_code} - ${station.station_name}`"
                  :value="station.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
      </el-card>

      <!-- Station Info -->
      <el-alert
        v-if="selectedStation"
        :title="`當前選擇: ${selectedProject?.project_code || ''} - ${selectedProject?.project_name || ''} / ${selectedStation.station_code} - ${selectedStation.station_name}`"
        type="info"
        :closable="false"
        style="margin-bottom: 20px"
      />

      <!-- Test Plan Table -->
      <el-table
        ref="testPlanTable"
        :data="testPlanItems"
        v-loading="loading"
        stripe
        @selection-change="handleSelectionChange"
        style="width: 100%"
      >
        <el-table-column type="selection" width="55" />

        <el-table-column prop="sequence_order" label="序號" width="80" sortable />

        <el-table-column prop="item_name" label="測試項目" min-width="150" />

        <el-table-column prop="item_key" label="項目鍵值" width="120" />

        <el-table-column prop="test_type" label="測試類型" width="120" />

        <el-table-column prop="execute_name" label="執行名稱" width="120" />

        <el-table-column prop="case_type" label="案例類型" width="100" />

        <el-table-column prop="value_type" label="數值類型" width="100" />

        <el-table-column prop="limit_type" label="限制類型" width="100" />

        <el-table-column label="限制值" width="180">
          <template #default="{ row }">
            <span v-if="row.lower_limit !== null || row.upper_limit !== null">
              {{ row.lower_limit ?? '-' }} ~ {{ row.upper_limit ?? '-' }}
            </span>
            <span v-else-if="row.eq_limit">= {{ row.eq_limit }}</span>
            <span v-else>-</span>
          </template>
        </el-table-column>

        <el-table-column prop="command" label="命令" min-width="200" show-overflow-tooltip />

        <el-table-column prop="timeout" label="超時(ms)" width="100" />

        <el-table-column prop="wait_msec" label="等待(ms)" width="100" />

        <el-table-column prop="use_result" label="使用結果" width="120" />

        <el-table-column label="狀態" width="80" fixed="right">
          <template #default="{ row }">
            <el-tag :type="row.enabled ? 'success' : 'info'">
              {{ row.enabled ? '啟用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="handleEditItem(row)">編輯</el-button>
            <el-button
              size="small"
              :type="row.enabled ? 'warning' : 'success'"
              @click="handleToggleEnabled(row)"
            >
              {{ row.enabled ? '停用' : '啟用' }}
            </el-button>
            <el-button
              size="small"
              type="danger"
              @click="handleDeleteItem(row)"
            >
              刪除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="table-footer">
        <el-text>共 {{ testPlanItems.length }} 個測試項目</el-text>
      </div>
    </el-card>

    <!-- CSV Upload Dialog -->
    <el-dialog
      v-model="showUploadDialog"
      title="上傳測試計劃 CSV"
      width="500px"
    >
      <el-form :model="uploadForm" label-width="120px">
        <!-- 新增: 選擇專案 -->
        <el-form-item label="選擇專案">
          <el-select
            v-model="uploadForm.projectId"
            placeholder="請選擇專案"
            style="width: 100%"
            filterable
            @change="handleProjectChange"
          >
            <el-option
              v-for="project in projectStore.projects"
              :key="project.id"
              :label="`${project.project_code} - ${project.project_name}`"
              :value="project.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="選擇站別">
          <el-select
            v-model="uploadForm.stationId"
            placeholder="請選擇站別"
            style="width: 100%"
            filterable
            :disabled="!uploadForm.projectId"
          >
            <el-option
              v-for="station in uploadFormFilteredStations"
              :key="station.id"
              :label="`${station.station_code} - ${station.station_name}`"
              :value="station.id"
            />
          </el-select>
        </el-form-item>

        <!-- 新增: 測試計劃名稱 -->
        <el-form-item label="測試計劃名稱">
          <el-input
            v-model="uploadForm.testPlanName"
            placeholder="請輸入測試計劃名稱(選填)"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="CSV 檔案">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            accept=".csv"
            :on-change="handleFileChange"
            :on-remove="handleFileRemove"
          >
            <el-button type="primary">選擇檔案</el-button>
            <template #tip>
              <div class="el-upload__tip">
                僅支援 CSV 格式檔案
              </div>
            </template>
          </el-upload>
        </el-form-item>

        <el-form-item label="處理方式">
          <el-radio-group v-model="uploadForm.replaceExisting">
            <el-radio :label="true">替換現有測試計劃</el-radio>
            <el-radio :label="false">附加到現有測試計劃</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showUploadDialog = false">取消</el-button>
        <el-button
          type="primary"
          :loading="uploading"
          :disabled="!uploadForm.file || !uploadForm.stationId || !uploadForm.projectId"
          @click="handleUpload"
        >
          上傳
        </el-button>
      </template>
    </el-dialog>

    <!-- Edit Item Dialog -->
    <el-dialog
      v-model="showEditDialog"
      :title="editingItem.id ? '編輯測試項目' : '新增測試項目'"
      width="800px"
    >
      <el-form
        ref="editFormRef"
        :model="editingItem"
        :rules="editFormRules"
        label-width="120px"
      >
        <el-divider content-position="left">基本資訊</el-divider>

        <!-- 新增: 測試計劃名稱欄位 -->
        <el-form-item label="測試計劃名稱">
          <el-input
            v-model="editingItem.test_plan_name"
            placeholder="請輸入測試計劃名稱(選填)"
          />
        </el-form-item>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="測試項目名稱" prop="item_name">
              <el-input v-model="editingItem.item_name" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="項目鍵值">
              <el-input v-model="editingItem.item_key" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="測試類型" prop="test_type">
              <el-input v-model="editingItem.test_type" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="執行名稱">
              <el-input v-model="editingItem.execute_name" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="案例類型">
              <el-input v-model="editingItem.case_type" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="序號" prop="sequence_order">
              <el-input-number v-model="editingItem.sequence_order" :min="1" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">數值與限制</el-divider>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="數值類型">
              <el-input v-model="editingItem.value_type" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="限制類型">
              <el-input v-model="editingItem.limit_type" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="下限值">
              <el-input-number
                v-model="editingItem.lower_limit"
                :precision="6"
                :controls="false"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="上限值">
              <el-input-number
                v-model="editingItem.upper_limit"
                :precision="6"
                :controls="false"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="等於限制">
              <el-input v-model="editingItem.eq_limit" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="單位">
              <el-input v-model="editingItem.unit" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="測量值">
              <el-input v-model="editingItem.measure_value" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">執行設定</el-divider>

        <el-form-item label="命令">
          <el-input v-model="editingItem.command" type="textarea" :rows="2" />
        </el-form-item>

        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="超時時間(ms)">
              <el-input-number v-model="editingItem.timeout" :min="0" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="等待時間(ms)">
              <el-input-number v-model="editingItem.wait_msec" :min="0" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="使用結果">
              <el-input v-model="editingItem.use_result" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="通過/失敗">
              <el-input v-model="editingItem.pass_or_fail" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="狀態">
              <el-switch
                v-model="editingItem.enabled"
                active-text="啟用"
                inactive-text="停用"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>

      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSaveItem">儲存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useProjectStore } from '@/stores/project'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload, Plus, Delete } from '@element-plus/icons-vue'
import {
  getStationTestPlan,
  uploadTestPlanCSV,
  createTestPlanItem,
  updateTestPlanItem,
  deleteTestPlanItem,
  bulkDeleteTestPlanItems
} from '@/api/testplans'

const projectStore = useProjectStore()
// const currentStation = computed(() => projectStore.currentStation)  // 原有程式碼: 使用 store 中的當前站別

// 新增: 使用本地狀態管理選擇的專案和站別,不依賴 store 的 currentProject/currentStation
const selectedProjectId = ref(null)
const selectedStationId = ref(null)

const selectedProject = computed(() => {
  if (!selectedProjectId.value) return null
  return projectStore.projects.find(p => p.id === selectedProjectId.value) || null
})

const selectedStation = computed(() => {
  if (!selectedStationId.value) return null
  return filteredStations.value.find(s => s.id === selectedStationId.value) || null
})

// 根據選擇的專案過濾站別(主篩選器)
const filteredStations = computed(() => {
  if (!selectedProjectId.value) return []
  return projectStore.stations.filter(station => station.project_id === selectedProjectId.value)
})

// 根據上傳表單的專案過濾站別(上傳對話框專用)
const uploadFormFilteredStations = computed(() => {
  if (!uploadForm.projectId) return []
  return projectStore.stations.filter(station => station.project_id === uploadForm.projectId)
})

const testPlanItems = ref([])
const selectedItems = ref([])
const loading = ref(false)
const uploading = ref(false)
const showUploadDialog = ref(false)
const showEditDialog = ref(false)

const uploadForm = reactive({
  file: null,
  projectId: null,  // 新增 projectId
  stationId: null,
  testPlanName: '',  // 新增 testPlanName
  replaceExisting: true
})

const editingItem = reactive({
  id: null,
  item_name: '',
  test_type: '',
  lower_limit: null,
  upper_limit: null,
  unit: '',
  sequence_order: 1,
  enabled: true,
  // 新增欄位
  item_key: '',
  value_type: '',
  limit_type: '',
  eq_limit: '',
  pass_or_fail: '',
  measure_value: '',
  execute_name: '',
  case_type: '',
  command: '',
  timeout: null,
  use_result: '',
  wait_msec: null,
  // 新增: 測試計劃名稱欄位
  test_plan_name: ''
})

const editFormRules = {
  item_name: [{ required: true, message: '請輸入測試項目名稱', trigger: 'blur' }],
  test_type: [{ required: true, message: '請輸入測試類型', trigger: 'blur' }],
  sequence_order: [{ required: true, message: '請輸入序號', trigger: 'blur' }]
}

const uploadRef = ref(null)
const editFormRef = ref(null)
const testPlanTable = ref(null)

// 新增: 處理專案選擇變更
const handleProjectSelect = async (projectId) => {
  // 清空站別選擇
  selectedStationId.value = null

  // 載入該專案的站別列表
  if (projectId) {
    try {
      await projectStore.fetchProjectStations(projectId)
    } catch (error) {
      console.error('Failed to load stations:', error)
      ElMessage.error('載入站別列表失敗')
    }
  }

  // 清空測試計劃列表
  testPlanItems.value = []
}

// 新增: 處理站別選擇變更
const handleStationSelect = async (stationId) => {
  // 載入測試計劃
  await loadTestPlan()
}

// Load test plan
const loadTestPlan = async () => {
  // 修正: 檢查是否選擇專案和站別
  if (!selectedProjectId.value || !selectedStationId.value) {
    // 原有程式碼: if (!currentStation.value)
    // ElMessage.warning('請先選擇站別')
    testPlanItems.value = []  // 清空測試計劃列表
    return
  }

  loading.value = true
  try {
    // 修正: 使用選擇的專案和站別 ID
    // 原有程式碼: testPlanItems.value = await getStationTestPlan(
    //   currentStation.value.id,
    //   projectStore.currentProject?.id || currentStation.value.project_id,
    //   false
    // )
    testPlanItems.value = await getStationTestPlan(
      selectedStationId.value,
      selectedProjectId.value,
      false
    )
  } catch (error) {
    console.error('Failed to load test plan:', error)
    ElMessage.error('載入測試計劃失敗')
  } finally {
    loading.value = false
  }
}

// Handle show upload dialog
const handleShowUploadDialog = () => {
  // 設定預設專案和站別為當前選擇的專案和站別(如果有的話)
  // 原有程式碼: uploadForm.projectId = projectStore.currentProject?.id || null
  // 原有程式碼: uploadForm.stationId = currentStation.value?.id || null
  uploadForm.projectId = selectedProjectId.value || null
  uploadForm.stationId = selectedStationId.value || null
  showUploadDialog.value = true
}

// 新增: 處理專案變更
const handleProjectChange = async (projectId) => {
  // 清空站別選擇
  uploadForm.stationId = null

  // 載入該專案的站別列表
  if (projectId) {
    try {
      await projectStore.fetchProjectStations(projectId)
    } catch (error) {
      console.error('Failed to load stations:', error)
      ElMessage.error('載入站別列表失敗')
    }
  }
}

// Handle file selection
const handleFileChange = (file) => {
  uploadForm.file = file.raw
}

const handleFileRemove = () => {
  uploadForm.file = null
}

// Handle CSV upload
const handleUpload = async () => {
  // 修正: 檢查是否選擇專案、站別和檔案
  if (!uploadForm.projectId) {
    ElMessage.warning('請選擇專案')
    return
  }

  if (!uploadForm.stationId) {
    ElMessage.warning('請選擇站別')
    return
  }

  if (!uploadForm.file) {
    ElMessage.warning('請選擇檔案')
    return
  }

  uploading.value = true
  try {
    const response = await uploadTestPlanCSV(
      uploadForm.stationId,
      uploadForm.file,
      uploadForm.projectId,  // 新增: 傳遞 projectId
      uploadForm.testPlanName,  // 新增: 傳遞 testPlanName
      uploadForm.replaceExisting
    )

    ElMessage.success(
      `上傳成功！共 ${response.total_items} 項，成功 ${response.created_items} 項`
    )

    // 儲存上傳的站別和專案 ID
    const uploadedStationId = uploadForm.stationId
    const uploadedProjectId = uploadForm.projectId

    showUploadDialog.value = false
    uploadForm.file = null
    uploadRef.value?.clearFiles()

    // 修正: 上傳後切換到該站別並載入測試計劃
    // 如果上傳的專案不是當前專案,先切換專案
    if (!projectStore.currentProject || projectStore.currentProject.id !== uploadedProjectId) {
      const project = projectStore.projects.find(p => p.id === uploadedProjectId)
      if (project) {
        await projectStore.setCurrentProject(project)
        await projectStore.fetchProjectStations(project.id)
      }
    }

    // 切換到上傳的站別
    // 修正: 更新本地選擇狀態而不是 store 狀態
    // 原有程式碼:
    // if (!currentStation.value || currentStation.value.id !== uploadedStationId) {
    //   const station = projectStore.stations.find(s => s.id === uploadedStationId)
    //   if (station) {
    //     await projectStore.setCurrentStation(station)
    //   }
    // }
    selectedProjectId.value = uploadedProjectId
    selectedStationId.value = uploadedStationId

    // 重新載入測試計劃
    await loadTestPlan()

    // 清空上傳表單的選擇
    uploadForm.projectId = null
    uploadForm.stationId = null
  } catch (error) {
    console.error('Upload failed:', error)
    ElMessage.error(error.response?.data?.detail || '上傳失敗')
  } finally {
    uploading.value = false
  }
}

// Handle selection change
const handleSelectionChange = (selection) => {
  selectedItems.value = selection
}

// Handle add item
const handleAddItem = () => {
  Object.assign(editingItem, {
    id: null,
    item_name: '',
    test_type: '',
    lower_limit: null,
    upper_limit: null,
    unit: '',
    sequence_order: testPlanItems.value.length + 1,
    enabled: true,
    // 重置新增欄位
    item_key: '',
    value_type: '',
    limit_type: '',
    eq_limit: '',
    pass_or_fail: '',
    measure_value: '',
    execute_name: '',
    case_type: '',
    command: '',
    timeout: null,
    use_result: '',
    wait_msec: null,
    // 新增: 重置測試計劃名稱
    test_plan_name: ''
  })
  showEditDialog.value = true
}

// Handle edit item
const handleEditItem = (row) => {
  Object.assign(editingItem, { ...row })
  showEditDialog.value = true
}

// Handle save item
const handleSaveItem = async () => {
  if (!editFormRef.value) return

  await editFormRef.value.validate(async (valid) => {
    if (!valid) return

    try {
      // 準備更新/新增資料 (包含所有欄位)
      const itemData = {
        item_name: editingItem.item_name,
        test_type: editingItem.test_type,
        lower_limit: editingItem.lower_limit,
        upper_limit: editingItem.upper_limit,
        unit: editingItem.unit,
        sequence_order: editingItem.sequence_order,
        enabled: editingItem.enabled,
        // 新增欄位
        item_key: editingItem.item_key,
        value_type: editingItem.value_type,
        limit_type: editingItem.limit_type,
        eq_limit: editingItem.eq_limit,
        pass_or_fail: editingItem.pass_or_fail,
        measure_value: editingItem.measure_value,
        execute_name: editingItem.execute_name,
        case_type: editingItem.case_type,
        command: editingItem.command,
        timeout: editingItem.timeout,
        use_result: editingItem.use_result,
        wait_msec: editingItem.wait_msec,
        // 新增: 測試計劃名稱
        test_plan_name: editingItem.test_plan_name
      }

      if (editingItem.id) {
        // Update existing item
        await updateTestPlanItem(editingItem.id, itemData)
        ElMessage.success('更新成功')
      } else {
        // Create new item
        // 修正: 使用選擇的專案和站別
        // 原有程式碼:
        // await createTestPlanItem({
        //   project_id: projectStore.currentProject?.id || currentStation.value.project_id,
        //   station_id: currentStation.value.id,
        //   item_no: editingItem.sequence_order,
        //   ...itemData,
        //   parameters: {}
        // })
        await createTestPlanItem({
          project_id: selectedProjectId.value,
          station_id: selectedStationId.value,
          item_no: editingItem.sequence_order,
          ...itemData,
          parameters: {}
        })
        ElMessage.success('新增成功')
      }

      showEditDialog.value = false
      await loadTestPlan()
    } catch (error) {
      console.error('Save failed:', error)
      ElMessage.error(error.response?.data?.detail || '儲存失敗')
    }
  })
}

// Handle toggle enabled
const handleToggleEnabled = async (row) => {
  try {
    await updateTestPlanItem(row.id, { enabled: !row.enabled })
    ElMessage.success('更新成功')
    await loadTestPlan()
  } catch (error) {
    console.error('Toggle failed:', error)
    ElMessage.error('更新失敗')
  }
}

// Handle delete item
const handleDeleteItem = async (row) => {
  try {
    await ElMessageBox.confirm(
      `確定要刪除測試項目 "${row.item_name}" 嗎?`,
      '確認刪除',
      {
        confirmButtonText: '確定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await deleteTestPlanItem(row.id)
    ElMessage.success('刪除成功')
    await loadTestPlan()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Delete failed:', error)
      ElMessage.error('刪除失敗')
    }
  }
}

// Handle bulk delete
const handleBulkDelete = async () => {
  try {
    await ElMessageBox.confirm(
      `確定要刪除選中的 ${selectedItems.value.length} 個測試項目嗎?`,
      '確認刪除',
      {
        confirmButtonText: '確定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const ids = selectedItems.value.map(item => item.id)
    await bulkDeleteTestPlanItems(ids)
    ElMessage.success('刪除成功')
    await loadTestPlan()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Bulk delete failed:', error)
      ElMessage.error('刪除失敗')
    }
  }
}

onMounted(async () => {
  // 原有程式碼: 從 localStorage 載入當前專案和站別
  // currentProject 和 currentStation 已在 store 初始化時自動載入，無需額外呼叫方法
  // 原程式碼: projectStore.loadFromStorage() - 此方法不存在，已移除

  // 修正: 載入所有專案列表
  if (projectStore.projects.length === 0) {
    try {
      await projectStore.fetchProjects()
    } catch (error) {
      console.error('Failed to load projects:', error)
    }
  }

  // 修正: 如果有 store 中有當前專案,自動選擇並載入站別列表
  if (projectStore.currentProject) {
    try {
      selectedProjectId.value = projectStore.currentProject.id
      await projectStore.fetchProjectStations(projectStore.currentProject.id)

      // 如果有 store 中有當前站別,自動選擇
      if (projectStore.currentStation) {
        selectedStationId.value = projectStore.currentStation.id
      }
    } catch (error) {
      console.error('Failed to load stations:', error)
    }
  }

  // 載入測試計劃(如果有選擇專案和站別)
  loadTestPlan()
})
</script>

<style scoped>
.testplan-manage-container {
  padding: 20px;
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

.header-actions {
  display: flex;
  gap: 10px;
}

.filter-card {
  margin-bottom: 20px;
}

.filter-card :deep(.el-card__body) {
  padding: 15px 20px;
}

.table-footer {
  margin-top: 16px;
  text-align: right;
}

:deep(.el-table) {
  font-size: 14px;
}
</style>
