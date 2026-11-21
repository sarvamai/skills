# Skills End-to-End Test Report

**Date:** 2026-09-28
**Scope:** Every skill touched in the `skills/sync-with-docs-sarvam-ai` merge (chat, speech-to-text, text-to-speech, translate/text, translate/document, doc-ai, voice-cloning, dubbing, voice-agents), tested live against `api.sarvam.ai` with a real API key. `sarvam-mcp` was intentionally excluded (per earlier instruction not to touch it).

## Method

- Upgraded `sarvamai` Python SDK `0.1.32 → 0.1.34` and installed the JS SDK (`sarvamai@1.1.10`) fresh in a scratch project — both needed for the newer gotchas (`keyterms`, `doc_ai`, `dubbing`) to even be reachable.
- Generated two self-contained test assets via Sarvam's own APIs rather than external files: a short Hindi TTS clip (`bulbul:v3`) reused as input for STT/voice-cloning/dubbing, and a one-page PDF (via `fpdf2`) for doc-ai/document-translation.
- Ran every documented Python code path live; mirrored the JS-specific gotchas (positional args, field casing, method presence) with a parallel JS suite.
- Real money was spent: dubbing (2 short jobs), voice cloning (create + synthesize), doc-ai (digitise + extract), document translation, TTS, and various chat/STT/translate calls. Total spend was modest — low-second-length audio and a 1-page PDF throughout — but check `dashboard.sarvam.ai` for exact billing if you want the number.
- "FAIL" in the raw test log below often means *"the thing I expected to error, errored"* (e.g. confirming `sarvam-30b` now hard-fails) — read the finding, not just the label.

## Headline: 6 real bugs found and fixed

| # | Skill | Bug | Fix |
|---|---|---|---|
| 1 | `chat` | Quick Start code samples used `model="sarvam-30b"`, which now hard-fails with `400` at the API (not just "discouraged") | Swapped Quick Start examples to `sarvam-105b-conversations`; added the exact verified error message as a gotcha |
| 2 | `chat` | `client.chat.completionsV2(...)` doesn't exist in the JS SDK (`sarvamai@1.1.10`) — `TypeError: not a function`. Only Python has it | Removed the JS claim; gotcha now says Python-only, told to check `npm ls sarvamai` before generating JS code for it |
| 3 | `speech-to-text` | The pre-existing legacy WebSocket example (`speech_to_text_streaming.connect(...)`) is missing `language_code`, which the installed SDK now requires — `TypeError: missing 1 required keyword-only argument` | Added `language_code="hi-IN"` to the example, with a gotcha explaining it's no longer optional |
| 4 | `translate/text` | Pre-existing gotcha claimed `output_script` on `sarvam-translate:v1` is "silently ignored" — it now returns a hard `400` | Rewrote the gotcha with the verified error text |
| 5 | `dubbing` | `client.dubbing.start(job_id=...)` throws `pydantic.ValidationError` in Python (`sarvamai==0.1.34`) — server returns `data.project_id`, SDK expects `data.job_id`. **Job still starts server-side regardless.** JS is unaffected (looser response typing) | Wrapped Python `start()` in try/except in the Quick Start; documented as Python-only, with the exact error and the confirmed workaround |
| 6 | `dubbing` | JS `dubbing.create({source_language_code, target_language_codes, ...})` — the exact field names shown in **Sarvam's own published TS SDK sample** on docs.sarvam.ai — returns `400: src_lang/target_langs Field required`. JS needs the raw wire names `src_lang`/`target_langs`, unlike Python which accepts `source_language_code`/`target_language_codes` fine | Rewrote the JS Quick Start to use `src_lang`/`target_langs`, with a gotcha calling out that Sarvam's own docs example is currently broken |

Plus one skill (**voice-cloning**) where the whole premise needed a caveat: **the `voice_cloning`/`voiceCloning` SDK group doesn't exist yet** in either released SDK, even though it's documented and the underlying REST API works perfectly. The skill now leads with a verified-working REST Quick Start and keeps the SDK version as "once released."

## Per-skill results

### chat
| Test | Result |
|---|---|
| `sarvam-105b` | ✅ works (hit the documented `content=None` flakiness once at `max_tokens=500`, then worked on retry — gotcha now says not to treat 500 as a hard guarantee) |
| `sarvam-105b-conversations` | ✅ works |
| `sarvam-30b` | ✅ confirmed hard `400`, exact message captured |
| `/v2` `glm5.3`, `gemma4`, `deepseekv4-flash` via `completions_v2` | ✅ all three work in Python (this key has beta access) |
| Same three via JS `completionsV2` | ❌ method doesn't exist — **fixed** |

### speech-to-text
| Test | Result |
|---|---|
| `saaras:v3` / `saaras:v4` transcribe | ✅ both work. Side note (not a bug): v3 spelled out digits as words, v4 gave clean `9840950950` — a real quality difference, not documented anywhere, informational only |
| `saaras:v4` + `keyterms` (REST, Python) | ✅ works |
| `saaras:v3` + `keyterms` | ✅ confirmed hard `400` as documented |
| Batch API + diarization | ✅ full job lifecycle works |
| Legacy WebSocket streaming | ❌ missing required `language_code` — **fixed** |
| Realtime streaming (`saaras:v3-realtime`) | ✅ works, got `session.begin` → `vad.speech_start` → multiple `transcript.partial` events as documented |
| JS `keyterms` on REST `transcribe()` | ✅ worked without error — **contradicts the docs page**, which says this hasn't shipped to npm yet. Softened that gotcha to "test it yourself, don't trust either source blindly" |

### text-to-speech
No changes needed — every gotcha confirmed accurate: `convert_stream` works, `pitch` on v3 returns `400` with the exact message now captured, `anushka` (v2 speaker) on `bulbul:v3` returns `400` listing valid v3 speakers.

### translate/text
`sarvam-translate:v1`, `mayura:v1`, and `mayura:v1` with `source_language_code="auto"` all work. `output_script` on `sarvam-translate:v1` — **fixed** (see bugs table).

### translate/document
Full create → upload → start → poll → trigger_export → poll-export pipeline ran clean end to end. No changes needed.

### doc-ai
Both `digitise()` and `extract()` ran clean end to end in Python and JS (`docAi.digitise` + positional `getStatus`/`getDownloadUrl` confirmed). `extract()` pulled the exact `policy_number`/`sum_insured` values out of the test PDF. No changes needed — this skill was fully accurate on the first pass.

### voice-cloning
SDK absent in both languages (see above) — **fixed** with a REST-first rewrite. Every documented REST gotcha confirmed exactly as written: unwrapped response, studio-only-field `400`, `pace`+`max_audio_duration` mutual-exclusion `400`, delete returns `204`.

### dubbing
Full pipeline (create → upload → start → poll → export) completed successfully once the `start()` workaround was applied — both `audio` and `srt` exports came back `completed` with real download URLs. Two real bugs found and fixed (see bugs table above); everything else (auto-export, `export`/`exports` swap, `limit` default, Odia `or-IN`, `partial_failure` handling) held up.

### voice-agents
Didn't run a full live LiveKit/Pipecat session (needs a real room/transport, out of scope for a CLI smoke test) — instead directly tested the exact claim the skill makes: `pipecat-ai`'s `SarvamLLMService` model allowlist. Confirmed live against `pipecat-ai==0.0.108`:
- `sarvam-105b` — accepted ✅
- `sarvam-30b` / `sarvam-30b-16k` — still **accepted at construction** even though the API itself now rejects them at call time (a real trap) — now called out explicitly
- `sarvam-105b-conversations` — **rejected** with `ValueError: Unsupported Sarvam LLM model...` — confirms the caution already in the skill was correct and necessary

## Not covered

- **`sarvam-mcp`** — excluded per earlier instruction; the tool-naming discrepancy from the original audit is still open.
- **A live LiveKit/Pipecat voice session** (actual audio room, telephony) — would need real room/transport infrastructure beyond a CLI smoke test. The underlying STT/TTS/LLM primitives it wraps were all verified independently above.

## Files changed in this pass

`chat/SKILL.md`, `speech-to-text/SKILL.md`, `translate/text/SKILL.md`, `dubbing/SKILL.md`, `voice-cloning/SKILL.md`, `voice-agents/SKILL.md` — all version-bumped. `doc-ai/SKILL.md`, `text-to-speech/SKILL.md`, `translate/document/SKILL.md` needed no changes.
