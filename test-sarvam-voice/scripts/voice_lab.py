#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "sarvamai>=0.1.28,<0.2",
#   "jiwer>=4,<5",
#   "PyYAML>=6,<7",
# ]
# ///
"""Reproducible quality, latency, cost, and reliability tests for Sarvam voice agents."""

from __future__ import annotations

import argparse
import asyncio
import base64
import copy
import hashlib
import html
import io
import json
import math
import os
import re
import statistics
import sys
import time
import unicodedata
import wave
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, AsyncIterator, Iterable, Mapping, Sequence


REPORT_SCHEMA = "sarvam.voice-eval/v1"
COMPARISON_SCHEMA = "sarvam.voice-compare/v1"
MOCK_SCHEMA = "sarvam.voice-mock/v1"
SUITE_VERSION = 1
EXIT_OK = 0
EXIT_REGRESSION = 1
EXIT_INVALID = 2
EXIT_LIVE_FAILURE = 3
EXIT_INTERRUPTED = 130

STT_LANGUAGES = {
    "unknown",
    "as-IN",
    "bn-IN",
    "brx-IN",
    "doi-IN",
    "en-IN",
    "gu-IN",
    "hi-IN",
    "kn-IN",
    "kok-IN",
    "ks-IN",
    "mai-IN",
    "ml-IN",
    "mni-IN",
    "mr-IN",
    "ne-IN",
    "od-IN",
    "pa-IN",
    "sa-IN",
    "sat-IN",
    "sd-IN",
    "ta-IN",
    "te-IN",
    "ur-IN",
}
TTS_LANGUAGES = {
    "bn-IN",
    "en-IN",
    "gu-IN",
    "hi-IN",
    "kn-IN",
    "ml-IN",
    "mr-IN",
    "od-IN",
    "pa-IN",
    "ta-IN",
    "te-IN",
}
STT_MODES = {"transcribe", "translate", "verbatim", "translit", "codemix"}
TTS_CODECS = {"mp3", "linear16", "mulaw", "alaw", "opus", "flac", "aac", "wav"}
REDACTED = "<redacted>"

DEFAULTS: dict[str, Any] = {
    "version": SUITE_VERSION,
    "name": "sarvam-voice-regression",
    "pipeline": {
        "stt": {
            "model": "saaras:v3",
            "language": "unknown",
            "mode": "transcribe",
            "sample_rate": 16000,
            "chunk_ms": 250,
            "realtime_pacing": True,
            "vad": {
                "high_sensitivity": False,
                "signals": True,
                "positive_speech_threshold": None,
                "negative_speech_threshold": None,
                "min_speech_frames": None,
                "first_turn_min_speech_frames": None,
                "negative_frames_count": None,
                "negative_frames_window": None,
                "start_speech_volume_threshold": None,
                "interrupt_min_speech_frames": None,
                "pre_speech_pad_frames": None,
                "num_initial_ignored_frames": None,
            },
        },
        "llm": {
            "model": "sarvam-30b",
            "system_prompt": (
                "You are a concise voice assistant. Answer in the user's language and keep "
                "the response easy to speak aloud."
            ),
            "temperature": 0.2,
            "reasoning_effort": None,
            "max_tokens": 500,
        },
        "tts": {
            "model": "bulbul:v3",
            "language": "hi-IN",
            "speaker": "shubh",
            "pace": 1.0,
            "temperature": 0.6,
            "codec": "wav",
            "sample_rate": 24000,
        },
    },
    "execution": {
        "repetitions": 1,
        "timeout_seconds": 60,
        "retries": 0,
        "concurrency": 1,
        "budget_inr": 10.0,
    },
    "pricing": {
        "currency": "INR",
        "retrieved_at": "2026-07-19",
        "source": "https://docs.sarvam.ai/api/getting-started/pricing",
        "stt_inr_per_hour": 30.0,
        "llm_input_inr_per_million_tokens": 2.5,
        "llm_cached_input_inr_per_million_tokens": 1.5,
        "llm_output_inr_per_million_tokens": 10.0,
        "tts_inr_per_10k_characters": 30.0,
    },
    "gates": {
        "max_normalized_wer": 0.25,
        "max_normalized_cer": 0.15,
        "min_configured_entity_recall": 0.95,
        "max_eos_to_first_audio_p95_ms": 2500.0,
        "min_success_rate": 0.99,
        "max_estimated_cost_inr": None,
    },
    "regression": {
        "max_normalized_wer_increase": 0.02,
        "max_eos_to_first_audio_p95_increase_ms": 250.0,
        "max_cost_increase_percent": 15.0,
        "max_success_rate_drop": 0.01,
    },
    "cases": [],
}


class VoiceLabError(Exception):
    """Base error for stable CLI handling."""


class ValidationError(VoiceLabError):
    """Invalid suite, report, or input audio."""


class LiveRunError(VoiceLabError):
    """A live pipeline stage failed."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def deep_merge(base: Mapping[str, Any], override: Mapping[str, Any]) -> dict[str, Any]:
    merged = copy.deepcopy(dict(base))
    for key, value in override.items():
        if isinstance(value, Mapping) and isinstance(merged.get(key), Mapping):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover - uv installs script dependencies
        raise ValidationError(
            "PyYAML is required; run this script with `uv run`."
        ) from exc
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValidationError(f"Suite does not exist: {path}") from exc
    except yaml.YAMLError as exc:
        raise ValidationError(f"Invalid YAML in {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValidationError("Suite root must be a YAML mapping.")
    return payload


def require_number(value: Any, field: str, *, minimum: float | None = None) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValidationError(f"{field} must be a number.")
    number = float(value)
    if minimum is not None and number < minimum:
        raise ValidationError(f"{field} must be at least {minimum}.")
    return number


def require_int(value: Any, field: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValidationError(f"{field} must be an integer >= {minimum}.")
    return value


def validate_suite(raw: Mapping[str, Any], manifest_path: Path) -> dict[str, Any]:
    suite = deep_merge(DEFAULTS, raw)
    if suite.get("version") != SUITE_VERSION:
        raise ValidationError(f"version must be {SUITE_VERSION}.")
    if not isinstance(suite.get("name"), str) or not suite["name"].strip():
        raise ValidationError("name must be a non-empty string.")

    pipeline = suite["pipeline"]
    stt, llm, tts = pipeline["stt"], pipeline["llm"], pipeline["tts"]
    if stt["model"] != "saaras:v3":
        raise ValidationError("pipeline.stt.model must be `saaras:v3` in v1.")
    if stt["language"] not in STT_LANGUAGES:
        raise ValidationError(f"Unsupported STT language: {stt['language']}")
    if stt["mode"] not in STT_MODES:
        raise ValidationError(f"Unsupported STT mode: {stt['mode']}")
    if stt["sample_rate"] not in {8000, 16000}:
        raise ValidationError("pipeline.stt.sample_rate must be 8000 or 16000.")
    require_int(stt["chunk_ms"], "pipeline.stt.chunk_ms", minimum=20)
    if not isinstance(stt["realtime_pacing"], bool):
        raise ValidationError("pipeline.stt.realtime_pacing must be true or false.")
    if not isinstance(stt.get("vad"), dict):
        raise ValidationError("pipeline.stt.vad must be a mapping.")
    for boolean_key in ("high_sensitivity", "signals"):
        if not isinstance(stt["vad"].get(boolean_key), bool):
            raise ValidationError(
                f"pipeline.stt.vad.{boolean_key} must be true or false."
            )

    if llm["model"] != "sarvam-30b":
        raise ValidationError("pipeline.llm.model must be `sarvam-30b` in v1.")
    require_number(llm["temperature"], "pipeline.llm.temperature", minimum=0)
    require_int(llm["max_tokens"], "pipeline.llm.max_tokens", minimum=1)
    if llm.get("reasoning_effort") not in {None, "low", "medium", "high"}:
        raise ValidationError(
            "pipeline.llm.reasoning_effort must be null, low, medium, or high."
        )
    if (
        not isinstance(llm.get("system_prompt"), str)
        or not llm["system_prompt"].strip()
    ):
        raise ValidationError("pipeline.llm.system_prompt must be a non-empty string.")

    if tts["model"] != "bulbul:v3":
        raise ValidationError("pipeline.tts.model must be `bulbul:v3` in v1.")
    if tts["language"] not in TTS_LANGUAGES:
        raise ValidationError(f"Unsupported TTS language: {tts['language']}")
    if tts["codec"] not in TTS_CODECS:
        raise ValidationError(f"Unsupported TTS codec: {tts['codec']}")
    if not isinstance(tts["speaker"], str) or tts["speaker"] != tts["speaker"].lower():
        raise ValidationError("pipeline.tts.speaker must be a lowercase speaker name.")
    pace = require_number(tts["pace"], "pipeline.tts.pace")
    if not 0.5 <= pace <= 2.0:
        raise ValidationError(
            "pipeline.tts.pace must be between 0.5 and 2.0 for Bulbul v3."
        )
    if tts["sample_rate"] not in {8000, 16000, 22050, 24000}:
        raise ValidationError(
            "Streaming TTS sample rate must be 8000, 16000, 22050, or 24000."
        )

    execution = suite["execution"]
    for key, minimum in (("repetitions", 1), ("retries", 0), ("concurrency", 1)):
        require_int(execution[key], f"execution.{key}", minimum=minimum)
    require_number(
        execution["timeout_seconds"], "execution.timeout_seconds", minimum=0.1
    )
    require_number(execution["budget_inr"], "execution.budget_inr", minimum=0)

    for section_name in ("gates", "regression"):
        section = suite.get(section_name)
        if not isinstance(section, dict):
            raise ValidationError(f"{section_name} must be a mapping.")
        for key, value in section.items():
            if value is not None:
                require_number(value, f"{section_name}.{key}")

    pricing = suite["pricing"]
    if pricing.get("currency") != "INR":
        raise ValidationError("pricing.currency must be INR.")
    for key in (
        "stt_inr_per_hour",
        "llm_input_inr_per_million_tokens",
        "llm_cached_input_inr_per_million_tokens",
        "llm_output_inr_per_million_tokens",
        "tts_inr_per_10k_characters",
    ):
        require_number(pricing.get(key), f"pricing.{key}", minimum=0)
    if not str(pricing.get("source", "")).startswith("https://docs.sarvam.ai/"):
        raise ValidationError(
            "pricing.source must link to Sarvam's official documentation."
        )

    cases = suite.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValidationError("cases must contain at least one case.")
    seen: set[str] = set()
    for index, case in enumerate(cases):
        prefix = f"cases[{index}]"
        if not isinstance(case, dict):
            raise ValidationError(f"{prefix} must be a mapping.")
        case_id = case.get("id")
        if not isinstance(case_id, str) or not re.fullmatch(
            r"[a-z0-9][a-z0-9._-]*", case_id
        ):
            raise ValidationError(
                f"{prefix}.id must use lowercase letters, digits, ., _, or -."
            )
        if case_id in seen:
            raise ValidationError(f"Duplicate case id: {case_id}")
        seen.add(case_id)
        if not isinstance(case.get("audio"), str) or not case["audio"].strip():
            raise ValidationError(f"{prefix}.audio must be a path string.")
        if not isinstance(case.get("reference"), str):
            raise ValidationError(f"{prefix}.reference must be a string.")
        language = case.get("language", stt["language"])
        if language not in STT_LANGUAGES:
            raise ValidationError(
                f"Unsupported case language for {case_id}: {language}"
            )
        tts_language = case.get("tts_language", tts["language"])
        if tts_language not in TTS_LANGUAGES:
            raise ValidationError(
                f"Unsupported case TTS language for {case_id}: {tts_language}"
            )
        tags = case.get("tags", [])
        if not isinstance(tags, list) or not all(
            isinstance(tag, str) and tag for tag in tags
        ):
            raise ValidationError(f"{prefix}.tags must be a list of non-empty strings.")
        entities = case.get("entities", [])
        if not isinstance(entities, list):
            raise ValidationError(f"{prefix}.entities must be a list.")
        for entity in entities:
            if isinstance(entity, str):
                continue
            if not isinstance(entity, dict) or not isinstance(entity.get("value"), str):
                raise ValidationError(
                    f"{prefix}.entities items need a string or a mapping with value."
                )
            aliases = entity.get("aliases", [])
            if not isinstance(aliases, list) or not all(
                isinstance(alias, str) for alias in aliases
            ):
                raise ValidationError(f"{prefix}.entities aliases must be strings.")
        case.setdefault("language", language)
        case.setdefault("tts_language", tts_language)
        case.setdefault("tags", [])
        case.setdefault("entities", [])
        case.setdefault("context", "")

    suite["_manifest"] = str(manifest_path.resolve())
    return suite


def case_audio_path(suite: Mapping[str, Any], case: Mapping[str, Any]) -> Path:
    manifest = Path(str(suite["_manifest"]))
    candidate = Path(str(case["audio"]))
    return (
        candidate
        if candidate.is_absolute()
        else (manifest.parent / candidate).resolve()
    )


def inspect_wav(path: Path, expected_rate: int | None = None) -> dict[str, Any]:
    if not path.exists():
        raise ValidationError(f"Audio file does not exist: {path}")
    try:
        with wave.open(str(path), "rb") as source:
            channels = source.getnchannels()
            sample_width = source.getsampwidth()
            sample_rate = source.getframerate()
            frames = source.getnframes()
            compression = source.getcomptype()
    except (wave.Error, EOFError) as exc:
        raise ValidationError(f"Not a readable PCM WAV file: {path}") from exc
    if (
        channels != 1
        or sample_width != 2
        or compression != "NONE"
        or sample_rate not in {8000, 16000}
    ):
        raise ValidationError(
            f"Unsupported audio {path}: expected mono 16-bit PCM WAV at 8 or 16 kHz. "
            "Convert with `ffmpeg -i input -ac 1 -ar 16000 -c:a pcm_s16le output.wav`."
        )
    if expected_rate is not None and sample_rate != expected_rate:
        raise ValidationError(
            f"Audio sample rate is {sample_rate} Hz but pipeline.stt.sample_rate is {expected_rate} Hz."
        )
    return {
        "channels": channels,
        "sample_width_bytes": sample_width,
        "sample_rate": sample_rate,
        "frames": frames,
        "duration_seconds": frames / sample_rate if sample_rate else 0.0,
    }


def wav_chunks(path: Path, chunk_ms: int) -> Iterable[tuple[bytes, float]]:
    """Yield independently decodable WAV chunks and each chunk's audio duration."""
    with wave.open(str(path), "rb") as source:
        channels = source.getnchannels()
        sample_width = source.getsampwidth()
        sample_rate = source.getframerate()
        frames_per_chunk = max(1, round(sample_rate * chunk_ms / 1000))
        while True:
            frames = source.readframes(frames_per_chunk)
            if not frames:
                return
            frame_count = len(frames) // (channels * sample_width)
            buffer = io.BytesIO()
            with wave.open(buffer, "wb") as chunk:
                chunk.setnchannels(channels)
                chunk.setsampwidth(sample_width)
                chunk.setframerate(sample_rate)
                chunk.writeframes(frames)
            yield buffer.getvalue(), frame_count / sample_rate


def estimate_tokens(text: str) -> int:
    return max(1, math.ceil(len(text) / 4))


def projected_cost(suite: Mapping[str, Any]) -> dict[str, Any]:
    execution, pipeline, pricing = (
        suite["execution"],
        suite["pipeline"],
        suite["pricing"],
    )
    stt_total = llm_input_total = llm_output_total = tts_total = 0.0
    audio_seconds = 0.0
    max_tokens = int(pipeline["llm"]["max_tokens"])
    for case in suite["cases"]:
        info = inspect_wav(
            case_audio_path(suite, case), int(pipeline["stt"]["sample_rate"])
        )
        repetitions = int(execution["repetitions"])
        maximum_attempts = repetitions * (int(execution["retries"]) + 1)
        duration = info["duration_seconds"]
        audio_seconds += duration * maximum_attempts
        billed_seconds = max(1, math.ceil(duration)) * maximum_attempts
        stt_total += billed_seconds * float(pricing["stt_inr_per_hour"]) / 3600
        prompt = f"{pipeline['llm']['system_prompt']}\n{case.get('context', '')}\n{case['reference']}"
        input_tokens = estimate_tokens(prompt) * maximum_attempts
        output_tokens = max_tokens * maximum_attempts
        llm_input_total += (
            input_tokens
            * float(pricing["llm_input_inr_per_million_tokens"])
            / 1_000_000
        )
        llm_output_total += (
            output_tokens
            * float(pricing["llm_output_inr_per_million_tokens"])
            / 1_000_000
        )
        conservative_chars = min(2500, max_tokens * 4) * maximum_attempts
        tts_total += (
            conservative_chars * float(pricing["tts_inr_per_10k_characters"]) / 10_000
        )
    total = stt_total + llm_input_total + llm_output_total + tts_total
    return {
        "audio_seconds": round(audio_seconds, 6),
        "stt_inr": round(stt_total, 6),
        "llm_input_inr": round(llm_input_total, 6),
        "llm_output_inr": round(llm_output_total, 6),
        "tts_inr": round(tts_total, 6),
        "total_inr": round(total, 6),
        "method": "conservative upper bound from audio duration, max tokens, and pricing snapshot",
    }


def build_plan(suite: Mapping[str, Any]) -> dict[str, Any]:
    projection = projected_cost(suite)
    cases = []
    for case in suite["cases"]:
        info = inspect_wav(
            case_audio_path(suite, case), suite["pipeline"]["stt"]["sample_rate"]
        )
        cases.append(
            {
                "id": case["id"],
                "audio": case["audio"],
                "language": case["language"],
                "tags": sorted(case["tags"]),
                "duration_seconds": round(info["duration_seconds"], 6),
            }
        )
    budget = float(suite["execution"]["budget_inr"])
    return {
        "schema_version": "sarvam.voice-plan/v1",
        "suite": suite["name"],
        "case_count": len(cases),
        "planned_runs": len(cases) * int(suite["execution"]["repetitions"]),
        "maximum_attempts": len(cases)
        * int(suite["execution"]["repetitions"])
        * (int(suite["execution"]["retries"]) + 1),
        "budget_inr": budget,
        "within_budget": projection["total_inr"] <= budget,
        "projected_cost": projection,
        "pricing": suite["pricing"],
        "cases": cases,
    }


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text).casefold()
    normalized = "".join(
        str(unicodedata.digit(character))
        if unicodedata.category(character) == "Nd"
        else character
        for character in normalized
    )
    normalized = "".join(
        " " if unicodedata.category(character)[0] in {"P", "S", "Z"} else character
        for character in normalized
    )
    return " ".join(normalized.split())


def edit_distance(reference: Sequence[Any], hypothesis: Sequence[Any]) -> int:
    if len(reference) < len(hypothesis):
        reference, hypothesis = hypothesis, reference
    previous = list(range(len(hypothesis) + 1))
    for row, reference_item in enumerate(reference, 1):
        current = [row]
        for column, hypothesis_item in enumerate(hypothesis, 1):
            current.append(
                min(
                    current[-1] + 1,
                    previous[column] + 1,
                    previous[column - 1] + (reference_item != hypothesis_item),
                )
            )
        previous = current
    return previous[-1]


def error_rate(reference: Sequence[Any], hypothesis: Sequence[Any]) -> float:
    if not reference:
        return 0.0 if not hypothesis else 1.0
    return edit_distance(reference, hypothesis) / len(reference)


def text_quality(reference: str, hypothesis: str) -> dict[str, float]:
    normalized_reference = normalize_text(reference)
    normalized_hypothesis = normalize_text(hypothesis)
    try:
        import jiwer
    except ImportError:  # pragma: no cover - direct imports can still exercise helpers

        def wer(left: str, right: str) -> float:
            return error_rate(left.split(), right.split())

        def cer(left: str, right: str) -> float:
            return error_rate(list(left), list(right))
    else:
        wer = jiwer.wer
        cer = jiwer.cer
    return {
        "raw_wer": float(wer(reference, hypothesis)),
        "raw_cer": float(cer(reference, hypothesis)),
        "normalized_wer": float(wer(normalized_reference, normalized_hypothesis)),
        "normalized_cer": float(cer(normalized_reference, normalized_hypothesis)),
    }


def entity_forms(entity: str | Mapping[str, Any]) -> list[str]:
    if isinstance(entity, str):
        return [entity]
    return [str(entity["value"]), *[str(alias) for alias in entity.get("aliases", [])]]


def lookup_forms(text: str) -> set[str]:
    normalized = normalize_text(text)
    forms = {normalized, re.sub(r"\s+", "", normalized)}
    digits = "".join(character for character in normalized if character.isdigit())
    if digits:
        forms.add(digits)
    return {form for form in forms if form}


def configured_entity_recall(
    entities: Sequence[str | Mapping[str, Any]], hypothesis: str
) -> float:
    if not entities:
        return 1.0
    hypothesis_forms = lookup_forms(hypothesis)
    normalized_hypothesis = normalize_text(hypothesis)
    compact_hypothesis = re.sub(r"\s+", "", normalized_hypothesis)
    hypothesis_digits = "".join(
        character for character in normalize_text(hypothesis) if character.isdigit()
    )
    found = 0
    for entity in entities:
        candidates = set().union(*(lookup_forms(form) for form in entity_forms(entity)))
        matched = any(
            candidate in hypothesis_forms
            or candidate in normalized_hypothesis
            or candidate in compact_hypothesis
            or (candidate.isdigit() and candidate in hypothesis_digits)
            for candidate in candidates
        )
        found += int(matched)
    return found / len(entities)


def transcript_payload(text: str, include_text: bool) -> dict[str, Any]:
    payload = {
        "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "characters": len(text),
        "redacted": not include_text,
    }
    if include_text:
        payload["text"] = text
    return payload


def sanitize_error(error: BaseException | str) -> str:
    message = str(error)
    key = os.getenv("SARVAM_API_KEY")
    if key:
        message = message.replace(key, REDACTED)
    message = re.sub(
        r"(?i)(api[-_ ]?subscription[-_ ]?key|authorization)(\s*[:=]\s*)([^\s,;}]+)",
        rf"\1\2{REDACTED}",
        message,
    )
    message = re.sub(r"sk_[A-Za-z0-9_-]+", REDACTED, message)
    return message[:1000]


def usage_dict(usage: Any) -> dict[str, int] | None:
    if usage is None:
        return None
    if isinstance(usage, Mapping):

        def get(key: str, default: int = 0) -> Any:
            return usage.get(key, default)
    else:

        def get(key: str, default: int = 0) -> Any:
            return getattr(usage, key, default)

    return {
        "prompt_tokens": int(get("prompt_tokens", 0)),
        "completion_tokens": int(get("completion_tokens", 0)),
        "total_tokens": int(get("total_tokens", 0)),
    }


def calculate_cost(
    suite: Mapping[str, Any],
    *,
    audio_seconds: float,
    prompt_text: str,
    response_text: str,
    usage: Mapping[str, int] | None,
) -> dict[str, Any]:
    pricing = suite["pricing"]
    billed_audio_seconds = max(1, math.ceil(audio_seconds))
    stt = billed_audio_seconds * float(pricing["stt_inr_per_hour"]) / 3600
    exact_usage = (
        usage is not None
        and usage.get("prompt_tokens", 0) + usage.get("completion_tokens", 0) > 0
    )
    prompt_tokens = (
        int(usage["prompt_tokens"]) if exact_usage else estimate_tokens(prompt_text)
    )
    completion_tokens = (
        int(usage["completion_tokens"])
        if exact_usage
        else estimate_tokens(response_text)
    )
    llm_input = (
        prompt_tokens * float(pricing["llm_input_inr_per_million_tokens"]) / 1_000_000
    )
    llm_output = (
        completion_tokens
        * float(pricing["llm_output_inr_per_million_tokens"])
        / 1_000_000
    )
    tts_characters = len(response_text)
    tts = tts_characters * float(pricing["tts_inr_per_10k_characters"]) / 10_000
    total = stt + llm_input + llm_output + tts
    return {
        "currency": "INR",
        "stt_inr": round(stt, 6),
        "llm_input_inr": round(llm_input, 6),
        "llm_output_inr": round(llm_output, 6),
        "tts_inr": round(tts, 6),
        "total_inr": round(total, 6),
        "billable_audio_seconds": billed_audio_seconds,
        "llm_prompt_tokens": prompt_tokens,
        "llm_completion_tokens": completion_tokens,
        "tts_characters": tts_characters,
        "llm_usage_exact": exact_usage,
        "estimated": not exact_usage,
    }


def response_type(response: Any) -> str:
    if isinstance(response, Mapping):
        return str(response.get("type", ""))
    return str(getattr(response, "type", ""))


def response_data(response: Any) -> Any:
    if isinstance(response, Mapping):
        return response.get("data", {})
    return getattr(response, "data", None)


def data_value(data: Any, key: str, default: Any = None) -> Any:
    if isinstance(data, Mapping):
        return data.get(key, default)
    return getattr(data, key, default)


def vad_connect_args(vad: Mapping[str, Any]) -> dict[str, Any]:
    args = {
        "high_vad_sensitivity": str(bool(vad["high_sensitivity"])).lower(),
        "vad_signals": str(bool(vad["signals"])).lower(),
        "flush_signal": "true",
    }
    mappings = {
        "positive_speech_threshold": "positive_speech_threshold",
        "negative_speech_threshold": "negative_speech_threshold",
        "min_speech_frames": "min_speech_frames",
        "first_turn_min_speech_frames": "first_turn_min_speech_frames",
        "negative_frames_count": "negative_frames_count",
        "negative_frames_window": "negative_frames_window",
        "start_speech_volume_threshold": "start_speech_volume_threshold",
        "interrupt_min_speech_frames": "interrupt_min_speech_frames",
        "pre_speech_pad_frames": "pre_speech_pad_frames",
        "num_initial_ignored_frames": "num_initial_ignored_frames",
    }
    for suite_key, api_key in mappings.items():
        if vad.get(suite_key) is not None:
            args[api_key] = str(vad[suite_key])
    return args


async def stream_stt(
    client: Any,
    suite: Mapping[str, Any],
    case: Mapping[str, Any],
    clock: Any = time.monotonic,
) -> dict[str, Any]:
    stt = suite["pipeline"]["stt"]
    path = case_audio_path(suite, case)
    start = clock()
    connected_at = start
    audio_finished_at = start
    flushed = False
    transcripts: list[str] = []
    vad_start: float | None = None
    vad_end: float | None = None
    finalized_at: float | None = None
    final_event = asyncio.Event()

    connect = client.speech_to_text_streaming.connect(
        language_code=case["language"],
        model=stt["model"],
        mode=stt["mode"],
        sample_rate=str(stt["sample_rate"]),
        input_audio_codec="wav",
        **vad_connect_args(stt["vad"]),
    )
    async with connect as socket:
        connected_at = clock()

        async def receive() -> None:
            nonlocal vad_start, vad_end, finalized_at
            while True:
                response = await socket.recv()
                now = clock()
                kind = response_type(response)
                data = response_data(response)
                if kind == "events":
                    signal = str(data_value(data, "signal_type", ""))
                    if signal == "START_SPEECH" and vad_start is None:
                        vad_start = now
                    elif signal == "END_SPEECH":
                        vad_end = now
                elif kind == "data":
                    transcript = str(data_value(data, "transcript", "")).strip()
                    if transcript:
                        transcripts.append(transcript)
                        finalized_at = now
                        if flushed:
                            final_event.set()
                elif kind == "error":
                    raise LiveRunError(
                        str(data_value(data, "error", "STT streaming error"))
                    )

        receiver = asyncio.create_task(receive())
        next_deadline = clock()
        try:
            for chunk, duration in wav_chunks(path, int(stt["chunk_ms"])):
                await socket.transcribe(
                    audio=base64.b64encode(chunk).decode("ascii"),
                    encoding="audio/wav",
                    sample_rate=int(stt["sample_rate"]),
                )
                if stt["realtime_pacing"]:
                    next_deadline += duration
                    delay = next_deadline - clock()
                    if delay > 0:
                        await asyncio.sleep(delay)
            audio_finished_at = clock()
            flushed = True
            await socket.flush()
            if transcripts:
                final_event.set()
            waiter = asyncio.create_task(final_event.wait())
            done, _ = await asyncio.wait(
                {waiter, receiver}, return_when=asyncio.FIRST_COMPLETED
            )
            if receiver in done:
                exception = receiver.exception()
                if exception:
                    raise exception
                if not final_event.is_set():
                    raise LiveRunError("STT stream closed without a final transcript.")
            await waiter
        finally:
            receiver.cancel()
            await asyncio.gather(receiver, return_exceptions=True)

    if not transcripts or finalized_at is None:
        raise LiveRunError("STT returned no transcript.")
    speech_end = vad_end or audio_finished_at
    return {
        "transcript": " ".join(transcripts).strip(),
        "connection_ms": (connected_at - start) * 1000,
        "vad_start_ms": (vad_start - start) * 1000 if vad_start is not None else None,
        "vad_end_ms": (vad_end - start) * 1000 if vad_end is not None else None,
        "audio_send_ms": (audio_finished_at - connected_at) * 1000,
        "finalization_after_speech_end_ms": max(
            0.0, (finalized_at - speech_end) * 1000
        ),
        "total_ms": (finalized_at - start) * 1000,
        "speech_end_at": speech_end,
        "finalized_at": finalized_at,
    }


async def stream_llm(
    client: Any,
    suite: Mapping[str, Any],
    case: Mapping[str, Any],
    transcript: str,
    clock: Any = time.monotonic,
) -> dict[str, Any]:
    config = suite["pipeline"]["llm"]
    user_text = transcript
    if case.get("context"):
        user_text = f"Context: {case['context']}\n\nUser said: {transcript}"
    messages = [
        {"role": "system", "content": config["system_prompt"]},
        {"role": "user", "content": user_text},
    ]
    start = clock()
    first_token_at: float | None = None
    pieces: list[str] = []
    usage = None
    stream: AsyncIterator[Any] = await client.chat.completions(
        messages=messages,
        model=config["model"],
        temperature=config["temperature"],
        reasoning_effort=config.get("reasoning_effort"),
        max_tokens=config["max_tokens"],
        stream=True,
        n=1,
    )
    async for chunk in stream:
        usage = usage_dict(getattr(chunk, "usage", None)) or usage
        choices = getattr(chunk, "choices", [])
        if not choices:
            continue
        content = getattr(choices[0].delta, "content", None)
        if content:
            if first_token_at is None:
                first_token_at = clock()
            pieces.append(content)
    finished_at = clock()
    text = "".join(pieces).strip()
    if not text or first_token_at is None:
        raise LiveRunError(
            "Sarvam-30B returned no speakable content. Increase max_tokens or keep reasoning_effort null."
        )
    return {
        "text": text,
        "prompt_text": f"{config['system_prompt']}\n{user_text}",
        "usage": usage,
        "time_to_first_token_ms": (first_token_at - start) * 1000,
        "total_ms": (finished_at - start) * 1000,
        "finished_at": finished_at,
    }


async def stream_tts(
    client: Any,
    suite: Mapping[str, Any],
    case: Mapping[str, Any],
    text: str,
    clock: Any = time.monotonic,
) -> dict[str, Any]:
    if len(text) > 2500:
        raise LiveRunError("Bulbul v3 input exceeds the 2,500 character limit.")
    config = suite["pipeline"]["tts"]
    start = clock()
    first_byte_at: float | None = None
    chunks: list[bytes] = []
    stream = client.text_to_speech.convert_stream(
        text=text,
        target_language_code=case["tts_language"],
        speaker=config["speaker"],
        pace=config["pace"],
        speech_sample_rate=config["sample_rate"],
        enable_preprocessing=True,
        model=config["model"],
        temperature=config["temperature"],
        output_audio_codec=config["codec"],
    )
    async for chunk in stream:
        if not chunk:
            continue
        if first_byte_at is None:
            first_byte_at = clock()
        chunks.append(bytes(chunk))
    finished_at = clock()
    if first_byte_at is None:
        raise LiveRunError("Bulbul v3 returned no audio bytes.")
    return {
        "audio": b"".join(chunks),
        "first_byte_at": first_byte_at,
        "time_to_first_byte_ms": (first_byte_at - start) * 1000,
        "total_ms": (finished_at - start) * 1000,
        "bytes": sum(len(chunk) for chunk in chunks),
    }


async def run_case_live_once(
    suite: Mapping[str, Any],
    case: Mapping[str, Any],
    repetition: int,
    include_transcripts: bool,
    retain_audio: bool,
    output_dir: Path,
) -> dict[str, Any]:
    try:
        from sarvamai import AsyncSarvamAI
    except ImportError as exc:  # pragma: no cover - uv installs script dependencies
        raise LiveRunError(
            "sarvamai is required; run this script with `uv run`."
        ) from exc
    client = AsyncSarvamAI(
        api_subscription_key=os.getenv("SARVAM_API_KEY"),
        timeout=suite["execution"]["timeout_seconds"],
    )
    started = time.monotonic()
    stt = await stream_stt(client, suite, case)
    llm = await stream_llm(client, suite, case, stt["transcript"])
    tts = await stream_tts(client, suite, case, llm["text"])
    audio_info = inspect_wav(
        case_audio_path(suite, case), suite["pipeline"]["stt"]["sample_rate"]
    )
    quality = text_quality(case["reference"], stt["transcript"])
    quality["configured_entity_recall"] = configured_entity_recall(
        case["entities"], stt["transcript"]
    )
    cost = calculate_cost(
        suite,
        audio_seconds=audio_info["duration_seconds"],
        prompt_text=llm["prompt_text"],
        response_text=llm["text"],
        usage=llm["usage"],
    )
    audio_path = None
    if retain_audio:
        audio_dir = output_dir / "audio"
        audio_dir.mkdir(parents=True, exist_ok=True)
        extension = suite["pipeline"]["tts"]["codec"]
        audio_path = audio_dir / f"{case['id']}-r{repetition}.{extension}"
        audio_path.write_bytes(tts["audio"])
    return {
        "case_id": case["id"],
        "repetition": repetition,
        "language": case["language"],
        "tags": sorted(case["tags"]),
        "status": "passed",
        "attempts": 1,
        "error": None,
        "transcript": transcript_payload(stt["transcript"], include_transcripts),
        "response": transcript_payload(llm["text"], include_transcripts),
        "quality": {key: round(value, 6) for key, value in quality.items()},
        "latency_ms": {
            "stt_connection": round(stt["connection_ms"], 3),
            "vad_start": round(stt["vad_start_ms"], 3)
            if stt["vad_start_ms"] is not None
            else None,
            "vad_end": round(stt["vad_end_ms"], 3)
            if stt["vad_end_ms"] is not None
            else None,
            "stt_finalization_after_speech_end": round(
                stt["finalization_after_speech_end_ms"], 3
            ),
            "stt_total": round(stt["total_ms"], 3),
            "llm_time_to_first_token": round(llm["time_to_first_token_ms"], 3),
            "llm_total": round(llm["total_ms"], 3),
            "tts_time_to_first_byte": round(tts["time_to_first_byte_ms"], 3),
            "tts_total": round(tts["total_ms"], 3),
            "eos_to_first_audio": round(
                (tts["first_byte_at"] - stt["speech_end_at"]) * 1000, 3
            ),
            "total_turn": round((time.monotonic() - started) * 1000, 3),
        },
        "billable_units": {
            "audio_seconds": cost["billable_audio_seconds"],
            "llm_prompt_tokens": cost["llm_prompt_tokens"],
            "llm_completion_tokens": cost["llm_completion_tokens"],
            "tts_characters": cost["tts_characters"],
            "tts_bytes": tts["bytes"],
        },
        "cost": cost,
        "retained_audio": str(audio_path.relative_to(output_dir))
        if audio_path
        else None,
    }


def mock_case_once(
    suite: Mapping[str, Any],
    case: Mapping[str, Any],
    repetition: int,
    entry: Mapping[str, Any],
    include_transcripts: bool,
) -> dict[str, Any]:
    if entry.get("error"):
        raise LiveRunError(str(entry["error"]))
    stt_events = entry.get("stt", [])
    if not isinstance(stt_events, list):
        raise ValidationError("Mock stt must be a list.")
    vad_start = vad_end = final_at = None
    transcript = ""
    for event in stt_events:
        at_ms = float(event.get("at_ms", 0))
        if event.get("type") == "events" and event.get("signal_type") == "START_SPEECH":
            vad_start = at_ms if vad_start is None else vad_start
        elif event.get("type") == "events" and event.get("signal_type") == "END_SPEECH":
            vad_end = at_ms
        elif event.get("type") == "data" and event.get("transcript"):
            transcript = str(event["transcript"])
            final_at = at_ms
        elif event.get("type") == "error":
            raise LiveRunError(str(event.get("message", "mock STT error")))
    if not transcript or final_at is None:
        raise LiveRunError("Mock STT returned no transcript.")

    llm = entry.get("llm", {})
    llm_chunks = llm.get("chunks", [])
    content_chunks = [chunk for chunk in llm_chunks if chunk.get("content")]
    if not content_chunks:
        raise LiveRunError("Mock LLM returned no speakable content.")
    response_text = "".join(str(chunk["content"]) for chunk in content_chunks).strip()
    llm_first = float(content_chunks[0].get("at_ms", 0))
    llm_total = max(float(chunk.get("at_ms", 0)) for chunk in llm_chunks)
    usage = usage_dict(llm.get("usage"))

    tts = entry.get("tts", {})
    tts_chunks = tts.get("chunks", [])
    if not tts_chunks:
        raise LiveRunError("Mock TTS returned no audio bytes.")
    tts_first = float(tts_chunks[0].get("at_ms", 0))
    tts_total = max(float(chunk.get("at_ms", 0)) for chunk in tts_chunks)
    tts_bytes = sum(int(chunk.get("bytes", 0)) for chunk in tts_chunks)
    speech_end = vad_end if vad_end is not None else max(0.0, final_at - 1)
    connection_ms = float(entry.get("connection_ms", 0))
    audio_info = inspect_wav(
        case_audio_path(suite, case), suite["pipeline"]["stt"]["sample_rate"]
    )
    prompt_text = f"{suite['pipeline']['llm']['system_prompt']}\n{case.get('context', '')}\n{transcript}"
    quality = text_quality(case["reference"], transcript)
    quality["configured_entity_recall"] = configured_entity_recall(
        case["entities"], transcript
    )
    cost = calculate_cost(
        suite,
        audio_seconds=audio_info["duration_seconds"],
        prompt_text=prompt_text,
        response_text=response_text,
        usage=usage,
    )
    return {
        "case_id": case["id"],
        "repetition": repetition,
        "language": case["language"],
        "tags": sorted(case["tags"]),
        "status": "passed",
        "attempts": 1,
        "error": None,
        "transcript": transcript_payload(transcript, include_transcripts),
        "response": transcript_payload(response_text, include_transcripts),
        "quality": {key: round(value, 6) for key, value in quality.items()},
        "latency_ms": {
            "stt_connection": round(connection_ms, 3),
            "vad_start": vad_start,
            "vad_end": vad_end,
            "stt_finalization_after_speech_end": round(final_at - speech_end, 3),
            "stt_total": round(connection_ms + final_at, 3),
            "llm_time_to_first_token": round(llm_first, 3),
            "llm_total": round(llm_total, 3),
            "tts_time_to_first_byte": round(tts_first, 3),
            "tts_total": round(tts_total, 3),
            "eos_to_first_audio": round(
                (final_at - speech_end) + llm_total + tts_first, 3
            ),
            "total_turn": round(connection_ms + final_at + llm_total + tts_total, 3),
        },
        "billable_units": {
            "audio_seconds": cost["billable_audio_seconds"],
            "llm_prompt_tokens": cost["llm_prompt_tokens"],
            "llm_completion_tokens": cost["llm_completion_tokens"],
            "tts_characters": cost["tts_characters"],
            "tts_bytes": tts_bytes,
        },
        "cost": cost,
        "retained_audio": None,
    }


def status_code(error: BaseException) -> int | None:
    value = getattr(error, "status_code", None)
    if isinstance(value, int):
        return value
    match = re.search(r"(?:status|HTTP)\D{0,8}(\d{3})", str(error), flags=re.IGNORECASE)
    return int(match.group(1)) if match else None


def retryable(error: BaseException) -> bool:
    code = status_code(error)
    if code in {400, 401, 403, 404, 409, 422, 429}:
        return False
    if code is not None:
        return code >= 500
    return isinstance(
        error, (TimeoutError, asyncio.TimeoutError, ConnectionError, OSError)
    )


def failed_result(
    case: Mapping[str, Any], repetition: int, attempts: int, error: BaseException
) -> dict[str, Any]:
    return {
        "case_id": case["id"],
        "repetition": repetition,
        "language": case["language"],
        "tags": sorted(case["tags"]),
        "status": "failed",
        "attempts": attempts,
        "error": {
            "type": type(error).__name__,
            "message": sanitize_error(error),
            "status_code": status_code(error),
        },
        "transcript": None,
        "response": None,
        "quality": None,
        "latency_ms": None,
        "billable_units": None,
        "cost": None,
        "retained_audio": None,
    }


async def execute_runs(
    suite: Mapping[str, Any],
    output_dir: Path,
    *,
    include_transcripts: bool,
    retain_audio: bool,
    mock: Mapping[str, Any] | None,
) -> list[dict[str, Any]]:
    execution = suite["execution"]
    semaphore = asyncio.Semaphore(int(execution["concurrency"]))
    retries = int(execution["retries"])
    timeout = float(execution["timeout_seconds"])
    mock_cases = mock.get("cases", {}) if mock else {}

    async def one(case: Mapping[str, Any], repetition: int) -> dict[str, Any]:
        async with semaphore:
            for attempt in range(1, retries + 2):
                try:
                    if mock is not None:
                        if case["id"] not in mock_cases:
                            raise ValidationError(
                                f"Mock fixture has no case named {case['id']}."
                            )
                        result = mock_case_once(
                            suite,
                            case,
                            repetition,
                            mock_cases[case["id"]],
                            include_transcripts,
                        )
                    else:
                        result = await asyncio.wait_for(
                            run_case_live_once(
                                suite,
                                case,
                                repetition,
                                include_transcripts,
                                retain_audio,
                                output_dir,
                            ),
                            timeout=timeout,
                        )
                    result["attempts"] = attempt
                    return result
                except ValidationError:
                    raise
                except BaseException as error:
                    if isinstance(error, (KeyboardInterrupt, asyncio.CancelledError)):
                        raise
                    if attempt <= retries and retryable(error):
                        continue
                    return failed_result(case, repetition, attempt, error)
            raise AssertionError("unreachable")

    tasks = [
        asyncio.create_task(one(case, repetition))
        for case in suite["cases"]
        for repetition in range(1, int(execution["repetitions"]) + 1)
    ]
    results = await asyncio.gather(*tasks)
    return sorted(results, key=lambda item: (item["case_id"], item["repetition"]))


def percentile(values: Sequence[float], quantile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(float(value) for value in values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * quantile
    lower, upper = math.floor(position), math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def metric_summary(values: Sequence[float]) -> dict[str, float | None]:
    if not values:
        return {"sample_count": 0, "mean": None, "p50": None, "p95": None}
    return {
        "sample_count": len(values),
        "mean": round(statistics.fmean(values), 6),
        "p50": round(float(percentile(values, 0.5)), 6),
        "p95": round(float(percentile(values, 0.95)), 6),
    }


def aggregate_results(results: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    successes = [result for result in results if result["status"] == "passed"]
    quality_fields = [
        "raw_wer",
        "raw_cer",
        "normalized_wer",
        "normalized_cer",
        "configured_entity_recall",
    ]
    latency_fields = [
        "stt_connection",
        "vad_start",
        "vad_end",
        "stt_finalization_after_speech_end",
        "stt_total",
        "llm_time_to_first_token",
        "llm_total",
        "tts_time_to_first_byte",
        "tts_total",
        "eos_to_first_audio",
        "total_turn",
    ]
    return {
        "sample_count": len(results),
        "success_count": len(successes),
        "failure_count": len(results) - len(successes),
        "success_rate": round(len(successes) / len(results), 6) if results else 0.0,
        "quality": {
            field: metric_summary(
                [float(result["quality"][field]) for result in successes]
            )
            for field in quality_fields
        },
        "latency_ms": {
            field: metric_summary(
                [
                    float(result["latency_ms"][field])
                    for result in successes
                    if result["latency_ms"].get(field) is not None
                ]
            )
            for field in latency_fields
        },
        "estimated_cost_inr": round(
            sum(float(result["cost"]["total_inr"]) for result in successes), 6
        ),
        "all_llm_usage_exact": bool(successes)
        and all(not result["cost"]["estimated"] for result in successes),
    }


def grouped_aggregates(results: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    by_language: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    by_tag: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for result in results:
        by_language[str(result["language"])].append(result)
        for tag in result["tags"]:
            by_tag[str(tag)].append(result)
    return {
        "suite": aggregate_results(results),
        "by_language": {
            key: aggregate_results(by_language[key]) for key in sorted(by_language)
        },
        "by_tag": {key: aggregate_results(by_tag[key]) for key in sorted(by_tag)},
    }


def make_gate(
    name: str, actual: float | None, threshold: float | None, direction: str
) -> dict[str, Any]:
    if threshold is None:
        return {
            "name": name,
            "status": "skipped",
            "actual": actual,
            "threshold": None,
            "direction": direction,
        }
    passed = actual is not None and (
        actual <= threshold if direction == "max" else actual >= threshold
    )
    return {
        "name": name,
        "status": "passed" if passed else "failed",
        "actual": actual,
        "threshold": threshold,
        "direction": direction,
    }


def evaluate_gates(
    aggregates: Mapping[str, Any], gates: Mapping[str, Any]
) -> list[dict[str, Any]]:
    suite = aggregates["suite"]
    return [
        make_gate(
            "normalized WER mean",
            suite["quality"]["normalized_wer"]["mean"],
            gates.get("max_normalized_wer"),
            "max",
        ),
        make_gate(
            "normalized CER mean",
            suite["quality"]["normalized_cer"]["mean"],
            gates.get("max_normalized_cer"),
            "max",
        ),
        make_gate(
            "configured entity recall mean",
            suite["quality"]["configured_entity_recall"]["mean"],
            gates.get("min_configured_entity_recall"),
            "min",
        ),
        make_gate(
            "EOS to first audio p95 (ms)",
            suite["latency_ms"]["eos_to_first_audio"]["p95"],
            gates.get("max_eos_to_first_audio_p95_ms"),
            "max",
        ),
        make_gate(
            "success rate", suite["success_rate"], gates.get("min_success_rate"), "min"
        ),
        make_gate(
            "estimated cost (INR)",
            suite["estimated_cost_inr"],
            gates.get("max_estimated_cost_inr"),
            "max",
        ),
    ]


def public_config(
    suite: Mapping[str, Any], include_sensitive_text: bool
) -> dict[str, Any]:
    config = {
        key: copy.deepcopy(value)
        for key, value in suite.items()
        if not key.startswith("_")
    }
    if include_sensitive_text:
        return config
    config["pipeline"]["llm"]["system_prompt"] = transcript_payload(
        config["pipeline"]["llm"]["system_prompt"], False
    )
    for case in config["cases"]:
        case["reference"] = transcript_payload(case["reference"], False)
        case["context"] = transcript_payload(case.get("context", ""), False)
        case["entities"] = [
            transcript_payload("|".join(entity_forms(entity)), False)
            for entity in case.get("entities", [])
        ]
    return config


def build_report(
    suite: Mapping[str, Any], results: Sequence[Mapping[str, Any]], mode: str
) -> dict[str, Any]:
    aggregates = grouped_aggregates(results)
    gates = evaluate_gates(aggregates, suite["gates"])
    include_sensitive_text = any(
        result.get("transcript") and not result["transcript"].get("redacted", True)
        for result in results
    )
    return {
        "schema_version": REPORT_SCHEMA,
        "created_at": utc_now(),
        "suite": suite["name"],
        "mode": mode,
        "config": public_config(suite, include_sensitive_text),
        "pricing": suite["pricing"],
        "aggregates": aggregates,
        "gates": gates,
        "gate_status": "failed"
        if any(gate["status"] == "failed" for gate in gates)
        else "passed",
        "results": list(results),
    }


def semantic_rows(
    suite: Mapping[str, Any], report: Mapping[str, Any]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    cases = {case["id"]: case for case in suite["cases"]}
    wer_rows, intent_rows = [], []
    for result in report["results"]:
        if result["status"] != "passed" or result["transcript"] is None:
            continue
        transcript = result["transcript"].get("text")
        if transcript is None:
            continue
        case = cases[result["case_id"]]
        audio_path = str(case_audio_path(suite, case))
        wer_rows.append(
            {
                "transcription": case["reference"],
                "prediction": transcript,
                "audio_filepath": audio_path,
                "language": case["language"],
                "case_id": case["id"],
            }
        )
        intent_rows.append(
            {
                "ground_truth": case["reference"],
                "asr_output": transcript,
                "audio_file": audio_path,
                "language": case["language"],
                "context": case.get("context", ""),
                "case_id": case["id"],
            }
        )
    return wer_rows, intent_rows


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    content = "".join(
        json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows
    )
    path.write_text(content, encoding="utf-8")


def format_value(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def document(title: str, body: str) -> str:
    safe_title = html.escape(title)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{safe_title}</title><style>
:root{{--ink:#171a21;--muted:#667085;--line:#d9dee8;--surface:#f6f8fb;--good:#087443;--bad:#b42318;--accent:#6d28d9}}
*{{box-sizing:border-box}}body{{font:14px/1.5 ui-sans-serif,system-ui,sans-serif;color:var(--ink);margin:0;background:#fff}}
main{{max-width:1180px;margin:auto;padding:40px 24px}}h1{{font-size:30px;margin:0 0 8px}}h2{{margin-top:36px}}
.muted{{color:var(--muted)}}.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin:24px 0}}
.card{{border:1px solid var(--line);border-radius:12px;padding:16px;background:var(--surface)}}.card b{{display:block;font-size:22px}}
table{{width:100%;border-collapse:collapse;margin:12px 0 24px}}th,td{{border-bottom:1px solid var(--line);padding:10px;text-align:left;vertical-align:top}}
th{{font-size:12px;text-transform:uppercase;color:var(--muted)}}.passed{{color:var(--good);font-weight:700}}.failed{{color:var(--bad);font-weight:700}}
code,pre{{font-family:ui-monospace,SFMono-Regular,monospace}}pre{{white-space:pre-wrap;background:var(--surface);padding:16px;border-radius:10px;overflow:auto}}
</style></head><body><main><h1>{safe_title}</h1>{body}</main></body></html>"""


def run_report_html(report: Mapping[str, Any]) -> str:
    summary = report["aggregates"]["suite"]
    cards = [
        ("Gate status", report["gate_status"]),
        ("Success rate", f"{summary['success_rate'] * 100:.1f}%"),
        ("Normalized WER", format_value(summary["quality"]["normalized_wer"]["mean"])),
        (
            "EOS → audio p95",
            f"{format_value(summary['latency_ms']['eos_to_first_audio']['p95'])} ms",
        ),
        ("Estimated cost", f"₹{summary['estimated_cost_inr']:.4f}"),
    ]
    cards_html = "".join(
        f'<div class="card"><span class="muted">{html.escape(label)}</span><b>{html.escape(value)}</b></div>'
        for label, value in cards
    )
    gates_html = "".join(
        "<tr>"
        f"<td>{html.escape(gate['name'])}</td>"
        f'<td class="{html.escape(gate["status"])}">{html.escape(gate["status"])}</td>'
        f"<td>{html.escape(format_value(gate['actual']))}</td>"
        f"<td>{html.escape(format_value(gate['threshold']))}</td>"
        f"<td>{html.escape(gate['direction'])}</td></tr>"
        for gate in report["gates"]
    )
    rows = []
    for result in report["results"]:
        quality = result.get("quality") or {}
        latency = result.get("latency_ms") or {}
        error = (result.get("error") or {}).get("message", "")
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(result['case_id']))}</td>"
            f"<td>{result['repetition']}</td>"
            f'<td class="{html.escape(result["status"])}">{html.escape(result["status"])}</td>'
            f"<td>{html.escape(format_value(quality.get('normalized_wer')))}</td>"
            f"<td>{html.escape(format_value(quality.get('configured_entity_recall')))}</td>"
            f"<td>{html.escape(format_value(latency.get('eos_to_first_audio')))}</td>"
            f"<td>{html.escape(error)}</td></tr>"
        )
    body = f"""
<p class="muted">{html.escape(report["suite"])} · {html.escape(report["mode"])} · {html.escape(report["created_at"])}</p>
<div class="cards">{cards_html}</div>
<h2>Quality gates</h2><table><thead><tr><th>Gate</th><th>Status</th><th>Actual</th><th>Threshold</th><th>Direction</th></tr></thead><tbody>{gates_html}</tbody></table>
<h2>Cases</h2><table><thead><tr><th>Case</th><th>Run</th><th>Status</th><th>WER</th><th>Entity recall</th><th>EOS → audio ms</th><th>Failure</th></tr></thead><tbody>{"".join(rows)}</tbody></table>
<h2>Configuration</h2><pre>{html.escape(json.dumps(report["config"], ensure_ascii=False, indent=2, sort_keys=True))}</pre>
"""
    return document("Sarvam voice regression report", body)


def flatten(value: Any, prefix: str = "") -> dict[str, Any]:
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key in sorted(value):
            result.update(
                flatten(value[key], f"{prefix}.{key}" if prefix else str(key))
            )
        return result
    if isinstance(value, list):
        return {prefix: value}
    return {prefix: value}


def config_diff(
    baseline: Mapping[str, Any], candidate: Mapping[str, Any]
) -> list[dict[str, Any]]:
    left, right = flatten(baseline), flatten(candidate)
    return [
        {"path": key, "baseline": left.get(key), "candidate": right.get(key)}
        for key in sorted(set(left) | set(right))
        if left.get(key) != right.get(key)
    ]


def load_report(path: Path) -> dict[str, Any]:
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValidationError(f"Report does not exist: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(f"Invalid JSON report {path}: {exc}") from exc
    if not isinstance(report, dict) or report.get("schema_version") != REPORT_SCHEMA:
        raise ValidationError(f"Expected {REPORT_SCHEMA} report: {path}")
    return report


def comparison_gate(
    name: str, delta: float | None, limit: float | None, unit: str
) -> dict[str, Any]:
    if limit is None:
        return {
            "name": name,
            "status": "skipped",
            "delta": delta,
            "limit": None,
            "unit": unit,
        }
    passed = delta is not None and delta <= limit
    return {
        "name": name,
        "status": "passed" if passed else "failed",
        "delta": round(delta, 6) if delta is not None else None,
        "limit": limit,
        "unit": unit,
    }


def build_comparison(
    baseline: Mapping[str, Any], candidate: Mapping[str, Any]
) -> dict[str, Any]:
    if baseline.get("mode") != candidate.get("mode"):
        raise ValidationError(
            "Baseline and candidate modes differ; do not compare mock latency with live latency."
        )
    left = baseline["aggregates"]["suite"]
    right = candidate["aggregates"]["suite"]
    thresholds = candidate["config"].get("regression", DEFAULTS["regression"])

    def metric(
        report: Mapping[str, Any], section: str, field: str, statistic: str
    ) -> float | None:
        return report[section][field][statistic]

    left_wer = metric(left, "quality", "normalized_wer", "mean")
    right_wer = metric(right, "quality", "normalized_wer", "mean")
    left_latency = metric(left, "latency_ms", "eos_to_first_audio", "p95")
    right_latency = metric(right, "latency_ms", "eos_to_first_audio", "p95")
    wer_delta = None if left_wer is None or right_wer is None else right_wer - left_wer
    latency_delta = (
        None
        if left_latency is None or right_latency is None
        else right_latency - left_latency
    )
    if left["estimated_cost_inr"] == 0:
        cost_percent = 0.0 if right["estimated_cost_inr"] == 0 else math.inf
    else:
        cost_percent = (
            (right["estimated_cost_inr"] - left["estimated_cost_inr"])
            / left["estimated_cost_inr"]
            * 100
        )
    success_drop = left["success_rate"] - right["success_rate"]
    gates = [
        comparison_gate(
            "normalized WER increase",
            wer_delta,
            thresholds.get("max_normalized_wer_increase"),
            "ratio",
        ),
        comparison_gate(
            "EOS to first audio p95 increase",
            latency_delta,
            thresholds.get("max_eos_to_first_audio_p95_increase_ms"),
            "ms",
        ),
        comparison_gate(
            "estimated cost increase",
            cost_percent,
            thresholds.get("max_cost_increase_percent"),
            "%",
        ),
        comparison_gate(
            "success-rate drop",
            success_drop,
            thresholds.get("max_success_rate_drop"),
            "ratio",
        ),
    ]
    baseline_cases = {
        (item["case_id"], item["repetition"]): item for item in baseline["results"]
    }
    candidate_cases = {
        (item["case_id"], item["repetition"]): item for item in candidate["results"]
    }
    case_rows = []
    for key in sorted(set(baseline_cases) | set(candidate_cases)):
        old, new = baseline_cases.get(key), candidate_cases.get(key)
        old_wer = (old.get("quality") or {}).get("normalized_wer") if old else None
        new_wer = (new.get("quality") or {}).get("normalized_wer") if new else None
        old_latency = (
            (old.get("latency_ms") or {}).get("eos_to_first_audio") if old else None
        )
        new_latency = (
            (new.get("latency_ms") or {}).get("eos_to_first_audio") if new else None
        )
        case_rows.append(
            {
                "case_id": key[0],
                "repetition": key[1],
                "baseline_status": old.get("status") if old else "missing",
                "candidate_status": new.get("status") if new else "missing",
                "normalized_wer_delta": None
                if old_wer is None or new_wer is None
                else round(new_wer - old_wer, 6),
                "eos_to_first_audio_delta_ms": None
                if old_latency is None or new_latency is None
                else round(new_latency - old_latency, 3),
            }
        )
    return {
        "schema_version": COMPARISON_SCHEMA,
        "created_at": utc_now(),
        "baseline": {
            "suite": baseline["suite"],
            "created_at": baseline["created_at"],
            "summary": left,
        },
        "candidate": {
            "suite": candidate["suite"],
            "created_at": candidate["created_at"],
            "summary": right,
        },
        "config_diff": config_diff(baseline["config"], candidate["config"]),
        "gates": gates,
        "gate_status": "failed"
        if any(gate["status"] == "failed" for gate in gates)
        else "passed",
        "cases": case_rows,
    }


def comparison_report_html(report: Mapping[str, Any]) -> str:
    cards = "".join(
        f'<div class="card"><span class="muted">{html.escape(label)}</span><b>{html.escape(value)}</b></div>'
        for label, value in [
            ("Regression status", report["gate_status"]),
            ("Baseline", report["baseline"]["suite"]),
            ("Candidate", report["candidate"]["suite"]),
            ("Configuration changes", str(len(report["config_diff"]))),
        ]
    )
    gates = "".join(
        f'<tr><td>{html.escape(gate["name"])}</td><td class="{html.escape(gate["status"])}">{html.escape(gate["status"])}</td>'
        f"<td>{html.escape(format_value(gate['delta']))}</td><td>{html.escape(format_value(gate['limit']))}</td><td>{html.escape(gate['unit'])}</td></tr>"
        for gate in report["gates"]
    )
    diffs = (
        "".join(
            f"<tr><td><code>{html.escape(diff['path'])}</code></td><td>{html.escape(format_value(diff['baseline']))}</td><td>{html.escape(format_value(diff['candidate']))}</td></tr>"
            for diff in report["config_diff"]
        )
        or '<tr><td colspan="3" class="muted">No configuration changes</td></tr>'
    )
    cases = "".join(
        f"<tr><td>{html.escape(row['case_id'])}</td><td>{row['repetition']}</td><td>{html.escape(row['baseline_status'])} → {html.escape(row['candidate_status'])}</td>"
        f"<td>{html.escape(format_value(row['normalized_wer_delta']))}</td><td>{html.escape(format_value(row['eos_to_first_audio_delta_ms']))}</td></tr>"
        for row in report["cases"]
    )
    body = f"""<p class="muted">Generated {html.escape(report["created_at"])}</p><div class="cards">{cards}</div>
<h2>Regression gates</h2><table><thead><tr><th>Gate</th><th>Status</th><th>Delta</th><th>Limit</th><th>Unit</th></tr></thead><tbody>{gates}</tbody></table>
<h2>Configuration differences</h2><table><thead><tr><th>Path</th><th>Baseline</th><th>Candidate</th></tr></thead><tbody>{diffs}</tbody></table>
<h2>Case differences</h2><table><thead><tr><th>Case</th><th>Run</th><th>Status</th><th>WER Δ</th><th>EOS → audio Δ ms</th></tr></thead><tbody>{cases}</tbody></table>"""
    return document("Sarvam voice comparison report", body)


def load_mock(path: Path) -> dict[str, Any]:
    try:
        mock = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValidationError(f"Mock fixture does not exist: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(f"Invalid mock fixture JSON: {exc}") from exc
    if not isinstance(mock, dict) or mock.get("schema_version") != MOCK_SCHEMA:
        raise ValidationError(f"Mock fixture must use schema_version {MOCK_SCHEMA}.")
    return mock


def command_plan(args: argparse.Namespace) -> int:
    path = Path(args.suite)
    suite = validate_suite(load_yaml(path), path)
    plan = build_plan(suite)
    print(json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True))
    return EXIT_OK


def command_run(args: argparse.Namespace) -> int:
    path = Path(args.suite)
    suite = validate_suite(load_yaml(path), path)
    if args.concurrency is not None:
        suite["execution"]["concurrency"] = require_int(
            args.concurrency, "--concurrency", minimum=1
        )
    if args.retries is not None:
        suite["execution"]["retries"] = require_int(
            args.retries, "--retries", minimum=0
        )
    plan = build_plan(suite)
    if not plan["within_budget"]:
        raise ValidationError(
            f"Projected cost ₹{plan['projected_cost']['total_inr']:.4f} exceeds budget "
            f"₹{plan['budget_inr']:.4f}; no network requests were made."
        )
    mock = load_mock(Path(args.mock_events)) if args.mock_events else None
    if mock is None and not os.getenv("SARVAM_API_KEY"):
        raise ValidationError(
            "Set SARVAM_API_KEY for a live run, or pass --mock-events for offline replay."
        )
    output_dir = Path(args.out)
    output_dir.mkdir(parents=True, exist_ok=True)
    results = asyncio.run(
        execute_runs(
            suite,
            output_dir,
            include_transcripts=args.include_transcripts,
            retain_audio=args.retain_audio,
            mock=mock,
        )
    )
    report = build_report(suite, results, "mock" if mock else "live")
    write_json(output_dir / "report.json", report)
    (output_dir / "report.html").write_text(run_report_html(report), encoding="utf-8")
    wer_rows, intent_rows = semantic_rows(suite, report)
    write_jsonl(output_dir / "llm-wer.jsonl", wer_rows)
    write_jsonl(output_dir / "llm-intent-entity.jsonl", intent_rows)
    print(
        json.dumps(
            {
                "report": str(output_dir / "report.json"),
                "gate_status": report["gate_status"],
            }
        )
    )
    if any(result["status"] == "failed" for result in results):
        return EXIT_LIVE_FAILURE
    return EXIT_REGRESSION if report["gate_status"] == "failed" else EXIT_OK


def command_compare(args: argparse.Namespace) -> int:
    baseline = load_report(Path(args.baseline))
    candidate = load_report(Path(args.candidate))
    comparison = build_comparison(baseline, candidate)
    output_dir = Path(args.out)
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "report.json", comparison)
    (output_dir / "report.html").write_text(
        comparison_report_html(comparison), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "report": str(output_dir / "report.json"),
                "gate_status": comparison["gate_status"],
            }
        )
    )
    return EXIT_REGRESSION if comparison["gate_status"] == "failed" else EXIT_OK


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        prog="voice_lab.py",
        description="Benchmark Sarvam voice-agent quality, latency, cost, and reliability.",
    )
    commands = root.add_subparsers(dest="command", required=True)
    plan = commands.add_parser(
        "plan", help="Validate a suite and project its maximum cost."
    )
    plan.add_argument("suite", help="Path to a versioned YAML suite.")
    plan.set_defaults(handler=command_plan)

    run = commands.add_parser(
        "run", help="Execute a live suite or replay mocked protocol events."
    )
    run.add_argument("suite", help="Path to a versioned YAML suite.")
    run.add_argument(
        "--out",
        required=True,
        help="Output directory for JSON, HTML, and JSONL reports.",
    )
    run.add_argument(
        "--concurrency", type=int, help="Override bounded concurrency (default: 1)."
    )
    run.add_argument("--retries", type=int, help="Override retry count (default: 0).")
    run.add_argument(
        "--include-transcripts",
        action="store_true",
        help="Include transcript and response text in reports and semantic exports.",
    )
    run.add_argument(
        "--retain-audio",
        action="store_true",
        help="Store synthesized audio under the output directory.",
    )
    run.add_argument(
        "--mock-events",
        help="Replay an offline protocol-event JSON fixture instead of calling APIs.",
    )
    run.set_defaults(handler=command_run)

    compare = commands.add_parser(
        "compare", help="Compare a candidate report against a baseline."
    )
    compare.add_argument("baseline", help="Baseline report.json.")
    compare.add_argument("candidate", help="Candidate report.json.")
    compare.add_argument(
        "--out", required=True, help="Output directory for comparison JSON and HTML."
    )
    compare.set_defaults(handler=command_compare)
    return root


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = parser().parse_args(argv)
        return int(args.handler(args))
    except ValidationError as error:
        print(f"error: {sanitize_error(error)}", file=sys.stderr)
        return EXIT_INVALID
    except (KeyError, TypeError, ValueError) as error:
        print(f"error: invalid input: {sanitize_error(error)}", file=sys.stderr)
        return EXIT_INVALID
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        return EXIT_INTERRUPTED
    except VoiceLabError as error:
        print(f"live run failed: {sanitize_error(error)}", file=sys.stderr)
        return EXIT_LIVE_FAILURE
    except Exception as error:  # pragma: no cover - defensive stable CLI boundary
        print(f"live run failed: {sanitize_error(error)}", file=sys.stderr)
        return EXIT_LIVE_FAILURE


if __name__ == "__main__":
    raise SystemExit(main())
