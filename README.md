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

## About

LLMs have fixed knowledge from their training cutoff. Sarvam AI's SDK has unique patterns that differ from standard conventions — method names that break expectations (`client.text.translate()` not `client.translate.translate()`), parameters that silently fail (`output_script` on sarvam-translate), and response quirks (`content` being `None` when reasoning consumes the token budget).

These skills bridge that gap. Each one gives AI coding assistants the exact SDK signatures and gotchas they need to generate correct Sarvam AI code, then routes to [llms.txt](https://docs.sarvam.ai/llms.txt) for detailed documentation.

## Skills

| Skill | Description |
|-------|-------------|
| [chat](./chat) | Chat completions with Sarvam-105B/30B. Python & JS/TS quick starts, streaming, reasoning mode, OpenAI-compatible path, and the `content=None` gotcha. |
| [speech-to-text](./speech-to-text) | Audio transcription with Saaras v3. Python & JS/TS quick starts, Batch API (long audio + diarization), and WebSocket streaming for 23 languages. |
| [text-to-speech](./text-to-speech) | Speech synthesis with Bulbul v3. Python & JS/TS quick starts, HTTP stream, WebSocket, pronunciation dictionaries, and unsupported parameter warnings. |
| [translate](./translate) | Text translation with Sarvam-Translate v1 and Mayura v1. Python & JS/TS quick starts, model feature differences, and silent parameter failures. |
| [voice-agents](./voice-agents) | Real-time voice agents with LiveKit and Pipecat (Python). JS/TS SDK reference for custom pipelines. |

## Installation

```bash
# Install all skills
npx skills add sarvamai/skills

# Install a specific skill
npx skills add sarvamai/skills --skill chat

# Browse skills interactively
npx skills add sarvamai/skills --list
```

```bash
# Setup
export SARVAM_API_KEY="your-api-key"  # get at dashboard.sarvam.ai
pip install sarvamai    # Python
npm install sarvamai    # JavaScript/TypeScript
```

Works with **Cursor**, **Claude Code**, **Windsurf**, and any agent that supports the [Agent Skills specification](https://agentskills.io/specification).

## How It Works

```
skill/SKILL.md           ← SDK signatures + gotchas (what agents get wrong)
    │
    ▼
llms.txt                 ← Always-fresh comprehensive docs index
    │
    ▼
Full API docs, OpenAPI spec, cookbooks, voice catalog, streaming protocols...
```

Each skill is a lean **correction layer** with both **Python** and **JavaScript/TypeScript** SDK snippets — it contains only what AI agents are likely to get wrong when generating Sarvam AI code:

- **SDK call signatures** that differ from conventions (e.g., no `.create()` on chat)
- **Parameters that silently fail** (e.g., `output_script` ignored on sarvam-translate)
- **Parameters that error** (e.g., `pitch`/`loudness` returns 400 on Bulbul v3)
- **Non-trivial SDK patterns** (e.g., Batch API job chain, WebSocket async connect)

For everything else — full parameter tables, voice catalogs, language codes, rate limits, cookbook examples — the skill points to [llms.txt](https://docs.sarvam.ai/llms.txt), which is always up to date.

## Links

- [API Documentation](https://docs.sarvam.ai)
- [llms.txt](https://docs.sarvam.ai/llms.txt)
- [Dashboard](https://dashboard.sarvam.ai)
- [Cookbook](https://github.com/sarvamai/sarvam-ai-cookbook)
- [Discord](https://discord.com/invite/5rAsykttcs)
- [GitHub](https://github.com/sarvamai)

## License

Apache-2.0
