# <Deck title> — Marp deck

<One-line description of what this deck covers.>

## Files

    deck.md              the deck (rename freely; update check_render.py's `deck=` to match)
    figures/              PNG/GIF assets (prefer PNG over SVG — Marp renders <img src="*.svg"> blank)
    check_render.py       the pixel-level build gate — thin wrapper around gatelib
    review/               rendered slide.NNN.png, DECK_SPEC.md, FIXES_Rn.md, CHECKPOINT.md

The theme (`theme.css`) and the QA pipeline (`gatelib`) are not copied into
this directory — they live once in `~/.claude/skills/slide/` and every
deck points at them.

## Build

```sh
npm i -g @marp-team/marp-cli   # once

marp deck.md --theme ~/.claude/skills/slide/theme.css \
     --allow-local-files --html --no-stdin -o deck.html
marp deck.md --theme ~/.claude/skills/slide/theme.css \
     --allow-local-files --html --no-stdin --pdf
```

Or in VS Code with the Marp extension, add to `settings.json`:

    "markdown.marp.themes": ["~/.claude/skills/slide/theme.css"]

Math is KaTeX (`math: katex` in the front matter), so `$...$` and `$$...$$` work as written.

## QA gate

Run from the skill directory, pointing at this deck's directory:

```sh
cd ~/.claude/skills/slide
python3 -m gatelib review /path/to/this-deck-directory
```

This renders the deck, runs every automated check (source + pixel-level),
auto-fixes what's mechanical, and prepares downscaled review images. See
`DECK_BUILD_GUIDE.md` and `FIGURE_GUIDE.md` for what "good" means and how to
draw figures that pass the gate; see `REVIEW_PLAYBOOK.md` for the review
loop itself.

## Design tokens (from the bundled default theme)

    accent          #3959A6
    accent 2        #B14434
    accent 3        #DAB167
    text            #000000
    annotation      #6b6b6b
    rule            #dddddd
    formula panel   #f7f4f1

    body            Libre Baskerville 400
    figure labels   Caveat

Using a different theme? Swap the `--theme` path above and re-measure the
pixel floors in `FIGURE_GUIDE.md` — they describe this bundled theme's
geometry, not Marp's.

## Conventions

    <!-- _class: lead -->      title slide
    <!-- _class: part -->      part divider (needs a <div class="band">)
    <!-- _class: mid -->       shallow slide — centers the body, not the heading
    ## Title + <hr>            title and rule on the SAME slide as content
                               (a bare --- after a title splits the slide)
    <div class="cols">         two-column: text + figure
    <div class="fig">          figure wrapper (![](figures/x.png) + <figcaption>)
    <div class="formula">      tinted formula panel
    <div class="note">         gray annotation copy — never the answer to a question
    <div class="steps-list">   numbered takeaway list, max 8 rows
    <!-- ... -->               speaker notes

Regenerate figures with your own `figures/make_figures.py` (TikZ for
node-link diagrams, Altair/seaborn for data figures — see `FIGURE_GUIDE.md`
for why and for the assertions to build in).
