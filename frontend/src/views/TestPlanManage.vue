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
              @click="showUploadDialog = true"
            >
              上傳 CSV
            </el-button>
            <el-button
              type="success"
              :icon="Plus"
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

      <!-- Station Info -->
      <el-alert
        v-if="currentStation"
        :title="`當前站別: ${currentStation.station_code} - ${currentStation.station_name}`"
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

        <el-table-column prop="item_name" label="測試項目" min-width="200" />

        <el-table-column prop="test_type" label="測試類型" width="120" />

        <el-table-column label="限制值" width="180">
          <template #default="{ row }">
            <span v-if="row.lower_limit !== null || row.upper_limit !== null">
              {{ row.lower_limit ?? '-' }} ~ {{ row.upper_limit ?? '-' }}
            </span>
            <span v-else>-</span>
          </template>
        </el-table-column>

        <el-table-column label="狀態" width="80">
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
          :disabled="!uploadForm.file"
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
      width="600px"
    >
      <el-form
        ref="editFormRef"
        :model="editingItem"
        :rules="editFormRules"
        label-width="120px"
      >
        <el-form-item label="測試項目名稱" prop="item_name">
          <el-input v-model="editingItem.item_name" />
        </el-form-item>

        <el-form-item label="測試類型" prop="test_type">
          <el-input v-model="editingItem.test_type" />
        </el-form-item>

        <el-form-item label="下限值">
          <el-input-number
            v-model="editingItem.lower_limit"
            :precision="6"
            :controls="false"
          />
        </el-form-item>

        <el-form-item label="上限值">
          <el-input-number
            v-model="editingItem.upper_limit"
            :precision="6"
            :controls="false"
          />
        </el-form-item>

        <el-form-item label="單位">
          <el-input v-model="editingItem.unit" />
        </el-form-item>

        <el-form-item label="序號" prop="sequence_order">
          <el-input-number v-model="editingItem.sequence_order" :min="1" />
        </el-form-item>

        <el-form-item label="狀態">
          <el-switch
            v-model="editingItem.enabled"
            active-text="啟用"
            inactive-text="停用"
          />
        </el-form-item>
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
const currentStation = computed(() => projectStore.currentStation)

const testPlanItems = ref([])
const selectedItems = ref([])
const loading = ref(false)
const uploading = ref(false)
const showUploadDialog = ref(false)
const showEditDialog = ref(false)

const uploadForm = reactive({
  file: null,
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
  enabled: true
})

const editFormRules = {
  item_name: [{ required: true, message: '請輸入測試項目名稱', trigger: 'blur' }],
  test_type: [{ required: true, message: '請輸入測試類型', trigger: 'blur' }],
  sequence_order: [{ required: true, message: '請輸入序號', trigger: 'blur' }]
}

const uploadRef = ref(null)
const editFormRef = ref(null)
const testPlanTable = ref(null)

// Load test plan
const loadTestPlan = async () => {
  if (!currentStation.value) {
    ElMessage.warning('請先選擇站別')
    return
  }

  loading.value = true
  try {
    testPlanItems.value = await getStationTestPlan(currentStation.value.id, false)
  } catch (error) {
    console.error('Failed to load test plan:', error)
    ElMessage.error('載入測試計劃失敗')
  } finally {
    loading.value = false
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
  if (!uploadForm.file) {
    ElMessage.warning('請選擇檔案')
    return
  }

  uploading.value = true
  try {
    const response = await uploadTestPlanCSV(
      currentStation.value.id,
      uploadForm.file,
      uploadForm.replaceExisting
    )

    ElMessage.success(
      `上傳成功！共 ${response.total_items} 項，成功 ${response.created_items} 項`
    )

    showUploadDialog.value = false
    uploadForm.file = null
    uploadRef.value?.clearFiles()
    await loadTestPlan()
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
    enabled: true
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
      if (editingItem.id) {
        // Update existing item
        await updateTestPlanItem(editingItem.id, {
          item_name: editingItem.item_name,
          test_type: editingItem.test_type,
          lower_limit: editingItem.lower_limit,
          upper_limit: editingItem.upper_limit,
          unit: editingItem.unit,
          sequence_order: editingItem.sequence_order,
          enabled: editingItem.enabled
        })
        ElMessage.success('更新成功')
      } else {
        // Create new item
        await createTestPlanItem({
          station_id: currentStation.value.id,
          item_no: editingItem.sequence_order,
          item_name: editingItem.item_name,
          test_type: editingItem.test_type,
          lower_limit: editingItem.lower_limit,
          upper_limit: editingItem.upper_limit,
          unit: editingItem.unit,
          sequence_order: editingItem.sequence_order,
          enabled: editingItem.enabled,
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

onMounted(() => {
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

.table-footer {
  margin-top: 16px;
  text-align: right;
}

:deep(.el-table) {
  font-size: 14px;
}
</style>
