---
name: sarvam-mcp
description: >-
  Run Indic speech and language tasks through the Sarvam MCP server: translate
  text, transcribe or dub audio, TTS, localize i18n files, LLM complete, vision
  extract, or fetch Sarvam API docs/snippets while coding. Use this skill when
  the user wants Sarvam to act in chat, when sarvam_tools_* / sarvam_code_* are
  available, or when setting up sarvam-mcp in Cursor, Claude Code, Claude
  Desktop, Windsurf, Zed, Codex, Gemini CLI, VS Code, Cline, Continue, or LM
  Studio — even if they only say "translate this to Hindi" or "make it speak."
  Do not use for LiveKit/Pipecat agent code (voice-agents) or SDK-only coding
  when MCP is not installed (translate, speech-to-text, text-to-speech, chat).
license: Apache-2.0
compatibility: Requires sarvam-mcp connected (or installable via uvx/pip) and network access to api.sarvam.ai.
metadata:
  author: sarvam-ai
  version: "2.0"
---

# Sarvam MCP

Drive [sarvam-mcp](https://github.com/sarvamai/sarvam-mcp). Prefer MCP tools over inventing HTTP/SDK calls for live work.

## Procedure

Copy and track:

```
- [ ] 1. MCP available? If no → read references/install.md (or fall back to SDK skills)
- [ ] 2. Namespace: live action → sarvam_tools_*; write/lookup code → sarvam_code_*
- [ ] 3. Prefer a composite if the task spans STT/translate/TTS/LLM
- [ ] 4. Call the tool (absolute paths; BCP-47 codes)
- [ ] 5. On auth error → sarvam_tools_set_api_key; on param error → fix and retry
- [ ] 6. Return the result path/text; mention observability only if debugging
```

### 1. Namespace (mandatory)

| User wants… | Namespace | Example |
|-------------|-----------|---------|
| Sarvam to **do it now** | `sarvam_tools_*` | "Translate this to Tamil" |
| Help **writing code** / API facts | `sarvam_code_*` | "How do I call TTS from Python?" |

Never use `sarvam_code_*` for a live translate/TTS/STT request. Never burn `sarvam_tools_*` credits just to draft code unless the user asked for a live demo.

### 2. Pick the tool (defaults)

**Composites first** — do not hand-chain STT → translate → TTS:

| Task | Tool |
|------|------|
| Spoken reply to audio | `sarvam_tools_voice` |
| Dub into another Indic language | `sarvam_tools_dub` |
| Localize JSON/YAML/PO/etc. | `sarvam_tools_localize` |
| Q&A / summary over audio | `sarvam_tools_recall` |

**Atomic runtime** (use when no composite fits):

| Task | Tool |
|------|------|
| Transcribe | `sarvam_tools_stt_transcribe` |
| Speech → English | `sarvam_tools_stt_translate` |
| Audio >~30s / diarization | `sarvam_tools_stt_batch_submit` → `_stt_batch_status` |
| Speak text | `sarvam_tools_tts_speak` |
| Translate text | `sarvam_tools_translate` |
| Transliterate / LID / analytics | `sarvam_tools_transliterate` / `_identify_language` / `_text_analytics` |
| Chat complete | `sarvam_tools_llm_complete` |
| Document intelligence | `sarvam_tools_vision_extract` → `_vision_job_status` |
| Pronunciation dicts | `sarvam_tools_pronunciation_*` |
| Set / rotate API key | `sarvam_tools_set_api_key` |

**Build-time** (coding help):

| Task | Tool |
|------|------|
| Unsure which model/lang | `sarvam_code_recommend_model` |
| Endpoint shape | `sarvam_code_api_reference` |
| Snippet | `sarvam_code_snippet` |
| Speakers / languages | `sarvam_code_speakers` / `_languages` |
| Validate draft body | `sarvam_code_validate_request` |
| Pricing | `sarvam_code_pricing` |

Coding flow: `recommend_model` → `snippet` or `api_reference` → `validate_request`.

For parameters and env knobs, read [references/tools.md](references/tools.md).

### 3. Defaults (use unless user overrides)

| Setting | Default |
|---------|---------|
| STT model | `saaras:v3` |
| TTS model / speaker | `bulbul:v3` / `priya` |
| LLM | `sarvam-30b` (use `sarvam-105b` for hard reasoning) |
| Translate model | `mayura:v1` (switch to `sarvam-translate:v1` for broader Indic coverage) |
| Audio path | Absolute local path |
| Language codes | BCP-47 (`hi-IN`, `ta-IN`, **`od-IN`** not `or-IN`) |

### 4. Auth

Key sources (env wins): `SARVAM_API_KEY`, or `~/.sarvam/credentials` (`api_key = sk_...`).

Dashboard: https://dashboard.sarvam.ai/key-management

On auth failure:

1. `sarvam_tools_set_api_key` with empty `api_key` → instructions + link
2. Call again with `sk_...` → persists to `~/.sarvam/credentials`

Wire auth is `api-subscription-key` — never invent `Authorization: Bearer`.

## Examples

**Live translate**

User: "Translate 'Good morning' to Hindi."

→ `sarvam_tools_translate` with `input`, `source_language_code=en-IN`, `target_language_code=hi-IN`. Return `translated_text`.

**Live TTS**

User: "Say नमस्ते in Hindi."

→ `sarvam_tools_tts_speak` with native-script text, `target_language_code=hi-IN`, `speaker=priya`. Return the audio path.

**Dub**

User: "Dub this clip into Tamil" + path.

→ `sarvam_tools_dub` with `audio_path`, `target_language_code=ta-IN` — not STT + translate + TTS separately.

**Code help**

User: "Show a Python TTS example."

→ `sarvam_code_snippet` with `api=tts`, `language=python` (not `sarvam_tools_tts_speak` unless they want audio now).

## Gotchas

| Mistake agents make | Correct behavior |
|---------------------|------------------|
| Invent `curl`/SDK for a live ask | Call `sarvam_tools_*` when MCP is connected |
| Hand-chain STT→translate→TTS | Use `voice` / `dub` / `localize` / `recall` |
| REST STT on long files | Use `stt_batch_*` above ~30s |
| TTS target outside ~11 langs | Check with `sarvam_code_languages` (`api=tts`); STT has ~23 |
| v2 speaker on Bulbul v3 | Use `priya`/`shubh` or `sarvam_code_speakers` |
| `pitch` / `loudness` on v3 | Only `pace` (0.5–2.0) |
| Romanized Indic for TTS | Prefer native script |
| `output_script` on `sarvam-translate:v1` | `mayura:v1` only |
| Relative audio paths | Prefer absolute paths; or `audio_base64`/`audio_url` + `filename` |
| Assume output cwd | Files go under `SARVAM_MCP_BASE_PATH` (default `~/Desktop`) unless tool returns another path |
| Stale tool names without `_tools`/`_code` | Match the connected server's tool list |

## When MCP is missing

1. Read [references/install.md](references/install.md) and help the user connect the server.
2. If they only need code: use sibling skills `translate`, `speech-to-text`, `text-to-speech`, `chat`, or https://docs.sarvam.ai/llms.txt.

## References (load on demand)

| File | Read when |
|------|-----------|
| [references/install.md](references/install.md) | MCP not connected, setup/troubleshoot, or user names a client |
| [references/tools.md](references/tools.md) | Choosing parameters, env vars, or an uncommon tool |
