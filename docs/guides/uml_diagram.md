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

### Mermaid 圖表最佳實務與高可讀性設定指南

本文整理如何使用 Mermaid 語法繪製清晰、好讀、不易出錯的圖表，特別針對「字型大小適中」「字體適合閱讀」「元件不遮蔽字體」三大原則，並延伸其他實務考量與常見錯誤修復方法。

#### 一、核心三大原則

1. **字型大小適中**  
   - 推薦範圍：14px ~ 18px  
   - 最常用且多數人覺得舒適：**16px**

2. **字體適合閱讀**  
   - 推薦使用 sans-serif 無襯線字型  
   - 常見安全選擇（依序優先）：  
     - Arial, Helvetica, sans-serif  
     - "Helvetica Neue", Arial, sans-serif  
     - system-ui, -apple-system, BlinkMacOSystemFont, "Segoe UI", Roboto, sans-serif

3. **元件不要遮蔽字體**  
   - 增加節點內距（padding）  
   - 加大節點間距（nodeSpacing / rankSpacing）  
   - 適當設定圖表整體留白（diagramPadding）

#### 二、推薦的萬用高可讀性模板（最穩定版本）

```mermaid
%%{init: {
  "theme": "base",
  "themeVariables": {
    "fontSize": "16px",
    "fontFamily": "Arial, Helvetica, sans-serif",
    "primaryTextColor": "#333333",
    "lineColor": "#555555",
    "primaryColor": "#f0f0f0"
  },
  "flowchart": {
    "padding": 20,
    "nodeSpacing": 60,
    "rankSpacing": 80,
    "curve": "basis",
    "diagramPadding": 30
  }
}}%%
graph TD
    A[這是比較長的節點文字<br>會自動換行] --> B[下一步]
    B --> C[結束]
```    


