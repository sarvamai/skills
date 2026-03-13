---
name: speech-to-text
description: Transcribe audio to text using Sarvam AI's Saaras model. Handles speech recognition, transcription, and voice interfaces for 23 Indian languages. Supports 5 output modes, auto language detection, WebSocket streaming, and batch diarization. Use when converting speech to text or building voice-enabled apps.
license: Apache-2.0
metadata:
  author: sarvam-ai
  version: "3.0"
---

# Speech-to-Text — Saaras

> [!IMPORTANT]
> Auth: `api-subscription-key` header — NOT `Authorization: Bearer`. Base URL: `https://api.sarvam.ai/v1`

## Model

`saaras:v3` — 23 languages, 5 output modes (`transcribe`, `translate`, `verbatim`, `translit`, `codemix`), auto language detection.

## Quick Start (Python)

```python
from sarvamai import SarvamAI
client = SarvamAI()

response = client.speech_to_text.transcribe(
    file=open("audio.wav", "rb"),
    model="saaras:v3",
    mode="transcribe"
)
print(response.transcript)
```

## Quick Start (JavaScript/TypeScript)

```typescript
import { SarvamAIClient } from "sarvamai";
import * as fs from "fs";

const client = new SarvamAIClient({ apiSubscriptionKey: "YOUR_SARVAM_API_KEY" });

const response = await client.speechToText.transcribe({
    file: fs.createReadStream("audio.wav"),
    model: "saaras:v3",
    mode: "transcribe"
});
console.log(response.transcript);
```

## Batch API (Long Audio + Diarization)

```python
job = client.speech_to_text_job.create_job(
    model="saaras:v3",
    mode="transcribe",
    language_code="hi-IN",
    with_diarization=True,
    num_speakers=2
)
job.upload_files(file_paths=["meeting.mp3"])
job.start()
job.wait_until_complete()
job.download_outputs(output_dir="./output")
```

Supports audio up to 1 hour, up to 8 speakers, all 5 output modes.

## WebSocket Streaming

```python
import asyncio, base64
from sarvamai import AsyncSarvamAI

async def stream_audio():
    client = AsyncSarvamAI()
    async with client.speech_to_text_streaming.connect(
        model="saaras:v3",
        high_vad_sensitivity=True,
        flush_signal=True
    ) as ws:
        with open("audio.wav", "rb") as f:
            audio_base64 = base64.b64encode(f.read()).decode("utf-8")
        await ws.transcribe(audio=audio_base64, encoding="audio/wav", sample_rate=16000)
        await ws.flush()
        response = await ws.recv()
        print(response)

asyncio.run(stream_audio())
```

Supports sessions up to 8 hours. Use `sample_rate=8000` for telephony audio.

## Gotchas

| Gotcha | Detail |
|--------|--------|
| **REST: 30s limit** | Audio >30s fails. Use Batch API or WebSocket for longer files. |
| **JS method name** | `client.speechToText.transcribe({...})` — camelCase, NOT `speech_to_text`. File via `fs.createReadStream()`. |
| **WebSocket codecs** | Only `wav`, `pcm_s16le`, `pcm_l16`, `pcm_raw`. MP3/AAC/OGG NOT supported for streaming. |
| **WebSocket audio** | Must be **base64-encoded**. Use `sample_rate=8000` for telephony audio. |
| **Flush signal** | `flush_signal=True` + `await ws.flush()` forces immediate transcription boundary. |
| **Short audio detection** | Set `language_code` explicitly for audio <3 seconds — auto-detection needs more signal. |

## Full Docs

Fetch streaming protocol, batch API SDK examples, and codec details from:

- **https://docs.sarvam.ai/llms.txt** — comprehensive docs index
- [STT Overview](https://docs.sarvam.ai/api-reference-docs/api-guides-tutorials/speech-to-text/overview)
- [Streaming API](https://docs.sarvam.ai/api-reference-docs/api-guides-tutorials/speech-to-text/streaming-api)
- [Batch API + Diarization](https://docs.sarvam.ai/api-reference-docs/api-guides-tutorials/speech-to-text/batch-api)
- [Rate Limits](https://docs.sarvam.ai/api-reference-docs/ratelimits)
