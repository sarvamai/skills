# Contributing to Sarvam AI Skills

Thanks for your interest in contributing! Skills are lean **correction layers** — they contain only what AI agents get wrong when generating Sarvam AI code or driving Sarvam tools. Full parameter tables, voice catalogs, and rate limits belong in [llms.txt](https://docs.sarvam.ai/llms.txt), not in skills.

## What belongs in a skill

- **SDK call signatures** that differ from conventions (e.g., no `.create()` on chat)
- **Parameters that silently fail** (e.g., `output_script` ignored on sarvam-translate)
- **Parameters that error** (e.g., `pitch`/`loudness` returns 400 on Bulbul v3)
- **Non-trivial SDK patterns** (e.g., Batch API job chain, WebSocket async connect)
- **Gotchas verified against the live API** — not assumed from training data

## What does NOT belong

- Full parameter tables (route to llms.txt)
- Voice catalogs, language code lists (route to llms.txt)
- Rate limit numbers (route to llms.txt)
- General LLM best practices (belongs in `vibe-coding`)

## Skill structure

Every skill is a directory with a `SKILL.md` file:

```
skill-name/
  SKILL.md          ← core skill content
  references/       ← (optional) deeper reference docs, loaded on demand
```

### Required frontmatter

```yaml
---
name: skill-name
description: >-
  One-paragraph description for agent routing — what the skill covers
  and when to use it (and, if relevant, when NOT to — see sarvam-mcp
  and vibe-coding for examples of routing agents away from the wrong skill).
license: Apache-2.0
metadata:
  author: your-name
  version: "X.Y"
---
```

### Body structure — depends on the skill's shape

There isn't one fixed section template. Match the shape of the skill you're adding to or creating:

- **SDK skills** (`chat`, `speech-to-text`, `text-to-speech`, `translate/text`, `translate/document`, `voice-agents`) — document API call signatures: **Quick Start (Python)**, **Quick Start (JavaScript/TypeScript)**, then **Gotchas**, then **Full Docs** links.
- **Tool-routing skills** (`sarvam-mcp`) — document decision procedure, not code: which tool to call for which task, defaults, auth flow, worked examples, then **Gotchas**.
- **Vendor-neutral skills** (`vibe-coding`) — no SDK signatures at all; document habits/practices, then **Gotchas**.

Every skill, regardless of shape, ends with a **Gotchas** table — that's the one universal section, and it's the highest-value part of the file for an agent.

## Conventions

- **Additive-only PRs preferred.** Don't reword existing content — add rows to the Gotchas table or add snippets, unless you're fixing something factually wrong.
- **Bump the version** in frontmatter on every change (`metadata.version`).
- **Verify gotchas against the live API** before opening a PR. Include what you verified in the PR description.
- **Both Python and JS/TS snippets** are expected for SDK skills. `sarvam-mcp` and `vibe-coding` don't have SDK signatures, so this doesn't apply to them.
- **Vendor-neutral habits** go in `vibe-coding`. Sarvam-specific API signatures go in the relevant product skill. Sarvam-specific *tool-calling* (not raw HTTP/SDK) goes in `sarvam-mcp`.

## How to contribute

1. Fork this repo.
2. Create a branch: `git checkout -b skill-name/your-change`
3. Make your change (additive only, unless fixing a factual error).
4. Verify against the live API if you're adding or changing a gotcha.
5. Commit with a clear message: `skill: what you changed`
6. Open a PR. In the description, explain what gap you found and how you verified the fix.

## Issues

Issues are restricted to maintainers. If you find a gap, open a PR directly — or start a Discussion if you want to propose a new skill before building it.

## License

By contributing, you agree your contributions are licensed under Apache-2.0.
