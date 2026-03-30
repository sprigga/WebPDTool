[Skip to main content](https://code.claude.com/docs/en/sandboxing#content-area)

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

Sandboxing

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

- [Overview](https://code.claude.com/docs/en/sandboxing#overview)
- [Why sandboxing matters](https://code.claude.com/docs/en/sandboxing#why-sandboxing-matters)
- [How it works](https://code.claude.com/docs/en/sandboxing#how-it-works)
- [Filesystem isolation](https://code.claude.com/docs/en/sandboxing#filesystem-isolation)
- [Network isolation](https://code.claude.com/docs/en/sandboxing#network-isolation)
- [OS-level enforcement](https://code.claude.com/docs/en/sandboxing#os-level-enforcement)
- [Getting started](https://code.claude.com/docs/en/sandboxing#getting-started)
- [Prerequisites](https://code.claude.com/docs/en/sandboxing#prerequisites)
- [Enable sandboxing](https://code.claude.com/docs/en/sandboxing#enable-sandboxing)
- [Sandbox modes](https://code.claude.com/docs/en/sandboxing#sandbox-modes)
- [Configure sandboxing](https://code.claude.com/docs/en/sandboxing#configure-sandboxing)
- [Granting subprocess write access to specific paths](https://code.claude.com/docs/en/sandboxing#granting-subprocess-write-access-to-specific-paths)
- [Security benefits](https://code.claude.com/docs/en/sandboxing#security-benefits)
- [Protection against prompt injection](https://code.claude.com/docs/en/sandboxing#protection-against-prompt-injection)
- [Reduced attack surface](https://code.claude.com/docs/en/sandboxing#reduced-attack-surface)
- [Transparent operation](https://code.claude.com/docs/en/sandboxing#transparent-operation)
- [Security Limitations](https://code.claude.com/docs/en/sandboxing#security-limitations)
- [How sandboxing relates to permissions](https://code.claude.com/docs/en/sandboxing#how-sandboxing-relates-to-permissions)
- [Advanced usage](https://code.claude.com/docs/en/sandboxing#advanced-usage)
- [Custom proxy configuration](https://code.claude.com/docs/en/sandboxing#custom-proxy-configuration)
- [Integration with existing security tools](https://code.claude.com/docs/en/sandboxing#integration-with-existing-security-tools)
- [Best practices](https://code.claude.com/docs/en/sandboxing#best-practices)
- [Open source](https://code.claude.com/docs/en/sandboxing#open-source)
- [Limitations](https://code.claude.com/docs/en/sandboxing#limitations)
- [What sandboxing does not cover](https://code.claude.com/docs/en/sandboxing#what-sandboxing-does-not-cover)
- [See also](https://code.claude.com/docs/en/sandboxing#see-also)

Configuration

# Sandboxing

Copy page

Learn how Claude Code’s sandboxed bash tool provides filesystem and network isolation for safer, more autonomous agent execution.

Copy page

## [​](https://code.claude.com/docs/en/sandboxing\#overview)  Overview

Claude Code features native sandboxing to provide a more secure environment for agent execution while reducing the need for constant permission prompts. Instead of asking permission for each bash command, sandboxing creates defined boundaries upfront where Claude Code can work more freely with reduced risk.The sandboxed bash tool uses OS-level primitives to enforce both filesystem and network isolation.

## [​](https://code.claude.com/docs/en/sandboxing\#why-sandboxing-matters)  Why sandboxing matters

Traditional permission-based security requires constant user approval for bash commands. While this provides control, it can lead to:

- **Approval fatigue**: Repeatedly clicking “approve” can cause users to pay less attention to what they’re approving
- **Reduced productivity**: Constant interruptions slow down development workflows
- **Limited autonomy**: Claude Code cannot work as efficiently when waiting for approvals

Sandboxing addresses these challenges by:

1. **Defining clear boundaries**: Specify exactly which directories and network hosts Claude Code can access
2. **Reducing permission prompts**: Safe commands within the sandbox don’t require approval
3. **Maintaining security**: Attempts to access resources outside the sandbox trigger immediate notifications
4. **Enabling autonomy**: Claude Code can run more independently within defined limits

Effective sandboxing requires **both** filesystem and network isolation. Without network isolation, a compromised agent could exfiltrate sensitive files like SSH keys. Without filesystem isolation, a compromised agent could backdoor system resources to gain network access. When configuring sandboxing it is important to ensure that your configured settings do not create bypasses in these systems.

## [​](https://code.claude.com/docs/en/sandboxing\#how-it-works)  How it works

### [​](https://code.claude.com/docs/en/sandboxing\#filesystem-isolation)  Filesystem isolation

The sandboxed bash tool restricts file system access to specific directories:

- **Default writes behavior**: Read and write access to the current working directory and its subdirectories
- **Default read behavior**: Read access to the entire computer, except certain denied directories
- **Blocked access**: Cannot modify files outside the current working directory without explicit permission
- **Configurable**: Define custom allowed and denied paths through settings

You can grant write access to additional paths using `sandbox.filesystem.allowWrite` in your settings. These restrictions are enforced at the OS level (Seatbelt on macOS, bubblewrap on Linux), so they apply to all subprocess commands, including tools like `kubectl`, `terraform`, and `npm`, not just Claude’s file tools.

### [​](https://code.claude.com/docs/en/sandboxing\#network-isolation)  Network isolation

Network access is controlled through a proxy server running outside the sandbox:

- **Domain restrictions**: Only approved domains can be accessed
- **User confirmation**: New domain requests trigger permission prompts (unless [`allowManagedDomainsOnly`](https://code.claude.com/docs/en/settings#sandbox-settings) is enabled, which blocks non-allowed domains automatically)
- **Custom proxy support**: Advanced users can implement custom rules on outgoing traffic
- **Comprehensive coverage**: Restrictions apply to all scripts, programs, and subprocesses spawned by commands

### [​](https://code.claude.com/docs/en/sandboxing\#os-level-enforcement)  OS-level enforcement

The sandboxed bash tool leverages operating system security primitives:

- **macOS**: Uses Seatbelt for sandbox enforcement
- **Linux**: Uses [bubblewrap](https://github.com/containers/bubblewrap) for isolation
- **WSL2**: Uses bubblewrap, same as Linux

WSL1 is not supported because bubblewrap requires kernel features only available in WSL2.These OS-level restrictions ensure that all child processes spawned by Claude Code’s commands inherit the same security boundaries.

## [​](https://code.claude.com/docs/en/sandboxing\#getting-started)  Getting started

### [​](https://code.claude.com/docs/en/sandboxing\#prerequisites)  Prerequisites

On **macOS**, sandboxing works out of the box using the built-in Seatbelt framework.On **Linux and WSL2**, install the required packages first:

- Ubuntu/Debian

- Fedora


Report incorrect code

Copy

Ask AI

```
sudo apt-get install bubblewrap socat
```

Report incorrect code

Copy

Ask AI

```
sudo dnf install bubblewrap socat
```

### [​](https://code.claude.com/docs/en/sandboxing\#enable-sandboxing)  Enable sandboxing

You can enable sandboxing by running the `/sandbox` command:

Report incorrect code

Copy

Ask AI

```
/sandbox
```

This opens a menu where you can choose between sandbox modes. If required dependencies are missing (such as `bubblewrap` or `socat` on Linux), the menu displays installation instructions for your platform.By default, if the sandbox cannot start (missing dependencies, unsupported platform, or platform restrictions), Claude Code shows a warning and runs commands without sandboxing. To make this a hard failure instead, set [`sandbox.failIfUnavailable`](https://code.claude.com/docs/en/settings#sandbox-settings) to `true`. This is intended for managed deployments that require sandboxing as a security gate.

### [​](https://code.claude.com/docs/en/sandboxing\#sandbox-modes)  Sandbox modes

Claude Code offers two sandbox modes:**Auto-allow mode**: Bash commands will attempt to run inside the sandbox and are automatically allowed without requiring permission. Commands that cannot be sandboxed (such as those needing network access to non-allowed hosts) fall back to the regular permission flow. Explicit ask/deny rules you’ve configured are always respected.**Regular permissions mode**: All bash commands go through the standard permission flow, even when sandboxed. This provides more control but requires more approvals.In both modes, the sandbox enforces the same filesystem and network restrictions. The difference is only in whether sandboxed commands are auto-approved or require explicit permission.

Auto-allow mode works independently of your permission mode setting. Even if you’re not in “accept edits” mode, sandboxed bash commands will run automatically when auto-allow is enabled. This means bash commands that modify files within the sandbox boundaries will execute without prompting, even when file edit tools would normally require approval.

### [​](https://code.claude.com/docs/en/sandboxing\#configure-sandboxing)  Configure sandboxing

Customize sandbox behavior through your `settings.json` file. See [Settings](https://code.claude.com/docs/en/settings#sandbox-settings) for complete configuration reference.

#### [​](https://code.claude.com/docs/en/sandboxing\#granting-subprocess-write-access-to-specific-paths)  Granting subprocess write access to specific paths

By default, sandboxed commands can only write to the current working directory. If subprocess commands like `kubectl`, `terraform`, or `npm` need to write outside the project directory, use `sandbox.filesystem.allowWrite` to grant access to specific paths:

Report incorrect code

Copy

Ask AI

```
{
  "sandbox": {
    "enabled": true,
    "filesystem": {
      "allowWrite": ["~/.kube", "/tmp/build"]
    }
  }
}
```

These paths are enforced at the OS level, so all commands running inside the sandbox, including their child processes, respect them. This is the recommended approach when a tool needs write access to a specific location, rather than excluding the tool from the sandbox entirely with `excludedCommands`.When `allowWrite` (or `denyWrite`/`denyRead`/`allowRead`) is defined in multiple [settings scopes](https://code.claude.com/docs/en/settings#settings-precedence), the arrays are **merged**, meaning paths from every scope are combined, not replaced. For example, if managed settings allow writes to `/opt/company-tools` and a user adds `~/.kube` in their personal settings, both paths are included in the final sandbox configuration. This means users and projects can extend the list without duplicating or overriding paths set by higher-priority scopes.Path prefixes control how paths are resolved:

| Prefix | Meaning | Example |
| --- | --- | --- |
| `/` | Absolute path from filesystem root | `/tmp/build` stays `/tmp/build` |
| `~/` | Relative to home directory | `~/.kube` becomes `$HOME/.kube` |
| `./` or no prefix | Relative to the project root for project settings, or to `~/.claude` for user settings | `./output` in `.claude/settings.json` resolves to `<project-root>/output` |

The older `//path` prefix for absolute paths still works. If you previously used single-slash `/path` expecting project-relative resolution, switch to `./path`. This syntax differs from [Read and Edit permission rules](https://code.claude.com/docs/en/permissions#read-and-edit), which use `//path` for absolute and `/path` for project-relative. Sandbox filesystem paths use standard conventions: `/tmp/build` is an absolute path.You can also deny write or read access using `sandbox.filesystem.denyWrite` and `sandbox.filesystem.denyRead`. These are merged with any paths from `Edit(...)` and `Read(...)` permission rules. To re-allow reading specific paths within a denied region, use `sandbox.filesystem.allowRead`, which takes precedence over `denyRead`. When `allowManagedReadPathsOnly` is enabled in managed settings, only managed `allowRead` entries are respected; user, project, and local `allowRead` entries are ignored.For example, to block reading from the entire home directory while still allowing reads from the current project, add this to your project’s `.claude/settings.json`:

Report incorrect code

Copy

Ask AI

```
{
  "sandbox": {
    "enabled": true,
    "filesystem": {
      "denyRead": ["~/"],
      "allowRead": ["."]
    }
  }
}
```

The `.` in `allowRead` resolves to the project root because this configuration lives in project settings. If you placed the same configuration in `~/.claude/settings.json`, `.` would resolve to `~/.claude` instead, and project files would remain blocked by the `denyRead` rule.

Not all commands are compatible with sandboxing out of the box. Some notes that may help you make the most out of the sandbox:

- Many CLI tools require accessing certain hosts. As you use these tools, they will request permission to access certain hosts. Granting permission will allow them to access these hosts now and in the future, enabling them to safely execute inside the sandbox.
- `watchman` is incompatible with running in the sandbox. If you’re running `jest`, consider using `jest --no-watchman`
- `docker` is incompatible with running in the sandbox. Consider specifying `docker` in `excludedCommands` to force it to run outside of the sandbox.

Claude Code includes an intentional escape hatch mechanism that allows commands to run outside the sandbox when necessary. When a command fails due to sandbox restrictions (such as network connectivity issues or incompatible tools), Claude is prompted to analyze the failure and may retry the command with the `dangerouslyDisableSandbox` parameter. Commands that use this parameter go through the normal Claude Code permissions flow requiring user permission to execute. This allows Claude Code to handle edge cases where certain tools or network operations cannot function within sandbox constraints.You can disable this escape hatch by setting `"allowUnsandboxedCommands": false` in your [sandbox settings](https://code.claude.com/docs/en/settings#sandbox-settings). When disabled, the `dangerouslyDisableSandbox` parameter is completely ignored and all commands must run sandboxed or be explicitly listed in `excludedCommands`.

## [​](https://code.claude.com/docs/en/sandboxing\#security-benefits)  Security benefits

### [​](https://code.claude.com/docs/en/sandboxing\#protection-against-prompt-injection)  Protection against prompt injection

Even if an attacker successfully manipulates Claude Code’s behavior through prompt injection, the sandbox ensures your system remains secure:**Filesystem protection:**

- Cannot modify critical config files such as `~/.bashrc`
- Cannot modify system-level files in `/bin/`
- Cannot read files that are denied in your [Claude permission settings](https://code.claude.com/docs/en/permissions#manage-permissions)

**Network protection:**

- Cannot exfiltrate data to attacker-controlled servers
- Cannot download malicious scripts from unauthorized domains
- Cannot make unexpected API calls to unapproved services
- Cannot contact any domains not explicitly allowed

**Monitoring and control:**

- All access attempts outside the sandbox are blocked at the OS level
- You receive immediate notifications when boundaries are tested
- You can choose to deny, allow once, or permanently update your configuration

### [​](https://code.claude.com/docs/en/sandboxing\#reduced-attack-surface)  Reduced attack surface

Sandboxing limits the potential damage from:

- **Malicious dependencies**: NPM packages or other dependencies with harmful code
- **Compromised scripts**: Build scripts or tools with security vulnerabilities
- **Social engineering**: Attacks that trick users into running dangerous commands
- **Prompt injection**: Attacks that trick Claude into running dangerous commands

### [​](https://code.claude.com/docs/en/sandboxing\#transparent-operation)  Transparent operation

When Claude Code attempts to access network resources outside the sandbox:

1. The operation is blocked at the OS level
2. You receive an immediate notification
3. You can choose to:
   - Deny the request
   - Allow it once
   - Update your sandbox configuration to permanently allow it

## [​](https://code.claude.com/docs/en/sandboxing\#security-limitations)  Security Limitations

- Network Sandboxing Limitations: The network filtering system operates by restricting the domains that processes are allowed to connect to. It does not otherwise inspect the traffic passing through the proxy and users are responsible for ensuring they only allow trusted domains in their policy.

Users should be aware of potential risks that come from allowing broad domains like `github.com` that may allow for data exfiltration. Also, in some cases it may be possible to bypass the network filtering through [domain fronting](https://en.wikipedia.org/wiki/Domain_fronting).

- Privilege Escalation via Unix Sockets: The `allowUnixSockets` configuration can inadvertently grant access to powerful system services that could lead to sandbox bypasses. For example, if it is used to allow access to `/var/run/docker.sock` this would effectively grant access to the host system through exploiting the docker socket. Users are encouraged to carefully consider any unix sockets that they allow through the sandbox.
- Filesystem Permission Escalation: Overly broad filesystem write permissions can enable privilege escalation attacks. Allowing writes to directories containing executables in `$PATH`, system configuration directories, or user shell configuration files (`.bashrc`, `.zshrc`) can lead to code execution in different security contexts when other users or system processes access these files.
- Linux Sandbox Strength: The Linux implementation provides strong filesystem and network isolation but includes an `enableWeakerNestedSandbox` mode that enables it to work inside of Docker environments without privileged namespaces. This option considerably weakens security and should only be used in cases where additional isolation is otherwise enforced.

## [​](https://code.claude.com/docs/en/sandboxing\#how-sandboxing-relates-to-permissions)  How sandboxing relates to permissions

Sandboxing and [permissions](https://code.claude.com/docs/en/permissions) are complementary security layers that work together:

- **Permissions** control which tools Claude Code can use and are evaluated before any tool runs. They apply to all tools: Bash, Read, Edit, WebFetch, MCP, and others.
- **Sandboxing** provides OS-level enforcement that restricts what Bash commands can access at the filesystem and network level. It applies only to Bash commands and their child processes.

Filesystem and network restrictions are configured through both sandbox settings and permission rules:

- Use `sandbox.filesystem.allowWrite` to grant subprocess write access to paths outside the working directory
- Use `sandbox.filesystem.denyWrite` and `sandbox.filesystem.denyRead` to block subprocess access to specific paths
- Use `sandbox.filesystem.allowRead` to re-allow reading specific paths within a `denyRead` region
- Use `Read` and `Edit` deny rules to block access to specific files or directories
- Use `WebFetch` allow/deny rules to control domain access
- Use sandbox `allowedDomains` to control which domains Bash commands can reach

Paths from both `sandbox.filesystem` settings and permission rules are merged together into the final sandbox configuration.This [repository](https://github.com/anthropics/claude-code/tree/main/examples/settings) includes starter settings configurations for common deployment scenarios, including sandbox-specific examples. Use these as starting points and adjust them to fit your needs.

## [​](https://code.claude.com/docs/en/sandboxing\#advanced-usage)  Advanced usage

### [​](https://code.claude.com/docs/en/sandboxing\#custom-proxy-configuration)  Custom proxy configuration

For organizations requiring advanced network security, you can implement a custom proxy to:

- Decrypt and inspect HTTPS traffic
- Apply custom filtering rules
- Log all network requests
- Integrate with existing security infrastructure

Report incorrect code

Copy

Ask AI

```
{
  "sandbox": {
    "network": {
      "httpProxyPort": 8080,
      "socksProxyPort": 8081
    }
  }
}
```

### [​](https://code.claude.com/docs/en/sandboxing\#integration-with-existing-security-tools)  Integration with existing security tools

The sandboxed bash tool works alongside:

- **Permission rules**: Combine with [permission settings](https://code.claude.com/docs/en/permissions) for defense-in-depth
- **Development containers**: Use with [devcontainers](https://code.claude.com/docs/en/devcontainer) for additional isolation
- **Enterprise policies**: Enforce sandbox configurations through [managed settings](https://code.claude.com/docs/en/settings#settings-precedence)

## [​](https://code.claude.com/docs/en/sandboxing\#best-practices)  Best practices

1. **Start restrictive**: Begin with minimal permissions and expand as needed
2. **Monitor logs**: Review sandbox violation attempts to understand Claude Code’s needs
3. **Use environment-specific configs**: Different sandbox rules for development vs. production contexts
4. **Combine with permissions**: Use sandboxing alongside IAM policies for comprehensive security
5. **Test configurations**: Verify your sandbox settings don’t block legitimate workflows

## [​](https://code.claude.com/docs/en/sandboxing\#open-source)  Open source

The sandbox runtime is available as an open source npm package for use in your own agent projects. This enables the broader AI agent community to build safer, more secure autonomous systems. This can also be used to sandbox other programs you may wish to run. For example, to sandbox an MCP server you could run:

Report incorrect code

Copy

Ask AI

```
npx @anthropic-ai/sandbox-runtime <command-to-sandbox>
```

For implementation details and source code, visit the [GitHub repository](https://github.com/anthropic-experimental/sandbox-runtime).

## [​](https://code.claude.com/docs/en/sandboxing\#limitations)  Limitations

- **Performance overhead**: Minimal, but some filesystem operations may be slightly slower
- **Compatibility**: Some tools that require specific system access patterns may need configuration adjustments, or may even need to be run outside of the sandbox
- **Platform support**: Supports macOS, Linux, and WSL2. WSL1 is not supported. Native Windows support is planned.

## [​](https://code.claude.com/docs/en/sandboxing\#what-sandboxing-does-not-cover)  What sandboxing does not cover

The sandbox isolates Bash subprocesses. Other tools operate under different boundaries:

- **Built-in file tools**: Read, Edit, and Write use the permission system directly rather than running through the sandbox. See [permissions](https://code.claude.com/docs/en/permissions).
- **Computer use on Desktop**: when Claude opens apps and controls your screen on macOS, it runs on your actual desktop rather than in an isolated environment. Per-app permission prompts gate each application. See [computer use](https://code.claude.com/docs/en/desktop#let-claude-use-your-computer).

## [​](https://code.claude.com/docs/en/sandboxing\#see-also)  See also

- [Security](https://code.claude.com/docs/en/security) \- Comprehensive security features and best practices
- [Permissions](https://code.claude.com/docs/en/permissions) \- Permission configuration and access control
- [Settings](https://code.claude.com/docs/en/settings) \- Complete configuration reference
- [CLI reference](https://code.claude.com/docs/en/cli-reference) \- Command-line options

Was this page helpful?

YesNo

[Permissions](https://code.claude.com/docs/en/permissions) [Terminal configuration](https://code.claude.com/docs/en/terminal-config)

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

[Privacy choices](https://code.claude.com/docs/en/sandboxing#) [Privacy policy](https://www.anthropic.com/legal/privacy) [Disclosure policy](https://www.anthropic.com/responsible-disclosure-policy) [Usage policy](https://www.anthropic.com/legal/aup) [Commercial terms](https://www.anthropic.com/legal/commercial-terms) [Consumer terms](https://www.anthropic.com/legal/consumer-terms)

Assistant

Responses are generated using AI and may contain mistakes.