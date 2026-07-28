---
name: vision
description: Document digitization and OCR using the Sarvam Vision model. Digitizes documents (PDF, PNG, JPG, ZIP) into structured Markdown or HTML, maintaining reading order and parsing tables. Use when extracting structured text, layout, and tables from documents in Indian languages.
license: Apache-2.0
metadata:
  author: sarvam-ai
  version: "3.0"
---

# Vision (Document Digitization) — Sarvam AI

> [!IMPORTANT]
> Auth: `api-subscription-key` header — NOT `Authorization: Bearer`. Base URL: `https://api.sarvam.ai/v1`

## Quick Start (Python)

```python
from sarvamai import SarvamAI
client = SarvamAI()

# Create a Document Digitization job
job = client.document_intelligence.create_job(
    language="hi-IN",           # Target language (BCP-47 format)
    output_format="md"          # Output format: "html" or "md"
)

# Upload document
job.upload_file("document.pdf")

# Start processing
job.start()

# Wait for completion
status = job.wait_until_complete()
print(f"Job completed: {status.job_state}")

# Download the output (ZIP file containing processed format + page-level JSON)
job.download_output("./output.zip")
```

## Quick Start (JavaScript/TypeScript)

```typescript
import { SarvamAIClient } from "sarvamai";

const client = new SarvamAIClient({ apiSubscriptionKey: "YOUR_SARVAM_API_KEY" });

const job = await client.documentIntelligence.createJob({
    language: "hi-IN",
    outputFormat: "md"
});

await job.uploadFile("document.pdf");
await job.start();

const status = await job.waitUntilComplete();
console.log(`Job completed: {status.job_state}`);

await job.downloadOutput("./output.zip");
```

## Gotchas

| Gotcha | Detail |
|--------|--------|
| **SDK Namespaces** | Python uses `client.document_intelligence.create_job(...)`. JS/TS uses `client.documentIntelligence.createJob({...})`. |
| **Parameter names** | Uses `language` (not `language_code` or `source_language_code`, which are ignored). Uses `output_format` (not `output_format_code` or `format`). |
| **`output_format` value** | Must be exactly `"md"` or `"html"`. Passing `"markdown"` will return a `400 Bad Request` error. |
| **10-page limit cap** | Both PDF and ZIP uploads are capped at a maximum of **10 pages**. Exceeding this returns a `422 Unprocessable Entity` with error code `max_page_limit_exceeded`. Split larger files beforehand. |
| **ZIP flat structure** | ZIP upload files must contain images (JPG/PNG) in a flat structure without nested directories. Order is determined alphabetically by filename. |
| **Output ZIP structure** | The download is a ZIP archive containing the requested format (HTML or Markdown) *and* a JSON file with page-level structured content. The JSON cannot be disabled. |

## Full Docs

Fetch supported language codes, pricing, and job state tables from:

- **https://docs.sarvam.ai/llms.txt** — comprehensive docs index
- [Document Digitization Guide](https://docs.sarvam.ai/api-reference-docs/api-guides-tutorials/document-digitization/overview)
- [Sarvam Vision Specs](https://docs.sarvam.ai/api-reference-docs/getting-started/models/sarvam-vision)
- [Rate Limits](https://docs.sarvam.ai/api-reference-docs/ratelimits)
