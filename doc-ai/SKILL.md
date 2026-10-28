---
name: doc-ai
description: >-
  Write correct Sarvam Document AI code (Sarvam Vision) — the doc_ai.parse() /
  .extract() / .classify() / .split() job lifecycle for OCR, table conversion,
  schema-based field extraction, document classification, and splitting
  multi-document PDFs, from PDFs, images, and scanned documents. Use this skill
  when building document digitization, structured-data extraction, document
  routing/triage, or RAG-ingestion pipelines in Python or JS/TS. Not for
  translating a document's content into another language — use
  translate/document for that. For live document intelligence in chat via MCP,
  use sarvam-mcp instead.
license: Apache-2.0
metadata:
  author: sarvam-ai
  version: "2.0"
---

# Document AI — Sarvam Vision

> Live in-chat document work → [sarvam-mcp](../sarvam-mcp) (`sarvam_tools_vision_parse` / `_extract` / `_classify` / `_split`). This skill = **SDK code**.

> Translating a document into another language? → [translate/document](../translate/document/SKILL.md) — a different API (`client.document_translation.*`), not this one.

> SDK floor for the code below: Python `sarvamai>=0.1.40`, JS `sarvamai@>=1.1.13`. Older versions have `doc_ai.digitise()` instead of `parse()` and no `classify()`/`split()`.

> [!IMPORTANT]
> Auth: `api-subscription-key` header — NOT `Authorization: Bearer`. Base URL: `https://api.sarvam.ai` (NOT `/v1` — that prefix is only for the OpenAI-compatible chat endpoint)

## What this API does

**Sarvam Vision** is a 3B-parameter document-intelligence model, exposed through the **Document AI** API (SDK group: `doc_ai` / `docAi`). Four job types share one lifecycle (create → poll → fetch):

| Job | What it returns | Best for |
|-----|------------------|----------|
| **Parse** (`doc_ai.parse`) | Full-page OCR: text + layout + tables, as HTML, Markdown, or JSON | Archival, search, RAG ingestion |
| **Extract** (`doc_ai.extract`) | Only the fields you define, as structured JSON/CSV/XLSX | KYC, invoices, forms |
| **Classify** (`doc_ai.classify`) | A label per document (or per page) from categories you define, or a suggested type | Routing, triage |
| **Split** (`doc_ai.split`) | A multi-document PDF divided into child documents with original page numbers | Scanned bundles, mixed batches |

Parse and Extract fetch output with `get_download_url` / `get_results`; **Classify and Split use a different call shape** (a JSON `request` object, see below) and fetch with `get_results`.

Supports PDF, PNG, JPG, and ZIP (flat archive of page images) across 23 languages (22 Indian + English).

## Quick Start — Parse (Python)

```python
import os, time
from sarvamai import SarvamAI

client = SarvamAI(api_subscription_key=os.environ["SARVAM_API_KEY"])

# `file` is a list of (filename, fileobj, content_type) tuples — even for one document
with open("document.pdf", "rb") as f:
    job = client.doc_ai.parse(
        file=[("document.pdf", f, "application/pdf")],
        language="hi-IN",
        # `parse()` has no output_format kwarg (output is HTML by default) — send it as a raw form field:
        request_options={"additional_body_parameters": {"output_format": "md"}},   # "html", "md", or "json"
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

## Quick Start — Parse (JavaScript/TypeScript)

```typescript
import fs from "fs";
import { SarvamAIClient } from "sarvamai";

const client = new SarvamAIClient({ apiSubscriptionKey: process.env.SARVAM_API_KEY });

// `file` is an array, even for one document
// `parse()` has no output_format option in JS — output is HTML. For md/json, POST /doc-ai/v1/job/parse
// directly with an `output_format` form field.
const job = await client.docAi.parse({
  file: [fs.createReadStream("document.pdf")],
  language: "hi-IN",
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

## Classify and Split

Both take the file(s) **plus a required `request` object** that holds the options. They return an acceptance object (`status="accepted"`), then you poll and fetch `get_results`.

```python
cats = [
    {"type": "invoice", "description": "A supplier bill with totals and payment details."},
    {"type": "bank_statement", "description": "A bank account statement."},
]

# Classify — scope "document" (default) gives one label; "page" gives one per page
with open("bundle.pdf", "rb") as f:
    job = client.doc_ai.classify(
        file=[("bundle.pdf", f, "application/pdf")],
        request={"config": {"scope": "page", "categories": cats}},
    )

# Split — methods: "semantic" (default), "fixed_pages", "page_ranges", "triggers"
with open("bundle.pdf", "rb") as f:
    job = client.doc_ai.split(
        file=[("bundle.pdf", f, "application/pdf")],
        request={"config": {"method": "semantic", "classify_segments": True, "categories": cats}},
    )

# ... poll get_status() as above, then:
r = client.doc_ai.get_results(job_id=job.job_id)          # include="details" adds pages/evidence
for seg in r.result.segments:                              # Split
    print(seg.pages, seg.type, seg.review_required)
# Classify: r.result.type (scope "document") or r.result.decisions[i].type / .input_page (scope "page")
```

```typescript
const job = await client.docAi.split({
  file: [fs.createReadStream("bundle.pdf")],
  request: { config: { method: "fixed_pages", pages_per_segment: 2, classify_segments: false } },
});
// ... poll getStatus(job.job_id), then:
const r: any = await client.docAi.getResults(job.job_id, { include: "details" });
console.log(r.result.segments.map((s: any) => [s.pages, s.type]));
```

## Gotchas

| Gotcha | Detail |
|--------|--------|
| **`file` is always a list** | Even for a single document: `file=[(name, fileobj, content_type)]` (Python) / `file: [stream]` (JS). A bare stream in JS fails with `TypeError: request.file is not iterable`. |
| **`job_id` is positional in JS** | `getStatus(job.job_id)`, `getDownloadUrl(job.job_id)`, `getResults(job.job_id)` — NOT `getStatus({ job_id })`. Passing an object sends `[object Object]` as the path segment and the service rejects it as a non-UUID. Python keeps the kwarg form: `get_status(job_id=...)`. |
| **`schema` is a JSON string** | Sent as a multipart form field: `json.dumps(schema)` in Python, `JSON.stringify(schema)` in JS — not a raw object/dict. |
| **JS uses wire names, not camelCase** | Unlike the rest of the JS SDK, `doc_ai` params/fields are snake_case on the wire: `output_format` (not `outputFormat`), `job_id`, `pages_processed`. Only the method names (`parse`, `getStatus`) are camelCased. |
| **`language`, not `language_code`** | Document AI takes `language`. Passing `language_code` (the STT/translate convention) is silently ignored. |
| **`output_format` values** | `"html"` (default), `"md"`, or `"json"` for Parse; `"json"` (default), `"csv"`, or `"xlsx"` for Extract. `"markdown"` returns `400` — use `"md"`. The SDK's `parse()` does not expose the field: Python needs `request_options={"additional_body_parameters": {...}}`; JS silently returns HTML (use REST for md/json). `extract()` takes `output_format` normally. |
| **Don't use `get_results` for Parse jobs** | Parse output comes from `get_download_url` (a ZIP). In Python `get_results()` on a Parse job raises a pydantic `ValidationError` — the API tags it `type: "digitise"`, which the SDK's result union doesn't accept. `get_results` is for Extract, Classify and Split. |
| **Classify/Split need `request`, and `config` is required** | `classify(file=...)` without `request={"config": {...}}` fails with `400 missing property 'config'`. To let the API suggest a document type, send `request={"config": {}}`. In JS, `request` is a property of the options object next to `file`. |
| **Don't use `execution: "auto"` via the SDK** | The API answers with `200` and the finished results body, but the SDK types the response as the `201` accepted object. Python raises `ValidationError` (the job was still created — you lose its `job_id`); JS returns the results at runtime but typed as if `status_url`/`results_url` exist. Submit normally and poll. |
| **Split: set `classify_segments` deliberately** | It defaults to `true` and then requires `categories` — omitting them returns `400 at '/config': missing property 'categories'`. Pass `"classify_segments": False` when you are not supplying categories. Segments come back with `type: None` and `classification_status: "not_requested"` in that case. |
| **Split `triggers`: `match` takes `equals` / `prefix` / `regex`** | Not `text`: `{"type": "text", "match": {"text": "INVOICE"}}` returns `400 additional properties 'text' not allowed`. Use `{"type": "text", "match": {"prefix": "INVOICE"}}`. Each marker page starts a new document. |
| **Classify a bundle → `type` is null** | A file containing several documents returns `classification_status: "mixed"`, `type: null`, and `MULTIPLE_DOCUMENTS_DETECTED` in `review_reasons` — not a wrong label. Split first, or use `scope: "page"`. |
| **`completed` ≠ trustworthy** | For Classify and Split, check `review_required` (and each segment's `review_required`) before acting on a label. `confidence` can be `null`. |
| **Idempotency key** | Python `idempotency_key="..."`; JS `"Idempotency-Key": "..."` in the options object. Same key + same request returns the same `job_id` (`idempotency_replayed: true`); same key + a changed request raises `409 ConflictError`. |
| **10-page cap (Parse/Extract)** | PDF and ZIP uploads are capped at 10 pages/images per job — exceeding it returns `400 invalid_request_error`. Split larger documents before uploading. |
| **Legacy `document_intelligence` group** | `document_intelligence.create_job()/upload_file()/start()/wait_until_complete()/download_output()` still works for existing integrations, but new code should use `doc_ai.parse()`/`.extract()` — one call creates and submits the job, no separate upload/start step. |
| **Terminal states** | `completed`, `partially_completed`, `failed`, `rejected`. Only fetch output/results when `completed` or `partially_completed`. Classify/Split jobs start as `accepted`. |
| **`digitise` was renamed `parse`** | Python `0.1.40` / JS `1.1.13` removed `doc_ai.digitise()` / `docAi.digitise()` in favour of `parse()`; params are otherwise unchanged. The REST path is `/doc-ai/v1/job/parse` (`/digitise` still answers). |

## Full Docs

Fetch schema rules, table-extraction details, and rate limits from:

- **https://docs.sarvam.ai/llms.txt** — comprehensive docs index
- [Document AI Overview](https://docs.sarvam.ai/api/api-guides-tutorials/document-intelligence/overview)
- [Sarvam Vision Model Page](https://docs.sarvam.ai/api/getting-started/models/sarvam-vision)
- [Rate Limits](https://docs.sarvam.ai/api/ratelimits)
