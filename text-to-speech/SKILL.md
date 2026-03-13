---
name: text-to-speech
description: Convert text to natural speech using Sarvam AI's Bulbul v3 model. Handles audio generation, voiceovers, and voice interfaces for 11 Indian languages with 30+ voices. Supports REST, HTTP streaming, WebSocket, and pronunciation dictionaries. Use when generating spoken audio from text.
license: Apache-2.0
metadata:
  author: sarvam-ai
  version: "3.0"
---

# Text-to-Speech — Bulbul

> [!IMPORTANT]
> Auth: `api-subscription-key` header — NOT `Authorization: Bearer`. Base URL: `https://api.sarvam.ai/v1`

## Model

`bulbul:v3` — 11 languages, 30+ voices (default: `shubh`), REST/HTTP stream/WebSocket.

## Quick Start (Python)

```python
from sarvamai import SarvamAI
from sarvamai.play import save

client = SarvamAI()

response = client.text_to_speech.convert(
    text="नमस्ते, आप कैसे हैं?",
    target_language_code="hi-IN",
    model="bulbul:v3",
    speaker="shubh"
)
save(response, "output.wav")

# HTTP Stream (lower latency, binary audio)
chunks = []
for chunk in client.text_to_speech.convert_stream(
    text="Hello from Sarvam AI",
    target_language_code="en-IN",
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
    target_language_code: "hi-IN",
    model: "bulbul:v3",
    speaker: "shubh"
});

// HTTP Stream (lower latency, returns BinaryResponse)
const streamResponse = await client.textToSpeech.convertStream({
    text: "Hello from Sarvam AI",
    target_language_code: "en-IN",
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
| **WebSocket** | 2,500 chars/msg |

## Gotchas

| Gotcha | Detail |
|--------|--------|
| **JS method name** | `client.textToSpeech.convert({...})` and `.convertStream({...})` — camelCase. Stream returns `BinaryResponse` with `.stream()`, `.bytes()`, `.blob()`. |
| **`pitch`/`loudness` rejected** | SDK accepts these but API returns 400 for v3. Only `pace` (0.5–2.0) works. |
| **v2 voices incompatible** | `anushka`, `abhilash`, `arya`, etc. don't work with v3. Use `shubh` (default). |
| **Sample rate >24kHz** | 32kHz, 44.1kHz, 48kHz only via REST, not streaming. |
| **REST response** | Base64-encoded audio in `response.audios[0]`. Use `sarvamai.play.save()` or `base64.b64decode()`. |
| **Pronunciation dictionary** | `dict_id` param teaches custom word pronunciations. Create via `client.pronunciation_dictionary.create(file=f)`. |

## Full Docs

Fetch voice catalog, streaming protocol, pronunciation dictionary CRUD, and codec options from:

- **https://docs.sarvam.ai/llms.txt** — comprehensive docs index
- [TTS Overview](https://docs.sarvam.ai/api-reference-docs/api-guides-tutorials/text-to-speech/overview)
- [Voice Catalog](https://docs.sarvam.ai/api-reference-docs/api-guides-tutorials/text-to-speech/how-to/change-the-speaker-voice)
- [HTTP Stream](https://docs.sarvam.ai/api-reference-docs/api-guides-tutorials/text-to-speech/streaming-api/http-stream)
- [Pronunciation Dictionary](https://docs.sarvam.ai/api-reference-docs/api-guides-tutorials/text-to-speech/pronunciation-dictionary)
- [Rate Limits](https://docs.sarvam.ai/api-reference-docs/ratelimits)
