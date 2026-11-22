#!/usr/bin/env python3
"""Generate NPC voice lines for a localized string table.

    python3 voice_lines.py out/hi-IN.json --lang hi-IN \
        --voice-map voices.json --personas personas.json --dry-run
    python3 voice_lines.py out/hi-IN.json --lang hi-IN --voice-map voices.json \
        --out audio/hi-IN

--dry-run needs no API key: it validates personas against the pinned roster,
catches the v4/v3 traps, and counts the requests you are about to make.

voices.json maps an NPC to a persona:

    {"elder_mira": {"persona": "aparna_hi_customer", "gender": "female"}}

The roster is not stable — Sarvam renamed voices on 2026-10-06 and the old IDs
now return 400. Pin it in personas.json and validate against that, not memory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

PERSONA_RE = re.compile(r"^[a-z]+_(?:hi|en|bn|gu|kn|mr|pa|ta|te|enhi)_[a-z]+$")
V3_SHORT_NAMES = {"shubh", "priya", "ishita", "anushka", "kavya", "roopa", "abhilash", "karun", "hitesh"}
NO_V4_PERSONA = {"ml-IN", "od-IN"}


def cache_key(text, speaker, model, language, extra):
    blob = json.dumps([text, speaker, model, language, extra], sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def load_json(path, default=None):
    if not path:
        return default
    p = Path(path)
    if not p.is_file():
        return default
    return json.loads(p.read_text(encoding="utf-8"))


def validate(args, lines, voices, roster):
    """Everything that would cost a 400, caught before the first request."""
    problems = []

    if args.model == "bulbul:v4-flash":
        if args.lang in NO_V4_PERSONA:
            problems.append(
                f"{args.lang} has no v4 personas — use --model bulbul:v3 with a v3 short name"
            )
        for npc, cfg in voices.items():
            persona = cfg.get("persona", "")
            if persona in V3_SHORT_NAMES:
                problems.append(f"{npc}: {persona!r} is a v3 short name and 400s on bulbul:v4-flash")
            elif roster and persona not in roster:
                problems.append(f"{npc}: {persona!r} not in the pinned roster")
            elif not PERSONA_RE.match(persona):
                problems.append(f"{npc}: {persona!r} is not shaped voice_language_style")

    missing = sorted({v["speaker"] for v in lines.values() if v.get("speaker")} - set(voices))
    if missing:
        problems.append(f"speakers with no voice mapped: {', '.join(missing)}")

    empty = [k for k, v in lines.items() if not str(v.get("text", "")).strip()]
    if empty:
        problems.append(f"{len(empty)} empty line(s): {', '.join(empty[:5])}")

    return problems


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("table", help="localized table, one language")
    parser.add_argument("--lang", required=True)
    parser.add_argument("--voice-map", required=True)
    parser.add_argument("--personas", help="pinned roster, JSON list of speaker ids")
    parser.add_argument("--model", default="bulbul:v4-flash")
    parser.add_argument("--codec", default="wav")
    parser.add_argument("--out", default="audio")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.lang == "or-IN":
        raise SystemExit("Odia is 'od-IN', not 'or-IN'")

    raw = load_json(args.table, {})
    lines = {k: (v if isinstance(v, dict) else {"text": v}) for k, v in raw.items()}
    voices = load_json(args.voice_map, {})
    roster = set(load_json(args.personas, []) or [])

    problems = validate(args, lines, voices, roster)
    calls = len(lines)

    print(f"table     : {args.table}")
    print(f"language  : {args.lang}")
    print(f"model     : {args.model}")
    print(f"lines     : {calls}")
    print(f"characters: {sum(len(str(v.get('text', ''))) for v in lines.values()):,}")
    print(f"npcs      : {len(voices)} mapped")
    if roster:
        print(f"roster    : {len(roster)} pinned persona(s)")

    if problems:
        print("\nBLOCKING:")
        for problem in problems:
            print(f"  ! {problem}")

    if args.dry_run:
        print(f"\ndry run: would make {calls} request(s), one WAV each -> {args.out}/{args.lang}/")
        return 1 if problems else 0

    if problems:
        raise SystemExit("refusing to spend requests on a broken voice map")

    try:
        from sarvamai import SarvamAI
        from sarvamai.play import save
    except ImportError:
        raise SystemExit("pip install 'sarvamai>=0.1.29'")

    client = SarvamAI()
    out_dir = Path(args.out) / args.lang
    out_dir.mkdir(parents=True, exist_ok=True)
    cache_path = out_dir / ".cache.json"
    cache = load_json(cache_path, {}) or {}

    def render(key, entry):
        npc = entry.get("speaker") or next(iter(voices), None)
        cfg = voices.get(npc, {})
        speaker = cfg.get("persona")
        text = str(entry.get("text", "")).strip()
        extra = {k: cfg[k] for k in ("pitch", "pace", "loudness") if k in cfg}
        ck = cache_key(text, speaker, args.model, args.lang, extra)
        target = out_dir / f"{key}.{args.codec}"
        if ck in cache and target.is_file():
            return key, "cached"
        response = client.text_to_speech.convert(
            text=text,
            language_code=args.lang,
            model=args.model,
            speaker=speaker,
            output_audio_codec=args.codec,
            **extra,
        )
        save(response, str(target))
        cache[ck] = target.name
        return key, "written"

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(render, k, v) for k, v in lines.items()]
        for future in futures:
            key, status = future.result()
            print(f"  {key}: {status}", file=sys.stderr)

    cache_path.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    print(f"done: {len(lines)} line(s) -> {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
