---
name: chat
description: >-
  Write correct Sarvam AI chat-completion code (Sarvam-105B and
  Sarvam-105B-Conversations; Sarvam-30B is fully retired) — OpenAI-compatible
  API, streaming, reasoning mode, and the content=None gotcha. Use this skill
  when building chatbots, Q&A, agents, or Indic LLM features in Python or
  JS/TS. For a live completion in chat via MCP, use sarvam-mcp instead.
license: Apache-2.0
metadata:
  author: sarvam-ai
  version: "3.3"
---

# Chat Completions — Sarvam AI

> Live in-chat completion → [sarvam-mcp](../sarvam-mcp) (`sarvam_tools_llm_complete`). This skill = **SDK code**.

> [!IMPORTANT]
> Auth: `api-subscription-key` header — NOT `Authorization: Bearer`. Base URL: `https://api.sarvam.ai/v1`
> `sarvam-30b` is fully retired: the API itself now rejects it with a 400, it is not just "discouraged". Use `sarvam-105b` or `sarvam-105b-conversations` instead — see Models below.

## Models

| Model | Context | Best For |
|-------|---------|----------|
| `sarvam-105b` | 128K | Complex reasoning, coding, agentic workflows |
| `sarvam-105b-conversations` | 32K | Real-time dialogue, voice agents, multi-turn chat — replaces `sarvam-30b` |

`sarvam-30b`, `sarvam-m`, `sarvam-105b-32k`, and `sarvam-30b-16k` are all fully removed from the API. Calling any of them returns a 400 naming the two current models above as replacements — confirmed live:
```
400 {"error":{"message":"Model 'sarvam-30b' has been deprecated. Please use one
of the available models instead: sarvam-105b, sarvam-105b-conversations.",
"code":"invalid_request_error"}}
```

### Beta: open-source models via `/v2/chat/completions`

A separate beta endpoint, `POST https://api.sarvam.ai/v2/chat/completions`, adds open-source models alongside `sarvam-105b`. Confirmed live and working (no whitelisting block observed on a normal key, though docs say access can be gated per key):

| Model id (as sent to API) | Marketing name | Context | Notes |
|---|---|---|---|
| `gemma4` | Gemma 4 31B | — | Image input, tool calling |
| `deepseekv4-flash` | DeepSeek V4 Flash | 1M | Tool calling, visible reasoning. Beta capacity is currently constrained — expect throttling and don't onboard new customers onto it until it stabilizes |

> [!NOTE]
> `glm5.2` has been deprecated and is no longer available on `/v2/chat/completions` — requests now return `404 not_found_error`. Use `deepseekv4-flash` or `sarvam-105b` instead.

Same request/response shape as `/v1/chat/completions`. If a key isn't whitelisted, expect `400 invalid_request_error` before the model is called.

## Quick Start (Python)

```python
from sarvamai import SarvamAI
client = SarvamAI()

response = client.chat.completions(
    model="sarvam-105b-conversations",
    messages=[{"role": "user", "content": "भारत की राजधानी क्या है?"}]
)
print(response.choices[0].message.content)
```

### Streaming (Python)

```python
for chunk in client.chat.completions(
    model="sarvam-105b-conversations",
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
    model: "sarvam-105b-conversations",
    messages: [{ role: "user", content: "भारत की राजधानी क्या है?" }]
});
console.log(response.choices[0].message.content);
```

### OpenAI-Compatible (both languages)

```python
from openai import OpenAI
client = OpenAI(api_key="your-key", base_url="https://api.sarvam.ai/v1")
response = client.chat.completions.create(model="sarvam-105b-conversations", messages=[...])
```

## Gotchas

| Gotcha | Detail |
|--------|--------|
| **SDK method** | Python: `client.chat.completions(...)`, JS: `client.chat.completions({...})` — no `.create()` in either. OpenAI SDK uses `.create()` as usual. |
| **JS constructor** | `new SarvamAIClient({ apiSubscriptionKey: "..." })` — NOT `SarvamAI()`. Key is passed explicitly. |
| **`content` can be `None`** | Models produce `reasoning_content` before `content`. If `max_tokens` is too low, reasoning consumes the budget, `finish_reason` is `"length"`, and `content` is `None`. Omit `max_tokens`, set 500+, or disable reasoning with `reasoning_effort=None`. Check `reasoning_content` as fallback. |
| **reasoning_effort** | Thinking is **on by default** at `"low"`. Values: `"low"\|"medium"\|"high"`, or `None` to disable reasoning entirely. NOT `thinking=True`. Reasoning tokens count toward completion tokens and billing. |
| **`sarvam-30b` / `sarvam-m` are gone** | Both return `400 invalid_request_error` naming `sarvam-105b`/`sarvam-105b-conversations` as replacements. So do the old fixed-context names `sarvam-105b-32k` and `sarvam-30b-16k`. |

## Rate Limits (requests/min, Starter/Pro/Business)

| Model | Starter | Pro | Business |
|-------|---------|-----|----------|
| Default (incl. `sarvam-105b-conversations`) | 60 | 200 | 1,000 |
| `sarvam-105b` | 40 | 60 | 120 |

## Full Docs

Fetch detailed parameters, tool calling, streaming, and examples from:

- **https://docs.sarvam.ai/llms.txt** — comprehensive docs index
- [Chat Completion Guide](https://docs.sarvam.ai/api/api-guides-tutorials/chat-completion/overview)
- [Model Specs](https://docs.sarvam.ai/api/getting-started/models)
- [Beta APIs](https://docs.sarvam.ai/api-reference/beta-apis)
- [Rate Limits](https://docs.sarvam.ai/api/getting-started/ratelimits)
