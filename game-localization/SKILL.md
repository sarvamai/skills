---
name: game-localization
description: >-
  Write correct Sarvam code for localizing a game — translating string tables
  with Mayura or sarvam-translate and generating NPC voice lines with Bulbul
  personas. Covers placeholder verification, per-model character limits,
  chunking, persona naming traps and batch caching. Use this skill when
  localizing game dialogue, quest text, UI strings or item descriptions into
  Indian languages, or when generating voiced NPC lines, barks or narration.
  Do not use it for plain text-to-speech with no game context (use
  text-to-speech), plain single-string translation (use translate/text), or
  whole documents (use translate/document).
license: Apache-2.0
metadata:
  author: Sambhav Jha
  version: "0.2.0"
---

# Game Localization — Sarvam AI

> Plain TTS → [text-to-speech](../text-to-speech/SKILL.md). Plain translation → [translate/text](../translate/text/SKILL.md). Whole documents → [translate/document](../translate/document/SKILL.md).

> [!IMPORTANT]
> Auth: `api-subscription-key` header — NOT `Authorization: Bearer`. Base URL `https://api.sarvam.ai` (NOT `/v1` — that prefix is only for the OpenAI-compatible chat endpoint).
> SDK floor: Python `sarvamai>=0.1.29`, JS `sarvamai@>=1.1.8`. On older versions the TTS parameter is `target_language_code`, not `language_code`.

## Scope

A game localizes a **string table** — a flat map of key to line — and then voices it. That is the whole surface of this skill. Keys never change; only values do. If there is no table and no audio, this is the wrong skill.

## Quick Start (Python)

```python
from sarvamai import SarvamAI
from sarvamai.play import save

client = SarvamAI()

# 1. translate one entry — keep placeholders intact, verify them after
response = client.text.translate(
    input="Deal {damage} damage to {target}.",
    source_language_code="en-IN",
    target_language_code="hi-IN",
    model="mayura:v1",
    mode="modern-colloquial",
)
line = response.translated_text
assert line.count("{") == 2, "placeholder lost — retry once, then keep the source"

# 2. voice it — one persona per NPC, pinned per language
audio = client.text_to_speech.convert(
    text=line,
    language_code="hi-IN",
    model="bulbul:v4-flash",
    speaker="aparna_hi_customer",
    output_audio_codec="wav",
)
save(audio, "audio/hi-IN/q_ashfields_intro_01.wav")
```

## Quick Start (JavaScript/TypeScript)

```typescript
import { SarvamAIClient } from "sarvamai";

const client = new SarvamAIClient({ apiSubscriptionKey: process.env.SARVAM_API_KEY! });

const { translated_text } = await client.text.translate({
    input: "Deal {damage} damage to {target}.",
    source_language_code: "en-IN",
    target_language_code: "hi-IN",
    model: "mayura:v1",
    mode: "modern-colloquial",
});

if ((translated_text.match(/\{/g) ?? []).length !== 2) {
    throw new Error("placeholder lost — retry once, then keep the source");
}

const audio = await client.textToSpeech.convert({
    text: translated_text,
    language_code: "hi-IN",
    model: "bulbul:v4-flash",
    speaker: "aparna_hi_customer",
    output_audio_codec: "wav",
});
```

## The three contracts that break

**Placeholders.** `{damage}`, `%s`, `<color=#FF0000>`. Send the line with tokens intact, then verify every token survived; retry once; if it still fails, keep the source string and flag the key. Never ship a line whose placeholder count changed. Never split a line at a placeholder to work around it.

**Limits.** 2,000 characters per request on `sarvam-translate:v1`, 1,000 on `mayura:v1`; over-limit is a 422. Split at sentence boundaries, rejoin with a single space, and flag anything longer than three chunks — a codex entry translated in four independent pieces drifts in register and pronoun.

**Register.** Translating 400 keys independently produces 400 slightly different voices. Group by speaker and hold `mode` and `speaker_gender` constant across that speaker's lines. `speaker_gender` works on both models and is the cheapest way to stop a female persona reading a line with masculine first-person agreement.

## Privacy

Only the string value is transmitted. The `context` and `speaker` fields stay on your machine — they exist for the human reviewer and for grouping, not for the request. Never put a key, a player identifier or an unreleased plot beat in `text`; that field is the one that leaves.

## Cost

Every key is one request. Cache on a hash of the text plus every parameter, so editing three lines re-bills three lines. Bound concurrency; do not open 400 sockets.

## Gotchas

| Gotcha | Detail |
|--------|--------|
| **Method name** | `client.text.translate(...)` in both SDKs — NOT `client.translate.translate()`. |
| **Colloquial modes are Mayura-only** | `sarvam-translate:v1` supports `mode="formal"` only. `modern-colloquial`, `classic-colloquial` and `code-mixed` require `mayura:v1`. |
| **`output_script` on sarvam-translate** | Not supported — `mayura:v1` only. Sending it is a hard 400 today, not a silent ignore. |
| **`source_language_code="auto"`** | `mayura:v1` only. `sarvam-translate:v1` needs an explicit source language. |
| **Character limits** | 2,000 (`sarvam-translate:v1`) / 1,000 (`mayura:v1`). Over-limit returns 422, not a truncated result. |
| **Placeholders are not preserved** | The API makes no guarantee. Verify after the call — this is the bug that ships. |
| **Omitting `model` on TTS silently gives v3** | v3 short names then work and v4 persona IDs fail. Always pass `model="bulbul:v4-flash"`. |
| **v3 short names on v4-flash** | `shubh`, `priya`, `ishita`, `anushka` return 400 on `bulbul:v4-flash`. Use `voice_language_style` IDs. |
| **No v4 personas for Malayalam or Odia** | `ml-IN` and `od-IN` need `model="bulbul:v3"` with a v3 short name. |
| **Default speaker** | Omitting `speaker` selects `shubh_enhi_ads` — a code-mixed ad read, not an NPC voice. Always set it. |
| **Persona roster drifts** | Sarvam renamed voices on 2026-10-06 and the old IDs now 400. Pin the live list in `personas.json`; do not hardcode from memory. |
| **Odia language code** | `od-IN`, never `or-IN`. |
| **`convert` vs `convert_stream`** | `convert(...)` returns a response for `save()`; `convert_stream(...)` yields chunks you join yourself. |
| **Param ranges** | Out-of-range `pitch` / `pace` / `loudness` returns 400. Get variety from persona choice, not extreme pitch. |

## Bundled files

- `scripts/localize_table.py` — batch translate with placeholder verification, chunking, retry and a disk cache. `--dry-run` needs no API key and no network.
- `scripts/voice_lines.py` — batch TTS into per-key WAVs with a persona map and the same caching. `--dry-run` validates personas before any spend.
- `references/string-table.md` — table schema, placeholder classes, the chunking algorithm, the review artifact.
- `references/voice-pipeline.md` — persona rules, per-NPC consistency, engine import notes for Godot, Unity and Unreal.

Both scripts are optional. The corrections above are the skill; the scripts are a worked implementation you can delete without losing anything.

## Full Docs

- **https://docs.sarvam.ai/llms.txt** — index for everything routed out of this skill: full parameter tables, the live voice catalog, language codes, rate limits
- [Text translation guide](https://docs.sarvam.ai/api/api-guides-tutorials/text-processing/translation)
- [Text-to-speech guide](https://docs.sarvam.ai/api/api-guides-tutorials/text-to-speech/overview)
- [Rate limits](https://docs.sarvam.ai/api/ratelimits)
