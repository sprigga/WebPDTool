[Skip to main content](https://code.claude.com/docs/en/model-config#content-area)

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

Model configuration

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

- [Available models](https://code.claude.com/docs/en/model-config#available-models)
- [Model aliases](https://code.claude.com/docs/en/model-config#model-aliases)
- [Setting your model](https://code.claude.com/docs/en/model-config#setting-your-model)
- [Restrict model selection](https://code.claude.com/docs/en/model-config#restrict-model-selection)
- [Default model behavior](https://code.claude.com/docs/en/model-config#default-model-behavior)
- [Control the model users run on](https://code.claude.com/docs/en/model-config#control-the-model-users-run-on)
- [Merge behavior](https://code.claude.com/docs/en/model-config#merge-behavior)
- [Special model behavior](https://code.claude.com/docs/en/model-config#special-model-behavior)
- [default model setting](https://code.claude.com/docs/en/model-config#default-model-setting)
- [opusplan model setting](https://code.claude.com/docs/en/model-config#opusplan-model-setting)
- [Adjust effort level](https://code.claude.com/docs/en/model-config#adjust-effort-level)
- [Extended context](https://code.claude.com/docs/en/model-config#extended-context)
- [Checking your current model](https://code.claude.com/docs/en/model-config#checking-your-current-model)
- [Add a custom model option](https://code.claude.com/docs/en/model-config#add-a-custom-model-option)
- [Environment variables](https://code.claude.com/docs/en/model-config#environment-variables)
- [Pin models for third-party deployments](https://code.claude.com/docs/en/model-config#pin-models-for-third-party-deployments)
- [Customize pinned model display and capabilities](https://code.claude.com/docs/en/model-config#customize-pinned-model-display-and-capabilities)
- [Override model IDs per version](https://code.claude.com/docs/en/model-config#override-model-ids-per-version)
- [Prompt caching configuration](https://code.claude.com/docs/en/model-config#prompt-caching-configuration)

Configuration

# Model configuration

Copy page

Learn about the Claude Code model configuration, including model aliases like `opusplan`

Copy page

## [​](https://code.claude.com/docs/en/model-config\#available-models)  Available models

For the `model` setting in Claude Code, you can configure either:

- A **model alias**
- A **model name**
  - Anthropic API: A full **[model name](https://platform.claude.com/docs/en/about-claude/models/overview)**
  - Bedrock: an inference profile ARN
  - Foundry: a deployment name
  - Vertex: a version name

### [​](https://code.claude.com/docs/en/model-config\#model-aliases)  Model aliases

Model aliases provide a convenient way to select model settings without
remembering exact version numbers:

| Model alias | Behavior |
| --- | --- |
| **`default`** | Recommended model setting, depending on your account type |
| **`sonnet`** | Uses the latest Sonnet model (currently Sonnet 4.6) for daily coding tasks |
| **`opus`** | Uses the latest Opus model (currently Opus 4.6) for complex reasoning tasks |
| **`haiku`** | Uses the fast and efficient Haiku model for simple tasks |
| **`sonnet[1m]`** | Uses Sonnet with a [1 million token context window](https://platform.claude.com/docs/en/build-with-claude/context-windows#1m-token-context-window) for long sessions |
| **`opus[1m]`** | Uses Opus with a [1 million token context window](https://platform.claude.com/docs/en/build-with-claude/context-windows#1m-token-context-window) for long sessions |
| **`opusplan`** | Special mode that uses `opus` during plan mode, then switches to `sonnet` for execution |

Aliases always point to the latest version. To pin to a specific version, use the full model name (for example, `claude-opus-4-6`) or set the corresponding environment variable like `ANTHROPIC_DEFAULT_OPUS_MODEL`.

### [​](https://code.claude.com/docs/en/model-config\#setting-your-model)  Setting your model

You can configure your model in several ways, listed in order of priority:

1. **During session** \- Use `/model <alias|name>` to switch models mid-session
2. **At startup** \- Launch with `claude --model <alias|name>`
3. **Environment variable** \- Set `ANTHROPIC_MODEL=<alias|name>`
4. **Settings** \- Configure permanently in your settings file using the `model`
field.

Example usage:

Report incorrect code

Copy

Ask AI

```
# Start with Opus
claude --model opus

# Switch to Sonnet during session
/model sonnet
```

Example settings file:

Report incorrect code

Copy

Ask AI

```
{
    "permissions": {
        ...
    },
    "model": "opus"
}
```

## [​](https://code.claude.com/docs/en/model-config\#restrict-model-selection)  Restrict model selection

Enterprise administrators can use `availableModels` in [managed or policy settings](https://code.claude.com/docs/en/settings#settings-files) to restrict which models users can select.When `availableModels` is set, users cannot switch to models not in the list via `/model`, `--model` flag, Config tool, or `ANTHROPIC_MODEL` environment variable.

Report incorrect code

Copy

Ask AI

```
{
  "availableModels": ["sonnet", "haiku"]
}
```

### [​](https://code.claude.com/docs/en/model-config\#default-model-behavior)  Default model behavior

The Default option in the model picker is not affected by `availableModels`. It always remains available and represents the system’s runtime default [based on the user’s subscription tier](https://code.claude.com/docs/en/model-config#default-model-setting).Even with `availableModels: []`, users can still use Claude Code with the Default model for their tier.

### [​](https://code.claude.com/docs/en/model-config\#control-the-model-users-run-on)  Control the model users run on

To fully control the model experience, use `availableModels` together with the `model` setting:

- **availableModels**: restricts what users can switch to
- **model**: sets the explicit model override, taking precedence over the Default

This example ensures all users run Sonnet 4.6 and can only choose between Sonnet and Haiku:

Report incorrect code

Copy

Ask AI

```
{
  "model": "sonnet",
  "availableModels": ["sonnet", "haiku"]
}
```

### [​](https://code.claude.com/docs/en/model-config\#merge-behavior)  Merge behavior

When `availableModels` is set at multiple levels, such as user settings and project settings, arrays are merged and deduplicated. To enforce a strict allowlist, set `availableModels` in managed or policy settings which take highest priority.

## [​](https://code.claude.com/docs/en/model-config\#special-model-behavior)  Special model behavior

### [​](https://code.claude.com/docs/en/model-config\#default-model-setting)  `default` model setting

The behavior of `default` depends on your account type:

- **Max and Team Premium**: defaults to Opus 4.6
- **Pro and Team Standard**: defaults to Sonnet 4.6
- **Enterprise**: Opus 4.6 is available but not the default

Claude Code may automatically fall back to Sonnet if you hit a usage threshold with Opus.

### [​](https://code.claude.com/docs/en/model-config\#opusplan-model-setting)  `opusplan` model setting

The `opusplan` model alias provides an automated hybrid approach:

- **In plan mode** \- Uses `opus` for complex reasoning and architecture
decisions
- **In execution mode** \- Automatically switches to `sonnet` for code generation
and implementation

This gives you the best of both worlds: Opus’s superior reasoning for planning,
and Sonnet’s efficiency for execution.

### [​](https://code.claude.com/docs/en/model-config\#adjust-effort-level)  Adjust effort level

[Effort levels](https://platform.claude.com/docs/en/build-with-claude/effort) control adaptive reasoning, which dynamically allocates thinking based on task complexity. Lower effort is faster and cheaper for straightforward tasks, while higher effort provides deeper reasoning for complex problems.Three levels persist across sessions: **low**, **medium**, and **high**. A fourth level, **max**, provides the deepest reasoning with no constraint on token spending, so responses are slower and cost more than at `high`. `max` is available on Opus 4.6 only and does not persist across sessions except through the `CLAUDE_CODE_EFFORT_LEVEL` environment variable.Opus 4.6 and Sonnet 4.6 default to medium effort. This applies to all providers, including Bedrock, Vertex AI, and direct API access.Medium is the recommended level for most coding tasks: it balances speed and reasoning depth, and higher levels can cause the model to overthink routine work. Reserve `high` or `max` for tasks that genuinely benefit from deeper reasoning, such as hard debugging problems or complex architectural decisions.For one-off deep reasoning without changing your session setting, include “ultrathink” in your prompt to trigger high effort for that turn.**Setting effort:**

- **`/effort`**: run `/effort low`, `/effort medium`, `/effort high`, or `/effort max` to change the level, or `/effort auto` to reset to the model default
- **In `/model`**: use left/right arrow keys to adjust the effort slider when selecting a model
- **`--effort` flag**: pass `low`, `medium`, `high`, or `max` to set the level for a single session when launching Claude Code
- **Environment variable**: set `CLAUDE_CODE_EFFORT_LEVEL` to `low`, `medium`, `high`, `max`, or `auto`
- **Settings**: set `effortLevel` in your settings file to `"low"`, `"medium"`, or `"high"`
- **Skill and subagent frontmatter**: set `effort` in a [skill](https://code.claude.com/docs/en/skills#frontmatter-reference) or [subagent](https://code.claude.com/docs/en/sub-agents#supported-frontmatter-fields) markdown file to override the effort level when that skill or subagent runs

The environment variable takes precedence over all other methods, then your configured level, then the model default. Frontmatter effort applies when that skill or subagent is active, overriding the session level but not the environment variable.Effort is supported on Opus 4.6 and Sonnet 4.6. The effort slider appears in `/model` when a supported model is selected. The current effort level is also displayed next to the logo and spinner, for example “with low effort”, so you can confirm which setting is active without opening `/model`.To disable adaptive reasoning on Opus 4.6 and Sonnet 4.6 and revert to the previous fixed thinking budget, set `CLAUDE_CODE_DISABLE_ADAPTIVE_THINKING=1`. When disabled, these models use the fixed budget controlled by `MAX_THINKING_TOKENS`. See [environment variables](https://code.claude.com/docs/en/env-vars).

### [​](https://code.claude.com/docs/en/model-config\#extended-context)  Extended context

Opus 4.6 and Sonnet 4.6 support a [1 million token context window](https://platform.claude.com/docs/en/build-with-claude/context-windows#1m-token-context-window) for long sessions with large codebases.Availability varies by model and plan. On Max, Team, and Enterprise plans, Opus is automatically upgraded to 1M context with no additional configuration. This applies to both Team Standard and Team Premium seats.

| Plan | Opus 4.6 with 1M context | Sonnet 4.6 with 1M context |
| --- | --- | --- |
| Max, Team, and Enterprise | Included with subscription | Requires [extra usage](https://support.claude.com/en/articles/12429409-extra-usage-for-paid-claude-plans) |
| Pro | Requires [extra usage](https://support.claude.com/en/articles/12429409-extra-usage-for-paid-claude-plans) | Requires [extra usage](https://support.claude.com/en/articles/12429409-extra-usage-for-paid-claude-plans) |
| API and pay-as-you-go | Full access | Full access |

To disable 1M context entirely, set `CLAUDE_CODE_DISABLE_1M_CONTEXT=1`. This removes 1M model variants from the model picker. See [environment variables](https://code.claude.com/docs/en/env-vars).The 1M context window uses standard model pricing with no premium for tokens beyond 200K. For plans where extended context is included with your subscription, usage remains covered by your subscription. For plans that access extended context through extra usage, tokens are billed to extra usage.If your account supports 1M context, the option appears in the model picker (`/model`) in the latest versions of Claude Code. If you don’t see it, try restarting your session.You can also use the `[1m]` suffix with model aliases or full model names:

Report incorrect code

Copy

Ask AI

```
# Use the opus[1m] or sonnet[1m] alias
/model opus[1m]
/model sonnet[1m]

# Or append [1m] to a full model name
/model claude-opus-4-6[1m]
```

## [​](https://code.claude.com/docs/en/model-config\#checking-your-current-model)  Checking your current model

You can see which model you’re currently using in several ways:

1. In [status line](https://code.claude.com/docs/en/statusline) (if configured)
2. In `/status`, which also displays your account information.

## [​](https://code.claude.com/docs/en/model-config\#add-a-custom-model-option)  Add a custom model option

Use `ANTHROPIC_CUSTOM_MODEL_OPTION` to add a single custom entry to the `/model` picker without replacing the built-in aliases. This is useful for LLM gateway deployments or testing model IDs that Claude Code does not list by default.This example sets all three variables to make a gateway-routed Opus deployment selectable:

Report incorrect code

Copy

Ask AI

```
export ANTHROPIC_CUSTOM_MODEL_OPTION="my-gateway/claude-opus-4-6"
export ANTHROPIC_CUSTOM_MODEL_OPTION_NAME="Opus via Gateway"
export ANTHROPIC_CUSTOM_MODEL_OPTION_DESCRIPTION="Custom deployment routed through the internal LLM gateway"
```

The custom entry appears at the bottom of the `/model` picker. `ANTHROPIC_CUSTOM_MODEL_OPTION_NAME` and `ANTHROPIC_CUSTOM_MODEL_OPTION_DESCRIPTION` are optional. If omitted, the model ID is used as the name and the description defaults to `Custom model (<model-id>)`.Claude Code skips validation for the model ID set in `ANTHROPIC_CUSTOM_MODEL_OPTION`, so you can use any string your API endpoint accepts.

## [​](https://code.claude.com/docs/en/model-config\#environment-variables)  Environment variables

You can use the following environment variables, which must be full **model**
**names** (or equivalent for your API provider), to control the model names that the aliases map to.

| Environment variable | Description |
| --- | --- |
| `ANTHROPIC_DEFAULT_OPUS_MODEL` | The model to use for `opus`, or for `opusplan` when Plan Mode is active. |
| `ANTHROPIC_DEFAULT_SONNET_MODEL` | The model to use for `sonnet`, or for `opusplan` when Plan Mode is not active. |
| `ANTHROPIC_DEFAULT_HAIKU_MODEL` | The model to use for `haiku`, or [background functionality](https://code.claude.com/docs/en/costs#background-token-usage) |
| `CLAUDE_CODE_SUBAGENT_MODEL` | The model to use for [subagents](https://code.claude.com/docs/en/sub-agents) |

Note: `ANTHROPIC_SMALL_FAST_MODEL` is deprecated in favor of
`ANTHROPIC_DEFAULT_HAIKU_MODEL`.

### [​](https://code.claude.com/docs/en/model-config\#pin-models-for-third-party-deployments)  Pin models for third-party deployments

When deploying Claude Code through [Bedrock](https://code.claude.com/docs/en/amazon-bedrock), [Vertex AI](https://code.claude.com/docs/en/google-vertex-ai), or [Foundry](https://code.claude.com/docs/en/microsoft-foundry), pin model versions before rolling out to users.Without pinning, Claude Code uses model aliases (`sonnet`, `opus`, `haiku`) that resolve to the latest version. When Anthropic releases a new model, users whose accounts don’t have the new version enabled will break silently.

Set all three model environment variables to specific version IDs as part of your initial setup. Skipping this step means a Claude Code update can break your users without any action on your part.

Use the following environment variables with version-specific model IDs for your provider:

| Provider | Example |
| --- | --- |
| Bedrock | `export ANTHROPIC_DEFAULT_OPUS_MODEL='us.anthropic.claude-opus-4-6-v1'` |
| Vertex AI | `export ANTHROPIC_DEFAULT_OPUS_MODEL='claude-opus-4-6'` |
| Foundry | `export ANTHROPIC_DEFAULT_OPUS_MODEL='claude-opus-4-6'` |

Apply the same pattern for `ANTHROPIC_DEFAULT_SONNET_MODEL` and `ANTHROPIC_DEFAULT_HAIKU_MODEL`. For current and legacy model IDs across all providers, see [Models overview](https://platform.claude.com/docs/en/about-claude/models/overview). To upgrade users to a new model version, update these environment variables and redeploy.To enable [extended context](https://code.claude.com/docs/en/model-config#extended-context) for a pinned model, append `[1m]` to the model ID in `ANTHROPIC_DEFAULT_OPUS_MODEL` or `ANTHROPIC_DEFAULT_SONNET_MODEL`:

Report incorrect code

Copy

Ask AI

```
export ANTHROPIC_DEFAULT_OPUS_MODEL='claude-opus-4-6[1m]'
```

The `[1m]` suffix applies the 1M context window to all usage of that alias, including `opusplan`. Claude Code strips the suffix before sending the model ID to your provider. Only append `[1m]` when the underlying model supports 1M context, such as Opus 4.6 or Sonnet 4.6.

The `settings.availableModels` allowlist still applies when using third-party providers. Filtering matches on the model alias (`opus`, `sonnet`, `haiku`), not the provider-specific model ID.

### [​](https://code.claude.com/docs/en/model-config\#customize-pinned-model-display-and-capabilities)  Customize pinned model display and capabilities

When you pin a model on a third-party provider, the provider-specific ID appears as-is in the `/model` picker and Claude Code may not recognize which features the model supports. You can override the display name and declare capabilities with companion environment variables for each pinned model.These variables only take effect on third-party providers such as Bedrock, Vertex AI, and Foundry. They have no effect when using the Anthropic API directly.

| Environment variable | Description |
| --- | --- |
| `ANTHROPIC_DEFAULT_OPUS_MODEL_NAME` | Display name for the pinned Opus model in the `/model` picker. Defaults to the model ID when not set |
| `ANTHROPIC_DEFAULT_OPUS_MODEL_DESCRIPTION` | Display description for the pinned Opus model in the `/model` picker. Defaults to `Custom Opus model` when not set |
| `ANTHROPIC_DEFAULT_OPUS_MODEL_SUPPORTED_CAPABILITIES` | Comma-separated list of capabilities the pinned Opus model supports |

The same `_NAME`, `_DESCRIPTION`, and `_SUPPORTED_CAPABILITIES` suffixes are available for `ANTHROPIC_DEFAULT_SONNET_MODEL` and `ANTHROPIC_DEFAULT_HAIKU_MODEL`.Claude Code enables features like [effort levels](https://code.claude.com/docs/en/model-config#adjust-effort-level) and [extended thinking](https://code.claude.com/docs/en/common-workflows#use-extended-thinking-thinking-mode) by matching the model ID against known patterns. Provider-specific IDs such as Bedrock ARNs or custom deployment names often don’t match these patterns, leaving supported features disabled. Set `_SUPPORTED_CAPABILITIES` to tell Claude Code which features the model actually supports:

| Capability value | Enables |
| --- | --- |
| `effort` | [Effort levels](https://code.claude.com/docs/en/model-config#adjust-effort-level) and the `/effort` command |
| `max_effort` | The `max` effort level |
| `thinking` | [Extended thinking](https://code.claude.com/docs/en/common-workflows#use-extended-thinking-thinking-mode) |
| `adaptive_thinking` | Adaptive reasoning that dynamically allocates thinking based on task complexity |
| `interleaved_thinking` | Thinking between tool calls |

When `_SUPPORTED_CAPABILITIES` is set, listed capabilities are enabled and unlisted capabilities are disabled for the matching pinned model. When the variable is unset, Claude Code falls back to built-in detection based on the model ID.This example pins Opus to a Bedrock custom model ARN, sets a friendly name, and declares its capabilities:

Report incorrect code

Copy

Ask AI

```
export ANTHROPIC_DEFAULT_OPUS_MODEL='arn:aws:bedrock:us-east-1:123456789012:custom-model/abc'
export ANTHROPIC_DEFAULT_OPUS_MODEL_NAME='Opus via Bedrock'
export ANTHROPIC_DEFAULT_OPUS_MODEL_DESCRIPTION='Opus 4.6 routed through a Bedrock custom endpoint'
export ANTHROPIC_DEFAULT_OPUS_MODEL_SUPPORTED_CAPABILITIES='effort,max_effort,thinking,adaptive_thinking,interleaved_thinking'
```

### [​](https://code.claude.com/docs/en/model-config\#override-model-ids-per-version)  Override model IDs per version

The family-level environment variables above configure one model ID per family alias. If you need to map several versions within the same family to distinct provider IDs, use the `modelOverrides` setting instead.`modelOverrides` maps individual Anthropic model IDs to the provider-specific strings that Claude Code sends to your provider’s API. When a user selects a mapped model in the `/model` picker, Claude Code uses your configured value instead of the built-in default.This lets enterprise administrators route each model version to a specific Bedrock inference profile ARN, Vertex AI version name, or Foundry deployment name for governance, cost allocation, or regional routing.Set `modelOverrides` in your [settings file](https://code.claude.com/docs/en/settings#settings-files):

Report incorrect code

Copy

Ask AI

```
{
  "modelOverrides": {
    "claude-opus-4-6": "arn:aws:bedrock:us-east-2:123456789012:application-inference-profile/opus-prod",
    "claude-opus-4-5-20251101": "arn:aws:bedrock:us-east-2:123456789012:application-inference-profile/opus-45-prod",
    "claude-sonnet-4-6": "arn:aws:bedrock:us-east-2:123456789012:application-inference-profile/sonnet-prod"
  }
}
```

Keys must be Anthropic model IDs as listed in the [Models overview](https://platform.claude.com/docs/en/about-claude/models/overview). For dated model IDs, include the date suffix exactly as it appears there. Unknown keys are ignored.Overrides replace the built-in model IDs that back each entry in the `/model` picker. On Bedrock, overrides take precedence over any inference profiles that Claude Code discovers automatically at startup. Values you supply directly through `ANTHROPIC_MODEL`, `--model`, or the `ANTHROPIC_DEFAULT_*_MODEL` environment variables are passed to the provider as-is and are not transformed by `modelOverrides`.`modelOverrides` works alongside `availableModels`. The allowlist is evaluated against the Anthropic model ID, not the override value, so an entry like `"opus"` in `availableModels` continues to match even when Opus versions are mapped to ARNs.

### [​](https://code.claude.com/docs/en/model-config\#prompt-caching-configuration)  Prompt caching configuration

Claude Code automatically uses [prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) to optimize performance and reduce costs. You can disable prompt caching globally or for specific model tiers:

| Environment variable | Description |
| --- | --- |
| `DISABLE_PROMPT_CACHING` | Set to `1` to disable prompt caching for all models (takes precedence over per-model settings) |
| `DISABLE_PROMPT_CACHING_HAIKU` | Set to `1` to disable prompt caching for Haiku models only |
| `DISABLE_PROMPT_CACHING_SONNET` | Set to `1` to disable prompt caching for Sonnet models only |
| `DISABLE_PROMPT_CACHING_OPUS` | Set to `1` to disable prompt caching for Opus models only |

These environment variables give you fine-grained control over prompt caching behavior. The global `DISABLE_PROMPT_CACHING` setting takes precedence over the model-specific settings, allowing you to quickly disable all caching when needed. The per-model settings are useful for selective control, such as when debugging specific models or working with cloud providers that may have different caching implementations.

Was this page helpful?

YesNo

[Terminal configuration](https://code.claude.com/docs/en/terminal-config) [Speed up responses with fast mode](https://code.claude.com/docs/en/fast-mode)

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

[Privacy choices](https://code.claude.com/docs/en/model-config#) [Privacy policy](https://www.anthropic.com/legal/privacy) [Disclosure policy](https://www.anthropic.com/responsible-disclosure-policy) [Usage policy](https://www.anthropic.com/legal/aup) [Commercial terms](https://www.anthropic.com/legal/commercial-terms) [Consumer terms](https://www.anthropic.com/legal/consumer-terms)

Assistant

Responses are generated using AI and may contain mistakes.