<p align="center">
  <img src="https://sarvam.ai/logo.svg" alt="Sarvam AI" width="200">
</p>

<h1 align="center">Sarvam AI Skills</h1>

<p align="center">
  <strong>Build AI applications for Bharat</strong><br>
  Speech, translation, and language understanding for 1.4 billion people
</p>

<p align="center">
  <a href="https://docs.sarvam.ai">Documentation</a> •
  <a href="https://dashboard.sarvam.ai">Get API Key</a> •
  <a href="https://agentskills.io/specification">Agent Skills Spec</a>
</p>

---

## Quick Start

```bash
# Install skills to your AI coding assistant
npx skills add sarvamai/skills

# Set your API key
export SARVAM_API_KEY="your-api-key"
```

## Available Skills

### 🎤 Speech-to-Text
**Model:** Saarika v2.5 • **Languages:** 11 Indian + English

Convert speech to text with automatic language detection, code-mixing support, and speaker diarization. WebSocket streaming accepts base64-encoded audio.

→ [View skill](./speech-to-text)

---

### 🔊 Text-to-Speech  
**Model:** Bulbul v2 • **Voices:** 6 (3 male, 3 female)

Generate natural Indian-accented speech with controllable pitch, pace, and loudness. Returns base64-encoded audio in 8+ formats.

→ [View skill](./text-to-speech)

---

### 🌐 Translate
**Model:** Mayura v1 • **Directions:** English ↔ Indian languages

Translate between English and 10 Indian languages with script control, numeral formatting, and code-mixed text support.

→ [View skill](./translate)

---

### 💬 Chat
**Model:** Sarvam-M (24B) • **Price:** Free

Chat completions with hybrid thinking mode for complex reasoning. OpenAI-compatible API with superior Indic language understanding.

→ [View skill](./chat)

---

### 🤖 Voice Agents
**Frameworks:** LiveKit, Pipecat

Build real-time conversational voice agents for customer service, IVR, and voice assistants in Indian languages.

→ [View skill](./voice-agents)

---

## Supported Languages

| Language | Code | Language | Code |
|----------|------|----------|------|
| Hindi | `hi-IN` | Tamil | `ta-IN` |
| Bengali | `bn-IN` | Telugu | `te-IN` |
| Kannada | `kn-IN` | Malayalam | `ml-IN` |
| Marathi | `mr-IN` | Gujarati | `gu-IN` |
| Punjabi | `pa-IN` | Odia | `or-IN` |
| English | `en-IN` | Auto-detect | `auto` |

## Why Sarvam?

- **Built for India** — Trained on Indian languages, accents, and contexts
- **Code-mixing** — Handles Hinglish, Tanglish, and mixed-language speech
- **Low latency** — Real-time streaming for voice applications
- **Free LLM** — Sarvam-M chat model is free to use

## Links

- [API Documentation](https://docs.sarvam.ai)
- [Dashboard](https://dashboard.sarvam.ai)
- [Discord Community](https://discord.gg/sarvam)

## License

Apache-2.0
