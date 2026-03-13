---
name: translate
description: Translate text between English and Indian languages using Sarvam AI (Sarvam-Translate, Mayura). Handles content translation and app localization across 22+ languages with mode control, script options, and numeral formats. Use when translating or localizing content for Indian users.
license: Apache-2.0
metadata:
  author: sarvam-ai
  version: "3.0"
---

# Translation — Sarvam AI

> [!IMPORTANT]
> Auth: `api-subscription-key` header — NOT `Authorization: Bearer`. Base URL: `https://api.sarvam.ai/v1`

## Models

| Model | Max Input | Languages | Features |
|-------|-----------|-----------|----------|
| `sarvam-translate:v1` | 2,000 chars | 22 languages | Formal style, `numerals_format` |
| `mayura:v1` | 1,000 chars | 11 languages | `mode`, `output_script`, `speaker_gender` |

## Quick Start

```python
from sarvamai import SarvamAI
client = SarvamAI()

response = client.text.translate(
    input="Hello, how are you?",
    source_language_code="en-IN",
    target_language_code="hi-IN",
    model="sarvam-translate:v1"
)
print(response.translated_text)
```

## Gotchas

| Gotcha | Detail |
|--------|--------|
| **Method name** | `client.text.translate()` — NOT `client.translate.translate()`. The API is under the `text` namespace. |
| **`output_script` on sarvam-translate** | NOT supported — only works with `mayura:v1`. Silently ignored on `sarvam-translate:v1`. |
| **`mode`/`speaker_gender`** | Only work with `mayura:v1`. `sarvam-translate:v1` only supports `formal` style + `numerals_format`. |
| **Odia language code** | `od-IN` — NOT `or-IN`. |
| **Character limits** | Exceeding returns 422. Split long text at sentence boundaries. |

## Full Docs

Fetch language codes, mode examples, script options, and numeral formats from:

- **https://docs.sarvam.ai/llms.txt** — comprehensive docs index
- [Translation Guide](https://docs.sarvam.ai/api-reference-docs/api-guides-tutorials/text-processing/translation)
- [Rate Limits](https://docs.sarvam.ai/api-reference-docs/ratelimits)
