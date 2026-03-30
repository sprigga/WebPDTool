# Claude Code Settings

> Source: https://code.claude.com/docs/en/settings
> Configure Claude Code with global and project-level settings, and environment variables.

Claude Code offers a variety of settings to configure its behavior. You can configure Claude Code by running the `/config` command in the interactive REPL, which opens a tabbed Settings interface.

---

## Table of Contents

- [Configuration Scopes](#configuration-scopes)
- [Settings Files](#settings-files)
- [Available Settings](#available-settings)
- [Global Config Settings](#global-config-settings)
- [Worktree Settings](#worktree-settings)
- [Permission Settings](#permission-settings)
- [Sandbox Settings](#sandbox-settings)
- [Attribution Settings](#attribution-settings)
- [File Suggestion Settings](#file-suggestion-settings)
- [Hook Configuration](#hook-configuration)
- [Settings Precedence](#settings-precedence)
- [System Prompt](#system-prompts)
- [Excluding Sensitive Files](#excluding-sensitive-files)
- [Subagent Configuration](#subagent-configuration)
- [Plugin Configuration](#plugin-configuration)
- [Environment Variables](#environment-variables)
- [Tools Available to Claude](#tools-available-to-claude)

---

## Configuration Scopes

Claude Code uses a **scope system** to determine where configurations apply and who they're shared with.

### Available Scopes

| Scope | Location | Who it Affects | Shared with Team? |
| --- | --- | --- | --- |
| **Managed** | Server-managed settings, plist / registry, or system-level `managed-settings.json` | All users on the machine | Yes (deployed by IT) |
| **User** | `~/.claude/` directory | You, across all projects | No |
| **Project** | `.claude/` in repository | All collaborators on this repository | Yes (committed to git) |
| **Local** | `.claude/settings.local.json` | You, in this repository only | No (gitignored) |

### When to Use Each Scope

**Managed scope** is for:
- Security policies that must be enforced organization-wide
- Compliance requirements that can't be overridden
- Standardized configurations deployed by IT/DevOps

**User scope** is best for:
- Personal preferences you want everywhere (themes, editor settings)
- Tools and plugins you use across all projects
- API keys and authentication (stored securely)

**Project scope** is best for:
- Team-shared settings (permissions, hooks, MCP servers)
- Plugins the whole team should have
- Standardizing tooling across collaborators

**Local scope** is best for:
- Personal overrides for a specific project
- Testing configurations before sharing with the team
- Machine-specific settings that won't work for others

### How Scopes Interact

When the same setting is configured in multiple scopes, more specific scopes take precedence:

1. **Managed** (highest) — can't be overridden by anything
2. **Command line arguments** — temporary session overrides
3. **Local** — overrides project and user settings
4. **Project** — overrides user settings
5. **User** (lowest) — applies when nothing else specifies the setting

> **Example:** If a permission is allowed in user settings but denied in project settings, the project setting takes precedence and the permission is blocked.

### What Uses Scopes

| Feature | User Location | Project Location | Local Location |
| --- | --- | --- | --- |
| **Settings** | `~/.claude/settings.json` | `.claude/settings.json` | `.claude/settings.local.json` |
| **Subagents** | `~/.claude/agents/` | `.claude/agents/` | None |
| **MCP servers** | `~/.claude.json` | `.mcp.json` | `~/.claude.json` (per-project) |
| **Plugins** | `~/.claude/settings.json` | `.claude/settings.json` | `.claude/settings.local.json` |
| **CLAUDE.md** | `~/.claude/CLAUDE.md` | `CLAUDE.md` or `.claude/CLAUDE.md` | None |

---

## Settings Files

The `settings.json` file is the official mechanism for configuring Claude Code through hierarchical settings.

### User Settings

Defined in `~/.claude/settings.json` — apply to all projects.

### Project Settings

- **Shared** (`.claude/settings.json`) — checked into source control, shared with your team
- **Local** (`.claude/settings.local.json`) — not checked in, useful for personal preferences and experimentation. Claude Code auto-configures git to ignore this file.

### Managed Settings

For organizations that need centralized control. All use the same JSON format and **cannot** be overridden by user or project settings:

- **Server-managed settings**: Delivered from Anthropic's servers via the Claude.ai admin console.
- **MDM/OS-level policies**: Delivered through native device management:
  - **macOS**: `com.anthropic.claudecode` managed preferences domain (via configuration profiles in Jamf, Kandji, etc.)
  - **Windows**: `HKLM\SOFTWARE\Policies\ClaudeCode` registry key with a `Settings` value (REG_SZ or REG_EXPAND_SZ) containing JSON (via Group Policy or Intune)
  - **Windows (user-level)**: `HKCU\SOFTWARE\Policies\ClaudeCode` (lowest policy priority, only when no admin-level source exists)
- **File-based**: `managed-settings.json` and `managed-mcp.json` deployed to system directories:
  - **macOS**: `/Library/Application Support/ClaudeCode/`
  - **Linux and WSL**: `/etc/claude-code/`
  - **Windows**: `C:\Program Files\ClaudeCode\`

> **Note:** The legacy Windows path `C:\ProgramData\ClaudeCode\managed-settings.json` is no longer supported as of v2.1.75.

File-based managed settings also support a **drop-in directory** at `managed-settings.d/` alongside `managed-settings.json`. Following the systemd convention, `managed-settings.json` is merged first as the base, then all `*.json` files in the drop-in directory are sorted alphabetically and merged on top. Later files override earlier ones for scalar values; arrays are concatenated and de-duplicated; objects are deep-merged. Hidden files starting with `.` are ignored. Use numeric prefixes to control merge order (e.g., `10-telemetry.json`, `20-security.json`).

### Other Configuration

`~/.claude.json` contains your preferences (theme, notification settings, editor mode), OAuth session, MCP server configurations, per-project state (allowed tools, trust settings), and various caches. Project-scoped MCP servers are stored separately in `.mcp.json`.

Claude Code automatically creates timestamped backups and retains the five most recent backups.

### Example settings.json

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "permissions": {
    "allow": [
      "Bash(npm run lint)",
      "Bash(npm run test *)",
      "Read(~/.zshrc)"
    ],
    "deny": [
      "Bash(curl *)",
      "Read(./.env)",
      "Read(./.env.*)",
      "Read(./secrets/**)"
    ]
  },
  "env": {
    "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
    "OTEL_METRICS_EXPORTER": "otlp"
  },
  "companyAnnouncements": [
    "Welcome to Acme Corp! Review our code guidelines at docs.acme.com",
    "Reminder: Code reviews required for all PRs",
    "New security policy in effect"
  ]
}
```

> The `$schema` line points to the [official JSON schema](https://json.schemastore.org/claude-code-settings.json) for Claude Code settings. Adding it enables autocomplete and inline validation in VS Code, Cursor, and other editors that support JSON schema validation.

---

## Available Settings

`settings.json` supports the following options:

| Key | Description | Example |
| --- | --- | --- |
| `apiKeyHelper` | Custom script (executed in `/bin/sh`) to generate an auth value. Sent as `X-Api-Key` and `Authorization: Bearer` headers | `/bin/generate_temp_api_key.sh` |
| `autoMemoryDirectory` | Custom directory for auto memory storage. Accepts `~/`-expanded paths. Not accepted in project settings (to prevent shared repos from redirecting memory writes to sensitive locations) | `"~/my-memory-dir"` |
| `cleanupPeriodDays` | Sessions inactive longer than this are deleted at startup (default: 30). Set to `0` to delete all transcripts at startup and disable session persistence entirely | `20` |
| `companyAnnouncements` | Announcement(s) to display at startup. If multiple, cycled through at random | `["Welcome to Acme Corp!"]` |
| `env` | Environment variables applied to every session | `{"FOO": "bar"}` |
| `attribution` | Customize attribution for git commits and PRs. See [Attribution Settings](#attribution-settings) | `{"commit": "...", "pr": ""}` |
| `includeCoAuthoredBy` | **Deprecated**: Use `attribution` instead. Whether to include co-authored-by byline (default: `true`) | `false` |
| `includeGitInstructions` | Include built-in git instructions in system prompt (default: `true`) | `false` |
| `permissions` | Permission rules. See [Permission Settings](#permission-settings) | |
| `autoMode` | Customize auto mode classifier. Contains `environment`, `allow`, and `soft_deny` arrays. Not read from shared project settings | `{"environment": ["Trusted repo: ..."]}` |
| `disableAutoMode` | Set to `"disable"` to prevent auto mode activation | `"disable"` |
| `useAutoModeDuringPlan` | Whether plan mode uses auto mode semantics (default: `true`) | `false` |
| `hooks` | Custom commands at lifecycle events. See [hooks documentation](https://code.claude.com/docs/en/hooks) | |
| `defaultShell` | Default shell for `!` commands: `"bash"` (default) or `"powershell"` | `"powershell"` |
| `disableAllHooks` | Disable all hooks and custom status line | `true` |
| `allowManagedHooksOnly` | (Managed only) Prevent user/project/plugin hooks; only managed and SDK hooks load | `true` |
| `allowedHttpHookUrls` | Allowlist of URL patterns for HTTP hooks. Supports `*` wildcard | `["https://hooks.example.com/*"]` |
| `httpHookAllowedEnvVars` | Allowlist of env var names HTTP hooks can interpolate into headers | `["MY_TOKEN"]` |
| `allowManagedPermissionRulesOnly` | (Managed only) Prevent user/project settings from defining permission rules | `true` |
| `allowManagedMcpServersOnly` | (Managed only) Only admin-defined MCP allowlist applies | `true` |
| `model` | Override the default model | `"claude-sonnet-4-6"` |
| `availableModels` | Restrict which models users can select via `/model`, `--model`, etc. | `["sonnet", "haiku"]` |
| `modelOverrides` | Map Anthropic model IDs to provider-specific IDs (e.g., Bedrock ARNs) | `{"claude-opus-4-6": "arn:aws:bedrock:..."}` |
| `effortLevel` | Persist effort level: `"low"`, `"medium"`, or `"high"` | `"medium"` |
| `otelHeadersHelper` | Script to generate dynamic OpenTelemetry headers | `/bin/generate_otel_headers.sh` |
| `statusLine` | Custom status line configuration | `{"type": "command", "command": "~/.claude/statusline.sh"}` |
| `fileSuggestion` | Custom script for `@` file autocomplete | `{"type": "command", "command": "~/.claude/file-suggestion.sh"}` |
| `respectGitignore` | Whether `@` file picker respects `.gitignore` (default: `true`) | `false` |
| `outputStyle` | Output style to adjust system prompt | `"Explanatory"` |
| `agent` | Run main thread as a named subagent | `"code-reviewer"` |
| `forceLoginMethod` | Restrict login: `claudeai` or `console` | `claudeai` |
| `forceLoginOrgUUID` | Specify organization UUID for auto-selection during login | `"xxxxxxxx-xxxx-..."` |
| `enableAllProjectMcpServers` | Auto-approve all MCP servers in project `.mcp.json` | `true` |
| `enabledMcpjsonServers` | List of specific `.mcp.json` servers to approve | `["memory", "github"]` |
| `disabledMcpjsonServers` | List of specific `.mcp.json` servers to reject | `["filesystem"]` |
| `channelsEnabled` | (Managed only) Allow channels for Team/Enterprise users | `true` |
| `allowedChannelPlugins` | (Managed only) Allowlist of channel plugins | `[{ "marketplace": "...", "plugin": "..." }]` |
| `allowedMcpServers` | Managed allowlist of MCP servers | `[{ "serverName": "github" }]` |
| `deniedMcpServers` | Managed denylist of MCP servers | `[{ "serverName": "filesystem" }]` |
| `strictKnownMarketplaces` | Managed allowlist of plugin marketplaces | `[{ "source": "github", "repo": "..." }]` |
| `blockedMarketplaces` | (Managed only) Blocklist of marketplace sources | `[{ "source": "github", "repo": "..." }]` |
| `pluginTrustMessage` | (Managed only) Custom message for plugin trust warning | `"All plugins approved by IT"` |
| `awsAuthRefresh` | Custom script for AWS auth refresh | `aws sso login --profile myprofile` |
| `awsCredentialExport` | Custom script outputting AWS credential JSON | `/bin/generate_aws_grant.sh` |
| `alwaysThinkingEnabled` | Enable extended thinking by default | `true` |
| `plansDirectory` | Custom plan file storage location (relative to project root) | `"./plans"` |
| `showClearContextOnPlanAccept` | Show "clear context" option on plan accept (default: `false`) | `true` |
| `spinnerVerbs` | Customize spinner action verbs | `{"mode": "append", "verbs": ["Pondering"]}` |
| `language` | Claude's preferred response language | `"japanese"` |
| `voiceEnabled` | Enable push-to-talk voice dictation | `true` |
| `autoUpdatesChannel` | Release channel: `"stable"` or `"latest"` (default) | `"stable"` |
| `spinnerTipsEnabled` | Show tips in spinner (default: `true`) | `false` |
| `spinnerTipsOverride` | Override spinner tips with custom strings | `{ "excludeDefault": true, "tips": ["..."] }` |
| `prefersReducedMotion` | Reduce/disable UI animations | `true` |
| `fastModePerSessionOptIn` | Fast mode doesn't persist across sessions (default: `false`) | `true` |
| `teammateMode` | Agent team display mode: `auto`, `in-process`, or `tmux` | `"in-process"` |
| `feedbackSurveyRate` | Probability (0-1) for session quality survey | `0.05` |

---

## Global Config Settings

These settings are stored in `~/.claude.json` (not `settings.json`). Adding them to `settings.json` will trigger a schema validation error.

| Key | Description | Example |
| --- | --- | --- |
| `autoConnectIde` | Auto-connect to running IDE from external terminal (default: `false`) | `true` |
| `autoInstallIdeExtension` | Auto-install Claude Code IDE extension in VS Code (default: `true`) | `false` |
| `editorMode` | Key binding mode: `"normal"` or `"vim"` (default: `"normal"`) | `"vim"` |
| `showTurnDuration` | Show turn duration after responses (default: `true`) | `false` |
| `terminalProgressBarEnabled` | Show terminal progress bar (default: `true`) | `false` |

---

## Worktree Settings

Configure how `--worktree` creates and manages git worktrees.

| Key | Description | Example |
| --- | --- | --- |
| `worktree.symlinkDirectories` | Directories to symlink from main repo into each worktree | `["node_modules", ".cache"]` |
| `worktree.sparsePaths` | Directories to check out via git sparse-checkout (cone mode) | `["packages/my-app", "shared/utils"]` |

---

## Permission Settings

| Key | Description | Example |
| --- | --- | --- |
| `allow` | Array of permission rules to **allow** tool use | `[ "Bash(git diff *)" ]` |
| `ask` | Array of permission rules to **ask** for confirmation | `[ "Bash(git push *)" ]` |
| `deny` | Array of permission rules to **deny** tool use | `[ "WebFetch", "Bash(curl *)", "Read(./.env)" ]` |
| `additionalDirectories` | Additional working directories Claude has access to | `[ "../docs/" ]` |
| `defaultMode` | Default permission mode | `"acceptEdits"` |
| `disableBypassPermissionsMode` | Set to `"disable"` to prevent `bypassPermissions` mode | `"disable"` |

### Permission Rule Syntax

Permission rules follow the format `Tool` or `Tool(specifier)`. Rules are evaluated in order: **deny first, then ask, then allow**. The first matching rule wins.

| Rule | Effect |
| --- | --- |
| `Bash` | Matches all Bash commands |
| `Bash(npm run *)` | Matches commands starting with `npm run` |
| `Read(./.env)` | Matches reading the `.env` file |
| `WebFetch(domain:example.com)` | Matches fetch requests to example.com |

---

## Sandbox Settings

Configure advanced sandboxing behavior. Sandboxing isolates bash commands from your filesystem and network.

| Key | Description | Example |
| --- | --- | --- |
| `enabled` | Enable bash sandboxing (macOS, Linux, WSL2) (default: `false`) | `true` |
| `failIfUnavailable` | Exit with error if sandbox can't start (default: `false`) | `true` |
| `autoAllowBashIfSandboxed` | Auto-approve bash commands when sandboxed (default: `true`) | `true` |
| `excludedCommands` | Commands that should run outside the sandbox | `["git", "docker"]` |
| `allowUnsandboxedCommands` | Allow `dangerouslyDisableSandbox` escape hatch (default: `true`) | `false` |
| `filesystem.allowWrite` | Additional writable paths (merged across scopes) | `["/tmp/build", "~/.kube"]` |
| `filesystem.denyWrite` | Non-writable paths (merged across scopes) | `["/etc", "/usr/local/bin"]` |
| `filesystem.denyRead` | Non-readable paths (merged across scopes) | `["~/.aws/credentials"]` |
| `filesystem.allowRead` | Re-allow reading within `denyRead` regions | `["."]` |
| `filesystem.allowManagedReadPathsOnly` | (Managed only) Only managed `allowRead` respected | `true` |
| `network.allowUnixSockets` | Unix socket paths accessible in sandbox | `["~/.ssh/agent-socket"]` |
| `network.allowAllUnixSockets` | Allow all Unix socket connections (default: `false`) | `true` |
| `network.allowLocalBinding` | Allow binding to localhost ports, macOS only (default: `false`) | `true` |
| `network.allowedDomains` | Domains for outbound traffic (supports wildcards) | `["github.com", "*.npmjs.org"]` |
| `network.allowManagedDomainsOnly` | (Managed only) Only managed domains respected | `true` |
| `network.httpProxyPort` | Custom HTTP proxy port | `8080` |
| `network.socksProxyPort` | Custom SOCKS5 proxy port | `8081` |
| `enableWeakerNestedSandbox` | Enable weaker sandbox for unprivileged Docker (reduces security) | `true` |
| `enableWeakerNetworkIsolation` | (macOS only) Allow system TLS trust service (reduces security) | `true` |

### Sandbox Path Prefixes

| Prefix | Meaning | Example |
| --- | --- | --- |
| `/` | Absolute path from filesystem root | `/tmp/build` stays `/tmp/build` |
| `~/` | Relative to home directory | `~/.kube` becomes `$HOME/.kube` |
| `./` or no prefix | Relative to project root (project settings) or `~/.claude` (user settings) | `./output` resolves to `<project-root>/output` |

### Sandbox Configuration Example

```json
{
  "sandbox": {
    "enabled": true,
    "autoAllowBashIfSandboxed": true,
    "excludedCommands": ["docker"],
    "filesystem": {
      "allowWrite": ["/tmp/build", "~/.kube"],
      "denyRead": ["~/.aws/credentials"]
    },
    "network": {
      "allowedDomains": ["github.com", "*.npmjs.org", "registry.yarnpkg.com"],
      "allowUnixSockets": ["/var/run/docker.sock"],
      "allowLocalBinding": true
    }
  }
}
```

### Filesystem and Network Restrictions

Two merged approaches:
1. **`sandbox.filesystem` settings** — OS-level sandbox boundary for all subprocess commands
2. **Permission rules** — `Edit`/`Read`/`WebFetch` allow/deny rules, merged into sandbox config

---

## Attribution Settings

Claude Code adds attribution to git commits and pull requests. Commits use git trailers (like `Co-Authored-By`); PR descriptions are plain text.

| Key | Description |
| --- | --- |
| `commit` | Attribution for git commits, including trailers. Empty string hides attribution |
| `pr` | Attribution for PR descriptions. Empty string hides attribution |

**Default commit attribution:**
```
🤖 Generated with Claude Code

   Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```

**Default PR attribution:**
```
🤖 Generated with Claude Code
```

**Example customization:**
```json
{
  "attribution": {
    "commit": "Generated with AI\n\nCo-Authored-By: AI <ai@example.com>",
    "pr": ""
  }
}
```

---

## File Suggestion Settings

Configure a custom command for `@` file path autocomplete (useful for large monorepos).

```json
{
  "fileSuggestion": {
    "type": "command",
    "command": "~/.claude/file-suggestion.sh"
  }
}
```

The command receives JSON via stdin with a `query` field and outputs newline-separated file paths to stdout (max 15):

```bash
#!/bin/bash
query=$(cat | jq -r '.query')
your-repo-file-index --query "$query" | head -20
```

---

## Hook Configuration

Controls which hooks are allowed and what HTTP hooks can access.

| Setting | Scope | Description |
| --- | --- | --- |
| `allowManagedHooksOnly` | Managed only | Block user/project/plugin hooks; only managed and SDK hooks load |
| `allowedHttpHookUrls` | Any | URL patterns HTTP hooks may target (supports `*` wildcard). Arrays merge across sources. Undefined = no restriction. Empty array = block all. |
| `httpHookAllowedEnvVars` | Any | Env var names HTTP hooks may interpolate. Each hook's effective list is the intersection. Arrays merge across sources. |

### Restrict HTTP Hook URLs

```json
{
  "allowedHttpHookUrls": ["https://hooks.example.com/*", "http://localhost:*"]
}
```

### Restrict HTTP Hook Environment Variables

```json
{
  "httpHookAllowedEnvVars": ["MY_TOKEN", "HOOK_SECRET"]
}
```

---

## Settings Precedence

From highest to lowest:

1. **Managed settings** — Cannot be overridden. Internal precedence: server-managed > MDM/OS-level > file-based (`managed-settings.d/*.json` + `managed-settings.json`) > HKCU registry (Windows only). Only one managed source is used; sources do not merge across tiers.
2. **Command line arguments** — Temporary session overrides
3. **Local project settings** (`.claude/settings.local.json`) — Personal project-specific
4. **Shared project settings** (`.claude/settings.json`) — Team-shared in source control
5. **User settings** (`~/.claude/settings.json`) — Personal global

**Array settings merge across scopes.** When the same array-valued setting appears in multiple scopes, arrays are **concatenated and deduplicated**, not replaced. Lower-priority scopes can add entries without overriding higher-priority ones.

### Verify Active Settings

Run `/status` inside Claude Code to see which settings sources are active, their origins, and any errors.

---

## Key Points About the Configuration System

- **Memory files (`CLAUDE.md`)** — Instructions and context loaded at startup
- **Settings files (JSON)** — Permissions, environment variables, tool behavior
- **Skills** — Custom prompts invoked with `/skill-name` or loaded automatically
- **MCP servers** — Additional tools and integrations
- **Precedence** — Higher-level (Managed) overrides lower-level (User/Project)
- **Inheritance** — Settings are merged, more specific add to or override broader

---

## System Prompts

Claude Code's internal system prompt is not published. To add custom instructions, use `CLAUDE.md` files or the `--append-system-prompt` flag.

---

## Excluding Sensitive Files

Use `permissions.deny` in `.claude/settings.json` to prevent access to sensitive files:

```json
{
  "permissions": {
    "deny": [
      "Read(./.env)",
      "Read(./.env.*)",
      "Read(./secrets/**)",
      "Read(./config/credentials.json)",
      "Read(./build)"
    ]
  }
}
```

This replaces the deprecated `ignorePatterns` configuration. Files matching these patterns are excluded from file discovery, search results, and read operations.

---

## Subagent Configuration

Custom AI subagents stored as Markdown files with YAML frontmatter:

- **User subagents**: `~/.claude/agents/` — Available across all projects
- **Project subagents**: `.claude/agents/` — Project-specific, shared with team

See the [subagents documentation](https://code.claude.com/docs/en/sub-agents) for details.

---

## Plugin Configuration

Claude Code supports a plugin system for skills, agents, hooks, and MCP servers distributed through marketplaces.

### Plugin Settings

```json
{
  "enabledPlugins": {
    "formatter@acme-tools": true,
    "deployer@acme-tools": true,
    "analyzer@security-plugins": false
  },
  "extraKnownMarketplaces": {
    "acme-tools": {
      "source": "github",
      "repo": "acme-corp/claude-plugins"
    }
  }
}
```

### `enabledPlugins`

Controls which plugins are enabled. Format: `"plugin-name@marketplace-name": true/false`

- **User settings** (`~/.claude/settings.json`): Personal preferences
- **Project settings** (`.claude/settings.json`): Team-shared
- **Local settings** (`.claude/settings.local.json`): Per-machine overrides

### `extraKnownMarketplaces`

Defines additional marketplaces for the repository. When a repo includes this, team members are prompted to install the marketplace and its plugins.

**Marketplace source types:**
- `github` — GitHub repository (uses `repo`)
- `git` — Any git URL (uses `url`)
- `directory` — Local filesystem path (uses `path`, development only)
- `hostPattern` — Regex pattern to match marketplace hosts
- `settings` — Inline marketplace in settings.json (uses `name` and `plugins`)

### `strictKnownMarketplaces`

**Managed settings only** — Controls which plugin marketplaces users can add.

- `undefined` (default): No restrictions
- Empty array `[]`: Complete lockdown
- List of sources: Exact match required

Supports: `github`, `git`, `url`, `npm`, `file`, `directory`, `hostPattern` sources.

### Comparison: `strictKnownMarketplaces` vs `extraKnownMarketplaces`

| Aspect | `strictKnownMarketplaces` | `extraKnownMarketplaces` |
| --- | --- | --- |
| **Purpose** | Organizational policy enforcement | Team convenience |
| **Settings file** | `managed-settings.json` only | Any settings file |
| **Behavior** | Blocks non-allowlisted additions | Auto-installs missing marketplaces |
| **When enforced** | Before network/filesystem operations | After user trust prompt |
| **Can be overridden** | No (highest precedence) | Yes |
| **Use case** | Compliance, security | Onboarding, standardization |

### Managing Plugins

Use the `/plugin` command to:
- Browse available plugins from marketplaces
- Install/uninstall plugins
- Enable/disable plugins
- View plugin details
- Add/remove marketplaces

---

## Environment Variables

Environment variables let you control Claude Code behavior without editing settings files. Any variable can also be configured in `settings.json` under the `env` key.

See the [environment variables reference](https://code.claude.com/docs/en/env-vars) for the full list.

---

## Tools Available to Claude

Claude Code has access to a set of tools for reading, editing, searching, running commands, and orchestrating subagents. Tool names are the exact strings used in permission rules and hook matchers.

See the [tools reference](https://code.claude.com/docs/en/tools-reference) for the full list.

---

## See Also

- [Permissions](https://code.claude.com/docs/en/permissions) — permission system, rule syntax, managed policies
- [Authentication](https://code.claude.com/docs/en/authentication) — user access setup
- [Troubleshooting](https://code.claude.com/docs/en/troubleshooting) — common configuration issues
