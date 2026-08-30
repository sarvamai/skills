---
name: chat
description: >-
  Write correct Sarvam AI chat-completion code (prefer Sarvam-105B; Sarvam-30B
  is deprecated) — OpenAI-compatible API, streaming, reasoning mode, and the
  content=None gotcha. Use this skill when building chatbots, Q&A, coding
  agents, or Indic LLM features in Python or JS/TS. For a live completion in
  chat via MCP, use sarvam-mcp instead.
license: Apache-2.0
metadata:
  author: sarvam-ai
  version: "3.3"
---

# Chat Completions — Sarvam AI

> Live in-chat completion → [sarvam-mcp](../sarvam-mcp) (`sarvam_tools_llm_complete`). This skill = **SDK code**.

> [!IMPORTANT]
> Auth: `api-subscription-key` header — NOT `Authorization: Bearer`. Base URL: `https://api.sarvam.ai/v1`

## Models

| Model | Context | Status | Best For |
|-------|---------|--------|----------|
| `sarvam-105b` | 128K | **Recommended** | Complex reasoning, coding, agentic workflows |
| `sarvam-30b` | 64K | **Deprecated** | Legacy only — prefer `sarvam-105b` for new work (voice latency exceptions: see [voice-agents](../voice-agents)) |

Public docs and the cookbook allowlist (`sarvam_api_rules.json`) treat **`sarvam-105b` as the source of truth** for new integrations. Do not start new examples on `sarvam-30b`.

The fixed-context variants (`sarvam-105b-32k`, `sarvam-30b-16k`) are retired — base models serve their full context window directly.

## Quick Start (Python)

```python
from sarvamai import SarvamAI
client = SarvamAI()

response = client.chat.completions(
    model="sarvam-105b",
    messages=[{"role": "user", "content": "भारत की राजधानी क्या है?"}],
    max_tokens=1024,
)
print(response.choices[0].message.content)
```

### Streaming (Python)

```python
for chunk in client.chat.completions(
    model="sarvam-105b",
    messages=[{"role": "user", "content": "Write a poem about India"}],
    max_tokens=1024,
    stream=True,
):
    if chunk.choices and chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

## Quick Start (JavaScript/TypeScript)

```typescript
import { SarvamAIClient } from "sarvamai";

const client = new SarvamAIClient({ apiSubscriptionKey: "YOUR_SARVAM_API_KEY" });

const response = await client.chat.completions({
    model: "sarvam-105b",
    messages: [{ role: "user", content: "भारत की राजधानी क्या है?" }],
    max_tokens: 1024,
});
console.log(response.choices[0].message.content);
```

### OpenAI-Compatible (both languages)

```python
from openai import OpenAI
client = OpenAI(api_key="your-key", base_url="https://api.sarvam.ai/v1")
response = client.chat.completions.create(
    model="sarvam-105b",
    messages=[...],
    max_tokens=1024,
)
```

## Gotchas

| Gotcha | Detail |
|--------|--------|
| **SDK method** | Python: `client.chat.completions(...)`, JS: `client.chat.completions({...})` — no `.create()` in either. OpenAI SDK uses `.create()` as usual. |
| **JS constructor** | `new SarvamAIClient({ apiSubscriptionKey: "..." })` — NOT `SarvamAI()`. Key is passed explicitly. |
| **`content` can be `None`** | Models produce `reasoning_content` before `content`. If `max_tokens` is too low, reasoning consumes the budget, `finish_reason` is `"length"`, and `content` is `None`. Set `max_tokens` to **500+** (1024 is a safe default), or disable reasoning with `reasoning_effort=None`. Check `reasoning_content` as fallback. |
| **reasoning_effort** | Thinking is **on by default** at `"low"`. Values: `"low"\|"medium"\|"high"`, or `None` to disable reasoning entirely. NOT `thinking=True`. Reasoning tokens count toward completion tokens and billing. |
| **Deprecated `sarvam-30b`** | Still accepted by some SDKs for compatibility, but new code should use `sarvam-105b`. |

## Full Docs

Fetch detailed parameters, tool calling, streaming, and examples from:

- **https://docs.sarvam.ai/llms.txt** — comprehensive docs index
- [Chat Completion Guide](https://docs.sarvam.ai/api/api-guides-tutorials/chat-completion/overview)
- [Model Specs](https://docs.sarvam.ai/api/getting-started/models)
- [Rate Limits](https://docs.sarvam.ai/api/ratelimits)
