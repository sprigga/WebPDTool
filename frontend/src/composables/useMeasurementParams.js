import { ref, computed, watch } from 'vue'
import { getMeasurementTemplates, validateMeasurementParams } from '@/api/measurements'
import { ElMessage } from 'element-plus'

/**
 * Composable for managing measurement parameters
 * Provides reactive parameter template management and validation
 */
export function useMeasurementParams() {
  // 狀態
  const templates = ref({})
  const loading = ref(false)
  const currentTestType = ref('')
  const currentSwitchMode = ref('')

  // 計算屬性：可用的測試類型列表
  const testTypes = computed(() => {
    return Object.keys(templates.value)
  })

  // 計算屬性：當前測試類型的 switch modes
  const switchModes = computed(() => {
    if (!currentTestType.value || !templates.value[currentTestType.value]) {
      return []
    }
    return Object.keys(templates.value[currentTestType.value])
  })

  // 計算屬性：當前選擇的參數模板
  const currentTemplate = computed(() => {
    if (!currentTestType.value) {
      return null
    }

    // 如果沒有選擇 switch_mode，但測試類型只有一個 switch mode，自動使用它
    let switchMode = currentSwitchMode.value
    if (!switchMode && switchModes.value.length === 1) {
      switchMode = switchModes.value[0]
    }

    if (!switchMode) {
      return null
    }

    return templates.value[currentTestType.value]?.[switchMode] || null
  })

  // 計算屬性：必填參數列表
  const requiredParams = computed(() => {
    return currentTemplate.value?.required || []
  })

  // 計算屬性：可選參數列表
  const optionalParams = computed(() => {
    return currentTemplate.value?.optional || []
  })

  // 計算屬性：所有參數列表
  const allParams = computed(() => {
    return [...requiredParams.value, ...optionalParams.value]
  })

  // 計算屬性：範例參數值
  const exampleParams = computed(() => {
    return currentTemplate.value?.example || {}
  })

  // 載入模板
  const loadTemplates = async () => {
    if (loading.value) return // 避免重複載入

    loading.value = true
    try {
      const response = await getMeasurementTemplates()
      templates.value = response.templates
      return response
    } catch (error) {
      console.error('Failed to load measurement templates:', error)
      ElMessage.error('載入測量參數模板失敗')
      throw error
    } finally {
      loading.value = false
    }
  }

  // 驗證參數
  const validateParams = async (parameters) => {
    if (!currentTestType.value) {
      return {
        valid: false,
        message: '請先選擇測試類型',
        missing_params: [],
        invalid_params: [],
        suggestions: []
      }
    }

    try {
      const result = await validateMeasurementParams(
        currentTestType.value,
        currentSwitchMode.value,
        parameters
      )
      return result
    } catch (error) {
      console.error('Parameter validation failed:', error)
      return {
        valid: false,
        message: error.response?.data?.detail || '參數驗證失敗',
        missing_params: [],
        invalid_params: [],
        suggestions: []
      }
    }
  }

  // 根據參數名稱和範例值推斷輸入類型
  const inferParamType = (paramName, exampleValue) => {
    const name = paramName.toLowerCase()

    // 數字類型
    if (name.includes('volt') || name.includes('curr') ||
        name.includes('channel') || name.includes('timeout') ||
        name.includes('nplc') || name.includes('range') ||
        name.includes('bandwidth') || name.includes('frequency') ||
        name.includes('delay')) {
      return 'number'
    }

    // 下拉選單類型
    if (name === 'baud') {
      return 'select'
    }

    if (name === 'type' && typeof exampleValue === 'string') {
      return 'select'
    }

    if (name === 'item' && typeof exampleValue === 'string') {
      return 'select'
    }

    // 預設文字輸入
    return 'text'
  }

  // 取得參數選項（用於下拉選單）
  const getParamOptions = (paramName) => {
    const name = paramName.toLowerCase()

    if (name === 'baud') {
      return ['9600', '19200', '38400', '57600', '115200']
    }

    if (name === 'type') {
      return ['DC', 'AC', 'RES', 'TEMP']
    }

    if (name === 'item') {
      return ['volt', 'curr', 'res', 'temp', 'freq']
    }

    return []
  }

  // 格式化參數標籤名稱
  const formatParamLabel = (paramName) => {
    // 將駝峰式命名轉換為可讀標籤
    // SetVolt -> Set Volt
    // Channel -> Channel
    return paramName.replace(/([A-Z])/g, ' $1').trim()
  }

  // 監聽 testType 變化，重置 switchMode
  watch(currentTestType, () => {
    currentSwitchMode.value = ''
  })

  return {
    // 狀態
    templates,
    loading,
    currentTestType,
    currentSwitchMode,

    // 計算屬性
    testTypes,
    switchModes,
    currentTemplate,
    requiredParams,
    optionalParams,
    allParams,
    exampleParams,

    // 方法
    loadTemplates,
    validateParams,
    inferParamType,
    getParamOptions,
    formatParamLabel
  }
}
