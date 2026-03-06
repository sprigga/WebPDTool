# 問題追蹤和解決方案文檔

## Issue: TestMain 導覽列缺少「測試結果查詢」按鈕

### 問題描述
**錯誤日期**: 2026-03-06
**錯誤類型**: UI 元件缺失
**發生位置**: `frontend/src/views/TestMain.vue`（頂部導覽列按鈕組）

`TestMain.vue` 的頂部導覽列缺少「測試結果查詢」按鈕，使用者無法從測試主畫面直接跳轉至測試結果查詢頁面（`/results`）。

### 根本原因

`TestMain.vue` 使用自訂頂部資訊列，而非其他頁面共用的 `AppNavBar.vue` 元件。`AppNavBar.vue` 已包含「測試結果查詢」按鈕，但 `TestMain.vue` 的自訂按鈕組在實作時漏加了這個按鈕：

```html
<!-- 修正前：缺少測試結果查詢按鈕 -->
<el-button size="default" @click="navigateTo('/testplan')">測試計劃</el-button>
<el-button size="default" @click="navigateTo('/projects')">專案管理</el-button>
<el-button size="default" @click="navigateTo('/users')">使用者管理</el-button>
<el-button type="danger" size="default" @click="handleLogout">登出</el-button>
```

### 解決方案

在「測試計劃」和「專案管理」按鈕之間加入「測試結果查詢」按鈕：

```html
<!-- 修正後 -->
<el-button size="default" @click="navigateTo('/testplan')">測試計劃</el-button>
<el-button size="default" @click="navigateTo('/results')">測試結果查詢</el-button>
<el-button size="default" @click="navigateTo('/projects')">專案管理</el-button>
<el-button size="default" @click="navigateTo('/users')">使用者管理</el-button>
<el-button type="danger" size="default" @click="handleLogout">登出</el-button>
```

**修改的文件**: `frontend/src/views/TestMain.vue`（Line 64-75）

### 架構說明

- `AppNavBar.vue`（共用元件）：已有完整導覽按鈕，被 `TestResults.vue`、`TestPlanManage.vue`、`ProjectManage.vue`、`UserManage.vue` 使用
- `TestMain.vue`：因版面需要（專案/站別選擇器、使用者資訊），使用自訂頂部列而非 `AppNavBar`，需手動同步導覽按鈕

長期建議：將 `TestMain.vue` 改用 `AppNavBar.vue`，避免未來再次發生按鈕不同步的問題。

### 影響範圍

- `frontend/src/views/TestMain.vue`

### 變更歷史

| 日期 | 變更內容 |
|------|---------|
| 2026-03-06 | 新增「測試結果查詢」導覽按鈕 |
