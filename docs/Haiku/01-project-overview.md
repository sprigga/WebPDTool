# 01 - 專案概述

## 專案背景

WebPDTool 是一個完整的 Web 應用型重構，從桌面應用 PDTool4 遷移到現代 Web 技術棧。它是一個自動化硬體測試系統，用於執行製造產品的測試計劃、驗證結果流程並記錄測試成果。

## 核心定位

**PDTool4 → WebPDTool 遷移**
- ✅ 保留所有測試邏輯和驗證規則
- ✅ 遷移到現代 Web 架構
- ✅ 改進使用者介面和開發體驗
- ✅ 支援分散式部署和擴充

## 關鍵特性

### 1. PDTool4 完全相容性
- 測量驗證邏輯完全複製 (7 限制型別 × 3 值型別)
- runAllTest 模式：故障後繼續執行，會話結束彙總錯誤
- CSV test plan 匯入格式完全相容
- 測試結果驗證行為完全一致

### 2. 現代化技術棧
```
前端：Vue 3 + Vite (新一代前端框架)
後端：FastAPI + SQLAlchemy 2.0 (非同步優先)
資料庫：MySQL 8.0 + Redis (效能優化)
DevOps: Docker + Docker Compose (一鍵部署)
```

### 3. 非同步優先設計
- 所有 I/O 操作均為 async/await
- 高效併發測試執行
- 非阻塞硬體通訊

### 4. 模組化架構
- 清晰的層次劃分 (API → Service → Measurement → Data)
- 20+ 測量型別實現
- 插件式測量系統

### 5. 企業級功能
- JWT 認證和基於角色的訪問控制 (RBAC)
- 使用者、專案、工站管理
- 測試計劃 CRUD 和批量匯入
- 詳細的結果查詢、匯出、分析

## 系統目標

| 目標 | 實現方式 |
|------|---------|
| **快速測試** | 非同步 I/O + 併發控制 |
| **資料完整** | 關係型資料庫 + 事務管理 |
| **易於擴充** | 插件式設計 + 模組化架構 |
| **可視化** | ECharts 資料圖表 + 實時 UI 更新 |
| **高可靠** | JWT 安全認證 + 錯誤恢復 |

## 使用場景

### 製造測試
```
產品進入測試工站
    ↓
營運人員/工程師啟動 test session
    ↓
系統自動執行測試計劃的所有專案
    ↓
測量資料與 specifications 對比驗證
    ↓
生成 PASS/FAIL 結果
    ↓
匯出報表或繼續下一產品
```

### 專案管理維度
```
ADMIN
  ├─ 管理使用者和角色
  ├─ 配置系統引數
  └─ 檢視全域性報表

ENGINEER
  ├─ 建立/編輯測試計劃
  ├─ 匯入 CSV test plan
  ├─ 專案和工站管理
  └─ 執行測試

OPERATOR
  ├─ 執行已準備的測試
  ├─ 檢視測試結果
  └─ 匯出報告
```

## 系統定位

**WebPDTool = PDTool4 功能 + Web 應用優勢**

```
桌面應用 (PDTool4)
  ├─ ✅ 成熟的測試邏輯
  ├─ ✅ 經過現場驗證
  └─ ❌ 難以遠端、擴充、協作

Web 應用 (WebPDTool)
  ├─ ✅ 任何瀏覽器訪問
  ├─ ✅ 多使用者併發
  ├─ ✅ 中心化資料管理
  ├─ ✅ 實時監控和分析
  └─ ✅ 容器化部署
```

## 產品時間線

| 階段 | 狀態 | 描述 |
|------|------|------|
| **Phase 1** | ✅ 完成 | API 框架 + 基礎 UI |
| **Phase 2** | ✅ 完成 | 測量系統 + 測試執行 |
| **Phase 3** | ✅ 完成 | 使用者管理 + 認證 |
| **Phase 4** | 進行中 | 報表分析 (ReportAnalysis.vue 在開發) |
| **Phase 5** | 規劃中 | WebSocket 實時更新 + 分散式執行 |

## 技術亮點

### 1. 完整的非同步 I/O
```python
# 所有資料庫操作
async def get_test_plan(db: AsyncSession, station_id: int):
    result = await db.execute(...)

# 所有硬體通訊
async def send_command(self, command: str) -> str:
    response = await instrument.execute(command)

# 所有測試執行
async def execute_test_session(...):
    for test_item in items:
        result = await measurement_service.execute()
```

### 2. 三相測量生命週期
```python
async def prepare(params):     # 配置階段
    # 設定硬體引數、分配資源

async def execute(params):      # 執行階段
    # 傳送命令、採集資料、返回結果

async def cleanup():            # 清理階段
    # 重置安全狀態、釋放資源
```

### 3. 測量驗證 10 進制
```
limit_type:   9 種 (lower/upper/both/equality/inequality/partial/none/...)
value_type:   3 種 (string/integer/float)
驗證邏輯：21 種 = 7 限制 × 3 值型別
```

### 4. Singleton 硬體管理
```python
# 確保全域性只有一個連線池
class InstrumentManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

## 程式碼規模

| 元件 | 程式碼行數 | 檔案數 |
|------|---------|--------|
| 後端 Python | ~15,000 | 40+ |
| 前端 JavaScript | ~8,000 | 25+ |
| 資料庫 SQL | ~2,000 | 1 |
| 測試程式碼 | ~5,000 | 15+ |
| **總計** | **~30,000** | **80+** |

## 支援的硬體

### 通訊介面
- Serial/ComPort (RS-232/485)
- TCPIP/Network
- Console/UART
- Modbus (待完善)

### 測量型別
- **電源類**: PowerRead, PowerSet (多通道)
- **RF 測試**: LTE TX/RX, WiFi, BLE, CMW100
- **資料採集**: GetSN (獲取序列號), CommandTest
- **製造整合**: SFCtest, OPjudge, SFC 日誌
- **硬體控制**: Relay, ChassisRotation, Wait
- **其他**: MDO34 示波器，L6MPU, 通用 Other 型別

## 開發成熟度

| 方面 | 成熟度 | 備註 |
|------|--------|------|
| 核心 API | ⭐⭐⭐⭐⭐ | 完全實現，生產就緒 |
| 測試執行 | ⭐⭐⭐⭐⭐ | 穩定可靠 |
| 使用者管理 | ⭐⭐⭐⭐ | 完整實現 |
| 報表分析 | ⭐⭐⭐ | 進行中 |
| 硬體整合 | ⭐⭐⭐ | 框架完善，驅動待補充 |
| 實時更新 | ⭐⭐ | WebSocket 計劃中 |

## 下一步閱讀

- **瞭解架構**: 閱讀 [02-architecture.md](02-architecture.md)
- **學習 API**: 檢視 [06-api-endpoints.md](06-api-endpoints.md)
- **開始開發**: 參考 [10-development-guide.md](10-development-guide.md)
- **系統部署**: 檢視 [09-deployment-devops.md](09-deployment-devops.md)
