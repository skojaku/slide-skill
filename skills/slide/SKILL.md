---
name: slide
description: Build or review a Marp slide deck for a lecture, technical talk, or workshop. Use when the user asks to create, update, or fix a slide deck, or to review, check, or QA one.
---

# Slide

One skill, two modes, sharing the same bundled infra (`theme.css`, `gatelib/`,
`template/`) at `~/.claude/skills/slide/` — a deck needs no external repo either way.

## Mode

- **Build** — user says create/write/add/update/fix a deck (or a deck doesn't exist yet).
  Read `DECK_BUILD_GUIDE.md` and `FIGURE_GUIDE.md`.
- **Review** — user says review/check/QA/audit a deck (or asks "is this deck good").
  Read `REVIEW_PLAYBOOK.md` and `SLIDE_RUBRIC.md`.
- Both — a build session always ends in the tiered review loop; read all four guides.
- Ambiguous ("work on this deck")? Ask which mode, don't guess.

## Which deck directory

If the user names a path, use it. Otherwise: if the current working directory already
looks like a deck directory (a `.md` file with `marp: true` front matter), use it.
Otherwise ask which directory, or offer to scaffold a new one from
`~/.claude/skills/slide/template/` — see `DECK_BUILD_GUIDE.md`'s "Deck directory" section.

## Automated pipeline

All checks run through `deckgate` (the gatelib CLI), bundled at `gatelib/`. Run it from
the skill directory, passing the deck's directory (absolute or relative — it does not
need to live under `~/.claude/skills/`):

```sh
cd ~/.claude/skills/slide

python3 -m gatelib review <deck_dir>      # full pipeline: fix → render → check → prepare
python3 -m gatelib check <deck_dir>       # all checks (source + render)
python3 -m gatelib fix <deck_dir>         # auto-fix mechanical issues
python3 -m gatelib fix <deck_dir> --dry-run  # preview fixes
python3 -m gatelib prepare <deck_dir> --changed-only  # downscaled review images
python3 -m gatelib render <deck_dir>      # render + check
```

`deckgate review` runs the full Tier 0 pipeline: auto-fix → marp render → source checks →
render checks → prepare downscaled review images. Exit code 0 = all pass. What it catches
automatically vs. what needs LLM judgment (Tier 1/2) is tabulated in `DECK_BUILD_GUIDE.md`
and detailed in `REVIEW_PLAYBOOK.md`.

If `python3 -m gatelib ...` fails with `ModuleNotFoundError: No module named 'numpy'` (or
`PIL`), your active `python3` is a virtualenv without them — call an interpreter that has
`numpy`+`Pillow` installed explicitly (e.g. `/opt/homebrew/bin/python3` on a Homebrew Mac).

## Review agent model

- Anthropic models → use `sonnet` for the review subagent
- Non-Anthropic models → use `grok-4.5` for the review subagent

## Agent architecture and checkpointing

See "Roles" / "Token-efficient agent architecture" in `REVIEW_PLAYBOOK.md` and step 6
("Commit every gate pass") in `DECK_BUILD_GUIDE.md`'s "Order of work" — same protocol
for both modes: lead agent reads guides once, cheap agents apply fixes, `review/CHECKPOINT.md`
tracks round state for session resume.
