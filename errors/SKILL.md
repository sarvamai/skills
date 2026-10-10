---
name: errors
description: >-
  Handle Sarvam AI API errors correctly — the error body shape, which HTTP
  statuses mean what (auth is 403, not 401), the SDK exception classes in
  Python and JS/TS, which errors to retry, and the SDK's built-in retries.
  Use this skill when writing try/except or try/catch around any Sarvam SDK
  call, adding retry/backoff, debugging a failed request, or turning an API
  error into a user-facing message. Pair it with the product skill (chat,
  speech-to-text, text-to-speech, translate, doc-ai, dubbing) for that
  API's own error cases.
license: Apache-2.0
metadata:
  author: sarvam-ai
  version: "1.0"
---

# Errors & Retries — Sarvam AI

> Product-specific error cases (bad speaker, unsupported param, page limits) live in each product skill's **Gotchas**. This skill = **how errors look and how to handle them**, across every API.

## Error body

Every REST error returns the same JSON shape (verified live on chat V1/V2, translate, text-to-speech, speech-to-text):

```json
{
  "error": {
    "message": "Invalid or missing authentication credentials",
    "code": "invalid_api_key_error",
    "request_id": "20261010_62a4b55c-180c-469c-b1fd-460764cef51c"
  }
}
```

`request_id` is also sent as the `x-request-id` response header. Log it — it is what support asks for.

| HTTP | `error.code` | Retry? | What to do |
|------|--------------|--------|------------|
| 400 | `invalid_request_error` | No | Fix the request. `error.message` names the field (`body.model : Field required`). |
| 403 | `invalid_api_key_error` | No | Missing, wrong, or unknown key. Auth is **403, not 401**. |
| 404 | `not_found_error` | No | Unknown model on V2 chat, unknown job/resource. |
| 422 | `unprocessable_entity_error` | No | Schema valid, business rule failed. |
| 429 | `rate_limit_exceeded_error` / `insufficient_quota_error` | Rate limit: yes. Quota: no | Check `error.code`: quota means credits are exhausted, so retrying won't help. |
| 500 / 502 / 503 / 504 | `internal_server_error` and others | Yes | Transient. Back off and retry. |

## Python

```python
from sarvamai import SarvamAI
from sarvamai.core.api_error import ApiError   # NOT `from sarvamai import ApiError`

client = SarvamAI(api_subscription_key="YOUR_SARVAM_API_KEY")

try:
    response = client.chat.completions(
        model="sarvam-105b",
        messages=[{"role": "user", "content": "Hello"}],
    )
except ApiError as e:
    err = (e.body or {}).get("error", {}) if isinstance(e.body, dict) else {}
    print(e.status_code, err.get("code"), err.get("message"), err.get("request_id"))
    raise
```

Typed subclasses exist in `sarvamai.errors` (`BadRequestError`, `ForbiddenError`, `NotFoundError`, `TooManyRequestsError`, `ServiceUnavailableError`, …) — all inherit from `ApiError`. Catch `ApiError` and branch on `status_code`; see the gotcha below for why.

## JavaScript / TypeScript

```typescript
import { SarvamAIClient, SarvamAIError } from "sarvamai";

const client = new SarvamAIClient({ apiSubscriptionKey: process.env.SARVAM_API_KEY });

try {
  const response = await client.chat.completions({
    model: "sarvam-105b",
    messages: [{ role: "user", content: "Hello" }],
  });
} catch (err) {
  if (err instanceof SarvamAIError) {
    if (err.statusCode === undefined) throw err;                // timeout / network: no HTTP response
    const e = (err.body as any)?.error ?? {};
    console.error(err.statusCode, e.code, e.message, e.request_id);
  }
  throw err;
}
```

Typed subclasses (`SarvamAI.ForbiddenError`, `SarvamAI.BadRequestError`, …) all extend `SarvamAIError`.

## Retries — the SDK already does them

Both SDKs **retry automatically, 2 times by default**, with exponential backoff + jitter (1s start, 60s cap), honoring `Retry-After`. Retried statuses: **408, 429, 5xx** (Python also retries **409**). By the time you catch a 429/503, it has already failed 3 times.

Tune it per request instead of writing your own loop:

```python
client.chat.completions(..., request_options={"max_retries": 5})   # or 0 to disable
```

```typescript
await client.chat.completions({...}, { maxRetries: 5 });          // or 0 to disable
```

Write a custom loop only around non-SDK calls (raw `requests` / `fetch`, the OpenAI SDK pointed at Sarvam), and only for 429 (`rate_limit_exceeded_error`) and 5xx.

## Gotchas

| Gotcha | Detail |
|--------|--------|
| **Auth is 403, not 401** | Verified live: bad key and missing key both return `403 invalid_api_key_error` on V1 and V2. Code that checks `status == 401` for "re-auth" never fires. |
| **Don't stack retry loops** | Verified in `sarvamai` 0.1.36a1 (Python) and 1.1.11 (JS): default `max_retries` is 2. Wrapping SDK calls in your own 5-try backoff loop means up to 15 requests per call. Raise `max_retries` instead. |
| **Don't retry 400/403/404/422** | They fail the same way every time. Read `error.message` — it names the bad field or value (e.g. an unknown TTS speaker returns the full list of valid speakers). |
| **Not every status has a typed class** | Verified live: an unknown model on `chat.completions_v2` / `completionsV2` returns `404` as base `ApiError` / `SarvamAIError`, not `NotFoundError`. `except NotFoundError` misses it. Catch the base class and check `status_code` / `statusCode`. |
| **V1 vs V2 chat report a bad model differently** | Verified live: unknown model on `/v1/chat/completions` → `400 invalid_request_error` listing valid models; on `/v2/chat/completions` → `404 not_found_error`. |
| **`e.body` is a dict, not a string** | Python `ApiError.body` and JS `err.body` are the parsed JSON. Use `body["error"]["message"]`, don't regex `str(e)`. Python's `str(e)` also dumps all response headers — don't show it to end users. |
| **Timeouts have no status** | Verified live: in JS (`sarvamai@1.1.11`, ESM and CJS) a timeout throws plain `SarvamAIError` with `statusCode === undefined` and message `"timeout"` — **not** the exported `SarvamAITimeoutError`, so `instanceof SarvamAITimeoutError` misses it. In Python it's an `httpx.TimeoutException` (e.g. `ConnectTimeout`), not `ApiError`. Handle both separately from HTTP errors. Default timeout is 60s; set `timeoutInSeconds` (JS) / `timeout=` (Python). |
| **Over-length input is 400, not 422** | Verified live: `translate` with more than 2,000 characters returns `400 invalid_request_error` — `"body.input : String should have at most 2000 characters"`. |
| **WebSocket errors are messages, not exceptions** | Streaming STT/TTS sockets send an `error` event (`message.code`, `message.message`) and may close. Check for it in the receive loop — see speech-to-text / text-to-speech. |

## Full Docs

- [Errors & Troubleshooting](https://docs.sarvam.ai/api/getting-started/errors-troubleshooting)
- [Authentication](https://docs.sarvam.ai/api-reference/authentication)
- [Credits & Rate Limits](https://docs.sarvam.ai/api/getting-started/ratelimits)
- **https://docs.sarvam.ai/llms.txt** — comprehensive docs index
