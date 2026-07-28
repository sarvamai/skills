---
name: language-identification
description: Detect the language and script of input text using Sarvam AI. Supports major Indian languages and scripts, returning standard ISO/BCP-47 language codes and ISO script codes. Use to determine user language or script in multilingual workflows.
license: Apache-2.0
metadata:
  author: sarvam-ai
  version: "3.0"
---

# Language Identification — Sarvam AI

> [!IMPORTANT]
> Auth: `api-subscription-key` header — NOT `Authorization: Bearer`. Base URL: `https://api.sarvam.ai/v1`

## Quick Start (Python)

```python
from sarvamai import SarvamAI
client = SarvamAI()

response = client.text.identify_language(
    input="यह एक उदाहरण वाक्य है जो हिंदी भाषा में লেখা गया है।"
)
print(f"Language: {response.language_code}, Script: {response.script_code}")
```

## Quick Start (JavaScript/TypeScript)

```typescript
import { SarvamAIClient } from "sarvamai";

const client = new SarvamAIClient({ apiSubscriptionKey: "YOUR_SARVAM_API_KEY" });

const response = await client.text.identifyLanguage({
    input: "यह एक उदाहरण वाक्य है जो हिंदी भाषा में লেখা गया है।"
});
console.log(`Language: ${response.language_code}, Script: ${response.script_code}`);
```

## Gotchas

| Gotcha | Detail |
|--------|--------|
| **Method names** | Both SDKs place this in the `text` namespace: Python is `client.text.identify_language(...)`, JS/TS is `client.text.identifyLanguage({...})`. |
| **Max characters limit** | The input text cannot exceed **1,000 characters**. Exceeding this limit will return a `422 Unprocessable Entity` or `400 Bad Request` error. |
| **Nullable response fields** | If language or script cannot be identified, `language_code` and `script_code` fields can be `null` in the response. Ensure you check for `null` values before processing. |
| **Odia language/script code** | Language code is `od-IN` (not `or-IN`). Script code is `Orya`. |

## Full Docs

Fetch language codes, script codes, and confidence score information from:

- **https://docs.sarvam.ai/llms.txt** — comprehensive docs index
- [Language Identification Guide](https://docs.sarvam.ai/api-reference-docs/api-guides-tutorials/text-processing/language-detection)
- [Rate Limits](https://docs.sarvam.ai/api-reference-docs/ratelimits)
