# Bug Fix: TestMain Navigation Bar Overflow (Scrollbar)

**日期：** 2026-03-10
**影響檔案：** `frontend/src/views/TestMain.vue`

## 問題描述

在 `TestMain.vue` 的 Top Info Bar（`el-card class="info-card"`）中，當導航按鈕使用 `size="default"` 時，按鈕總寬度超出 `el-col :span="7"` 的空間，導致 `info-card` 出現 scrollbar。

## 根本原因

`el-row` 的 span 分配原本為：
- 專案選擇器：`span="5"`
- 站別選擇器：`span="5"`
- 使用者：`span="4"`
- 版本：`span="3"`
- 導航按鈕區：`span="7"`（總計 = 24）

6 個 `size="default"` 按鈕（測試計劃、測試結果查詢、專案管理、使用者管理、報表分析、登出）在 `span="7"` 的寬度內放不下，造成 overflow。

## 解決方式

1. 移除「版本」欄位（`span="3"`），釋出空間
2. 「使用者」欄位從 `span="4"` 縮減為 `span="3"`
3. 導航按鈕區從 `span="7"` 擴大為 `span="11"`

最終 span 分配：5 + 5 + 3 + 11 = 24 ✅

4. 「登出」按鈕也統一改為 `size="default"`（原本誤設為 `size="small"`）

## 修改前後對比

```html
<!-- 修改前 -->
<el-col :span="4">使用者</el-col>
<el-col :span="3">版本</el-col>
<el-col :span="7" style="text-align: right; white-space: nowrap;">
  <!-- 6 個按鈕 → 空間不足，出現 scrollbar -->
</el-col>

<!-- 修改後 -->
<el-col :span="3">使用者</el-col>
<!-- 版本欄位移除 -->
<el-col :span="11" style="text-align: right; white-space: nowrap;">
  <!-- 6 個按鈕 → 空間充足，無 scrollbar -->
</el-col>
```

## 相關變更

同次修改也在 `TestMain.vue` 導航列加入「報表分析」按鈕（導向 `/analysis`），以及在 `AppNavBar.vue` 新增對應按鈕，保持兩套導航的功能一致性。
