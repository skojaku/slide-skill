# gatelib — slide deck QA pipeline

Single CLI entry point (`deckgate`) for all automated slide checks, fixes, and
review image preparation for any Marp deck. Replaces per-deck copy-and-edit scripts.

## Quick start

Run from this directory (`~/.claude/skills/slide/`), passing an absolute or
relative path to your deck's directory — it does not need to live under this repo:

```sh
cd ~/.claude/skills/slide

# Full pipeline: auto-fix → render → check → prepare review images
python3 -m gatelib review /path/to/my-deck

# Individual commands
python3 -m gatelib check /path/to/my-deck              # all checks
python3 -m gatelib check-deck /path/to/my-deck         # source-level only
python3 -m gatelib check-render /path/to/my-deck       # pixel-level only
python3 -m gatelib fix /path/to/my-deck                # auto-fix mechanical issues
python3 -m gatelib fix /path/to/my-deck --dry-run      # preview fixes
python3 -m gatelib prepare /path/to/my-deck --changed-only  # downscaled review images
python3 -m gatelib render /path/to/my-deck             # render + check
```

## What it automates

| Check | Auto-fix | Command |
|-------|----------|---------|
| Fragment syntax mixing | ✅ | `fix` |
| KaTeX in HTML blocks | ✅ | `fix` |
| Demo links in speaker notes | ✅ | `fix` |
| Trailing whitespace | ✅ | `fix` |
| Node disc sizes (opt-in, network/graph diagrams) | ❌ | `check-render` |
| Text size (x-height) | ❌ | `check-render` |
| Content overflow | ❌ | `check-render` |
| Container mismatch | ❌ | `check-render` |
| Figure reuse w/ diff captions | ❌ | `check-deck` |
| Answer leak (text) | ❌ | `check-deck` |
| Bold overuse | ❌ | `check-deck` |
| Stale render | ❌ | `check-deck` |
| Em dashes | ❌ | `check-render` |
| Caption colours | ❌ | `check-render` |

## Architecture

```
gatelib/
  __main__.py       # python3 -m gatelib entry
  cli.py            # CLI argument parsing + subcommands
  check_deck.py     # source-level checks (markdown)
  check_render.py   # pixel-level checks (rendered PNGs)
  fix_deck.py       # auto-fixers for mechanical issues
  review_images.py  # downscale/contact-sheet for LLM review
```

Each deck keeps a thin `check_render.py` wrapper that carries only its own
constants (deck filename, FIG_H modifiers, exempt figures, and — only if the
deck draws circular node-link diagrams — a NODE_FILLS palette). All logic
lives in gatelib. See `../template/check_render.py` for a starting point.

## Render hash change detection

`check-deck` saves SHA-256 hashes of rendered slide PNGs to
`review/.render_hashes.json`. Changed slides are the Tier 1 LLM review scope.
A figure edit propagates to every slide that uses it — the hash catches this.

## Token-efficient review images

`prepare` downscales 1280x720 slides to 640x360 (~307 tokens each vs ~1,229).
With `--changed-only`, only changed slides are prepared. Typical savings:
75% per slide, 95% when combined with changed-only filtering.

## Why a shared library, not per-deck copies

This started as a per-deck copy-and-edit script. Checks written for one deck
(`caption_colours`, `em_dashes`, a border-flood-fill helper) were silently lost
whenever the next deck copied an older version instead of the latest one.
Centralizing in gatelib means a check fixed once is fixed for every deck.

## Adding a new check

Add it to `check_render.py` or `check_deck.py` in gatelib. Every deck
inherits it on the next run. No per-deck copies to update.
