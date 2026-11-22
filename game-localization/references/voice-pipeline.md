# Voice pipeline

## Model choice

`bulbul:v4-flash` for everything except Malayalam (`ml-IN`) and Odia (`od-IN`), which have no v4 personas — use `bulbul:v3` with a v3 short name there.

Always pass `model` explicitly. Omitting it selects `bulbul:v3`, and the v4 persona IDs then fail with a 400 that reads like a bad speaker name rather than a missing model.

## Persona ID shape

`voice_language_style`, e.g. `aparna_hi_customer`.

- First token: the voice.
- Middle token: language tag (`hi`, `en`, `bn`, `gu`, `kn`, `mr`, `pa`, `ta`, `te`) or `enhi` for English–Hindi code-mix.
- Last token: style or use case.

Use an `_enhi_` persona only when a single utterance is genuinely mixed. A few English loanwords inside Hindi script do not need it — pick the Hindi persona and let the text carry the code-mixing.

Two rules that account for most failures:

- **Never omit `speaker`.** The default is `shubh_enhi_ads`, a code-mixed ad read.
- **Never hardcode an ID from memory.** Sarvam renamed the roster on 2026-10-06 and the old IDs now return 400. Fetch the live list, write it to `personas.json`, and validate against that file on every build. An unknown speaker returns 400 with the full list attached, so one deliberate probe against a throwaway key refreshes it.

The full catalog lives in `llms.txt`, not here — it changes too often to duplicate.

## Per-NPC consistency

```json
{
  "elder_mira":    { "persona": "aparna_hi_customer", "gender": "female" },
  "quartermaster": { "persona": "shubh_hi_customer",  "gender": "male" }
}
```

One persona per NPC per language. Do not vary pitch or pace per line to add emotion: out-of-range values return 400, and small in-range changes make a character sound unstable across a conversation rather than expressive. If an NPC needs a different register, that is a second explicit entry in the map.

Match `speaker_gender` in translation to the persona's gender. A female persona reading a line translated with masculine first-person agreement is the most audible localization bug in Indian-language games.

## Naming and caching

One file per key: `audio/<language>/<key>.wav`. The key is the join to the table, so the filename must be the key, not an index.

Cache on a hash of `(text, speaker, model, language_code, output_audio_codec, pitch, pace, loudness)`. A re-run after editing three lines should make three requests and leave the other four hundred files untouched.

## Engine import

Engine-side, not Sarvam-side, but this is where these pipelines usually fail.

**Godot** — WAVs under `res://audio/<language>/`, looping off, referenced by `AudioStreamPlayer`. Keep the folder name equal to the BCP-47 code so a language switch is a path swap.

**Unity** — WAVs become `AudioClip`. One Addressables group per language so a language pack is a download rather than a rebuild. Decompress On Load for barks, Streaming for narration.

**Unreal** — import as `Sound Wave`; add a `Sound Cue` per line only if you need attenuation or randomisation.

Check one file per language by ear before generating four hundred. A wrong persona is cheap at line one and expensive at line four hundred.
