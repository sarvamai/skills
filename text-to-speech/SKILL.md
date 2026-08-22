---
name: text-to-speech
description: >-
  Write correct Sarvam Bulbul TTS code — REST, HTTP stream, WebSocket,
  pronunciation dictionaries, and v3 parameter traps (pitch/loudness,
  speaker compatibility). Use this skill when generating speech in an app
  with Python or JS/TS. For live TTS in chat via MCP, use sarvam-mcp instead.
license: Apache-2.0
metadata:
  author: sarvam-ai
  version: "3.4"
---

# Text-to-Speech — Bulbul

> Live in-chat TTS → [sarvam-mcp](../sarvam-mcp) (`sarvam_tools_tts_*`). This skill = **SDK code**.

> [!IMPORTANT]
> Auth: `api-subscription-key` header — NOT `Authorization: Bearer`. Base URL: `https://api.sarvam.ai` (NOT `/v1` — that prefix is only for the OpenAI-compatible chat endpoint)
> SDK floor for the code below: Python `sarvamai>=0.1.29`, JS `sarvamai@>=1.1.8`. On older versions the TTS param is `target_language_code` — see Gotchas.

## Model

`bulbul:v3` — 11 languages, 37 voices (23 male, 14 female; default: `shubh`), REST/HTTP stream/WebSocket.

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
| **`pitch`/`loudness` rejected** | SDK accepts these but API returns 400 for v3. Only `pace` (0.5–2.0) works. |
| **v2 voices incompatible** | `anushka`, `abhilash`, `arya`, etc. don't work with v3. Use `shubh` (default). |
| **Sample rate >24kHz** | 32kHz, 44.1kHz, 48kHz only via REST, not streaming. |
| **REST response** | Base64-encoded audio in `response.audios[0]`. Use `sarvamai.play.save()` or `base64.b64decode()`. |
| **No SSML** | SSML markup is NOT supported. Use `pace` for speed control and the pronunciation dictionary for word-level fixes. |
| **Use native script** | Romanized Indic input ("Aapka order confirm ho gaya hai") degrades quality. Write Indic words in native script. |
| **Pronunciation dictionary** | `dict_id` param teaches custom word pronunciations (bulbul:v3 only; 10 dicts/user, 100 words/dict). Create via Python `client.pronunciation_dictionary.create(file=f)`. JS SDK upload is broken (missing multipart `Content-Type`) — use raw `fetch` + `FormData` with an explicit `Blob` type. |

## Full Docs

Fetch voice catalog, streaming protocol, pronunciation dictionary CRUD, and codec options from:

- **https://docs.sarvam.ai/llms.txt** — comprehensive docs index
- [TTS Overview](https://docs.sarvam.ai/api/api-guides-tutorials/text-to-speech/overview)
- [Voice Catalog](https://docs.sarvam.ai/api/api-guides-tutorials/text-to-speech/how-to/change-the-speaker-voice)
- [HTTP Stream](https://docs.sarvam.ai/api/api-guides-tutorials/text-to-speech/streaming-api/http-stream)
- [Pronunciation Dictionary](https://docs.sarvam.ai/api/api-guides-tutorials/text-to-speech/pronunciation-dictionary)
- [Rate Limits](https://docs.sarvam.ai/api/ratelimits)
