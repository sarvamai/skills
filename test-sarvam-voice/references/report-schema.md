# Report contract and measurement semantics

## Contents

- [Artifacts](#artifacts)
- [Timing boundaries](#timing-boundaries)
- [Quality and reliability](#quality-and-reliability)
- [Cost model](#cost-model)
- [Regression gates](#regression-gates)
- [Semantic exports](#semantic-exports)
- [CI pattern](#ci-pattern)

## Artifacts

Treat `schema_version` as the compatibility boundary. Run reports use `sarvam.voice-eval/v1`; comparisons use `sarvam.voice-compare/v1`. Consumers must reject unknown major versions.

Run reports contain the resolved suite configuration, pricing snapshot, absolute gate results, deterministic per-case records, and aggregates for the full suite, each language, and each tag. Report ordering is stable by case ID and repetition. HTML is a standalone escaped view of the same JSON data and loads no scripts, fonts, or stylesheets.

Transcript, reference, context, configured entity, system-prompt, and LLM response text are absent by default. Their records contain only a SHA-256 digest, character count, and `redacted: true`. Semantic JSONL files are intentionally empty unless `--include-transcripts` is set.

## Timing boundaries

All live timings use the local monotonic clock:

| Metric | Start | End |
|---|---|---|
| `stt_connection` | before entering the Saaras WebSocket context | connected socket available |
| `vad_start`, `vad_end` | STT stage start | local receipt of the corresponding VAD event |
| `stt_finalization_after_speech_end` | received `END_SPEECH`, or last audio chunk when absent | final non-empty transcript receipt |
| `llm_time_to_first_token` | Sarvam-30B request start | first non-empty content delta |
| `tts_time_to_first_byte` | Bulbul HTTP-stream request start | first non-empty binary chunk |
| `eos_to_first_audio` | received `END_SPEECH`, or last audio chunk when absent | first synthesized audio byte |
| `total_turn` | before STT connection | complete TTS stream |

Mock fixtures use the same field names but are deterministic protocol replays. Do not mix mock and live reports in a performance baseline.

## Quality and reliability

`raw_wer` and `raw_cer` preserve the input strings. Normalized metrics apply Unicode NFKC, case folding, punctuation/symbol removal, and whitespace collapse before deterministic edit distance. Empty references score `0` only against an empty hypothesis and `1` otherwise.

`configured_entity_recall` checks only suite-provided strings and aliases after deterministic text, compact-whitespace, and digit normalization. It is intentionally not Sarvam's LLM-based Entity Score and makes no semantic-equivalence claim.

Success rate includes every requested repetition. A failed attempt records a sanitized exception type, message, and status code. The runner retries only transport/time-out and server-side failures when explicitly configured; it never retries authentication, quota/rate-limit, or invalid-request responses.

P50 and P95 use linearly interpolated percentiles over successful samples. Each metric summary carries its own `sample_count`; always inspect it and the aggregate `failure_count` beside percentiles.

## Cost model

STT duration rounds up to a minimum of one billed second per case attempt. LLM input/output uses returned streaming usage when available. If usage is absent, a four-characters-per-token heuristic is used and `estimated: true` remains visible. TTS uses the response character count.

`plan` projects a conservative maximum from audio duration, configured `max_tokens`, every allowed retry attempt, and the dated suite pricing snapshot. `run` rejects a projection above `execution.budget_inr` before importing the live client or opening a connection. The measured cost aggregate covers completed runs; use the conservative projection or provider billing when failed attempts may have consumed partial stages. Refresh pricing from the official source before using reports for financial planning.

## Regression gates

Run gates apply absolute requirements to the candidate suite. Comparison gates apply candidate-minus-baseline deltas:

- WER increase must remain at or below its ratio limit.
- EOS-to-audio P95 increase must remain at or below its millisecond limit.
- estimated cost percentage increase must remain at or below its percentage limit.
- success-rate drop must remain at or below its ratio limit.

A skipped gate has a null threshold. Gate failure returns exit code `1`; incomplete live execution returns `3`, even if aggregate gates also fail.

## Semantic exports

With transcript inclusion enabled, `llm-wer.jsonl` exposes `transcription`, `prediction`, `audio_filepath`, and `language`, matching the configurable dataset columns consumed by Sarvam's `llm_wer` project.

`llm-intent-entity.jsonl` exposes `ground_truth`, `asr_output`, `audio_file`, `language`, and `context`, matching the columns consumed by Sarvam's `llm_intent_entity` project. Run those projects separately when semantic judgments are needed; this skill does not bundle an LLM judge or its credentials.

## CI pattern

Keep live credentials out of pull-request CI. Replay a checked-in protocol fixture against generated temporary WAV input, compare the report to a reviewed baseline, and fail on exit `1`, `2`, or `3`. Run live suites only in a protected scheduled workflow with a strict INR ceiling and private artifact retention.
