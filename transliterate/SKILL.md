---
name: transliterate
description: Transliterate text between scripts (e.g. Latin ↔ Devanagari) across 11 Indian languages using Sarvam AI. Supports Indic-to-English, English-to-Indic, and Indic-to-Indic transliteration. Use when converting text phonetically between scripts or converting text to natural spoken phonetic form.
license: Apache-2.0
metadata:
  author: sarvam-ai
  version: "3.0"
---

# Transliteration — Sarvam AI

> [!IMPORTANT]
> Auth: `api-subscription-key` header — NOT `Authorization: Bearer`. Base URL: `https://api.sarvam.ai/v1`

## Quick Start (Python)

```python
from sarvamai import SarvamAI
client = SarvamAI()

response = client.text.transliterate(
    input="मैं ऑफिस जा रहा हूँ",
    source_language_code="hi-IN",
    target_language_code="en-IN"
)
print(response.transliterated_text)
```

## Quick Start (JavaScript/TypeScript)

```typescript
import { SarvamAIClient } from "sarvamai";

const client = new SarvamAIClient({ apiSubscriptionKey: "YOUR_SARVAM_API_KEY" });

const response = await client.text.transliterate({
    input: "मैं ऑफिस जा रहा हूँ",
    source_language_code: "hi-IN",
    target_language_code: "en-IN"
});
console.log(response.transliterated_text);
```

## Gotchas

| Gotcha | Detail |
|--------|--------|
| **Method name** | Both Python & JS: `client.text.transliterate({...})` — NOT `client.transliterate.transliterate()`. Same `text` namespace in both SDKs. |
| **`spoken_form_numerals_language` requirement** | Only works when `spoken_form=True` (Python) or `spoken_form: true` (JS/TS). Silently ignored if `spoken_form` is false/omitted. |
| **`spoken_form` on en-IN output** | Has no effect if `target_language_code` is `en-IN`. |
| **Odia language code** | `od-IN` — NOT `or-IN`. |
| **Language support limits** | Only supports 11 languages (`bn-IN`, `en-IN`, `gu-IN`, `hi-IN`, `kn-IN`, `ml-IN`, `mr-IN`, `od-IN`, `pa-IN`, `ta-IN`, `te-IN`). Do not pass other codes. |

## Full Docs

Fetch language codes, numerals formats, and spoken form options from:

- **https://docs.sarvam.ai/llms.txt** — comprehensive docs index
- [Transliteration Guide](https://docs.sarvam.ai/api-reference-docs/api-guides-tutorials/text-processing/transliteration)
- [Rate Limits](https://docs.sarvam.ai/api-reference-docs/ratelimits)
