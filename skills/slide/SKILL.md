---
name: slide
description: Build or review an English Marp slide deck in this style - dense, annotated math slides that read as a handout - black-bar titles with a one-sentence lead, formulas in boxes with black tab labels, lavender highlights, boxes split into 2-3 columns, code with its output, and TikZ figures (dot plots of vectors, flow diagrams, number lines, data curves) with pins and leader lines. Use when the user asks for math or handout-style slides, or for a deck "in this style".
---

# slide

A Marp theme, a component set, a figure kit and a checker for dense math slides in English.
Everything is in this directory (`~/.claude/skills/slide/`).

| file | read it for |
|---|---|
| `STYLE.md` | the look and its rules: frame, colour, type, text amount, formula placement, annotation, slide patterns, builds, review checklist |
| `COMPONENTS.md` | the markup of every part (boxes, tab labels, columns, connectors, pins, overlays, math macros, layouts) |
| `FIGURES.md` | how to draw the figures with `figkit/` (TikZ from Python, SVG at slide size) |
| `gallery/gallery.md` | one slide per pattern, rendered in `reference/gallery-*.png`; copy from it |
| `template/` | a starter deck and figure script |

## Build a deck

1. **Wireframe first.** In `review/WIREFRAME.md` of the deck directory, list every slide: layout
   (title / agenda / divider / a pattern from `STYLE.md` section 8), title (a topic noun phrase),
   lead (the claim in one literal sentence), the evidence it shows (formula, code, figure) and
   what is marked. Check the wording rule (`STYLE.md` section 5, N9) here, before any markup.
2. **Scaffold.** `cp -R ~/.claude/skills/slide/template/. <deck_dir>/` and rename `deck.md`.
3. **Figures.** Write `figures/make_figures.py` with the kit (`FIGURES.md`); run it from the deck
   directory. Author each figure at the width of the container it goes in (`FIGURES.md` section 3).
4. **Slides.** Copy the matching slide from `gallery/gallery.md`, change the words. Keep the three
   markup rules of `COMPONENTS.md` section 0 (blank lines inside divs, no math in raw HTML, no
   hand positioning except overlays).
5. **Check** until it reports 0 errors:
   `python3 ~/.claude/skills/slide/tools/check.py deck.md`
   It measures the laid-out slides in Chrome: content past the bottom or right margin, titles over
   one line, formulas or code wider than their box, unrendered LaTeX, KaTeX errors, missing images;
   it warns on leads or bullets over two lines and slides over 130 words.
6. **Look.** `~/.claude/skills/slide/tools/render.sh deck.md png` writes one PNG per slide in
   `review/png/` and contact sheets `review/sheet-N.png`. Read the sheets and every changed slide,
   and go through the checklist in `STYLE.md` section 11. Compare with `reference/gallery-*.png`.
7. **Overlays last.** When the layout is final, add leader lines and dashed boxes
   (`COMPONENTS.md` section 5); get coordinates from `check.py deck.md --boxes`; re-render and look.
8. **Export.** `render.sh deck.md all`: `deck.html` (to share), `deck.pdf` (the handout), PNGs.
9. If the deck is in a git repository, commit after each passing check.

## Review a deck

Run `check.py`, render the PNGs, read every slide against `STYLE.md` section 11, and report
findings as Blocker (wrong content, unreadable, overflow), Major (breaks a rule of `STYLE.md`),
Minor (polish), each with the slide number and the exact fix.

## Requirements

`marp` (marp-cli 4), Chrome or Chromium (set `SLIDE_MATH_CHROME` if not in the usual place),
`python3` with Pillow (contact sheets), `xelatex` with `pgfplots`, `standalone`, `fontspec`, and
`pdftocairo` (figures). Fonts are bundled (`fonts/`, SIL OFL) and embedded in
`theme/math-fonts.css` by `tools/build_fonts.py` (run with `uv run`, only when a font changes;
never open that CSS file, it is one long base64 line per face). KaTeX loads its own fonts from a
CDN, so render online.
