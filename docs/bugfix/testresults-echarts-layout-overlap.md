---
title: TestResults 歷史趨勢圖表排版重疊問題
date: 2026-03-26
component: frontend/src/views/TestResults.vue
composable: frontend/src/composables/useTestTimeline.js
severity: high
status: fixed
---

# Bug：歷史趨勢 ECharts 圖表元素重疊及統計卡被截斷

## 問題描述

**重現步驟：**

1. 進入 TestResults 頁面，切換至「歷史趨勢」Tab
2. 查詢有測試資料的專案（例如 Demo Project 2 / Test Station 3）
3. 觀察統計卡片和圖表的顯示

**問題 1：統計卡片只顯示前 2 格**
- 統計卡片應顯示「總測試次數 / 通過 / 失敗 / 通過率」4 格
- 實際只看到「總測試次數」和「通過」，右側「失敗」和「通過率」被截斷

**問題 2：圖表 legend 與 Y 軸文字重疊**
- ECharts legend 項目（通過、失敗、通過率）垂直顯示在左側
- 與左 Y 軸的軸名稱「測試次數」及數字標籤重疊，造成文字難以閱讀
- 圖表的柱狀圖區域被壓縮到左側一小角

**截圖：** `.cp-images/pasted-image-2026-03-26T05-04-27-410Z.png`

---

## 根本原因分析

### 問題 1：統計卡片截斷

**原因：`el-row :gutter` 產生負 margin，被 `overflow: hidden` 截斷**

Element Plus 的 `el-row` 使用 CSS 負 margin 來補償 `el-col` 的 padding，實現 gutter 間距系統。即使設定 `:gutter="0"`，部分 Element Plus 版本仍保留 `-8px` 的負 margin。

```html
<!-- 舊版 template -->
<el-card class="stats-card" shadow="never">
  <el-row :gutter="0" class="stats-row">
    <el-col :span="6" class="stat-col stat-col--total">...</el-col>
    <el-col :span="6" class="stat-col stat-col--pass">...</el-col>
    <el-col :span="6" class="stat-col stat-col--fail">...</el-col>
    <el-col :span="6" class="stat-col stat-col--rate">...</el-col>
  </el-row>
</el-card>
```

```css
/* el-card 設定了 overflow: hidden */
.stats-card {
  overflow: hidden;  /* ← 截斷了 el-row 的負 margin 溢出部分 */
}
```

**觸發順序：**

```
el-row 產生 margin-right: -Npx
  → .stats-row 寬度超出 .el-card__body
  → overflow: hidden 截斷右側
  → 最右邊的 el-col 看不到
```

### 問題 2：ECharts legend 與 Y 軸重疊

**原因：legend 位置設定與 grid 邊距互相衝突**

初版圖表設定中 legend 放在頂部中央：

```js
legend: {
  top: 44,
  left: 'center',
  orient: 'horizontal',
  // ...
},
grid: {
  top: 80,
  left: '3%',
  containLabel: true
},
yAxis: {
  name: '次數',         // ← Y 軸名稱顯示在軸的上方
  nameLocation: 'end',
}
```

後來加入雙 Y 軸（測試次數 + 通過率）並嘗試將 legend 改為右側垂直排列時，問題更嚴重：

```js
legend: {
  top: 10,
  right: 16,
  orient: 'vertical',   // ← 垂直排列在右側
},
grid: {
  right: 80,            // ← 為 legend 留空間
  left: 16,             // ← 太小，containLabel 撐開後擠壓
  top: 60,
}
yAxis: [
  { name: '測試次數', nameLocation: 'end' },   // ← 顯示在左上
  { name: '通過率 %', nameLocation: 'end' },   // ← 顯示在右上
]
```

**重疊的根本問題：**

| 元素 | 位置 | 衝突對象 |
|------|------|----------|
| title `測試趨勢` | 左上或中央 | legend（右上）的文字行 |
| Y 軸 `name: '測試次數'` | 左 Y 軸頂端 | legend 的第一個項目 |
| Y 軸 `name: '通過率 %'` | 右 Y 軸頂端 | legend 的最後一個項目 |
| legend（垂直） | right:16 | 右 Y 軸的數字標籤（`100%`、`80%`...） |

`containLabel: true` 會根據軸標籤實際寬度自動調整 grid，但當數值很大（如 429）時，左 Y 軸標籤寬度可達 30px，加上 `left: 16`，grid 左邊界實際位置才能確定，legend 如果也在同側就會衝突。

---

## 修正方式

### 修正 1：統計卡片 — 用原生 CSS flex 取代 `el-row`

**檔案：** `frontend/src/views/TestResults.vue`

**Template 修改：**

```html
<!-- 修正後：改用純 div，不依賴 Element Plus Grid -->
<el-card class="stats-card" shadow="never">
  <div class="stats-row">
    <div class="stat-col stat-col--total">
      <el-statistic title="總測試次數" :value="..." />
    </div>
    <div class="stat-col stat-col--pass">
      <el-statistic title="通過" :value="..." />
    </div>
    <div class="stat-col stat-col--fail">
      <el-statistic title="失敗" :value="..." />
    </div>
    <div class="stat-col stat-col--rate">
      <el-statistic title="通過率" :value="..." />
    </div>
  </div>
</el-card>
```

**CSS 修改：**

```css
/* 舊版（有問題） */
.stats-row {
  margin: 0 !important;  /* 無法完全消除 el-row 的負 margin */
}

/* 修正後：原生 flex，無 margin 問題 */
.stats-row {
  display: flex;
  width: 100%;
}

.stat-col {
  flex: 1 1 0;    /* 4 格均等分配 */
  min-width: 0;   /* 防止 flex 子項超出 */
  padding: 20px 12px;
  text-align: center;
  position: relative;
}

/* 分隔線用 ::before pseudo-element，不受 overflow 影響 */
.stat-col + .stat-col::before {
  content: '';
  position: absolute;
  left: 0; top: 20%; height: 60%;
  width: 1px;
  background: #e4e7ed;
}
```

同時為各格加入色彩背景以視覺區分：

```css
.stat-col--total { background: #f4f4f5; }   /* 灰  */
.stat-col--pass  { background: #f0f9eb; }   /* 淡綠 */
.stat-col--fail  { background: #fef0f0; }   /* 淡紅 */
.stat-col--rate  { background: #ecf5ff; }   /* 淡藍 */
```

---

### 修正 2：ECharts 圖表 — 整理佈局層次

**檔案：** `frontend/src/composables/useTestTimeline.js`

**核心原則：每個視覺元素只佔一個區域，不相互競爭空間。**

```
┌──────────────────────────────────────────────────┐
│  title（測試趨勢）        [top: 6, left: center]  │
│  subtext（共N天·M次）                              │
├──────────────────────────────────────────────────┤
│                                                  │
│  [left Y axis]   繪圖區（grid）   [right Y axis]  │
│                  柱狀圖 + 折線    %標籤（藍色）    │
│                                                  │
├──────────────────────────────────────────────────┤
│  legend: 通過 ● 失敗 ● 通過率%  [bottom: 4]       │
└──────────────────────────────────────────────────┘
```

**關鍵設定：**

```js
// 1. legend 移到底部水平排列 → 不與任何軸元素競爭
legend: {
  bottom: 4,
  left: 'center',
  orient: 'horizontal',
  itemGap: 20,
},

// 2. grid 對應 legend 在底部的配置
grid: {
  top: 60,                               // title 2 行的高度
  left: 8,
  right: 8,
  bottom: xRotate > 0 ? 68 : 44,        // legend(24px) + x 標籤 + 旋轉補償
  containLabel: true                     // 動態處理 Y 軸標籤寬度
},

// 3. Y 軸移除 name → 避免在軸頂產生額外文字佔位
yAxis: [
  {
    // 舊: name: '測試次數'  ← 刪除
    axisLabel: { color: '#606266' },  // 左軸：黑色數字
  },
  {
    // 舊: name: '通過率 %'  ← 刪除
    axisLabel: { color: '#409EFF', formatter: '{value}%' },  // 右軸：藍色 %
    interval: 25,   // 0/25/50/75/100，較稀疏
  }
],

// 4. 通過率 series 改名含 % → legend 直接說明含義
series: [
  { name: '通過率%', type: 'line', ... }  // 舊: '通過率'
]
```

**同時加入的額外改善：**

```js
// initChart 加防護：避免重複 init 殘留舊實例
const initChart = () => {
  if (!chartRef.value) return
  if (chartInstance.value) {
    chartInstance.value.dispose()   // ← 新增：先清除舊實例
  }
  chartInstance.value = echarts.init(chartRef.value)
  updateChart()
  window.addEventListener('resize', handleResize)
}

// chart-card 的 el-card__body padding 減小，讓圖表更貼邊
// 在 TestResults.vue CSS 加入：
.chart-card :deep(.el-card__body) {
  padding: 12px 4px;
}
```

---

## 除錯過程

### 第一輪：加入雙 Y 軸，重構佈局

**操作：** 加入通過率折線圖（第二 Y 軸），將 legend 從頂部水平改為右側垂直。

**問題：** 截圖顯示 legend 文字「測試次數 / 失敗 / 通過率」出現在 Y 軸左側，與軸數字重疊。

**診斷過程：**
1. 檢查 `grid.left: 16` + `containLabel: true` → 發現 Y 軸數字「429」寬約 28px，加上 16px margin 共 44px，但 legend 垂直排在 `right: 16`，同時右 Y 軸標籤「100%」需要約 36px，grid 實際可用寬度被大幅壓縮
2. 注意到 `yAxis.name: '測試次數'` 的文字顯示位置是 `nameLocation: 'end'`（Y 軸頂端），正好與 legend 的第一個項目位置重合

**嘗試的方向：**
- 調整 `grid.right: 80` → 圖表可用寬度縮小，柱子更細
- 調整 `grid.left: '10%'` → 百分比可自適應，但 legend 仍在右側擠壓

**結論：** 右側同時放 legend（垂直）和右 Y 軸無法避免衝突，需要換策略。

### 第二輪：重新分配視覺空間

**決策：** 將 legend 移到底部，完全清空上方和左右側的空間競爭。

**同時移除 Y 軸 `name`：**
- Y 軸名稱和 legend 項目重複說明同一件事（左 Y 軸 = 測試次數 = legend 中的通過/失敗；右 Y 軸 = 通過率 = legend 中的通過率%）
- 移除軸名，改用**軸標籤顏色**區分：左軸黑色數字（次數），右軸藍色 `%`（通過率）

**grid bottom 計算：**
```
legend 高度:  ~24px  (底部 4px + itemHeight 12px + 文字行距)
x 軸標籤:     ~16px  (無旋轉時)
旋轉補償:     +24px  (>14天時旋轉 45°)

→ 無旋轉: bottom = 44
→ 有旋轉: bottom = 68
```

### 第三輪：統計卡片問題

**觀察：** 圖片中統計卡只顯示前 2 格，右側 2 格消失。

**診斷：**
1. 確認 template 結構有 4 個 `el-col :span="6"` → HTML 正確
2. 確認 CSS `stats-card { overflow: hidden }` → 懷疑截斷
3. 確認 `el-row :gutter="0"` → 在 Element Plus 中，gutter 實作是透過 `el-col` 的 padding 和 `el-row` 的負 margin 配對，gutter=0 的行為依版本不同
4. 用 DevTools 模擬：el-row 的實際 margin 為 `-8px`，超出 card 邊界被 `overflow: hidden` 截掉

**修正：** 直接用原生 `div` + `display: flex` 取代，繞過 Element Plus Grid 系統的負 margin 機制。

---

## 修正前後對比

| 項目 | 修正前 | 修正後 |
|------|--------|--------|
| 統計卡格數 | 只顯示 2 格（右側截斷） | 4 格完整顯示，各有顏色背景 |
| legend 位置 | 右側垂直 / 頂部水平（與軸重疊） | 底部水平，不與任何元素衝突 |
| Y 軸區分方式 | `name: '測試次數'` 文字 | 軸標籤顏色（左黑右藍）+ legend |
| 圖表自適應 | `grid.left` 固定，大數值溢出 | `containLabel: true` + 百分比邊距 |
| 重複 init 防護 | 無 | `initChart` 先 `dispose` 舊實例 |

---

## 關鍵知識點

### ECharts 佈局注意事項

1. **`title`、`legend`、`grid` 是獨立的佈局元件**，ECharts 不會自動避免它們重疊，需要手動規劃每個元件佔用的區域。

2. **`containLabel: true` 的作用**：讓 `grid` 的邊界自動向內縮，以容納 Y 軸的數字標籤。但它只處理「軸標籤」，不處理 `legend` 或 `title`。

3. **`yAxis.name` 顯示位置**：`nameLocation: 'end'` 會把名稱顯示在 Y 軸的頂端（最大值上方），容易與 `legend` 的 `top` 位置衝突。

4. **雙 Y 軸的空間規劃**：右 Y 軸的標籤（如 `100%`）需要 `grid.right` 留有足夠空間，如果同時有右側 `legend`，兩者會互相擠壓。

### Element Plus Grid 系統的負 margin 陷阱

```
el-row 實作：
  margin-left: -(gutter/2)px
  margin-right: -(gutter/2)px

el-col 實作：
  padding-left: (gutter/2)px
  padding-right: (gutter/2)px

→ 即使 gutter=0，仍可能有預設的最小 margin
→ 外層容器如有 overflow: hidden，會截斷負 margin 溢出部分
→ 解法：改用原生 CSS flex，或對 el-row 加 overflow: visible
```
