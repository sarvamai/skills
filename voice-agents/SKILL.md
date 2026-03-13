---
name: voice-agents
description: Build conversational voice agents using Sarvam AI with LiveKit or Pipecat. Handles voice assistants, phone bots, IVR, and real-time conversational AI for Indian languages. Integrates Sarvam STT (Saaras v3), TTS (Bulbul v3), and LLM (Sarvam-30B) with low-latency streaming. Use when creating voice-enabled applications or real-time speech pipelines.
license: Apache-2.0
metadata:
  author: sarvam-ai
  version: "3.0"
---

# Voice Agents — Sarvam AI

> [!IMPORTANT]
> Auth: `api-subscription-key` header — NOT `Authorization: Bearer`. Env var: `SARVAM_API_KEY`

## LiveKit Quick Start

```bash
pip install livekit-agents livekit-plugins-sarvam livekit-plugins-silero
```

```python
from livekit.agents import Agent, AgentSession, JobContext, WorkerOptions, cli
from livekit.plugins import sarvam, silero

class VoiceAssistant(Agent):
    def __init__(self):
        super().__init__(
            vad=silero.VAD.load(),
            stt=sarvam.STT(model="saaras:v3"),
            llm=sarvam.LLM(model="sarvam-30b"),
            tts=sarvam.TTS(model="bulbul:v3", voice="shubh")
        )

    async def on_enter(self, session: AgentSession):
        await session.say("नमस्ते! मैं आपकी कैसे मदद कर सकती हूं?")

async def entrypoint(ctx: JobContext):
    agent = VoiceAssistant()
    await agent.start(ctx)

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
```

## Pipecat Quick Start

```bash
pip install pipecat-ai "pipecat-ai[sarvam,silero,daily]"
```

```python
from pipecat.pipeline import Pipeline
from pipecat.services.sarvam import SarvamSTT, SarvamTTS, SarvamLLM
from pipecat.vad.silero import SileroVAD
from pipecat.transports.local import LocalAudioTransport

transport = LocalAudioTransport()
pipeline = Pipeline([
    transport.input(), SileroVAD(),
    SarvamSTT(model="saaras:v3"),
    SarvamLLM(model="sarvam-30b", system_prompt="You are a helpful voice assistant."),
    SarvamTTS(model="bulbul:v3", voice="shubh"),
    transport.output()
])
```

## JavaScript/TypeScript Note

LiveKit and Pipecat agents are Python-only. For JS/TS voice pipelines, use the individual SDK methods directly:

```typescript
import { SarvamAIClient } from "sarvamai";
const client = new SarvamAIClient({ apiSubscriptionKey: "YOUR_SARVAM_API_KEY" });

// STT: client.speechToText.transcribe({...})
// TTS: client.textToSpeech.convertStream({...})  // returns BinaryResponse
// LLM: client.chat.completions({...})
```

## Gotchas

| Gotcha | Detail |
|--------|--------|
| **Use `sarvam-30b`** | Best latency for voice. Only use `sarvam-105b` when reasoning quality matters more than speed. |
| **`max_tokens` budget** | Sarvam models reason internally. Don't set low `max_tokens` or `content` will be `None`. Omit or set 500+. |
| **TTS pitch/loudness** | NOT supported on Bulbul v3 — API returns 400. Only `pace` works. |
| **STT WebSocket codecs** | Only `wav`/`pcm` — no MP3/AAC/OGG for streaming. |
| **HTTP Stream for TTS** | `convert_stream` returns binary audio directly (no base64), better for pipelines. |

## Full Docs

Fetch framework integration guides, environment setup, and advanced patterns from:

- **https://docs.sarvam.ai/llms.txt** — comprehensive docs index
- [LiveKit Guide](https://docs.sarvam.ai/api-reference-docs/integration/build-voice-agent-with-live-kit)
- [Pipecat Guide](https://docs.sarvam.ai/api-reference-docs/integration/build-voice-agent-with-pipecat)
- [Rate Limits](https://docs.sarvam.ai/api-reference-docs/ratelimits)
