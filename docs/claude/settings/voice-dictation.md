# Voice Dictation

> Source: https://code.claude.com/docs/en/voice-dictation
> Use push-to-talk voice dictation to speak your prompts in the Claude Code CLI.

Hold a key and speak to dictate prompts. Speech is transcribed live into the input, so you can mix voice and typing. Enable with `/voice`. Default push-to-talk key is `Space`.

Requires Claude Code v2.1.69 or later.

---

## Requirements

- **Claude.ai account only** — not available with API keys, Bedrock, Vertex AI, or Foundry
- **Local microphone access** — does not work in remote environments (SSH, web sessions)
- **WSL**: Requires WSLg for audio access (included with WSL2 on Windows 11)
- **Linux fallback**: If native module can't load, falls back to `arecord` (ALSA) or `rec` (SoX)

---

## Enable Voice Dictation

Run `/voice` to toggle on. First time triggers microphone permission prompt (macOS).

```
/voice
Voice mode enabled. Hold Space to record. Dictation language: en (/config to change).
```

Voice dictation persists across sessions. Set directly in settings:

```json
{
  "voiceEnabled": true
}
```

While enabled, the input footer shows a `hold Space to speak` hint (hidden if custom status line configured).

---

## Record a Prompt

Hold `Space` to start recording. Brief warmup before recording begins (footer shows `keep holding…`, then live waveform).

To skip warmup, rebind to a modifier combination like `meta+k` (starts on first keypress).

Speech appears dimmed until finalized. Release `Space` to stop. Transcript is inserted at cursor position. Mix typing and dictation in any order:

```
> refactor the auth middleware to ▮
  # hold Space, speak "use the new token validation helper"
> refactor the auth middleware to use the new token validation helper▮
```

Transcription is tuned for coding vocabulary (`regex`, `OAuth`, `JSON`, `localhost`). Your project name and git branch are added as recognition hints.

---

## Change the Dictation Language

Voice dictation uses the [`language` setting](./claude-code-settings.md) that controls Claude's response language. If empty, defaults to English.

### Supported Languages

| Language | Code |
| --- | --- |
| Czech | `cs` |
| Danish | `da` |
| Dutch | `nl` |
| English | `en` |
| French | `fr` |
| German | `de` |
| Greek | `el` |
| Hindi | `hi` |
| Indonesian | `id` |
| Italian | `it` |
| Japanese | `ja` |
| Korean | `ko` |
| Norwegian | `no` |
| Polish | `pl` |
| Portuguese | `pt` |
| Russian | `ru` |
| Spanish | `es` |
| Swedish | `sv` |
| Turkish | `tr` |
| Ukrainian | `uk` |

Set in `/config` or settings (BCP 47 code or language name):

```json
{
  "language": "japanese"
}
```

If language is not supported, `/voice` warns and falls back to English for dictation. Claude's text responses are not affected.

---

## Rebind the Push-to-Talk Key

Bound to `voice:pushToTalk` in the `Chat` context. Rebind in [`~/.claude/keybindings.json`](./keybindings.md):

```json
{
  "bindings": [
    {
      "context": "Chat",
      "bindings": {
        "meta+k": "voice:pushToTalk",
        "space": null
      }
    }
  ]
}
```

Set `"space": null` to remove the default. Avoid bare letter keys like `v` (types into prompt during warmup). Use `Space` or modifier combos.

---

## Troubleshooting

| Issue | Solution |
| --- | --- |
| `Voice mode requires a Claude.ai account` | Run `/login` to sign in with Claude.ai |
| `Microphone access is denied` | Grant mic permission to terminal in OS settings |
| `No audio recording tool found` (Linux) | Install SoX: `sudo apt-get install sox` |
| Nothing happens holding `Space` | Run `/voice` to enable; ensure key-repeat is enabled at OS level |
| Transcription in wrong language | Set language in `/config` |
