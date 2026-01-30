# Mermaid 優化 Prompt 目錄

本目錄包含用於優化 Mermaid UML 架構圖的 Prompt 模板和最佳實踐指南。

---

## 📁 檔案列表

| 檔案 | 用途 | 適用場景 |
|------|------|----------|
| [mermaid-basic-optimization.md](./mermaid-basic-optimization.md) | 基礎版 Prompt | 初次優化架構圖，建立清晰視覺結構 |
| [mermaid-advanced-optimization.md](./mermaid-advanced-optimization.md) | 進階版 Prompt | 精細控制各項細節，建立專業級文檔 |
| [mermaid-quick-fix.md](./mermaid-quick-fix.md) | 快速修復版 Prompt | 針對性修復特定問題 |
| [mermaid-principles.md](./mermaid-principles.md) | 通用原則指南 | 了解最佳實踐和設計原則 |

---

## 🚀 快速開始

### 1. 首次優化架構圖
使用 **[基礎版 Prompt](./mermaid-basic-optimization.md)**：
```bash
cat docs/prompt/mermaid-basic-optimization.md
```

### 2. 需要精細控制
使用 **[進階版 Prompt](./mermaid-advanced-optimization.md)**：
```bash
cat docs/prompt/mermaid-advanced-optimization.md
```

### 3. 修復特定問題
使用 **[快速修復版 Prompt](./mermaid-quick-fix.md)**：
```bash
cat docs/prompt/mermaid-quick-fix.md
```

### 4. 了解最佳實踐
閱讀 **[通用原則指南](./mermaid-principles.md)**：
```bash
cat docs/prompt/mermaid-principles.md
```

---

## 📋 使用流程

```
┌─────────────────────┐
│  需要優化架構圖？    │
└──────────┬──────────┘
           │
    ┌──────┴──────┐
    │             │
   是            否
    │             │
    ▼             ▼
┌─────────┐  ┌──────────┐
│ 首次？  │  │ 無需動作 │
└────┬────┘  └──────────┘
     │
  ┌──┴──┐
  │     │
 是    否
  │     │
  ▼     ▼
┌──────┐ ┌──────┐
│基礎版│ │進階版│
└──────┘ └──────┘

遇到問題？
  │
  ▼
┌──────┐
│快速修復│
└──────┘
```

---

## 🎯 Prompt 模板結構

每個 Prompt 模板包含以下部分：

1. **使用時機**：說明何時使用該 Prompt
2. **Prompt 內容**：實際可複製使用的 Prompt 文字
3. **範例輸出**：展示預期的 Mermaid 程式碼
4. **檢查清單**：完成後的驗證項目
5. **注意事項**：使用時的重要提醒

---

## 📝 範例：使用基礎版 Prompt

### Step 1: 複製 Prompt
```bash
# 複製以下內容給 AI 助手
請優化 README.md 中的「整體系統架構圖」Mermaid UML，要求：

1. 布局方向：主圖使用 graph TB，API 層使用 direction TB
2. 字型大小：主層級 20px，子層級 18px
3. 防止文字遮蔽：為節點設定 width 樣式（140-200px）
4. 視覺元素：保留 Emoji，保持色彩樣式
5. 節點合併：7 個 API 合併為「API 層 (7個模組)」
```

### Step 2: AI 執行優化
AI 會根據 Prompt 修改 README.md 中的 Mermaid 程式碼

### Step 3: 驗證結果
```markdown
- [ ] 無語法錯誤
- [ ] 文字完整顯示
- [ ] 字型大小正確
- [ ] 布局清晰
```

---

## 🔧 常見使用場景

### 場景 1：新建專案架構圖
```
使用：進階版 Prompt
原因：需要完整的規範和檢查清單
```

### 場景 2：優化現有架構圖
```
使用：基礎版 Prompt
原因：快速改善視覺效果
```

### 場景 3：修復文字遮蔽問題
```
使用：快速修復版 Prompt
原因：針對性解決特定問題
```

### 場景 4：學習 Mermaid 最佳實踐
```
使用：通用原則指南
原因：了解設計原則和技巧
```

---

## 💡 提示與技巧

### 提示 1：漸進式優化
```
第一次 → 使用基礎版建立結構
第二次 → 使用進階版精細調整
遇到問題 → 使用快速修復版
```

### 提示 2：保留原始程式碼
```
修改前：
- 備份原檔
- 使用註解標記原始內容
- 方便回滾和比較
```

### 提示 3：測試多個環境
```
- GitHub Markdown
- VS Code + Mermaid Preview
- GitLab Markdown
- 確保跨平台相容
```

### 提示 4：記錄優化過程
```
- 記錄使用的 Prompt
- 記錄修改內容
- 記錄遇到的問題
- 方便後續參考
```

---

## 📚 相關資源

- [專案 README](../../README.md) - WebPDTool 專案說明
- [架構圖範例](../../README.md#整體系統架構圖) - 實際優化後的架構圖
- [Mermaid 官方文檔](https://mermaid.js.org/) - 官方語法說明
- [Mermaid 線上編輯器](https://mermaid.live/) - 即時預覽工具

---

## 📮 回饋

如果您有改進建議或發現問題，請：
1. 記錄問題描述
2. 提供複現步驟
3. 附上截圖或範例
4. 提交 Issue 或 PR

---

**最後更新**：2026-01-30
**版本**：v1.0.0
