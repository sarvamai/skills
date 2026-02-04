<p align="center">
  <img src="https://sarvam.ai/logo.svg" alt="Sarvam AI" width="200">
</p>

<h1 align="center">Sarvam AI Skills</h1>

<p align="center">
  <strong>Full-stack AI for Bharat</strong>
</p>

<p align="center">
  <a href="https://docs.sarvam.ai">Documentation</a> •
  <a href="https://dashboard.sarvam.ai">Get API Key</a> •
  <a href="https://agentskills.io/specification">Agent Skills Spec</a>
</p>

---

Sarvam provides **Models & APIs across the stack** to help developers build powerful applications. Whether you're looking for chat completion, text translation, speech-to-text conversion, or building voice agents — Sarvam has you covered.

These skills follow the [Agent Skills specification](https://agentskills.io/specification) and work with AI coding assistants like Claude Code, Cursor, and Windsurf.

## Quick Start

```bash
# Install skills to your AI coding assistant
npx skills add sarvamai/skills

# Set your API key
export SARVAM_API_KEY="your-api-key"
```

Get your free API key at [dashboard.sarvam.ai](https://dashboard.sarvam.ai)

## SDKs

Official SDKs for Python and JavaScript that provide a simple interface to access all Sarvam AI APIs.

### Python

```bash
pip install sarvamai
```

```python
from sarvamai import SarvamAI

client = SarvamAI()

# Speech-to-Text
response = client.speech_to_text.transcribe(
    file=open("audio.wav", "rb"),
    model="saarika:v2.5"
)

# Text-to-Speech
response = client.text_to_speech.convert(
    text="नमस्ते",
    target_language_code="hi-IN",
    model="bulbul:v2"
)

# Chat
response = client.chat.completions.create(
    model="sarvam-m",
    messages=[{"role": "user", "content": "Hello!"}]
)

# Translate
response = client.translate.translate(
    input="Hello",
    source_language_code="en-IN",
    target_language_code="hi-IN"
)
```

### JavaScript

```bash
npm install sarvamai
```

```javascript
import { SarvamAI } from "sarvamai";

const client = new SarvamAI();

// Chat
const response = await client.chat.completions.create({
  model: "sarvam-m",
  messages: [{ role: "user", content: "Hello!" }]
});
```

### Package Links

| Language | Package |
|----------|---------|
| Python | [PyPI](https://pypi.org/project/sarvamai/) |
| JavaScript | [npm](https://www.npmjs.com/package/sarvamai) |

## Skills

| Skill | Model | Description |
|-------|-------|-------------|
| [speech-to-text](./speech-to-text) | Saarika v2.5 | Transcribe audio with base64 WebSocket streaming |
| [text-to-speech](./text-to-speech) | Bulbul v2 | Generate speech, returns base64 audio |
| [translate](./translate) | Mayura v1 | English ↔ 10 Indian languages |
| [chat](./chat) | Sarvam-M | Chat completions (free) |
| [voice-agents](./voice-agents) | — | LiveKit & Pipecat integrations |

## Links

- 📚 [API Documentation](https://docs.sarvam.ai)
- 🔑 [Dashboard](https://dashboard.sarvam.ai)
- 📓 [Cookbook](https://github.com/sarvamai/sarvam-ai-cookbook)
- 💬 [Discord](https://discord.com/invite/5rAsykttcs)
- 🐙 [GitHub](https://github.com/sarvamai)

## License

Apache-2.0
