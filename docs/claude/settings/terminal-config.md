# Terminal Configuration

> Source: https://code.claude.com/docs/en/terminal-config
> Optimize your terminal setup for Claude Code.

---

## Themes and Appearance

Claude cannot control the theme of your terminal — that's handled by your terminal application. Match Claude Code's theme to your terminal via the `/config` command.

For additional customization, configure a [custom status line](./statusline.md) to display contextual information.

---

## Line Breaks

Several options for entering line breaks:

- **Quick escape**: Type `\` followed by Enter
- **Shift+Enter**: Works natively in iTerm2, WezTerm, Ghostty, and Kitty
- **Keyboard shortcut**: Set up a keybinding to insert a newline

### Set up Shift+Enter for other terminals

Run `/terminal-setup` within Claude Code to auto-configure Shift+Enter for VS Code, Alacritty, Zed, and Warp.

The `/terminal-setup` command only appears in terminals requiring manual configuration. iTerm2, WezTerm, Ghostty, and Kitty already support it natively.

### Set up Option+Enter (VS Code, iTerm2, macOS Terminal.app)

**Terminal.app:**
1. Settings → Profiles → Keyboard
2. Check "Use Option as Meta Key"

**iTerm2:**
1. Settings → Profiles → Keys
2. Under General, set Left/Right Option key to "Esc+"

**VS Code terminal:** Set `"terminal.integrated.macOptionIsMeta": true` in VS Code settings.

---

## Notification Setup

When Claude finishes working and is waiting for input, it fires a notification event.

### Terminal Notifications

Kitty and Ghostty support desktop notifications without configuration. iTerm2 requires:

1. Settings → Profiles → Terminal
2. Enable "Notification Center Alerts"
3. Click "Filter Alerts" and check "Send escape sequence-generated alerts"

If notifications aren't appearing, verify your terminal has notification permissions in OS settings.

When running inside **tmux**, enable passthrough:

```
set -g allow-passthrough on
```

Other terminals (including default macOS Terminal) do not support native notifications. Use notification hooks instead.

### Notification Hooks

Add custom behavior (play a sound, send a message) by configuring a [notification hook](https://code.claude.com/docs/en/hooks#notification). Hooks run alongside terminal notifications.

---

## Handling Large Inputs

- **Avoid direct pasting**: Claude Code may struggle with very long pasted content
- **Use file-based workflows**: Write content to a file and ask Claude to read it
- **VS Code limitation**: The VS Code terminal is prone to truncating long pastes

---

## Vim Mode

Claude Code supports a subset of Vim keybindings, enabled with `/vim` or `/config`. Set `editorMode` to `"vim"` in `~/.claude.json`.

Supported subset:

- **Mode switching**: `Esc` (NORMAL), `i`/`I`, `a`/`A`, `o`/`O` (INSERT)
- **Navigation**: `h`/`j`/`k`/`l`, `w`/`e`/`b`, `0`/`$`/`^`, `gg`/`G`, `f`/`F`/`t`/`T` with `;`/`,` repeat
- **Editing**: `x`, `dw`/`de`/`db`/`dd`/`D`, `cw`/`ce`/`cb`/`cc`/`C`, `.` (repeat)
- **Yank/paste**: `yy`/`Y`, `yw`/`ye`/`yb`, `p`/`P`
- **Text objects**: `iw`/`aw`, `iW`/`aW`, `i"`/`a"`, `i'`/`a'`, `i(`/`a(`, `i[`/`a[`, `i{`/`a{`
- **Indentation**: `>>`/`<<`
- **Line operations**: `J` (join lines)
