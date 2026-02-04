# WebSocket Streaming Reference

Detailed documentation for real-time speech-to-text streaming with Sarvam AI.

## Connection

```python
from sarvamai import AsyncSarvamAI

client = AsyncSarvamAI()

async with client.speech_to_text_streaming.connect(
    language_code="hi-IN",
    model="saarika:v2.5",
    high_vad_sensitivity=True,
    vad_signals=True,
    flush_signal=True
) as ws:
    # Streaming operations
    pass
```

## Connection Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `language_code` | string | required | BCP-47 language code |
| `model` | string | `saarika:v2.5` | Model version |
| `high_vad_sensitivity` | bool | `False` | Better voice activity detection |
| `vad_signals` | bool | `False` | Emit speech start/end events |
| `flush_signal` | bool | `False` | Enable manual flush control |

## Audio Input Format

Audio must be **base64 encoded**. Only these formats are supported:

| Format | Description |
|--------|-------------|
| `audio/wav` | WAV files |
| `pcm_s16le` | Signed 16-bit little-endian PCM |
| `pcm_l16` | Linear 16-bit PCM |
| `pcm_raw` | Raw PCM (must be 16kHz) |

**Not supported for streaming:** MP3, AAC, OGG, FLAC, WebM

## Sending Audio

```python
import base64

# Read and encode audio
with open("chunk.wav",
"rb") as f:
    audio_base64 = base64.b64encode(f.read()).decode("utf-8")

# Send to WebSocket
await ws.transcribe(
    audio=audio_base64,
    encoding="audio/wav",
    sample_rate=16000
)
```

## Receiving Events

```python
async for event in ws:
    if event.type == "transcript":
        print(f"Final: {event.transcript}")
    elif event.type == "partial":
        print(f"Partial: {event.partial}")
    elif event.type == "speech_start":
        print("Speech started")
    elif event.type == "speech_end":
        print("Speech ended")
```

## Flush Signal

Force immediate processing without waiting for silence:

```python
# Send audio chunks
await ws.transcribe(audio=chunk1)
await ws.transcribe(audio=chunk2)

# Force transcription now
await ws.flush()

# Get result immediately
result = await ws.recv()
```

## VAD Signals

When `vad_signals=True`, the WebSocket emits:

- `speech_start` - Voice activity begins
- `speech_end` - Voice activity ends

```python
async with client.speech_to_text_streaming.connect(
    language_code="hi-IN",
    vad_signals=True
) as ws:
    async for event in ws:
        if event.type == "speech_start":
            print("User started speaking")
        elif event.type == "speech_end":
            print("User stopped speaking")
```

## JavaScript WebSocket

```javascript
import { SarvamAIClient
} from "sarvamai";
import * as fs from "fs";

const client = new SarvamAIClient();

const socket = await client.speechToTextStreaming.connect({
    "language-code": "hi-IN",
  model: "saarika:v2.5",
  high_vad_sensitivity: "true"
});

// Convert audio to base64
const audioData = fs.readFileSync("audio.wav").toString("base64");

socket.on("open", () => {
  socket.transcribe({
    audio: audioData,
    sample_rate: 16000,
    encoding: "audio/wav"
    });
});

socket.on("message", (event) => {
  console.log("Transcript:", event);
});

socket.on("error", (error) => {
  console.error("Error:", error);
});
```

## Best Practices

1. **Use 16kHz sample rate** for optimal accuracy
2. **Send chunks of 100-500ms** for low latency
3. **Handle reconnection** for long-running sessions
4. **Use flush signals** for turn-based conversations
5. **Enable VAD signals** for voice activity tracking

