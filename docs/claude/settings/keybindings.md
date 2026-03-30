# Keyboard Shortcuts

> Source: https://code.claude.com/docs/en/keybindings
> Customize keyboard shortcuts in Claude Code with a keybindings configuration file.

Requires Claude Code v2.1.18 or later. Run `/keybindings` to create or open `~/.claude/keybindings.json`. Changes are automatically detected and applied without restarting.

---

## Configuration File

```json
{
  "$schema": "https://www.schemastore.org/claude-code-keybindings.json",
  "$docs": "https://code.claude.com/docs/en/keybindings",
  "bindings": [
    {
      "context": "Chat",
      "bindings": {
        "ctrl+e": "chat:externalEditor",
        "ctrl+u": null
      }
    }
  ]
}
```

| Field | Description |
| --- | --- |
| `$schema` | JSON Schema URL for editor autocompletion |
| `$docs` | Documentation URL |
| `bindings` | Array of binding blocks by context |

---

## Contexts

| Context | Description |
| --- | --- |
| `Global` | Applies everywhere in the app |
| `Chat` | Main chat input area |
| `Autocomplete` | Autocomplete menu is open |
| `Settings` | Settings menu (escape-only dismiss) |
| `Confirmation` | Permission and confirmation dialogs |
| `Tabs` | Tab navigation components |
| `Help` | Help menu is visible |
| `Transcript` | Transcript viewer |
| `HistorySearch` | History search mode (Ctrl+R) |
| `Task` | Background task is running |
| `ThemePicker` | Theme picker dialog |
| `Attachments` | Image/attachment bar navigation |
| `Footer` | Footer indicator navigation |
| `MessageSelector` | Rewind and summarize message selection |
| `DiffDialog` | Diff viewer navigation |
| `ModelPicker` | Model picker effort level |
| `Select` | Generic select/list components |
| `Plugin` | Plugin dialog (browse, discover, manage) |

---

## Available Actions

Actions follow `namespace:action` format.

### App Actions (Global context)

| Action | Default | Description |
| --- | --- | --- |
| `app:interrupt` | Ctrl+C | Cancel current operation |
| `app:exit` | Ctrl+D | Exit Claude Code |
| `app:toggleTodos` | Ctrl+T | Toggle task list visibility |
| `app:toggleTranscript` | Ctrl+O | Toggle verbose transcript |

### History Actions

| Action | Default | Description |
| --- | --- | --- |
| `history:search` | Ctrl+R | Open history search |
| `history:previous` | Up | Previous history item |
| `history:next` | Down | Next history item |

### Chat Actions

| Action | Default | Description |
| --- | --- | --- |
| `chat:cancel` | Escape | Cancel current input |
| `chat:killAgents` | Ctrl+X Ctrl+K | Kill all background agents |
| `chat:cycleMode` | Shift+Tab* | Cycle permission modes |
| `chat:modelPicker` | Cmd+P / Meta+P | Open model picker |
| `chat:fastMode` | Meta+O | Toggle fast mode |
| `chat:thinkingToggle` | Cmd+T / Meta+T | Toggle extended thinking |
| `chat:submit` | Enter | Submit message |
| `chat:undo` | Ctrl+\_ | Undo last action |
| `chat:externalEditor` | Ctrl+G, Ctrl+X Ctrl+E | Open in external editor |
| `chat:stash` | Ctrl+S | Stash current prompt |
| `chat:imagePaste` | Ctrl+V (Alt+V on Windows) | Paste image |

*On Windows without VT mode, defaults to Meta+M.

### Autocomplete Actions

| Action | Default | Description |
| --- | --- | --- |
| `autocomplete:accept` | Tab | Accept suggestion |
| `autocomplete:dismiss` | Escape | Dismiss menu |
| `autocomplete:previous` | Up | Previous suggestion |
| `autocomplete:next` | Down | Next suggestion |

### Confirmation Actions

| Action | Default | Description |
| --- | --- | --- |
| `confirm:yes` | Y, Enter | Confirm action |
| `confirm:no` | N, Escape | Decline action |
| `confirm:previous` | Up | Previous option |
| `confirm:next` | Down | Next option |
| `confirm:nextField` | Tab | Next field |
| `confirm:previousField` | (unbound) | Previous field |
| `confirm:cycleMode` | Shift+Tab | Cycle permission modes |
| `confirm:toggleExplanation` | Ctrl+E | Toggle permission explanation |

### Permission Actions (Confirmation context)

| Action | Default | Description |
| --- | --- | --- |
| `permission:toggleDebug` | Ctrl+D | Toggle permission debug info |

### Transcript Actions

| Action | Default | Description |
| --- | --- | --- |
| `transcript:toggleShowAll` | Ctrl+E | Toggle show all content |
| `transcript:exit` | Ctrl+C, Escape | Exit transcript view |

### History Search Actions

| Action | Default | Description |
| --- | --- | --- |
| `historySearch:next` | Ctrl+R | Next match |
| `historySearch:accept` | Escape, Tab | Accept selection |
| `historySearch:cancel` | Ctrl+C | Cancel search |
| `historySearch:execute` | Enter | Execute selected command |

### Task Actions

| Action | Default | Description |
| --- | --- | --- |
| `task:background` | Ctrl+B | Background current task |

### Theme Actions

| Action | Default | Description |
| --- | --- | --- |
| `theme:toggleSyntaxHighlighting` | Ctrl+T | Toggle syntax highlighting |

### Help Actions

| Action | Default | Description |
| --- | --- | --- |
| `help:dismiss` | Escape | Close help menu |

### Tabs Actions

| Action | Default | Description |
| --- | --- | --- |
| `tabs:next` | Tab, Right | Next tab |
| `tabs:previous` | Shift+Tab, Left | Previous tab |

### Attachments Actions

| Action | Default | Description |
| --- | --- | --- |
| `attachments:next` | Right | Next attachment |
| `attachments:previous` | Left | Previous attachment |
| `attachments:remove` | Backspace, Delete | Remove selected |
| `attachments:exit` | Down, Escape | Exit attachment bar |

### Footer Actions

| Action | Default | Description |
| --- | --- | --- |
| `footer:next` | Right | Next footer item |
| `footer:previous` | Left | Previous footer item |
| `footer:up` | Up | Navigate up (deselects at top) |
| `footer:down` | Down | Navigate down |
| `footer:openSelected` | Enter | Open selected item |
| `footer:clearSelection` | Escape | Clear selection |

### Message Selector Actions

| Action | Default | Description |
| --- | --- | --- |
| `messageSelector:up` | Up, K, Ctrl+P | Move up |
| `messageSelector:down` | Down, J, Ctrl+N | Move down |
| `messageSelector:top` | Ctrl+Up, Shift+Up, Meta+Up, Shift+K | Jump to top |
| `messageSelector:bottom` | Ctrl+Down, Shift+Down, Meta+Down, Shift+J | Jump to bottom |
| `messageSelector:select` | Enter | Select message |

### Diff Actions

| Action | Default | Description |
| --- | --- | --- |
| `diff:dismiss` | Escape | Close diff viewer |
| `diff:previousSource` | Left | Previous diff source |
| `diff:nextSource` | Right | Next diff source |
| `diff:previousFile` | Up | Previous file in diff |
| `diff:nextFile` | Down | Next file in diff |
| `diff:viewDetails` | Enter | View diff details |
| `diff:back` | (context-specific) | Go back |

### Model Picker Actions

| Action | Default | Description |
| --- | --- | --- |
| `modelPicker:decreaseEffort` | Left | Decrease effort level |
| `modelPicker:increaseEffort` | Right | Increase effort level |

### Select Actions

| Action | Default | Description |
| --- | --- | --- |
| `select:next` | Down, J, Ctrl+N | Next option |
| `select:previous` | Up, K, Ctrl+P | Previous option |
| `select:accept` | Enter | Accept selection |
| `select:cancel` | Escape | Cancel selection |

### Plugin Actions

| Action | Default | Description |
| --- | --- | --- |
| `plugin:toggle` | Space | Toggle plugin selection |
| `plugin:install` | I | Install selected plugins |

### Settings Actions

| Action | Default | Description |
| --- | --- | --- |
| `settings:search` | / | Enter search mode |
| `settings:retry` | R | Retry loading usage data |

### Voice Actions (Chat context)

| Action | Default | Description |
| --- | --- | --- |
| `voice:pushToTalk` | Space | Hold to dictate a prompt |

---

## Keystroke Syntax

### Modifiers

Use `+` separator:

- `ctrl` or `control`
- `alt`, `opt`, or `option`
- `shift`
- `meta`, `cmd`, or `command`

```
ctrl+k          Single key with modifier
shift+tab       Shift + Tab
meta+p          Command/Meta + P
ctrl+shift+c    Multiple modifiers
```

### Uppercase Letters

Standalone uppercase implies Shift: `K` = `shift+k`. Uppercase with modifiers (e.g., `ctrl+K`) does **not** imply Shift.

### Chords

Sequences separated by spaces:

```
ctrl+k ctrl+s   Press Ctrl+K, release, then Ctrl+S
```

### Special Keys

- `escape` or `esc`
- `enter` or `return`
- `tab`
- `space`
- `up`, `down`, `left`, `right`
- `backspace`, `delete`

---

## Unbind Default Shortcuts

Set action to `null`:

```json
{
  "bindings": [
    {
      "context": "Chat",
      "bindings": {
        "ctrl+s": null
      }
    }
  ]
}
```

---

## Reserved Shortcuts

| Shortcut | Reason |
| --- | --- |
| Ctrl+C | Hardcoded interrupt/cancel |
| Ctrl+D | Hardcoded exit |
| Ctrl+M | Identical to Enter in terminals |

---

## Terminal Conflicts

| Shortcut | Conflict |
| --- | --- |
| Ctrl+B | tmux prefix (press twice to send) |
| Ctrl+A | GNU screen prefix |
| Ctrl+Z | Unix process suspend (SIGTSTP) |

---

## Vim Mode Interaction

When vim mode is enabled (`/vim`), keybindings and vim mode operate independently:

- **Vim mode** handles text input level (cursor, modes, motions)
- **Keybindings** handle component-level actions (toggle todos, submit, etc.)
- Escape in vim mode switches INSERT→NORMAL; does not trigger `chat:cancel`
- Most Ctrl+key shortcuts pass through vim mode
- In NORMAL mode, `?` shows help menu

---

## Validation

Claude Code validates and warns for: parse errors, invalid contexts, reserved conflicts, terminal multiplexer conflicts, and duplicate bindings. Run `/doctor` to see warnings.
