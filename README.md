# Slide Skill

A Claude Code skill for building and reviewing English [Marp](https://marp.app/) slide decks
in one style: dense, annotated math slides that read as a handout.

- Black-bar titles with a one-sentence lead
- Formulas in boxes with black tab labels, lavender highlights
- Boxes split into 2-3 columns, code with its output
- TikZ figures (dot plots, flow diagrams, number lines, data curves) with pins and leader lines

Bundled: Marp theme (`theme/`), component set (`COMPONENTS.md`), figure kit (`figkit/`),
checker (`tools/check.py`), fonts (`fonts/`), deck template (`template/`) and a gallery
(`gallery/`).

## Sample

[Embedding lecture deck](https://skojaku.github.io/slide-skill/samples/m08-embedding/)

## Installation

### Using `npx skills`

```bash
npx skills add skojaku/slide-skill --all
# or
npx skills add skojaku/slide-skill -a claude-code
```

### Manual install

Copy `skills/slide/` to `~/.claude/skills/slide/`.

See `skills/slide/SKILL.md` for the full guide.

## Requirements

`marp` (marp-cli 4), Chrome or Chromium, `python3` with Pillow, `xelatex` with `pgfplots`,
`standalone` and `fontspec`, and `pdftocairo`. Rendering needs a network connection (KaTeX
fonts load from a CDN). Details: `skills/slide/SKILL.md`.

## Fonts

Source Sans 3, Source Serif 4 and Source Code Pro, each under the SIL Open Font License
(license files in `skills/slide/fonts/`).
