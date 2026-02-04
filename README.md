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

## Skills

| Skill | Model | Description |
|-------|-------|-------------|
| [speech-to-text](./speech-to-text) | Saarika v2.5 | Transcribe audio with language detection, code-mixing, diarization. WebSocket streaming with base64 input. |
| [text-to-speech](./text-to-speech) | Bulbul v2 | Generate natural speech with 6 voices, pitch/pace control. Returns base64 audio. |
| [translate](./translate) | Mayura v1 | Translate English ↔ 10 Indian languages with script & numeral control. |
| [chat](./chat) | Sarvam-M (24B) | Chat completions with hybrid thinking. OpenAI-compatible. **Free to use.** |
| [voice-agents](./voice-agents) | — | Build conversational agents with LiveKit or Pipecat frameworks. |

## Supported Languages

```
Hindi (hi-IN)      Tamil (ta-IN)      Bengali (bn-IN)
Telugu (te-IN)     Kannada (kn-IN)    Malayalam (ml-IN)
Marathi (mr-IN)    Gujarati (gu-IN)   Punjabi (pa-IN)
Odia (or-IN)       English (en-IN)    Auto-detect (auto)
```

## Why Sarvam?

| Feature | Description |
|---------|-------------|
| 🇮🇳 **Built for India** | Trained on Indian languages, accents, and contexts |
| 🗣️ **Code-mixing** | Handles Hinglish, Tanglish, and mixed-language speech naturally |
| ⚡ **Low latency** | Real-time WebSocket streaming for voice applications |
| 🆓 **Free LLM** | Sarvam-M chat model is completely free to use |
| 🔌 **OpenAI-compatible** | Drop-in replacement for existing OpenAI integrations |

## Links

- 📚 [API Documentation](https://docs.sarvam.ai)
- 🔑 [Dashboard](https://dashboard.sarvam.ai)
- 💬 [Discord Community](https://discord.gg/sarvam)
- 🐙 [GitHub](https://github.com/sarvamai)

## License

Apache-2.0
