# Loop 測試功能修正

## 修正日期
2026-01-28

## 問題描述
1. **問題 1**: 原有的 Loop 測試功能配置後，不會按照 `loopCount` 的數值去執行循環測試。系統只會執行一次測試，不會重複執行。
2. **問題 2**: 當 Loop 測試完成後，會出現 "執行測試時發生錯誤: errorItems is not defined" 的訊息。

## 問題原因
1. `executeMeasurements` 函數缺少外層循環邏輯
2. `sfcConfig.loopEnabled` 和 `sfcConfig.loopCount` 沒有被實際使用
3. `loopCount` 只是用於顯示的計數器，沒有與循環執行邏輯連動
4. **變數作用域問題**: `passCount`、`failCount`、`errorCount` 和 `errorItems` 使用 `let` 和 `const` 在循環內部定義，導致這些變數的作用域只限於循環內部。當循環結束後嘗試使用這些變數時，會出現 "is not defined" 錯誤。

## 修正內容

### 1. 修改 `executeMeasurements` 函數 - 修正變數作用域
**位置**: `frontend/src/views/TestMain.vue:610-656`

**問題**: `passCount`、`failCount`、`errorCount` 和 `errorItems` 在循環內部定義，導致循環結束後無法存取。

**修正**:
```javascript
// 原有程式碼: 沒有實現 Loop 測試功能
// 修改: 根據 sfcConfig.loopEnabled 和 sfcConfig.loopCount 來執行循環測試
const loopEnabled = sfcConfig.loopEnabled
const totalLoops = loopEnabled ? sfcConfig.loopCount : 1

// 原有程式碼: passCount, failCount, errorCount, errorItems 在循環內部定義
// 修改: 將這些變數移到循環外部,以便在循環結束後仍能存取
let passCount = 0
let failCount = 0
let errorCount = 0
const errorItems = [] // PDTool4 runAllTest: 收集錯誤項目

// 外層循環: 處理 Loop 測試
for (let currentLoop = 0; currentLoop < totalLoops; currentLoop++) {
  // 如果是循環測試,顯示當前循環次數
  if (loopEnabled) {
    addStatusMessage(`========== Loop ${currentLoop + 1}/${totalLoops} ==========`, 'info')
    loopCount.value = currentLoop + 1
  }

  // Reset tracking variables for each loop
  testResults.value = {}
  usedInstruments.value = {}

  // 原有程式碼: 每次循環都重新定義 passCount, failCount, errorCount, errorItems
  // 修改: 每次循環重置這些變數的值,而不是重新定義
  passCount = 0
  failCount = 0
  errorCount = 0
  errorItems.length = 0 // 清空陣列

  // 執行所有測試項目
  for (let index = 0; index < testPlanItems.value.length; index++) {
    // ... 執行測試項目
  }

  // 循環測試模式: 在每次循環結束後顯示結果
  if (currentLoop < totalLoops - 1) {
    addStatusMessage(`Loop ${currentLoop + 1} 完成，準備進行下一次循環...`, 'info')
  }
}
```

### 2. 修改 `handleStartTest` 函數
**位置**: `frontend/src/views/TestMain.vue:954-1012`

**新增邏輯**:
```javascript
// 原有程式碼: 沒有重置 loopCount
// 修改: 重置 loopCount 為 0，表示準備開始新的循環測試
loopCount.value = 0
```

### 3. 修改最終結果顯示
**位置**: `frontend/src/views/TestMain.vue:766-801`

**新增邏輯**:
```javascript
// 原有程式碼: 只顯示一次測試的結果
// 修改: 支援循環測試模式,顯示循環次數
const loopText = loopEnabled ? ` (共 ${totalLoops} 次循環)` : ''
addStatusMessage(
  `測試完成: ${finalResult.value}${loopText} (通過: ${passCount}, 失敗: ${failCount}, 錯誤: ${errorCount})`,
  finalResult.value === 'PASS' ? 'success' : 'error'
)
```

## 功能特性

### 1. Loop 測試配置
- **設定位置**: SFC Configuration Dialog
- **配置項目**:
  - `Loop 測試`: 開關，啟用後會執行循環測試
  - `循環次數`: 設定循環次數 (1-9999)

### 2. 執行行為
- **非 Loop 模式**: 執行一次測試
- **Loop 模式**: 根據設定的次數重複執行測試
  - 每次循環會顯示當前循環進度
  - 循環計數器會即時更新顯示
  - 每次循環開始前會重置測試項目的狀態
  - 每次循環結束後會顯示完成訊息

### 3. 與 runAllTest 模式的整合
- Loop 測試可以與 runAllTest 模式同時使用
- 每次循環都會遵循 runAllTest 的錯誤處理邏輯
- 顯示每次循環的錯誤摘要

## 使用範例

### 設定 Loop 測試
1. 點擊「SFC 設定」按鈕
2. 啟用「Loop 測試」開關
3. 設定循環次數（例如: 3 次）
4. 點擊「儲存」

### 執行測試
1. 掃描或輸入產品序號
2. 點擊「開始測試」
3. 系統會執行 3 次循環測試
4. Loop 計數器會顯示當前循環次數 (1/3, 2/3, 3/3)
5. 測試完成後會顯示總結: 「測試完成: PASS (共 3 次循環)」

## 測試驗證

### 測試腳本
使用 Python 模擬循環邏輯驗證:
```python
# 測試 Loop 測試邏輯
sfcConfig = {
    'loopEnabled': True,
    'loopCount': 3
}

totalLoops = sfcConfig['loopCount'] if sfcConfig['loopEnabled'] else 1

for currentLoop in range(totalLoops):
    print(f"Loop {currentLoop + 1}/{totalLoops}")
    # 執行測試項目...
```

### 預期結果
- Loop 1/3: 執行所有測試項目
- Loop 2/3: 執行所有測試項目
- Loop 3/3: 執行所有測試項目
- 測試完成: 共 3 次循環

## 注意事項
1. 循環測試會執行完整的測試流程，包括所有測試項目
2. 每次循環都會重新執行所有測量，不會使用之前的結果
3. 循環過程中可以隨時停止測試
4. Loop 計數器會即時更新，反映當前循環進度
5. 測試結果會基於最後一次循環的結果判定

## JavaScript 變數作用域說明

### 問題: 塊級作用域 (Block Scope)
在 JavaScript 中，使用 `let` 和 `const` 定義的變數具有**塊級作用域** (block scope)。這意味著：
- 變數只在定義它的程式碼區塊 `{ ... }` 內有效
- 在 `for` 循環內定義的變數，循環結束後就無法存取

### 錯誤範例
```javascript
for (let currentLoop = 0; currentLoop < totalLoops; currentLoop++) {
  let passCount = 0;        // 在循環內定義
  const errorItems = [];    // 在循環內定義

  // ... 執行測試
}

// ❌ 錯誤: passCount is not defined
console.log(passCount);

// ❌ 錯誤: errorItems is not defined
console.log(errorItems);
```

### 正確範例
```javascript
// 在循環外定義
let passCount = 0;
const errorItems = [];

for (let currentLoop = 0; currentLoop < totalLoops; currentLoop++) {
  // 重置值，而不是重新定義
  passCount = 0;
  errorItems.length = 0;  // 清空陣列

  // ... 執行測試
}

// ✅ 正確: 可以存取
console.log(passCount);
console.log(errorItems);
```

### 修正方式
1. **將變數定義移到循環外部**: 使用 `let` 和 `const` 在循環之前定義變數
2. **在循環內重置值**: 每次循環時重置變數的值，而不是重新定義
3. **使用 `array.length = 0` 清空陣列**: 這比重新建立新陣列更有效率

## 相關檔案
- `frontend/src/views/TestMain.vue`: 主要修改檔案
- `frontend/src/api/tests.js`: 測試執行 API
