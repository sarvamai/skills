---
name: speech-to-text
description: >-
  Write correct Sarvam Saaras STT code for 23 Indic languages — REST modes,
  Batch API with diarization, and WebSocket streaming gotchas. Use this skill
  when building transcription or voice apps in Python or JS/TS. For live
  transcription in chat via MCP, use sarvam-mcp instead.
license: Apache-2.0
metadata:
  author: sarvam-ai
  version: "3.6"
---

# Speech-to-Text — Saaras

> Live in-chat transcription → [sarvam-mcp](../sarvam-mcp) (`sarvam_tools_stt_*`). This skill = **SDK code**.

> [!IMPORTANT]
> Auth: `api-subscription-key` header — NOT `Authorization: Bearer`. Base URL: `https://api.sarvam.ai` (NOT `/v1` — that prefix is only for the OpenAI-compatible chat endpoint)

## Model

`saaras:v3` (default, recommended) — 23 languages, 5 output modes (`transcribe`, `translate`, `verbatim`, `translit`, `codemix`), auto language detection.

`saaras:v4` (latest) — same modes/languages, plus Global English (not just Indian English) and **Keyterm Prompting**: pass `keyterms=["Sarvam", "New Delhi", ...]` (up to 50 terms, 64 chars each) on REST, Batch, or either WebSocket streaming endpoint to bias recognition toward domain-specific names/brands/terms. `keyterms` is `saaras:v4`-only — see Gotchas for a JS-specific caveat.

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

## WebSocket Streaming

```python
import asyncio, base64
from sarvamai import AsyncSarvamAI

async def stream_audio():
    client = AsyncSarvamAI()
    async with client.speech_to_text_streaming.connect(
        model="saaras:v3",
        language_code="hi-IN",   # required — connect() now rejects a missing language_code
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

Verified live: `connect()` currently raises `TypeError: ... missing 1 required keyword-only argument: 'language_code'` if you omit it — it is not optional in the installed SDK, despite not being marked required in some docs examples.

## Realtime Streaming (New — `saaras:v3-realtime` / `saaras:v4`)

A newer, separate WebSocket API — not a replacement for the "WebSocket Streaming" above, which still works. Use this one for true interim results and finer turn control.

```python
import asyncio, base64
from sarvamai import AsyncSarvamAI, RealtimeAudioInput, RealtimeEnd

async def transcribe(audio_chunks):
    client = AsyncSarvamAI()
    async with client.speech_to_text_realtime_streaming.connect(
        language_code="hi-IN",
        stream_type="fast",   # "fast" | "balanced" (default) | "simulated"
    ) as ws:
        async def send_audio():
            async for chunk in audio_chunks:
                await ws.send_realtime_audio_input(
                    RealtimeAudioInput(audio=base64.b64encode(chunk).decode("utf-8"))
                )
            await ws.send_realtime_end(RealtimeEnd())

        async def receive_events():
            async for message in ws:
                if message.event == "transcript.partial":
                    print(f"partial: {message.text}")
                elif message.event == "transcript.final":
                    print(f"final: {message.text}")
                elif message.event == "error":
                    print(f"error ({message.code}): {message.message}")

        await asyncio.gather(send_audio(), receive_events())
```

JS: `client.speechToTextRealtimeStreaming.connect({ language_code, stream_type })`, then `socket.sendRealtimeAudioInput({...})` / `socket.sendRealtimeEnd({...})`, with events on `socket.on("message", ...)`.

## Gotchas

| Gotcha | Detail |
|--------|--------|
| **REST: 30s limit** | Audio >30s fails. Use Batch API or WebSocket for longer files. |
| **JS method name** | `client.speechToText.transcribe({...})` — camelCase, NOT `speech_to_text`. File via `fs.createReadStream()`. |
| **WebSocket codecs** | Only `wav`, `pcm_s16le`, `pcm_l16`, `pcm_raw`. MP3/AAC/OGG NOT supported for streaming. PCM input is 16kHz only. |
| **WebSocket audio** | Must be **base64-encoded**. Use `sample_rate=8000` for telephony audio. |
| **WebSocket idle timeout** | Connection closes after **60s of inactivity**. For long-running sessions, send periodic silent (near-zero amplitude) audio chunks as keep-alive. |
| **Flush signal** | `flush_signal=True` + `await ws.flush()` forces immediate transcription boundary. |
| **VAD events** | `vad_signals=True` emits `START_SPEECH`/`END_SPEECH` events alongside transcripts. `high_vad_sensitivity=True` for automatic end-of-speech detection. |
| **Short audio detection** | Set `language_code` explicitly for audio <3 seconds — auto-detection needs more signal. |
| **`keyterms` is v4-only** | Accepted with `model="saaras:v4"` on REST, Batch, and **both** WebSocket streaming endpoints (legacy `/speech-to-text/ws` and realtime). Verified live: `saaras:v3` + `keyterms` returns `400` — `"'keyterms' is only supported by model 'saaras:v4', got 'saaras:v3'."` — a hard error, not a silent ignore. Format: JSON list of strings, max 50 terms, 64 chars each — don't use the older `keyterm`/`hotwords` fields. |
| **`keyterms` JS support** | Docs (as of this writing) say JS `speechToText.transcribe({..., keyterms})` hasn't shipped to npm, with only `speechToTextJob.createJob({..., keyterms})` (Batch) working. Verified live against `sarvamai@1.1.10`: REST `transcribe({..., keyterms})` **worked without error** — the docs note may already be stale. Don't trust either source blindly; the gap may be closed by the time you read this — test the actual call once. Python needs `sarvamai>=0.1.33a1` (REST) / `>=0.1.33a3` (Batch) either way. |
| **Realtime vs legacy streaming are different endpoints** | Legacy WebSocket (`/speech-to-text/ws`, `speech_to_text_streaming`) has no interim results and needs a reconnect to change params. Realtime (`/speech-to-text-realtime/ws`, `speech_to_text_realtime_streaming`) adds `transcript.partial` events, millisecond VAD params (`threshold`, `silence_duration_ms`, `min_speech_duration_ms`), and live `config.update` — don't mix the two APIs' parameter names. |
| **Realtime sample rate** | Only `8000` or `16000` Hz — any other value closes the connection with code `4000`. |
| **Errors & retries** | Errors return `{"error": {"message", "code", "request_id"}}`. Auth failures are **403**, not 401. The SDK already retries 429/5xx twice — raise `max_retries` / `maxRetries` instead of wrapping calls in your own loop. Full handling patterns: [errors](../errors) skill. |

## Full Docs

Fetch streaming protocol, batch API SDK examples, and codec details from:

- **https://docs.sarvam.ai/llms.txt** — comprehensive docs index
- [STT Overview](https://docs.sarvam.ai/api/api-guides-tutorials/speech-to-text/overview)
- [Streaming API (legacy)](https://docs.sarvam.ai/api/api-guides-tutorials/speech-to-text/streaming-api)
- [Realtime Streaming API](https://docs.sarvam.ai/api/api-guides-tutorials/speech-to-text/realtime-streaming)
- [Keyterm Prompting](https://docs.sarvam.ai/api/api-guides-tutorials/speech-to-text/how-to/keyterms)
- [Batch API + Diarization](https://docs.sarvam.ai/api/api-guides-tutorials/speech-to-text/batch-api)
- [Rate Limits](https://docs.sarvam.ai/api/ratelimits)
