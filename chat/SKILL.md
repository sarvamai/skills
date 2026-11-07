---
name: chat
description: >-
  Write correct Sarvam AI chat-completion code (Sarvam-105B, Sarvam-30B) —
  OpenAI-compatible API, streaming, reasoning mode, and the content=None
  gotcha. Use this skill when building chatbots, Q&A, agents, or Indic LLM
  features in Python or JS/TS. For a live completion in chat via MCP, use
  sarvam-mcp instead.
license: Apache-2.0
metadata:
  author: sarvam-ai
  version: "3.5"
---

# Chat Completions — Sarvam AI

> Live in-chat completion → [sarvam-mcp](../sarvam-mcp) (`sarvam_tools_llm_complete`). This skill = **SDK code**.

> [!IMPORTANT]
> Auth: `api-subscription-key` header — NOT `Authorization: Bearer`. Base URL: `https://api.sarvam.ai/v1`

## Models

| Model | Context | Best For |
|-------|---------|----------|
| `sarvam-105b` | 128K | Complex reasoning, coding, agentic workflows |
| `sarvam-105b-conversations` | 32K | Real-time chat, voice agents, conversational AI |

`sarvam-30b` is **deprecated** — migrate to `sarvam-105b` for complex tasks or `sarvam-105b-conversations` for real-time/voice (the model built to fill `sarvam-30b`'s old slot). The fixed-context variants (`sarvam-105b-32k`, `sarvam-30b-16k`) are retired — base models serve their full context window directly.

Also available on `/v2/chat/completions` — open-weight **Token Factory** models, each labelled **Serverless** (any API key, billed per token) or **Provisioned Throughput** (capacity enabled per organisation; ask Sarvam for access):

| Model | Context | Input | Availability |
|-------|---------|-------|--------------|
| `glm5.3` | 1M | text | Serverless |
| `glm5.3-flash` | 1M | text + image | Serverless — lowest per-token price |
| `deepseekv4.1-flash-1017` | 1M | text + image | Serverless — `deepseekv4.1-flash-1017-interactive` is the 200+ tok/s variant |
| `gemma4` | 131K | text + image | Serverless |
| `qwen38-27b` | 262K | text + image, tool calling | Provisioned Throughput |
| `deepseek-v4-pro` | 1M | text | Provisioned Throughput |
| `kimi-k3.1-pro` | 1M | text + image + video | Provisioned Throughput |

Called via `client.chat.completions_v2(...)` in Python — **not** `.completions()`. `kimi-k3`, `mimo-v2.6-flash` and `mimo-v2.6-pro` are no longer offered; `deepseekv4-flash` is now `deepseekv4.1-flash-1017`. See Full Docs for the per-model pages.

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
| **`content` can be `None`** | Models produce `reasoning_content` before `content`. If `max_tokens` is too low, reasoning consumes the budget, `finish_reason` is `"length"`, and `content` is `None`. Omit `max_tokens`, set 500+, or disable reasoning with `reasoning_effort=None`. Check `reasoning_content` as fallback. Verified live: this is real and a little flaky — the same short prompt at `max_tokens=500` returned `content=None` once and `content="OK"` on retry, with reasoning eating 251 of the 500 tokens that time. Don't treat 500 as a guarantee; check `reasoning_content`/`finish_reason` regardless. |
| **reasoning_effort** | Thinking is **on by default** at `"low"`. Values: `"low"\|"medium"\|"high"`, or `None` to disable reasoning entirely. NOT `thinking=True`. Reasoning tokens count toward completion tokens and billing. |
| **`sarvam-30b` now hard-errors, not just "deprecated"** | Verified live: calling it returns `400 invalid_request_error` — `"Model 'sarvam-30b' has been deprecated. Please use one of the available models instead: sarvam-105b, sarvam-105b-conversations."` It's not a soft warning; existing code on `sarvam-30b` is already broken. Migrate to `sarvam-105b` or `sarvam-105b-conversations`. |
| **One completion per request** | `n` must be `1` on every model, on both `/v1` and `/v2`. Requests with `n > 1` return `400 invalid_request_error` — send separate requests for multiple completions. |
| **Open-weight models: Python-only for now** | `glm5.3` / `glm5.3-flash` / `gemma4` / `deepseekv4.1-flash-1017` / `qwen38-27b` go through `client.chat.completions_v2(...)` on `/v2/chat/completions` in Python (verified working, all three, with a beta-enabled key). Verified live: the installed JS SDK (`sarvamai@1.1.10`) has **no `completionsV2` method at all** (`client.chat.completionsV2 is not a function`) — only `.completions()` exists in JS right now. Don't generate JS code calling `completionsV2` until the JS SDK ships it; check `npm ls sarvamai` / the changelog first. |

## Full Docs

Fetch detailed parameters, tool calling, streaming, and examples from:

- **https://docs.sarvam.ai/llms.txt** — comprehensive docs index
- [Chat Completion Guide](https://docs.sarvam.ai/api/api-guides-tutorials/chat-completion/overview)
- [Model Specs](https://docs.sarvam.ai/api/getting-started/models)
- [Rate Limits](https://docs.sarvam.ai/api/ratelimits)
