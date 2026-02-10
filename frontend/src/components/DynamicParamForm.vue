<template>
  <div class="dynamic-param-form">
    <!-- 參數欄位區域 -->
    <div v-if="hasParams" class="param-fields">
      <el-row :gutter="20">
        <el-col
          v-for="param in allParams"
          :key="param.name"
          :span="12"
        >
          <el-form-item
            :label="formatParamLabel(param.name)"
            :required="param.required"
          >
            <!-- 數字輸入 -->
            <el-input-number
              v-if="param.type === 'number'"
              v-model="localParams[param.name]"
              :placeholder="param.example"
              :precision="getNumberPrecision(param.name)"
              :controls="false"
              style="width: 100%"
              @change="handleChange"
            />

            <!-- 下拉選單 -->
            <el-select
              v-else-if="param.type === 'select'"
              v-model="localParams[param.name]"
              :placeholder="param.example"
              style="width: 100%"
              clearable
              @change="handleChange"
            >
              <el-option
                v-for="option in param.options"
                :key="option"
                :label="option"
                :value="option"
              />
            </el-select>

            <!-- 文字輸入 (預設) -->
            <el-input
              v-else
              v-model="localParams[param.name]"
              :placeholder="param.example"
              clearable
              @input="handleChange"
            />

            <!-- 參數提示 -->
            <div v-if="param.required" class="param-hint">
              <el-text size="small" type="info">
                必填 · 範例: {{ param.example }}
              </el-text>
            </div>
            <div v-else class="param-hint">
              <el-text size="small" type="info">
                選填 · 範例: {{ param.example }}
              </el-text>
            </div>
          </el-form-item>
        </el-col>
      </el-row>
    </div>

    <!-- 無參數提示 -->
    <el-empty
      v-else
      description="請先選擇測試類型和儀器模式"
      :image-size="100"
    />

    <!-- 驗證錯誤提示 -->
    <el-alert
      v-if="validationErrors.length > 0"
      type="warning"
      :closable="false"
      style="margin-top: 10px"
    >
      <template #title>
        參數驗證錯誤
      </template>
      <ul style="margin: 5px 0; padding-left: 20px">
        <li v-for="(error, index) in validationErrors" :key="index">
          {{ error }}
        </li>
      </ul>
    </el-alert>
  </div>
</template>

<script setup>
import { computed, watch, ref } from 'vue'
import { useMeasurementParams } from '@/composables/useMeasurementParams'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({})
  },
  testType: {
    type: String,
    default: ''
  },
  switchMode: {
    type: String,
    default: ''
  },
  // 新增: 從父組件接收 templates，避免重複創建 composable 實例
  templates: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:modelValue', 'validation-change'])

// 原有程式碼: 創建新的 composable 實例導致模板數據不同步
// const {
//   currentTestType,
//   currentSwitchMode,
//   requiredParams,
//   optionalParams,
//   exampleParams,
//   inferParamType,
//   getParamOptions,
//   formatParamLabel
// } = useMeasurementParams()

// 修正: 只使用工具函數，模板數據從 props 接收
const {
  inferParamType,
  getParamOptions,
  formatParamLabel
} = useMeasurementParams()

// 新增: 本地狀態管理
const currentTestType = ref(props.testType)
const currentSwitchMode = ref(props.switchMode)

const validationErrors = ref([])
const localParams = ref({ ...props.modelValue })

// 同步 props 到本地狀態
watch(() => props.testType, (val) => {
  currentTestType.value = val
}, { immediate: true })

watch(() => props.switchMode, (val) => {
  currentSwitchMode.value = val
}, { immediate: true })

// 同步 props.modelValue 到 localParams
watch(() => props.modelValue, (val) => {
  localParams.value = { ...val }
}, { deep: true })

// 新增: 計算當前模板（從 props.templates 取得）
const currentTemplate = computed(() => {
  if (!currentTestType.value || !props.templates || Object.keys(props.templates).length === 0) {
    return null
  }

  const switchMode = currentSwitchMode.value
  if (!switchMode) {
    return null
  }

  return props.templates[currentTestType.value]?.[switchMode] || null
})

// 新增: 計算必填參數列表
const requiredParams = computed(() => {
  return currentTemplate.value?.required || []
})

// 新增: 計算可選參數列表
const optionalParams = computed(() => {
  return currentTemplate.value?.optional || []
})

// 新增: 計算範例參數值
const exampleParams = computed(() => {
  return currentTemplate.value?.example || {}
})

// 計算所有參數（含類型資訊）
const allParams = computed(() => {
  const params = []

  // 必填參數
  requiredParams.value.forEach(name => {
    params.push({
      name,
      required: true,
      type: inferParamType(name, exampleParams.value[name]),
      options: getParamOptions(name),
      example: String(exampleParams.value[name] || '')
    })
  })

  // 可選參數
  optionalParams.value.forEach(name => {
    params.push({
      name,
      required: false,
      type: inferParamType(name, exampleParams.value[name]),
      options: getParamOptions(name),
      example: String(exampleParams.value[name] || '')
    })
  })

  return params
})

// 是否有參數可顯示
const hasParams = computed(() => {
  return allParams.value.length > 0
})

// 取得數字精度
const getNumberPrecision = (paramName) => {
  const name = paramName.toLowerCase()
  // Channel 類型不需要小數
  if (name.includes('channel')) {
    return 0
  }
  // 電壓、電流使用 2 位小數
  if (name.includes('volt') || name.includes('curr')) {
    return 2
  }
  // 頻率、頻寬使用 3 位小數
  if (name.includes('frequency') || name.includes('bandwidth')) {
    return 3
  }
  // 預設 2 位小數
  return 2
}

// 處理變更
const handleChange = () => {
  emit('update:modelValue', { ...localParams.value })
  validateParams()
}

// 驗證參數
const validateParams = () => {
  const errors = []

  // 檢查必填參數
  requiredParams.value.forEach(paramName => {
    const value = localParams.value[paramName]
    if (value === undefined || value === null || value === '') {
      errors.push(`參數 "${formatParamLabel(paramName)}" 為必填`)
    }
  })

  validationErrors.value = errors
  emit('validation-change', errors.length === 0)
}

// 監聽參數模板變化，清空驗證錯誤
watch([currentTestType, currentSwitchMode], () => {
  validationErrors.value = []
})

// 初始驗證
watch(() => localParams.value, validateParams, { deep: true, immediate: true })
</script>

<style scoped>
.dynamic-param-form {
  padding: 10px 0;
}

.param-fields {
  min-height: 100px;
}

.param-hint {
  margin-top: 4px;
  line-height: 1.2;
}

:deep(.el-form-item__label) {
  font-weight: 500;
}

:deep(.el-empty) {
  padding: 30px 0;
}
</style>
