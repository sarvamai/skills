---
name: voice-agents
description: >-
  Build real-time Indic voice agents with Sarvam STT/TTS/LLM on LiveKit or
  Pipecat (Python), plus JS/TS custom-pipeline notes. Use this skill when
  creating phone bots, IVR, or always-on conversational voice apps. For
  one-shot in-chat voice reply or dubbing via MCP, use sarvam-mcp instead.
license: Apache-2.0
metadata:
  author: sarvam-ai
  version: "3.3"
---

# Voice Agents — Sarvam AI

> One-shot in-chat voice/dub → [sarvam-mcp](../sarvam-mcp) (`sarvam_tools_voice` / `_dub`). This skill = **LiveKit/Pipecat agent code**.

> [!IMPORTANT]
> Auth: `api-subscription-key` header — NOT `Authorization: Bearer`. Env var: `SARVAM_API_KEY`

## LiveKit Quick Start

```bash
pip install "livekit-agents[sarvam,silero]" python-dotenv
```

```python
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import sarvam

class VoiceAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="You are a helpful voice assistant. Be friendly, concise, and conversational.",
            stt=sarvam.STT(
                language="unknown",   # auto-detect; or "hi-IN", "ta-IN", etc.
                model="saaras:v3",
                mode="transcribe",
                flush_signal=True     # emits speech start/end events for turn-taking
            ),
            llm=sarvam.LLM(model="sarvam-105b"),
            tts=sarvam.TTS(
                target_language_code="en-IN",
                model="bulbul:v3",
                speaker="shubh"
            ),
        )

    async def on_enter(self):
        self.session.generate_reply()

async def entrypoint(ctx: JobContext):
    # Do NOT pass vad= — VAD is handled internally by the Sarvam plugin
    session = AgentSession(
        turn_detection="stt",       # let Sarvam STT handle turn detection
        min_endpointing_delay=0.07  # ~70ms matches Sarvam STT processing latency
    )
    await session.start(agent=VoiceAgent(), room=ctx.room)

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
```

Run with `python agent.py dev`, test with `python agent.py console`.

## Pipecat Quick Start

```bash
pip install "pipecat-ai[daily,sarvam]" python-dotenv loguru
```

```python
import os
from pipecat.pipeline.pipeline import Pipeline
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import LLMContextAggregatorPair
from pipecat.services.sarvam.stt import SarvamSTTService
from pipecat.services.sarvam.tts import SarvamTTSService
from pipecat.services.sarvam.llm import SarvamLLMService

stt = SarvamSTTService(
    api_key=os.getenv("SARVAM_API_KEY"),
    language="unknown",   # auto-detect; or "hi-IN", "ta-IN", etc.
    model="saaras:v3",
    mode="transcribe"     # or "translate" for speech-to-English
)
tts = SarvamTTSService(
    api_key=os.getenv("SARVAM_API_KEY"),
    target_language_code="en-IN",
    model="bulbul:v3",
    speaker="anand",
    pace=1.0
)
llm = SarvamLLMService(
    api_key=os.getenv("SARVAM_API_KEY"),
    settings=SarvamLLMService.Settings(model="sarvam-105b"),
)

messages = [{"role": "system", "content": "You are a friendly AI assistant. Keep responses brief."}]
context_aggregator = LLMContextAggregatorPair(LLMContext(messages))

pipeline = Pipeline([
    transport.input(),            # Daily or WebRTC transport
    stt,
    context_aggregator.user(),
    llm,
    tts,
    transport.output(),
    context_aggregator.assistant(),
])
```

## JavaScript/TypeScript Note

LiveKit and Pipecat agents are Python-only. For JS/TS voice pipelines, use the individual SDK methods directly:

```typescript
import { SarvamAIClient } from "sarvamai";
const client = new SarvamAIClient({ apiSubscriptionKey: process.env.SARVAM_API_KEY });

// STT: client.speechToText.transcribe({...})
// TTS: client.textToSpeech.convertStream({...})  // returns BinaryResponse
// LLM: client.chat.completions({...})
```

## Gotchas

| Gotcha | Detail |
|--------|--------|
| **LiveKit: no `vad=`** | Do NOT pass `vad=` to `AgentSession` — VAD is handled internally by the Sarvam plugin. Set `turn_detection="stt"` and `min_endpointing_delay=0.07` instead. |
| **LiveKit: `flush_signal=True`** | Required on `sarvam.STT` for speech start/end events and proper turn-taking. |
| **TTS param is `speaker`** | Both LiveKit and Pipecat plugins use `speaker="shubh"` — NOT `voice=`. |
| **Pipecat class names** | `SarvamSTTService`/`SarvamTTSService`/`SarvamLLMService` from `pipecat.services.sarvam.stt/.tts/.llm` — NOT `SarvamSTT`. LLM model goes in `SarvamLLMService.Settings(model=...)`, system prompt in `LLMContext` messages. |
| **`sarvam-30b` is deprecated** | Docs list it under Legacy Models ("migrate to Sarvam-105B"), and `sarvamai` ≥0.1.29 types chat as `SarvamModelIds = Literal["sarvam-105b"]`. Pipecat rejects it outright — `SarvamLLMService._SUPPORTED_MODELS = frozenset({"sarvam-105b"})`, so a non-105b model raises `ValueError` at construction. Use `sarvam-105b` for voice too. |
| **`max_tokens` budget** | Sarvam models reason internally. Don't set low `max_tokens` or `content` will be `None`. Omit, set 500+, or disable with `reasoning_effort=None`. |
| **TTS pitch/loudness** | NOT supported on Bulbul v3 — API returns 400. Only `pace` works. |
| **STT WebSocket codecs** | Only `wav`/`pcm` — no MP3/AAC/OGG for streaming. |
| **HTTP Stream for TTS** | `convert_stream` returns binary audio directly (no base64), better for pipelines. |
| **Telephony** | For phone agents (e.g. Exotel), set `audio_in_sample_rate=8000` and `audio_out_sample_rate=8000` to match telephony audio. |

## Full Docs

Fetch framework integration guides, environment setup, and advanced patterns from:

- **https://docs.sarvam.ai/llms.txt** — comprehensive docs index
- [LiveKit Guide](https://docs.sarvam.ai/api/integration/build-voice-agent-with-live-kit)
- [Pipecat Guide](https://docs.sarvam.ai/api/integration/build-voice-agent-with-pipecat)
- [Rate Limits](https://docs.sarvam.ai/api/ratelimits)
