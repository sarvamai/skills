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
  version: "3.3"
---

# Chat Completions — Sarvam AI

> Live in-chat completion → [sarvam-mcp](../sarvam-mcp) (`sarvam_tools_llm_complete`). This skill = **SDK code**.

> [!IMPORTANT]
> Auth: `api-subscription-key` header — NOT `Authorization: Bearer`. Base URL: `https://api.sarvam.ai/v1`

## Models

| Model | Context | Best For |
|-------|---------|----------|
| `sarvam-105b` | 128K | Complex reasoning, coding, agentic workflows |
| `sarvam-30b` | 64K | Real-time chat, voice agents, conversational AI |

The fixed-context variants (`sarvam-105b-32k`, `sarvam-30b-16k`) are retired — base models serve their full context window directly.

> **`sarvam-m` is deprecated.** Requests with `model: "sarvam-m"` fail with a 400. Use `sarvam-105b` instead.

## Quick Start (Python)

```python
from sarvamai import SarvamAI
client = SarvamAI()

response = client.chat.completions(
    model="sarvam-30b",
    messages=[{"role": "user", "content": "भारत की राजधानी क्या है?"}]
)
print(response.choices[0].message.content)
```

### Streaming (Python)

```python
for chunk in client.chat.completions(
    model="sarvam-30b",
    messages=[{"role": "user", "content": "Write a poem about India"}],
    stream=True
):
    if not chunk.choices:
        continue
    delta = chunk.choices[0].delta
    # Reasoning tokens arrive BEFORE content — check separately, or the
    # first non-empty delta gets mistaken for the answer.
    if getattr(delta, "reasoning_content", None):
        pass  # thinking tokens, not the answer
    if delta.content:
        print(delta.content, end="", flush=True)
```

## Quick Start (JavaScript/TypeScript)

```typescript
import { SarvamAIClient } from "sarvamai";

const client = new SarvamAIClient({ apiSubscriptionKey: "YOUR_SARVAM_API_KEY" });

const response = await client.chat.completions({
    model: "sarvam-30b",
    messages: [{ role: "user", content: "भारत की राजधानी क्या है?" }]
});
console.log(response.choices[0].message.content);
```

### Streaming (JavaScript/TypeScript)

```typescript
const stream = await client.chat.completions({
    model: "sarvam-30b",
    messages: [{ role: "user", content: "Write a poem about India" }],
    stream: true
});

for await (const chunk of stream) {
    const delta = chunk.choices[0]?.delta;
    // Reasoning tokens arrive BEFORE content — check separately, or the
    // first non-empty delta gets mistaken for the answer.
    if (delta?.reasoning_content) {
        // thinking tokens, not the answer
    }
    if (delta?.content) {
        process.stdout.write(delta.content);
    }
}
```

### OpenAI-Compatible (both languages)

```python
from openai import OpenAI
client = OpenAI(api_key="your-key", base_url="https://api.sarvam.ai/v1")
response = client.chat.completions.create(model="sarvam-30b", messages=[...])
```

## Gotchas

| Gotcha | Detail |
|--------|--------|
| **SDK method** | Python: `client.chat.completions(...)`, JS: `client.chat.completions({...})` — no `.create()` in either. OpenAI SDK uses `.create()` as usual. |
| **JS constructor** | `new SarvamAIClient({ apiSubscriptionKey: "..." })` — NOT `SarvamAI()`. Key is passed explicitly. |
| **`content` can be `None`** | Models produce `reasoning_content` before `content`. If `max_tokens` is too low, reasoning consumes the budget, `finish_reason` is `"length"`, and `content` is `None`. Omit `max_tokens`, set 500+, or disable reasoning with `reasoning_effort=None`. Check `reasoning_content` as fallback. |
| **reasoning_effort** | Thinking is **on by default** at `"low"`. Values: `"low"\|"medium"\|"high"`, or `None` to disable reasoning entirely. NOT `thinking=True`. Reasoning tokens count toward completion tokens and billing. |
| **Auth failures return 403** | A bad or expired API key returns **403 Forbidden**, not 401. The SDK throws `ForbiddenError`. Standard "catch 401 → re-prompt" logic silently misses it — catch 403 in retry/re-auth flows. |
| **`sarvam-m` is deprecated** | Requests with `model: "sarvam-m"` fail with a 400: `"Model 'sarvam-m' has been deprecated."` Use `sarvam-105b` instead. |
| **Streaming reasoning order** | In stream chunks, `delta.reasoning_content` arrives **before** `delta.content`. Check for `reasoning_content` first and handle separately, or the agent may treat thinking tokens as content. |

## Full Docs

Fetch detailed parameters, tool calling, streaming, and examples from:

- **https://docs.sarvam.ai/llms.txt** — comprehensive docs index
- [Chat Completion Guide](https://docs.sarvam.ai/api/api-guides-tutorials/chat-completion/overview)
- [Model Specs](https://docs.sarvam.ai/api/getting-started/models)
- [Rate Limits](https://docs.sarvam.ai/api/ratelimits)
