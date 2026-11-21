# Document Translation API — poll and export reference

Base: `https://api.sarvam.ai/translate/document`

## Endpoint summary

| Step | Method | Path |
|------|--------|------|
| Create job | POST | `/jobs` |
| Upload file | PUT | `{upload_url}` (absolute URL from create response) |
| Start | POST | `/jobs/{job_id}/start` |
| Poll status | GET | `/jobs/{job_id}/live-status` |
| Trigger export | POST | `/jobs/{job_id}/export?lang={code}` |
| Poll export | GET | `/jobs/{job_id}/export/status?export_id={export_id}` |

## Create body (example)

```json
{
  "source_language_code": "en-IN",
  "target_language_codes": ["hi-IN", "ta-IN"],
  "original_filename": "report.pdf"
}
```

Optional fields: `job_name`, `genre`, `style_guidelines`, `language_specific_guidelines`, `use_native_numerals`.

## Upload (curl)

```bash
curl -X PUT "$UPLOAD_URL" \
  -H "x-ms-blob-type: BlockBlob" \
  -H "Content-Type: application/pdf" \
  --data-binary @report.pdf
```

## Full poll-and-export loop (Python)

```python
import time
from sarvamai import SarvamAI

client = SarvamAI()
job_id = "your-job-id"
target_codes = ["hi-IN", "ta-IN"]
TERMINAL = {"Completed", "PartiallyCompleted", "Failed"}

# 4. Poll live-status
while True:
    status = client.document_translation.get_live_status(job_id=job_id)
    print(f"job_state={status.job_state} progress={status.progress}%")
    if status.job_state in TERMINAL:
        break
    time.sleep(12)

# 5. Export each completed language
downloads = {}
for t in (status.translations or []):
    if t.state != "Completed":
        continue
    export = client.document_translation.trigger_export(
        job_id=job_id, lang=t.target_language_code
    )
    while True:
        export_status = client.document_translation.get_export_status(
            job_id=job_id, export_id=export.export_id
        )
        if export_status.export_state == "Completed":
            downloads[t.target_language_code] = export_status.download_url
            break
        if export_status.export_state == "Failed":
            raise RuntimeError(f"Export failed for {t.target_language_code}")
        time.sleep(5)

print("Downloads:", downloads)
```

## Full poll-and-export loop (JavaScript/TypeScript)

```javascript
const TERMINAL = new Set(["Completed", "PartiallyCompleted", "Failed"]);

// 4. Poll live-status
let status;
while (true) {
    status = await client.documentTranslation.getLiveStatus(jobId);
    console.log(`job_state=${status.job_state} progress=${status.progress}%`);
    if (TERMINAL.has(status.job_state)) break;
    await new Promise((r) => setTimeout(r, 12_000));
}

// 5. Export each completed language
const downloads = {};
for (const t of status.translations ?? []) {
    if (t.state !== "Completed") continue;
    const exportJob = await client.documentTranslation.triggerExport(jobId, {
        lang: t.target_language_code,
    });
    while (true) {
        const exportStatus = await client.documentTranslation.getExportStatus(
            jobId, { exportId: exportJob.export_id }
        );
        if (exportStatus.export_state === "Completed") {
            downloads[t.target_language_code] = exportStatus.download_url;
            break;
        }
        if (exportStatus.export_state === "Failed") {
            throw new Error(`Export failed for ${t.target_language_code}`);
        }
        await new Promise((r) => setTimeout(r, 5_000));
    }
}
console.log("Downloads:", downloads);
```

## Terminal job states

`Completed`, `PartiallyCompleted`, `Failed` — stop polling when `job_state` reaches one of these. But still check each `translations[].state` before exporting: a `PartiallyCompleted` job has some languages that succeeded and some that failed.

## Export notes

- One export call **per target language** — there is no batch export.
- Call export only when that language's `state` is `Completed` (otherwise `409 Conflict`).
- Download from `download_url` when `export_state` is `Completed`.
- Signed download URLs expire in 24 hours; call `export/status` again for a fresh link.
