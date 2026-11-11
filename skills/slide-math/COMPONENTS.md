# slide-math: components

Every part of a slide and its markup. Copy from here or from `gallery/gallery.md` (one slide per
pattern, each with a comment naming its layout). The rules behind them are in `STYLE.md`.

## 0. Three rules of the markup

1. **A blank line after every opening `<div ...>` and before every `</div>`.** Marp parses
   Markdown (and math) inside an HTML block only after a blank line. Without it, `$x$` and
   `**bold**` are printed as typed.
2. **No math in raw HTML.** `<p class="note">$x$</p>` prints `$x$`. Write
   `<div class="note">` + blank line + `text with $x$` + blank line + `</div>` instead.
   A `<p>` or `<span>` with plain words is fine. `tools/check.py` catches this.
3. **Nothing positioned by hand except overlays.** Layout comes from the classes below. The
   only coordinates in a deck are those of an overlay SVG (section 5) or an occasional
   `style="grid-template-columns: ..."`.

## 1. Front matter and frame

```markdown
---
marp: true
theme: math
paginate: true
footer: "Sadamori Kojaku, 2026"
header: "![](figures/logo.svg)"     # optional logo, top right; omit if none
---
```

Render with the skill's config (it registers the theme, enables HTML and the KaTeX macros):
`~/.claude/skills/slide-math/tools/render.sh deck.md [html|pdf|png|all]`.

A content slide:

```markdown
## Softmax collapse in float32

When the target logit is much larger than the others, the standard cross-entropy rounds the target gradient to 0.

...body...

<div class="ref">Kingma, D. P., & Ba, J. (2015). Adam: A method for stochastic optimization. ICLR.</div>
```

- `## Title` draws the black bar and the title (one line; it is clipped, and the checker errors,
  if longer).
- **The first paragraph after the title is the lead** (22 px). To start a slide without a lead,
  start the body with a `<div>`.
- `.ref` (optional, a plain-text `<div>`): the full reference, bottom left above the footer.
- Per-slide directives: `<!-- _footer: "" -->`, `<!-- _paginate: false -->`, `<!-- _header: "" -->`.
- `<!-- _class: dense -->` (body 19 px) or `roomy` (24 px) for a single slide.

## 2. Text

| markup | gives |
|---|---|
| `**word**` | bold |
| `<span class="key">claim</span>` | red bold: the claim of a bullet group (math inside is fine) |
| `<mark>text</mark>` | lavender highlight on a phrase or a whole bullet |
| `<mark class="alt">text</mark>` | cyan highlight (the alternative) |
| `<span class="s-base">standard</span>`, `<span class="s-new">fixed</span>` | words in the series colours |
| `[title](url)` | blue link |
| `<span class="gap"></span>` | a 2.5 em space between two definitions on one line |
| `### Heading` | a bold run-in heading inside a box (21 px) |
| `<p class="small">` / `<div class="note">` | 15 px text; `.note` adds 4 px above |
| `<p class="muted">` | grey (asides about the slide itself, never content) |

Lists: `-` bullets, two spaces to nest. A blank line between two top-level items (a loose list)
adds a gap before the next group, as in the reference's grouped bullets:

```markdown
- **Overflow** at large logits
  - $e^{z}$ is larger than the largest float32 number when $z > 88.7$
  - <span class="key">subtracting $\max_j z_j$ before the exponential avoids it</span>

- **Collapse** at a large margin
  - ...
```

`<div class="vcenter">` + list + `</div>` centres a text-only body in the remaining height.

## 3. Boxes

```markdown
<div class="box" data-tab="Logit margin">

$$m = z_t - \log \sum_{j \neq t} e^{z_j}$$

- $m$ is how far $z_t$ is above the other logits

</div>
```

| class | what |
|---|---|
| `.box` | white, 2 px black border |
| `data-tab="Words"` | black tab label on the top border (plain text only, no math) |
| `.box.grey` | grey fill: secondary content, an aside, program output |
| `.box.tight` | less padding |
| `.box.eq-sm` / `.box.eq-lg` | smaller / larger display math inside |
| `<hr>` inside a box | a full-width black rule between sections of the box |
| `.split` (on a box) + ratio | columns inside the box with grey rules between; `.norule` drops the rules |
| `.span` (on a child of `.split` or `.cols`) | that child spans all columns (a title row) |
| `.panel` | white backing without border, for a figure quoted from a paper |

Box in sections (gallery 17):

```markdown
<div class="box">

### Softmax with temperature

One sentence about it, with $T$.

<hr>

<div class="split c12 mid">
<div class="center">

$$q_k = \frac{e^{z_k/T}}{\sum_j e^{z_j/T}}$$

</div>
<div>

- $T = 1$: the usual softmax

</div>
</div>
</div>
```

**Code and output** (gallery 10). A fenced block is a white code box; ` ```output ` (or
` ```text `) is grey. For output with a note under it, wrap it:

````markdown
```python
print(q - p)                # gradient with respect to z
```

<div class="out" id="out">

```output
[0.0000000e+00 1.5229979e-08 1.5229979e-08]
```

The exact value is $[-3.046\times10^{-8},\ \dots]$; the target entry is lost.

</div>
````

Run the code and paste its real output; never type an output by hand. Width: code is 18 px Source
Code Pro, about 11 px a character, so a code box holds about 100 characters at full width, 58 in a
`c32` left column, 47 in a `c11` column, 36 in a `c32` right column. Break long lines or widen the
column; `check.py` reports a code box wider than its column.

**Label-cell rows** (`.kv`, gallery 18): a Markdown table inside `<div class="kv">`; the header
row is required by Markdown and hidden; the first column becomes the grey label cell.

```markdown
<div class="kv">

| symbol | meaning |
|---|---|
| $\vb z$ | logits, one per class |

</div>
```

A plain Markdown table (no `.kv`) gets booktabs rules (top, header, bottom).

## 4. Grids and connectors

```markdown
<div class="cols c32">
<div>

left block (3 parts of 5)

</div>
<div>

right block

</div>
</div>
```

| class | columns |
|---|---|
| `.cols` (= `.c11`) | two equal columns, 28 px gap |
| `.c21` `.c12` `.c32` `.c23` `.c31` `.c13` | two columns in that ratio |
| `.c111` `.c211` `.c112` | three columns |
| `.cols.flow` (+ `.c21`, `.c12`, `.c111`) | blocks with a black triangle between. Its children, in order: block, `<span class="tri"></span>` (as its own paragraph, blank lines around it), block (and for `.c111`: tri, block). Each block is one `<div>` or one image paragraph |
| `.mid` | centre the columns vertically; `.stretch`: equal heights (boxes side by side) |
| `style="grid-template-columns: 1fr 560px"` | any other split |

Each column is one child `<div>` (or one paragraph: an image, a formula). A 2 x 2 grid of figures
with triangles (gallery 5): `.cols.flow.mid` with six paragraphs, image / tri / image, image /
tri / image.

Connectors:

| markup | what |
|---|---|
| `<span class="tri"></span>` | black triangle pointing right: "becomes" |
| `<span class="tri down"></span>` | pointing down |
| `<div class="darrow r"></div>` | thick down arrow between two stacked boxes, overlapping both borders; `.r` right, `.l` left, none = centre |

Height helpers, for **direct children of the slide only** (they act on the slide's column of
blocks; inside a `.cols` column they do nothing): `.fill` (take the remaining height), `.vcenter`
(centre the content in it), `.push` (move this block to the bottom of the slide).

## 5. Annotations

**Pin under a formula** (flow layout, no coordinates):

```markdown
<div class="pin">

For $m > 16.6$ the fraction rounds to 1, and $g_t$ becomes 0.

</div>
```

**Formula in parts with tags and pins** (gallery 12): each `.part` is one cell of the formula;
`data-tag` puts an outlined label above it; a `.pin` inside it hangs below. The row reserves room
above and below.

```markdown
<div class="parts eq-lg">
<div class="part">

$$g_t =$$

</div>
<div class="part" data-tag="standard">

$$\hl{\frac{1}{1 + e^{-m}}} - 1$$

<div class="pin">

For $m > 16.6$ the fraction rounds to 1.

</div>
</div>
</div>
```

**Inline**: `<span class="tag">aside</span>` (outlined label), `<span class="callout">one
sentence</span>` (outlined box), `<span class="chip">item</span>` (rounded, in a row).

**Overlay** (leader lines across blocks, dashed boxes over a slide): one SVG in slide coordinates,
after the body. Its styles come from the theme: `line` and `polyline` are 1.6 px black,
`circle` is a filled black dot (r 5), `rect` is a dashed 2.2 px box (`class="solid"` for solid),
`text` is 15 px Source Sans 3 (words only, no math).

```markdown
<svg class="overlay" viewBox="0 0 1280 720"><circle cx="568" cy="414" r="5"/><line x1="568" y1="414" x2="836" y2="226"/></svg>
```

Keep the SVG on one line (a blank line inside it ends the HTML block). The dot goes on the thing
being explained; the line ends at the note or the formula it points to.

**Getting the coordinates:** give the targets ids, then ask the checker for their boxes.

- a block: `<div class="out" id="out">`, `<p class="small" id="n1">`
- a part of a formula: `\htmlId{frac}{\hl{\frac{1}{1+e^{-m}}}}`
- run `python3 ~/.claude/skills/slide-math/tools/check.py deck.md --boxes` and read
  `box #frac: x 847-983, y 197-233 (centre 915,215)`.
- a point inside a figure: read it off the rendered PNG (`review/png/deck.NNN.png` is 1280 x 720,
  so pixel = slide coordinate), or put the annotation inside the figure itself (`FIGURES.md`),
  which is better when it belongs to the data.

## 6. Math

Display math: `$$...$$` on its own lines; inline: `$...$`. KaTeX, Computer Modern. Display math is
left-aligned with a small indent; wrap it in `<div class="center">` to centre it.

| class | display size |
|---|---|
| (default) | 1.3x the body |
| `.eq-lg` on a container | 1.7x: the one formula a slide is about |
| `.eq-sm` on a container | 1.05x: long derivations |

`.def` (definition line, inline math 1.32x):

```markdown
<div class="def">

Logits: $\vb z = [z_1, \dots, z_K]$ <span class="gap"></span> Target: $\vb p = [p_1, \dots, p_K]$

</div>
```

`.eqrow` (formula with its role at the right):

```markdown
<div class="eqrow eq-lg" data-label="parameter update">

$$\theta_i \leftarrow \theta_i - \eta\,\frac{\hat m_i}{\sqrt{\hat v_i} + \epsilon}$$

</div>
```

Macros (defined in `marp.config.mjs`):

| macro | gives |
|---|---|
| `\hl{x}` | lavender box behind `x` (keeps display style) |
| `\hlc{x}` | cyan box behind `x` |
| `\why{(text)}` | small text in the body font: the reason at the right of a step (`&& \why{(definition of $m$)}`), or a label over a part (`\overset{\why{this term jumps}}{...}`) |
| `\lbl{text}` | a word in the body font at math size |
| `\key{x}` | red `x` (rare) |
| `\vb{z}` | bold vector |
| `\softmax`, `\sigmoid`, `\argmax`, `\argmin`, `\tr`, `\diag` | upright operators |
| `\R`, `\E`, `\Pr`, `\d` (upright d), `\given` (inside `\left( \right)`) | |
| `\T` | transpose, written **without** `^`: `P\T` gives $P^{\top}$ (`P^\T` is a KaTeX error) |
| `\htmlId{id}{x}`, `\htmlClass{c}{x}` | an id or class on a formula part (trust is on) |

A derivation with reasons:

```latex
$$
\begin{aligned}
e^{-m} &= e^{-z_t + \log \sum_{j\neq t} e^{z_j}} && \why{(definition of $m$)}\\
&= \hl{\sum_{j\neq t} e^{z_j - z_t}}
\end{aligned}
$$
```

Builds mark with `\hl{}`, `<mark>` and `<div class="hl">` (lavender block behind a whole column).

## 7. Figures on the slide

```markdown
<div class="fig">
<p class="figtitle">Training loss</p>

![](figures/loss.svg)

<p class="cap">Figure 2 of Author et al. (2026)</p>
</div>
```

- Figures are SVG from the figure kit (`FIGURES.md`), shown at their authored size: one figure
  unit = one slide px. `![w:400](...)` scales one if needed (avoid: author it at the size).
- `.fig` centres; `.fig.left` aligns left. `<p class="cap">` and `<p class="figtitle">` take plain
  words only; **a caption with math needs the div form** (`<div class="cap">` + blank line + text
  with `$...$` + blank line + `</div>`): `<p class="cap">uniform, $\vb 1/n$</p>` prints the dollars.
- A figure quoted from a paper: a PNG crop of the paper's figure inside `<div class="panel">`,
  `.cap` "Figure N of Author et al. (Year)", the full reference in `.ref`.

## 8. Layouts (`<!-- _class: ... -->`)

**title** (cover; also clear footer and pagination):

```markdown
<!-- _class: title -->
<!-- _paginate: false -->
<!-- _footer: "" -->

# Softmax

## and its rounding <span class="hot">errors</span>

When float32 rounds the gradient to zero

<p class="by">Sadamori Kojaku</p>

<div class="art">

![](figures/art.svg)

</div>
```

`#` = one or two words in the black box (Source Serif 4 Display Black, 118 px; at most about
9 characters per line); `##` = the rest in 84 px with one `.hot` (pink) word; the paragraph after
`##` = the black band (one line); `.by` = author line; `.art` = a figure at the right (about 300 px).

**agenda**: `## Outline` and an ordered list (at most 6 items, one line each). `agenda at-3`
greys every item but the 3rd.

**divider** (first slide of a part):

```markdown
<!-- _class: divider -->

<p class="crumb">Softmax rounding errors</p>

## Softmax and cross-entropy

<div class="art">

![](figures/art.svg)

</div>
```

`.crumb` = the deck title in grey with the line and dot; `.art` = grey line art at the right
(optional; draw it in `muted` with the figure kit).

## 9. Pitfalls found while building the gallery

- A Python script that writes deck Markdown must use raw strings (`r"..."`): `"\frac"` contains a
  form feed and `"\to"` a tab, and KaTeX then fails on an invisible character.
- `data-tab`, `data-label`, `data-tag` take plain text: no math, no Markdown.
- Two display formulas in a row need a blank line between them, each its own `$$...$$`.
- A figure in a narrow column is scaled down with all its text; build it for the column width.
- The checker measures with the KaTeX fonts from the CDN; offline, math widths are approximate.
