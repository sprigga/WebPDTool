[Skip to main content](https://code.claude.com/docs/en/permissions#content-area)

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

Configure permissions

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

- [Permission system](https://code.claude.com/docs/en/permissions#permission-system)
- [Manage permissions](https://code.claude.com/docs/en/permissions#manage-permissions)
- [Permission modes](https://code.claude.com/docs/en/permissions#permission-modes)
- [Permission rule syntax](https://code.claude.com/docs/en/permissions#permission-rule-syntax)
- [Match all uses of a tool](https://code.claude.com/docs/en/permissions#match-all-uses-of-a-tool)
- [Use specifiers for fine-grained control](https://code.claude.com/docs/en/permissions#use-specifiers-for-fine-grained-control)
- [Wildcard patterns](https://code.claude.com/docs/en/permissions#wildcard-patterns)
- [Tool-specific permission rules](https://code.claude.com/docs/en/permissions#tool-specific-permission-rules)
- [Bash](https://code.claude.com/docs/en/permissions#bash)
- [Read and Edit](https://code.claude.com/docs/en/permissions#read-and-edit)
- [WebFetch](https://code.claude.com/docs/en/permissions#webfetch)
- [MCP](https://code.claude.com/docs/en/permissions#mcp)
- [Agent (subagents)](https://code.claude.com/docs/en/permissions#agent-subagents)
- [Extend permissions with hooks](https://code.claude.com/docs/en/permissions#extend-permissions-with-hooks)
- [Working directories](https://code.claude.com/docs/en/permissions#working-directories)
- [How permissions interact with sandboxing](https://code.claude.com/docs/en/permissions#how-permissions-interact-with-sandboxing)
- [Managed settings](https://code.claude.com/docs/en/permissions#managed-settings)
- [Managed-only settings](https://code.claude.com/docs/en/permissions#managed-only-settings)
- [Configure the auto mode classifier](https://code.claude.com/docs/en/permissions#configure-the-auto-mode-classifier)
- [Define trusted infrastructure](https://code.claude.com/docs/en/permissions#define-trusted-infrastructure)
- [Override the block and allow rules](https://code.claude.com/docs/en/permissions#override-the-block-and-allow-rules)
- [Inspect the defaults and your effective config](https://code.claude.com/docs/en/permissions#inspect-the-defaults-and-your-effective-config)
- [Settings precedence](https://code.claude.com/docs/en/permissions#settings-precedence)
- [Example configurations](https://code.claude.com/docs/en/permissions#example-configurations)
- [See also](https://code.claude.com/docs/en/permissions#see-also)

Configuration

# Configure permissions

Copy page

Control what Claude Code can access and do with fine-grained permission rules, modes, and managed policies.

Copy page

Claude Code supports fine-grained permissions so that you can specify exactly what the agent is allowed to do and what it cannot. Permission settings can be checked into version control and distributed to all developers in your organization, as well as customized by individual developers.

## [​](https://code.claude.com/docs/en/permissions\#permission-system)  Permission system

Claude Code uses a tiered permission system to balance power and safety:

| Tool type | Example | Approval required | ”Yes, don’t ask again” behavior |
| --- | --- | --- | --- |
| Read-only | File reads, Grep | No | N/A |
| Bash commands | Shell execution | Yes | Permanently per project directory and command |
| File modification | Edit/write files | Yes | Until session end |

## [​](https://code.claude.com/docs/en/permissions\#manage-permissions)  Manage permissions

You can view and manage Claude Code’s tool permissions with `/permissions`. This UI lists all permission rules and the settings.json file they are sourced from.

- **Allow** rules let Claude Code use the specified tool without manual approval.
- **Ask** rules prompt for confirmation whenever Claude Code tries to use the specified tool.
- **Deny** rules prevent Claude Code from using the specified tool.

Rules are evaluated in order: **deny -> ask -> allow**. The first matching rule wins, so deny rules always take precedence.

## [​](https://code.claude.com/docs/en/permissions\#permission-modes)  Permission modes

Claude Code supports several permission modes that control how tools are approved. See [Permission modes](https://code.claude.com/docs/en/permission-modes) for when to use each one. Set the `defaultMode` in your [settings files](https://code.claude.com/docs/en/settings#settings-files):

| Mode | Description |
| --- | --- |
| `default` | Standard behavior: prompts for permission on first use of each tool |
| `acceptEdits` | Automatically accepts file edit permissions for the session |
| `plan` | Plan Mode: Claude can analyze but not modify files or execute commands |
| `auto` | Auto-approves tool calls with background safety checks that verify actions align with your request. Currently a research preview |
| `dontAsk` | Auto-denies tools unless pre-approved via `/permissions` or `permissions.allow` rules |
| `bypassPermissions` | Skips permission prompts except for writes to protected directories (see warning below) |

`bypassPermissions` mode skips permission prompts. Writes to `.git`, `.claude`, `.vscode`, and `.idea` directories still prompt for confirmation to prevent accidental corruption of repository state and local configuration. Writes to `.claude/commands`, `.claude/agents`, and `.claude/skills` are exempt and do not prompt, because Claude routinely writes there when creating skills, subagents, and commands. Only use this mode in isolated environments like containers or VMs where Claude Code cannot cause damage. Administrators can prevent this mode by setting `disableBypassPermissionsMode` to `"disable"` in [managed settings](https://code.claude.com/docs/en/permissions#managed-settings).

To prevent `bypassPermissions` or `auto` mode from being used, set `permissions.disableBypassPermissionsMode` or `disableAutoMode` to `"disable"` in any [settings file](https://code.claude.com/docs/en/settings#settings-files). These are most useful in [managed settings](https://code.claude.com/docs/en/permissions#managed-settings) where they cannot be overridden.

## [​](https://code.claude.com/docs/en/permissions\#permission-rule-syntax)  Permission rule syntax

Permission rules follow the format `Tool` or `Tool(specifier)`.

### [​](https://code.claude.com/docs/en/permissions\#match-all-uses-of-a-tool)  Match all uses of a tool

To match all uses of a tool, use just the tool name without parentheses:

| Rule | Effect |
| --- | --- |
| `Bash` | Matches all Bash commands |
| `WebFetch` | Matches all web fetch requests |
| `Read` | Matches all file reads |

`Bash(*)` is equivalent to `Bash` and matches all Bash commands.

### [​](https://code.claude.com/docs/en/permissions\#use-specifiers-for-fine-grained-control)  Use specifiers for fine-grained control

Add a specifier in parentheses to match specific tool uses:

| Rule | Effect |
| --- | --- |
| `Bash(npm run build)` | Matches the exact command `npm run build` |
| `Read(./.env)` | Matches reading the `.env` file in the current directory |
| `WebFetch(domain:example.com)` | Matches fetch requests to example.com |

### [​](https://code.claude.com/docs/en/permissions\#wildcard-patterns)  Wildcard patterns

Bash rules support glob patterns with `*`. Wildcards can appear at any position in the command. This configuration allows npm and git commit commands while blocking git push:

Report incorrect code

Copy

Ask AI

```
{
  "permissions": {
    "allow": [\
      "Bash(npm run *)",\
      "Bash(git commit *)",\
      "Bash(git * main)",\
      "Bash(* --version)",\
      "Bash(* --help *)"\
    ],
    "deny": [\
      "Bash(git push *)"\
    ]
  }
}
```

The space before `*` matters: `Bash(ls *)` matches `ls -la` but not `lsof`, while `Bash(ls*)` matches both. The legacy `:*` suffix syntax is equivalent to ` *` but is deprecated.

## [​](https://code.claude.com/docs/en/permissions\#tool-specific-permission-rules)  Tool-specific permission rules

### [​](https://code.claude.com/docs/en/permissions\#bash)  Bash

Bash permission rules support wildcard matching with `*`. Wildcards can appear at any position in the command, including at the beginning, middle, or end:

- `Bash(npm run build)` matches the exact Bash command `npm run build`
- `Bash(npm run test *)` matches Bash commands starting with `npm run test`
- `Bash(npm *)` matches any command starting with `npm`
- `Bash(* install)` matches any command ending with ` install`
- `Bash(git * main)` matches commands like `git checkout main`, `git merge main`

When `*` appears at the end with a space before it (like `Bash(ls *)`), it enforces a word boundary, requiring the prefix to be followed by a space or end-of-string. For example, `Bash(ls *)` matches `ls -la` but not `lsof`. In contrast, `Bash(ls*)` without a space matches both `ls -la` and `lsof` because there’s no word boundary constraint.

Claude Code is aware of shell operators (like `&&`) so a prefix match rule like `Bash(safe-cmd *)` won’t give it permission to run the command `safe-cmd && other-cmd`.

When you approve a compound command with “Yes, don’t ask again”, Claude Code saves a separate rule for each subcommand that requires approval, rather than a single rule for the full compound string. For example, approving `git status && npm test` saves a rule for `npm test`, so future `npm test` invocations are recognized regardless of what precedes the `&&`. Subcommands like `cd` into a subdirectory generate their own Read rule for that path. Up to 5 rules may be saved for a single compound command.

Bash permission patterns that try to constrain command arguments are fragile. For example, `Bash(curl http://github.com/ *)` intends to restrict curl to GitHub URLs, but won’t match variations like:

- Options before URL: `curl -X GET http://github.com/...`
- Different protocol: `curl https://github.com/...`
- Redirects: `curl -L http://bit.ly/xyz` (redirects to github)
- Variables: `URL=http://github.com && curl $URL`
- Extra spaces: `curl  http://github.com`

For more reliable URL filtering, consider:

- **Restrict Bash network tools**: use deny rules to block `curl`, `wget`, and similar commands, then use the WebFetch tool with `WebFetch(domain:github.com)` permission for allowed domains
- **Use PreToolUse hooks**: implement a hook that validates URLs in Bash commands and blocks disallowed domains
- Instructing Claude Code about your allowed curl patterns via CLAUDE.md

Note that using WebFetch alone does not prevent network access. If Bash is allowed, Claude can still use `curl`, `wget`, or other tools to reach any URL.

### [​](https://code.claude.com/docs/en/permissions\#read-and-edit)  Read and Edit

`Edit` rules apply to all built-in tools that edit files. Claude makes a best-effort attempt to apply `Read` rules to all built-in tools that read files like Grep and Glob.

Read and Edit deny rules apply to Claude’s built-in file tools, not to Bash subprocesses. A `Read(./.env)` deny rule blocks the Read tool but does not prevent `cat .env` in Bash. For OS-level enforcement that blocks all processes from accessing a path, [enable the sandbox](https://code.claude.com/docs/en/sandboxing).

Read and Edit rules both follow the [gitignore](https://git-scm.com/docs/gitignore) specification with four distinct pattern types:

| Pattern | Meaning | Example | Matches |
| --- | --- | --- | --- |
| `//path` | **Absolute** path from filesystem root | `Read(//Users/alice/secrets/**)` | `/Users/alice/secrets/**` |
| `~/path` | Path from **home** directory | `Read(~/Documents/*.pdf)` | `/Users/alice/Documents/*.pdf` |
| `/path` | Path **relative to project root** | `Edit(/src/**/*.ts)` | `<project root>/src/**/*.ts` |
| `path` or `./path` | Path **relative to current directory** | `Read(*.env)` | `<cwd>/*.env` |

A pattern like `/Users/alice/file` is NOT an absolute path. It’s relative to the project root. Use `//Users/alice/file` for absolute paths.

On Windows, paths are normalized to POSIX form before matching. `C:\Users\alice` becomes `/c/Users/alice`, so use `//c/**/.env` to match `.env` files anywhere on that drive. To match across all drives, use `//**/.env`.Examples:

- `Edit(/docs/**)`: edits in `<project>/docs/` (NOT `/docs/` and NOT `<project>/.claude/docs/`)
- `Read(~/.zshrc)`: reads your home directory’s `.zshrc`
- `Edit(//tmp/scratch.txt)`: edits the absolute path `/tmp/scratch.txt`
- `Read(src/**)`: reads from `<current-directory>/src/`

In gitignore patterns, `*` matches files in a single directory while `**` matches recursively across directories. To allow all file access, use just the tool name without parentheses: `Read`, `Edit`, or `Write`.

### [​](https://code.claude.com/docs/en/permissions\#webfetch)  WebFetch

- `WebFetch(domain:example.com)` matches fetch requests to example.com

### [​](https://code.claude.com/docs/en/permissions\#mcp)  MCP

- `mcp__puppeteer` matches any tool provided by the `puppeteer` server (name configured in Claude Code)
- `mcp__puppeteer__*` wildcard syntax that also matches all tools from the `puppeteer` server
- `mcp__puppeteer__puppeteer_navigate` matches the `puppeteer_navigate` tool provided by the `puppeteer` server

### [​](https://code.claude.com/docs/en/permissions\#agent-subagents)  Agent (subagents)

Use `Agent(AgentName)` rules to control which [subagents](https://code.claude.com/docs/en/sub-agents) Claude can use:

- `Agent(Explore)` matches the Explore subagent
- `Agent(Plan)` matches the Plan subagent
- `Agent(my-custom-agent)` matches a custom subagent named `my-custom-agent`

Add these rules to the `deny` array in your settings or use the `--disallowedTools` CLI flag to disable specific agents. To disable the Explore agent:

Report incorrect code

Copy

Ask AI

```
{
  "permissions": {
    "deny": ["Agent(Explore)"]
  }
}
```

## [​](https://code.claude.com/docs/en/permissions\#extend-permissions-with-hooks)  Extend permissions with hooks

[Claude Code hooks](https://code.claude.com/docs/en/hooks-guide) provide a way to register custom shell commands to perform permission evaluation at runtime. When Claude Code makes a tool call, PreToolUse hooks run before the permission prompt. The hook output can deny the tool call, force a prompt, or skip the prompt to let the call proceed.Skipping the prompt does not bypass permission rules. Deny and ask rules are still evaluated after a hook returns `"allow"`, so a matching deny rule still blocks the call. This preserves the deny-first precedence described in [Manage permissions](https://code.claude.com/docs/en/permissions#manage-permissions), including deny rules set in managed settings.A blocking hook also takes precedence over allow rules. A hook that exits with code 2 stops the tool call before permission rules are evaluated, so the block applies even when an allow rule would otherwise let the call proceed. To run all Bash commands without prompts except for a few you want blocked, add `"Bash"` to your allow list and register a PreToolUse hook that rejects those specific commands. See [Block edits to protected files](https://code.claude.com/docs/en/hooks-guide#block-edits-to-protected-files) for a hook script you can adapt.

## [​](https://code.claude.com/docs/en/permissions\#working-directories)  Working directories

By default, Claude has access to files in the directory where it was launched. You can extend this access:

- **During startup**: use `--add-dir <path>` CLI argument
- **During session**: use `/add-dir` command
- **Persistent configuration**: add to `additionalDirectories` in [settings files](https://code.claude.com/docs/en/settings#settings-files)

Files in additional directories follow the same permission rules as the original working directory: they become readable without prompts, and file editing permissions follow the current permission mode.

## [​](https://code.claude.com/docs/en/permissions\#how-permissions-interact-with-sandboxing)  How permissions interact with sandboxing

Permissions and [sandboxing](https://code.claude.com/docs/en/sandboxing) are complementary security layers:

- **Permissions** control which tools Claude Code can use and which files or domains it can access. They apply to all tools (Bash, Read, Edit, WebFetch, MCP, and others).
- **Sandboxing** provides OS-level enforcement that restricts the Bash tool’s filesystem and network access. It applies only to Bash commands and their child processes.

Use both for defense-in-depth:

- Permission deny rules block Claude from even attempting to access restricted resources
- Sandbox restrictions prevent Bash commands from reaching resources outside defined boundaries, even if a prompt injection bypasses Claude’s decision-making
- Filesystem restrictions in the sandbox use Read and Edit deny rules, not separate sandbox configuration
- Network restrictions combine WebFetch permission rules with the sandbox’s `allowedDomains` list

## [​](https://code.claude.com/docs/en/permissions\#managed-settings)  Managed settings

For organizations that need centralized control over Claude Code configuration, administrators can deploy managed settings that cannot be overridden by user or project settings. These policy settings follow the same format as regular settings files and can be delivered through MDM/OS-level policies, managed settings files, or [server-managed settings](https://code.claude.com/docs/en/server-managed-settings). See [settings files](https://code.claude.com/docs/en/settings#settings-files) for delivery mechanisms and file locations.

### [​](https://code.claude.com/docs/en/permissions\#managed-only-settings)  Managed-only settings

Some settings are only effective in managed settings:

| Setting | Description |
| --- | --- |
| `allowManagedPermissionRulesOnly` | When `true`, prevents user and project settings from defining `allow`, `ask`, or `deny` permission rules. Only rules in managed settings apply |
| `allowManagedHooksOnly` | When `true`, prevents loading of user, project, and plugin hooks. Only managed hooks and SDK hooks are allowed |
| `allowManagedMcpServersOnly` | When `true`, only `allowedMcpServers` from managed settings are respected. `deniedMcpServers` still merges from all sources. See [Managed MCP configuration](https://code.claude.com/docs/en/mcp#managed-mcp-configuration) |
| `allowedChannelPlugins` | Allowlist of channel plugins that may push messages. Replaces the default Anthropic allowlist when set. Requires `channelsEnabled: true`. See [Restrict which channel plugins can run](https://code.claude.com/docs/en/channels#restrict-which-channel-plugins-can-run) |
| `blockedMarketplaces` | Blocklist of marketplace sources. Blocked sources are checked before downloading, so they never touch the filesystem. See [managed marketplace restrictions](https://code.claude.com/docs/en/plugin-marketplaces#managed-marketplace-restrictions) |
| `sandbox.network.allowManagedDomainsOnly` | When `true`, only `allowedDomains` and `WebFetch(domain:...)` allow rules from managed settings are respected. Non-allowed domains are blocked automatically without prompting the user. Denied domains still merge from all sources |
| `sandbox.filesystem.allowManagedReadPathsOnly` | When `true`, only `allowRead` paths from managed settings are respected. `allowRead` entries from user, project, and local settings are ignored |
| `strictKnownMarketplaces` | Controls which plugin marketplaces users can add. See [managed marketplace restrictions](https://code.claude.com/docs/en/plugin-marketplaces#managed-marketplace-restrictions) |

Access to [Remote Control](https://code.claude.com/docs/en/remote-control) and [web sessions](https://code.claude.com/docs/en/claude-code-on-the-web) is not controlled by a managed settings key. On Team and Enterprise plans, an admin enables or disables these features in [Claude Code admin settings](https://claude.ai/admin-settings/claude-code).

## [​](https://code.claude.com/docs/en/permissions\#configure-the-auto-mode-classifier)  Configure the auto mode classifier

[Auto mode](https://code.claude.com/docs/en/permission-modes#eliminate-prompts-with-auto-mode) uses a classifier model to decide whether each action is safe to run without prompting. Out of the box it trusts only the working directory and, if present, the current repo’s remotes. Actions like pushing to your company’s source control org or writing to a team cloud bucket will be blocked as potential data exfiltration. The `autoMode` settings block lets you tell the classifier which infrastructure your organization trusts.The classifier reads `autoMode` from user settings, `.claude/settings.local.json`, and managed settings. It does not read from shared project settings in `.claude/settings.json`, because a checked-in repo could otherwise inject its own allow rules.

| Scope | File | Use for |
| --- | --- | --- |
| One developer | `~/.claude/settings.json` | Personal trusted infrastructure |
| One project, one developer | `.claude/settings.local.json` | Per-project trusted buckets or services, gitignored |
| Organization-wide | Managed settings | Trusted infrastructure enforced for all developers |

Entries from each scope are combined. A developer can extend `environment`, `allow`, and `soft_deny` with personal entries but cannot remove entries that managed settings provide. Because allow rules act as exceptions to block rules inside the classifier, a developer-added `allow` entry can override an organization `soft_deny` entry: the combination is additive, not a hard policy boundary. If you need a rule that developers cannot work around, use `permissions.deny` in managed settings instead, which blocks actions before the classifier is consulted.

### [​](https://code.claude.com/docs/en/permissions\#define-trusted-infrastructure)  Define trusted infrastructure

For most organizations, `autoMode.environment` is the only field you need to set. It tells the classifier which repos, buckets, and domains are trusted, without touching the built-in block and allow rules. The classifier uses `environment` to decide what “external” means: any destination not listed is a potential exfiltration target.

Report incorrect code

Copy

Ask AI

```
{
  "autoMode": {
    "environment": [\
      "Source control: github.example.com/acme-corp and all repos under it",\
      "Trusted cloud buckets: s3://acme-build-artifacts, gs://acme-ml-datasets",\
      "Trusted internal domains: *.corp.example.com, api.internal.example.com",\
      "Key internal services: Jenkins at ci.example.com, Artifactory at artifacts.example.com"\
    ]
  }
}
```

Entries are prose, not regex or tool patterns. The classifier reads them as natural-language rules. Write them the way you would describe your infrastructure to a new engineer. A thorough environment section covers:

- **Organization**: your company name and what Claude Code is primarily used for, like software development, infrastructure automation, or data engineering
- **Source control**: every GitHub, GitLab, or Bitbucket org your developers push to
- **Cloud providers and trusted buckets**: bucket names or prefixes that Claude should be able to read from and write to
- **Trusted internal domains**: hostnames for APIs, dashboards, and services inside your network, like `*.internal.example.com`
- **Key internal services**: CI, artifact registries, internal package indexes, incident tooling
- **Additional context**: regulated-industry constraints, multi-tenant infrastructure, or compliance requirements that affect what the classifier should treat as risky

A useful starting template: fill in the bracketed fields and remove any lines that don’t apply:

Report incorrect code

Copy

Ask AI

```
{
  "autoMode": {
    "environment": [\
      "Organization: {COMPANY_NAME}. Primary use: {PRIMARY_USE_CASE, e.g. software development, infrastructure automation}",\
      "Source control: {SOURCE_CONTROL, e.g. GitHub org github.example.com/acme-corp}",\
      "Cloud provider(s): {CLOUD_PROVIDERS, e.g. AWS, GCP, Azure}",\
      "Trusted cloud buckets: {TRUSTED_BUCKETS, e.g. s3://acme-builds, gs://acme-datasets}",\
      "Trusted internal domains: {TRUSTED_DOMAINS, e.g. *.internal.example.com, api.example.com}",\
      "Key internal services: {SERVICES, e.g. Jenkins at ci.example.com, Artifactory at artifacts.example.com}",\
      "Additional context: {EXTRA, e.g. regulated industry, multi-tenant infrastructure, compliance requirements}"\
    ]
  }
}
```

The more specific context you give, the better the classifier can distinguish routine internal operations from exfiltration attempts.You don’t need to fill everything in at once. A reasonable rollout: start with the defaults and add your source control org and key internal services, which resolves the most common false positives like pushing to your own repos. Add trusted domains and cloud buckets next. Fill the rest as blocks come up.

### [​](https://code.claude.com/docs/en/permissions\#override-the-block-and-allow-rules)  Override the block and allow rules

Two additional fields let you replace the classifier’s built-in rule lists: `autoMode.soft_deny` controls what gets blocked, and `autoMode.allow` controls which exceptions apply. Each is an array of prose descriptions, read as natural-language rules.Inside the classifier, the precedence is: `soft_deny` rules block first, then `allow` rules override as exceptions, then explicit user intent overrides both. If the user’s message directly and specifically describes the exact action Claude is about to take, the classifier allows it even if a `soft_deny` rule matches. General requests don’t count: asking Claude to “clean up the repo” does not authorize force-pushing, but asking Claude to “force-push this branch” does.To loosen: remove rules from `soft_deny` when the defaults block something your pipeline already guards against with PR review, CI, or staging environments, or add to `allow` when the classifier repeatedly flags a routine pattern the default exceptions don’t cover. To tighten: add to `soft_deny` for risks specific to your environment that the defaults miss, or remove from `allow` to hold a default exception to the block rules. In all cases, run `claude auto-mode defaults` to get the full default lists, then copy and edit: never start from an empty list.

Report incorrect code

Copy

Ask AI

```
{
  "autoMode": {
    "environment": [\
      "Source control: github.example.com/acme-corp and all repos under it"\
    ],
    "allow": [\
      "Deploying to the staging namespace is allowed: staging is isolated from production and resets nightly",\
      "Writing to s3://acme-scratch/ is allowed: ephemeral bucket with a 7-day lifecycle policy"\
    ],
    "soft_deny": [\
      "Never run database migrations outside the migrations CLI, even against dev databases",\
      "Never modify files under infra/terraform/prod/: production infrastructure changes go through the review workflow",\
      "...copy full default soft_deny list here first, then add your rules..."\
    ]
  }
}
```

Setting `allow` or `soft_deny` replaces the entire default list for that section. If you set `soft_deny` with a single entry, every built-in block rule is discarded: force push, data exfiltration, `curl | bash`, production deploys, and all other default block rules become allowed. To customize safely, run `claude auto-mode defaults` to print the built-in rules, copy them into your settings file, then review each rule against your own pipeline and risk tolerance. Only remove rules for risks your infrastructure already mitigates.

The three sections are evaluated independently, so setting `environment` alone leaves the default `allow` and `soft_deny` lists intact.

### [​](https://code.claude.com/docs/en/permissions\#inspect-the-defaults-and-your-effective-config)  Inspect the defaults and your effective config

Because setting `allow` or `soft_deny` replaces the defaults, start any customization by copying the full default lists. Three CLI subcommands help you inspect and validate:

Report incorrect code

Copy

Ask AI

```
claude auto-mode defaults  # the built-in environment, allow, and soft_deny rules
claude auto-mode config    # what the classifier actually uses: your settings where set, defaults otherwise
claude auto-mode critique  # get AI feedback on your custom allow and soft_deny rules
```

Save the output of `claude auto-mode defaults` to a file, edit the lists to match your policy, and paste the result into your settings file. After saving, run `claude auto-mode config` to confirm the effective rules are what you expect. If you’ve written custom rules, `claude auto-mode critique` reviews them and flags entries that are ambiguous, redundant, or likely to cause false positives.

## [​](https://code.claude.com/docs/en/permissions\#settings-precedence)  Settings precedence

Permission rules follow the same [settings precedence](https://code.claude.com/docs/en/settings#settings-precedence) as all other Claude Code settings:

1. **Managed settings**: cannot be overridden by any other level, including command line arguments
2. **Command line arguments**: temporary session overrides
3. **Local project settings** (`.claude/settings.local.json`)
4. **Shared project settings** (`.claude/settings.json`)
5. **User settings** (`~/.claude/settings.json`)

If a tool is denied at any level, no other level can allow it. For example, a managed settings deny cannot be overridden by `--allowedTools`, and `--disallowedTools` can add restrictions beyond what managed settings define.If a permission is allowed in user settings but denied in project settings, the project setting takes precedence and the permission is blocked.

## [​](https://code.claude.com/docs/en/permissions\#example-configurations)  Example configurations

This [repository](https://github.com/anthropics/claude-code/tree/main/examples/settings) includes starter settings configurations for common deployment scenarios. Use these as starting points and adjust them to fit your needs.

## [​](https://code.claude.com/docs/en/permissions\#see-also)  See also

- [Settings](https://code.claude.com/docs/en/settings): complete configuration reference including the permission settings table
- [Sandboxing](https://code.claude.com/docs/en/sandboxing): OS-level filesystem and network isolation for Bash commands
- [Authentication](https://code.claude.com/docs/en/authentication): set up user access to Claude Code
- [Security](https://code.claude.com/docs/en/security): security safeguards and best practices
- [Hooks](https://code.claude.com/docs/en/hooks-guide): automate workflows and extend permission evaluation

Was this page helpful?

YesNo

[Settings](https://code.claude.com/docs/en/settings) [Sandboxing](https://code.claude.com/docs/en/sandboxing)

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

[Privacy choices](https://code.claude.com/docs/en/permissions#) [Privacy policy](https://www.anthropic.com/legal/privacy) [Disclosure policy](https://www.anthropic.com/responsible-disclosure-policy) [Usage policy](https://www.anthropic.com/legal/aup) [Commercial terms](https://www.anthropic.com/legal/commercial-terms) [Consumer terms](https://www.anthropic.com/legal/consumer-terms)

Assistant

Responses are generated using AI and may contain mistakes.