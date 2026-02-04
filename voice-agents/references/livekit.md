# LiveKit Reference

Detailed documentation for building voice agents with LiveKit and Sarvam AI.

## Architecture

```
┌─────────────┐    WebRTC    ┌─────────────┐
│   Client    │◄────────────►│  LiveKit    │
│  (Browser)  │              │   Server    │
└─────────────┘              └──────┬──────┘
                                    │
                             ┌──────▼──────┐
                             │   Agent     │
                             │  (Python)   │
                             └──────┬──────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
              ┌─────────┐    ┌─────────┐    ┌─────────┐
              │ Sarvam  │    │ Sarvam  │    │ Sarvam  │
              │   STT   │    │   LLM   │    │   TTS   │
              └─────────┘    └─────────┘    └─────────┘
```

## Installation

```bash
pip install livekit-agents livekit-plugins-sarvam livekit-plugins-silero
```

## Full Agent Example

```python
import asyncio
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    WorkerOptions,
    cli,
)
from livekit.plugins import sarvam, silero

class VoiceAssistant(Agent):
    def __init__(self):
        super().__init__(
            vad=silero.VAD.load(),
            stt=sarvam.STT(
                model="saarika:v2.5",
                language="hi-IN"
            ),
            llm=sarvam.LLM(model="sarvam-m"),
            tts=sarvam.TTS(
                model="bulbul:v2",
                voice="anushka"
            )
        )

    async def on_enter(self, session: AgentSession):
        await session.say("नमस्ते! मैं आपकी कैसे मदद कर सकती हूं?")

    async def on_message(self, session: AgentSession, message: str):
        response = await session.llm.generate(
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": message}
            ]
        )
        await session.say(response)

async def entrypoint(ctx: JobContext):
    agent = VoiceAssistant()
    await agent.start(ctx)

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
```

## STT Configuration

```python
from livekit.plugins import sarvam

stt = sarvam.STT(
    model="saarika:v2.5",
    language="hi-IN",              # Language code
    sample_rate=16000,             # Audio sample rate
    interim_results=True,          # Get partial transcriptions
    punctuate=True,                # Add punctuation
    profanity_filter=False         # Filter profanity
)
```

## TTS Configuration

```python
from livekit.plugins import sarvam

tts = sarvam.TTS(
    model="bulbul:v2",
    voice="anushka",
    sample_rate=24000,             # Output sample rate
    pitch=0.0,                     # -1.0 to 1.0
    pace=1.0,                      # 0.5 to 2.0
    loudness=1.0                   # 0.5 to 2.0
)
```

## LLM Configuration

```python
from livekit.plugins import sarvam

llm = sarvam.LLM(
    model="sarvam-m",
    temperature=0.7,
    max_tokens=150,                # Keep responses concise for voice
    thinking=False                 # Enable for complex reasoning
)
```

## Event Handlers

```python
class MyAgent(Agent):
    async def on_enter(self, session: AgentSession):
        """Called when user joins."""
        pass
    
    async def on_message(self, session: AgentSession, message: str):
        """Called when user speaks."""
        pass
    
    async def on_leave(self, session: AgentSession):
        """Called when user leaves."""
        pass
    
    async def on_error(self, session: AgentSession, error: Exception):
        """Called on error."""
        await session.say("Sorry, something went wrong.")
```

## Room Management

```python
from livekit import api

async def create_room():
    lk = api.LiveKitAPI()
    room = await lk.room.create_room(
        api.CreateRoomRequest(name="voice-agent-room")
    )
    return room

async def create_token(room_name: str, participant_name: str):
    lk = api.LiveKitAPI()
    token = await lk.access_token.create(
        api.AccessTokenOptions(
            identity=participant_name,
            room=room_name,
            room_join=True,
            can_publish=True,
            can_subscribe=True
        )
    )
    return token
```

## Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "agent.py", "start"]
```

### Environment Variables

```bash
LIVEKIT_URL=wss://your-server.livekit.cloud
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret
SARVAM_API_KEY=your-sarvam-key
```

## Scaling

LiveKit handles scaling automatically:

```python
# Run multiple workers
# Each worker handles multiple rooms
cli.run_app(
    WorkerOptions(
        entrypoint_fnc=entrypoint,
        num_idle_processes=3  # Pre-warm processes
    )
)
```

