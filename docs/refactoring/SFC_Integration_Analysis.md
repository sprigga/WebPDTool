# SFC 配置整合分析

**日期：** 2026-03-25
**分析範圍：** TestMain.vue SFC 配置 UI ↔ Backend SFC 服務 ↔ SFCLog DB 整合完整性

---

## 1. 現狀摘要

SFC（Shop Floor Control / 製造執行系統）配置功能呈「前端 UI 完整、後端骨架存在、兩端完全未連接」狀態。

| 層級 | 狀態 | 說明 |
|------|------|------|
| Frontend UI（對話框、表單） | ✅ 完整 | 6 個配置欄位 + Loop 設定 |
| Frontend → Backend API | ❌ 缺失 | 配置只存 localStorage，從未送後端 |
| Backend SFC 配置 CRUD API | ❌ 缺失 | 無任何 `/api/sfc/...` 路由 |
| Backend `SFCMeasurement` | ❌ Stub | `sleep(0.5)` → 永遠回傳 PASS |
| `SFCLog` DB 寫入 | ❌ 缺失 | Model 存在但從未被寫入 |
| SFC WebService/URL 整合 | ❌ 缺失 | 無 `SFCFunctions` 等效實作 |

---

## 2. Frontend 實作細節

### 2.1 SFC 配置 Dialog（`TestMain.vue`）

**觸發入口（line 76）：**
```html
<el-button @click="showSFCConfig = true">SFC 設定</el-button>
<el-switch v-model="sfcEnabled" @change="handleSFCToggle" />
```

**配置表單欄位（line 407–434）：**
```html
<el-form :model="sfcConfig" label-width="120px">
  <el-form-item label="SFC 路徑">    <!-- sfcConfig.path -->
  <el-form-item label="站點 ID">     <!-- sfcConfig.stationID -->
  <el-form-item label="線路名稱">    <!-- sfcConfig.lineName -->
  <el-form-item label="治具 ID">     <!-- sfcConfig.fixtureID -->
  <el-form-item label="資料庫">      <!-- sfcConfig.database -->
  <el-form-item label="日誌路徑">    <!-- sfcConfig.logPath -->
  <el-form-item label="Loop 測試">   <!-- sfcConfig.loopEnabled + loopCount -->
</el-form>
```

**reactive 資料結構（line 535–544）：**
```js
const sfcConfig = reactive({
  path: '',
  stationID: '',
  lineName: '',
  fixtureID: '',
  database: '',
  logPath: '',
  loopEnabled: false,
  loopCount: 1
})
```

### 2.2 儲存邏輯問題

**`saveSFCConfig()`（line 1372–1376）— 只存 localStorage，無 API call：**
```js
const saveSFCConfig = () => {
  ElMessage.success('SFC 配置已儲存')
  showSFCConfig.value = false
  addStatusMessage('SFC 配置已更新', 'success')
  // ← 無 await api.sfc.saveConfig(sfcConfig)
}
```

**`onMounted` 讀取（line 1667–1671）：**
```js
const savedConfig = localStorage.getItem('sfcConfig')
if (savedConfig) {
  Object.assign(sfcConfig, JSON.parse(savedConfig))
}
```

**`onUnmounted` 寫入（line 1677–1678）：**
```js
localStorage.setItem('sfcConfig', JSON.stringify(sfcConfig))
```

### 2.3 sfcEnabled 未影響測試執行

`sfcEnabled`（line 501）在測試執行邏輯中完全未被讀取。`handleSFCToggle`（line 1364）只顯示 status message，沒有任何副作用。

### 2.4 Loop 功能（已實作）

`sfcConfig.loopEnabled` 和 `loopCount` 有實際執行邏輯（line 821–823），這是 SFC 配置中**唯一已接通**的部分：
```js
const loopEnabled = sfcConfig.loopEnabled
const totalLoops = loopEnabled ? sfcConfig.loopCount : 1
```

---

## 3. Backend 實作細節

### 3.1 SFCMeasurement（純 Stub）

**位置：** `backend/app/measurements/implementations.py:1046–1060`

```python
class SFCMeasurement(BaseMeasurement):
    """Integrates with manufacturing execution systems"""

    async def execute(self) -> MeasurementResult:
        try:
            sfc_mode = get_param(self.test_params, "Mode", default="webStep1_2")
            self.logger.info(f"Executing SFC test with mode: {sfc_mode}")
            await asyncio.sleep(0.5)   # ← 假裝執行
            return self.create_result(result="PASS", measured_value=Decimal("1.0"))
        except Exception as e:
            self.logger.error(f"SFC test error: {e}")
            return self.create_result(result="ERROR", error_message=str(e))
```

- 無連線邏輯，無 HTTP/WebService 呼叫
- 無讀取 sfcConfig 的任何參數（path、stationID 等完全忽略）
- 永遠回傳 PASS

### 3.2 SFCLog Model（存在但從未被使用）

**位置：** `backend/app/models/sfc_log.py`

```python
class SFCLog(Base):
    __tablename__ = "sfc_logs"
    id = Column(Integer, primary_key=True, ...)
    test_session_id = Column(Integer, ForeignKey("test_sessions.id"), ...)
    timestamp = Column(TIMESTAMP, ...)
    command = Column(String(255), ...)
    response = Column(Text, ...)
    status = Column(String(50), ...)
    session = relationship("TestSession", back_populates="sfc_logs")
```

整個 codebase 中，`SFCLog` 只有在 `main.py` 和 `models/__init__.py` 中 import，**從未有任何程式碼向此 table 寫入資料**。

### 3.3 缺失的 SFC 配置 API

整個 `backend/app/api/` 目錄中，無任何 SFC 配置相關路由：
- 無 `GET /api/sfc/config`
- 無 `POST /api/sfc/config`
- 無 `GET /api/sfc/logs`

---

## 4. PDTool4 對應功能（缺口參考）

PDTool4 的 SFC 整合流程（`oneCSV_atlas_2.py` Lines 278–327）：

```python
if SFCway == 'WebService':
    step4Res = sfc_funcs.sfc_Web_step3_txt(PASSorFAIL, testtime, final_error_msgs)
elif SFCway == 'URL':
    step4Res = sfc_funcs.sfc_url_step3_txt(PASSorFAIL, testtime, final_error_msgs)
```

PDTool4 有完整的 4 步驟 SFC 工作流：
1. **Step 1** — 條碼驗證（barcode → MES 查詢）
2. **Step 2** — 測試開始通知
3. **Step 3** — 測試結束上傳結果
4. **Step 4** — 最終 PASS/FAIL 回報

WebPDTool 這 4 個步驟全部缺失。

---

## 5. 完整實作所需工作

### 5.1 Backend

1. **`backend/app/services/sfc_service.py`** — 新增 SFC 服務類別
   - WebService 模式（SOAP/REST 呼叫）
   - URL 模式（HTTP GET/POST）
   - Step 1–4 工作流
   - 寫入 `SFCLog` table
   - 錯誤重試邏輯

2. **`backend/app/api/sfc.py`** — 新增 SFC 配置 API
   - `GET /api/sfc/config` — 讀取當前配置
   - `POST /api/sfc/config` — 儲存配置
   - `GET /api/sfc/logs` — 查詢 SFC 通訊日誌

3. **`SFCMeasurement.execute()`** — 改為呼叫 `sfc_service`

### 5.2 Frontend

1. **`frontend/src/api/sfc.js`** — 新增 Axios API 客戶端
2. **`saveSFCConfig()`** — 改為呼叫 `POST /api/sfc/config`
3. **`sfcEnabled`** — 影響測試執行時是否呼叫 SFC 工作流
4. `onMounted` 從 API 讀取配置（而非 localStorage）

---

## 6. 影響等級

**HIGH** — 若生產線需要 MES/SFC 整合，此功能完全不可用。

**不影響：** Loop 測試功能已實作，不依賴 SFC 後端。

---

*參考文件：`docs/refactoring/PDTool4_to_WebPDTool_Gap_Analysis.md` §2.1*
