# slide: the style

The look of these decks, why it works, and the rules that keep it. `COMPONENTS.md` has the markup,
`FIGURES.md` the figures. Numbers below are slide pixels on the 1280 x 720 slide.

The style was learnt from a Japanese handout deck on softmax rounding errors (37 pages, Figma,
2026). Its pages are not included here. Do not copy that deck's content, its channel's logo or
its line art. `reference/gallery-*.png` is this skill's own rendering of the style (`gallery/gallery.md`). It was rebuilt for
English text: fonts, sizes and wording rules below are chosen for English, not translated.

## 1. What makes it work

1. **The slide is a page of a handout.** It must make sense when read alone, without the speaker.
   So every content slide says its point in a full sentence (the lead) right under the title.
2. **Title = topic, lead = claim.** The title is a short noun phrase ("Softmax collapse", "Adam
   (Kingma & Ba 2015)"). The sentence under it says what is true ("When the target logit is much
   larger than the others, the standard cross-entropy rounds the target gradient to 0.").
3. **Evidence, not prose, fills the slide.** Under the lead come formulas, code, its output and
   figures, framed in black-bordered boxes. Text below them is a few one-line bullets.
4. **Formulas are large and framed.** The defining formula of a slide sits in a box with a black
   tab label, about 1.5x the body text. Derivations sit in their own box, smaller, with the reason
   for each step at the right.
5. **One highlight colour says "look here".** A pale lavender fill marks the part of a formula,
   the entry of a figure or the bullet the slide is about, and the same lavender links them: the
   entry on a lavender band in the figure is the term highlighted in the formula. A pale cyan marks the
   alternative being compared. Everything else is black on white or warm off-white.
6. **Annotations sit on the thing they explain.** A dot on the point, a straight black line, a
   short note; a dashed rectangle around a region; an outlined tag above a formula part. Notes
   are small (15 px) and never more than two lines.
7. **Figures are drawn for the slide.** Dot plots of the entries of logits and probabilities, flow
   diagrams, number lines: black dots, thin black outlines, white fills, the entry the slide is
   about on a lavender band, Computer Modern numbers,
   the same type sizes as the slide. Data curves use two colour-blind-safe colours for
   "standard" and "proposed".
8. **Builds repeat the slide.** To walk through an argument, the same slide is repeated and the
   lavender mark moves (bullet 1-2, then the update rule, then bullet 4). Nothing else moves.

## 2. The frame

| element | position | size |
|---|---|---|
| title bar | x 27, y 20 | 10 x 37 black |
| title | x 49, y 20, one line | Source Sans 3 Bold 30 px, line 37 px |
| lead | x 49, from y 72 | 22 px, line 1.5, one or two lines |
| body | x 57 to 1223, y below the lead to 668 | 21 px, line 1.5 |
| logo (optional) | top right, 24 px in | 44 px tall |
| reference line (optional) | x 27, bottom 28 | 11 px, black |
| footer | x 27, bottom 12 | 10.5 px, grey `#969696` ("Author, Year") |
| page number | right 27, bottom 12 | 10.5 px, grey |

Boxes have a 2 px black border; a tab label is 37 px tall, black, white bold text, set 20 px
from the box's left edge and centred on its top border. Box padding 16 x 24 px; 14 px between
stacked boxes; 28 px between columns.

Other layouts: the **title** slide (black serif box, a second serif line with one pink word, a
black band with a one-line subtitle, optional figure at right), the **agenda** (numbered black
discs, 40 px bold items), the **divider** that opens each part (grey breadcrumb line with a dot
and the deck title, the part title in 42 px bold at the left, optional grey line art at the
right).

## 3. Colour

| token | hex | role | rule |
|---|---|---|---|
| paper | `#FAF9F6` | slide background | never pure white for the slide |
| white | `#FFFFFF` | box fill, quoted-figure panel | |
| ink | `#000000` | text, borders, arrows, leader lines | crisp black, as the reference |
| fill | `#F4F4F4` | output box, label cells | "secondary", not "important" |
| rule | `#C9C9C9` | divider inside a box | |
| muted | `#969696` | footer, breadcrumb, line art, greyed agenda | never for content text |
| **hl** | `#F4E6FF` | lavender: the part to look at | at most two marked things per slide (one thing marked in both the figure and the formula counts once) |
| hl2 | `#E5FDFF` | cyan: the alternative being compared | only next to a lavender mark |
| key | `#B70000` | red bold: the claim of a bullet group | at most one per group, two per slide |
| link | `#2700D5` | title of a work, URL | |
| pink | `#E31663` | one word on the title slide | title slide only |
| s-base | `#D55E00` | data series: the baseline / standard | Okabe-Ito vermillion |
| s-new | `#0072B2` | data series: the proposal / fixed | Okabe-Ito blue |
| s-3, s-4, s-5 | `#E69F00` `#56B4E9` `#CC79A7` | further series | only if a figure needs them |

Rules:
- **Meaning is fixed across the deck.** Lavender is always "the thing this slide is about"; cyan is
  always "the other one"; vermillion is always the standard method and blue the proposed one,
  in every figure and in prose (`<span class="s-base">standard</span>`).
- **The same lavender links text and figure.** If an entry of a figure, a term and a bullet are the same thing,
  all three carry lavender. Nothing unrelated may be lavender on that slide.
- **No green** anywhere (the user's rule): not in figures, not in code highlighting.
- **No bar charts** (the user's rule): a value is a dot. The entries of a vector are a dot plot
  (`vecdots`), a comparison of methods is dots or lines, never bars.
- Colour is never the only carrier: a series also has a label next to its curve; a highlighted
  term is also the one the text names.
- Highlights are fills, not coloured text. Red text is for a claim only, in bold.

## 4. Type

- **Source Sans 3** for all text (titles 700, body 400, labels 600-700). Chosen for English:
  a humanist sans with a moderate x-height that sits well next to Computer Modern math, narrow
  enough for dense handout text, with true italics, and it is the Latin of Source Han Sans
  (Noto Sans JP), the face of the reference deck, so the look carries over.
- **Computer Modern** (KaTeX) for all math, in the slides and in the figures (numbers on axes
  included). Vectors in bold italic (`\vb z`), operators upright (`\softmax`, `\log`).
- **Source Code Pro** for code and program output (the Source family's monospace).
- **Source Serif 4 Display** Black/Bold on the title slide only.
- All fonts ship with the skill (SIL OFL) and are embedded in the theme, so HTML, PDF and PNG
  look the same on any machine, offline.

Sizes (px): title 30 bold; lead 22; body and bullets 21; code 18; notes, captions, annotations
15; figure titles 16 bold; tab labels 21 bold; footer 10.5. Inline math is scaled to the body
x-height; display math is 1.3x (about 31 px); `.eq-lg` 1.7x for the one formula a slide is
about; `.eq-sm` 1.05x for long derivations.

English-specific rules:
- Sentence case everywhere ("Softmax collapse in float32", not "Softmax Collapse In Float32").
  Proper names keep their capitals (Adam, KaTeX).
- No all-caps, no letter-spacing, no underlining for emphasis.
- The lead is a full sentence with a full stop; bullets are fragments without a full stop.
- A number compared with or assigned to a symbol is set as math (`$m > 16.6$`); other numbers
  are plain text ("10,000 steps"). Do it the same way on every slide and in every build.
- Cite in text as "Kingma & Ba 2015"; give the full reference in the `.ref` line of the slide.

## 5. How much text

| part | limit |
|---|---|
| title | one line, about 45 characters; a noun phrase naming the topic |
| lead | one sentence (two at most), at most two lines (about 40 words) |
| bullet | one line (about 14 words); two lines only if unavoidable |
| bullets per group | at most 5; at most 2 levels |
| note / annotation | at most two lines at 15 px |
| text per slide | at most 130 words, formulas and code not counted (`tools/check.py` warns) |

The density is that of a handout: a slide may hold a lead, two boxes, a figure and four bullets.
It may not hold paragraphs. When it does not fit, split the slide or move a derivation to its own
slide; do not shrink the type below these sizes (`dense` exists for one slide in a deck, not as
a habit).

**Wording (the user's rule N9, 2026-10-31):** every title, lead, label and note is literal, direct
and brief. No figure of speech, no thematic title, no personified abstraction ("the gradient
dies", "the slowest term sets the clock"), no rhetorical question, no build-up sentence. Name the
mathematical object and define its symbols ("$m$ is the logit margin: $m = z_t - \log\sum_{j\ne
t} e^{z_j}$"). If a standard name, a symbol or a number exists, use it.

## 6. Placing formulas

- **Definition line first.** Before the boxes, one line states the objects with larger math:
  "Logits: $\vb z = [z_1, \dots, z_K]$" (`.def`). Two definitions share the line.
- **The defining formula in a tab box**, display size, left-aligned with a small indent; the tab
  names it in words ("Probabilities", "Logit margin", "Adam update"). A one-line note under
  the formula, inside the box, says the one fact the reader needs (15 px).
- **A derivation in its own box**, aligned on `=`, `.eq-sm` if it is long, with the reason for a
  step at the right in the body font (`\why{(definition of $m$)}`). Highlight (`\hl{...}`) the
  term that the next line or the next slide uses.
- **A transformation is shown as two boxes** joined by a thick down arrow (stacked) or a black
  triangle (side by side): "softmax" -> "standard implementation"; "derivative" -> "for a
  hard target".
- **A formula row with a role.** When a slide lists the update rules of an algorithm, each row
  gets its role at the right: "· · ·  parameter update" (`.eqrow`).
- **Formula parts with labels.** To contrast two forms of one quantity, cut the formula into
  parts (`.parts`), label each part with a tag above ("standard", "fixed"), give each a pin
  below with one sentence, and fill them lavender and cyan.
- **Code and its output** come as a white code box and a grey output box under it; the output
  box carries a small indented note with the exact value ("The exact value is ...").
- Never put math inside a tab label, a raw HTML attribute or an SVG `<text>`: it is not rendered.

## 7. Annotation

- **Pin**: a 10 px black dot on the point, a straight 1.5 px black line, the note at the other end.
  The line may be diagonal; it never bends and never has an arrowhead.
- **Zoom box**: a dashed 2 px black rectangle around the region discussed or enlarged; a leader
  line may join it to the enlarged figure.
- **Tag**: an outlined 2 px box with a 17 px word above a formula part or a figure part.
- **Callout**: an outlined box with one short sentence, placed over the region it describes.
- **Figure title** above a figure in 16 px bold, centred; **caption** under it in 15 px
  ("Figure 2 of Author et al. (2026)" for a quoted figure, always with the source).
- Notes go next to their target, not in a legend. Data series are labelled by a word in the
  series colour next to the curve, not by a legend box, when there is room.
- At most four annotations on one figure.

## 8. Slide patterns

The reference deck uses a small set of compositions. Use them; `gallery/gallery.md` has each one.

| pattern | when | gallery slide |
|---|---|---|
| lead + one large diagram | the pipeline or system a part is about | 4 |
| two tab boxes stacked (with a thick arrow) + before/after figures with triangles | a definition and its implementation | 5 |
| definition + tab box with bullets + two small figures (left), tall derivation box (right) | a new quantity, its meaning, and what it implies | 6 |
| tab box on top, two boxes joined by a triangle below | a general result, then a special case | 7 |
| box split into formula / bullets, box with title row + two plots + text column | an algorithm and how it behaves | 8 |
| code box, output box with note, bullets (left), derivation (right), leader line | a numerical example that shows a failure | 10 |
| stacked data plots (left), grouped bullets (right) | an experiment and what it shows | 11 |
| formula in parts with tags and pins, figure with callouts | two formulas for one quantity | 12 |
| big update rule with role labels, bullets, repeated as builds | a mechanism in steps | 13-15 |
| quoted figure on a white panel, title above, source below, notes joined by lines | evidence from a paper | 16 |
| box in sections (header, rule, split columns), chips, grey aside | a summary card | 17 |
| label-cell rows | notation, settings, a comparison by row | 18 |
| text only, grouped bullets with one red claim each | the problem statement | 19 |
| nested bullets | the summary | 20 |

## 9. Builds

A build is the same slide repeated with one more thing marked: a `<mark>` on a bullet, `\hl{}` on
a term, `.hl` on a block, a tag or pin added. Everything else is identical, character for
character, so nothing jumps when the slides are flipped. Two to four builds per argument.

## 10. Deck structure

Title -> agenda -> for each part: divider, content slides -> summary. Repeat the agenda before
each part with `at-N` to grey the other items (optional for short decks). Every content slide has
a title and a lead; the agenda, dividers and the summary have no lead.

## 11. Review checklist

1. `tools/check.py deck.md` reports 0 errors (overflow, one-line titles, unrendered math, images).
2. Every content slide: title = topic noun phrase; lead = one literal sentence stating the claim.
3. Wording (N9): no figure of speech, no thematic title; symbols defined where they first appear.
4. Lavender marks only the thing the lead talks about, and the same thing in figure and formula.
5. Formulas: the defining one in a tab box at display size; derivations smaller with reasons.
6. Every annotation touches its target; no note longer than two lines; no arrowheads on leaders.
7. Figures: SVG from the figure kit, authored at the size they are shown, Computer Modern numbers,
   dots not bars, no green, series labelled by the curve; a quoted figure has its source.
8. Builds differ only in the marks.
9. The contact sheet (`tools/render.sh deck.md png`) reads as one deck: same frame on every slide.
