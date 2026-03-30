# Status Line Configuration

> Source: https://code.claude.com/docs/en/statusline
> Configure a custom status bar to monitor context window usage, costs, and git status.

The status line is a customizable bar at the bottom of Claude Code that runs any shell script. It receives JSON session data on stdin and displays whatever your script prints.

---

## Set Up a Status Line

### Use the `/statusline` Command

Accepts natural language instructions and generates a script automatically:

```
/statusline show model name and context percentage with a progress bar
```

### Manual Configuration

Add `statusLine` to user settings (`~/.claude/settings.json`) or project settings:

```json
{
  "statusLine": {
    "type": "command",
    "command": "~/.claude/statusline.sh",
    "padding": 2
  }
}
```

The `command` field runs in a shell, so inline commands work too:

```json
{
  "statusLine": {
    "type": "command",
    "command": "jq -r '\"[\\(.model.display_name)] \\(.context_window.used_percentage // 0)% context\"'"
  }
}
```

Optional `padding` field adds horizontal spacing (default: `0`).

### Disable

Run `/statusline` with "delete", "clear", or "remove it". Or manually delete the `statusLine` field from settings.

---

## Build a Status Line Step by Step

1. **Create a script** that reads JSON from stdin:

```bash
#!/bin/bash
input=$(cat)

MODEL=$(echo "$input" | jq -r '.model.display_name')
DIR=$(echo "$input" | jq -r '.workspace.current_dir')
PCT=$(echo "$input" | jq -r '.context_window.used_percentage // 0' | cut -d. -f1)

echo "[$MODEL] ${DIR##*/} | ${PCT}% context"
```

2. **Make executable**: `chmod +x ~/.claude/statusline.sh`

3. **Add to settings** (see above)

---

## How Status Lines Work

Claude Code runs your script and pipes JSON session data via stdin. Your script reads JSON, extracts what it needs, and prints text to stdout.

**When it updates:** After each new assistant message, permission mode change, or vim mode toggle. Updates are debounced at 300ms.

**What your script can output:**
- **Multiple lines**: Each `echo` is a separate row
- **Colors**: ANSI escape codes (`\033[32m` for green)
- **Links**: OSC 8 escape sequences (Cmd+click on macOS, Ctrl+click on Windows/Linux)

The status line runs locally, does **not** consume API tokens, and temporarily hides during autocomplete, help menu, and permission prompts.

---

## Available Data

| Field | Description |
| --- | --- |
| `model.id`, `model.display_name` | Current model identifier and display name |
| `cwd`, `workspace.current_dir` | Current working directory |
| `workspace.project_dir` | Directory where Claude Code was launched |
| `cost.total_cost_usd` | Total session cost in USD |
| `cost.total_duration_ms` | Wall-clock time since session start (ms) |
| `cost.total_api_duration_ms` | Time waiting for API responses (ms) |
| `cost.total_lines_added`, `.total_lines_removed` | Lines of code changed |
| `context_window.total_input_tokens` | Cumulative input tokens |
| `context_window.total_output_tokens` | Cumulative output tokens |
| `context_window.context_window_size` | Max context window size (200000 default, 1000000 for extended) |
| `context_window.used_percentage` | Percentage of context window used |
| `context_window.remaining_percentage` | Percentage remaining |
| `context_window.current_usage` | Token counts from last API call |
| `exceeds_200k_tokens` | Whether total tokens exceed 200k |
| `rate_limits.five_hour.used_percentage` | 5-hour rate limit used (0-100) |
| `rate_limits.seven_day.used_percentage` | 7-day rate limit used (0-100) |
| `rate_limits.five_hour.resets_at` | Unix epoch for 5-hour window reset |
| `rate_limits.seven_day.resets_at` | Unix epoch for 7-day window reset |
| `session_id` | Unique session identifier |
| `transcript_path` | Path to transcript file |
| `version` | Claude Code version |
| `output_style.name` | Current output style name |
| `vim.mode` | `NORMAL` or `INSERT` when vim mode enabled |
| `agent.name` | Agent name when using `--agent` flag |
| `worktree.name` | Active worktree name |
| `worktree.path` | Absolute path to worktree directory |
| `worktree.branch` | Git branch for worktree |
| `worktree.original_cwd` | Directory before entering worktree |
| `worktree.original_branch` | Git branch before entering worktree |

### Fields that may be absent

- `vim`: Only when vim mode enabled
- `agent`: Only with `--agent` flag or agent settings
- `worktree`: Only during `--worktree` sessions
- `rate_limits`: Only for Claude.ai subscribers (Pro/Max) after first API response

### Full JSON Schema

```json
{
  "cwd": "/current/working/directory",
  "session_id": "abc123...",
  "transcript_path": "/path/to/transcript.jsonl",
  "model": {
    "id": "claude-opus-4-6",
    "display_name": "Opus"
  },
  "workspace": {
    "current_dir": "/current/working/directory",
    "project_dir": "/original/project/directory"
  },
  "version": "1.0.80",
  "output_style": { "name": "default" },
  "cost": {
    "total_cost_usd": 0.01234,
    "total_duration_ms": 45000,
    "total_api_duration_ms": 2300,
    "total_lines_added": 156,
    "total_lines_removed": 23
  },
  "context_window": {
    "total_input_tokens": 15234,
    "total_output_tokens": 4521,
    "context_window_size": 200000,
    "used_percentage": 8,
    "remaining_percentage": 92,
    "current_usage": {
      "input_tokens": 8500,
      "output_tokens": 1200,
      "cache_creation_input_tokens": 5000,
      "cache_read_input_tokens": 2000
    }
  },
  "exceeds_200k_tokens": false,
  "rate_limits": {
    "five_hour": {
      "used_percentage": 23.5,
      "resets_at": 1738425600
    },
    "seven_day": {
      "used_percentage": 41.2,
      "resets_at": 1738857600
    }
  },
  "vim": { "mode": "NORMAL" },
  "agent": { "name": "security-reviewer" },
  "worktree": {
    "name": "my-feature",
    "path": "/path/to/.claude/worktrees/my-feature",
    "branch": "worktree-my-feature",
    "original_cwd": "/path/to/project",
    "original_branch": "main"
  }
}
```

### Context Window Fields

- **Cumulative totals**: Sum across entire session
- **`current_usage`**: From most recent API call — use for accurate context percentage
- `used_percentage` = `input_tokens + cache_creation + cache_read` (output tokens excluded)
- `current_usage` is `null` before first API call

---

## Examples

### Context Window Usage

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

GREEN='\033[32m'; YELLOW='\033[33m'; RESET='\033[0m'

if git rev-parse --git-dir > /dev/null 2>&1; then
    BRANCH=$(git branch --show-current 2>/dev/null)
    STAGED=$(git diff --cached --numstat 2>/dev/null | wc -l | tr -d ' ')
    MODIFIED=$(git diff --numstat 2>/dev/null | wc -l | tr -d ' ')

    GIT_STATUS=""
    [ "$STAGED" -gt 0 ] && GIT_STATUS="${GREEN}+${STAGED}${RESET}"
    [ "$MODIFIED" -gt 0 ] && GIT_STATUS="${GIT_STATUS}${YELLOW}~${MODIFIED}${RESET}"

    echo -e "[$MODEL] ${DIR##*/} | $BRANCH $GIT_STATUS"
else
    echo "[$MODEL] ${DIR##*/}"
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

echo "[$MODEL] $COST_FMT | ${MINS}m ${SECS}s"
```

### Display Multiple Lines

```bash
#!/bin/bash
input=$(cat)

MODEL=$(echo "$input" | jq -r '.model.display_name')
DIR=$(echo "$input" | jq -r '.workspace.current_dir')
COST=$(echo "$input" | jq -r '.cost.total_cost_usd // 0')
PCT=$(echo "$input" | jq -r '.context_window.used_percentage // 0' | cut -d. -f1)
DURATION_MS=$(echo "$input" | jq -r '.cost.total_duration_ms // 0')

CYAN='\033[36m'; GREEN='\033[32m'; YELLOW='\033[33m'; RED='\033[31m'; RESET='\033[0m'

if [ "$PCT" -ge 90 ]; then BAR_COLOR="$RED"
elif [ "$PCT" -ge 70 ]; then BAR_COLOR="$YELLOW"
else BAR_COLOR="$GREEN"; fi

FILLED=$((PCT / 10)); EMPTY=$((10 - FILLED))
printf -v FILL "%${FILLED}s"; printf -v PAD "%${EMPTY}s"
BAR="${FILL// /█}${PAD// /░}"

MINS=$((DURATION_MS / 60000)); SECS=$(((DURATION_MS % 60000) / 1000))

BRANCH=""
git rev-parse --git-dir > /dev/null 2>&1 && BRANCH=" | $(git branch --show-current 2>/dev/null)"

echo -e "${CYAN}[$MODEL]${RESET} ${DIR##*/}$BRANCH"
COST_FMT=$(printf '$%.2f' "$COST")
echo -e "${BAR_COLOR}${BAR}${RESET} ${PCT}% | ${YELLOW}${COST_FMT}${RESET} | ${MINS}m ${SECS}s"
```

### Rate Limit Usage

```bash
#!/bin/bash
input=$(cat)
MODEL=$(echo "$input" | jq -r '.model.display_name')
FIVE_H=$(echo "$input" | jq -r '.rate_limits.five_hour.used_percentage // empty')
WEEK=$(echo "$input" | jq -r '.rate_limits.seven_day.used_percentage // empty')

LIMITS=""
[ -n "$FIVE_H" ] && LIMITS="5h: $(printf '%.0f' "$FIVE_H")%"
[ -n "$WEEK" ] && LIMITS="${LIMITS:+$LIMITS }7d: $(printf '%.0f' "$WEEK")%"

[ -n "$LIMITS" ] && echo "[$MODEL] | $LIMITS" || echo "[$MODEL]"
```

### Cache Expensive Operations

Use a fixed filename for the cache (process-based IDs produce a different value every time):

```bash
#!/bin/bash
input=$(cat)
MODEL=$(echo "$input" | jq -r '.model.display_name')
DIR=$(echo "$input" | jq -r '.workspace.current_dir')

CACHE_FILE="/tmp/statusline-git-cache"
CACHE_MAX_AGE=5

cache_is_stale() {
    [ ! -f "$CACHE_FILE" ] ||
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
echo "[$MODEL] ${DIR##*/} | $BRANCH +$STAGED ~$MODIFIED"
```

---

## Windows Configuration

On Windows, Claude Code runs status line commands through Git Bash. You can invoke PowerShell:

```json
{
  "statusLine": {
    "type": "command",
    "command": "powershell -NoProfile -File C:/Users/username/.claude/statusline.ps1"
  }
}
```

Or run a Bash script directly:

```json
{
  "statusLine": {
    "type": "command",
    "command": "~/.claude/statusline.sh"
  }
}
```

---

## Tips

- **Test with mock input**: `echo '{"model":{"display_name":"Opus"},"context_window":{"used_percentage":25}}' | ./statusline.sh`
- **Keep output short**: Long output may get truncated
- **Cache slow operations**: `git status` can cause lag in large repos
- **Community projects**: [ccstatusline](https://github.com/sirmalloc/ccstatusline), [starship-claude](https://github.com/martinemde/starship-claude)

---

## Troubleshooting

| Issue | Solution |
| --- | --- |
| Status line not appearing | Verify script is executable (`chmod +x`), outputs to stdout, check `disableAllHooks` isn't `true` |
| Shows `--` or empty values | Handle null values with fallbacks (`// 0` in jq); values populate after first API response |
| Unexpected context percentage | Use `used_percentage` rather than cumulative totals |
| OSC 8 links not clickable | Requires iTerm2, Kitty, or WezTerm; Terminal.app doesn't support them |
| Display glitches | Simplify scripts to plain text output; multi-line with escape codes are more prone to issues |
| Workspace trust required | Accept workspace trust dialog; restart if you see `statusline skipped` |
| Script errors or hangs | Test independently with mock input; scripts that exit non-zero or produce no output cause blank status |
