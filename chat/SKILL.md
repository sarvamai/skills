---
name: chat
description: Chat completions using Sarvam AI LLMs (Sarvam-105B, Sarvam-30B). Handles AI chat, text generation, reasoning, coding, and multilingual conversations in Indian languages. OpenAI-compatible API. Use when building chatbots, Q&A systems, agents, or any LLM feature targeting Indian users.
license: Apache-2.0
metadata:
  author: sarvam-ai
  version: "3.0"
---

# Chat Completions — Sarvam AI

> [!IMPORTANT]
> Auth: `api-subscription-key` header — NOT `Authorization: Bearer`. Base URL: `https://api.sarvam.ai/v1`

## Models

| Model | Context | Best For |
|-------|---------|----------|
| `sarvam-105b` | 128K | Complex reasoning, coding, agentic workflows |
| `sarvam-30b` | 64K | Real-time chat, voice agents, conversational AI |
| `sarvam-105b-32k` | 32K | Cost-efficient 105B |
| `sarvam-30b-16k` | 16K | Cost-efficient 30B |

## Quick Start

```python
from sarvamai import SarvamAI
client = SarvamAI()

response = client.chat.completions(
    model="sarvam-30b",
    messages=[{"role": "user", "content": "भारत की राजधानी क्या है?"}]
)
print(response.choices[0].message.content)
```

### Streaming

```python
for chunk in client.chat.completions(
    model="sarvam-30b",
    messages=[{"role": "user", "content": "Write a poem about India"}],
    stream=True
):
    if chunk.choices and chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

### OpenAI-Compatible

```python
from openai import OpenAI
client = OpenAI(api_key="your-key", base_url="https://api.sarvam.ai/v1")
response = client.chat.completions.create(model="sarvam-30b", messages=[...])
```

## Gotchas

| Gotcha | Detail |
|--------|--------|
| **SDK method** | Sarvam SDK: `client.chat.completions(...)` — no `.create()`. OpenAI SDK uses `.create()` as usual. |
| **`content` can be `None`** | Models produce `reasoning_content` before `content`. If `max_tokens` is too low, reasoning consumes the budget and `content` is `None`. Omit `max_tokens` or set 500+. Check `reasoning_content` as fallback. |
| **reasoning_effort** | `reasoning_effort="low"\|"medium"\|"high"` for thinking mode. NOT `thinking=True`. |

## Full Docs

Fetch detailed parameters, tool calling, streaming, and examples from:

- **https://docs.sarvam.ai/llms.txt** — comprehensive docs index
- [Chat Completion Guide](https://docs.sarvam.ai/api-reference-docs/api-guides-tutorials/chat-completion/overview)
- [Model Specs](https://docs.sarvam.ai/api-reference-docs/getting-started/models)
- [Rate Limits](https://docs.sarvam.ai/api-reference-docs/ratelimits)
