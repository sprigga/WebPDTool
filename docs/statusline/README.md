# Claude Code Status Line Documentation

## Overview

The status line is a customizable bar at the bottom of Claude Code that runs any shell script you configure. It receives JSON session data on stdin and displays whatever your script prints, giving you a persistent, at-a-glance view of context usage, costs, git status, or anything else you want to track.

### When to Use Status Lines

- Monitor context window usage as you work
- Track session costs
- Work across multiple sessions and need to distinguish them
- Keep git branch and status always visible

## Setup Methods

### Method 1: Use the `/statusline` Command

The `/statusline` command accepts natural language instructions:

```bash
/statusline show model name and context percentage with a progress bar
```

Claude Code generates a script file in `~/.claude/` and updates your settings automatically.

### Method 2: Manual Configuration

Add a `statusLine` field to your user settings (`~/.claude/settings.json`):

```json
{
  "statusLine": {
    "type": "command",
    "command": "~/.claude/statusline.sh",
    "padding": 2
  }
}
```

The optional `padding` field adds extra horizontal spacing (default: 0).

You can also use inline commands:

```json
{
  "statusLine": {
    "type": "command",
    "command": "jq -r '\"[\\(.model.display_name)] \\(.context_window.used_percentage // 0)% context\"'"
  }
}
```

### Disable Status Line

Run `/statusline` and ask it to remove or clear (e.g., `/statusline delete`, `/statusline clear`), or manually delete the `statusLine` field from settings.json.

## How Status Lines Work

1. **Data Flow**: Claude Code runs your script and pipes JSON session data to it via stdin
2. **Update Frequency**: After each new assistant message, when permission mode changes, or when vim mode toggles (debounced at 300ms)
3. **Output**: Your script prints text to stdout, which Claude Code displays

### Supported Output

- **Multiple lines**: Each `echo` or `print` displays as a separate row
- **Colors**: ANSI escape codes (e.g., `\033[32m` for green)
- **Links**: OSC 8 escape sequences for clickable links (Cmd+click on macOS, Ctrl+click on Windows/Linux)

## Available Data Fields

| Field | Description |
|-------|-------------|
| `model.id`, `model.display_name` | Current model identifier and display name |
| `cwd`, `workspace.current_dir` | Current working directory |
| `workspace.project_dir` | Directory where Claude Code was launched |
| `cost.total_cost_usd` | Total session cost in USD |
| `cost.total_duration_ms` | Total wall-clock time since session started |
| `cost.total_api_duration_ms` | Time waiting for API responses |
| `cost.total_lines_added`, `cost.total_lines_removed` | Lines of code changed |
| `context_window.total_input_tokens` | Cumulative input tokens |
| `context_window.total_output_tokens` | Cumulative output tokens |
| `context_window.context_window_size` | Max context window size (200000 or 1000000) |
| `context_window.used_percentage` | Percentage of context window used |
| `context_window.remaining_percentage` | Percentage remaining |
| `context_window.current_usage` | Token counts from last API call |
| `exceeds_200k_tokens` | Whether last response exceeded 200k tokens |
| `rate_limits.five_hour.used_percentage` | 5-hour rate limit usage |
| `rate_limits.seven_day.used_percentage` | 7-day rate limit usage |
| `rate_limits.five_hour.resets_at` | Unix epoch when 5-hour window resets |
| `rate_limits.seven_day.resets_at` | Unix epoch when 7-day window resets |
| `session_id` | Unique session identifier |
| `transcript_path` | Path to conversation transcript |
| `version` | Claude Code version |
| `output_style.name` | Current output style name |
| `vim.mode` | Vim mode (`NORMAL` or `INSERT`) when enabled |
| `agent.name` | Agent name when running with `--agent` flag |
| `worktree.name` | Active worktree name |
| `worktree.path` | Absolute path to worktree |
| `worktree.branch` | Git branch for worktree |
| `worktree.original_cwd` | Directory before entering worktree |
| `worktree.original_branch` | Git branch before entering worktree |

### Conditional Fields

These fields may be absent:
- `vim`: Only when vim mode is enabled
- `agent`: Only with `--agent` flag or agent settings
- `worktree`: Only during `--worktree` sessions
- `rate_limits`: Only for Claude.ai subscribers after first API response

These fields may be `null`:
- `context_window.current_usage`: Before first API call
- `context_window.used_percentage`, `context_window.remaining_percentage`: Early in session

## Example Scripts

### Basic: Model and Context Percentage

```bash
#!/bin/bash
input=$(cat)

MODEL=$(echo "$input" | jq -r '.model.display_name')
PCT=$(echo "$input" | jq -r '.context_window.used_percentage // 0' | cut -d. -f1)

echo "[$MODEL] ${PCT}% context"
```

### Context Window with Progress Bar

```bash
#!/bin/bash
input=$(cat)

MODEL=$(echo "$input" | jq -r '.model.display_name')
PCT=$(echo "$input" | jq -r '.context_window.used_percentage // 0' | cut -d. -f1)

BAR_WIDTH=10
FILLED=$((PCT * BAR_WIDTH / 100))
EMPTY=$((BAR_WIDTH - FILLED))
BAR=""
[ "$FILLED" -gt 0 ] && printf -v FILL "%${FILLED}s" && BAR="${FILL// /▓}"
[ "$EMPTY" -gt 0 ] && printf -v PAD "%${EMPTY}s" && BAR="${BAR}${PAD// /░}"

echo "[$MODEL] $BAR $PCT%"
```

### Git Status with Colors

```bash
#!/bin/bash
input=$(cat)

MODEL=$(echo "$input" | jq -r '.model.display_name')
DIR=$(echo "$input" | jq -r '.workspace.current_dir')

GREEN='\033[32m'
YELLOW='\033[33m'
RESET='\033[0m'

if git rev-parse --git-dir > /dev/null 2>&1; then
    BRANCH=$(git branch --show-current 2>/dev/null)
    STAGED=$(git diff --cached --numstat 2>/dev/null | wc -l | tr -d ' ')
    MODIFIED=$(git diff --numstat 2>/dev/null | wc -l | tr -d ' ')

    GIT_STATUS=""
    [ "$STAGED" -gt 0 ] && GIT_STATUS="${GREEN}+${STAGED}${RESET}"
    [ "$MODIFIED" -gt 0 ] && GIT_STATUS="${GIT_STATUS}${YELLOW}~${MODIFIED}${RESET}"

    echo -e "[$MODEL] 📁 ${DIR##*/} | 🌿 $BRANCH $GIT_STATUS"
else
    echo "[$MODEL] 📁 ${DIR##*/}"
fi
```

### Cost and Duration Tracking

```bash
#!/bin/bash
input=$(cat)

MODEL=$(echo "$input" | jq -r '.model.display_name')
COST=$(echo "$input" | jq -r '.cost.total_cost_usd // 0')
DURATION_MS=$(echo "$input" | jq -r '.cost.total_duration_ms // 0')

COST_FMT=$(printf '$%.2f' "$COST")
DURATION_SEC=$((DURATION_MS / 1000))
MINS=$((DURATION_SEC / 60))
SECS=$((DURATION_SEC % 60))

echo "[$MODEL] 💰 $COST_FMT | ⏱️ ${MINS}m ${SECS}s"
```

### Multi-line Display

```bash
#!/bin/bash
input=$(cat)

MODEL=$(echo "$input" | jq -r '.model.display_name')
DIR=$(echo "$input" | jq -r '.workspace.current_dir')
COST=$(echo "$input" | jq -r '.cost.total_cost_usd // 0')
PCT=$(echo "$input" | jq -r '.context_window.used_percentage // 0' | cut -d. -f1)
DURATION_MS=$(echo "$input" | jq -r '.cost.total_duration_ms // 0')

CYAN='\033[36m'; GREEN='\033[32m'; YELLOW='\033[33m'; RED='\033[31m'; RESET='\033[0m'

# Pick bar color based on context usage
if [ "$PCT" -ge 90 ]; then BAR_COLOR="$RED"
elif [ "$PCT" -ge 70 ]; then BAR_COLOR="$YELLOW"
else BAR_COLOR="$GREEN"; fi

FILLED=$((PCT / 10)); EMPTY=$((10 - FILLED))
printf -v FILL "%${FILLED}s"; printf -v PAD "%${EMPTY}s"
BAR="${FILL// /█}${PAD// /░}"

MINS=$((DURATION_MS / 60000)); SECS=$(((DURATION_MS % 60000) / 1000))

BRANCH=""
git rev-parse --git-dir > /dev/null 2>&1 && BRANCH=" | 🌿 $(git branch --show-current 2>/dev/null)"

echo -e "${CYAN}[$MODEL]${RESET} 📁 ${DIR##*/}$BRANCH"
COST_FMT=$(printf '$%.2f' "$COST")
echo -e "${BAR_COLOR}${BAR}${RESET} ${PCT}% | ${YELLOW}${COST_FMT}${RESET} | ⏱️ ${MINS}m ${SECS}s"
```

### Clickable Links

```bash
#!/bin/bash
input=$(cat)

MODEL=$(echo "$input" | jq -r '.model.display_name')

# Convert git SSH URL to HTTPS
REMOTE=$(git remote get-url origin 2>/dev/null | sed 's/git@github.com:/https:\/\/github.com\//' | sed 's/\.git$//')

if [ -n "$REMOTE" ]; then
    REPO_NAME=$(basename "$REMOTE")
    # OSC 8 format: \e]8;;URL\a then TEXT then \e]8;;\a
    printf '%b' "[$MODEL] 🔗 \e]8;;${REMOTE}\a${REPO_NAME}\e]8;;\a\n"
else
    echo "[$MODEL]"
fi
```

### Rate Limit Usage

```bash
#!/bin/bash
input=$(cat)

MODEL=$(echo "$input" | jq -r '.model.display_name')
# "// empty" produces no output when rate_limits is absent
FIVE_H=$(echo "$input" | jq -r '.rate_limits.five_hour.used_percentage // empty')
WEEK=$(echo "$input" | jq -r '.rate_limits.seven_day.used_percentage // empty')

LIMITS=""
[ -n "$FIVE_H" ] && LIMITS="5h: $(printf '%.0f' "$FIVE_H")%"
[ -n "$WEEK" ] && LIMITS="${LIMITS:+$LIMITS }7d: $(printf '%.0f' "$WEEK")%"

[ -n "$LIMITS" ] && echo "[$MODEL] | $LIMITS" || echo "[$MODEL]"
```

### Rate Limit Usage on Second Line (Multi-line)

將 Rate Limit 獨立顯示在第二行，只在有資料時才輸出，避免空行。
使用 `printf '\n...'` 而非 `echo` 來避免自動換行符號重複。

```bash
#!/usr/bin/env bash
input=$(cat)

model=$(echo "$input" | jq -r '.model.display_name // empty')
used=$(echo "$input" | jq -r '.context_window.used_percentage // empty')

# Rate limit usage — "// empty" produces no output when rate_limits is absent
FIVE_H=$(echo "$input" | jq -r '.rate_limits.five_hour.used_percentage // empty')
WEEK=$(echo "$input" | jq -r '.rate_limits.seven_day.used_percentage // empty')

LIMITS=""
[ -n "$FIVE_H" ] && LIMITS="5h:$(printf '%.0f' "$FIVE_H")%"
[ -n "$WEEK" ] && LIMITS="${LIMITS:+$LIMITS }7d:$(printf '%.0f' "$WEEK")%"

# Line 1: model and context usage
if [ -n "$model" ] && [ -n "$used" ]; then
    printf '\033[00;33m[%s | ctx:%s%%]\033[00m' "$model" "$(printf '%.0f' "$used")"
elif [ -n "$model" ]; then
    printf '\033[00;33m[%s]\033[00m' "$model"
fi

# Line 2: rate limits (only when available)
if [ -n "$LIMITS" ]; then
    printf '\n\033[00;35m📊 %s\033[00m' "$LIMITS"
fi
```

**輸出範例（有 Rate Limit 資料）：**
```
[claude-sonnet-4-6 | ctx:42%]
📊 5h:18% 7d:5%
```

**輸出範例（無 Rate Limit 資料，例如 session 初期）：**
```
[claude-sonnet-4-6 | ctx:25%]
```

### Cache Expensive Operations

```bash
#!/bin/bash
input=$(cat)

MODEL=$(echo "$input" | jq -r '.model.display_name')
DIR=$(echo "$input" | jq -r '.workspace.current_dir')

CACHE_FILE="/tmp/statusline-git-cache"
CACHE_MAX_AGE=5  # seconds

cache_is_stale() {
    [ ! -f "$CACHE_FILE" ] ||
    # stat -f %m is macOS, stat -c %Y is Linux
    [ $(($(date +%s) - $(stat -f %m "$CACHE_FILE" 2>/dev/null || stat -c %Y "$CACHE_FILE" 2>/dev/null || echo 0))) -gt $CACHE_MAX_AGE ]
}

if cache_is_stale; then
    if git rev-parse --git-dir > /dev/null 2>&1; then
        BRANCH=$(git branch --show-current 2>/dev/null)
        STAGED=$(git diff --cached --numstat 2>/dev/null | wc -l | tr -d ' ')
        MODIFIED=$(git diff --numstat 2>/dev/null | wc -l | tr -d ' ')
        echo "$BRANCH|$STAGED|$MODIFIED" > "$CACHE_FILE"
    else
        echo "||" > "$CACHE_FILE"
    fi
fi

IFS='|' read -r BRANCH STAGED MODIFIED < "$CACHE_FILE"

if [ -n "$BRANCH" ]; then
    echo "[$MODEL] 📁 ${DIR##*/} | 🌿 $BRANCH +$STAGED ~$MODIFIED"
else
    echo "[$MODEL] 📁 ${DIR##*/}"
fi
```

## Windows Configuration

### PowerShell

settings.json:
```json
{
  "statusLine": {
    "type": "command",
    "command": "powershell -NoProfile -File C:/Users/username/.claude/statusline.ps1"
  }
}
```

### Git Bash (Direct)

settings.json:
```json
{
  "statusLine": {
    "type": "command",
    "command": "~/.claude/statusline.sh"
  }
}
```

## Tips

1. **Test with mock input**: `echo '{"model":{"display_name":"Opus"},"context_window":{"used_percentage":25}}' | ./statusline.sh`
2. **Keep output short**: Status bar has limited width
3. **Cache slow operations**: Commands like `git status` can cause lag (see caching example)

## Troubleshooting

### Status line not appearing

- Verify script is executable: `chmod +x ~/.claude/statusline.sh`
- Check script outputs to stdout, not stderr
- Run script manually to verify output
- If `disableAllHooks` is `true` in settings, status line is disabled
- Run `claude --debug` to log exit code and stderr

### Status line shows `--` or empty values

- Fields may be `null` before first API response
- Handle null values with fallbacks like `// 0` in jq

### Context percentage shows unexpected values

- Use `used_percentage` for accurate context state
- Cumulative totals may exceed context window size

### OSC 8 links not clickable

- Verify terminal supports OSC 8 hyperlinks (iTerm2, Kitty, WezTerm)
- Terminal.app does not support clickable links

### Workspace trust required

- The status line command only runs if workspace trust is accepted
- You'll see `statusline skipped · restart to fix` if trust not accepted

## Community Projects

- [ccstatusline](https://github.com/sirmalloc/ccstatusline)
- [starship-claude](https://github.com/martinemde/starship-claude)

---

## 實作記錄：加入 Rate Limit 顯示

### 背景

`~/.claude/settings.json` 中設定的 statusLine 指向的是 `~/.claude/statusline-command.sh`，
而非同目錄下的 `statusline.sh`。開始修改前必須先確認實際生效的腳本路徑：

```bash
# 查看 settings.json 中的 statusLine.command 欄位
cat ~/.claude/settings.json | jq '.statusLine'
# 輸出：{ "type": "command", "command": "bash /home/ubuntu/.claude/statusline-command.sh" }

# 確認兩個腳本都存在
ls ~/.claude/statusline*.sh
# /home/ubuntu/.claude/statusline-command.sh  ← 這個才是生效的
# /home/ubuntu/.claude/statusline.sh
```

**關鍵陷阱：** 目錄下可能有多個 `statusline*.sh`，修改錯誤的檔案不會有任何效果，
也不會出現錯誤提示。務必從 `settings.json` 確認 `statusLine.command` 指向的路徑。

### 第一步：加入 Rate Limit 到同一行

初版實作將 rate limit 資訊附加在第一行末尾：

```bash
# 原本的輸出格式：
# [model | ctx:42% | 5h:18% 7d:5%]

if [ -n "$model" ] && [ -n "$used" ]; then
    printf ' \033[00;33m[%s | ctx:%s%%' "$model" "$(printf '%.0f' "$used")"
    [ -n "$LIMITS" ] && printf ' | %s' "$LIMITS"
    printf ']\033[00m'
fi
```

**問題：** 當 rate limit 資訊存在時，整行會變得很長，尤其在窄視窗下容易溢出或截斷。

### 第二步：改為 newline 顯示

將 rate limit 移到第二行，使用 `printf '\n...'` 而非 `echo`：

```bash
# 修改後：rate limits 獨立顯示在第二行
if [ -n "$LIMITS" ]; then
    printf '\n\033[00;35m📊 %s\033[00m' "$LIMITS"
fi
```

**為何用 `printf '\n...'` 而非 `echo`：**
- `echo` 會在輸出末尾自動加上換行符，導致最後一行多一個空行
- `printf` 精確控制換行位置，只在 rate limit 存在時才輸出換行

**為何用 `// empty` 而非 `// null` 或 `// 0`：**
- `// 0` 會在欄位不存在時輸出 `0`，導致 `5h:0% 7d:0%` 的錯誤顯示
- `// empty` 在欄位不存在時讓 jq 不輸出任何內容，bash 變數保持空字串
- 空字串判斷 `[ -n "$FIVE_H" ]` 可乾淨地略過不可用的欄位

### 除錯方法

#### 用 mock input 測試腳本

在修改腳本後，不需要重啟 Claude Code，直接用 `echo` 模擬 stdin 測試：

```bash
# 測試有 rate limit 資料的情況
echo '{"model":{"display_name":"claude-sonnet-4-6"},"context_window":{"used_percentage":42},"rate_limits":{"five_hour":{"used_percentage":18},"seven_day":{"used_percentage":5}}}' \
  | bash ~/.claude/statusline-command.sh

# 測試無 rate limit 資料的情況（session 初期或非 Claude.ai 訂閱者）
echo '{"model":{"display_name":"claude-sonnet-4-6"},"context_window":{"used_percentage":25}}' \
  | bash ~/.claude/statusline-command.sh
```

#### 常見問題排查

| 症狀 | 可能原因 | 解決方式 |
|------|----------|----------|
| 修改後沒有變化 | 修改了錯誤的腳本檔案 | 確認 `settings.json` 中的路徑 |
| Rate limit 顯示 `0%` | 使用了 `// 0` fallback | 改用 `// empty` 並加上 `[ -n "$VAR" ]` 判斷 |
| 出現多餘空行 | 用了 `echo` 輸出 rate limits | 改用 `printf '\n...'` |
| 狀態列完全不顯示 | 腳本沒有執行權限 | `chmod +x ~/.claude/statusline-command.sh` |
| 顏色代碼顯示為亂碼 | 使用 `echo` 而非 `echo -e` 或 `printf` | 改用 `printf` 輸出 ANSI codes |

#### 確認 settings.json 語法正確

修改 `settings.json` 後可用 `jq` 驗證語法：

```bash
jq . ~/.claude/settings.json && echo "JSON valid"
```

JSON 語法錯誤會導致整個 settings 檔案失效，所有設定（包含 statusLine）都會被忽略。
