# Sarvam AI Skills

Agent skills for [Sarvam AI
](https: //sarvam.ai) — India's AI platform for speech, translation, and language understanding. These skills follow the [Agent Skills specification](https://agentskills.io/specification).

## Installation

```bash
npx skills add sarvam-ai/skills
```

## Skills

| Skill | Description |
|-------|-------------|
| [speech-to-text
](./speech-to-text) | Transcribe audio using Saarika model |
| [text-to-speech
](./text-to-speech) | Generate speech using Bulbul model |
| [translate
](./translate) | Translate text using Mayura model |
| [chat
](./chat) | Chat completion using Sarvam-M model |
| [voice-agents
](./voice-agents) | Build voice agents with LiveKit/Pipecat |

## Configuration

```bash
export SARVAM_API_KEY="your-api-key"
```

Get your key at [dashboard.sarvam.ai
](https: //dashboard.sarvam.ai).

## License

Apache-2.0
