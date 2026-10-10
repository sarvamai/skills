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

Also available (beta, on `/v2/chat/completions`): open-weight models `glm5.3` (1M context, reasoning), `deepseekv4-flash` (1M context, reasoning), `gemma4` (131K context, text+image, no reasoning). Requires beta access on your API key. Called via `client.chat.completions_v2(...)` in Python — **not** `.completions()`. Still under beta and expected to GA soon — see Full Docs for details.

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
| **Open-weight models use `completions_v2` / `completionsV2`** | `glm5.3` / `gemma4` / `deepseekv4.1-flash` go through `/v2/chat/completions`: Python `client.chat.completions_v2(...)`, JS `client.chat.completionsV2({...})`. Verified live: JS `completionsV2` works in `sarvamai@1.1.11` (it was missing in 1.1.10 — upgrade if you get `completionsV2 is not a function`). Requires a beta-enabled key. |
| **V2 chat error codes** | Verified live on `/v2/chat/completions`: unknown model → `404 not_found_error` (`"Model 'nope' not found."`), while V1 returns `400` listing valid models. More than 4 `stop` sequences → `400` — `"'stop' takes at most 4 sequences."`. Wrong field type → `400` naming the field (`"'max_tokens' must be an integer."`). The V2 404 is a base `ApiError` / `SarvamAIError`, not `NotFoundError` — catch the base class. |
| **Errors & retries** | Errors return `{"error": {"message", "code", "request_id"}}`. Auth failures are **403**, not 401. The SDK already retries 429/5xx twice — raise `max_retries` / `maxRetries` instead of wrapping calls in your own loop. Full handling patterns: [errors](../errors) skill. |

## Full Docs

Fetch detailed parameters, tool calling, streaming, and examples from:

- **https://docs.sarvam.ai/llms.txt** — comprehensive docs index
- [Chat Completion Guide](https://docs.sarvam.ai/api/api-guides-tutorials/chat-completion/overview)
- [Model Specs](https://docs.sarvam.ai/api/getting-started/models)
- [Rate Limits](https://docs.sarvam.ai/api/ratelimits)
