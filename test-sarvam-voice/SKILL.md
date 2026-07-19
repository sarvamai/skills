---
name: test-sarvam-voice
description: Benchmark Sarvam AI voice-agent pipelines end to end across Saaras v3, Sarvam-30B, and Bulbul v3. Use for prerecorded voice regression tests, multilingual ASR quality checks, VAD tuning, latency and cost analysis, reliability testing, baseline comparisons, or CI quality gates. Produces reproducible JSON, standalone HTML, and semantic-evaluation exports.
license: Apache-2.0
metadata:
  author: sarvam-ai
  version: "1.0"
---

# Test Sarvam Voice

Measure the pipeline instead of testing STT, LLM, and TTS in isolation. Use the bundled CLI for deterministic validation, execution, reporting, and regression gates. Use `voice-agents` when building a LiveKit or Pipecat agent; use this skill when proving that an existing voice pipeline remains fast, accurate, reliable, and affordable.

> [!IMPORTANT]
> Keep `SARVAM_API_KEY` in the environment. Never put credentials, raw headers, private audio, or unredacted transcripts in a suite or report.

## Run the workflow

Run commands from the `sarvamai/skills` repository root.

1. Copy `references/example-suite.yaml` and replace each audio path and reference transcript.
2. Keep v1 input audio as mono 16-bit PCM WAV at 8 or 16 kHz. Convert other audio first:

   ```bash
   ffmpeg -i input.mp3 -ac 1 -ar 16000 -c:a pcm_s16le output.wav
   ```

3. Validate the suite and review the conservative cost projection before any network call:

   ```bash
   uv run test-sarvam-voice/scripts/voice_lab.py plan suite.yaml
   ```

4. Run the suite sequentially with no retry by default:

   ```bash
   export SARVAM_API_KEY="your-api-key"
   uv run test-sarvam-voice/scripts/voice_lab.py run suite.yaml --out results/
   ```

5. Compare a candidate with a committed or downloaded baseline:

   ```bash
   uv run test-sarvam-voice/scripts/voice_lab.py compare \
     baseline/report.json candidate/report.json --out comparison/
   ```

Treat exit `0` as success, `1` as a quality/regression gate failure, `2` as invalid input or a rejected budget, `3` as an incomplete live run, and `130` as interruption.

## Design the suite

- Cover the languages, acoustic conditions, intents, numbers, names, and code-mixing patterns that matter in production.
- Use a stable human-verified reference transcript for each case.
- Add `entities` only for critical values that must survive ASR, such as phone numbers, amounts, dates, people, and locations. Interpret `configured_entity_recall` as deterministic substring preservation, not Sarvam's LLM-based Entity Score.
- Tag cases by language, channel, domain, and risk so the report exposes cohort regressions.
- Set absolute gates for release requirements and regression thresholds for candidate-versus-baseline changes.
- Keep `reasoning_effort: null` for latency-sensitive voice responses. Increase `max_tokens` if Sarvam-30B returns no speakable content.
- Keep the budget ceiling conservative. The CLI refuses an over-budget run before creating a connection.

Read [references/report-schema.md](references/report-schema.md) when adding CI gates, interpreting timings, or consuming JSON/JSONL artifacts.

## Protect evaluation integrity

- Default to one worker, zero retries, redacted text, and discarded TTS audio.
- Add `--concurrency` only after checking account rate limits. Add bounded `--retries` only to measure recovery behavior; authentication, quota, and validation failures are never retried.
- Add `--include-transcripts` only in a private output directory when semantic evaluation is required.
- Add `--retain-audio` only for deliberate listening tests. Do not commit generated speech.
- Use `--mock-events` for offline protocol regression tests. Never present mock latency as live service performance.
- Compare distributions and P95 latency, not only averages. Inspect per-case failures before accepting a passing aggregate.

## Interpret the outputs

The run directory contains:

- `report.json`: schema-versioned measurements, configuration, errors, gates, and suite/language/tag aggregates.
- `report.html`: escaped, standalone comparison surface with no external assets.
- `llm-wer.jsonl`: rows compatible with Sarvam's `llm_wer` dataset columns when transcript inclusion is enabled.
- `llm-intent-entity.jsonl`: rows compatible with Sarvam's `llm_intent_entity` dataset columns when transcript inclusion is enabled.
- `audio/`: synthesized responses only when explicitly retained.

Use raw and normalized WER/CER together. Normalization removes punctuation, symbols, casing, and Unicode compatibility differences; it does not make semantic judgments. Treat all INR values as estimates tied to the dated pricing snapshot in the suite.

## Refresh changing interfaces

Before changing model IDs, supported languages, VAD parameters, limits, or pricing, fetch the current index and primary pages:

- **https://docs.sarvam.ai/llms.txt** — current documentation index
- [Pricing](https://docs.sarvam.ai/api/getting-started/pricing)
- [Saaras v3](https://docs.sarvam.ai/api/getting-started/models/saaras)
- [Sarvam-30B](https://docs.sarvam.ai/api/getting-started/models/sarvam-30b)
- [Bulbul v3](https://docs.sarvam.ai/api/getting-started/models/bulbul)
- [Credits and rate limits](https://docs.sarvam.ai/api/getting-started/ratelimits)
