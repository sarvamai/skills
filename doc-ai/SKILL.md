---
name: doc-ai
description: >-
  Write correct Sarvam Document AI code (Sarvam Vision) — the doc_ai.digitise(),
  doc_ai.extract(), doc_ai.split() and doc_ai.classify() job lifecycle for OCR,
  table conversion, schema-based field extraction, document splitting and
  classification of PDFs, images, and scanned documents. Use this skill when
  building document digitization, structured-data extraction, bundle splitting,
  document routing, or RAG-ingestion pipelines in Python or JS/TS. Not for
  translating a document's content into another language — use translate/document
  for that. For live document intelligence in chat via MCP, use sarvam-mcp instead.
license: Apache-2.0
metadata:
  author: sarvam-ai
  version: "1.0"
---

# Document AI — Sarvam Vision

> Live in-chat document extraction → [sarvam-mcp](../sarvam-mcp) (`sarvam_tools_vision_extract`). This skill = **SDK code**.

> Translating a document into another language? → [translate/document](../translate/document/SKILL.md) — a different API (`client.document_translation.*`), not this one.

> [!IMPORTANT]
> Auth: `api-subscription-key` header — NOT `Authorization: Bearer`. Base URL: `https://api.sarvam.ai` (NOT `/v1` — that prefix is only for the OpenAI-compatible chat endpoint)

## What this API does

**Sarvam Vision** is a 3B-parameter document-intelligence model, exposed through the **Document AI** API (SDK group: `doc_ai` / `docAi`). Four job types share one lifecycle (create → poll → fetch):

| Job | What it returns | Best for |
|-----|------------------|----------|
| **Digitise** (`doc_ai.digitise`) | Full-page OCR: text + layout + tables, as HTML, Markdown, or JSON | Archival, search, RAG ingestion |
| **Extract** (`doc_ai.extract`) | Only the fields you define, as structured JSON/CSV/XLSX | KYC, invoices, forms |
| **Split** (`doc_ai.split`) | Child documents, each with its original page numbers and a `document_ref` | A bundle that holds several documents — a scanned stack of invoices and receipts |
| **Classify** (`doc_ai.classify`) | A document type, or one per page, with evidence and a `review_required` flag | Routing and triage before extraction; works with or without categories |

Endpoints: `POST /doc-ai/v1/job/{digitise,extract,split,classify}`, then `GET /doc-ai/v1/job/{job_id}/status`, `/results` and `/download-url`.

PDF, PNG and JPG are accepted by every job; TIFF is accepted by Split and Classify; ZIP (a flat archive of JPG/PNG page images) by Digitise and Extract. All four cover 23 languages (22 Indian + English).

**Limits** — from the [Languages, Formats & Limits](https://docs.sarvam.ai/api/api-guides-tutorials/document-intelligence/languages-formats-limits) page:

| Limit | Digitise | Extract | Split / Classify |
|-------|----------|---------|------------------|
| Pages per PDF | 30 | 20 | 500 |
| Images per ZIP | 30 | 20 | n/a |
| File size | 200 MB | 200 MB | 512 MB per document |

Split and Classify additionally accept up to 10 documents per request, up to 20 categories, and up to 1,000 segments.

## Quick Start — Digitise (Python)

```python
import os, time
from sarvamai import SarvamAI

client = SarvamAI(api_subscription_key=os.environ["SARVAM_API_KEY"])

# `file` is a list of (filename, fileobj, content_type) tuples — even for one document
with open("document.pdf", "rb") as f:
    job = client.doc_ai.digitise(
        file=[("document.pdf", f, "application/pdf")],
        language="hi-IN",
        output_format="md",   # "html" (default), "md", or "json"
    )

TERMINAL = {"completed", "partially_completed", "failed", "rejected"}
while True:
    st = client.doc_ai.get_status(job_id=job.job_id)
    if st.status.lower() in TERMINAL:
        break
    time.sleep(5)

dl = client.doc_ai.get_download_url(job_id=job.job_id)
print("download:", dl.method, dl.url)   # a ZIP: primary file + per-page metadata JSON
```

## Quick Start — Digitise (JavaScript/TypeScript)

```typescript
import fs from "fs";
import { SarvamAIClient } from "sarvamai";

const client = new SarvamAIClient({ apiSubscriptionKey: process.env.SARVAM_API_KEY });

// `file` is an array, even for one document
const job = await client.docAi.digitise({
  file: [fs.createReadStream("document.pdf")],
  language: "hi-IN",
  output_format: "md",
});

const TERMINAL = new Set(["completed", "partially_completed", "failed", "rejected"]);
let st;
while (true) {
  st = await client.docAi.getStatus(job.job_id);   // positional — NOT { job_id }
  if (TERMINAL.has(st.status.toLowerCase())) break;
  await new Promise((resolve) => setTimeout(resolve, 5000));
}

const dl = await client.docAi.getDownloadUrl(job.job_id);   // also positional
console.log("download:", dl.method, dl.url);
```

## Extract (schema-based fields)

Same lifecycle, but pass a `schema` (or a saved `config_id`) alongside the file:

```python
import json
schema = {
    "type": "object",
    "properties": {
        "policy_number": {"type": "string", "description": "Insurance policy number"},
        "sum_insured":   {"type": "number", "description": "Total sum insured, in INR"},
    },
}

with open("insurance-policy.pdf", "rb") as f:
    job = client.doc_ai.extract(
        file=[("insurance-policy.pdf", f, "application/pdf")],
        schema=json.dumps(schema),   # JSON string, not a dict — or pass config_id="cfg_abc123" instead
        language="en-IN",
        output_format="json",
    )
# ... poll get_status() same as above, then:
results = client.doc_ai.get_results(job_id=job.job_id)
print(results.result)   # {"policy_number": ..., "sum_insured": ...}
```

## Gotchas

| Gotcha | Detail |
|--------|--------|
| **`file` is always a list** | Even for a single document: `file=[(name, fileobj, content_type)]` (Python) / `file: [stream]` (JS). A bare stream in JS fails with `TypeError: request.file is not iterable`. |
| **`job_id` is positional in JS** | `getStatus(job.job_id)`, `getDownloadUrl(job.job_id)`, `getResults(job.job_id)` — NOT `getStatus({ job_id })`. Passing an object sends `[object Object]` as the path segment and the service rejects it as a non-UUID. Python keeps the kwarg form: `get_status(job_id=...)`. |
| **`schema` is a JSON string** | Sent as a multipart form field: `json.dumps(schema)` in Python, `JSON.stringify(schema)` in JS — not a raw object/dict. |
| **JS uses wire names, not camelCase** | Unlike the rest of the JS SDK, `doc_ai` params/fields are snake_case on the wire: `output_format` (not `outputFormat`), `job_id`, `pages_processed`. Only the method names (`digitise`, `getStatus`) are camelCased. |
| **`language`, not `language_code`** | Document AI takes `language`. Passing `language_code` (the STT/translate convention) is silently ignored. |
| **`output_format` values** | `"html"` (default), `"md"`, or `"json"` for Digitise; `"json"` (default), `"csv"`, or `"xlsx"` for Extract. `"markdown"` returns `400` — use `"md"`. |
| **Page limits differ per job** | Digitise takes up to 30 pages per PDF (30 images per ZIP) and Extract up to 20; Split and Classify take up to 500 pages and 512 MB per document. Exceeding a limit returns `400 invalid_request_error`. Batch larger documents before uploading. |
| **Split/Classify need the SDK alpha** | `doc_ai.split()` and `doc_ai.classify()` are documented against the `sarvamai` Python and TypeScript alpha builds; the released SDKs (checked 2026-10-27) still expose only `digitise`/`extract`. Pin the alpha, or call `POST /doc-ai/v1/job/split` / `/classify` directly. |
| **Legacy `document_intelligence` group** | `document_intelligence.create_job()/upload_file()/start()/wait_until_complete()/download_output()` still works for existing integrations, but new code should use `doc_ai.digitise()`/`.extract()` — one call creates and submits the job, no separate upload/start step. |
| **Terminal states** | `completed`, `partially_completed`, `failed`, `rejected`. Only fetch output/results when `completed` or `partially_completed`. |

## Full Docs

Fetch schema rules, table-extraction details, and rate limits from:

- **https://docs.sarvam.ai/llms.txt** — comprehensive docs index
- [Document AI Overview](https://docs.sarvam.ai/api/api-guides-tutorials/document-intelligence/overview)
- [Sarvam Vision Model Page](https://docs.sarvam.ai/api/getting-started/models/sarvam-vision)
- [Languages, Formats & Limits](https://docs.sarvam.ai/api/api-guides-tutorials/document-intelligence/languages-formats-limits)
- [How to split a document bundle](https://docs.sarvam.ai/api/api-guides-tutorials/document-intelligence/how-to/split)
- [How to classify documents](https://docs.sarvam.ai/api/api-guides-tutorials/document-intelligence/how-to/classify)
- [Rate Limits](https://docs.sarvam.ai/api/ratelimits)
