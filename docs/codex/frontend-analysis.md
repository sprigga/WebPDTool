# Frontend Codebase Analysis

## Overview
- 技術棧: Vue 3 + Vite + Element Plus + Pinia + Axios + ECharts (vue-echarts)
- 入口: `frontend/src/main.js` 掛載 `App.vue`，註冊 router、Pinia、Element Plus 與全部 Element Plus Icons
- 架構: 單頁應用 (SPA)，核心由 routes/views 組成，API 與狀態集中管理

## Structure
- Entry/Shell: `frontend/src/main.js`, `frontend/src/App.vue`
- Routing: `frontend/src/router/index.js`
- API: `frontend/src/api/*.js`, 共用 Axios client 在 `frontend/src/api/client.js`
- State (Pinia): `frontend/src/stores/*.js`
- Composables: `frontend/src/composables/useMeasurementParams.js`
- Views: `frontend/src/views/*.vue`
- Components: `frontend/src/components/*.vue`
- Build Config: `frontend/vite.config.js`

## Routing & Auth
- 路由包含: `/login`, `/main`, `/test`, `/results`, `/analysis`, `/testplan`, `/config`, `/projects`, `/users`, `/instruments`
- `beforeEach` 導航守衛依 `authStore.isAuthenticated` 判斷是否可進入受保護路由
- 登入後導向 `/main`，未登入訪問受保護路由導向 `/login`

## API Layer
- `client.js` 以 `VITE_API_BASE_URL` 為 baseURL，未設定時使用空字串，透過 Vite proxy 轉發 `/api/*`
- Request Interceptor 會自動加上 `Authorization: Bearer <token>`
- Response Interceptor 統一處理錯誤訊息並在 401 時登出與導向 `/login`
- API 模組按功能拆分:
  - `auth.js` 使用者登入/登出/刷新
  - `tests.js` 測試 session、結果、執行與儀器操作
  - `measurements.js` 測量模板與驗證
  - `testplans.js` 測試計畫 CRUD、上傳與排序
  - `testResults.js` 查詢與匯出
  - `projects.js` 專案與站別
  - `users.js` 使用者 CRUD 與改密碼
  - `instruments.js` 儀器 CRUD
  - `analysis.js` 報表分析

## State Management
- `auth` store: token/user 由 localStorage 初始化與持久化，提供 login/logout 與 `isAuthenticated`
- `project` store: 專案與站別，支援記住選擇與批量載入站別
- `users` store: 使用者 CRUD 與 loading 狀態
- `instruments` store: 儀器列表與 loading 狀態

## Composables
- `useMeasurementParams`:
  - 載入測量模板與驗證
  - 依測試類型與 switch mode 動態計算參數
  - 參數欄位型態推斷與 select 選項提供

## Views Summary
- `Login.vue`: 登入畫面
- `TestMain.vue`: 主畫面，含專案/站別選擇、SFC 設定、測試計畫選擇、導航
- `TestExecution.vue`: 測試執行流程、儀器狀態與結果上傳
- `TestResults.vue`: 測試 session/結果查詢與匯出
- `ReportAnalysis.vue`: 統計分析與趨勢圖 (ECharts)
- `TestPlanManage.vue`: 測試計畫 CRUD、CSV 上傳、排序與驗證
- `ProjectManage.vue`: 專案與站別管理
- `UserManage.vue`: 使用者管理與改密碼
- `InstrumentManage.vue`: 儀器管理
- `SystemConfig.vue`: 簡易設定頁
- `TestHistory.vue`: 舊/簡易頁面 (目前未在 router 使用)

## Components
- `AppNavBar.vue`: 管理頁導航與登出
- `ProjectStationSelector.vue`: 專案/站別選擇器，與 project store 同步
- `DynamicParamForm.vue`: 依測量模板動態產生參數表單

## Build & Proxy
- `vite.config.js`:
  - dev server: `5678`
  - proxy: `/api` -> `http://localhost:8765`
  - alias: `@` -> `frontend/src`

## Observations
- `auth` 守衛僅依 token 是否存在，token 失效需等 API 401 才會登出
- `client.js` 在 401 時直接 `window.location.href` 重新導向，會觸發全頁刷新
- 部分檔案有大量 console log 與註解，若需產線品質可考慮整理
- `dist/` 與 `node_modules/` 存在於 repo，會影響檔案乾淨度與 diff
