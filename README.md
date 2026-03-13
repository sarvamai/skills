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

Modular [Agent Skills](https://agentskills.io/specification) for building with Sarvam AI. Each skill is a lean correction layer that gives AI coding assistants the exact SDK signatures and gotchas they need, then routes to [llms.txt](https://docs.sarvam.ai/llms.txt) for detailed docs.

## Install

```bash
npx skills add sarvamai/skills

export SARVAM_API_KEY="your-api-key"  # get at dashboard.sarvam.ai
pip install sarvamai
```

## Skills

| Skill | Model | What It Corrects |
|-------|-------|------------------|
| [chat](./chat) | `sarvam-105b` / `sarvam-30b` | SDK method (no `.create()`), `content=None` when `max_tokens` low |
| [speech-to-text](./speech-to-text) | `saaras:v3` | 30s REST limit, WebSocket codec restrictions, Batch API pattern |
| [text-to-speech](./text-to-speech) | `bulbul:v3` | `pitch`/`loudness` 400 error, v2 voice incompatibility |
| [translate](./translate) | `sarvam-translate:v1` / `mayura:v1` | Wrong method name, `output_script` silently ignored |
| [voice-agents](./voice-agents) | LiveKit / Pipecat | Framework setup, `max_tokens` budget for voice |

## Architecture

```
skill/SKILL.md           ← Correction layer: SDK signatures + gotchas
    │
    │  What agents get wrong: method names, unsupported params, silent failures
    │
    ▼
llms.txt                 ← Always-fresh comprehensive docs index
    │
    ▼
Full API docs, OpenAPI spec, cookbooks, voice catalog, streaming protocols...
```

**Why this structure?**

- **Discoverable** — 5 targeted skills match agent intent (search "text-to-speech" finds the right one)
- **Lean** — ~50-95 lines per skill vs ~140+ before. Install only what you need
- **Always fresh** — detailed docs fetched from `llms.txt` at query time, never stale
- **Correction-first** — focuses on what agents get wrong: SDK quirks, silent failures, param incompatibilities

## Links

- [API Documentation](https://docs.sarvam.ai)
- [llms.txt](https://docs.sarvam.ai/llms.txt)
- [Dashboard](https://dashboard.sarvam.ai)
- [Cookbook](https://github.com/sarvamai/sarvam-ai-cookbook)
- [Discord](https://discord.com/invite/5rAsykttcs)
- [GitHub](https://github.com/sarvamai)

## License

Apache-2.0
