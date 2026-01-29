/**
 * Test Plan API client
 */
import apiClient from './client'

/**
 * Get test plan for a station
 * @param {number} stationId - Station ID
 * @param {number} projectId - Project ID
 * @param {boolean} enabledOnly - Return only enabled items
 * @param {string} testPlanName - Optional test plan name to filter by
 * @returns {Promise} Test plan items
 */
export const getStationTestPlan = (stationId, projectId, enabledOnly = true, testPlanName = null) => {
  const params = {
    enabled_only: enabledOnly,
    project_id: projectId  // 原有程式碼缺少 project_id 參數導致後端 API 報錯
  }
  if (testPlanName) {
    params.test_plan_name = testPlanName
  }
  return apiClient.get(`/api/stations/${stationId}/testplan`, { params })
}

/**
 * Get distinct test plan names for a station
 * @param {number} stationId - Station ID
 * @param {number} projectId - Project ID
 * @returns {Promise} List of test plan names
 */
export const getStationTestPlanNames = (stationId, projectId) => {
  const params = { project_id: projectId }  // 原有程式碼缺少 project_id 參數導致後端 API 報錯
  return apiClient.get(`/api/stations/${stationId}/testplan-names`, { params })
}

/**
 * Upload CSV test plan file
 * @param {number} stationId - Station ID
 * @param {File} file - CSV file
 * @param {number} projectId - Project ID (新增)
 * @param {string} testPlanName - Test plan name (新增)
 * @param {boolean} replaceExisting - Replace existing test plan
 * @returns {Promise} Upload response
 */
export const uploadTestPlanCSV = (stationId, file, projectId, testPlanName = '', replaceExisting = true) => {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('project_id', String(projectId))  // Ensure string conversion
  if (testPlanName) {
    formData.append('test_plan_name', testPlanName)  // Optional field
  }
  formData.append('replace_existing', String(replaceExisting))  // Convert boolean to string

  return apiClient.post(`/api/stations/${stationId}/testplan/upload`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

/**
 * Create a new test plan item
 * @param {Object} testPlanData - Test plan item data
 * @returns {Promise} Created test plan item
 */
export const createTestPlanItem = (testPlanData) => {
  return apiClient.post('/api/testplans', testPlanData)
}

/**
 * Get a specific test plan item
 * @param {number} testPlanId - Test plan item ID
 * @returns {Promise} Test plan item
 */
export const getTestPlanItem = (testPlanId) => {
  return apiClient.get(`/api/testplans/${testPlanId}`)
}

/**
 * Update a test plan item
 * @param {number} testPlanId - Test plan item ID
 * @param {Object} updateData - Fields to update
 * @returns {Promise} Updated test plan item
 */
export const updateTestPlanItem = (testPlanId, updateData) => {
  return apiClient.put(`/api/testplans/${testPlanId}`, updateData)
}

/**
 * Delete a test plan item
 * @param {number} testPlanId - Test plan item ID
 * @returns {Promise} Deletion response
 */
export const deleteTestPlanItem = (testPlanId) => {
  return apiClient.delete(`/api/testplans/${testPlanId}`)
}

/**
 * Bulk delete test plan items
 * @param {Array<number>} testPlanIds - List of test plan IDs to delete
 * @returns {Promise} Deletion response
 */
export const bulkDeleteTestPlanItems = (testPlanIds) => {
  return apiClient.post('/api/testplans/bulk-delete', {
    test_plan_ids: testPlanIds
  })
}

/**
 * Reorder test plan items
 * @param {Object} itemOrders - Mapping of test plan ID to new sequence order
 * @returns {Promise} Reorder response
 */
export const reorderTestPlanItems = (itemOrders) => {
  return apiClient.post('/api/testplans/reorder', {
    item_orders: itemOrders
  })
}

/**
 * Get TestPlanMap for a station (包含測試點狀態資訊)
 * 對應 PDTool4 test_point_map.py: new_test_point_map()
 *
 * @param {number} stationId - Station ID
 * @param {number} projectId - Project ID
 * @param {boolean} enabledOnly - Return only enabled test items (default: true)
 * @param {string} testPlanName - Optional test plan name to filter by
 * @returns {Promise} TestPlanMap with test point status information
 *
 * Response format:
 * {
 *   station_id: number,
 *   project_id: number,
 *   test_plan_name: string | null,
 *   total_test_points: number,
 *   test_points: [
 *     {
 *       unique_id: string,      // 測試點唯一識別碼
 *       name: string,           // 測試點名稱
 *       item_key: string,       // 項目鍵值
 *       executed: boolean,      // 是否已執行
 *       passed: boolean | null, // 通過狀態
 *       value: any,             // 測量值
 *       limit_type: string,     // 限制類型 (LOWER_LIMIT_TYPE, UPPER_LIMIT_TYPE, etc.)
 *       value_type: string,     // 數值類型 (STRING_VALUE_TYPE, FLOAT_VALUE_TYPE, etc.)
 *       lower_limit: number,    // 下限
 *       upper_limit: number,    // 上限
 *       unit: string            // 單位
 *     }
 *   ]
 * }
 */
export const getStationTestPlanMap = (stationId, projectId, enabledOnly = true, testPlanName = null) => {
  const params = {
    enabled_only: enabledOnly,
    project_id: projectId
  }
  if (testPlanName) {
    params.test_plan_name = testPlanName
  }
  return apiClient.get(`/api/stations/${stationId}/testplan-map`, { params })
}
