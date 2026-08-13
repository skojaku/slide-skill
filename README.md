# Slide Skill

A Claude Code skill for building and reviewing [Marp](https://marp.app/) slide decks —
lectures, technical talks, workshops. One skill, two modes:

- **Build** — write or fix a deck: `DECK_BUILD_GUIDE.md` (structure, pacing, deck
  directory layout) and `FIGURE_GUIDE.md` (drawing figures that pass the gate).
- **Review** — run the tiered review loop: `REVIEW_PLAYBOOK.md` (the review → fix →
  re-verify process) and `SLIDE_RUBRIC.md` (what "good" means, criteria P1/F1/F4/N1–N4/S1–S5).

Both modes share one bundled QA pipeline (`gatelib/`, a CLI called `deckgate`) and a
default theme (`theme.css`), so a deck needs no external repo to build or review against.
Automated checks (`deckgate check`) catch layout, overflow, KaTeX, and figure-consistency
issues for free; LLM review is reserved for narrative and figure-choice judgment calls
the pipeline can't measure.

## Installation

### Using `npx skills` (works across agents)

[`npx skills`](https://github.com/vercel-labs/skills) is a package manager for AI agent skills.

```bash
npx skills add skojaku/slide-skill --all
# or
npx skills add skojaku/slide-skill -a claude-code
```

### Manual install

**Claude Code:** Copy `skills/slide/` to `~/.claude/skills/slide/`.

**Codex / Cursor / other agents:** Copy the contents of `skills/slide/SKILL.md` into your
`AGENTS.md` or system prompt, and keep the bundled files (`gatelib/`, `template/`,
`theme.css`, the guide docs) alongside it.

See `skills/slide/SKILL.md` for the full guide and mode-selection logic.

## License

MIT
