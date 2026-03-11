# WebPDTool 程式碼庫分析 - Haiku Version

**分析日期:** 2026 年 3 月 11 日
**專案名稱:** WebPDTool - 基於 Web 的 PDTool4 測試系統
**架構版本:** Vue 3 + FastAPI + SQLAlchemy 2.0 + MySQL 8.0

---

## 📚 文件導航

本分析將 WebPDTool 專案分解為 10 個核心主題，每個主題都有詳細的文件：

### 核心文件

1. **[專案概述](01-project-overview.md)**
   - 專案背景和關鍵特性
   - 系統定位和目標

2. **[架構設計](02-architecture.md)**
   - 整體系統架構
   - 三層架構詳解
   - 關鍵架構模式

3. **[後端結構](03-backend-structure.md)**
   - API 層、Service 層、Measurement 層
   - 資料模型設計
   - Core 模組

4. **[前端結構](04-frontend-structure.md)**
   - View 元件和路由
   - 狀態管理 (Pinia)
   - API 用戶端設計

5. **[資料庫架構](05-database-schema.md)**
   - 7 個核心表結構
   - 關係和索引
   - 效能考慮

6. **[API 端點](06-api-endpoints.md)**
   - 40+ API 路由詳解
   - 請求/響應示例
   - 錯誤處理

7. **[測量系統](07-measurement-system.md)**
   - 20+ 測量型別實現
   - 驗證邏輯 (7 種限制型別 × 3 種值型別)
   - PDTool4 相容性

8. **[認證與安全](08-authentication-security.md)**
   - JWT token 流程
   - 基於角色的訪問控制 (RBAC)
   - 密碼安全策略

9. **[部署與維運](09-deployment-devops.md)**
   - Docker Compose 配置
   - 環境變數
   - 開發和生產部署

10. **[開發指南](10-development-guide.md)**
    - 程式碼風格規範 (Python/Vue 3)
    - 快速啟動指南
    - 新增新功能的具體步驟
    - 常用開發命令參考
    - 測試策略和 CI/CD

---

## 🎯 快速概覽

### 技術棧總結

```
前端：Vue 3 + Vite + Pinia + Element Plus + ECharts
後端：FastAPI + SQLAlchemy 2.0 + Pydantic + Uvicorn
資料庫：MySQL 8.0 + Redis (日誌)
DevOps: Docker + Docker Compose + Nginx
```

### 關鍵數字

| 指標 | 數值 |
|------|------|
| 後端程式碼行數 | ~15,000 行 (Python) |
| 前端程式碼行數 | ~8,000 行 (Vue 3/JavaScript) |
| 資料庫表數 | 7 個核心表 |
| API 端點數 | 40+ |
| 測量型別數 | 20+ |
| View 元件數 | 10 個 |
| Service 類數 | 6 個 |

### 核心元件

```
├── API 層 (FastAPI)
│   ├── auth.py - 認證
│   ├── users.py - 使用者管理
│   ├── projects.py - 專案管理
│   ├── stations.py - 工站管理
│   ├── testplans.py - 測試計劃
│   ├── tests.py - 測試執行
│   ├── measurements.py - 測量
│   ├── dut_control.py - 裝置控制
│   └── results/ - 結果分析
│
├── Service 層
│   ├── TestEngine - 測試編排
│   ├── MeasurementService - 測量執行
│   ├── InstrumentManager - 硬體管理
│   ├── TestPlanService - 計劃管理
│   ├── ReportService - 報表生成
│   └── AuthService - 認證服務
│
├── 測量抽象層
│   ├── BaseMeasurement - 基類
│   └── Implementations - 20+ 具體實現
│
└── 資料層
    ├── Models - ORM 模型 (7 表)
    └── Schemas - Pydantic 驗證
```

---

## ✨ 核心特性

✅ **PDTool4 完全相容** - 測量驗證邏輯完全複製
✅ **非同步優先設計** - 所有 I/O 操作均為非同步
✅ **runAllTest 模式** - 故障後繼續執行 (如 PDTool4)
✅ **JWT 認證** - 基於角色的訪問控制
✅ **實時日誌** - Redis 支援的日誌流
✅ **Docker 支援** - 一鍵啟動完整環境
✅ **模組化架構** - 清晰的關注點分離

---

## 🚀 快速開始

### 啟動開發環境

```bash
# Docker 方式 (推薦)
docker-compose up -d

# 訪問地址
# 前端：http://localhost:9080
# 後端 API: http://localhost:9100
# 文件：http://localhost:9100/docs
```

### 本地開發

```bash
# 後端
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 9100

# 前端
cd frontend
npm install && npm run dev
```

### 執行測試

```bash
# 所有測試
pytest

# 單元測試
pytest -m unit

# 覆蓋率報告
pytest --cov=app tests/
```

---

## 📖 文件結構

```
docs/Haiku/
├── README.md (本檔案)
├── 01-project-overview.md
├── 02-architecture.md
├── 03-backend-structure.md
├── 04-frontend-structure.md
├── 05-database-schema.md
├── 06-api-endpoints.md
├── 07-measurement-system.md
├── 08-authentication-security.md
├── 09-deployment-devops.md
└── 10-development-guide.md
```

---

## 🔍 使用方式

### 對於新開發者
1. 從 [專案概述](01-project-overview.md) 開始瞭解專案背景
2. 閱讀 [架構設計](02-architecture.md) 理解系統整體結構
3. 按照 [開發指南](10-development-guide.md) 配置開發環境

### 對於功能實現
1. 檢視 [後端結構](03-backend-structure.md) 瞭解模組組織
2. 參考 [API 端點](06-api-endpoints.md) 設計新 API
3. 使用 [開發指南](10-development-guide.md) 中的最佳實踐

### 對於測試工程師
1. 參考 [API 端點](06-api-endpoints.md) 瞭解可用介面
2. 檢視 [測量系統](07-measurement-system.md) 理解測試概念
3. 使用 [部署與維運](09-deployment-devops.md) 啟動測試環境

### 對於維運/DevOps
1. 閱讀 [部署與維運](09-deployment-devops.md)
2. 參考 [認證與安全](08-authentication-security.md) 的安全配置
3. 檢視 [資料庫架構](05-database-schema.md) 進行資料管理

---

## 🎓 核心概念

### 三相測量生命週期
```
prepare() → execute() → cleanup()
   配置      執行       清理
```

### PDTool4 驗證邏輯 (7 種限制型別)
```
lower       ≥ 下限
upper       ≤ 上限
both        下限 ≤ 值 ≤ 上限
equality    = 期望值
inequality  ≠ 期望值
partial     字串包含匹配
none        總是通過
```

### 非同步執行模式 (runAllTest)
```
順序執行測試項，失敗不停止
收集所有錯誤→會話末尾彙總報告
```

---

## 📊 統計資料

### 程式碼統計
- Python 程式碼：~15,000 行
- JavaScript 程式碼：~8,000 行
- SQL 程式碼：~2,000 行
- 測試程式碼：~5,000 行

### 功能統計
- ORM 表：7 個
- API 端點：40+
- 測量型別：20+
- UI 視圖：10 個
- Service 類：6 個
- Pinia 儲存：3 個

---

## 📝 更新記錄

| 日期 | 版本 | 更新內容 |
|------|------|---------|
| 2026-03-11 | 1.0 | 初始分析完成，整理成 Haiku 版本 |

---

## ❓ FAQ

**Q: 如何新增新的測量型別？**
A: 檢視 [測量系統](07-measurement-system.md) 和 [開發指南](10-development-guide.md)

**Q: 如何修改資料庫架構？**
A: 參考 [資料庫架構](05-database-schema.md) 和部署章節

**Q: 如何新增新的 API 端點？**
A: 檢視 [API 端點](06-api-endpoints.md) 和 [開發指南](10-development-guide.md)

**Q: 系統支援哪些使用者角色？**
A: 檢視 [認證與安全](08-authentication-security.md)

**Q: 如何部署到生產環境？**
A: 參考 [部署與維運](09-deployment-devops.md)

---

## 🔗 相關資源

- **專案根目錄:** [AGENTS.md](/AGENTS.md), [CLAUDE.md](/CLAUDE.md)
- **後端文件:** [backend/README.md](/backend/README.md)
- **前端文件:** [frontend/README.md](/frontend/README.md)
- **資料庫文件:** [database/README.md](/database/README.md)
- **API 文件:** http://localhost:9100/docs (執行時)

---

**文件維護:** 2026-03-11
**分析工具:** Claude Haiku 4.5
