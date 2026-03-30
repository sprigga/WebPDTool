[Skip to main content](https://code.claude.com/docs/en/statusline#content-area)

[Claude Code Docs home page![light logo](https://mintcdn.com/claude-code/c5r9_6tjPMzFdDDT/logo/light.svg?fit=max&auto=format&n=c5r9_6tjPMzFdDDT&q=85&s=78fd01ff4f4340295a4f66e2ea54903c)![dark logo](https://mintcdn.com/claude-code/c5r9_6tjPMzFdDDT/logo/dark.svg?fit=max&auto=format&n=c5r9_6tjPMzFdDDT&q=85&s=1298a0c3b3a1da603b190d0de0e31712)](https://code.claude.com/docs/en/overview)

![US](https://d3gk2c5xim1je2.cloudfront.net/flags/US.svg)

English

Search...

Ctrl KAsk AI

- [Claude Developer Platform](https://platform.claude.com/)
- [Claude Code on the Web](https://claude.ai/code)
- [Claude Code on the Web](https://claude.ai/code)

Search...

Navigation

Configuration

Customize your status line

[Getting started](https://code.claude.com/docs/en/overview) [Build with Claude Code](https://code.claude.com/docs/en/sub-agents) [Deployment](https://code.claude.com/docs/en/third-party-integrations) [Administration](https://code.claude.com/docs/en/setup) [Configuration](https://code.claude.com/docs/en/settings) [Reference](https://code.claude.com/docs/en/cli-reference) [Resources](https://code.claude.com/docs/en/legal-and-compliance)

##### Configuration

- [Settings](https://code.claude.com/docs/en/settings)
- [Permissions](https://code.claude.com/docs/en/permissions)
- [Sandboxing](https://code.claude.com/docs/en/sandboxing)
- [Terminal configuration](https://code.claude.com/docs/en/terminal-config)
- [Model configuration](https://code.claude.com/docs/en/model-config)
- [Speed up responses with fast mode](https://code.claude.com/docs/en/fast-mode)
- [Voice dictation](https://code.claude.com/docs/en/voice-dictation)
- [Output styles](https://code.claude.com/docs/en/output-styles)
- [Customize status line](https://code.claude.com/docs/en/statusline)
- [Customize keyboard shortcuts](https://code.claude.com/docs/en/keybindings)

On this page

- [Set up a status line](https://code.claude.com/docs/en/statusline#set-up-a-status-line)
- [Use the /statusline command](https://code.claude.com/docs/en/statusline#use-the-%2Fstatusline-command)
- [Manually configure a status line](https://code.claude.com/docs/en/statusline#manually-configure-a-status-line)
- [Disable the status line](https://code.claude.com/docs/en/statusline#disable-the-status-line)
- [Build a status line step by step](https://code.claude.com/docs/en/statusline#build-a-status-line-step-by-step)
- [How status lines work](https://code.claude.com/docs/en/statusline#how-status-lines-work)
- [Available data](https://code.claude.com/docs/en/statusline#available-data)
- [Context window fields](https://code.claude.com/docs/en/statusline#context-window-fields)
- [Examples](https://code.claude.com/docs/en/statusline#examples)
- [Context window usage](https://code.claude.com/docs/en/statusline#context-window-usage)
- [Git status with colors](https://code.claude.com/docs/en/statusline#git-status-with-colors)
- [Cost and duration tracking](https://code.claude.com/docs/en/statusline#cost-and-duration-tracking)
- [Display multiple lines](https://code.claude.com/docs/en/statusline#display-multiple-lines)
- [Clickable links](https://code.claude.com/docs/en/statusline#clickable-links)
- [Rate limit usage](https://code.claude.com/docs/en/statusline#rate-limit-usage)
- [Cache expensive operations](https://code.claude.com/docs/en/statusline#cache-expensive-operations)
- [Windows configuration](https://code.claude.com/docs/en/statusline#windows-configuration)
- [Tips](https://code.claude.com/docs/en/statusline#tips)
- [Troubleshooting](https://code.claude.com/docs/en/statusline#troubleshooting)

Configuration

# Customize your status line

Copy page

Configure a custom status bar to monitor context window usage, costs, and git status in Claude Code

Copy page

The status line is a customizable bar at the bottom of Claude Code that runs any shell script you configure. It receives JSON session data on stdin and displays whatever your script prints, giving you a persistent, at-a-glance view of context usage, costs, git status, or anything else you want to track.Status lines are useful when you:

- Want to monitor context window usage as you work
- Need to track session costs
- Work across multiple sessions and need to distinguish them
- Want git branch and status always visible

Here’s an example of a [multi-line status line](https://code.claude.com/docs/en/statusline#display-multiple-lines) that displays git info on the first line and a color-coded context bar on the second.

![A multi-line status line showing model name, directory, git branch on the first line, and a context usage progress bar with cost and duration on the second line](https://mintcdn.com/claude-code/nibzesLaJVh4ydOq/images/statusline-multiline.png?fit=max&auto=format&n=nibzesLaJVh4ydOq&q=85&s=60f11387658acc9ff75158ae85f2ac87)

This page walks through [setting up a basic status line](https://code.claude.com/docs/en/statusline#set-up-a-status-line), explains [how the data flows](https://code.claude.com/docs/en/statusline#how-status-lines-work) from Claude Code to your script, lists [all the fields you can display](https://code.claude.com/docs/en/statusline#available-data), and provides [ready-to-use examples](https://code.claude.com/docs/en/statusline#examples) for common patterns like git status, cost tracking, and progress bars.

## [​](https://code.claude.com/docs/en/statusline\#set-up-a-status-line)  Set up a status line

Use the [`/statusline` command](https://code.claude.com/docs/en/statusline#use-the-statusline-command) to have Claude Code generate a script for you, or [manually create a script](https://code.claude.com/docs/en/statusline#manually-configure-a-status-line) and add it to your settings.

### [​](https://code.claude.com/docs/en/statusline\#use-the-/statusline-command)  Use the /statusline command

The `/statusline` command accepts natural language instructions describing what you want displayed. Claude Code generates a script file in `~/.claude/` and updates your settings automatically:

Report incorrect code

Copy

Ask AI

```
/statusline show model name and context percentage with a progress bar
```

### [​](https://code.claude.com/docs/en/statusline\#manually-configure-a-status-line)  Manually configure a status line

Add a `statusLine` field to your user settings (`~/.claude/settings.json`, where `~` is your home directory) or [project settings](https://code.claude.com/docs/en/settings#settings-files). Set `type` to `"command"` and point `command` to a script path or an inline shell command. For a full walkthrough of creating a script, see [Build a status line step by step](https://code.claude.com/docs/en/statusline#build-a-status-line-step-by-step).

Report incorrect code

Copy

Ask AI

```
{
  "statusLine": {
    "type": "command",
    "command": "~/.claude/statusline.sh",
    "padding": 2
  }
}
```

The `command` field runs in a shell, so you can also use inline commands instead of a script file. This example uses `jq` to parse the JSON input and display the model name and context percentage:

Report incorrect code

Copy

Ask AI

```
{
  "statusLine": {
    "type": "command",
    "command": "jq -r '\"[\\(.model.display_name)] \\(.context_window.used_percentage // 0)% context\"'"
  }
}
```

The optional `padding` field adds extra horizontal spacing (in characters) to the status line content. Defaults to `0`. This padding is in addition to the interface’s built-in spacing, so it controls relative indentation rather than absolute distance from the terminal edge.

### [​](https://code.claude.com/docs/en/statusline\#disable-the-status-line)  Disable the status line

Run `/statusline` and ask it to remove or clear your status line (e.g., `/statusline delete`, `/statusline clear`, `/statusline remove it`). You can also manually delete the `statusLine` field from your settings.json.

## [​](https://code.claude.com/docs/en/statusline\#build-a-status-line-step-by-step)  Build a status line step by step

This walkthrough shows what’s happening under the hood by manually creating a status line that displays the current model, working directory, and context window usage percentage.

Running [`/statusline`](https://code.claude.com/docs/en/statusline#use-the-statusline-command) with a description of what you want configures all of this for you automatically.

These examples use Bash scripts, which work on macOS and Linux. On Windows, see [Windows configuration](https://code.claude.com/docs/en/statusline#windows-configuration) for PowerShell and Git Bash examples.

![A status line showing model name, directory, and context percentage](https://mintcdn.com/claude-code/nibzesLaJVh4ydOq/images/statusline-quickstart.png?fit=max&auto=format&n=nibzesLaJVh4ydOq&q=85&s=696445e59ca0059213250651ad23db6b)

1

[Navigate to header](https://code.claude.com/docs/en/statusline#)

Create a script that reads JSON and prints output

Claude Code sends JSON data to your script via stdin. This script uses [`jq`](https://jqlang.github.io/jq/), a command-line JSON parser you may need to install, to extract the model name, directory, and context percentage, then prints a formatted line.Save this to `~/.claude/statusline.sh` (where `~` is your home directory, such as `/Users/username` on macOS or `/home/username` on Linux):

Report incorrect code

Copy

Ask AI

```
#!/bin/bash
# Read JSON data that Claude Code sends to stdin
input=$(cat)

# Extract fields using jq
MODEL=$(echo "$input" | jq -r '.model.display_name')
DIR=$(echo "$input" | jq -r '.workspace.current_dir')
# The "// 0" provides a fallback if the field is null
PCT=$(echo "$input" | jq -r '.context_window.used_percentage // 0' | cut -d. -f1)

# Output the status line - ${DIR##*/} extracts just the folder name
echo "[$MODEL] 📁 ${DIR##*/} | ${PCT}% context"
```

2

[Navigate to header](https://code.claude.com/docs/en/statusline#)

Make it executable

Mark the script as executable so your shell can run it:

Report incorrect code

Copy

Ask AI

```
chmod +x ~/.claude/statusline.sh
```

3

[Navigate to header](https://code.claude.com/docs/en/statusline#)

Add to settings

Tell Claude Code to run your script as the status line. Add this configuration to `~/.claude/settings.json`, which sets `type` to `"command"` (meaning “run this shell command”) and points `command` to your script:

Report incorrect code

Copy

Ask AI

```
{
  "statusLine": {
    "type": "command",
    "command": "~/.claude/statusline.sh"
  }
}
```

Your status line appears at the bottom of the interface. Settings reload automatically, but changes won’t appear until your next interaction with Claude Code.

## [​](https://code.claude.com/docs/en/statusline\#how-status-lines-work)  How status lines work

Claude Code runs your script and pipes [JSON session data](https://code.claude.com/docs/en/statusline#available-data) to it via stdin. Your script reads the JSON, extracts what it needs, and prints text to stdout. Claude Code displays whatever your script prints.**When it updates**Your script runs after each new assistant message, when the permission mode changes, or when vim mode toggles. Updates are debounced at 300ms, meaning rapid changes batch together and your script runs once things settle. If a new update triggers while your script is still running, the in-flight execution is cancelled. If you edit your script, the changes won’t appear until your next interaction with Claude Code triggers an update.**What your script can output**

- **Multiple lines**: each `echo` or `print` statement displays as a separate row. See the [multi-line example](https://code.claude.com/docs/en/statusline#display-multiple-lines).
- **Colors**: use [ANSI escape codes](https://en.wikipedia.org/wiki/ANSI_escape_code#Colors) like `\033[32m` for green (terminal must support them). See the [git status example](https://code.claude.com/docs/en/statusline#git-status-with-colors).\
- **Links**: use [OSC 8 escape sequences](https://en.wikipedia.org/wiki/ANSI_escape_code#OSC) to make text clickable (Cmd+click on macOS, Ctrl+click on Windows/Linux). Requires a terminal that supports hyperlinks like iTerm2, Kitty, or WezTerm. See the [clickable links example](https://code.claude.com/docs/en/statusline#clickable-links).\
\
The status line runs locally and does not consume API tokens. It temporarily hides during certain UI interactions, including autocomplete suggestions, the help menu, and permission prompts.\
\
## [​](https://code.claude.com/docs/en/statusline\#available-data)  Available data\
\
Claude Code sends the following JSON fields to your script via stdin:\
\
| Field | Description |\
| --- | --- |\
| `model.id`, `model.display_name` | Current model identifier and display name |\
| `cwd`, `workspace.current_dir` | Current working directory. Both fields contain the same value; `workspace.current_dir` is preferred for consistency with `workspace.project_dir`. |\
| `workspace.project_dir` | Directory where Claude Code was launched, which may differ from `cwd` if the working directory changes during a session |\
| `cost.total_cost_usd` | Total session cost in USD |\
| `cost.total_duration_ms` | Total wall-clock time since the session started, in milliseconds |\
| `cost.total_api_duration_ms` | Total time spent waiting for API responses in milliseconds |\
| `cost.total_lines_added`, `cost.total_lines_removed` | Lines of code changed |\
| `context_window.total_input_tokens`, `context_window.total_output_tokens` | Cumulative token counts across the session |\
| `context_window.context_window_size` | Maximum context window size in tokens. 200000 by default, or 1000000 for models with extended context. |\
| `context_window.used_percentage` | Pre-calculated percentage of context window used |\
| `context_window.remaining_percentage` | Pre-calculated percentage of context window remaining |\
| `context_window.current_usage` | Token counts from the last API call, described in [context window fields](https://code.claude.com/docs/en/statusline#context-window-fields) |\
| `exceeds_200k_tokens` | Whether the total token count (input, cache, and output tokens combined) from the most recent API response exceeds 200k. This is a fixed threshold regardless of actual context window size. |\
| `rate_limits.five_hour.used_percentage`, `rate_limits.seven_day.used_percentage` | Percentage of the 5-hour or 7-day rate limit consumed, from 0 to 100 |\
| `rate_limits.five_hour.resets_at`, `rate_limits.seven_day.resets_at` | Unix epoch seconds when the 5-hour or 7-day rate limit window resets |\
| `session_id` | Unique session identifier |\
| `transcript_path` | Path to conversation transcript file |\
| `version` | Claude Code version |\
| `output_style.name` | Name of the current output style |\
| `vim.mode` | Current vim mode (`NORMAL` or `INSERT`) when [vim mode](https://code.claude.com/docs/en/interactive-mode#vim-editor-mode) is enabled |\
| `agent.name` | Agent name when running with the `--agent` flag or agent settings configured |\
| `worktree.name` | Name of the active worktree. Present only during `--worktree` sessions |\
| `worktree.path` | Absolute path to the worktree directory |\
| `worktree.branch` | Git branch name for the worktree (for example, `"worktree-my-feature"`). Absent for hook-based worktrees |\
| `worktree.original_cwd` | The directory Claude was in before entering the worktree |\
| `worktree.original_branch` | Git branch checked out before entering the worktree. Absent for hook-based worktrees |\
\
Full JSON schema\
\
Your status line command receives this JSON structure via stdin:\
\
Report incorrect code\
\
Copy\
\
Ask AI\
\
```\
{\
  "cwd": "/current/working/directory",\
  "session_id": "abc123...",\
  "transcript_path": "/path/to/transcript.jsonl",\
  "model": {\
    "id": "claude-opus-4-6",\
    "display_name": "Opus"\
  },\
  "workspace": {\
    "current_dir": "/current/working/directory",\
    "project_dir": "/original/project/directory"\
  },\
  "version": "1.0.80",\
  "output_style": {\
    "name": "default"\
  },\
  "cost": {\
    "total_cost_usd": 0.01234,\
    "total_duration_ms": 45000,\
    "total_api_duration_ms": 2300,\
    "total_lines_added": 156,\
    "total_lines_removed": 23\
  },\
  "context_window": {\
    "total_input_tokens": 15234,\
    "total_output_tokens": 4521,\
    "context_window_size": 200000,\
    "used_percentage": 8,\
    "remaining_percentage": 92,\
    "current_usage": {\
      "input_tokens": 8500,\
      "output_tokens": 1200,\
      "cache_creation_input_tokens": 5000,\
      "cache_read_input_tokens": 2000\
    }\
  },\
  "exceeds_200k_tokens": false,\
  "rate_limits": {\
    "five_hour": {\
      "used_percentage": 23.5,\
      "resets_at": 1738425600\
    },\
    "seven_day": {\
      "used_percentage": 41.2,\
      "resets_at": 1738857600\
    }\
  },\
  "vim": {\
    "mode": "NORMAL"\
  },\
  "agent": {\
    "name": "security-reviewer"\
  },\
  "worktree": {\
    "name": "my-feature",\
    "path": "/path/to/.claude/worktrees/my-feature",\
    "branch": "worktree-my-feature",\
    "original_cwd": "/path/to/project",\
    "original_branch": "main"\
  }\
}\
```\
\
**Fields that may be absent** (not present in JSON):\
\
- `vim`: appears only when vim mode is enabled\
- `agent`: appears only when running with the `--agent` flag or agent settings configured\
- `worktree`: appears only during `--worktree` sessions. When present, `branch` and `original_branch` may also be absent for hook-based worktrees\
- `rate_limits`: appears only for Claude.ai subscribers (Pro/Max) after the first API response in the session. Each window (`five_hour`, `seven_day`) may be independently absent. Use `jq -r '.rate_limits.five_hour.used_percentage // empty'` to handle absence gracefully.\
\
**Fields that may be `null`**:\
\
- `context_window.current_usage`: `null` before the first API call in a session\
- `context_window.used_percentage`, `context_window.remaining_percentage`: may be `null` early in the session\
\
Handle missing fields with conditional access and null values with fallback defaults in your scripts.\
\
### [​](https://code.claude.com/docs/en/statusline\#context-window-fields)  Context window fields\
\
The `context_window` object provides two ways to track context usage:\
\
- **Cumulative totals** (`total_input_tokens`, `total_output_tokens`): sum of all tokens across the entire session, useful for tracking total consumption\
- **Current usage** (`current_usage`): token counts from the most recent API call, use this for accurate context percentage since it reflects the actual context state\
\
The `current_usage` object contains:\
\
- `input_tokens`: input tokens in current context\
- `output_tokens`: output tokens generated\
- `cache_creation_input_tokens`: tokens written to cache\
- `cache_read_input_tokens`: tokens read from cache\
\
The `used_percentage` field is calculated from input tokens only: `input_tokens + cache_creation_input_tokens + cache_read_input_tokens`. It does not include `output_tokens`.If you calculate context percentage manually from `current_usage`, use the same input-only formula to match `used_percentage`.The `current_usage` object is `null` before the first API call in a session.\
\
## [​](https://code.claude.com/docs/en/statusline\#examples)  Examples\
\
These examples show common status line patterns. To use any example:\
\
1. Save the script to a file like `~/.claude/statusline.sh` (or `.py`/`.js`)\
2. Make it executable: `chmod +x ~/.claude/statusline.sh`\
3. Add the path to your [settings](https://code.claude.com/docs/en/statusline#manually-configure-a-status-line)\
\
The Bash examples use [`jq`](https://jqlang.github.io/jq/) to parse JSON. Python and Node.js have built-in JSON parsing.\
\
### [​](https://code.claude.com/docs/en/statusline\#context-window-usage)  Context window usage\
\
Display the current model and context window usage with a visual progress bar. Each script reads JSON from stdin, extracts the `used_percentage` field, and builds a 10-character bar where filled blocks (▓) represent usage:\
\
![A status line showing model name and a progress bar with percentage](https://mintcdn.com/claude-code/nibzesLaJVh4ydOq/images/statusline-context-window-usage.png?fit=max&auto=format&n=nibzesLaJVh4ydOq&q=85&s=15b58ab3602f036939145dde3165c6f7)\
\
Bash\
\
Python\
\
Node.js\
\
Report incorrect code\
\
Copy\
\
Ask AI\
\
```\
#!/bin/bash\
# Read all of stdin into a variable\
input=$(cat)\
\
# Extract fields with jq, "// 0" provides fallback for null\
MODEL=$(echo "$input" | jq -r '.model.display_name')\
PCT=$(echo "$input" | jq -r '.context_window.used_percentage // 0' | cut -d. -f1)\
\
# Build progress bar: printf -v creates a run of spaces, then\
# ${var// /▓} replaces each space with a block character\
BAR_WIDTH=10\
FILLED=$((PCT * BAR_WIDTH / 100))\
EMPTY=$((BAR_WIDTH - FILLED))\
BAR=""\
[ "$FILLED" -gt 0 ] && printf -v FILL "%${FILLED}s" && BAR="${FILL// /▓}"\
[ "$EMPTY" -gt 0 ] && printf -v PAD "%${EMPTY}s" && BAR="${BAR}${PAD// /░}"\
\
echo "[$MODEL] $BAR $PCT%"\
```\
\
### [​](https://code.claude.com/docs/en/statusline\#git-status-with-colors)  Git status with colors\
\
Show git branch with color-coded indicators for staged and modified files. This script uses [ANSI escape codes](https://en.wikipedia.org/wiki/ANSI_escape_code#Colors) for terminal colors: `\033[32m` is green, `\033[33m` is yellow, and `\033[0m` resets to default.\
\
![A status line showing model, directory, git branch, and colored indicators for staged and modified files](https://mintcdn.com/claude-code/nibzesLaJVh4ydOq/images/statusline-git-context.png?fit=max&auto=format&n=nibzesLaJVh4ydOq&q=85&s=e656f34f90d1d9a1d0e220988914345f)\
\
Each script checks if the current directory is a git repository, counts staged and modified files, and displays color-coded indicators:\
\
Bash\
\
Python\
\
Node.js\
\
Report incorrect code\
\
Copy\
\
Ask AI\
\
```\
#!/bin/bash\
input=$(cat)\
\
MODEL=$(echo "$input" | jq -r '.model.display_name')\
DIR=$(echo "$input" | jq -r '.workspace.current_dir')\
\
GREEN='\033[32m'\
YELLOW='\033[33m'\
RESET='\033[0m'\
\
if git rev-parse --git-dir > /dev/null 2>&1; then\
    BRANCH=$(git branch --show-current 2>/dev/null)\
    STAGED=$(git diff --cached --numstat 2>/dev/null | wc -l | tr -d ' ')\
    MODIFIED=$(git diff --numstat 2>/dev/null | wc -l | tr -d ' ')\
\
    GIT_STATUS=""\
    [ "$STAGED" -gt 0 ] && GIT_STATUS="${GREEN}+${STAGED}${RESET}"\
    [ "$MODIFIED" -gt 0 ] && GIT_STATUS="${GIT_STATUS}${YELLOW}~${MODIFIED}${RESET}"\
\
    echo -e "[$MODEL] 📁 ${DIR##*/} | 🌿 $BRANCH $GIT_STATUS"\
else\
    echo "[$MODEL] 📁 ${DIR##*/}"\
fi\
```\
\
### [​](https://code.claude.com/docs/en/statusline\#cost-and-duration-tracking)  Cost and duration tracking\
\
Track your session’s API costs and elapsed time. The `cost.total_cost_usd` field accumulates the cost of all API calls in the current session. The `cost.total_duration_ms` field measures total elapsed time since the session started, while `cost.total_api_duration_ms` tracks only the time spent waiting for API responses.Each script formats cost as currency and converts milliseconds to minutes and seconds:\
\
![A status line showing model name, session cost, and duration](https://mintcdn.com/claude-code/nibzesLaJVh4ydOq/images/statusline-cost-tracking.png?fit=max&auto=format&n=nibzesLaJVh4ydOq&q=85&s=e3444a51fe6f3440c134bd5f1f08ad29)\
\
Bash\
\
Python\
\
Node.js\
\
Report incorrect code\
\
Copy\
\
Ask AI\
\
```\
#!/bin/bash\
input=$(cat)\
\
MODEL=$(echo "$input" | jq -r '.model.display_name')\
COST=$(echo "$input" | jq -r '.cost.total_cost_usd // 0')\
DURATION_MS=$(echo "$input" | jq -r '.cost.total_duration_ms // 0')\
\
COST_FMT=$(printf '$%.2f' "$COST")\
DURATION_SEC=$((DURATION_MS / 1000))\
MINS=$((DURATION_SEC / 60))\
SECS=$((DURATION_SEC % 60))\
\
echo "[$MODEL] 💰 $COST_FMT | ⏱️ ${MINS}m ${SECS}s"\
```\
\
### [​](https://code.claude.com/docs/en/statusline\#display-multiple-lines)  Display multiple lines\
\
Your script can output multiple lines to create a richer display. Each `echo` statement produces a separate row in the status area.\
\
![A multi-line status line showing model name, directory, git branch on the first line, and a context usage progress bar with cost and duration on the second line](https://mintcdn.com/claude-code/nibzesLaJVh4ydOq/images/statusline-multiline.png?fit=max&auto=format&n=nibzesLaJVh4ydOq&q=85&s=60f11387658acc9ff75158ae85f2ac87)\
\
This example combines several techniques: threshold-based colors (green under 70%, yellow 70-89%, red 90%+), a progress bar, and git branch info. Each `print` or `echo` statement creates a separate row:\
\
Bash\
\
Python\
\
Node.js\
\
Report incorrect code\
\
Copy\
\
Ask AI\
\
```\
#!/bin/bash\
input=$(cat)\
\
MODEL=$(echo "$input" | jq -r '.model.display_name')\
DIR=$(echo "$input" | jq -r '.workspace.current_dir')\
COST=$(echo "$input" | jq -r '.cost.total_cost_usd // 0')\
PCT=$(echo "$input" | jq -r '.context_window.used_percentage // 0' | cut -d. -f1)\
DURATION_MS=$(echo "$input" | jq -r '.cost.total_duration_ms // 0')\
\
CYAN='\033[36m'; GREEN='\033[32m'; YELLOW='\033[33m'; RED='\033[31m'; RESET='\033[0m'\
\
# Pick bar color based on context usage\
if [ "$PCT" -ge 90 ]; then BAR_COLOR="$RED"\
elif [ "$PCT" -ge 70 ]; then BAR_COLOR="$YELLOW"\
else BAR_COLOR="$GREEN"; fi\
\
FILLED=$((PCT / 10)); EMPTY=$((10 - FILLED))\
printf -v FILL "%${FILLED}s"; printf -v PAD "%${EMPTY}s"\
BAR="${FILL// /█}${PAD// /░}"\
\
MINS=$((DURATION_MS / 60000)); SECS=$(((DURATION_MS % 60000) / 1000))\
\
BRANCH=""\
git rev-parse --git-dir > /dev/null 2>&1 && BRANCH=" | 🌿 $(git branch --show-current 2>/dev/null)"\
\
echo -e "${CYAN}[$MODEL]${RESET} 📁 ${DIR##*/}$BRANCH"\
COST_FMT=$(printf '$%.2f' "$COST")\
echo -e "${BAR_COLOR}${BAR}${RESET} ${PCT}% | ${YELLOW}${COST_FMT}${RESET} | ⏱️ ${MINS}m ${SECS}s"\
```\
\
### [​](https://code.claude.com/docs/en/statusline\#clickable-links)  Clickable links\
\
This example creates a clickable link to your GitHub repository. It reads the git remote URL, converts SSH format to HTTPS with `sed`, and wraps the repo name in OSC 8 escape codes. Hold Cmd (macOS) or Ctrl (Windows/Linux) and click to open the link in your browser.\
\
![A status line showing a clickable link to a GitHub repository](https://mintcdn.com/claude-code/nibzesLaJVh4ydOq/images/statusline-links.png?fit=max&auto=format&n=nibzesLaJVh4ydOq&q=85&s=4bcc6e7deb7cf52f41ab85a219b52661)\
\
Each script gets the git remote URL, converts SSH format to HTTPS, and wraps the repo name in OSC 8 escape codes. The Bash version uses `printf '%b'` which interprets backslash escapes more reliably than `echo -e` across different shells:\
\
Bash\
\
Python\
\
Node.js\
\
Report incorrect code\
\
Copy\
\
Ask AI\
\
```\
#!/bin/bash\
input=$(cat)\
\
MODEL=$(echo "$input" | jq -r '.model.display_name')\
\
# Convert git SSH URL to HTTPS\
REMOTE=$(git remote get-url origin 2>/dev/null | sed 's/git@github.com:/https:\/\/github.com\//' | sed 's/\.git$//')\
\
if [ -n "$REMOTE" ]; then\
    REPO_NAME=$(basename "$REMOTE")\
    # OSC 8 format: \e]8;;URL\a then TEXT then \e]8;;\a\
    # printf %b interprets escape sequences reliably across shells\
    printf '%b' "[$MODEL] 🔗 \e]8;;${REMOTE}\a${REPO_NAME}\e]8;;\a\n"\
else\
    echo "[$MODEL]"\
fi\
```\
\
### [​](https://code.claude.com/docs/en/statusline\#rate-limit-usage)  Rate limit usage\
\
Display Claude.ai subscription rate limit usage in the status line. The `rate_limits` object contains `five_hour` (5-hour rolling window) and `seven_day` (weekly) windows. Each window provides `used_percentage` (0-100) and `resets_at` (Unix epoch seconds when the window resets).This field is only present for Claude.ai subscribers (Pro/Max) after the first API response. Each script handles the absent field gracefully:\
\
Bash\
\
Python\
\
Node.js\
\
Report incorrect code\
\
Copy\
\
Ask AI\
\
```\
#!/bin/bash\
input=$(cat)\
\
MODEL=$(echo "$input" | jq -r '.model.display_name')\
# "// empty" produces no output when rate_limits is absent\
FIVE_H=$(echo "$input" | jq -r '.rate_limits.five_hour.used_percentage // empty')\
WEEK=$(echo "$input" | jq -r '.rate_limits.seven_day.used_percentage // empty')\
\
LIMITS=""\
[ -n "$FIVE_H" ] && LIMITS="5h: $(printf '%.0f' "$FIVE_H")%"\
[ -n "$WEEK" ] && LIMITS="${LIMITS:+$LIMITS }7d: $(printf '%.0f' "$WEEK")%"\
\
[ -n "$LIMITS" ] && echo "[$MODEL] | $LIMITS" || echo "[$MODEL]"\
```\
\
### [​](https://code.claude.com/docs/en/statusline\#cache-expensive-operations)  Cache expensive operations\
\
Your status line script runs frequently during active sessions. Commands like `git status` or `git diff` can be slow, especially in large repositories. This example caches git information to a temp file and only refreshes it every 5 seconds.Use a stable, fixed filename for the cache file like `/tmp/statusline-git-cache`. Each status line invocation runs as a new process, so process-based identifiers like `$$`, `os.getpid()`, or `process.pid` produce a different value every time and the cache is never reused.Each script checks if the cache file is missing or older than 5 seconds before running git commands:\
\
Bash\
\
Python\
\
Node.js\
\
Report incorrect code\
\
Copy\
\
Ask AI\
\
```\
#!/bin/bash\
input=$(cat)\
\
MODEL=$(echo "$input" | jq -r '.model.display_name')\
DIR=$(echo "$input" | jq -r '.workspace.current_dir')\
\
CACHE_FILE="/tmp/statusline-git-cache"\
CACHE_MAX_AGE=5  # seconds\
\
cache_is_stale() {\
    [ ! -f "$CACHE_FILE" ] || \\
    # stat -f %m is macOS, stat -c %Y is Linux\
    [ $(($(date +%s) - $(stat -f %m "$CACHE_FILE" 2>/dev/null || stat -c %Y "$CACHE_FILE" 2>/dev/null || echo 0))) -gt $CACHE_MAX_AGE ]\
}\
\
if cache_is_stale; then\
    if git rev-parse --git-dir > /dev/null 2>&1; then\
        BRANCH=$(git branch --show-current 2>/dev/null)\
        STAGED=$(git diff --cached --numstat 2>/dev/null | wc -l | tr -d ' ')\
        MODIFIED=$(git diff --numstat 2>/dev/null | wc -l | tr -d ' ')\
        echo "$BRANCH|$STAGED|$MODIFIED" > "$CACHE_FILE"\
    else\
        echo "||" > "$CACHE_FILE"\
    fi\
fi\
\
IFS='|' read -r BRANCH STAGED MODIFIED < "$CACHE_FILE"\
\
if [ -n "$BRANCH" ]; then\
    echo "[$MODEL] 📁 ${DIR##*/} | 🌿 $BRANCH +$STAGED ~$MODIFIED"\
else\
    echo "[$MODEL] 📁 ${DIR##*/}"\
fi\
```\
\
### [​](https://code.claude.com/docs/en/statusline\#windows-configuration)  Windows configuration\
\
On Windows, Claude Code runs status line commands through Git Bash. You can invoke PowerShell from that shell:\
\
settings.json\
\
statusline.ps1\
\
Report incorrect code\
\
Copy\
\
Ask AI\
\
```\
{\
  "statusLine": {\
    "type": "command",\
    "command": "powershell -NoProfile -File C:/Users/username/.claude/statusline.ps1"\
  }\
}\
```\
\
Or run a Bash script directly:\
\
settings.json\
\
statusline.sh\
\
Report incorrect code\
\
Copy\
\
Ask AI\
\
```\
{\
  "statusLine": {\
    "type": "command",\
    "command": "~/.claude/statusline.sh"\
  }\
}\
```\
\
## [​](https://code.claude.com/docs/en/statusline\#tips)  Tips\
\
- **Test with mock input**: `echo '{"model":{"display_name":"Opus"},"context_window":{"used_percentage":25}}' | ./statusline.sh`\
- **Keep output short**: the status bar has limited width, so long output may get truncated or wrap awkwardly\
- **Cache slow operations**: your script runs frequently during active sessions, so commands like `git status` can cause lag. See the [caching example](https://code.claude.com/docs/en/statusline#cache-expensive-operations) for how to handle this.\
\
Community projects like [ccstatusline](https://github.com/sirmalloc/ccstatusline) and [starship-claude](https://github.com/martinemde/starship-claude) provide pre-built configurations with themes and additional features.\
\
## [​](https://code.claude.com/docs/en/statusline\#troubleshooting)  Troubleshooting\
\
**Status line not appearing**\
\
- Verify your script is executable: `chmod +x ~/.claude/statusline.sh`\
- Check that your script outputs to stdout, not stderr\
- Run your script manually to verify it produces output\
- If `disableAllHooks` is set to `true` in your settings, the status line is also disabled. Remove this setting or set it to `false` to re-enable.\
- Run `claude --debug` to log the exit code and stderr from the first status line invocation in a session\
- Ask Claude to read your settings file and execute the `statusLine` command directly to surface errors\
\
**Status line shows `--` or empty values**\
\
- Fields may be `null` before the first API response completes\
- Handle null values in your script with fallbacks such as `// 0` in jq\
- Restart Claude Code if values remain empty after multiple messages\
\
**Context percentage shows unexpected values**\
\
- Use `used_percentage` for accurate context state rather than cumulative totals\
- The `total_input_tokens` and `total_output_tokens` are cumulative across the session and may exceed the context window size\
- Context percentage may differ from `/context` output due to when each is calculated\
\
**OSC 8 links not clickable**\
\
- Verify your terminal supports OSC 8 hyperlinks (iTerm2, Kitty, WezTerm)\
- Terminal.app does not support clickable links\
- SSH and tmux sessions may strip OSC sequences depending on configuration\
- If escape sequences appear as literal text like `\e]8;;`, use `printf '%b'` instead of `echo -e` for more reliable escape handling\
\
**Display glitches with escape sequences**\
\
- Complex escape sequences (ANSI colors, OSC 8 links) can occasionally cause garbled output if they overlap with other UI updates\
- If you see corrupted text, try simplifying your script to plain text output\
- Multi-line status lines with escape codes are more prone to rendering issues than single-line plain text\
\
**Workspace trust required**\
\
- The status line command only runs if you’ve accepted the workspace trust dialog for the current directory. Because `statusLine` executes a shell command, it requires the same trust acceptance as hooks and other shell-executing settings.\
- If trust isn’t accepted, you’ll see the notification `statusline skipped · restart to fix` instead of your status line output. Restart Claude Code and accept the trust prompt to enable it.\
\
**Script errors or hangs**\
\
- Scripts that exit with non-zero codes or produce no output cause the status line to go blank\
- Slow scripts block the status line from updating until they complete. Keep scripts fast to avoid stale output.\
- If a new update triggers while a slow script is running, the in-flight script is cancelled\
- Test your script independently with mock input before configuring it\
\
**Notifications share the status line row**\
\
- System notifications like MCP server errors, auto-updates, and token warnings display on the right side of the same row as your status line\
- Enabling verbose mode adds a token counter to this area\
- On narrow terminals, these notifications may truncate your status line output\
\
Was this page helpful?\
\
YesNo\
\
[Output styles](https://code.claude.com/docs/en/output-styles) [Customize keyboard shortcuts](https://code.claude.com/docs/en/keybindings)\
\
Ctrl+I\
\
[Claude Code Docs home page![light logo](https://mintcdn.com/claude-code/c5r9_6tjPMzFdDDT/logo/light.svg?fit=max&auto=format&n=c5r9_6tjPMzFdDDT&q=85&s=78fd01ff4f4340295a4f66e2ea54903c)![dark logo](https://mintcdn.com/claude-code/c5r9_6tjPMzFdDDT/logo/dark.svg?fit=max&auto=format&n=c5r9_6tjPMzFdDDT&q=85&s=1298a0c3b3a1da603b190d0de0e31712)](https://code.claude.com/docs/en/overview)\
\
[x](https://x.com/AnthropicAI) [linkedin](https://www.linkedin.com/company/anthropicresearch)\
\
Company\
\
[Anthropic](https://www.anthropic.com/company) [Careers](https://www.anthropic.com/careers) [Economic Futures](https://www.anthropic.com/economic-futures) [Research](https://www.anthropic.com/research) [News](https://www.anthropic.com/news) [Trust center](https://trust.anthropic.com/) [Transparency](https://www.anthropic.com/transparency)\
\
Help and security\
\
[Availability](https://www.anthropic.com/supported-countries) [Status](https://status.anthropic.com/) [Support center](https://support.claude.com/)\
\
Learn\
\
[Courses](https://www.anthropic.com/learn) [MCP connectors](https://claude.com/partners/mcp) [Customer stories](https://www.claude.com/customers) [Engineering blog](https://www.anthropic.com/engineering) [Events](https://www.anthropic.com/events) [Powered by Claude](https://claude.com/partners/powered-by-claude) [Service partners](https://claude.com/partners/services) [Startups program](https://claude.com/programs/startups)\
\
Terms and policies\
\
[Privacy choices](https://code.claude.com/docs/en/statusline#) [Privacy policy](https://www.anthropic.com/legal/privacy) [Disclosure policy](https://www.anthropic.com/responsible-disclosure-policy) [Usage policy](https://www.anthropic.com/legal/aup) [Commercial terms](https://www.anthropic.com/legal/commercial-terms) [Consumer terms](https://www.anthropic.com/legal/consumer-terms)\
\
Assistant\
\
Responses are generated using AI and may contain mistakes.\
\
![A multi-line status line showing model name, directory, git branch on the first line, and a context usage progress bar with cost and duration on the second line](https://mintcdn.com/claude-code/nibzesLaJVh4ydOq/images/statusline-multiline.png?w=1100&fit=max&auto=format&n=nibzesLaJVh4ydOq&q=85&s=d7720e5f51310185c0c02152f6c10d8b)\
\
![A status line showing model name, directory, and context percentage](https://mintcdn.com/claude-code/nibzesLaJVh4ydOq/images/statusline-quickstart.png?w=1100&fit=max&auto=format&n=nibzesLaJVh4ydOq&q=85&s=52cdd52865842f0cda24489dd5310d3b)\
\
![A status line showing model name and a progress bar with percentage](https://mintcdn.com/claude-code/nibzesLaJVh4ydOq/images/statusline-context-window-usage.png?w=1100&fit=max&auto=format&n=nibzesLaJVh4ydOq&q=85&s=d9334e6a08e6f11a253733c8592774a9)\
\
![A status line showing model, directory, git branch, and colored indicators for staged and modified files](https://mintcdn.com/claude-code/nibzesLaJVh4ydOq/images/statusline-git-context.png?w=1100&fit=max&auto=format&n=nibzesLaJVh4ydOq&q=85&s=26aff0978865756d5ea299a22e5e9afd)\
\
![A status line showing model name, session cost, and duration](https://mintcdn.com/claude-code/nibzesLaJVh4ydOq/images/statusline-cost-tracking.png?w=1100&fit=max&auto=format&n=nibzesLaJVh4ydOq&q=85&s=479c2515e53f46d5d1da3b87a6dd993a)\
\
![A multi-line status line showing model name, directory, git branch on the first line, and a context usage progress bar with cost and duration on the second line](https://mintcdn.com/claude-code/nibzesLaJVh4ydOq/images/statusline-multiline.png?w=1100&fit=max&auto=format&n=nibzesLaJVh4ydOq&q=85&s=d7720e5f51310185c0c02152f6c10d8b)\
\
![A status line showing a clickable link to a GitHub repository](https://mintcdn.com/claude-code/nibzesLaJVh4ydOq/images/statusline-links.png?w=1100&fit=max&auto=format&n=nibzesLaJVh4ydOq&q=85&s=9f7e0c729ea093c3b39682619fd3f201)