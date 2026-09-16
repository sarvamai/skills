---
name: text-to-speech
description: >-
  Write correct Sarvam Bulbul TTS code — REST, HTTP stream, WebSocket,
  pronunciation dictionaries, and v3 parameter traps (pitch/loudness
  ranges, temperature, speaker compatibility). Use this skill when
  generating speech in an app with Python or JS/TS. For live TTS in chat
  via MCP, use sarvam-mcp instead.
license: Apache-2.0
metadata:
  author: sarvam-ai
  version: "3.6"
---

# Text-to-Speech — Bulbul

> Live in-chat TTS → [sarvam-mcp](../sarvam-mcp) (`sarvam_tools_tts_*`). This skill = **SDK code**.

> [!IMPORTANT]
> Auth: `api-subscription-key` header — NOT `Authorization: Bearer`. Base URL: `https://api.sarvam.ai` (NOT `/v1` — that prefix is only for the OpenAI-compatible chat endpoint)
> SDK floor for the code below: Python `sarvamai>=0.1.29`, JS `sarvamai@>=1.1.8`. On older versions the TTS param is `target_language_code` — see Gotchas. Confirmed live against installed SDK `sarvamai==0.1.32`: passing `target_language_code` to `client.text_to_speech.convert()` raises `TypeError: got an unexpected keyword argument 'target_language_code'`.

## Model

`bulbul:v3` — 11 languages, 37 named voices, default speaker `shubh`, REST/HTTP stream/WebSocket. Confirmed live by requesting an invalid speaker and reading the full list back from the 400 error.

## Quick Start (Python)

```python
from sarvamai import SarvamAI
from sarvamai.play import save

client = SarvamAI()

response = client.text_to_speech.convert(
    text="नमस्ते, आप कैसे हैं?",
    language_code="hi-IN",
    model="bulbul:v3",
    speaker="shubh"
)
save(response, "output.wav")

# HTTP Stream (lower latency, binary audio)
chunks = []
for chunk in client.text_to_speech.convert_stream(
    text="Hello from Sarvam AI",
    language_code="en-IN",
    speaker="shubh",
    model="bulbul:v3"
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
    model: "bulbul:v3",
    speaker: "shubh"
});

// HTTP Stream (lower latency, returns BinaryResponse)
const streamResponse = await client.textToSpeech.convertStream({
    text: "Hello from Sarvam AI",
    language_code: "en-IN",
    speaker: "shubh",
    model: "bulbul:v3"
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
    async with client.text_to_speech_streaming.connect(model="bulbul:v3") as ws:
        await ws.configure(target_language_code="hi-IN", speaker="shubh")
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
| **WebSocket** | 2,500 chars/msg (keep <500 for lowest latency; send many messages per connection) |

## Gotchas

| Gotcha | Detail |
|--------|--------|
| **`language_code` is version-gated** | Python `>=0.1.29` and JS `>=1.1.8` (both 2026-08-03) take `language_code`; earlier versions take `target_language_code`. Hard rename — no alias, no deprecation shim, and the JSON body key changed too, so the wrong name raises `TypeError` before any request goes out. Check with `pip show sarvamai` / `npm ls sarvamai` if you hit that. |
| **WebSocket was not renamed** | Python `ws.configure()` still takes `target_language_code` (mapped to `language_code` on the wire); JS `configureConnection()` takes `language_code`. REST and WebSocket disagree inside the Python SDK. |
| **JS method name** | `client.textToSpeech.convert({...})` and `.convertStream({...})` — camelCase. Stream returns `BinaryResponse` with `.stream()`, `.bytes()`, `.blob()`. |
| **`pitch`/`loudness` now work on v3** | Reversed from earlier behavior — confirmed live: `pitch` must be in **-0.5 to 0.5** (not the SDK's wider -1..1 validation range — values outside -0.5..0.5 return a 400 from the API), `loudness` must be in **0.1 to 2.5** (SDK allows up to 3, API rejects above 2.5). `pace` remains 0.5–2.0. All three measurably change the output audio. |
| **v2 voices incompatible with v3** | Confirmed live: `anushka` on `bulbul:v3` returns 400 "Speaker 'anushka' is not compatible with model bulbul:v3" and lists the current 37 valid v3 speakers. Use `shubh` (default) or another v3-listed name. |
| **Sample rate >24kHz** | 32kHz, 44.1kHz, 48kHz only via REST, not streaming. |
| **REST response** | Base64-encoded audio in `response.audios[0]`. Use `sarvamai.play.save()` or `base64.b64decode()`. |
| **No SSML** | SSML markup is NOT supported. Use `pace`, `pitch`, `loudness`, and `temperature` for control, plus the pronunciation dictionary for word-level fixes. |
| **`temperature` param** | Controls expressiveness/prosodic variation, range 0.01–1.0. Lower (0.01–0.2) = flat, consistent delivery (good for accessibility); higher (0.9–1.0) = more natural, expressive variation. Confirmed live (accepted by the API on v3). |
| **Use native script** | Romanized Indic input ("Aapka order confirm ho gaya hai") degrades quality. Write Indic words in native script. |
| **Pronunciation dictionary** | `dict_id` param teaches custom word pronunciations (bulbul:v3 only). Limits: 10 dictionaries/user, 100 words/dictionary, 1MB file size, 1 dictionary per TTS request. Create via Python `client.pronunciation_dictionary.create(file=f)`. JS SDK upload is reported broken (missing multipart `Content-Type`) — not independently re-verified this pass; if hit, use raw `fetch` + `FormData` with an explicit `Blob` type. |

## Rate Limits (requests/min, Starter/Pro/Business — WebSocket is concurrent connections)

| API | Model | Starter | Pro | Business |
|-----|-------|---------|-----|----------|
| REST | default | 60 | 200 | 1,000 |
| REST | bulbul:v3 | 30 | 200 | 1,000 |
| WebSocket | default | 60 | 200 | 1,000 |
| WebSocket | bulbul:v3 | 30 | 200 | 1,000 |

## Full Docs

Fetch voice catalog, streaming protocol, pronunciation dictionary CRUD, and codec options from:

- **https://docs.sarvam.ai/llms.txt** — comprehensive docs index
- [TTS Overview](https://docs.sarvam.ai/api/api-guides-tutorials/text-to-speech/overview)
- [Voice Catalog](https://docs.sarvam.ai/api/api-guides-tutorials/text-to-speech/how-to/change-the-speaker-voice)
- [HTTP Stream](https://docs.sarvam.ai/api/api-guides-tutorials/text-to-speech/streaming-api/http-stream)
- [Pronunciation Dictionary](https://docs.sarvam.ai/api/api-guides-tutorials/text-to-speech/pronunciation-dictionary)
- [Rate Limits](https://docs.sarvam.ai/api/getting-started/ratelimits)
