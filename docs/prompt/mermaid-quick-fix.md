# Mermaid 架構圖優化 Prompt - 快速修復版

## 使用時機
適用於已存在的 Mermaid UML 架構圖出現特定問題時，進行針對性修復。

---

## Prompt 模板

修復 README.md 中「整體系統架構圖」的以下問題：

### 問題 1：[描述問題]
**範例**：API 層節點文字被遮蔽

**解決方案**：為 API 層節點增加 width 樣式，設定適當寬度（140-170px）

```mermaid
%% 為每個 API 節點設定寬度
style AuthAPI width:140px
style ProjectsAPI width:160px
style StationsAPI width:160px
```

### 問題 2：[描述問題]
**範例**：字型太小

**解決方案**：調整 font-size 為 18-20px

```mermaid
%% 主層級 20px
style Client font-size:20px
style Frontend font-size:20px

%% 子層級 18px
style API font-size:18px
```

### 問題 3：[描述問題]
**範例**：布局擁擠

**解決方案**：在 API 層子圖新增 direction TB

```mermaid
subgraph API["API 層 (7個模組)"]
    direction TB
    AuthAPI["🔐 Auth API"]
    %% ...
end
```

---

## 常見問題與解決方案

### 文字遮蔽問題
**症狀**：節點內文字顯示不完整或溢出

**解決方案**：
```mermaid
%% 為節點設定固定寬度
style NodeName width:150px

%% 使用 <br/> 換行
NodeName["第一行<br/>第二行<br/>第三行"]
```

### 字型問題
**症狀**：字型太小或太大

**解決方案**：
```mermaid
%% 設定字型大小（單位：px）
style SubgraphName font-size:18px
```

### 布局問題
**症狀**：圖形過寬或過高

**解決方案**：
```mermaid
%% 主圖使用垂直布局
graph TB

%% 子圖使用垂直布局
subgraph SubgraphName
    direction TB
end
```

### 連線混亂問題
**症狀**：連線交叉過多，難以理解

**解決方案**：
```mermaid
%% 簡化連線，使用虛線表示次要連線
Main -.-> External

%% 減少交叉連線，改用分層結構
Layer1 --> Layer2
Layer2 --> Layer3
```

### 色彩問題
**症狀**：色彩不統一或對比度不足

**解決方案**：
```mermaid
%% 定義統一的樣式類別
classDef clientStyle fill:#e1f5ff,stroke:#0277bd,stroke-width:2px,color:#000

%% 應用樣式
class Node1,Node2,Node3 clientStyle
```

---

## 快速修復檢查清單

使用前確認：
- [ ] 問題具體描述清楚
- [ ] 知道問題發生的檔案和行號
- [ ] 有範例或截圖可參考

使用後驗證：
- [ ] 問題已解決
- [ ] 無新問題產生
- [ ] 圖表正常顯示

---

## 使用範例

### 範例 1：修復文字遮蔽

```
修復 README.md 中「整體系統架構圖」的以下問題：

問題：API 層節點「Results API」文字被遮蔽

解決：為 ResultsAPI 節點增加 width 樣式
style ResultsAPI width:160px

請直接修改程式碼，不要移除原有註解。
```

### 範例 2：調整字型大小

```
修復 README.md 中「整體系統架構圖」的以下問題：

問題：整體字型太小，閱讀困難

解決：將所有字型大小調整為 18-20px
- 主層級（Client/Frontend/Backend/Database/External）：20px
- 子層級（API/Services/Measurements/Models）：18px

請直接修改程式碼，不要移除原有註解。
```

### 範例 3：修改布局方向

```
修復 README.md 中「整體系統架構圖」的以下問題：

問題：API 層節點水平排列，導致圖形過寬

解決：在 API 層子圖新增 direction TB，改為垂直排列

subgraph API["API 層 (7個模組)"]
    direction TB
    AuthAPI["🔐 Auth API"]
    %% ...
end

請直接修改程式碼，不要移除原有註解。
```

---

## 注意事項

1. **保留註解**：修改時保留原有 `%%` 註解，方便後續維護
2. **最小變更**：只修改必要的部分，避免引入新問題
3. **測試驗證**：修改後在 GitHub 或支援 Mermaid 的編輯器中驗證
4. **備份原檔**：重要修改前先備份原檔
