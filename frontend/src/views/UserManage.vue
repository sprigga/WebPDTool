<template>
  <div class="user-manage-container">
    <el-alert
      v-if="!isAdmin"
      title="僅供查看"
      description="您沒有管理權限，無法新增、編輯或刪除使用者"
      type="info"
      :closable="false"
      style="margin-bottom: 20px"
    />

    <el-card>
      <template #header>
        <div class="card-header">
          <h2>使用者管理</h2>
          <el-button
            v-if="canEdit"
            type="primary"
            :icon="Plus"
            @click="handleAddUser"
          >
            新增使用者
          </el-button>
        </div>
      </template>

      <!-- Users Table -->
      <div v-if="usersStore.users.length === 0 && !loading" class="empty-state">
        <el-empty description="尚無使用者資料，點擊「新增使用者」開始建立" />
      </div>
      <el-table
        v-else
        v-loading="loading"
        :data="usersStore.users"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="username" label="使用者名稱" width="150" />

        <el-table-column prop="full_name" label="全名" min-width="150" />

        <el-table-column prop="email" label="電子郵件" min-width="200" />

        <el-table-column label="角色" width="120">
          <template #default="{ row }">
            <el-tag :type="getRoleType(row.role)" size="small">
              {{ getRoleLabel(row.role) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="狀態" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
              {{ row.is_active ? '啟用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="created_at" label="建立時間" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-tooltip content="需要管理員權限" :disabled="canEdit">
              <span>
                <el-button
                  size="small"
                  :disabled="!canEdit"
                  @click="handleEditUser(row)"
                >
                  編輯
                </el-button>
              </span>
            </el-tooltip>
            <el-tooltip content="需要管理員權限" :disabled="canEdit">
              <span>
                <el-button
                  size="small"
                  :disabled="!canEdit"
                  @click="handleChangePassword(row)"
                >
                  變更密碼
                </el-button>
              </span>
            </el-tooltip>
            <el-tooltip :content="row.id === currentUser?.id ? '無法刪除自己' : '需要管理員權限'" :disabled="canEdit && row.id !== currentUser?.id">
              <span>
                <el-button
                  size="small"
                  type="danger"
                  :disabled="!canEdit || row.id === currentUser?.id"
                  @click="handleDeleteUser(row)"
                >
                  刪除
                </el-button>
              </span>
            </el-tooltip>
          </template>
        </el-table-column>
      </el-table>

      <div class="table-footer">
        <el-text>共 {{ usersStore.users.length }} 個使用者</el-text>
      </div>
    </el-card>

    <!-- User Create/Edit Dialog -->
    <el-dialog
      v-model="showUserDialog"
      :title="editingUser.id ? '編輯使用者' : '新增使用者'"
      width="600px"
    >
      <el-form
        ref="userFormRef"
        :model="editingUser"
        :rules="userFormRules"
        label-width="120px"
      >
        <el-form-item label="使用者名稱" prop="username">
          <el-input
            v-model="editingUser.username"
            placeholder="請輸入使用者名稱"
            :disabled="!!editingUser.id"
          />
        </el-form-item>

        <el-form-item label="全名" prop="full_name">
          <el-input
            v-model="editingUser.full_name"
            placeholder="請輸入全名"
          />
        </el-form-item>

        <el-form-item label="電子郵件" prop="email">
          <el-input
            v-model="editingUser.email"
            placeholder="請輸入電子郵件"
            type="email"
          />
        </el-form-item>

        <el-form-item label="密碼" prop="password" v-if="!editingUser.id">
          <el-input
            v-model="editingUser.password"
            type="password"
            placeholder="請輸入密碼"
            show-password
          />
        </el-form-item>

        <el-form-item label="確認密碼" prop="confirmPassword" v-if="!editingUser.id">
          <el-input
            v-model="editingUser.confirmPassword"
            type="password"
            placeholder="請再次輸入密碼"
            show-password
          />
        </el-form-item>

        <el-form-item label="角色" prop="role">
          <el-select v-model="editingUser.role" placeholder="請選擇角色" style="width: 100%">
            <el-option label="管理員" value="admin" />
            <el-option label="工程師" value="engineer" />
            <el-option label="操作員" value="operator" />
          </el-select>
        </el-form-item>

        <el-form-item label="狀態">
          <el-switch
            v-model="editingUser.is_active"
            active-text="啟用"
            inactive-text="停用"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showUserDialog = false">取消</el-button>
        <el-button
          type="primary"
          :loading="saving"
          @click="handleSaveUser"
        >
          儲存
        </el-button>
      </template>
    </el-dialog>

    <!-- Change Password Dialog -->
    <el-dialog
      v-model="showPasswordDialog"
      title="變更密碼"
      width="500px"
    >
      <el-form
        ref="passwordFormRef"
        :model="passwordForm"
        :rules="passwordFormRules"
        label-width="120px"
      >
        <el-form-item label="使用者">
          <el-text>{{ passwordForm.username }}</el-text>
        </el-form-item>

        <el-form-item label="新密碼" prop="newPassword">
          <el-input
            v-model="passwordForm.newPassword"
            type="password"
            placeholder="請輸入新密碼"
            show-password
          />
        </el-form-item>

        <el-form-item label="確認密碼" prop="confirmPassword">
          <el-input
            v-model="passwordForm.confirmPassword"
            type="password"
            placeholder="請再次輸入新密碼"
            show-password
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showPasswordDialog = false">取消</el-button>
        <el-button
          type="primary"
          :loading="savingPassword"
          @click="handleSavePassword"
        >
          確認變更
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUsersStore } from '@/stores/users'
import { useAuthStore } from '@/stores/auth'
import { createUser, updateUser, changeUserPassword, deleteUser } from '@/api/users'

const usersStore = useUsersStore()
const authStore = useAuthStore()

// State
const loading = ref(false)
const saving = ref(false)
const savingPassword = ref(false)

// Computed
const currentUser = computed(() => authStore.user)
const isAdmin = computed(() => currentUser.value?.role === 'admin')
const canEdit = computed(() => isAdmin.value)

// Dialog state
const showUserDialog = ref(false)
const userFormRef = ref(null)

// Form data
const editingUser = reactive({
  id: null,
  username: '',
  full_name: '',
  email: '',
  password: '',
  confirmPassword: '',
  role: 'operator',
  is_active: true
})

// Form validation rules
const validateConfirmPassword = (rule, value, callback) => {
  if (!editingUser.id) {
    // Only validate on create
    if (value === '') {
      callback(new Error('請再次輸入密碼'))
    } else if (value !== editingUser.password) {
      callback(new Error('兩次輸入的密碼不一致'))
    } else {
      callback()
    }
  } else {
    callback()
  }
}

const userFormRules = {
  username: [
    { required: true, message: '請輸入使用者名稱', trigger: 'blur' },
    { min: 3, max: 50, message: '使用者名稱長度在 3 到 50 個字元', trigger: 'blur' },
    {
      pattern: /^[a-zA-Z0-9_-]+$/,
      message: '只能包含字母、數字、底線和破折號',
      trigger: 'blur'
    }
  ],
  full_name: [
    { required: true, message: '請輸入全名', trigger: 'blur' },
    { min: 2, max: 100, message: '全名長度在 2 到 100 個字元', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '請輸入電子郵件', trigger: 'blur' },
    { type: 'email', message: '請輸入正確的電子郵件格式', trigger: 'blur' }
  ],
  password: [
    {
      validator: (rule, value, callback) => {
        if (!editingUser.id && !value) {
          callback(new Error('請輸入密碼'))
        } else if (value && value.length < 6) {
          callback(new Error('密碼長度至少 6 個字元'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ],
  confirmPassword: [
    { validator: validateConfirmPassword, trigger: 'blur' }
  ],
  role: [
    { required: true, message: '請選擇角色', trigger: 'change' }
  ]
}

// Password dialog state
const showPasswordDialog = ref(false)
const passwordFormRef = ref(null)

// Password form data
const passwordForm = reactive({
  id: null,
  username: '',
  newPassword: '',
  confirmPassword: ''
})

// Password form validation rules
const validatePasswordConfirm = (rule, value, callback) => {
  if (value === '') {
    callback(new Error('請再次輸入密碼'))
  } else if (value !== passwordForm.newPassword) {
    callback(new Error('兩次輸入的密碼不一致'))
  } else {
    callback()
  }
}

const passwordFormRules = {
  newPassword: [
    { required: true, message: '請輸入新密碼', trigger: 'blur' },
    { min: 6, message: '密碼長度至少 6 個字元', trigger: 'blur' }
  ],
  confirmPassword: [
    { validator: validatePasswordConfirm, trigger: 'blur' }
  ]
}

// Helper functions
const getRoleType = (role) => {
  const roleTypes = {
    admin: 'danger',
    engineer: 'warning',
    operator: 'info'
  }
  return roleTypes[role] || 'info'
}

const getRoleLabel = (role) => {
  const roleLabels = {
    admin: '管理員',
    engineer: '工程師',
    operator: '操作員'
  }
  return roleLabels[role] || role
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
const handleAddUser = () => {
  Object.assign(editingUser, {
    id: null,
    username: '',
    full_name: '',
    email: '',
    password: '',
    confirmPassword: '',
    role: 'operator',
    is_active: true
  })
  showUserDialog.value = true
}

const handleEditUser = (row) => {
  Object.assign(editingUser, {
    id: row.id,
    username: row.username,
    full_name: row.full_name,
    email: row.email,
    password: '',
    confirmPassword: '',
    role: row.role,
    is_active: row.is_active
  })
  showUserDialog.value = true
}

const handleDeleteUser = async (row) => {
  if (row.id === currentUser.value?.id) {
    ElMessage.warning('無法刪除自己的帳號')
    return
  }

  try {
    await ElMessageBox.confirm(
      `確定要刪除使用者 "${row.full_name}" 嗎？此操作無法復原。`,
      '確認刪除',
      {
        confirmButtonText: '確定',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger'
      }
    )

    loading.value = true
    await deleteUser(row.id)
    ElMessage.success('使用者刪除成功')
    await usersStore.fetchUsers()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Delete user failed:', error)
      const message = error.response?.data?.detail || '刪除失敗'
      ElMessage.error(message)
    }
  } finally {
    loading.value = false
  }
}

const handleSaveUser = async () => {
  if (!userFormRef.value) return

  await userFormRef.value.validate(async (valid) => {
    if (!valid) return

    saving.value = true
    try {
      const userData = {
        username: editingUser.username,
        full_name: editingUser.full_name,
        email: editingUser.email,
        role: editingUser.role,
        is_active: editingUser.is_active
      }

      if (editingUser.id) {
        // Update existing user (no password update here)
        await updateUser(editingUser.id, userData)
        ElMessage.success('使用者更新成功')
      } else {
        // Create new user (include password)
        userData.password = editingUser.password
        await createUser(userData)
        ElMessage.success('使用者建立成功')
      }

      showUserDialog.value = false
      loading.value = true
      await usersStore.fetchUsers()
      loading.value = false
    } catch (error) {
      console.error('Save user failed:', error)
      const message = error.response?.data?.detail || '操作失敗'
      ElMessage.error(message)
    } finally {
      saving.value = false
    }
  })
}

const handleChangePassword = (row) => {
  Object.assign(passwordForm, {
    id: row.id,
    username: row.username,
    newPassword: '',
    confirmPassword: ''
  })
  showPasswordDialog.value = true
}

const handleSavePassword = async () => {
  if (!passwordFormRef.value) return

  await passwordFormRef.value.validate(async (valid) => {
    if (!valid) return

    savingPassword.value = true
    try {
      // Send JSON body with new_password field
      await changeUserPassword(passwordForm.id, passwordForm.newPassword)
      ElMessage.success('密碼變更成功')
      showPasswordDialog.value = false
    } catch (error) {
      console.error('Change password failed:', error)
      const message = error.response?.data?.detail || '密碼變更失敗'
      ElMessage.error(message)
    } finally {
      savingPassword.value = false
    }
  })
}

onMounted(async () => {
  loading.value = true
  try {
    await usersStore.fetchUsers()
  } catch (error) {
    console.error('Failed to load users:', error)
    ElMessage.error('載入使用者列表失敗')
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.user-manage-container {
  padding: 20px;
  height: calc(100vh - 180px);
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

:deep(.el-card) {
  height: 100%;
  display: flex;
  flex-direction: column;
}

:deep(.el-card__body) {
  flex: 1;
  overflow: auto;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .user-manage-container {
    padding: 10px;
  }
}

/* Improve table action column spacing */
:deep(.el-table .el-button + .el-button) {
  margin-left: 4px;
}
</style>
