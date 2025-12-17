<template>
  <div class="login-container">
    <el-card class="login-card">
      <template #header>
        <div class="card-header">
          <h2>WebPDTool</h2>
          <p>測試系統登入</p>
        </div>
      </template>

      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="rules"
        label-width="80px"
        @keyup.enter="handleLogin"
      >
        <el-form-item label="使用者" prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="請輸入使用者名稱"
            prefix-icon="User"
            clearable
          />
        </el-form-item>

        <el-form-item label="密碼" prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="請輸入密碼"
            prefix-icon="Lock"
            show-password
            clearable
          />
        </el-form-item>

        <!-- Show project/station selector after login -->
        <div v-if="showProjectSelector">
          <ProjectStationSelector
            @project-selected="onProjectSelected"
            @station-selected="onStationSelected"
          />
        </div>

        <el-form-item>
          <el-button
            v-if="!showProjectSelector"
            type="primary"
            :loading="loading"
            style="width: 100%"
            @click="handleLogin"
          >
            {{ loading ? '登入中...' : '登入' }}
          </el-button>
          <el-button
            v-else
            type="success"
            :disabled="!stationSelected"
            style="width: 100%"
            @click="handleProceed"
          >
            進入系統
          </el-button>
        </el-form-item>
      </el-form>

      <div class="login-footer">
        <p>預設帳號: admin / engineer1 / operator1</p>
        <p>預設密碼: admin123</p>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useProjectStore } from '@/stores/project'
import { ElMessage } from 'element-plus'
import ProjectStationSelector from '@/components/ProjectStationSelector.vue'

const router = useRouter()
const authStore = useAuthStore()
const projectStore = useProjectStore()
const loginFormRef = ref(null)
const loading = ref(false)
const showProjectSelector = ref(false)
const stationSelected = ref(false)

const loginForm = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [
    { required: true, message: '請輸入使用者名稱', trigger: 'blur' },
    { min: 3, max: 50, message: '長度在 3 到 50 個字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '請輸入密碼', trigger: 'blur' },
    { min: 6, message: '密碼至少 6 個字符', trigger: 'blur' }
  ]
}

const handleLogin = async () => {
  if (!loginFormRef.value) return

  await loginFormRef.value.validate(async (valid) => {
    if (!valid) return

    loading.value = true
    try {
      await authStore.login(loginForm.username, loginForm.password)
      ElMessage.success('登入成功，請選擇專案與站別')
      showProjectSelector.value = true
    } catch (error) {
      console.error('Login error:', error)
      ElMessage.error(error.response?.data?.detail || '登入失敗，請檢查帳號密碼')
    } finally {
      loading.value = false
    }
  })
}

const onProjectSelected = (project) => {
  console.log('Project selected:', project)
  stationSelected.value = false
}

const onStationSelected = (station) => {
  console.log('Station selected:', station)
  stationSelected.value = true
}

const handleProceed = () => {
  ElMessage.success('進入測試系統')
  router.push('/main')
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
  width: 450px;
  border-radius: 10px;
}

.card-header {
  text-align: center;
}

.card-header h2 {
  margin: 0 0 10px 0;
  color: #409eff;
  font-size: 28px;
}

.card-header p {
  margin: 0;
  color: #666;
  font-size: 14px;
}

.login-footer {
  text-align: center;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #eee;
}

.login-footer p {
  margin: 5px 0;
  color: #999;
  font-size: 12px;
}

:deep(.el-form-item__label) {
  font-weight: 500;
}
</style>
