---
name: prism
description: >-
  Write correct Sarvam Prism code (`sarvam-prism`, the System-1 decision model
  built on Sarvam 105B) — the Decisions API (`client.decisions.create`,
  `POST /v2/systemone`) that answers typed yes/no (`noul`), pick-one
  (`choice`) and ordered-scale (`score`) questions with a calibrated
  probability for every option. Use this skill when building routing, triage,
  moderation, intent or label classification, scoring, prompt-injection
  checks, or judging of agent runs in Python or JS/TS — anywhere you would
  otherwise prompt a chat model to "answer yes or no" or "reply with one of
  these labels" and parse the reply. Not for generating text (use chat), not
  for classifying or splitting document files (use doc-ai), and not for
  images (text only).
license: Apache-2.0
metadata:
  author: sarvam-ai
  version: "1.1"
---

# Sarvam Prism — Decisions API

> Need generated text, summaries or tool calling? → [chat](../chat/SKILL.md). Need to classify or split a PDF/image file? → [doc-ai](../doc-ai/SKILL.md) (`doc_ai.classify()` / `.split()`).

> SDK floor: Python `sarvamai>=0.1.43`, JS `sarvamai@>=1.1.15`. Older versions have no `client.decisions` (Python `AttributeError`, JS `undefined`). Check `pip show sarvamai` / `npm ls sarvamai` first.

> [!IMPORTANT]
> Endpoint: `POST https://api.sarvam.ai/v2/systemone` — NOT `/v1/chat/completions`. Auth: `api-subscription-key` header; `Authorization: Bearer <key>` also works here.

## What it does

You send a **state** (the input to decide on) and a map of **typed questions**. One call returns a probability for every option of every question. It generates no text, so there is nothing to parse and output tokens cost ₹0.

| `type` | Asks | `criteria` | Answer fields |
|--------|------|------------|---------------|
| `noul` | Yes / no | Optional `{"true": "...", "false": "..."}` | `noul` (probability of yes) |
| `choice` | Pick one | **Required** object of option ID → description, 2–255 options | `choice`, `confidence`, `probabilities` |
| `score` | Rate on an ordered scale | **Required** list of levels, lowest first, 2–10 levels | `score`, `confidence`, `legend`, `probabilities` |

### Prism or chat?

| Situation | Use |
|-----------|-----|
| A fixed set of answers (yes/no, a label, a level) and you want a probability to gate on | **Prism** |
| High volume of small judgements — ₹4 / 1M input tokens, ₹0 output, ~0.14 s per short call (measured from one location) | **Prism** |
| Free-form text, summaries, explanations, tool calling, images | [chat](../chat/SKILL.md) |
| You need the *reason* for the answer | [chat](../chat/SKILL.md) — Prism returns probabilities only, no explanation |

Worked patterns (routing, injection guard, judging agent runs, moderation, voice intents, concurrency) and a design checklist: [references/recipes.md](references/recipes.md).

## Quick Start (Python)

```python
import os
from sarvamai import SarvamAI

client = SarvamAI(api_subscription_key=os.environ["SARVAM_API_KEY"])

response = client.decisions.create(
    model="sarvam-prism",
    state="My Stripe integration stopped working and all checkout payments are failing.",
    questions={
        "urgent": {"type": "noul", "instructions": "Is this urgent and revenue-impacting?"},
        "department": {
            "type": "choice",
            "instructions": "Which team should handle this?",
            "criteria": {
                "billing": "Payments or invoices",
                "technical": "Bugs or outages",
                "sales": "New business enquiries",
            },
        },
        "severity": {
            "type": "score",
            "instructions": "Rate the severity.",
            "criteria": ["trivial", "minor", "moderate", "major", "critical"],
        },
    },
)

a = response.answers                       # dict keyed by YOUR question IDs
print(a["urgent"].noul)                    # 0.978  -> probability of "yes"
print(a["department"].choice, a["department"].probabilities)
print(a["severity"].score, a["severity"].legend)   # 3.83, {"0": "trivial", ...}
print(response.usage.input_tokens, response.usage.output_tokens)   # output is always 0
```

### Act automatically only on confident answers

```python
# reuses `client` from the Quick Start above
THRESHOLD = 0.9
d = client.decisions.create(
    model="sarvam-prism",
    state="I was charged twice for my last order.",
    questions={"department": {"type": "choice", "instructions": "Which team?",
                              "criteria": {"billing": "Payments or invoices", "technical": "Bugs or outages"}}},
).answers["department"]

if d.probabilities[d.choice] >= THRESHOLD:     # top PROBABILITY, not d.confidence
    route(d.choice)
else:
    send_to_human()
```

## Quick Start (JavaScript/TypeScript)

```typescript
import { SarvamAIClient } from "sarvamai";

const client = new SarvamAIClient({ apiSubscriptionKey: process.env.SARVAM_API_KEY });

const response = await client.decisions.create({
  model: "sarvam-prism",
  state: "My Stripe integration stopped working and all checkout payments are failing.",
  questions: {
    urgent: { type: "noul", instructions: "Is this urgent and revenue-impacting?" },
    department: {
      type: "choice",
      instructions: "Which team should handle this?",
      criteria: { billing: "Payments or invoices", technical: "Bugs or outages", sales: "New business enquiries" },
    },
    severity: { type: "score", instructions: "Rate the severity.", criteria: ["trivial", "minor", "moderate", "major", "critical"] },
  },
});

for (const [id, answer] of Object.entries(response.answers)) {
  switch (answer.type) {            // every answer carries its `type`
    case "noul":   console.log(id, answer.noul); break;
    case "choice": console.log(id, answer.choice, answer.probabilities[answer.choice]); break;
    case "score":  console.log(id, answer.score, answer.legend[String(Math.round(answer.score))]); break;
  }
}
```

## Gotchas

| Gotcha | Detail |
|--------|--------|
| **Not a chat model** | `client.decisions.create(...)`, never `client.chat.completions(...)`. Sending `sarvam-prism` to chat returns `400 ... should be one of sarvam-105b, sarvam-105b-conversations`; sending a chat model to `/v2/systemone` returns `404 Model '...' not found`. There is no `messages` field (`422`). |
| **`state` + `questions`, both required** | `questions` is a **map** of your question ID → question, at least one (`{}` → `422`). Each answer comes back under the same ID. `model` is required (`400` if missing, `404` if unknown). Model IDs are case-sensitive: `Sarvam-Prism` → `404`. |
| **`state` can be a dict or list** | Objects/arrays are rendered as compact JSON — pass the record as-is, don't `json.dumps` it. An empty string is accepted but gives an uninformative answer (≈0.57 on a yes/no); `null`, a number, or a missing `state` → `422`. |
| **Type names are lowercase** | `noul` (not `yesno`/`boolean`/`binary`), `choice`, `score`. `NOUL` or `yesno` → `422`. |
| **`noul` returns only a float** | `answer.noul` = probability of **yes**. No label, no `confidence`. Threshold at 0.5 for a hard answer. It needs `instructions`, `criteria`, or both (neither → `422`). |
| **`noul` criteria keys are `"true"` / `"false"`** | `{"yes": ..., "no": ...}` → `422 Extra inputs are not permitted`. |
| **`choice` criteria is a dict, `score` criteria is a list** | Swapping them → `422`. `choice`: 2–255 options (256 → `422`). `score`: 2–10 levels (11 → `422`). Write each description as the condition under which that option applies; an empty or `null` description is shown to the model as the bare ID. |
| **Order: irrelevant for `choice`, essential for `score`** | Reordering `choice` options changes nothing (probabilities moved by ≤0.003 across shuffles). A `score` list defines the scale **lowest first** — reversing it flips the meaning (verified: the same state scored 3.83 ascending vs 0.30 reversed). |
| **`score` is a float, keys are strings** | `score` = expected level (`Σ index × probability`, e.g. `3.83`), levels indexed from 0. `probabilities` and `legend` are keyed `"0"`, `"1"`, … — look up with `legend[str(round(score))]` (Python) / `legend[String(Math.round(score))]` (JS). |
| **Always add an `other` option to a `choice`** | Probabilities sum to 1 over *your* options, so off-topic input is forced into one of them — verified: `"Hi"` → `sales` 0.87, `"asdf qwer zxcv"` → `technical` 0.77. With an explicit `other` ("None of the above: …") the same inputs land on `other` at 0.83–0.98. Treat `other` and below-threshold the same way (human/fallback). |
| **Opaque option IDs need descriptions** | Self-explanatory IDs (`billing`/`technical`/`sales`) worked bare, 10/10; opaque IDs (`P1`/`P2`/`P3`) scored **4/10 bare vs 10/10 with descriptions**. Write the description as the condition under which the option applies. |
| **Multi-label → several `noul`, not one `choice`** | `choice` returns one winner; on a two-topic message three `noul` questions gave 0.965 / 0.94 / 0.028 for the three topics. |
| **Your `instructions` decide what counts** | The same indirect prompt-injection input scored 0.107 under a narrow question and 0.976 under a broad one. Test the wording, and keep untrusted text in `state`, never in `instructions`. |
| **Threshold on probability, not `confidence`** | `confidence` is rescaled: for `choice` it is `(p_top − 1/n) / (1 − 1/n)` (verified), so 0.80 over 3 options reports `0.70`. The calibration claims (a 0.9 answer is wrong ≤10% of the time) apply to the top **probability** — `noul`, or `probabilities[choice]`. |
| **Only `type`, `instructions`, `criteria` in a question** | Any other key → `422`, including the typo `instruction` (`questions.u.noul.instruction: Extra inputs are not permitted`). `instructions` may be a string, object or array. |
| **Generation params: some 422, some silently ignored** | `temperature`, `max_tokens`, `stream`, `top_p`, `n`, `tools`, `response_format`, `messages` → `422`. But `seed`, `stop`, `reasoning_effort`, `frequency_penalty` and unknown top-level keys return `200` and do **nothing**. There are no determinism or reasoning knobs — don't rely on them. |
| **Batch questions on one state** | The state is billed **once per request**; each question adds only its own tokens. Same 3 questions: 153 input tokens in one request vs 181 as three requests. Prefer one request per state. |
| **Limits fail the whole request** | 32,768 tokens **per question** (state + that question + options). If any one question is over → `422 question 'u' encodes to 45029 tokens, over the 32768-token limit` and **nothing** is answered; the state is never truncated, so check size first. No cap on the number of questions (30 verified). Each request must finish in 60 s, else `503 model_overloaded` — split large batches. |
| **Errors: bad key is `403`, not `401`** | Missing/invalid key → `403 invalid_api_key_error`. `402` = empty credits, `429` = rate limit. Retry only `429`/`502`/`503` with backoff; fix `4xx`. Branch on status/`code`, not message text. Validation errors carry `param` (the field path). SDK classes: `NotFoundError`, `UnprocessableEntityError`, `ForbiddenError` (all subclass `ApiError`) in both Python and JS. |
| **Text only, no streaming** | An `images` field is refused (image URL → `400`, inline image → `422`). Every response is one JSON body. Works on English, Hindi, and Hinglish input (verified); the docs report Indian-language answers clear a 0.9 threshold less often (≈38% vs ≈69% English), so expect more human review there. |
| **Repeatability** | Identical requests can differ slightly in `choice`/`score` probabilities (observed ±0.003 on `choice`; `noul` was identical across 4 runs). The top answer is stable. Leave a margin around thresholds instead of testing for exact equality. |
| **Pricing** | ₹4 per 1M input tokens, ₹0 output, on every plan. Read `usage.input_tokens` for the exact count. |

## Full Docs

Fetch parameter details, benchmarks, error table, and rate limits from:

- **https://docs.sarvam.ai/llms.txt** — comprehensive docs index
- [Sarvam Prism model page](https://docs.sarvam.ai/api/token-factory/models/sarvam-prism)
- [Decisions API guide](https://docs.sarvam.ai/api/token-factory/decisions-api)
- [API reference — `POST /v2/systemone`](https://docs.sarvam.ai/api-reference/decisions/systemone)
- [Pricing & Rate Limits](https://docs.sarvam.ai/api/getting-started/pricing)
