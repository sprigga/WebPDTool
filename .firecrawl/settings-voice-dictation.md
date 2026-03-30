[Skip to main content](https://code.claude.com/docs/en/voice-dictation#content-area)

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

Voice dictation

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

- [Requirements](https://code.claude.com/docs/en/voice-dictation#requirements)
- [Enable voice dictation](https://code.claude.com/docs/en/voice-dictation#enable-voice-dictation)
- [Record a prompt](https://code.claude.com/docs/en/voice-dictation#record-a-prompt)
- [Change the dictation language](https://code.claude.com/docs/en/voice-dictation#change-the-dictation-language)
- [Rebind the push-to-talk key](https://code.claude.com/docs/en/voice-dictation#rebind-the-push-to-talk-key)
- [Troubleshooting](https://code.claude.com/docs/en/voice-dictation#troubleshooting)
- [See also](https://code.claude.com/docs/en/voice-dictation#see-also)

Configuration

# Voice dictation

Copy page

Use push-to-talk voice dictation to speak your prompts instead of typing them in the Claude Code CLI.

Copy page

Hold a key and speak to dictate your prompts. Your speech is transcribed live into the prompt input, so you can mix voice and typing in the same message. Enable dictation with `/voice`. The default push-to-talk key is `Space`; [rebind to a modifier combination](https://code.claude.com/docs/en/voice-dictation#rebind-the-push-to-talk-key) to activate on the first keypress rather than after a brief hold.

Voice dictation requires Claude Code v2.1.69 or later. Check your version with `claude --version`.

## [​](https://code.claude.com/docs/en/voice-dictation\#requirements)  Requirements

Voice dictation uses a streaming speech-to-text service that is only available when you authenticate with a Claude.ai account. It is not available when Claude Code is configured to use an Anthropic API key directly, Amazon Bedrock, Google Vertex AI, or Microsoft Foundry.Voice dictation also needs local microphone access, so it does not work in remote environments such as [Claude Code on the web](https://code.claude.com/docs/en/claude-code-on-the-web) or SSH sessions. In WSL, voice dictation requires WSLg for audio access, which is included with WSL2 on Windows 11. On Windows 10 or WSL1, run Claude Code in native Windows instead.Audio recording uses a built-in native module on macOS, Linux, and Windows. On Linux, if the native module cannot load, Claude Code falls back to `arecord` from ALSA utils or `rec` from SoX. If neither is available, `/voice` prints an install command for your package manager.

## [​](https://code.claude.com/docs/en/voice-dictation\#enable-voice-dictation)  Enable voice dictation

Run `/voice` to toggle voice dictation on. The first time you enable it, Claude Code runs a microphone check. On macOS, this triggers the system microphone permission prompt for your terminal if it has never been granted.

Report incorrect code

Copy

Ask AI

```
/voice
Voice mode enabled. Hold Space to record. Dictation language: en (/config to change).
```

Voice dictation persists across sessions. Run `/voice` again to turn it off, or set it directly in your [user settings file](https://code.claude.com/docs/en/settings):

Report incorrect code

Copy

Ask AI

```
{
  "voiceEnabled": true
}
```

While voice dictation is enabled, the input footer shows a `hold Space to speak` hint when the prompt is empty. The hint does not appear if you have a [custom status line](https://code.claude.com/docs/en/statusline) configured.

## [​](https://code.claude.com/docs/en/voice-dictation\#record-a-prompt)  Record a prompt

Hold `Space` to start recording. Claude Code detects a held key by watching for rapid key-repeat events from your terminal, so there is a brief warmup before recording begins. The footer shows `keep holding…` during warmup, then switches to a live waveform once recording is active.The first couple of key-repeat characters type into the input during warmup and are removed automatically when recording activates. A single `Space` tap still types a space, since hold detection only triggers on rapid repeat.

To skip the warmup, [rebind to a modifier combination](https://code.claude.com/docs/en/voice-dictation#rebind-the-push-to-talk-key) like `meta+k`. Modifier combos start recording on the first keypress.

Your speech appears in the prompt as you speak, dimmed until the transcript is finalized. Release `Space` to stop recording and finalize the text. The transcript is inserted at your cursor position and the cursor stays at the end of the inserted text, so you can mix typing and dictation in any order. Hold `Space` again to append another recording, or move the cursor first to insert speech elsewhere in the prompt:

Report incorrect code

Copy

Ask AI

```
> refactor the auth middleware to ▮
  # hold Space, speak "use the new token validation helper"
> refactor the auth middleware to use the new token validation helper▮
```

Transcription is tuned for coding vocabulary. Common development terms like `regex`, `OAuth`, `JSON`, and `localhost` are recognized correctly, and your current project name and git branch name are added as recognition hints automatically.

## [​](https://code.claude.com/docs/en/voice-dictation\#change-the-dictation-language)  Change the dictation language

Voice dictation uses the same [`language` setting](https://code.claude.com/docs/en/settings) that controls Claude’s response language. If that setting is empty, dictation defaults to English.

Supported dictation languages

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

Set the language in `/config` or directly in settings. You can use either the [BCP 47 language code](https://en.wikipedia.org/wiki/IETF_language_tag) or the language name:

Report incorrect code

Copy

Ask AI

```
{
  "language": "japanese"
}
```

If your `language` setting is not in the supported list, `/voice` warns you on enable and falls back to English for dictation. Claude’s text responses are not affected by this fallback.

## [​](https://code.claude.com/docs/en/voice-dictation\#rebind-the-push-to-talk-key)  Rebind the push-to-talk key

The push-to-talk key is bound to `voice:pushToTalk` in the `Chat` context and defaults to `Space`. Rebind it in [`~/.claude/keybindings.json`](https://code.claude.com/docs/en/keybindings):

Report incorrect code

Copy

Ask AI

```
{
  "bindings": [\
    {\
      "context": "Chat",\
      "bindings": {\
        "meta+k": "voice:pushToTalk",\
        "space": null\
      }\
    }\
  ]
}
```

Setting `"space": null` removes the default binding. Omit it if you want both keys active.Because hold detection relies on key-repeat, avoid binding a bare letter key like `v` since it types into the prompt during warmup. Use `Space`, or use a modifier combination like `meta+k` to start recording on the first keypress with no warmup. See [customize keyboard shortcuts](https://code.claude.com/docs/en/keybindings) for the full keybinding syntax.

## [​](https://code.claude.com/docs/en/voice-dictation\#troubleshooting)  Troubleshooting

Common issues when voice dictation does not activate or record:

- **`Voice mode requires a Claude.ai account`**: you are authenticated with an API key or a third-party provider. Run `/login` to sign in with a Claude.ai account.
- **`Microphone access is denied`**: grant microphone permission to your terminal in system settings. On macOS, go to System Settings → Privacy & Security → Microphone. On Windows, go to Settings → Privacy → Microphone. Then run `/voice` again.
- **`No audio recording tool found` on Linux**: the native audio module could not load and no fallback is installed. Install SoX with the command shown in the error message, for example `sudo apt-get install sox`.
- **Nothing happens when holding `Space`**: watch the prompt input while you hold. If spaces keep accumulating, voice dictation is off; run `/voice` to enable it. If only one or two spaces appear and then nothing, voice dictation is on but hold detection is not triggering. Hold detection requires your terminal to send key-repeat events, so it cannot detect a held key if key-repeat is disabled at the OS level.
- **Transcription is garbled or in the wrong language**: dictation defaults to English. If you are dictating in another language, set it in `/config` first. See [Change the dictation language](https://code.claude.com/docs/en/voice-dictation#change-the-dictation-language).

## [​](https://code.claude.com/docs/en/voice-dictation\#see-also)  See also

- [Customize keyboard shortcuts](https://code.claude.com/docs/en/keybindings): rebind `voice:pushToTalk` and other CLI keyboard actions
- [Configure settings](https://code.claude.com/docs/en/settings): full reference for `voiceEnabled`, `language`, and other settings keys
- [Interactive mode](https://code.claude.com/docs/en/interactive-mode): keyboard shortcuts, input modes, and session controls
- [Built-in commands](https://code.claude.com/docs/en/commands): reference for `/voice`, `/config`, and all other commands

Was this page helpful?

YesNo

[Speed up responses with fast mode](https://code.claude.com/docs/en/fast-mode) [Output styles](https://code.claude.com/docs/en/output-styles)

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

[Privacy choices](https://code.claude.com/docs/en/voice-dictation#) [Privacy policy](https://www.anthropic.com/legal/privacy) [Disclosure policy](https://www.anthropic.com/responsible-disclosure-policy) [Usage policy](https://www.anthropic.com/legal/aup) [Commercial terms](https://www.anthropic.com/legal/commercial-terms) [Consumer terms](https://www.anthropic.com/legal/consumer-terms)

Assistant

Responses are generated using AI and may contain mistakes.