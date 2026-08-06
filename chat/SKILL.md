---
name: chat
description: >-
  Write correct Sarvam AI chat-completion code (Sarvam-105B) — OpenAI-compatible
  API, streaming, tool calling, reasoning mode, and the content=None gotcha.
  Use this skill when building chatbots, Q&A, agents, or Indic LLM features in
  Python or JS/TS. For a live completion in chat via MCP, use sarvam-mcp
  instead.
license: Apache-2.0
metadata:
  author: sarvam-ai
  version: "4.0"
---

# Chat Completions — Sarvam AI

> Live in-chat completion → [sarvam-mcp](../sarvam-mcp) (`sarvam_tools_llm_complete`). This skill = **SDK code**.

> [!IMPORTANT]
> Auth: `api-subscription-key` header — NOT `Authorization: Bearer`. Base URL: `https://api.sarvam.ai/v1`

## Models

| Model | Context | Best For |
|-------|---------|----------|
| `sarvam-105b` | 128K | Complex reasoning, coding, agentic workflows — the only model both SDKs currently type-check |

`sarvam-30b` and `sarvam-m` are **deprecated and no longer available through the API** — the Python and JS/TS SDKs (`sarvamai` ≥0.1.29 / ≥1.x) both narrowed their model type to `Literal["sarvam-105b"]`. Passing `sarvam-30b` will fail type-checking and the live call will reject it. The fixed-context variants (`sarvam-105b-32k`, `sarvam-30b-16k`) are retired too — the base model serves its full context window directly.

## Quick Start (Python)

```python
from sarvamai import SarvamAI
client = SarvamAI()

response = client.chat.completions(
    model="sarvam-105b",
    messages=[{"role": "user", "content": "भारत की राजधानी क्या है?"}]
)
print(response.choices[0].message.content)
```

### Streaming (Python)

```python
for chunk in client.chat.completions(
    model="sarvam-105b",
    messages=[{"role": "user", "content": "Write a poem about India"}],
    stream=True
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
    messages: [{ role: "user", content: "भारत की राजधानी क्या है?" }]
});
console.log(response.choices[0].message.content);
```

### OpenAI-Compatible (both languages)

```python
from openai import OpenAI
client = OpenAI(api_key="your-key", base_url="https://api.sarvam.ai/v1")
response = client.chat.completions.create(model="sarvam-105b", messages=[...])
```

## Gotchas

| Gotcha | Detail |
|--------|--------|
| **SDK method** | Python: `client.chat.completions(...)`, JS: `client.chat.completions({...})` — no `.create()` in either. OpenAI SDK uses `.create()` as usual. |
| **JS constructor** | `new SarvamAIClient({ apiSubscriptionKey: "..." })` — NOT `SarvamAI()`. Key is passed explicitly. |
| **`content` can be `None`** | Models produce `reasoning_content` before `content`. If `max_tokens` is too low, reasoning consumes the budget, `finish_reason` is `"length"`, and `content` is `None`. Omit `max_tokens`, set 500+, or disable reasoning with `reasoning_effort=None`. Check `reasoning_content` as fallback. |
| **reasoning_effort** | Thinking is **on by default** at `"low"`. Values: `"low"\|"medium"\|"high"`, or `None` to disable reasoning entirely. NOT `thinking=True`. Reasoning tokens count toward completion tokens and billing. |
| **Tool calling** | `tools=[...]` + `tool_choice=...` are real params (OpenAI-style function calling) on both SDKs — not documented in the older skill version. Also available: `wiki_grounding=True` (grounded answers), plus standard `stop`, `n`, `seed`, `frequency_penalty`, `presence_penalty`. |
| **SDK's own docstrings can mislead** | The Python SDK's `completions()` docstring example still shows `model="sarvam-m"` even though `sarvam-m` is deprecated and not a valid `SarvamModelIds` value. If an agent reads the installed package's help text for a model name, don't trust it over this table. |

## Full Docs

Fetch detailed parameters, tool calling, streaming, and examples from:

- **https://docs.sarvam.ai/llms.txt** — comprehensive docs index
- [Chat Completion Guide](https://docs.sarvam.ai/api/api-guides-tutorials/chat-completion/overview)
- [Model Specs](https://docs.sarvam.ai/api/getting-started/models)
- [Rate Limits](https://docs.sarvam.ai/api/ratelimits)
