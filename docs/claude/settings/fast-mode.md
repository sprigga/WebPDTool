# Fast Mode

> Source: https://code.claude.com/docs/en/fast-mode
> Get faster Opus 4.6 responses in Claude Code by toggling fast mode.

Fast mode is in **research preview**. The feature, pricing, and availability may change based on feedback.

Fast mode is a high-speed configuration for Claude Opus 4.6, making the model **2.5x faster** at a higher cost per token. Toggle it on with `/fast` for interactive work like rapid iteration or live debugging, and off when cost matters more than latency.

Fast mode is **not a different model**. It uses the same Opus 4.6 with a different API configuration that prioritizes speed over cost efficiency. You get identical quality and capabilities, just faster responses.

Requires Claude Code v2.1.36 or later.

---

## Toggle Fast Mode

- Type `/fast` and press Tab to toggle on or off
- Set `"fastMode": true` in your [user settings file](./claude-code-settings.md)

Fast mode persists across sessions by default.

When enabling fast mode:
- If on a different model, Claude Code automatically switches to Opus 4.6
- Confirmation: "Fast mode ON"
- A small `↯` icon appears next to the prompt
- `/fast` again toggles off (you remain on Opus 4.6; use `/model` to switch)

For best cost efficiency, enable fast mode at session start rather than mid-conversation.

---

## Cost Tradeoff

| Mode | Input (MTok) | Output (MTok) |
| --- | --- | --- |
| Fast mode on Opus 4.6 | $30 | $150 |

Flat pricing across the full 1M token context window. Switching mid-conversation costs more because the entire context is re-priced at the uncached fast mode rate.

---

## When to Use Fast Mode

**Best for** (latency matters more than cost):
- Rapid iteration on code changes
- Live debugging sessions
- Time-sensitive work with tight deadlines

**Standard mode better for**:
- Long autonomous tasks
- Batch processing or CI/CD pipelines
- Cost-sensitive workloads

### Fast Mode vs Effort Level

| Setting | Effect |
| --- | --- |
| **Fast mode** | Same model quality, lower latency, higher cost |
| **Lower effort level** | Less thinking time, faster responses, potentially lower quality |

Both can be combined: fast mode + lower effort for maximum speed on straightforward tasks.

---

## Requirements

- **Not available on third-party cloud providers**: Bedrock, Vertex AI, or Foundry
- **Extra usage enabled**: Required for billing beyond plan's included usage
- **Admin enablement**: Disabled by default for Teams/Enterprise; admin must enable

Usage billed directly to extra usage, even with remaining plan usage.

---

## Per-Session Opt-In

Set `fastModePerSessionOptIn` to `true` in [managed settings](./claude-code-settings.md) to reset fast mode each session:

```json
{
  "fastModePerSessionOptIn": true
}
```

Users must explicitly enable with `/fast` each session. The preference is still saved — removing this setting restores persistent behavior.

---

## Rate Limits

Fast mode has separate rate limits from standard Opus 4. When hitting limits:

1. Auto-falls back to standard Opus 4.6
2. `↯` icon turns gray (cooldown)
3. Continue working at standard speed/pricing
4. Auto re-enables when cooldown expires

Run `/fast` to manually disable instead of waiting.
