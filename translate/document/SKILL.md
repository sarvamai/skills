---
name: document-translation
description: >-
  Write correct Sarvam Document Translation code — async create → upload →
  start → poll → export pipeline for PDF, Word, Excel, PowerPoint, and HTML
  files. Use this skill when building document-to-document translation
  features in Python or JS/TS. For short pasted text, use text-translation
  instead. For live document translation in chat via MCP, use sarvam-mcp
  instead.
license: Apache-2.0
metadata:
  author: sarvam-ai
  version: "1.0"
---

# Document Translation — Sarvam AI

> Live in-chat document translation → [sarvam-mcp](../../sarvam-mcp). This skill = **SDK code**.

> Translating short text (a sentence or paragraph)? → [text-translation](../text/SKILL.md) — `client.text.translate()`, not this API.

> [!IMPORTANT]
> Auth: `api-subscription-key` header — NOT `Authorization: Bearer`. Base URL: `https://api.sarvam.ai` (NOT `/v1` — that prefix is only for the OpenAI-compatible chat endpoint)

## What this API does

Translates a **whole document** (PDF, Word, Excel, PowerPoint, HTML) into up to 12 Indian languages per job, preserving layout and formatting. The output is a translated file in the original format — not plain text.

This is an **asynchronous** API. There is no single-call "translate this file" method. Every integration follows five steps: **create → upload → start → poll → export**.

## Supported file formats

| Category | Extensions |
|----------|------------|
| PDF | `.pdf` |
| Word | `.doc`, `.docx`, `.odt` |
| Spreadsheets | `.xls`, `.xlsx`, `.ods` |
| Presentations | `.ppt`, `.pptx`, `.odp` |
| Web pages | `.html`, `.xhtml`, `.mhtml` |

## Quick Start (Python)

```python
import os
from pathlib import Path

import httpx
from sarvamai import SarvamAI

client = SarvamAI(api_subscription_key=os.environ["SARVAM_API_KEY"])
document = Path("report.pdf")

# 1. Create job
job = client.document_translation.create(
    source_language_code="en-IN",
    target_language_codes=["hi-IN", "ta-IN"],
    original_filename=document.name,
)

# 2. Upload to the signed URL (SDK does NOT do this — use httpx/requests)
with document.open("rb") as f:
    httpx.put(
        job.upload_url,
        content=f.read(),
        headers={
            "Content-Type": "application/pdf",
            "x-ms-blob-type": "BlockBlob",
        },
        timeout=120.0,
    )

# 3. Start the pipeline
client.document_translation.start(job_id=job.job_id)

# 4. Poll live-status (every 10-15s) — see references/api-flow.md for full loop
# 5. Export each completed language — see references/api-flow.md
print(job.job_id)
```

## Quick Start (JavaScript/TypeScript)

```typescript
import fs from "fs";
import { SarvamAIClient } from "sarvamai";

const client = new SarvamAIClient({
    apiSubscriptionKey: process.env.SARVAM_API_KEY!,
});
const documentPath = "report.pdf";

// 1. Create job
const job = await client.documentTranslation.create({
    source_language_code: "en-IN",
    target_language_codes: ["hi-IN", "ta-IN"],
    original_filename: documentPath,
});

// 2. Upload to the signed URL (SDK does NOT do this — use fetch)
await fetch(job.upload_url, {
    method: "PUT",
    headers: {
        "Content-Type": "application/pdf",
        "x-ms-blob-type": "BlockBlob",
    },
    body: fs.readFileSync(documentPath),
});

// 3. Start the pipeline
await client.documentTranslation.start(job.job_id);

// 4. Poll live-status (every 10-15s) — see references/api-flow.md for full loop
// 5. Export each completed language — see references/api-flow.md
console.log(job.job_id);
```

## SDK method reference

| Step | Python | JavaScript/TypeScript |
|------|--------|----------------------|
| Create job | `client.document_translation.create(...)` | `client.documentTranslation.create({...})` |
| Start | `client.document_translation.start(job_id=...)` | `client.documentTranslation.start(jobId)` |
| Poll status | `client.document_translation.get_live_status(job_id=...)` | `client.documentTranslation.getLiveStatus(jobId)` |
| Trigger export | `client.document_translation.trigger_export(job_id=..., lang=...)` | `client.documentTranslation.triggerExport(jobId, { lang })` |
| Poll export | `client.document_translation.get_export_status(job_id=..., export_id=...)` | `client.documentTranslation.getExportStatus(jobId, { exportId })` |

## Gotchas

| Gotcha | Detail |
|--------|--------|
| **Upload is manual** | The SDK `create()` returns `upload_url` but does **not** PUT the file. You must upload separately with `httpx`/`fetch`/`curl`, including `x-ms-blob-type: BlockBlob` and a correct `Content-Type` header. Forgetting this leaves the job stuck — `start` will fail validation. |
| **Export is per-language** | `trigger_export` handles **one** target language per call. Loop over `target_language_codes` and call export once for each. There is no "export all" method. |
| **Export before Completed → 409** | Calling `trigger_export` for a language whose `state` is not yet `Completed` returns `409 Conflict`. Gate on `translations[].state`, not `job_state` — languages finish independently. |
| **`job_state` vs per-language `state`** | A job at `PartiallyCompleted` can still have individual languages ready to export. Always check each language's own `state` in `translations[]` before exporting. |
| **Terminal job states** | `Completed`, `PartiallyCompleted`, `Failed` — stop polling when `job_state` reaches one of these. But still check per-language `state` for the export decision. |
| **Odia language code** | `or-IN` in **document** translation — NOT `od-IN` (which is the text translation code). The two APIs use different codes for Odia. |
| **`original_filename` must match** | The filename in `create()` must match the file you upload, including extension. Mismatch causes validation failure at `start`. |
| **Office formats export in original format only** | PDF uploads can optionally export as `pdf`, `docx`, `html`, `txt`, or `epub`. Word/Excel/PowerPoint uploads always export in the original format — `format` is ignored. |
| **Signed URLs expire** | Both `upload_url` and `download_url` expire in 24 hours (`expires_in_hours`). If a download link expires, call `export/status` again for a fresh one. |
| **Poll interval** | Every 10-15 seconds against `live-status`. Faster polling wastes credits; slower delays exports. |
| **Method namespace** | Python: `client.document_translation.*` (snake_case). JS: `client.documentTranslation.*` (camelCase). NOT `client.translate.*` or `client.text.*` — those are the text translation API. |
| **Credits per language** | Billed at ₹5 per 1,000 billable characters **per target language**, counted after parsing (not raw file size). Each language in `target_language_codes` is billed separately. |

## Full Docs

Fetch supported formats, genre options, style guidelines, and language codes from:

- **https://docs.sarvam.ai/llms.txt** — comprehensive docs index
- [Document Translation Overview](https://docs.sarvam.ai/api/api-guides-tutorials/doc-translation/overview)
- [Poll and Export Guide](https://docs.sarvam.ai/api/api-guides-tutorials/doc-translation/how-to/poll-and-export)
- [Rate Limits](https://docs.sarvam.ai/api/ratelimits)
- [references/api-flow.md](references/api-flow.md) — full poll-and-export code loop
