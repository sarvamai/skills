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

For **in-chat** Sarvam actions (translate this, speak that, dub audio) across Cursor, Claude Code, and other MCP clients, install [sarvam-mcp](https://github.com/sarvamai/sarvam-mcp) and use the [sarvam-mcp](./sarvam-mcp) skill.

## Skills

The [vibe-coding](./vibe-coding) skill is **stack- and vendor-agnostic**—it is for anyone building with an agent. [sarvam-mcp](./sarvam-mcp) teaches agents to drive the Sarvam MCP server in any harness. The other skills document **Sarvam** SDK APIs for writing code.

| Skill                              | Description                                                                                                                             |
| ---------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| [sarvam-mcp](./sarvam-mcp)         | **MCP (any harness)** — live `sarvam_tools_*` vs build-time `sarvam_code_*`, composites, auth, install. Use for in-chat Sarvam actions. |
| [chat](./chat)                     | **SDK** — Sarvam-105B/30B completions, streaming, reasoning, `content=None` gotcha.                                                     |
| [speech-to-text](./speech-to-text) | **SDK** — Saaras v3 REST, Batch + diarization, WebSocket streaming.                                                                     |
| [text-to-speech](./text-to-speech) | **SDK** — Bulbul v3 REST/stream/WebSocket, pronunciation dicts, v3 param traps.                                                         |
| [translate](./translate)           | **SDK** — Mayura / Sarvam-Translate signatures and silent failures.                                                                     |
| [voice-agents](./voice-agents)     | **SDK** — LiveKit / Pipecat real-time voice agents.                                                                                     |
| [vibe-coding](./vibe-coding)       | **Vendor-neutral** agent habits (slice → verify → iterate). Pair with a domain skill for APIs.                                          |

## Installation

```bash
# Install all skills
npx skills add sarvamai/skills

# Install a specific skill
npx skills add sarvamai/skills --skill sarvam-mcp
npx skills add sarvamai/skills --skill chat
npx skills add sarvamai/skills --skill vibe-coding

# Browse skills interactively
npx skills add sarvamai/skills --list
```

```bash
# Setup (SDK skills)
export SARVAM_API_KEY="your-api-key"  # get at dashboard.sarvam.ai
pip install sarvamai    # Python
npm install sarvamai    # JavaScript/TypeScript

# Setup (MCP skill — live tools in-chat)
# uvx sarvam-mcp  — see sarvam-mcp/references/install.md for each client
```

Works with **Cursor**, **Claude Code**, **Windsurf**, and any agent that supports the [Agent Skills specification](https://agentskills.io/specification). The MCP skill also covers Claude Desktop, Zed, Codex, Gemini CLI, VS Code, Cline, Continue, and LM Studio.

## SDK usage & naming

The examples in this repository use different SDK client names across Python and JavaScript/TypeScript. The table below shows the canonical constructors and recommended authentication methods.

| Language                | SDK client                                             | Recommended authentication                                       |
| ----------------------- | ------------------------------------------------------ | ---------------------------------------------------------------- |
| Python                  | `from sarvamai import SarvamAI`                        | `SARVAM_API_KEY` environment variable or `~/.sarvam/credentials` |
| JavaScript / TypeScript | `new SarvamAIClient({ apiSubscriptionKey: "sk_..." })` | `apiSubscriptionKey` constructor option                          |

You can verify that your API key works with a simple `curl` request:

```bash
curl -sS -X POST "https://api.sarvam.ai/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "api-subscription-key: sk_..." \
  -d '{
    "model": "sarvam-30b",
    "messages": [
      {"role": "user", "content": "Hello"}
    ]
  }'
```

**Note:** Sarvam APIs use the `api-subscription-key` header. If you use an OpenAI-compatible client or wrapper with a custom `base_url`, make sure it sends `api-subscription-key` rather than `Authorization: Bearer`, or use a proxy/middleware that injects the required header.

## How It Works

```
sarvam-mcp/SKILL.md     ← MCP routing (tools_* vs code_*) for any harness
SDK skill/SKILL.md      ← SDK signatures + gotchas (what agents get wrong)
    │
    ▼
llms.txt / MCP code_*   ← Always-fresh docs index or live API reference tools
    │
    ▼
Full API docs, OpenAPI spec, cookbooks, voice catalog, streaming protocols...
```

**sarvam-mcp** teaches agents when to call live MCP tools vs build-time helpers, and how to install the server in each client. The other Sarvam skills are a lean **correction layer** with both **Python** and **JavaScript/TypeScript** SDK snippets — only what AI agents get wrong when generating Sarvam AI code:

* **SDK call signatures** that differ from conventions (e.g., no `.create()` on chat)
* **Parameters that silently fail** (e.g., `output_script` ignored on sarvam-translate)
* **Parameters that error** (e.g., `pitch`/`loudness` returns 400 on Bulbul v3)
* **Non-trivial SDK patterns** (e.g., Batch API job chain, WebSocket async connect)

For everything else — full parameter tables, voice catalogs, language codes, rate limits, cookbook examples — the skill points to [llms.txt](https://docs.sarvam.ai/llms.txt), which is always up to date.

## Links

* [API Documentation](https://docs.sarvam.ai)
* [llms.txt](https://docs.sarvam.ai/llms.txt)
* [Dashboard](https://dashboard.sarvam.ai)
* [Cookbook](https://github.com/sarvamai/sarvam-ai-cookbook)
* [Discord](https://discord.com/invite/5rAsykttcs)
* [GitHub](https://github.com/sarvamai)

## License

Apache-2.0
