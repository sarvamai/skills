---
name: dubbing
description: >-
  Write correct Sarvam Dubbing API code — async create → upload → start →
  poll → export pipeline for localizing video/audio into 12 Indian languages
  with speaker voice cloning. Use this skill when building a dub-a-video/audio
  feature in Python or JS/TS. For translating written documents, use
  translate/document instead. For live dubbing in chat via MCP, use
  sarvam-mcp instead.
license: Apache-2.0
metadata:
  author: sarvam-ai
  version: "1.1"
---

# Dubbing — Sarvam AI

> Live in-chat dubbing → [sarvam-mcp](../sarvam-mcp) (`sarvam_tools_dub`). This skill = **SDK code**.

> Translating a PDF/Word/Excel file's text? → [translate/document](../translate/document/SKILL.md) — a different API.

> [!IMPORTANT]
> Auth: `api-subscription-key` header — NOT `Authorization: Bearer`. Base URL: `https://api.sarvam.ai`.
> `client.dubbing.upload()` requires `sarvamai>=0.1.31a1`.

## What this API does

Localizes a video or audio file into up to 12 Indian languages **in one job**, preserving each speaker's voice via voice cloning, and exports dubbed video, isolated audio, and SRT subtitles. Async, like `translate/document`, but **exports fire automatically** once the pipeline finishes — no manual per-language trigger call needed (unlike document translation).

Every integration follows five steps: **create → upload → start → poll status → poll exports**.

## Quick Start (Python)

```python
import os, time
from pathlib import Path
from sarvamai import SarvamAI

client = SarvamAI(api_subscription_key=os.environ["SARVAM_API_KEY"])
media = Path("sample.mp4")

# 1. Create job (does not accept the file itself)
created = client.dubbing.create(
    source_language_code="en-IN",
    target_language_codes=["hi-IN", "ta-IN"],
    export_options=["video", "srt"],
    voice_cloning=True,
    num_speakers=1,
    job_name=media.name,
)
job_id = created.data.job_id

# 2. Upload — the SDK handles the signed PUT + x-ms-blob-type header for you
client.dubbing.upload(created.data.upload_url, media)

# 3. Start the pipeline — wrap in try/except (see Gotchas: start() currently
#    throws a pydantic ValidationError even on success in some SDK versions)
try:
    client.dubbing.start(job_id=job_id)
except Exception:
    pass  # job starts server-side regardless — confirm via get_live_status below

# 4. Poll until the dub itself is done (exports still render after this)
TERMINAL = {"completed", "partial_failure", "failed", "deleted"}
while True:
    job = client.dubbing.get_live_status(job_id=job_id).data
    if job.status in TERMINAL:
        break
    time.sleep(15)

if job.status == "failed":
    raise RuntimeError(job.error_message or "job failed")

# 5. Poll export-status for the actual download links (limit defaults to 5 — set it high)
exports = client.dubbing.get_export_status(job_id=job_id, limit=100).data.exports
downloads = {(e.target_language, e.export_type): e.download_url for e in exports if e.status == "completed"}
print(downloads)
```

## Quick Start (JavaScript/TypeScript)

```typescript
import fs from "fs";
import { SarvamAIClient } from "sarvamai";

const client = new SarvamAIClient({ apiSubscriptionKey: process.env.SARVAM_API_KEY });

// 1. Create job — JS wants the RAW WIRE field names src_lang/target_langs
//    here, NOT source_language_code/target_language_codes (see Gotchas —
//    this differs from what Sarvam's own docs sample currently shows)
const created = await client.dubbing.create({
  src_lang: "en-IN",
  target_langs: ["hi-IN", "ta-IN"],
  export_options: ["video", "srt"],
  voice_cloning: true,
  num_speakers: 1,
  job_name: "sample.mp4",
});
const jobId = created.data.job_id;

// 2. Upload to the signed URL (no documented JS upload helper — PUT it yourself)
await fetch(created.data.upload_url, {
  method: "PUT",
  headers: { "Content-Type": "video/mp4", "x-ms-blob-type": "BlockBlob" },
  body: fs.readFileSync("sample.mp4"),
});

// 3. Start — job_id is positional
await client.dubbing.start(jobId);

// 4. Poll live status — also positional
let job;
do {
  job = (await client.dubbing.getLiveStatus(jobId)).data;
  await new Promise((r) => setTimeout(r, 15000));
} while (!["completed", "partial_failure", "failed", "deleted"].includes(job.status));

// 5. Poll export status for download links
const exports = (await client.dubbing.getExportStatus(jobId, { limit: 100 })).data.exports;
console.log(exports.filter((e) => e.status === "completed"));
```

## Gotchas

| Gotcha | Detail |
|--------|--------|
| **Exports are automatic** | Unlike `translate/document`'s per-language `trigger_export`, dubbing auto-produces every format in `export_options` once the pipeline finishes (as long as `editor_flow` stays `false`, the default). There is no manual export-trigger call. |
| **`editor_flow: true` doubles the cost** | ₹80/min vs ₹40/min on Starter, and it **suppresses auto-export** entirely (exports must be triggered manually in Creator Studio instead) — leave it `false` for API integrations. |
| **Python has a documented upload helper** | `client.dubbing.upload(upload_url, media)` (`sarvamai>=0.1.31a1`) handles the signed PUT including the `x-ms-blob-type: BlockBlob` header, and accepts a path or an open binary file. No JS equivalent exists — PUT the file yourself with `fetch` and the same header, same as `translate/document`. |
| **Python `start()` can throw even when the job starts fine** | Verified live against `sarvamai==0.1.34`: `client.dubbing.start(job_id=...)` raised `pydantic.ValidationError: data.job_id Field required` — the server's actual response body is `{"data": {"project_id": ..., "status": "queued", ...}}`, no `job_id` key, which the Python SDK's response model doesn't expect. The job **does** start server-side regardless (confirmed via `get_live_status` and a raw REST call) — wrap the `start()` call in try/except and move on to polling `get_live_status()`, which parses fine. This is Python-specific: `client.dubbing.start(jobId)` in JS (`sarvamai@1.1.10`) returned the same `project_id`-shaped body without error, since the JS SDK doesn't validate response shape as strictly. Re-check if a newer `sarvamai` (Python) has fixed this before assuming it's still broken. |
| **JS `create()` needs `src_lang`/`target_langs`, not `source_language_code`/`target_language_codes`** | Verified live against `sarvamai@1.1.10`: passing `source_language_code`/`target_language_codes` — the exact field names shown in Sarvam's own published TS "SDK Code" sample for this endpoint — returns `400 InvalidInputError: src_lang: Field required, target_langs: Field required`. The JS SDK does **not** translate those field names to wire format for this call; only `src_lang`/`target_langs` work. This is a bug in Sarvam's own docs example, not a hypothetical — don't trust that sample as-is. (Python's `source_language_code`/`target_language_codes` do work correctly — this is JS-only.) |
| **`job_id` is positional in JS** | `client.dubbing.start(jobId)`, `.getLiveStatus(jobId)`, `.getExportStatus(jobId, { limit })` — not `{ job_id }`. Python keeps the kwarg form (`job_id=...`). |
| **`limit` defaults to 5 on export-status** | A 2-language × 3-format job has 6 export entries; the default `limit=5` silently truncates the list. Pass `limit` comfortably above `languages × formats` (max `100`). |
| **`export` vs `exports` in live-status** | A single-target-language job populates `export` (object) and leaves `exports` `null`; 2+ languages does the reverse. Handle both keys — don't assume one is always populated. Use `export-status` (not `live-status`) as the source of truth for downloads either way. |
| **`partial_failure` is terminal and has real output** | Treat it alongside `completed` when deciding to stop polling — some languages may have succeeded even if others failed. `failed` is the only terminal status with nothing to collect. |
| **`completed` job ≠ downloadable files yet** | Exports render after the dub finishes. Poll `export-status` and only download entries whose own `status` is `completed`. |
| **Odia is `or-IN` here** | Same as `translate/document`, NOT `od-IN` (the STT/text-translation code) — dubbing and document translation share the `or-IN` convention. |
| **Media validated at `start`, not at upload** | Storage accepts whatever bytes you send; an unsupported/corrupt file only surfaces as a `failed` job (check `error_message`) after `start`, not as an upload-time error. |
| **Signed URLs expire** | `upload_url` and `download_url` are short-lived (~24h for downloads). Re-poll `export-status` for a fresh download link rather than caching the URL. |
| **File limits** | Max size/duration depend on plan: 2GB/1hr (Starter), 3GB/1hr (Pro), 4GB/4hr (Business). |

## Full Docs

Fetch voice options, register/tone control, and the full job-lifecycle reference from:

- **https://docs.sarvam.ai/llms.txt** — comprehensive docs index
- [Dubbing Overview](https://docs.sarvam.ai/api/api-guides-tutorials/dubbing/overview)
- [Job Lifecycle](https://docs.sarvam.ai/api/api-guides-tutorials/dubbing/job-lifecycle)
- [Rate Limits](https://docs.sarvam.ai/api/ratelimits)
