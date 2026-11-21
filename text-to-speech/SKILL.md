---
name: text-to-speech
description: >-
  Write correct Sarvam Bulbul TTS code — bulbul:v4-flash persona speaker IDs
  (voice_language_style), REST, HTTP stream, WebSocket, pronunciation
  dictionaries, and v3/v4 traps (short names rejected on v4, param ranges).
  Use this skill when generating speech in an app with Python or JS/TS. For
  live TTS in chat via MCP, use sarvam-mcp instead.
license: Apache-2.0
metadata:
  author: sarvam-ai
  version: "4.1"
---

# Text-to-Speech — Bulbul

> Live in-chat TTS → [sarvam-mcp](../sarvam-mcp) (`sarvam_tools_tts_*`). This skill = **SDK code**.

> [!IMPORTANT]
> Auth: `api-subscription-key` header — NOT `Authorization: Bearer`. Base URL: `https://api.sarvam.ai` (NOT `/v1` — that prefix is only for the OpenAI-compatible chat endpoint)
> SDK floor for the code below: Python `sarvamai>=0.1.29`, JS `sarvamai@>=1.1.8`. On older versions the TTS param is `target_language_code` — see Gotchas.

## Model

`bulbul:v4-flash` — latest, use this for new integrations. Same REST / HTTP stream / WebSocket contract as v3. **200+ persona voices (222 IDs).**

`bulbul:v3` — what the API uses when `model` is omitted. Short names (`shubh`, `priya`). Still the right model for Malayalam and Odia, which have no v4 personas yet.

## Speakers (v4 Flash)

IDs are lowercase `voice_language_style`: `aparna_hi_customer`, `simran_en_customer`, `shubh_enhi_ads`. Omit `speaker` and the default is `shubh_enhi_ads`. v2/v3 short names (`shubh`, `priya`, `ishita`, `anushka`) return 400.

The middle token is a language tag (`hi`, `en`, `bn`, `gu`, `kn`, `mr`, `pa`, `ta`, `te`) or `enhi` for English–Hindi code-mix. Use an `_enhi_` persona when one utterance is genuinely mixed; a few English loanwords in Hindi script do not need it.

`language_code` still takes the usual BCP-47 values (`hi-IN`, `en-IN`, … including `ml-IN` and `od-IN`). There are no `ml` or `od` persona IDs — for those languages set `model="bulbul:v3"` and a v3 short name.

| Use case | Hindi | English |
|----------|-------|---------|
| Customer care | `aparna_hi_customer` | `aparna_en_companion` |
| Sales | `aparna_hi_customer`, `shubh_hi_customer` | `simran_en_sales` |
| Collections | `simran_hi_recovery` | `shubh_en_recovery` |
| Hinglish (one utterance) | `simran_enhi_customer` | — |

Do not copy `speaker="ishita"` from the Voices “generate your own sample” snippet — that is a v3 short name and fails on v4-flash.

**Coverage by language** (live-verified 2026-10-06; one working persona each — pick others from the live list):

| Language | Example persona | Language | Example persona |
|----------|-----------------|----------|-----------------|
| `en-IN` | `simran_en_customer`, `sunny_en_social` | `mr-IN` | `ishita_mr_conversational` |
| `hi-IN` | `aparna_hi_customer`, `shubh_hi_customer` | `gu-IN` | `bhavik_gu_conversation` |
| `hi-IN` (Hinglish) | `shubh_enhi_ads` (the default) | `kn-IN` | `chaitra_kn_conversation` |
| `bn-IN` | `roopa_bn_conversational`, `arnab_bn_conversation` | `pa-IN` | `anand_pa_conversation` |
| `ta-IN` | `gokul_ta_narration`, `aravind_ta_ads` | `te-IN` | `kavitha_te_conversation` |

**The roster changes.** Sarvam renamed voices on 2026-10-06 (`bappa_bn_conversation` → `arnab_bn_conversation`, `vetri_ta_ads`/`vetri_ta_suspense` → `aravind_ta_*`), and the old IDs now 400. Do not hardcode IDs from memory or old blog posts. An unknown speaker returns 400 with the full live list, so the list is one bad request away. The API also lists 2 Assamese (`_as_`) personas that the docs catalog does not.

## Quick Start (Python)

```python
from sarvamai import SarvamAI
from sarvamai.play import save

client = SarvamAI()

response = client.text_to_speech.convert(
    text="नमस्ते, आप कैसे हैं?",
    language_code="hi-IN",
    model="bulbul:v4-flash",
    speaker="aparna_hi_customer",
    enable_preprocessing=True,
)
save(response, "output.wav")

# HTTP Stream (lower latency, binary audio)
chunks = []
for chunk in client.text_to_speech.convert_stream(
    text="Hello from Sarvam AI",
    language_code="en-IN",
    model="bulbul:v4-flash",
    speaker="simran_en_customer",
    output_audio_codec="wav",
):
    chunks.append(chunk)
audio = b"".join(chunks)
```

## Quick Start (JavaScript/TypeScript)

```typescript
import { SarvamAIClient } from "sarvamai";
import { writeFile } from "fs/promises";

const client = new SarvamAIClient({ apiSubscriptionKey: "YOUR_SARVAM_API_KEY" });

// REST
const response = await client.textToSpeech.convert({
    text: "नमस्ते, आप कैसे हैं?",
    language_code: "hi-IN",
    model: "bulbul:v4-flash",
    speaker: "aparna_hi_customer",
    enable_preprocessing: true,
});

// HTTP Stream (lower latency, returns BinaryResponse)
const streamResponse = await client.textToSpeech.convertStream({
    text: "Hello from Sarvam AI",
    language_code: "en-IN",
    model: "bulbul:v4-flash",
    speaker: "simran_en_customer",
    output_audio_codec: "wav",
});
const bytes = await streamResponse.bytes();
await writeFile("output.wav", bytes);
```

## WebSocket Streaming

```python
import asyncio
from sarvamai import AsyncSarvamAI

async def tts_stream():
    client = AsyncSarvamAI()
    async with client.text_to_speech_streaming.connect(model="bulbul:v4-flash") as ws:
        await ws.configure(
            target_language_code="hi-IN",
            speaker="aparna_hi_customer",
            output_audio_codec="wav",
        )
        await ws.convert("Your text here")
        await ws.flush()
        async for message in ws:
            pass  # base64 audio chunks

asyncio.run(tts_stream())
```

## Character Limits

| Method | Max Text |
|--------|----------|
| **REST** (`convert`) | 2,500 chars |
| **HTTP Stream** (`convert_stream`) | 3,500 chars |
| **Legacy `inputs` array** (raw REST) | 500 chars per item — send `text` instead to get the 2,500 limit |
| **WebSocket** | 2,500 chars/msg (keep <500 for lowest latency; send many messages per connection) |

## Gotchas

| Gotcha | Detail |
|--------|--------|
| **Set `model` or you get v3** | Omitting `model` selects `bulbul:v3`. v3 short names then work; v4 persona IDs do not. New code sets `model="bulbul:v4-flash"`. |
| **v3/v2 short names on v4** | `shubh`, `priya`, `ishita`, `anushka`, etc. are rejected. Use `voice_language_style`. Unknown IDs 400 with the live speaker list. |
| **`language_code` is version-gated** | Python `>=0.1.29` and JS `>=1.1.8` (both 2026-08-03) take `language_code`; earlier versions take `target_language_code`. Hard rename — no alias, no deprecation shim, and the JSON body key changed too, so the wrong name raises `TypeError` before any request goes out. Check with `pip show sarvamai` / `npm ls sarvamai` if you hit that. |
| **WebSocket was not renamed** | Python `ws.configure()` still takes `target_language_code` (mapped to `language_code` on the wire). Docs that pass `language_code=` into `ws.configure()` raise `TypeError`. JS `configureConnection()` takes `language_code`. |
| **JS method name** | `client.textToSpeech.convert({...})` and `.convertStream({...})` — camelCase. Stream returns `BinaryResponse` with `.stream()`, `.bytes()`, `.blob()`. |
| **`pitch` / `loudness` ranges** | `pitch` −0.5–0.5 (default 0), `loudness` 0.1–2.5 (default 1), `pace` 0.5–2.0. Out-of-range values return 400. Bulbul v3 used to reject `pitch` / `loudness`; as of 2026-10-06 it accepts them too (live-verified). v2-only ranges in the model-page limits table do not apply. |
| **Streaming codec default** | HTTP stream and WebSocket do not default to WAV. Set `output_audio_codec` (`wav` or `mp3`; also `flac` / `aac` on HTTP stream). `opus` can appear in the schema and currently errors on `/text-to-speech`. |
| **Sample rate** | `speech_sample_rate` 8000, 16000, 24000 and 48000 verified on v4-flash REST (the returned WAV matches the requested rate). |
| **Sample rate >24kHz** | 32kHz, 44.1kHz, 48kHz only via REST, not streaming. Omitted → 22050 Hz. |
| **REST response** | Base64-encoded audio in `response.audios[0]`. Use `sarvamai.play.save()` or `base64.b64decode()`. Writing the raw base64 string to disk is not playable audio. |
| **Speaker must match model** | The mismatch fails both ways: a v3 short name on `bulbul:v4-flash` and a v4 persona on `bulbul:v3` both return 400. Pair `model` and `speaker` explicitly. |
| **No SSML** | SSML markup is NOT supported. Use `pace` (and on v4, `pitch` / `loudness`) plus sentence-boundary chunking. |
| **Use native script** | Romanized Indic input ("Aapka order confirm ho gaya hai") degrades quality. Write Indic words in native script; keep English loanwords in Latin (`"आपका order confirm हो गया है"`). With `enable_preprocessing=true`, do not hand-expand numbers, dates, or currency. |
| **`ml-IN` / `od-IN` have no v4 personas** | Codes are accepted. The catalog has no Malayalam or Odia IDs. Use `bulbul:v3` for those languages. |
| **Pronunciation dictionary** | Pass `dict_id` on v4-flash the same way as v3 (10 dicts/user, 100 words/dict). Create via Python `client.pronunciation_dictionary.create(file=f)`. JS SDK upload is broken (missing multipart `Content-Type`) — use raw `fetch` + `FormData` with an explicit `Blob` type. The pronunciation-page limits row that says “v3 only” is stale; the examples on that page send `dict_id` with `bulbul:v4-flash`. |

## Full Docs

Fetch the voice catalog, ranked picks, streaming protocol, and codec options from:

- **https://docs.sarvam.ai/llms.txt** — comprehensive docs index
- [Bulbul models](https://docs.sarvam.ai/api/getting-started/models/bulbul)
- [Voices (v4 catalog + v3 previews)](https://docs.sarvam.ai/api/api-guides-tutorials/text-to-speech/voices)
- [Bulbul v4 Flash best practices](https://docs.sarvam.ai/api/api-guides-tutorials/text-to-speech/best-practice-guide-for-bulbul-v-4-flash)
- [TTS Overview](https://docs.sarvam.ai/api/api-guides-tutorials/text-to-speech/overview)
- [HTTP Stream](https://docs.sarvam.ai/api/api-guides-tutorials/text-to-speech/streaming-api/http-stream)
- [Pronunciation Dictionary](https://docs.sarvam.ai/api/api-guides-tutorials/text-to-speech/pronunciation-dictionary)
- [Rate Limits](https://docs.sarvam.ai/api/ratelimits)
