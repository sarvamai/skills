#!/usr/bin/env python3
"""Batch-translate a game string table, with placeholder verification.

    python3 localize_table.py table.json --lang hi-IN ta-IN --dry-run
    python3 localize_table.py table.json --lang hi-IN --model mayura:v1 \
        --mode modern-colloquial --out out/

--dry-run needs no API key and no network: it reports chunk counts, placeholder
problems and keys that will need human review, which is the check worth running
before you spend money on four hundred lines.

Design notes that matter:
  * A key is never translated, only its value. Keys join the table, the audio
    filenames and the engine references.
  * Placeholders are verified after the call, not trusted to survive it.
  * Over-limit text is split at sentence boundaries; over-limit returns 422.
  * Every result is cached on a hash of the text and every parameter, so a
    re-run after a one-line edit bills one line.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

PLACEHOLDER_RE = re.compile(r"(\{[^{}]*\}|%[0-9]*\.?[0-9]*[sdif]|<[^<>\n]+>|\$\{[^{}]*\})")
SENTENCE_RE = re.compile(r"(?<=[.!?।॥])\s+")

LIMITS = {"mayura:v1": 1000, "sarvam-translate:v1": 2000}
SAFETY = 0.95  # headroom for tokenisation drift
MAX_CHUNKS_BEFORE_FLAG = 3


# --------------------------------------------------------------------------- table

def load_table(path):
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    table = {}
    for key, value in raw.items():
        if isinstance(value, str):
            table[key] = {"text": value, "speaker": None, "context": None, "skip": False}
        elif isinstance(value, dict) and "text" in value:
            table[key] = {
                "text": value["text"],
                "speaker": value.get("speaker"),
                "context": value.get("context"),
                "skip": bool(value.get("skip", False)),
            }
        else:
            raise SystemExit(f"key {key!r}: value must be a string or an object with 'text'")
    return table


def placeholders(text):
    return sorted(PLACEHOLDER_RE.findall(text))


# ------------------------------------------------------------------------ chunking

def chunk(text, limit):
    """Pack sentences under the limit; never split a sentence holding a placeholder."""
    budget = int(limit * SAFETY)
    if len(text) <= budget:
        return [text]

    chunks, current = [], ""
    for sentence in SENTENCE_RE.split(text):
        if len(sentence) > budget:
            # A single oversized sentence: clause split, then word split.
            for piece in re.split(r"(?<=[,;—])\s+", sentence):
                while len(piece) > budget:
                    cut = piece.rfind(" ", 0, budget)
                    cut = cut if cut > 0 else budget
                    if current:
                        chunks.append(current)
                        current = ""
                    chunks.append(piece[:cut].strip())
                    piece = piece[cut:].strip()
                if current and len(current) + len(piece) + 1 > budget:
                    chunks.append(current)
                    current = ""
                current = f"{current} {piece}".strip()
            continue
        if current and len(current) + len(sentence) + 1 > budget:
            chunks.append(current)
            current = ""
        current = f"{current} {sentence}".strip()
    if current:
        chunks.append(current)
    return chunks


# ------------------------------------------------------------------------ translate

def cache_key(text, source, target, model, extra):
    blob = json.dumps([text, source, target, model, extra], sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def translate_one(client, entry, target, args):
    """Translate a single entry. Returns (text, [reasons needing review])."""
    reasons = []
    source_text = entry["text"]
    chunks = chunk(source_text, LIMITS[args.model])

    if len(chunks) > MAX_CHUNKS_BEFORE_FLAG:
        reasons.append(f"split across {len(chunks)} chunks; register drift likely")

    pieces = []
    for piece in chunks:
        ck = cache_key(piece, args.source, target, args.model, args.extra)
        if ck in args.cache:
            pieces.append(args.cache[ck])
            continue
        out = None
        for attempt in (1, 2):
            try:
                response = client.text.translate(
                    input=piece,
                    source_language_code=args.source,
                    target_language_code=target,
                    model=args.model,
                    **args.extra,
                )
                out = response.translated_text
            except Exception as exc:  # noqa: BLE001 - retry once, then flag
                if attempt == 2:
                    reasons.append(f"request failed: {exc}")
                    out = None
                continue
            if placeholders(piece) == placeholders(out):
                break
            if attempt == 2:
                reasons.append(f"placeholder mismatch in {piece!r}")
                out = None
        if out is None:
            return source_text, reasons or ["translation failed; source kept"]
        args.cache[ck] = out
        pieces.append(out)

    translated = " ".join(pieces)
    if placeholders(source_text) != placeholders(translated):
        reasons.append("placeholder mismatch after rejoin")
    return translated, reasons


def validate_args(args):
    """Fail fast on the combinations that the API rejects anyway."""
    if "or-IN" in args.lang:
        raise SystemExit("Odia is 'od-IN', not 'or-IN'")
    if args.model == "sarvam-translate:v1":
        if args.output_script:
            raise SystemExit(
                "output_script is mayura:v1 only — sarvam-translate:v1 returns 400. "
                "Switch --model mayura:v1 or drop --output-script."
            )
        if args.mode and args.mode != "formal":
            raise SystemExit(f"mode={args.mode!r} is mayura:v1 only; sarvam-translate:v1 is 'formal'")
        if args.source == "auto":
            raise SystemExit("source_language_code='auto' is mayura:v1 only")
    if args.model == "mayura:v1" and args.mode and args.mode not in {
        "formal", "modern-colloquial", "classic-colloquial", "code-mixed"
    }:
        raise SystemExit(f"unknown mode {args.mode!r}")


# ----------------------------------------------------------------------------- main

def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("table")
    parser.add_argument("--lang", nargs="+", required=True)
    parser.add_argument("--source", default="en-IN")
    parser.add_argument("--model", default="mayura:v1", choices=sorted(LIMITS))
    parser.add_argument("--mode")
    parser.add_argument("--output-script")
    parser.add_argument("--speaker-gender", choices=["male", "female"])
    parser.add_argument("--out", default="localized")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--fail-on-review",
        action="store_true",
        help="exit 1 if any key needs human review, so CI can gate on it",
    )
    args = parser.parse_args()

    extra = {}
    if args.mode:
        extra["mode"] = args.mode
    if args.output_script:
        extra["output_script"] = args.output_script
    if args.speaker_gender:
        extra["speaker_gender"] = args.speaker_gender
    args.extra = extra
    validate_args(args)

    table = load_table(args.table)
    active = {k: v for k, v in table.items() if not v["skip"]}

    if args.dry_run:
        total_chars = sum(len(v["text"]) for v in active.values())
        oversized = [k for k, v in active.items() if len(chunk(v["text"], LIMITS[args.model])) > 1]
        with_ph = [k for k, v in active.items() if placeholders(v["text"])]
        print(f"table        : {args.table}")
        print(f"keys         : {len(table)} ({len(active)} active, {len(table) - len(active)} skipped)")
        print(f"characters   : {total_chars:,}")
        print(f"model        : {args.model} (limit {LIMITS[args.model]:,}/request)")
        print(f"languages    : {', '.join(args.lang)}")
        print(f"requests     : ~{len(active) * len(args.lang)} before chunking, "
              f"~{sum(len(chunk(v['text'], LIMITS[args.model])) for v in active.values()) * len(args.lang)} after")
        print(f"over limit   : {len(oversized)} key(s) will be chunked"
              + (f" -> {', '.join(oversized[:5])}" if oversized else ""))
        print(f"placeholders : {len(with_ph)} key(s) carry tokens and will be verified"
              + (f" -> {', '.join(with_ph[:5])}" if with_ph else ""))
        return 0

    try:
        from sarvamai import SarvamAI
    except ImportError:
        raise SystemExit("pip install 'sarvamai>=0.1.29'")

    client = SarvamAI()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    cache_path = out_dir / ".cache.json"
    args.cache = json.loads(cache_path.read_text()) if cache_path.is_file() else {}

    flagged = 0
    for target in args.lang:
        results, review = {}, []
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = {pool.submit(translate_one, client, v, target, args): k for k, v in active.items()}
            for future, key in futures.items():
                text, reasons = future.result()
                results[key] = text
                if reasons:
                    review.append({"key": key, "reasons": reasons})
                print(f"  {'!' if reasons else '.'} {key}", file=sys.stderr)

        for key, value in table.items():
            if value["skip"]:
                results.setdefault(key, value["text"])

        (out_dir / f"{target}.json").write_text(
            json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (out_dir / f"review.{target}.json").write_text(
            json.dumps(
                {"language": target, "total": len(results),
                 "needs_review": review}, ensure_ascii=False, indent=2
            ),
            encoding="utf-8",
        )
        flagged += len(review)
        print(f"{target}: {len(results) - len(review)}/{len(results)} verified, "
              f"{len(review)} need review -> {out_dir}/review.{target}.json")

    cache_path.write_text(json.dumps(args.cache, ensure_ascii=False), encoding="utf-8")
    if args.fail_on_review and flagged:
        print(f"{flagged} key(s) need review; failing because --fail-on-review is set", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
