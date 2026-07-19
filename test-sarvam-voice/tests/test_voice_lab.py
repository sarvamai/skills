from __future__ import annotations

import asyncio
import contextlib
import copy
import importlib.util
import io
import json
import os
import tempfile
import unittest
import wave
from pathlib import Path
from typing import Any


SCRIPT = Path(__file__).parents[1] / "scripts" / "voice_lab.py"
SPEC = importlib.util.spec_from_file_location("voice_lab", SCRIPT)
assert SPEC and SPEC.loader
voice_lab = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(voice_lab)


def write_wav(
    path: Path,
    *,
    seconds: float = 0.5,
    rate: int = 16000,
    channels: int = 1,
    sample_width: int = 2,
) -> None:
    frame_count = round(seconds * rate)
    frame = b"\x00" * sample_width * channels
    with wave.open(str(path), "wb") as output:
        output.setnchannels(channels)
        output.setsampwidth(sample_width)
        output.setframerate(rate)
        output.writeframes(frame * frame_count)


def raw_suite(audio: str = "case.wav") -> dict[str, Any]:
    return {
        "version": 1,
        "name": "unit-suite",
        "execution": {"budget_inr": 20.0},
        "cases": [
            {
                "id": "case-one",
                "audio": audio,
                "reference": "मेरा नंबर 1234 है",
                "language": "hi-IN",
                "tts_language": "hi-IN",
                "tags": ["hindi", "numbers"],
                "entities": [{"value": "1234", "aliases": ["१२३४"]}],
                "context": "Account support",
            }
        ],
    }


def mock_fixture(transcript: str = "मेरा नंबर 1234 है") -> dict[str, Any]:
    return {
        "schema_version": voice_lab.MOCK_SCHEMA,
        "cases": {
            "case-one": {
                "connection_ms": 40,
                "stt": [
                    {"at_ms": 80, "type": "events", "signal_type": "START_SPEECH"},
                    {"at_ms": 450, "type": "events", "signal_type": "END_SPEECH"},
                    {"at_ms": 520, "type": "data", "transcript": transcript},
                ],
                "llm": {
                    "chunks": [
                        {"at_ms": 50, "reasoning_content": "private reasoning"},
                        {"at_ms": 100, "content": "ठीक है।"},
                    ],
                    "usage": {
                        "prompt_tokens": 20,
                        "completion_tokens": 5,
                        "total_tokens": 25,
                    },
                },
                "tts": {
                    "chunks": [
                        {"at_ms": 90, "bytes": 1024},
                        {"at_ms": 140, "bytes": 512},
                    ]
                },
            }
        },
    }


class VoiceLabTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.audio = self.root / "case.wav"
        write_wav(self.audio)
        self.manifest = self.root / "suite.yaml"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def suite(self, raw: dict[str, Any] | None = None) -> dict[str, Any]:
        return voice_lab.validate_suite(raw or raw_suite(), self.manifest)

    def run_mock(
        self,
        suite: dict[str, Any] | None = None,
        fixture: dict[str, Any] | None = None,
        *,
        include_transcripts: bool = False,
    ) -> list[dict[str, Any]]:
        return asyncio.run(
            voice_lab.execute_runs(
                suite or self.suite(),
                self.root / "output",
                include_transcripts=include_transcripts,
                retain_audio=False,
                mock=fixture or mock_fixture(),
            )
        )

    def test_defaults_and_paths_are_resolved(self) -> None:
        suite = self.suite()
        self.assertEqual(suite["pipeline"]["stt"]["chunk_ms"], 250)
        self.assertEqual(suite["pipeline"]["llm"]["model"], "sarvam-30b")
        self.assertEqual(
            voice_lab.case_audio_path(suite, suite["cases"][0]), self.audio.resolve()
        )

    def test_duplicate_case_ids_are_rejected(self) -> None:
        raw = raw_suite()
        raw["cases"].append(copy.deepcopy(raw["cases"][0]))
        with self.assertRaisesRegex(voice_lab.ValidationError, "Duplicate case id"):
            self.suite(raw)

    def test_invalid_models_and_languages_are_rejected(self) -> None:
        raw = raw_suite()
        raw["pipeline"] = {"llm": {"model": "sarvam-m"}}
        with self.assertRaisesRegex(voice_lab.ValidationError, "sarvam-30b"):
            self.suite(raw)
        raw = raw_suite()
        raw["cases"][0]["language"] = "fr-FR"
        with self.assertRaisesRegex(
            voice_lab.ValidationError, "Unsupported case language"
        ):
            self.suite(raw)

    def test_missing_and_incompatible_audio_are_actionable(self) -> None:
        suite = self.suite(raw_suite("missing.wav"))
        with self.assertRaisesRegex(voice_lab.ValidationError, "does not exist"):
            voice_lab.build_plan(suite)
        stereo = self.root / "stereo.wav"
        write_wav(stereo, channels=2)
        suite = self.suite(raw_suite("stereo.wav"))
        with self.assertRaisesRegex(voice_lab.ValidationError, "ffmpeg"):
            voice_lab.build_plan(suite)

    def test_audio_sample_rate_must_match_pipeline(self) -> None:
        audio = self.root / "eight.wav"
        write_wav(audio, rate=8000)
        suite = self.suite(raw_suite("eight.wav"))
        with self.assertRaisesRegex(
            voice_lab.ValidationError, "pipeline.stt.sample_rate"
        ):
            voice_lab.build_plan(suite)

    def test_wav_chunks_are_independent_and_complete(self) -> None:
        chunks = list(voice_lab.wav_chunks(self.audio, 250))
        self.assertEqual(len(chunks), 2)
        self.assertAlmostEqual(sum(duration for _, duration in chunks), 0.5)
        for payload, duration in chunks:
            with wave.open(io.BytesIO(payload), "rb") as source:
                self.assertEqual(source.getnchannels(), 1)
                self.assertEqual(source.getsampwidth(), 2)
                self.assertEqual(source.getframerate(), 16000)
                self.assertAlmostEqual(
                    source.getnframes() / source.getframerate(), duration
                )

    def test_plan_reveals_budget_rejection(self) -> None:
        raw = raw_suite()
        raw["execution"] = {"budget_inr": 0.01}
        raw["pipeline"] = {"llm": {"max_tokens": 500}}
        plan = voice_lab.build_plan(self.suite(raw))
        self.assertFalse(plan["within_budget"])
        self.assertGreater(plan["projected_cost"]["total_inr"], plan["budget_inr"])

    def test_text_quality_handles_unicode_and_indic_punctuation(self) -> None:
        quality = voice_lab.text_quality("नमस्ते, दुनिया!", "नमस्ते दुनिया")
        self.assertGreater(quality["raw_cer"], 0)
        self.assertEqual(quality["normalized_wer"], 0)
        self.assertEqual(voice_lab.text_quality("ＡＢＣ", "abc")["normalized_cer"], 0)

    def test_empty_reference_has_stable_error_rates(self) -> None:
        self.assertEqual(voice_lab.text_quality("", "")["normalized_wer"], 0)
        self.assertEqual(voice_lab.text_quality("", "unexpected")["normalized_wer"], 1)

    def test_numeric_entities_normalize_unicode_digits_and_spacing(self) -> None:
        entities = [{"value": "9840950950"}]
        self.assertEqual(
            voice_lab.configured_entity_recall(entities, "नंबर ९८४०-९५०-९५० है"), 1
        )
        self.assertEqual(
            voice_lab.configured_entity_recall(entities, "नंबर उपलब्ध नहीं है"), 0
        )

    def test_mock_protocol_events_measure_every_stage(self) -> None:
        result = self.run_mock(include_transcripts=True)[0]
        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["transcript"]["text"], "मेरा नंबर 1234 है")
        self.assertEqual(result["quality"]["configured_entity_recall"], 1)
        self.assertEqual(result["latency_ms"]["stt_finalization_after_speech_end"], 70)
        self.assertEqual(result["latency_ms"]["eos_to_first_audio"], 260)
        self.assertEqual(result["billable_units"]["tts_bytes"], 1536)
        self.assertFalse(result["cost"]["estimated"])

    def test_reasoning_only_mock_is_a_visible_failure(self) -> None:
        fixture = mock_fixture()
        fixture["cases"]["case-one"]["llm"]["chunks"] = [
            {"at_ms": 100, "reasoning_content": "not speakable"}
        ]
        result = self.run_mock(fixture=fixture)[0]
        self.assertEqual(result["status"], "failed")
        self.assertIn("no speakable content", result["error"]["message"])

    def test_partial_suite_reports_failures_without_losing_successes(self) -> None:
        raw = raw_suite()
        second = copy.deepcopy(raw["cases"][0])
        second["id"] = "case-two"
        raw["cases"].append(second)
        suite = self.suite(raw)
        fixture = mock_fixture()
        fixture["cases"]["case-two"] = {"error": "upstream unavailable"}
        results = self.run_mock(suite, fixture)
        aggregate = voice_lab.aggregate_results(results)
        self.assertEqual(aggregate["sample_count"], 2)
        self.assertEqual(aggregate["success_count"], 1)
        self.assertEqual(aggregate["success_rate"], 0.5)

    def test_retries_are_bounded_and_skip_auth_quota_failures(self) -> None:
        class ApiError(Exception):
            def __init__(self, code: int):
                self.status_code = code
                super().__init__(f"HTTP status {code}")

        self.assertTrue(voice_lab.retryable(ApiError(503)))
        self.assertTrue(voice_lab.retryable(TimeoutError()))
        for code in (400, 401, 403, 422, 429):
            self.assertFalse(voice_lab.retryable(ApiError(code)))

    def test_secret_redaction_covers_header_and_environment_key(self) -> None:
        old = os.environ.get("SARVAM_API_KEY")
        os.environ["SARVAM_API_KEY"] = "secret-value"
        try:
            message = voice_lab.sanitize_error(
                "api-subscription-key: secret-value Authorization=BearerValue sk_example"
            )
        finally:
            if old is None:
                os.environ.pop("SARVAM_API_KEY", None)
            else:
                os.environ["SARVAM_API_KEY"] = old
        self.assertNotIn("secret-value", message)
        self.assertNotIn("BearerValue", message)
        self.assertNotIn("sk_example", message)

    def test_percentiles_and_grouping_are_deterministic(self) -> None:
        results = self.run_mock()
        for index, value in enumerate((100, 200, 300, 400), 1):
            item = copy.deepcopy(results[0])
            item["repetition"] = index
            item["latency_ms"]["eos_to_first_audio"] = value
            results.append(item)
        summary = voice_lab.aggregate_results(results[1:])
        self.assertEqual(summary["latency_ms"]["eos_to_first_audio"]["p50"], 250)
        self.assertEqual(summary["latency_ms"]["eos_to_first_audio"]["p95"], 385)
        grouped = voice_lab.grouped_aggregates(results[1:])
        self.assertIn("hi-IN", grouped["by_language"])
        self.assertIn("numbers", grouped["by_tag"])

    def test_gate_directions_are_explicit(self) -> None:
        report = voice_lab.build_report(self.suite(), self.run_mock(), "mock")
        statuses = {gate["name"]: gate["status"] for gate in report["gates"]}
        self.assertEqual(statuses["normalized WER mean"], "passed")
        report["aggregates"]["suite"]["success_rate"] = 0.5
        gates = voice_lab.evaluate_gates(
            report["aggregates"], report["config"]["gates"]
        )
        status = {gate["name"]: gate["status"] for gate in gates}
        self.assertEqual(status["success rate"], "failed")

    def test_run_report_schema_ordering_and_html_escaping(self) -> None:
        suite = self.suite()
        suite["cases"][0]["context"] = "<script>alert(1)</script>"
        report = voice_lab.build_report(suite, self.run_mock(suite), "mock")
        self.assertEqual(report["schema_version"], voice_lab.REPORT_SCHEMA)
        self.assertEqual(
            set(report),
            {
                "schema_version",
                "created_at",
                "suite",
                "mode",
                "config",
                "pricing",
                "aggregates",
                "gates",
                "gate_status",
                "results",
            },
        )
        rendered = voice_lab.run_report_html(report)
        self.assertNotIn("<script>alert(1)</script>", rendered)
        self.assertNotIn("alert(1)", rendered)
        self.assertIn("&quot;redacted&quot;: true", rendered)

    def test_transcripts_default_to_redacted_and_exports_require_opt_in(self) -> None:
        suite = self.suite()
        redacted = voice_lab.build_report(suite, self.run_mock(suite), "mock")
        self.assertTrue(redacted["results"][0]["transcript"]["redacted"])
        self.assertNotIn("text", redacted["results"][0]["transcript"])
        self.assertTrue(redacted["config"]["cases"][0]["reference"]["redacted"])
        self.assertTrue(
            redacted["config"]["pipeline"]["llm"]["system_prompt"]["redacted"]
        )
        self.assertNotIn("मेरा नंबर", json.dumps(redacted["config"], ensure_ascii=False))
        self.assertEqual(voice_lab.semantic_rows(suite, redacted), ([], []))
        private = voice_lab.build_report(
            suite, self.run_mock(suite, include_transcripts=True), "mock"
        )
        wer_rows, intent_rows = voice_lab.semantic_rows(suite, private)
        self.assertEqual(wer_rows[0]["prediction"], "मेरा नंबर 1234 है")
        self.assertEqual(intent_rows[0]["asr_output"], "मेरा नंबर 1234 है")

    def test_comparison_detects_configuration_and_metric_regression(self) -> None:
        suite = self.suite()
        baseline = voice_lab.build_report(suite, self.run_mock(suite), "mock")
        candidate = copy.deepcopy(baseline)
        candidate["created_at"] = "later"
        candidate["config"]["pipeline"]["stt"]["vad"]["high_sensitivity"] = True
        candidate["aggregates"]["suite"]["quality"]["normalized_wer"]["mean"] += 0.1
        comparison = voice_lab.build_comparison(baseline, candidate)
        self.assertEqual(comparison["schema_version"], voice_lab.COMPARISON_SCHEMA)
        self.assertEqual(comparison["gate_status"], "failed")
        paths = {change["path"] for change in comparison["config_diff"]}
        self.assertIn("pipeline.stt.vad.high_sensitivity", paths)
        rendered = voice_lab.comparison_report_html(comparison)
        self.assertIn("Configuration differences", rendered)

    def test_cli_plan_mock_run_and_compare_exit_codes(self) -> None:
        try:
            import yaml
        except ImportError as exc:  # pragma: no cover
            self.fail(f"PyYAML missing from test environment: {exc}")
        self.manifest.write_text(
            yaml.safe_dump(raw_suite(), allow_unicode=True), encoding="utf-8"
        )
        fixture_path = self.root / "mock.json"
        fixture_path.write_text(
            json.dumps(mock_fixture(), ensure_ascii=False), encoding="utf-8"
        )
        baseline_dir = self.root / "baseline"
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(
                voice_lab.main(["plan", str(self.manifest)]), voice_lab.EXIT_OK
            )
            self.assertEqual(
                voice_lab.main(
                    [
                        "run",
                        str(self.manifest),
                        "--out",
                        str(baseline_dir),
                        "--mock-events",
                        str(fixture_path),
                    ]
                ),
                voice_lab.EXIT_OK,
            )
            self.assertEqual(
                voice_lab.main(
                    [
                        "compare",
                        str(baseline_dir / "report.json"),
                        str(baseline_dir / "report.json"),
                        "--out",
                        str(self.root / "comparison"),
                    ]
                ),
                voice_lab.EXIT_OK,
            )
        self.assertTrue((baseline_dir / "report.html").exists())
        self.assertEqual(
            (baseline_dir / "llm-wer.jsonl").read_text(encoding="utf-8"), ""
        )

    def test_budget_and_missing_key_use_invalid_exit_without_network(self) -> None:
        try:
            import yaml
        except ImportError as exc:  # pragma: no cover
            self.fail(f"PyYAML missing from test environment: {exc}")
        raw = raw_suite()
        raw["execution"] = {"budget_inr": 0.0}
        self.manifest.write_text(
            yaml.safe_dump(raw, allow_unicode=True), encoding="utf-8"
        )
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            code = voice_lab.main(
                ["run", str(self.manifest), "--out", str(self.root / "blocked")]
            )
        self.assertEqual(code, voice_lab.EXIT_INVALID)
        self.assertIn("no network requests were made", stderr.getvalue())
        self.assertFalse((self.root / "blocked").exists())

    def test_skill_metadata_and_eval_prompts_are_well_formed(self) -> None:
        try:
            import yaml
        except ImportError as exc:  # pragma: no cover
            self.fail(f"PyYAML missing from test environment: {exc}")
        skill = Path(__file__).parents[1] / "SKILL.md"
        text = skill.read_text(encoding="utf-8")
        _, frontmatter, _ = text.split("---", 2)
        metadata = yaml.safe_load(frontmatter)
        self.assertEqual(metadata["name"], "test-sarvam-voice")
        self.assertIn("VAD tuning", metadata["description"])
        evals = json.loads(
            (Path(__file__).parents[1] / "evals" / "evals.json").read_text()
        )
        self.assertEqual(evals["skill_name"], metadata["name"])
        self.assertEqual(len(evals["evals"]), 3)

    def test_documented_exit_codes_are_stable(self) -> None:
        self.assertEqual(
            (
                voice_lab.EXIT_OK,
                voice_lab.EXIT_REGRESSION,
                voice_lab.EXIT_INVALID,
                voice_lab.EXIT_LIVE_FAILURE,
                voice_lab.EXIT_INTERRUPTED,
            ),
            (0, 1, 2, 3, 130),
        )


if __name__ == "__main__":
    unittest.main()
