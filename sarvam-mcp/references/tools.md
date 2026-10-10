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
| `tts_speak` | Text → file | `model` = `bulbul:v3` (default) or `bulbul:v4-flash` (sarvam-mcp ≥ 0.2.11; default speaker `shubh_enhi_ads`). `text` max 2,500 chars. Optional `pace`, `pitch`, `loudness`. If the connected schema enums only `bulbul:v3`, the server is older — stay on v3 / `priya`. Output per `SARVAM_AUDIO_OUTPUT_MODE` |
| `tts_stream` | Lower-latency stream | Same `model` / `speaker` / `pitch` / `loudness` args as `tts_speak`. When client handles streams |

SDK code should also use `bulbul:v4-flash` and a `voice_language_style` speaker — see the text-to-speech skill. `pitch` is −0.5–0.5 and `loudness` 0.1–2.5 on both models. Native-script Indic text.

### Text / LLM / vision

| Tool | Use for |
|------|---------|
| `translate` | Text translation (`mayura:v1` or `sarvam-translate:v1`) |
| `transliterate` | Script conversion |
| `identify_language` | LID + script (pre-step for TTS/translate) |
| `text_analytics` | Typed Q&A over text |
| `llm_complete` | Chat (prefer `sarvam-105b`; `sarvam-30b` is deprecated) |
| `vision_extract` | Document intelligence |
| `vision_job_status` | Poll vision job |
| `pronunciation_*` | Dict CRUD; pass `dict_id` on v3 and v4-flash TTS calls |
| `set_api_key` | Persist key to `~/.sarvam/credentials` |

Prefix every name above with `sarvam_tools_`.

### Composites

| Tool | Pipeline | Typical required args |
|------|----------|------------------------|
| `voice` | STT → LLM → TTS | audio in; optional `system_prompt`, `reply_language`, `tts_model` (`bulbul:v3` default / `bulbul:v4-flash`), `speaker` |
| `dub` | STT → Translate → TTS | audio + `target_language_code` (TTS langs only); optional `tts_model`, `speaker` |
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
| `speakers` | Pass `model=bulbul:v4-flash` for the 222 persona IDs, or `bulbul:v3` for 37 names (sarvam-mcp ≥ 0.2.11; older servers list v3 / v2 / beta only). The 2 Assamese personas the API lists are not included. |
| `validate_request` | Draft body lint before ship |
| `pricing` | Billing structure (confirm on dashboard) |

Prefix every name above with `sarvam_code_`.

## Env

| Variable | Default | Meaning |
|----------|---------|---------|
| `SARVAM_API_KEY` | — | Required unless credentials file set |
| `SARVAM_API_BASE_URL` | `https://api.sarvam.ai` | Staging override |
| `SARVAM_MCP_BASE_PATH` | `~/Desktop` | Output directory |
| `SARVAM_AUDIO_OUTPUT_MODE` | `files` | `files` \| `resources` \| `both` |

## Observability

Runtime responses often include `observability` (latency, request IDs, credits). Surface when debugging; skip in casual answers.
