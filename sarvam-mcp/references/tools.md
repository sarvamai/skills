# Tool & env reference

Connected-server schemas win. Use this for defaults and routing; for exact request shapes while coding, call `sarvam_code_api_reference`.

## Audio input pattern

Most audio tools accept one of:

- `audio_path` — absolute local path (preferred)
- `audio_base64` + `filename`
- `audio_url` + `filename`

## Runtime — `sarvam_tools_*`

### STT

| Tool | Use for | Notes |
|------|---------|-------|
| `stt_transcribe` | Short clip → text | `saaras:v3`; modes: `transcribe`, `translate`, `verbatim`, `translit`, `codemix`. REST ~30s. |
| `stt_translate` | Speech → English | Dedicated path |
| `stt_batch_submit` | Long audio, diarization, multi-file | Then poll status |
| `stt_batch_status` | Poll / download batch job | |

### TTS

| Tool | Use for | Notes |
|------|---------|-------|
| `tts_speak` | Text → file | `bulbul:v3`; output per `SARVAM_AUDIO_OUTPUT_MODE` |
| `tts_stream` | Lower-latency stream | When client handles streams |

Speaker default: `priya`. `tts_speak` also exposes `pitch` (default 0.0) and `loudness` (default 1.0), passed straight through to the API — the tool itself allows a wider range (-1.0..1.0 / 0.1..3.0) than the live API actually accepts for bulbul:v3 (-0.5..0.5 / 0.1..2.5), so an out-of-range value here still comes back as a 400 from Sarvam, not from the tool. Native-script Indic text.

### Text / LLM / vision

| Tool | Use for |
|------|---------|
| `translate` | Text translation (`mayura:v1` or `sarvam-translate:v1`) |
| `transliterate` | Script conversion |
| `identify_language` | LID + script (pre-step for TTS/translate) |
| `text_analytics` | Typed Q&A over text |
| `llm_complete` | Chat — `sarvam-105b` is the only model this tool accepts (v0.2.9); `sarvam-30b` is dead at the API level entirely |
| `vision_extract` | Document intelligence |
| `vision_job_status` | Poll vision job |
| `pronunciation_*` | Dict CRUD (bulbul:v3) |
| `set_api_key` | Persist key to `~/.sarvam/credentials` |
| `upgrade` | Check for / install a newer sarvam-mcp release (`confirm_upgrade=True` to actually upgrade) |

Prefix every name above with `sarvam_tools_`. Confirmed against the sarvam-mcp v0.2.9 package source (`@mcp.tool(name="sarvam_tools_...")` decorators) — this is ground truth, more reliable than the docs.sarvam.ai MCP page, which lists tool names without the prefix.

### Composites

| Tool | Pipeline | Typical required args |
|------|----------|------------------------|
| `voice` | STT → LLM → TTS | audio in; optional `system_prompt`, `reply_language`, `speaker` |
| `dub` | STT → Translate → TTS | audio + `target_language_code` (TTS langs only) |
| `localize` | String-table translate | `source_path` + `target_language_code` |
| `recall` | STT → LLM Q&A | `question` + audio `paths` |

## Build-time — `sarvam_code_*`

Safe for drafting integrations (no user-content generation credits, except live-verified snippets where documented).

| Tool | Use for |
|------|---------|
| `recommend_model` | Plain-English task → model + lang (no API key) |
| `api_reference` | Known endpoint path → request/response |
| `snippet` | `stt`/`tts`/`translate`/`llm` × `python`/`javascript`/`typescript`/`curl` |
| `languages` | Coverage for `stt`/`tts`/`translate`/… |
| `speakers` | `bulbul:v3` only (its `model` param type is `Literal["bulbul:v3"]` — no v2/beta). Its baked-in list has 38 names including `niharika`, but the live API's current error-message speaker list has only 37 and does not include `niharika` — treat a `sarvam_code_speakers` result as a starting point, not gospel, and expect the live API to be the final word if a speaker name is rejected. |
| `validate_request` | Draft body lint before ship |
| `pricing` | Billing structure (confirm on dashboard) |

Prefix every name above with `sarvam_code_`. (`search_docs` was in an earlier version of this reference but does not exist in sarvam-mcp v0.2.9 — removed.)

## Env

| Variable | Default | Meaning |
|----------|---------|---------|
| `SARVAM_API_KEY` | — | Required unless credentials file set |
| `SARVAM_API_BASE_URL` | `https://api.sarvam.ai` | Staging override |
| `SARVAM_MCP_BASE_PATH` | `~/Desktop` | Output directory |
| `SARVAM_AUDIO_OUTPUT_MODE` | `files` | `files` \| `resources` \| `both` |

## Observability

Runtime responses often include `observability` (latency, request IDs, credits). Surface when debugging; skip in casual answers.
