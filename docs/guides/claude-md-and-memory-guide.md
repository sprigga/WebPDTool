# Claude Code 記憶體系統指南：CLAUDE.md、規則與 Subagent 持久記憶體

> 資料來源：[官方文件 - 記憶](https://code.claude.com/docs/zh-TW/memory) 與 [官方文件 - Subagents](https://code.claude.com/docs/zh-TW/sub-agents)

---

## 一、兩大記憶機制概覽

每個 Claude Code 工作階段都以全新的 context window 開始。以下兩種機制可以跨工作階段傳遞知識：

| 項目 | CLAUDE.md 檔案 | 自動記憶（Auto Memory） |
|------|--------------|----------------------|
| **誰編寫** | 你（開發者） | Claude 自動產生 |
| **包含內容** | 指令和規則 | 學習、模式、偏好 |
| **範圍** | 專案、使用者或組織 | 每個工作樹（worktree） |
| **載入時機** | 每個工作階段完整載入 | 每個工作階段（前 200 行） |
| **典型用途** | 編碼標準、工作流程、專案架構 | 建置命令、除錯見解、Claude 發現的偏好 |

**核心原則**：CLAUDE.md 是**上下文**，不是強制配置。Claude 讀取後嘗試遵循，但沒有嚴格遵循保證。**指令越具體、越簡潔，遵循度越高。**

---

## 二、編寫良好的 CLAUDE.md

### 2.1 檔案位置與範圍

| 範圍 | 位置 | 目的 | 共享對象 |
|------|------|------|--------|
| **受管理政策** | macOS: `/Library/Application Support/ClaudeCode/CLAUDE.md`<br>Linux/WSL: `/etc/claude-code/CLAUDE.md` | IT/DevOps 管理的組織範圍指令 | 組織所有使用者 |
| **專案指令** | `./CLAUDE.md` 或 `./.claude/CLAUDE.md` | 專案的團隊共享指令 | 透過 git 的團隊成員 |
| **使用者指令** | `~/.claude/CLAUDE.md` | 所有專案的個人偏好 | 僅你（所有專案） |
| **本機指令** | `./CLAUDE.local.md` | 個人專案特定偏好，未簽入 git | 僅你（目前專案） |

> **優先級**：更具體的位置優先於更廣泛的位置（專案 > 使用者 > 受管理政策）

### 2.2 編寫有效指令的四大原則

#### ① 大小控制（Size）
- **目標在 200 行以下**。較長的檔案消耗更多上下文並降低遵循度。
- 超出時使用 `@path` 匯入或 `.claude/rules/` 分割。

#### ② 結構清晰（Structure）
- 使用 **markdown 標題**和**項目符號**分組相關指令。
- 組織良好的章節比密集段落更容易被遵循。

#### ③ 具體可驗證（Specificity）
```
❌ 不好：「正確格式化程式碼」
✅ 好的：「使用 2 空格縮排」

❌ 不好：「測試您的變更」
✅ 好的：「提交前執行 `npm test`」

❌ 不好：「保持檔案組織」
✅ 好的：「API 處理程式位於 `src/api/handlers/`」
```

#### ④ 一致性（Consistency）
- 定期檢查跨 CLAUDE.md 檔案的**衝突指令**。
- 兩個規則互相矛盾時，Claude 可能任意選擇其中一個。

### 2.3 匯入其他檔案

使用 `@path/to/import` 語法，在啟動時將外部檔案展開至上下文中：

```markdown
有關專案概述，請參閱 @README，有關可用命令，請參閱 @package.json。

# 其他指令
- git 工作流程 @docs/git-instructions.md
```

- 允許相對和絕對路徑
- 最大遞迴深度：**5 跳**
- 第一次遇到外部匯入時，Claude 會顯示核准對話框

---

## 三、使用 `.claude/rules/` 組織規則

### 3.1 目錄結構

```
your-project/
├── .claude/
│   ├── CLAUDE.md            # 主要專案指令（200 行以內）
│   └── rules/
│       ├── code-style.md    # 程式碼樣式指南
│       ├── testing.md       # 測試慣例
│       ├── security.md      # 安全要求
│       ├── frontend/        # 前端相關規則
│       └── backend/         # 後端相關規則
```

**優點**：
- 規則模組化，易於維護
- 可將規則**範圍限定於特定檔案路徑**，減少不必要的上下文佔用
- 支援符號連結，跨專案共享規則

### 3.2 路徑特定規則（Path-Specific Rules）

使用 YAML frontmatter 的 `paths` 欄位，讓規則只在 Claude 處理匹配檔案時載入：

```markdown
---
paths:
  - "src/api/**/*.ts"
  - "lib/**/*.ts"
---

# API 開發規則

- 所有 API 端點必須包括輸入驗證
- 使用標準錯誤回應格式
- 包括 OpenAPI 文件註解
```

| 模式範例 | 匹配對象 |
|---------|---------|
| `**/*.ts` | 任何目錄中的所有 TypeScript 檔案 |
| `src/**/*` | `src/` 目錄下的所有檔案 |
| `*.md` | 專案根目錄中的 Markdown 檔案 |
| `src/components/*.tsx` | 特定目錄中的 React 元件 |

> **沒有 `paths` 欄位的規則**會在啟動時無條件載入，優先級與 `.claude/CLAUDE.md` 相同。

### 3.3 使用者級規則

在 `~/.claude/rules/` 放置適用於所有專案的個人規則：

```
~/.claude/rules/
├── preferences.md    # 個人編碼偏好
└── workflows.md      # 首選工作流程
```

> 使用者級規則在**專案規則之前**載入，因此專案規則具有更高優先級。

---

## 四、自動記憶（Auto Memory）

### 4.1 啟用/停用

自動記憶**預設為開啟**。

```bash
# 透過環境變數停用
CLAUDE_CODE_DISABLE_AUTO_MEMORY=1 claude

# 透過設定檔停用（.claude/settings.json）
{
  "autoMemoryEnabled": false
}
```

也可在工作階段中執行 `/memory` 切換開關。

### 4.2 儲存位置

```
~/.claude/projects/<project>/memory/
├── MEMORY.md          # 簡潔索引（前 200 行在每次對話載入）
├── debugging.md       # 除錯模式的詳細筆記
├── api-conventions.md # API 設計決策
└── ...                # Claude 建立的其他主題檔案
```

- `<project>` 路徑衍生自 git 儲存庫
- 同一儲存庫中的所有 worktrees 和子目錄**共享一個**自動記憶目錄
- 自動記憶是**機器本機的**，不跨機器或雲端環境共享

### 4.3 運作機制

- `MEMORY.md` 前 200 行在每次對話開始時載入
- Claude 將詳細筆記移到主題檔案（如 `debugging.md`），保持 `MEMORY.md` 簡潔
- 主題檔案**在啟動時不載入**，Claude 需要時按需讀取

### 4.4 查看與編輯記憶

```bash
/memory   # 列出所有載入的 CLAUDE.md 和規則檔案，切換自動記憶開關
```

- 所有記憶檔案都是純 markdown，可直接編輯或刪除
- 告訴 Claude「始終使用 pnpm，而不是 npm」，它會自動保存到自動記憶
- 若要保存到 CLAUDE.md，請明確說「將其新增到 CLAUDE.md」

---

## 五、Subagent 持久記憶體

### 5.1 什麼是 Subagent

Subagent 是專門的 AI 助手，在自己的 context window 中執行，具有：
- 自訂系統提示
- 特定工具存取控制
- 獨立權限
- **可選的持久記憶體**

### 5.2 啟用 Subagent 持久記憶體

在 subagent 的 markdown 檔案中，使用 `memory` frontmatter 欄位：

```markdown
---
name: code-reviewer
description: Reviews code for quality and best practices
memory: user
---

You are a code reviewer. As you review code, update your agent memory with
patterns, conventions, and recurring issues you discover.

Update your agent memory as you discover codepaths, patterns, library
locations, and key architectural decisions. This builds up institutional
knowledge across conversations. Write concise notes about what you found
and where.
```

### 5.3 記憶體範圍選擇

| 範圍 | 位置 | 使用時機 |
|------|------|---------|
| `user` | `~/.claude/agent-memory/<name>/` | subagent 記憶跨所有專案的學習（**建議預設**） |
| `project` | `.claude/agent-memory/<name>/` | subagent 知識特定於專案，可透過版本控制共享 |
| `local` | `.claude/agent-memory-local/<name>/` | subagent 知識特定於專案，但不應簽入版本控制 |

### 5.4 啟用記憶體後的自動行為

當設定 `memory` 欄位時，Claude Code 自動：

1. 在 subagent 系統提示中注入讀取/寫入記憶體目錄的說明
2. 載入記憶體目錄中 `MEMORY.md` 的前 200 行到 subagent 上下文
3. 自動啟用 Read、Write、Edit 工具以管理記憶體檔案

### 5.5 Subagent 檔案完整範例

```markdown
---
name: webpdtool-analyzer
description: Analyzes WebPDTool codebase patterns and architecture. Use proactively when exploring test execution flows or measurement implementations.
tools: Read, Grep, Glob, Bash
model: haiku
memory: project
---

You are a specialist in the WebPDTool codebase architecture.

## Your responsibilities
- Analyze measurement implementations in `backend/app/measurements/`
- Trace test execution flows through TestEngine and MeasurementService
- Document PDTool4 compatibility patterns you discover

## Memory management
Before starting any analysis, check your memory for relevant patterns.
After completing analysis, save discovered patterns, file locations,
and architectural insights to your memory. Be concise and specific.

Focus on:
- Measurement class locations and responsibilities
- Test execution state machine transitions
- PDTool4 validation logic patterns
- Database relationship patterns
```

### 5.6 有效使用 Subagent 記憶體的技巧

```bash
# 讓 subagent 先查詢記憶體再開始工作
"Review this PR, and check your memory for patterns you've seen before."

# 任務完成後讓 subagent 更新記憶體
"Now that you're done, save what you learned to your memory."

# 直接叫用特定 subagent
"Use the code-reviewer subagent to review the authentication module"
```

---

## 六、Subagent 配置完整參考

### 6.1 Subagent 檔案結構

```markdown
---
name: agent-name          # 必需：小寫字母和連字號
description: "..."        # 必需：Claude 何時委派給此 agent
tools: Read, Grep, Glob   # 可選：工具白名單（省略則繼承所有工具）
disallowedTools: Write    # 可選：工具黑名單
model: sonnet             # 可選：sonnet/opus/haiku/inherit（預設 inherit）
permissionMode: default   # 可選：default/acceptEdits/dontAsk/bypassPermissions/plan
maxTurns: 10              # 可選：最大代理轉數
memory: user              # 可選：user/project/local
background: false         # 可選：是否始終作為背景任務執行
isolation: worktree       # 可選：在隔離的 git worktree 中執行
skills:                   # 可選：預載入的 skills
  - api-conventions
hooks:                    # 可選：生命週期 hooks
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/validate.sh"
---

系統提示內容...
```

### 6.2 Subagent 存放位置

| 位置 | 範圍 | 優先級 |
|------|------|--------|
| `--agents` CLI 旗標 | 目前工作階段 | 1（最高） |
| `.claude/agents/` | 目前專案 | 2 |
| `~/.claude/agents/` | 所有你的專案 | 3 |
| Plugin 的 `agents/` | 啟用 plugin 的位置 | 4（最低） |

---

## 七、疑難排解

### Claude 不遵循 CLAUDE.md

1. 執行 `/memory` 確認 CLAUDE.md 是否已載入
2. 檢查檔案是否位於正確的[載入位置](#21-檔案位置與範圍)
3. 讓指令更具體（可驗證）
4. 尋找跨檔案的衝突指令

### CLAUDE.md 太大

- 將詳細內容移到用 `@path` 匯入的獨立檔案
- 將指令分割到 `.claude/rules/` 檔案

### 指令在 `/compact` 後消失

- `/compact` 後 CLAUDE.md 完整保留（從磁碟重新讀取）
- 若指令消失，表示它只存在於對話中，未寫入 CLAUDE.md
- 解法：明確要求 Claude「將其新增到 CLAUDE.md」

---

## 八、WebPDTool 專案建議配置

基於本專案架構，建議的規則組織方式：

```
.claude/
├── CLAUDE.md              # 主要專案指令（已存在）
└── rules/
    ├── testing.md          # pytest 測試慣例
    ├── api-design.md       # FastAPI 端點設計規範
    ├── measurement.md      # 測量層開發規則
    └── frontend.md         # Vue 3 元件開發規範
```

路徑特定規則範例（`.claude/rules/measurement.md`）：

```markdown
---
paths:
  - "backend/app/measurements/**/*.py"
---

# 測量層開發規則

- 所有測量類別必須繼承自 `BaseMeasurement`
- 實作三段式執行：`prepare()` → `execute()` → `cleanup()`
- 新類別必須在 `registry.py` 的 `MEASUREMENT_REGISTRY` 中註冊
- `execute()` 必須回傳 `MeasurementResult` dataclass
- 錯誤值使用 "No instrument found" 或 "Error:" 前綴
```
