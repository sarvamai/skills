# Pipecat Reference

Detailed documentation for building voice agents with Pipecat and Sarvam AI.

## Architecture

```
┌─────────────────────────────────────────────────┐
│                   Pipeline                       │
│                                                 │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌───────┐
│  │Transport│ → │   STT   │ → │   LLM   │ → │  TTS  │
│  │ (Input) │   │(Sarvam) │   │(Sarvam) │   │(Sarvam)│
│  └─────────┘   └─────────┘   └─────────┘   └───────┘
│       ▲                                        │
│       │                                        ▼
│  ┌────────────────────────────────────────────────┐
│  │              Transport (Output)                │
│  └────────────────────────────────────────────────┘
└─────────────────────────────────────────────────┘
```

## Installation

```bash
pip install pipecat-ai "pipecat-ai[sarvam,silero,daily]"
```

## Basic Pipeline

```python
import asyncio
from pipecat.pipeline import Pipeline
from pipecat.frames import TextFrame, AudioFrame
from pipecat.services.sarvam import SarvamSTT, SarvamTTS, SarvamLLM
from pipecat.vad.silero import SileroVAD
from pipecat.transports.local import LocalAudioTransport

async def main():
    transport = LocalAudioTransport()
    
    pipeline = Pipeline([
        transport.input(),
        SileroVAD(),
        SarvamSTT(
            model="saarika:v2.5",
            language="hi-IN"
        ),
        SarvamLLM(
            model="sarvam-m",
            system_prompt="You are a helpful voice assistant."
        ),
        SarvamTTS(
            model="bulbul:v2",
            voice="anushka"
        ),
        transport.output()
    ])
    
    await pipeline.run()

if __name__ == "__main__":
    asyncio.run(main())
```

## Service Configuration

### STT Service

```python
from pipecat.services.sarvam import SarvamSTT

stt = SarvamSTT(
    model="saarika:v2.5",
    language="hi-IN",
    sample_rate=16000
)
```

### LLM Service

```python
from pipecat.services.sarvam import SarvamLLM

llm = SarvamLLM(
    model="sarvam-m",
    system_prompt="You are a helpful assistant.",
    temperature=0.7,
    max_tokens=150
)
```

### TTS Service

```python
from pipecat.services.sarvam import SarvamTTS

tts = SarvamTTS(
    model="bulbul:v2",
    voice="anushka",
    pitch=0.0,
    pace=1.0,
    loudness=1.0
)
```

## Function Calling

```python
from pipecat.services.sarvam import SarvamLLM
from pipecat.functions import function_tool

@function_tool
def check_balance(account_id: str) -> str:
    """Check account balance."""
    # Your logic here
    return f"Balance for {account_id}: ₹10,000"

@function_tool
def transfer_money(from_account: str, to_account: str, amount: float) -> str:
    """Transfer money between accounts."""
    return f"Transferred ₹{amount} from {from_account} to {to_account}"

llm = SarvamLLM(
    model="sarvam-m",
    system_prompt="You are a banking assistant.",
    tools=[check_balance, transfer_money]
)
```

## Custom Processors

```python
from pipecat.processors import FrameProcessor
from pipecat.frames import TextFrame

class SentimentFilter(FrameProcessor):
    async def process_frame(self, frame):
        if isinstance(frame, TextFrame):
            # Add sentiment analysis
            text = frame.text
            if "angry" in text.lower():
                # Escalate to human
                frame.metadata["escalate"] = True
        return frame

pipeline = Pipeline([
    transport.input(),
    SarvamSTT(...),
    SentimentFilter(),  # Custom processor
    SarvamLLM(...),
    SarvamTTS(...),
    transport.output()
])
```

## Transports

### Local Audio (Testing)

```python
from pipecat.transports.local import LocalAudioTransport

transport = LocalAudioTransport(
    input_device=0,   # Microphone
    output_device=1   # Speaker
)
```

### Daily.co (WebRTC)

```python
from pipecat.transports.daily import DailyTransport

transport = DailyTransport(
    room_url="https://your-domain.daily.co/room-name",
    token="your-meeting-token"
)
```

### WebSocket

```python
from pipecat.transports.websocket import WebSocketTransport

transport = WebSocketTransport(
    host="0.0.0.0",
    port=8765
)
```

## Context Management

```python
from pipecat.services.sarvam import SarvamLLM

class ConversationalLLM(SarvamLLM):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.conversation_history = []
        self.max_history = 10
    
    async def process_frame(self, frame):
        if isinstance(frame, TextFrame):
            self.conversation_history.append({
                "role": "user",
                "content": frame.text
            })
            
            # Trim history
            if len(self.conversation_history) > self.max_history:
                self.conversation_history = self.conversation_history[-self.max_history:]
            
            response = await self.generate(self.conversation_history)
            
            self.conversation_history.append({
                "role": "assistant",
                "content": response
            })
            
            return TextFrame(response)
        return frame
```

## Error Handling

```python
from pipecat.pipeline import Pipeline

async def main():
    pipeline = Pipeline([...])
    
    @pipeline.on_error
    async def handle_error(error, frame):
        print(f"Error processing {frame}: {error}")
        # Return fallback response
        return TextFrame("Sorry, I didn't understand. Please try again.")
    
    await pipeline.run()
```

## Testing

```python
import pytest
from pipecat.testing import MockTransport

@pytest.mark.asyncio
async def test_pipeline():
    transport = MockTransport()
    
    pipeline = Pipeline([
        transport.input(),
        SarvamSTT(...),
        SarvamLLM(...),
        SarvamTTS(...),
        transport.output()
    ])
    
    # Simulate input
    await transport.send_audio(test_audio_bytes)
    
    # Check output
    output = await transport.receive_audio()
    assert output is not None
```

