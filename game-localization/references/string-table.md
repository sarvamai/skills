# String tables

## Schema

```json
{
  "<key>": "<text>"
}
```

or, with metadata:

```json
{
  "<key>": {
    "text": "<text>",
    "context": "<who says it, to whom, in what mood>",
    "speaker": "<npc_id>",
    "skip": false
  }
}
```

Reserved keys: `speaker`, `context`, `skip`, `text`.

Only `text` is ever transmitted. `context` and `speaker` stay local — they exist for the human reviewer and for grouping, so put the spoiler or the internal note in `context`, never in `text`. Anything else is ignored so a table can carry engine-specific fields without breaking the loader.

Keys must be stable, unique and filesystem-safe if you also generate audio: `q_ashfields_intro_01` works, `Quest #12 (intro)` does not.

## Placeholder classes

| Class | Example | Notes |
|-------|---------|-------|
| Brace | `{player_class}`, `{0}` | Unity `string.Format`, Godot `format()` |
| Percent | `%s`, `%d`, `%.1f` | C-style, `printf`-family |
| Markup | `<color=#C8A24A>`, `[b]`, `[/i]` | Unity rich text, Godot BBCode |
| Template | `${gold}`, `$PLAYER` | custom engines |

## The placeholder policy

1. Extract every token from the source line, in order.
2. Send the line to the model with tokens untouched.
3. Extract tokens from the returned line.
4. Compare multisets. Any missing, extra or renamed token is a failure.
5. Retry once. Still failing → write the source string to the output and list the key in `review.json`.

Do not translate token-by-token and reassemble around the placeholders. It guarantees token survival and destroys the grammar, which for an SOV language like Hindi is worse than a flagged key.

Do not invent sentinels like `⟦0⟧` and hope the model preserves them. It is the same gamble with an extra step and a worse failure mode.

## Chunking

Limits are per request: 2,000 characters for `sarvam-translate:v1`, 1,000 for `mayura:v1`. Over-limit is a 422.

Algorithm:

1. Split on sentence boundaries — `.`, `!`, `?`, `।`, `॥`.
2. Greedily pack sentences into chunks under the limit, minus a safety margin of 5% for tokenisation drift.
3. If a single sentence exceeds the limit, split on clause boundaries (`,`, `;`, `—`), and only then on word boundaries.
4. Never split a sentence that contains a placeholder — carry the whole sentence into the next chunk instead.
5. Translate chunks independently and rejoin with a single space.

Rejoining is where meaning leaks. For anything longer than three chunks, flag the key: a 3,000-character codex entry translated in four independent pieces will drift in register and pronoun, and no amount of post-processing fixes that. Prefer a human translator for codex-scale text.

## Review file

`review.json` is the deliverable, not an afterthought:

```json
{
  "language": "hi-IN",
  "total": 412,
  "translated": 398,
  "needs_review": [
    { "key": "q_ashfields_intro_01", "reason": "placeholder lost: {player_class}" },
    { "key": "lore_ashfall_03", "reason": "split across 4 chunks; register drift likely" }
  ]
}
```

A pipeline that reports `412/412 translated` is lying unless it also reports how many it verified.

## Skipping

Ship a skip list rather than a heuristic. Typical entries: item IDs, debug strings, `ALL_CAPS` constants, anything already in the target script, and proper nouns the writer wants left alone. Heuristics on `ALL_CAPS` are fine as a default, but the list must be able to override them.
