# Slide Math Skill

A Claude Code skill for building and reviewing English [Marp](https://marp.app/) slide decks
in the slide-math style: dense, annotated math slides that read as a handout.

- Black-bar titles with a one-sentence lead
- Formulas in boxes with black tab labels, lavender highlights
- Boxes split into 2-3 columns, code with its output
- TikZ figures (dot plots, flow diagrams, number lines, data curves) with pins and leader lines

Bundled: Marp theme (`theme/`), component set (`COMPONENTS.md`), figure kit (`figkit/`),
checker (`tools/check.py`), fonts (`fonts/`), deck template (`template/`) and a gallery
(`gallery/`). A deck needs nothing else.

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

Copy `skills/slide-math/` to `~/.claude/skills/slide-math/`.

See `skills/slide-math/SKILL.md` for the full guide.

## Fonts

Source Sans 3, Source Serif 4 and Source Code Pro, each under the SIL Open Font License
(license files in `skills/slide-math/fonts/`).

## License

MIT
