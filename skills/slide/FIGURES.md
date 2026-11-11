# slide: figures

How the figures of this style are drawn. The kit is `figkit/`: Python functions that write TikZ,
`slidemath.sty` (fonts, colours, styles), and `build()`, which compiles with XeLaTeX and writes an
SVG. `gallery/figures/make_figures.py` builds one figure of every type below; start from it.

## 1. Principles

1. **Drawn for the slide, at the size it is shown.** One figure unit is one slide pixel
   (`P(x, y)` takes px; TikZ's y axis points up). A figure for a 569 px column is drawn 569 px
   wide or less, never drawn large and scaled down: scaling shrinks the text with it.
2. **The slide's type.** Words in Source Sans 3; numbers and symbols in Computer Modern, as KaTeX
   sets them on the slide. Sizes: ticks 13 px (`\fstick`), notes, legends and axis titles 15
   (`\fssmall`), node labels 17 (`\fslabel`), text as large as the body 21 (`\fsbody`), a formula
   in a node 26 (`\fslarge`).
3. **Black lines, white fills, one lavender.** Box borders 2 px, arrows 1.6 px with a small
   Stealth tip, data dots 9 px across, axes 1 px, leader lines 1.4 px. The element the slide talks
   about is filled `hl` (lavender); the alternative `hlc` (cyan). Reference lines are dashed grey.
4. **Data colours** (Okabe-Ito, colour-blind safe): `sbase` vermillion for the standard method,
   `snew` blue for the proposal; `sthree`, `sfour`, `sfive` only if needed. **No green.** A pair
   of curves of the same kind can be black solid vs black dashed.
5. **Label the thing, not a legend.** Put "standard" in vermillion next to the vermillion curve.
   Use a legend only when the curves are too tangled to label.
6. **Annotate in the figure when the note belongs to the data** (a spike, a threshold): dot, straight
   leader, note (`pin`), dashed box (`zoom`). Annotations that join a figure to a formula or a
   note elsewhere on the slide go in the slide's overlay SVG (`COMPONENTS.md` section 5).
7. **TikZ/pgfplots only.** No matplotlib (the user's rule: it models a plot, not a diagram, and its
   sizes are computed, not declared). Data comes in as Python lists.
8. **Honest data.** Figures of results use the real numbers; a synthetic illustration says so in
   its caption. Dots and axes are to scale; a log axis is labelled with powers of ten.
9. **No bar charts** (the user's rule). A value is a dot: dot plots for vectors and for any
   comparison by category, lines for a quantity over time or steps.

## 2. Use

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path.home() / ".claude/skills/slide/figkit"))
from figkit import P, build, vecdots, node, arrow, pin, zoom, label, brace, lineplot, hrule_axis, graph, vertex, edge, raw

build("logits", vecdots([0.5, -0.8, 2.6, 0.2, None, -0.6],
                        labels=["1", "2", "3", "4", r"\cdots", "K"],
                        highlight=[2], yticks=[-1, 0, 1, 2], unit=30, step=22),
      outdir="figures")            # -> figures/logits.svg
```

Keep one `figures/make_figures.py` per deck that builds every figure; run it from the deck
directory: `python3 figures/make_figures.py`. `build()` recompiles only figures whose code changed
(the TeX source and log are in `figures/_build/`). Needs `xelatex`, `pdftocairo`, and the TeX
packages `pgfplots`, `standalone`, `fontspec`.

Reference the SVG from the deck: `![](figures/logits.svg)`. SVG is vector in the PDF handout and
exact in size; use `build(..., png=True)` only if a PNG is needed elsewhere.

## 3. Sizes of the containers

Content width is 1167 px (x 57 to 1224). A column of `.cols` is
`(1167 - 28 (n-1)) x share`; inside a box subtract 52 (padding and border); inside `.split`
subtract 44 per column more.

| container | width (px) |
|---|---|
| full width | 1167 |
| `.cols` c11 column | 569 |
| c32 columns | 683 / 455 |
| c21 columns | 759 / 380 |
| c111 column | 370 |
| `.cols.flow` (two figures + triangle) inside a c11 column | 259 each |
| inside a box at full width | 1115 |

Height available under a one-line lead is about 545 px; under a two-line lead about 510.

## 4. Figure types

### 4.1 Vector dot plots (logits, probabilities, gradients)

The signature figure: the entries of one vector as black dots on a value axis with arrows, index
labels under the axis, a gap with `\cdots` before the last index `K`, and a lavender band behind
the entry the slide is about (the figure's `\hl{}`). A probability vector gets a dashed grey line
at 1 (`ref=1`). No bars.

```python
vecdots(values, labels=None, highlight=[2], unit=30, step=22, r=4.5,
        yticks=[-1, 0, 1, 2], ref=None, origin=(0, 0), name="z")
```

- `values`: one number per entry; `None` = the gap (its label is usually `r"\cdots"`).
- `unit`: px per 1.0 of value; `step`: px between entries; `r`: dot radius in px.
- `highlight`: indices on a lavender band, or `{i: "hlc"}` for cyan.
- defines `(name-i)` at dot i and `(name)` as the bounding box, for arrows.

Show before/after vectors side by side with a triangle between (`.cols.flow`), on the same
`unit`, so the values compare.

### 4.2 Flow diagram

Boxes (`node(..., style="box")`, 2 px border, label in `\fslabel`, formula in `\fslarge`),
vector dot plots inside it, orthogonal arrows. `left=True` sets a box's text flush left (a
caption line over a formula, as in the slides' boxes).

```python
node("ce", (880, 262), r"cross-entropy\\[6\px]\fslarge$L(\bm z,\bm p)=-\sum_k p_k\log\operatorname{softmax}(\bm z)_k$",
     w=500, h=96, left=True)
arrow((430, 465), (560, 465), (560, 262), "(ce.west)")       # right, down, right
arrow("(gr.west)", "(llm.east)", text="parameter update")    # a labelled arrow
```

Points are `(x, y)` tuples in px or TikZ strings such as `"(ce.west)"`. In TeX, `\bm` makes a bold
vector (the slide's `\vb`), `\operatorname{softmax}` the upright name.

### 4.3 Number line

`hrule_axis(x0, x1, y, ticks, labels, scale=px_per_unit, tick=22)` draws the line, ticks and
labels (`{0.25: r"$\tfrac14$"}`); add dots (`raw(f"\\fill[ink] {P(x, 0)} circle (6\\px);")`),
a curved arrow (`to[out=90, in=60]` between two `P()` points) and outlined callouts
(`node(..., style="tag", extra=r"font=\fsbody")`). See `numberline()` in the gallery script.

### 4.4 Data plots

```python
lineplot([{"x": steps, "y": loss_std, "style": "base"},
          {"x": steps, "y": loss_fix, "style": "new"}],
         w=500, h=170, ymode="log", ymin=1e-8, ymax=8, xmin=0, xmax=10000,
         ylabel="training loss", legend=None,
         extra=r"ytick={1e-7,1e-5,1e-3,1e-1}, scaled x ticks=false",
         after=r"\node[note, text=sbase, anchor=south east] at (axis cs:9950,1e-3) {standard};")
```

- `w`, `h`: the size of the axis box itself; labels add about 70 px left and 40 px below.
- `style`: `base`, `new`, `third`, or any TikZ options (`"draw=ink, dash pattern=on 6\\px off 4\\px"`).
- `after`: TikZ code drawn in axis coordinates `(axis cs:x,y)`: direct labels, `\draw[zoom]`,
  pins (`\fill[ink] (axis cs:...) circle (4.5\px); \draw[lead] ... node[note] {...};`),
  `\draw[refline]` for a threshold.
- The figure title goes on the slide (`<p class="figtitle">`), not in the plot, so the space above
  the frame is free for annotations.
- Thin black frame, ticks outside, no grid, no legend frame (all in the `slidemath` pgfplots style).

### 4.5 Small multiples

Two or three plots of the same quantity side by side, same axes, same `w`/`h`, black solid vs
dashed for the two parameters; titles in `\fssmall` bold through `title=`. Build each as its own
SVG and place them in `.split` columns of one box with a figure title row (gallery 8).

### 4.6 Network diagrams

```python
pos = {1: (0, 120), 2: (0, 0), 3: (110, 60), 4: (230, 120), 5: (230, 0), 6: (330, 60)}
edges = [(1, 2), (1, 3), (3, 1), (2, 3), (4, 3), (5, 3), (4, 6), (6, 4), (5, 6), (3, 5), (5, 4)]
build("network", graph(pos, edges, directed=True, highlight=[3]), outdir="figures")
```

`graph()` draws circles (26 px, 1.5 px outline, the name in math) and edges that stop at the
circles' borders, under the vertices; a reciprocal pair in a directed graph becomes two bent
arrows. `highlight` fills vertices lavender (`{v: "hlc"}` cyan, `{v: "grey"}` grey). For more
control use `vertex(name, at, text, style=...)` and `edge("v1", "v3", directed=True, bend=14,
text="0.85")`; node names are `v` + the key. Lay the vertices out by hand on a coarse grid
(multiples of 10 px): a hand layout reads better than a computed one at this size.

### 4.7 Line art (divider and title slides)

A math object drawn in `muted` grey thin lines, e.g. softmax paths on the probability simplex
(`art()` in the gallery script). About 500 px wide; nothing in it is read.

## 5. Quoting a figure from a paper

Crop it from the PDF at 2x: `pdftoppm -r 200 -f 5 -l 5 -x X -y Y -W W -H H -png paper.pdf figures/fig2`
(coordinates at 200 dpi), show it on a `.panel` with `![w:N](figures/fig2-05.png)` where N is the
display width, a `.figtitle` above saying what to see, a `.cap` "Figure 2 of Author et al. (Year)",
and the full reference in `.ref`. Annotate it from the slide overlay (pins to notes below it).

## 6. Pitfalls

- **`\px` inside a `to[...]` path or an arrow tip stops XeLaTeX** with "Missing \endcsname"
  (TikZ caches those by name). `P()` writes plain bp numbers, so use `P()` for every coordinate;
  arrow-tip sizes in `slidemath.sty` are in bp.
- pgfplots legend images take the plot's `color=`; a style that sets only `draw=` gives grey
  legend lines (the kit's `base`/`new` styles use `color=`).
- A long series is thinned to 1500 points to keep the SVG small.
- `text width` must be set for flush-left text in a fixed-width box (`node(..., left=True)`).
- After changing `slidemath.sty`, delete `figures/_build/*.sha` to force a rebuild.
