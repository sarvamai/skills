---
name: document-intelligence
description: >-
  Write correct Sarvam Document Intelligence code — digitise scanned/PDF
  documents to HTML/Markdown and extract structured fields via `doc_ai`
  (current), plus the legacy `document_intelligence` job API and its silent
  parameter traps. Use this skill when building OCR, document parsing, or
  structured-extraction features in Python or JS/TS. For live document
  extraction in chat via MCP, use sarvam-mcp instead.
license: Apache-2.0
metadata:
  author: sarvam-ai
  version: "1.1"
---

# Document Intelligence — Sarvam AI

> Live in-chat document extraction → [sarvam-mcp](../sarvam-mcp) (`sarvam_tools_vision_extract` → `_vision_job_status`). This skill = **SDK code**.

> [!IMPORTANT]
> Auth: `api-subscription-key` header — NOT `Authorization: Bearer`. Base URL: `https://api.sarvam.ai` (NOT `/v1` — that prefix is only for the OpenAI-compatible chat endpoint)

## Two unrelated APIs — pick `doc_ai`

The SDK exposes **two separate clients that do not wrap each other** — different URL namespaces, different types, different job-state vocabularies:

| | `client.doc_ai` (JS: `docAi`) | `client.document_intelligence` (JS: `documentIntelligence`) |
|---|---|---|
| Status | **Current** (`/doc-ai/v1/job/*`) | **Legacy** (`/document-intelligence/*`) |
| Capabilities | Digitise (HTML/MD) **and** schema-based structured **extract** (JSON/CSV/XLSX) | Digitise only (HTML/MD/JSON) |
| Upload | One call — pass `file` directly, or `upload_ids` from a presign step | Two-step: `get_upload_links` then upload, or use the `create_job()` wrapper below |
| Size limit | Not stated in the SDK docstrings — confirm current limits in the API reference before assuming a cap | 200MB file size, 500 pages/images (stated in the `start()` docstring) |
| Job states | `completed` / `partially_completed` / `failed` / `rejected` | `Accepted` → `Pending` → `Running` → `Completed` / `PartiallyCompleted` / `Failed` |

Default to `doc_ai` for new code. Reach for `document_intelligence` only if you specifically need its high-level polling wrapper or are matching existing legacy job IDs.

## Quick Start — `doc_ai` (Python)

```python
from sarvamai import SarvamAI
client = SarvamAI()

# Digitise: scanned/PDF -> structured HTML or Markdown
job = client.doc_ai.digitise(
    file=[open("invoice.pdf", "rb")],
    output_format="md",
    content_type="printed"   # "printed" | "handwritten" | "mixed"
)

# Extract: pull specific fields per a JSON schema
import json
schema = json.dumps({
    "type": "object",
    "properties": {
        "invoice_number": {"type": "string", "description": "The invoice number"},
        "total": {"type": "number", "description": "The total amount due"}
    }
})
job = client.doc_ai.extract(file=[open("invoice.pdf", "rb")], schema=schema, output_format="json")

# Poll until terminal, then fetch results
status = client.doc_ai.get_status(job.job_id)
result = client.doc_ai.get_results(job.job_id)
```

## Quick Start — `doc_ai` (JavaScript/TypeScript)

```typescript
import { SarvamAIClient } from "sarvamai";
import * as fs from "fs";

const client = new SarvamAIClient({ apiSubscriptionKey: "YOUR_SARVAM_API_KEY" });

// NOTE: request fields are snake_case even in the JS/TS SDK — this is a raw
// pass-through type, NOT camelCase like most other SarvamAIClient methods.
const job = await client.docAi.digitise({
    file: [fs.createReadStream("invoice.pdf")],
    output_format: "md",
    content_type: "printed"
});

const status = await client.docAi.getStatus(job.job_id);   // response fields are snake_case too
const result = await client.docAi.getResults(job.job_id);
```

## Quick Start — `document_intelligence` (legacy, Python)

```python
from sarvamai import SarvamAI
client = SarvamAI()

job = client.document_intelligence.create_job(language="hi-IN", output_format="md")
job.upload_file("scan.pdf")   # PDF, PNG, JPG, or ZIP (ZIP = multiple images, flat, JPEG/PNG only)
job.start()
job.wait_until_complete()
job.download_output("./output.zip")
```

## Quick Start — `document_intelligence` (legacy, JavaScript/TypeScript)

```typescript
// NOTE: this wrapper (unlike docAi) genuinely uses camelCase — it's hand-written,
// not a raw Fern pass-through, and translates outputFormat -> output_format internally.
const job = await client.documentIntelligence.createJob({ language: "hi-IN", outputFormat: "md" });
await job.uploadFile("scan.pdf");
await job.start();
await job.waitUntilComplete();
await job.downloadOutput("./output.zip");
```

## Gotchas

| Gotcha | Detail |
|--------|--------|
| **`document_intelligence` param is `language`, NOT `language_code`** | Every other Sarvam API uses `language_code`. This one uses `language` — send `language_code` and it's silently ignored, defaulting to `hi-IN`. |
| **`document_intelligence` output_format is `"md"`, not `"markdown"`** | Passing `"markdown"` returns a **400**. Accepted values: `md`, `html`, `json`. |
| **`document_intelligence` Odia code is `or-IN`** | Every other Sarvam API (translate, STT, TTS) uses `od-IN` for Odia and explicitly rejects `or-IN`. This one is the opposite — it lists `or-IN` as the supported Odia code. Don't copy the `od-IN` convention here without checking. |
| **`doc_ai` output formats differ by operation** | `digitise()` → `"html"` \| `"md"` only. `extract()` → `"json"` \| `"csv"` \| `"xlsx"`. Passing an extract format to digitise (or vice versa) is invalid. |
| **`doc_ai` booleans are strings** | `auto_orient` (digitise + extract) and `classification` (extract only) are typed `Optional[str]`, not `bool` — send the literal text `"true"`/`"false"`, not a native boolean. Passing `True`/`False` in Python serializes wrong. |
| **`content_type` on `digitise()`** | `"printed"` \| `"handwritten"` \| `"mixed"` — hints the model at document nature; not present on `extract()`. |
| **`extract()` needs exactly one of `schema` / `config_id`** | `schema` is an inline JSON string — root must be `type: "object"` with non-empty `properties`, every field needs `type` + a non-empty `description`, max nesting depth 4. `config_id` references a saved config created via the dashboard/API instead. Passing both or neither fails. |
| **`digitise()`/`extract()` need exactly one of `file` / `upload_ids`** | `upload_ids` is a comma-separated string from `doc_ai.create_upload_url()` (presigned direct upload) — not a list. |
| **Results are unavailable mid-job** | `get_results()` / `get_download_url()` / `document_intelligence`'s download step all return **409** until the job reaches a terminal status. Poll `get_status()` first. |
| **`doc_ai` has no `create_job()` wrapper** | Unlike `document_intelligence` and `speech_to_text_job`, `doc_ai.digitise()`/`.extract()` create *and* start the job in one call — there's no separate `initialise`/`start` split to orchestrate. |
| **JS field casing is inconsistent between the two clients** | `docAi.digitise()`/`.extract()` are raw Fern pass-throughs — request **and response** fields stay snake_case even in JS/TS (`output_format`, `upload_ids`, `job_id`). `documentIntelligence.createJob()` is a hand-written wrapper that genuinely uses camelCase (`outputFormat`) and translates internally; its job object exposes both `.jobId` and a `.job_id` alias. Don't assume one convention applies to both clients. |
| **Extract confidence scores** | Extract results include `result` (the values) plus a parallel `annotations` tree mirroring the same shape where every leaf carries `confidence` and `sources` — use `annotations` to flag low-confidence fields for human review, don't assume `result` values are always correct. |

## Full Docs

Fetch job lifecycle details, schema rules, and dashboard-based workflows from:

- **https://docs.sarvam.ai/llms.txt** — comprehensive docs index
- [Doc AI Overview](https://docs.sarvam.ai/docai/getting-started/overview)
- [Digitise a Document](https://docs.sarvam.ai/docai/how-to/digitise-a-document)
- [Extract Structured Fields](https://docs.sarvam.ai/docai/how-to/extract-fields-from-a-document/extract-structured-fields)
- [Create a Reusable Extraction Config](https://docs.sarvam.ai/docai/how-to/extract-fields-from-a-document/create-a-reusable-config)
- [API Reference — doc-ai/job/*](https://docs.sarvam.ai/api-reference/doc-ai/job/digitise)
- [API Reference — legacy/document-intelligence/*](https://docs.sarvam.ai/api-reference/legacy/document-intelligence/initialise)
- [Rate Limits](https://docs.sarvam.ai/api/ratelimits)
