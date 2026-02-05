# Mermaid 繪製工整與規範圖表之最佳實踐指南

Mermaid 是一種 "Code-as-Diagram" 的工具，想要繪製出專業、易讀且好維護的圖表，核心在於**結構化思維**與**代碼規範**。本指南整理了五大關鍵建議。

---

## 1. 佈局邏輯：決定圖表的骨架

正確的流向與分組能大幅降低閱讀認知負荷。

### 方向選擇 (Direction)
* **TD (Top-Down)**：由上而下。
    * 適用場景：層級結構、決策樹、標準業務流程。
    * *優點*：符合人類閱讀清單的習慣。
* **LR (Left-Right)**：由左而右。
    * 適用場景：時間軸、數據流向 (Data Flow)、步驟極長的流程。
    * *優點*：善用寬螢幕空間，避免圖表過長。

### 模組化分組 (Subgraphs)
使用 `subgraph` 將相關邏輯（如：同一服務、同一階段）包裹起來。
* **規範**：子圖標題應清晰，內部流向可獨立設定（使用 `direction` 指令）。

---

## 2. 語法規範：代碼的可維護性

嚴禁將「顯示文字」直接作為「節點 ID」使用。

### ID 與 標籤分離原則
* **❌ 錯誤寫法**（難以維護）：
    ```mermaid
    graph TD
    [使用者輸入帳號密碼] --> [系統檢查資料庫]
    ```
* **✅ 推薦寫法**（語意清晰）：
    ```mermaid
    graph TD
    UserInput[使用者輸入帳號密碼] --> DBCheck[系統檢查資料庫]
    ```
    * **優點**：修改文字時不影響圖表結構；短 ID 讓代碼更整潔。

### 註釋習慣
在複雜邏輯區塊前使用 `%%` 添加註釋。
* 範例：`%% 此區塊為異常處理流程`

---

## 3. 視覺語意：形狀代表意義

遵循 BPMN 等標準思維，讓形狀本身傳遞訊息。

| 語法 | 形狀 | 建議用途 (語意) |
| :--- | :--- | :--- |
| `Node[文字]` | 矩形 | **處理 / 動作 (Process)** |
| `Node{文字}` | 菱形 | **決策 / 判斷 (Decision)** |
| `Node([文字])` | 圓角矩形 | **開始 / 結束 (Terminal)** |
| `Node[(文字)]` | 圓柱體 | **資料庫 / 儲存 (Database)** |
| `Node[[文字]]` | 雙框矩形 | **子程序 / 既定模組 (Subroutine)** |
| `Node[/文字/]` | 平行四邊形 | **輸入 / 輸出 (Input/Output)** |

---

## 4. 樣式管理：統一視覺風格

避免在節點後直接寫 `style`，應使用 `classDef` 進行全域管理。

### 定義與應用
1.  **定義類別**：在圖表頂部定義顏色與邊框。
2.  **應用類別**：使用 `:::` 運算子套用。


# 專用 Mermaid 圖表規範範本  

## 1. 核心原則（請所有成員嚴格遵守）

1. 可讀性第一：即使不渲染圖，純文字也要能大致看懂流程
2. 結構三段式寫法（強制）：
   - 第一段：全部節點定義（id + 形狀 + 文字）
   - 第二段：子圖（subgraph） + 主要連線關係
   - 第三段：樣式定義（classDef + class）
3. 禁止使用 A、B、C、D、E 等無意義命名
4. 單張圖主要節點建議控制在 8–15 個，超過請拆分或使用多層 subgraph
5. 決策說明、動作、狀態盡量寫在箭頭標籤上，而非節點內
6. 中文長文字一律使用 `<br>` 或 `<br/>` 換行
7. 每張圖必須使用下方統一的 `init` 主題區塊

## 2. 標準 init 主題區塊（每張圖最上方必貼）

```mermaid
%%{init: {
  "theme": "base",
  "themeVariables": {
    "fontFamily": "Microsoft JhengHei, 'Noto Sans TC', -apple-system, BlinkMacSystemFont, sans-serif",
    "fontSize": "14px",
    "primaryColor": "#4a90e2",
    "primaryTextColor": "#ffffff",
    "primaryBorderColor": "#2a6099",
    "secondaryColor": "#f39c12",
    "lineColor": "#555555",
    "edgeLabelBackground": "rgba(255,255,255,0.92)",
    "clusterBkg": "#f0f4ff",
    "clusterBorder": "#a0c0ff"
  }
}}%%


