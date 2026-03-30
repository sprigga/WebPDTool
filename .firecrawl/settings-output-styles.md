[Skip to main content](https://code.claude.com/docs/en/output-styles#content-area)

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

Output styles

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

- [Built-in output styles](https://code.claude.com/docs/en/output-styles#built-in-output-styles)
- [How output styles work](https://code.claude.com/docs/en/output-styles#how-output-styles-work)
- [Change your output style](https://code.claude.com/docs/en/output-styles#change-your-output-style)
- [Create a custom output style](https://code.claude.com/docs/en/output-styles#create-a-custom-output-style)
- [Frontmatter](https://code.claude.com/docs/en/output-styles#frontmatter)
- [Comparisons to related features](https://code.claude.com/docs/en/output-styles#comparisons-to-related-features)
- [Output Styles vs. CLAUDE.md vs. —append-system-prompt](https://code.claude.com/docs/en/output-styles#output-styles-vs-claude-md-vs-%E2%80%94append-system-prompt)
- [Output Styles vs. Agents](https://code.claude.com/docs/en/output-styles#output-styles-vs-agents)
- [Output Styles vs. Skills](https://code.claude.com/docs/en/output-styles#output-styles-vs-skills)

Configuration

# Output styles

Copy page

Adapt Claude Code for uses beyond software engineering

Copy page

Output styles allow you to use Claude Code as any type of agent while keeping
its core capabilities, such as running local scripts, reading/writing files, and
tracking TODOs.

## [​](https://code.claude.com/docs/en/output-styles\#built-in-output-styles)  Built-in output styles

Claude Code’s **Default** output style is the existing system prompt, designed
to help you complete software engineering tasks efficiently.There are two additional built-in output styles focused on teaching you the
codebase and how Claude operates:

- **Explanatory**: Provides educational “Insights” in between helping you
complete software engineering tasks. Helps you understand implementation
choices and codebase patterns.
- **Learning**: Collaborative, learn-by-doing mode where Claude will not only
share “Insights” while coding, but also ask you to contribute small, strategic
pieces of code yourself. Claude Code will add `TODO(human)` markers in your
code for you to implement.

## [​](https://code.claude.com/docs/en/output-styles\#how-output-styles-work)  How output styles work

Output styles directly modify Claude Code’s system prompt.

- All output styles exclude instructions for efficient output (such as
responding concisely).
- Custom output styles exclude instructions for coding (such as verifying code
with tests), unless `keep-coding-instructions` is true.
- All output styles have their own custom instructions added to the end of the
system prompt.
- All output styles trigger reminders for Claude to adhere to the output style
instructions during the conversation.

## [​](https://code.claude.com/docs/en/output-styles\#change-your-output-style)  Change your output style

Run `/config` and select **Output style** to pick a style from a menu. Your
selection is saved to `.claude/settings.local.json` at the
[local project level](https://code.claude.com/docs/en/settings).To set a style without the menu, edit the `outputStyle` field directly in a
settings file:

```
{
  "outputStyle": "Explanatory"
}
```

Because the output style is set in the system prompt at session start,
changes take effect the next time you start a new session. This keeps the system
prompt stable throughout a conversation so prompt caching can reduce latency and
cost.

## [​](https://code.claude.com/docs/en/output-styles\#create-a-custom-output-style)  Create a custom output style

Custom output styles are Markdown files with frontmatter and the text that will
be added to the system prompt:

```
---
name: My Custom Style
description:
  A brief description of what this style does, to be displayed to the user
---

# Custom Style Instructions

You are an interactive CLI tool that helps users with software engineering
tasks. [Your custom instructions here...]

## Specific Behaviors

[Define how the assistant should behave in this style...]
```

You can save these files at the user level (`~/.claude/output-styles`) or
project level (`.claude/output-styles`).

### [​](https://code.claude.com/docs/en/output-styles\#frontmatter)  Frontmatter

Output style files support frontmatter for specifying metadata:

| Frontmatter | Purpose | Default |
| --- | --- | --- |
| `name` | Name of the output style, if not the file name | Inherits from file name |
| `description` | Description of the output style, shown in the `/config` picker | None |
| `keep-coding-instructions` | Whether to keep the parts of Claude Code’s system prompt related to coding. | false |

## [​](https://code.claude.com/docs/en/output-styles\#comparisons-to-related-features)  Comparisons to related features

### [​](https://code.claude.com/docs/en/output-styles\#output-styles-vs-claude-md-vs-%E2%80%94append-system-prompt)  Output Styles vs. CLAUDE.md vs. —append-system-prompt

Output styles completely “turn off” the parts of Claude Code’s default system
prompt specific to software engineering. Neither CLAUDE.md nor
`--append-system-prompt` edit Claude Code’s default system prompt. CLAUDE.md
adds the contents as a user message _following_ Claude Code’s default system
prompt. `--append-system-prompt` appends the content to the system prompt.

### [​](https://code.claude.com/docs/en/output-styles\#output-styles-vs-agents)  Output Styles vs. [Agents](https://code.claude.com/docs/en/sub-agents)

Output styles directly affect the main agent loop and only affect the system
prompt. Agents are invoked to handle specific tasks and can include additional
settings like the model to use, the tools they have available, and some context
about when to use the agent.

### [​](https://code.claude.com/docs/en/output-styles\#output-styles-vs-skills)  Output Styles vs. [Skills](https://code.claude.com/docs/en/skills)

Output styles modify how Claude responds (formatting, tone, structure) and are always active once selected. Skills are task-specific prompts that you invoke with `/skill-name` or that Claude loads automatically when relevant. Use output styles for consistent formatting preferences; use skills for reusable workflows and tasks.

Was this page helpful?

YesNo

[Voice dictation](https://code.claude.com/docs/en/voice-dictation) [Customize status line](https://code.claude.com/docs/en/statusline)

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

[Privacy choices](https://code.claude.com/docs/en/output-styles#) [Privacy policy](https://www.anthropic.com/legal/privacy) [Disclosure policy](https://www.anthropic.com/responsible-disclosure-policy) [Usage policy](https://www.anthropic.com/legal/aup) [Commercial terms](https://www.anthropic.com/legal/commercial-terms) [Consumer terms](https://www.anthropic.com/legal/consumer-terms)

Assistant

Responses are generated using AI and may contain mistakes.