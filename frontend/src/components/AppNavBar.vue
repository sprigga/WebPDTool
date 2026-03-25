<template>
  <el-card class="nav-card" shadow="never">
    <el-row :gutter="10" align="middle" justify="space-between">
      <el-col :span="18">
        <div class="nav-buttons">
          <el-button :type="buttonType('main')" size="default" :disabled="isCurrent('main')" @click="navigateTo('/main')">
            測試主畫面
          </el-button>
          <el-button :type="buttonType('testplan')" size="default" :disabled="isCurrent('testplan')" @click="navigateTo('/testplan')">
            測試計劃管理
          </el-button>
          <el-button :type="buttonType('results')" size="default" :disabled="isCurrent('results')" @click="navigateTo('/results')">
            測試結果查詢
          </el-button>
          <el-button :type="buttonType('history')" size="default" :disabled="isCurrent('history')" @click="navigateTo('/history')">
            測試歷史記錄
          </el-button>
          <el-button :type="buttonType('projects')" size="default" :disabled="isCurrent('projects')" @click="navigateTo('/projects')">
            專案管理
          </el-button>
          <el-button :type="buttonType('users')" size="default" :disabled="isCurrent('users')" @click="navigateTo('/users')">
            使用者管理
          </el-button>
          <el-button :type="buttonType('instruments')" size="default" :disabled="isCurrent('instruments')" @click="navigateTo('/instruments')">
            儀器管理
          </el-button>
          <el-button :type="buttonType('analysis')" size="default" :disabled="isCurrent('analysis')" @click="navigateTo('/analysis')">
            報表分析
          </el-button>
          <el-button :type="buttonType('modbus-config')" size="default" :disabled="isCurrent('modbus-config')" @click="navigateTo('/modbus-config')">
            Modbus 設定
          </el-button>
        </div>
      </el-col>
      <el-col :span="6" style="text-align: right">
        <el-text type="info">{{ authStore.user?.username || '-' }}</el-text>
        <el-button type="danger" size="small" @click="handleLogout" style="margin-left: 10px">
          登出
        </el-button>
      </el-col>
    </el-row>
  </el-card>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const props = defineProps({
  currentPage: {
    type: String,
    required: true
  }
})

const router = useRouter()
const authStore = useAuthStore()

const isCurrent = (page) => props.currentPage === page
const buttonType = (page) => (isCurrent(page) ? 'primary' : 'default')

const navigateTo = (path) => {
  router.push(path)
}

const handleLogout = async () => {
  try {
    await authStore.logout()
    router.push('/login')
  } catch (error) {
    console.error('Logout failed:', error)
    router.push('/login')
  }
}
</script>

<style scoped>
.nav-card {
  margin-bottom: 20px;
}

.nav-buttons {
  display: flex;
  gap: 8px;
}

.nav-buttons .el-button {
  margin: 0;
}
</style>
