[Skip to main content](https://code.claude.com/docs/en/keybindings#content-area)

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

Customize keyboard shortcuts

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

- [Configuration file](https://code.claude.com/docs/en/keybindings#configuration-file)
- [Contexts](https://code.claude.com/docs/en/keybindings#contexts)
- [Available actions](https://code.claude.com/docs/en/keybindings#available-actions)
- [App actions](https://code.claude.com/docs/en/keybindings#app-actions)
- [History actions](https://code.claude.com/docs/en/keybindings#history-actions)
- [Chat actions](https://code.claude.com/docs/en/keybindings#chat-actions)
- [Autocomplete actions](https://code.claude.com/docs/en/keybindings#autocomplete-actions)
- [Confirmation actions](https://code.claude.com/docs/en/keybindings#confirmation-actions)
- [Permission actions](https://code.claude.com/docs/en/keybindings#permission-actions)
- [Transcript actions](https://code.claude.com/docs/en/keybindings#transcript-actions)
- [History search actions](https://code.claude.com/docs/en/keybindings#history-search-actions)
- [Task actions](https://code.claude.com/docs/en/keybindings#task-actions)
- [Theme actions](https://code.claude.com/docs/en/keybindings#theme-actions)
- [Help actions](https://code.claude.com/docs/en/keybindings#help-actions)
- [Tabs actions](https://code.claude.com/docs/en/keybindings#tabs-actions)
- [Attachments actions](https://code.claude.com/docs/en/keybindings#attachments-actions)
- [Footer actions](https://code.claude.com/docs/en/keybindings#footer-actions)
- [Message selector actions](https://code.claude.com/docs/en/keybindings#message-selector-actions)
- [Diff actions](https://code.claude.com/docs/en/keybindings#diff-actions)
- [Model picker actions](https://code.claude.com/docs/en/keybindings#model-picker-actions)
- [Select actions](https://code.claude.com/docs/en/keybindings#select-actions)
- [Plugin actions](https://code.claude.com/docs/en/keybindings#plugin-actions)
- [Settings actions](https://code.claude.com/docs/en/keybindings#settings-actions)
- [Voice actions](https://code.claude.com/docs/en/keybindings#voice-actions)
- [Keystroke syntax](https://code.claude.com/docs/en/keybindings#keystroke-syntax)
- [Modifiers](https://code.claude.com/docs/en/keybindings#modifiers)
- [Uppercase letters](https://code.claude.com/docs/en/keybindings#uppercase-letters)
- [Chords](https://code.claude.com/docs/en/keybindings#chords)
- [Special keys](https://code.claude.com/docs/en/keybindings#special-keys)
- [Unbind default shortcuts](https://code.claude.com/docs/en/keybindings#unbind-default-shortcuts)
- [Reserved shortcuts](https://code.claude.com/docs/en/keybindings#reserved-shortcuts)
- [Terminal conflicts](https://code.claude.com/docs/en/keybindings#terminal-conflicts)
- [Vim mode interaction](https://code.claude.com/docs/en/keybindings#vim-mode-interaction)
- [Validation](https://code.claude.com/docs/en/keybindings#validation)

Configuration

# Customize keyboard shortcuts

Copy page

Customize keyboard shortcuts in Claude Code with a keybindings configuration file.

Copy page

Customizable keyboard shortcuts require Claude Code v2.1.18 or later. Check your version with `claude --version`.

Claude Code supports customizable keyboard shortcuts. Run `/keybindings` to create or open your configuration file at `~/.claude/keybindings.json`.

## [​](https://code.claude.com/docs/en/keybindings\#configuration-file)  Configuration file

The keybindings configuration file is an object with a `bindings` array. Each block specifies a context and a map of keystrokes to actions.

Changes to the keybindings file are automatically detected and applied without restarting Claude Code.

| Field | Description |
| --- | --- |
| `$schema` | Optional JSON Schema URL for editor autocompletion |
| `$docs` | Optional documentation URL |
| `bindings` | Array of binding blocks by context |

This example binds `Ctrl+E` to open an external editor in the chat context, and unbinds `Ctrl+U`:

Report incorrect code

Copy

Ask AI

```
{
  "$schema": "https://www.schemastore.org/claude-code-keybindings.json",
  "$docs": "https://code.claude.com/docs/en/keybindings",
  "bindings": [\
    {\
      "context": "Chat",\
      "bindings": {\
        "ctrl+e": "chat:externalEditor",\
        "ctrl+u": null\
      }\
    }\
  ]
}
```

## [​](https://code.claude.com/docs/en/keybindings\#contexts)  Contexts

Each binding block specifies a **context** where the bindings apply:

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
| `Footer` | Footer indicator navigation (tasks, teams, diff) |
| `MessageSelector` | Rewind and summarize dialog message selection |
| `DiffDialog` | Diff viewer navigation |
| `ModelPicker` | Model picker effort level |
| `Select` | Generic select/list components |
| `Plugin` | Plugin dialog (browse, discover, manage) |

## [​](https://code.claude.com/docs/en/keybindings\#available-actions)  Available actions

Actions follow a `namespace:action` format, such as `chat:submit` to send a message or `app:toggleTodos` to show the task list. Each context has specific actions available.

### [​](https://code.claude.com/docs/en/keybindings\#app-actions)  App actions

Actions available in the `Global` context:

| Action | Default | Description |
| --- | --- | --- |
| `app:interrupt` | Ctrl+C | Cancel current operation |
| `app:exit` | Ctrl+D | Exit Claude Code |
| `app:toggleTodos` | Ctrl+T | Toggle task list visibility |
| `app:toggleTranscript` | Ctrl+O | Toggle verbose transcript |

### [​](https://code.claude.com/docs/en/keybindings\#history-actions)  History actions

Actions for navigating command history:

| Action | Default | Description |
| --- | --- | --- |
| `history:search` | Ctrl+R | Open history search |
| `history:previous` | Up | Previous history item |
| `history:next` | Down | Next history item |

### [​](https://code.claude.com/docs/en/keybindings\#chat-actions)  Chat actions

Actions available in the `Chat` context:

| Action | Default | Description |
| --- | --- | --- |
| `chat:cancel` | Escape | Cancel current input |
| `chat:killAgents` | Ctrl+X Ctrl+K | Kill all background agents |
| `chat:cycleMode` | Shift+Tab\* | Cycle permission modes |
| `chat:modelPicker` | Cmd+P / Meta+P | Open model picker |
| `chat:fastMode` | Meta+O | Toggle fast mode |
| `chat:thinkingToggle` | Cmd+T / Meta+T | Toggle extended thinking |
| `chat:submit` | Enter | Submit message |
| `chat:undo` | Ctrl+\_ | Undo last action |
| `chat:externalEditor` | Ctrl+G, Ctrl+X Ctrl+E | Open in external editor |
| `chat:stash` | Ctrl+S | Stash current prompt |
| `chat:imagePaste` | Ctrl+V (Alt+V on Windows) | Paste image |

\*On Windows without VT mode (Node <24.2.0/<22.17.0, Bun <1.2.23), defaults to Meta+M.

### [​](https://code.claude.com/docs/en/keybindings\#autocomplete-actions)  Autocomplete actions

Actions available in the `Autocomplete` context:

| Action | Default | Description |
| --- | --- | --- |
| `autocomplete:accept` | Tab | Accept suggestion |
| `autocomplete:dismiss` | Escape | Dismiss menu |
| `autocomplete:previous` | Up | Previous suggestion |
| `autocomplete:next` | Down | Next suggestion |

### [​](https://code.claude.com/docs/en/keybindings\#confirmation-actions)  Confirmation actions

Actions available in the `Confirmation` context:

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

### [​](https://code.claude.com/docs/en/keybindings\#permission-actions)  Permission actions

Actions available in the `Confirmation` context for permission dialogs:

| Action | Default | Description |
| --- | --- | --- |
| `permission:toggleDebug` | Ctrl+D | Toggle permission debug info |

### [​](https://code.claude.com/docs/en/keybindings\#transcript-actions)  Transcript actions

Actions available in the `Transcript` context:

| Action | Default | Description |
| --- | --- | --- |
| `transcript:toggleShowAll` | Ctrl+E | Toggle show all content |
| `transcript:exit` | Ctrl+C, Escape | Exit transcript view |

### [​](https://code.claude.com/docs/en/keybindings\#history-search-actions)  History search actions

Actions available in the `HistorySearch` context:

| Action | Default | Description |
| --- | --- | --- |
| `historySearch:next` | Ctrl+R | Next match |
| `historySearch:accept` | Escape, Tab | Accept selection |
| `historySearch:cancel` | Ctrl+C | Cancel search |
| `historySearch:execute` | Enter | Execute selected command |

### [​](https://code.claude.com/docs/en/keybindings\#task-actions)  Task actions

Actions available in the `Task` context:

| Action | Default | Description |
| --- | --- | --- |
| `task:background` | Ctrl+B | Background current task |

### [​](https://code.claude.com/docs/en/keybindings\#theme-actions)  Theme actions

Actions available in the `ThemePicker` context:

| Action | Default | Description |
| --- | --- | --- |
| `theme:toggleSyntaxHighlighting` | Ctrl+T | Toggle syntax highlighting |

### [​](https://code.claude.com/docs/en/keybindings\#help-actions)  Help actions

Actions available in the `Help` context:

| Action | Default | Description |
| --- | --- | --- |
| `help:dismiss` | Escape | Close help menu |

### [​](https://code.claude.com/docs/en/keybindings\#tabs-actions)  Tabs actions

Actions available in the `Tabs` context:

| Action | Default | Description |
| --- | --- | --- |
| `tabs:next` | Tab, Right | Next tab |
| `tabs:previous` | Shift+Tab, Left | Previous tab |

### [​](https://code.claude.com/docs/en/keybindings\#attachments-actions)  Attachments actions

Actions available in the `Attachments` context:

| Action | Default | Description |
| --- | --- | --- |
| `attachments:next` | Right | Next attachment |
| `attachments:previous` | Left | Previous attachment |
| `attachments:remove` | Backspace, Delete | Remove selected attachment |
| `attachments:exit` | Down, Escape | Exit attachment bar |

### [​](https://code.claude.com/docs/en/keybindings\#footer-actions)  Footer actions

Actions available in the `Footer` context:

| Action | Default | Description |
| --- | --- | --- |
| `footer:next` | Right | Next footer item |
| `footer:previous` | Left | Previous footer item |
| `footer:up` | Up | Navigate up in footer (deselects at top) |
| `footer:down` | Down | Navigate down in footer |
| `footer:openSelected` | Enter | Open selected footer item |
| `footer:clearSelection` | Escape | Clear footer selection |

### [​](https://code.claude.com/docs/en/keybindings\#message-selector-actions)  Message selector actions

Actions available in the `MessageSelector` context:

| Action | Default | Description |
| --- | --- | --- |
| `messageSelector:up` | Up, K, Ctrl+P | Move up in list |
| `messageSelector:down` | Down, J, Ctrl+N | Move down in list |
| `messageSelector:top` | Ctrl+Up, Shift+Up, Meta+Up, Shift+K | Jump to top |
| `messageSelector:bottom` | Ctrl+Down, Shift+Down, Meta+Down, Shift+J | Jump to bottom |
| `messageSelector:select` | Enter | Select message |

### [​](https://code.claude.com/docs/en/keybindings\#diff-actions)  Diff actions

Actions available in the `DiffDialog` context:

| Action | Default | Description |
| --- | --- | --- |
| `diff:dismiss` | Escape | Close diff viewer |
| `diff:previousSource` | Left | Previous diff source |
| `diff:nextSource` | Right | Next diff source |
| `diff:previousFile` | Up | Previous file in diff |
| `diff:nextFile` | Down | Next file in diff |
| `diff:viewDetails` | Enter | View diff details |
| `diff:back` | (context-specific) | Go back in diff viewer |

### [​](https://code.claude.com/docs/en/keybindings\#model-picker-actions)  Model picker actions

Actions available in the `ModelPicker` context:

| Action | Default | Description |
| --- | --- | --- |
| `modelPicker:decreaseEffort` | Left | Decrease effort level |
| `modelPicker:increaseEffort` | Right | Increase effort level |

### [​](https://code.claude.com/docs/en/keybindings\#select-actions)  Select actions

Actions available in the `Select` context:

| Action | Default | Description |
| --- | --- | --- |
| `select:next` | Down, J, Ctrl+N | Next option |
| `select:previous` | Up, K, Ctrl+P | Previous option |
| `select:accept` | Enter | Accept selection |
| `select:cancel` | Escape | Cancel selection |

### [​](https://code.claude.com/docs/en/keybindings\#plugin-actions)  Plugin actions

Actions available in the `Plugin` context:

| Action | Default | Description |
| --- | --- | --- |
| `plugin:toggle` | Space | Toggle plugin selection |
| `plugin:install` | I | Install selected plugins |

### [​](https://code.claude.com/docs/en/keybindings\#settings-actions)  Settings actions

Actions available in the `Settings` context:

| Action | Default | Description |
| --- | --- | --- |
| `settings:search` | / | Enter search mode |
| `settings:retry` | R | Retry loading usage data (on error) |

### [​](https://code.claude.com/docs/en/keybindings\#voice-actions)  Voice actions

Actions available in the `Chat` context when [voice dictation](https://code.claude.com/docs/en/voice-dictation) is enabled:

| Action | Default | Description |
| --- | --- | --- |
| `voice:pushToTalk` | Space | Hold to dictate a prompt |

## [​](https://code.claude.com/docs/en/keybindings\#keystroke-syntax)  Keystroke syntax

### [​](https://code.claude.com/docs/en/keybindings\#modifiers)  Modifiers

Use modifier keys with the `+` separator:

- `ctrl` or `control` \- Control key
- `alt`, `opt`, or `option` \- Alt/Option key
- `shift` \- Shift key
- `meta`, `cmd`, or `command` \- Meta/Command key

For example:

Report incorrect code

Copy

Ask AI

```
ctrl+k          Single key with modifier
shift+tab       Shift + Tab
meta+p          Command/Meta + P
ctrl+shift+c    Multiple modifiers
```

### [​](https://code.claude.com/docs/en/keybindings\#uppercase-letters)  Uppercase letters

A standalone uppercase letter implies Shift. For example, `K` is equivalent to `shift+k`. This is useful for vim-style bindings where uppercase and lowercase keys have different meanings.Uppercase letters with modifiers (e.g., `ctrl+K`) are treated as stylistic and do **not** imply Shift: `ctrl+K` is the same as `ctrl+k`.

### [​](https://code.claude.com/docs/en/keybindings\#chords)  Chords

Chords are sequences of keystrokes separated by spaces:

Report incorrect code

Copy

Ask AI

```
ctrl+k ctrl+s   Press Ctrl+K, release, then Ctrl+S
```

### [​](https://code.claude.com/docs/en/keybindings\#special-keys)  Special keys

- `escape` or `esc` \- Escape key
- `enter` or `return` \- Enter key
- `tab` \- Tab key
- `space` \- Space bar
- `up`, `down`, `left`, `right` \- Arrow keys
- `backspace`, `delete` \- Delete keys

## [​](https://code.claude.com/docs/en/keybindings\#unbind-default-shortcuts)  Unbind default shortcuts

Set an action to `null` to unbind a default shortcut:

Report incorrect code

Copy

Ask AI

```
{
  "bindings": [\
    {\
      "context": "Chat",\
      "bindings": {\
        "ctrl+s": null\
      }\
    }\
  ]
}
```

## [​](https://code.claude.com/docs/en/keybindings\#reserved-shortcuts)  Reserved shortcuts

These shortcuts cannot be rebound:

| Shortcut | Reason |
| --- | --- |
| Ctrl+C | Hardcoded interrupt/cancel |
| Ctrl+D | Hardcoded exit |
| Ctrl+M | Identical to Enter in terminals (both send CR) |

## [​](https://code.claude.com/docs/en/keybindings\#terminal-conflicts)  Terminal conflicts

Some shortcuts may conflict with terminal multiplexers:

| Shortcut | Conflict |
| --- | --- |
| Ctrl+B | tmux prefix (press twice to send) |
| Ctrl+A | GNU screen prefix |
| Ctrl+Z | Unix process suspend (SIGTSTP) |

## [​](https://code.claude.com/docs/en/keybindings\#vim-mode-interaction)  Vim mode interaction

When vim mode is enabled (`/vim`), keybindings and vim mode operate independently:

- **Vim mode** handles input at the text input level (cursor movement, modes, motions)
- **Keybindings** handle actions at the component level (toggle todos, submit, etc.)
- The Escape key in vim mode switches INSERT to NORMAL mode; it does not trigger `chat:cancel`
- Most Ctrl+key shortcuts pass through vim mode to the keybinding system
- In vim NORMAL mode, `?` shows the help menu (vim behavior)

## [​](https://code.claude.com/docs/en/keybindings\#validation)  Validation

Claude Code validates your keybindings and shows warnings for:

- Parse errors (invalid JSON or structure)
- Invalid context names
- Reserved shortcut conflicts
- Terminal multiplexer conflicts
- Duplicate bindings in the same context

Run `/doctor` to see any keybinding warnings.

Was this page helpful?

YesNo

[Customize status line](https://code.claude.com/docs/en/statusline)

Ctrl+I

[Claude Code Docs home page![light logo](https://mintcdn.com/claude-code/c5r9_6tjPMzFdDDT/logo/light.svg?fit=max&auto=format&n=c5r9_6tjPMzFdDDT&q=85&s=78fd01ff4f4340295a4f66e2ea54903c)![dark logo](https://mintcdn.com/claude-code/c5r9_6tjPMzFdDDT/logo/dark.svg?fit=max&auto=format&n=c5r9_6tjPMzFdDDT&q=85&s=1298a0c3b3a1da603b190d0de0e31712)](https://code.claude.com/docs/en/overview)

[x](https://x.com/AnthropicAI) [linkedin](https://www.linkedin.com/company/anthropicresearch)

Company

[Anthropic](https://www.anthropic.com/company) [Careers](https://www.anthropic.com/careers) [Economic Futures](https://www.anthropic.com/economic-futures) [Research](https://www.anthropic.com/research) [News](https://www.anthropic.com/news) [Trust center](https://trust.anthropic.com/) [Transparency](https://www.anthropic.com/transparency)

Help and security

[Availability](https://www.anthropic.com/supported-countries) [Status](https://status.anthropic.com/) [Support center](https://support.claude.com/)

Learn

[Courses](https://www.anthropic.com/learn) [MCP connectors](https://claude.com/partners/mcp) [Customer stories](https://www.claude.com/customers) [Engineering blog](https://www.anthropic.com/engineering) [Events](https://www.anthropic.com/events) [Powered by Claude](https://claude.com/partners/powered-by-claude) [Service partners](https://claude.com/partners/services) [Startups program](https://claude.com/programs/startups)

Terms and policies

[Privacy choices](https://code.claude.com/docs/en/keybindings#) [Privacy policy](https://www.anthropic.com/legal/privacy) [Disclosure policy](https://www.anthropic.com/responsible-disclosure-policy) [Usage policy](https://www.anthropic.com/legal/aup) [Commercial terms](https://www.anthropic.com/legal/commercial-terms) [Consumer terms](https://www.anthropic.com/legal/consumer-terms)

Assistant

Responses are generated using AI and may contain mistakes.