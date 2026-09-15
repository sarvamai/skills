---
name: speech-to-text
description: >-
  Write correct Sarvam Saaras STT code for 23 Indic languages (saaras:v3 and
  v4) — REST modes, Batch API with diarization, and beta Realtime Streaming
  gotchas. Use this skill when building transcription or voice apps in
  Python or JS/TS. For live transcription in chat via MCP, use sarvam-mcp
  instead.
license: Apache-2.0
metadata:
  author: sarvam-ai
  version: "3.4"
---

# Speech-to-Text — Saaras

> Live in-chat transcription → [sarvam-mcp](../sarvam-mcp) (`sarvam_tools_stt_*`). This skill = **SDK code**.

> [!IMPORTANT]
> Auth: `api-subscription-key` header — NOT `Authorization: Bearer`. Base URL: `https://api.sarvam.ai` (NOT `/v1` — that prefix is only for the OpenAI-compatible chat endpoint)

## Model

`saaras:v3` — 23 languages, 5 output modes (`transcribe`, `translate`, `verbatim`, `translit`, `codemix`), auto language detection. Default, recommended for most use.

`saaras:v4` — latest. Adds Global English (in addition to Indian English) and Keyterm Prompting (up to 50 domain-specific terms to bias recognition). Same 5 output modes. Also accepted as a model for the Realtime Streaming WebSocket (see below). `saaras:v4-multispk` exists for multi-speaker REST transcription.

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

Supports audio up to 2 hours per file, up to 20 files per job, up to 20 speakers (`num_speakers`), all 5 output modes. Diarized output gives one timestamped entry per speaker turn — **chunk-level timestamps only, not word-level**.

## Realtime Streaming (beta, preferred for new voice-agent/live work)

```python
import asyncio
from sarvamai import AsyncSarvamAI

async def stream_audio():
    client = AsyncSarvamAI()
    async with client.speech_to_text_realtime_streaming.connect(
        model="saaras:v3-realtime",
        language_code="en-IN",
        encoding="linear16",
        sample_rate="16000"
    ) as ws:
        # send audio chunks via ws.send / equivalent, then read events
        async for event in ws:
            print(event)

asyncio.run(stream_audio())
```

Codecs: `linear16`, `linear32`, `mulaw`, `alaw` (mono only). Sample rate must be `8000` or `16000`; anything else closes the connection with code `4000`. VAD params: `threshold` (0.0–1.0, default 0.3), `silence_duration_ms` (default observed live as 1000ms, not the 500ms some docs pages state — verify against the `session.begin` event's echoed config before relying on an exact number), `min_speech_duration_ms` (default 250), `prefix_padding_ms` (default 300). Model accepts `saaras:v3-realtime` or plain `saaras:v4` — `saaras:v4-realtime` is not a valid model name despite appearing in some SDK type hints. Idle/inactivity closes with code `1008`; no fixed duration is documented, send periodic pings.

## Gotchas

| Gotcha | Detail |
|--------|--------|
| **REST: 30s limit** | Audio >30s fails. Use Batch API or Realtime Streaming for longer files. |
| **JS method name** | `client.speechToText.transcribe({...})` — camelCase, NOT `speech_to_text`. File via `fs.createReadStream()`. |
| **`saaras:v2.5` doesn't exist** | The old v2.5 model's API id is `saarika:v2.5`, not `saaras:v2.5` — passing `saaras:v2.5` fails validation. |
| **Idle timeout is not a fixed number** | No documented exact duration for the Realtime Streaming WebSocket. Send periodic keep-alive pings/audio rather than relying on a specific cutoff. |
| **VAD tuning** | Tune `threshold`/`silence_duration_ms`/`min_speech_duration_ms` for end-of-speech detection. |
| **Short audio detection** | Set `language_code` explicitly for audio <3 seconds — auto-detection needs more signal. |
| **Batch timestamps** | Diarized batch output gives chunk-level (per-turn) timestamps only, never word-level. |

## Rate Limits (requests/min unless noted, Starter/Pro/Business)

| API | Starter | Pro | Business |
|-----|---------|-----|----------|
| REST | 60 | 100 | 4,000 |
| WebSocket (concurrent connections) | 20 | 100 | 100 |
| Batch | 20 | 100 | 500 |

## Full Docs

Fetch streaming protocol, batch API SDK examples, and codec details from:

- **https://docs.sarvam.ai/llms.txt** — comprehensive docs index
- [STT Overview](https://docs.sarvam.ai/api/api-guides-tutorials/speech-to-text/overview)
- [Realtime Streaming](https://docs.sarvam.ai/api/api-guides-tutorials/speech-to-text/realtime-streaming)
- [Batch API + Diarization](https://docs.sarvam.ai/api/api-guides-tutorials/speech-to-text/batch-api)
- [Rate Limits](https://docs.sarvam.ai/api/getting-started/ratelimits)
