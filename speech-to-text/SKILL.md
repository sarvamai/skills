---
name: speech-to-text
description: >-
  Write correct Sarvam Saaras STT code for 23 Indic languages — REST modes,
  Batch API with diarization, standard WebSocket streaming, and the newer
  low-latency saaras:v3-realtime streaming API. Use this skill when building
  transcription or voice apps in Python or JS/TS. For live transcription in
  chat via MCP, use sarvam-mcp instead.
license: Apache-2.0
metadata:
  author: sarvam-ai
  version: "3.5"
---

# Speech-to-Text — Saaras

> Live in-chat transcription → [sarvam-mcp](../sarvam-mcp) (`sarvam_tools_stt_*`). This skill = **SDK code**.

> [!IMPORTANT]
> Auth: `api-subscription-key` header — NOT `Authorization: Bearer`. Base URL: `https://api.sarvam.ai` (NOT `/v1` — that prefix is only for the OpenAI-compatible chat endpoint)

## Model

`saaras:v3` — 23 languages, 5 output modes (`transcribe`, `translate`, `verbatim`, `translit`, `codemix`), auto language detection. `saaras:v4` is also available in both SDKs.

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

Supports audio up to 2 hours per file, up to 20 files per job, up to 20 speakers (`num_speakers`), all 5 output modes.

## WebSocket Streaming (`saaras:v3`/`v4`)

```python
import asyncio, base64
from sarvamai import AsyncSarvamAI

async def stream_audio():
    client = AsyncSarvamAI()
    async with client.speech_to_text_streaming.connect(
        language_code="unknown",  # required — "unknown" auto-detects, or pass e.g. "hi-IN"
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

No fixed session duration limit — but the connection closes after **60 seconds of inactivity**. Use `sample_rate=8000` for telephony audio.

## Real-Time Streaming (`saaras:v3-realtime`)

A **separate** WebSocket API and model family (`/speech-to-text-realtime/ws`), not a version bump of the streaming API above — different protocol, different socket methods, different config knobs. Built for lowest-latency conversational/voice-agent use cases (`stream_type="fast"` trades accuracy for latency).

```python
import asyncio, base64
from sarvamai import AsyncSarvamAI, RealtimeAudioInput, RealtimeFlush

async def stream_realtime():
    client = AsyncSarvamAI()
    async with client.speech_to_text_realtime_streaming.connect(
        language_code="auto",   # required — "auto" auto-detects (NOT "unknown")
        model="saaras:v3-realtime",
        stream_type="fast",     # "fast" | "balanced" (default) | "simulated"
        endpointing="vad"       # "vad" (default, server-side turn detection) | "manual"
    ) as ws:
        with open("audio.wav", "rb") as f:
            audio_base64 = base64.b64encode(f.read()).decode("utf-8")
        await ws.send_realtime_audio_input(RealtimeAudioInput(audio=audio_base64))
        await ws.send_realtime_flush(RealtimeFlush())
        response = await ws.recv()
        print(response)

asyncio.run(stream_realtime())
```

There's no bare `.transcribe(audio=...)` convenience here — every message is a typed object (`RealtimeAudioInput`, `RealtimeSpeechStart`, `RealtimeSpeechEnd`, `RealtimeFlush`, `RealtimeConfigUpdate`, `RealtimeEnd`, `RealtimePing`), sent via `send_realtime_*` methods (`sendRealtime*` in JS/TS). `recv()` returns one of a 9-member discriminated union (`session.begin`, `transcript.partial`, `transcript.final`, VAD events, `pong`, `session.end`, `error`) instead of a single response shape.

## Gotchas

| Gotcha | Detail |
|--------|--------|
| **REST: 30s limit** | Audio >30s fails. Use Batch API or WebSocket for longer files. |
| **`connect()` requires `language_code`** | It's a required keyword arg with no default on both SDKs — omitting it raises immediately. |
| **Auto-detect sentinel differs by module** | `speech_to_text_streaming` uses `language_code="unknown"` for auto-detect; `speech_to_text_realtime_streaming` uses `"auto"`. Both type-check for either value (the type falls back to `Any`), but the wrong sentinel gets rejected by the live connection — match it to the module you're calling. |
| **JS method name** | `client.speechToText.transcribe({...})` — camelCase, NOT `speech_to_text`. File via `fs.createReadStream()`. |
| **WebSocket codecs** | Only `wav`, `pcm_s16le`, `pcm_l16`, `pcm_raw`. MP3/AAC/OGG NOT supported for streaming. PCM input is 16kHz only. |
| **WebSocket audio** | Must be **base64-encoded**. Use `sample_rate=8000` for telephony audio. |
| **WebSocket idle timeout** | Connection closes after **60s of inactivity**. For long-running sessions, send periodic silent (near-zero amplitude) audio chunks as keep-alive. |
| **Flush signal** | `flush_signal=True` + `await ws.flush()` forces immediate transcription boundary. |
| **VAD events** | `vad_signals=True` emits `START_SPEECH`/`END_SPEECH` events alongside transcripts. `high_vad_sensitivity=True` for automatic end-of-speech detection. |
| **Short audio detection** | Set `language_code` explicitly for audio <3 seconds — auto-detection needs more signal. |
| **Realtime `mode` applies to finals only** | `mode` (`transcribe`/`translate`/etc.) on `speech_to_text_realtime_streaming` affects only `transcript.final` — partials are always plain transcription regardless of `mode`. |
| **Realtime `sample_rate`** | Only `"8000"` or `"16000"` (strings). Any other value closes the connection with code `4000`. |

## Full Docs

Fetch streaming protocol, batch API SDK examples, and codec details from:

- **https://docs.sarvam.ai/llms.txt** — comprehensive docs index
- [STT Overview](https://docs.sarvam.ai/api/api-guides-tutorials/speech-to-text/overview)
- [Streaming API](https://docs.sarvam.ai/api/api-guides-tutorials/speech-to-text/streaming-api)
- [Realtime Streaming API Reference](https://docs.sarvam.ai/api-reference/speech-to-text/transcribe/realtime/ws)
- [Batch API + Diarization](https://docs.sarvam.ai/api/api-guides-tutorials/speech-to-text/batch-api)
- [Rate Limits](https://docs.sarvam.ai/api/ratelimits)
