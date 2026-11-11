"""figkit -- figures for slide-math decks, written in Python, drawn by TikZ.

Every function returns a string of TikZ code; `build()` wraps the strings in a
standalone XeLaTeX document (figkit/slidemath.sty), compiles it and writes an SVG
that is exactly as large on the slide as the coordinates say: 1 unit = 1 slide px.
TikZ's y axis points UP (the slide's points down).

    import sys; sys.path.insert(0, str(Path.home() / ".claude/skills/slide-math/figkit"))
    from figkit import *
    build("logits", vecdots([0.5, -0.8, 2.6, None, -0.6], labels=["1","2","3","\\cdots","K"],
                            highlight={2: "hl"}, yticks=[-1, 0, 1, 2]))

See FIGURES.md for the rules (sizes, colours, annotation) and gallery/figures/make_figures.py
for one script that builds every figure type.
"""

from __future__ import annotations

import hashlib
import shutil
import subprocess
from pathlib import Path
from typing import Iterable, Sequence

KIT = Path(__file__).resolve().parent
FONTS = KIT.parent / "fonts"

__all__ = [
    "P", "build", "vecdots", "node", "arrow", "pin", "zoom", "label", "brace",
    "lineplot", "hrule_axis", "raw", "vertex", "edge", "graph",
]


def P(x: float, y: float) -> str:
    """A TikZ coordinate in slide px, written in bp: P(10, 20) -> '(7.5bp,15bp)'.

    Plain numbers, not the \\px register: TikZ caches `to[...]` paths and arrow tips by
    name, and a register inside such a name stops XeLaTeX ("Missing \\endcsname").
    """
    return f"({_n(x * 0.75)}bp,{_n(y * 0.75)}bp)"


def _n(v: float) -> str:
    return f"{float(v):.3f}".rstrip("0").rstrip(".")


def _pt(p) -> str:
    """Accept a TikZ coordinate string '(a.east)' or a tuple (x, y) in px."""
    if isinstance(p, str):
        return p if p.startswith("(") else f"({p})"
    return P(*p)


def raw(code: str) -> str:
    """Pass TikZ code through unchanged."""
    return code


# ----------------------------------------------------------------------------- build

def build(name: str, *parts: str, outdir: str | Path = "figures", border: float = 2,
          png: bool = False, preamble: str = "") -> Path:
    """Compile the TikZ parts into <outdir>/<name>.svg (and .png at 2x if png=True).

    Recompiles only when the generated .tex changes. Returns the SVG path.
    """
    outdir = Path(outdir)
    work = outdir / "_build"
    work.mkdir(parents=True, exist_ok=True)
    body = "\n".join(parts)
    tex = (
        f"\\documentclass[border={_n(border * 0.75)}bp]{{standalone}}\n"
        f"\\def\\slidemathfonts{{{FONTS.as_posix()}/}}\n"
        f"\\usepackage{{{(KIT / 'slidemath').as_posix()}}}\n"
        f"{preamble}\n"
        "\\begin{document}\n\\begin{tikzpicture}\n"
        f"{body}\n"
        "\\end{tikzpicture}\n\\end{document}\n"
    )
    digest = hashlib.sha1(tex.encode()).hexdigest()[:12]
    svg = outdir / f"{name}.svg"
    stamp = work / f"{name}.sha"
    if svg.exists() and stamp.exists() and stamp.read_text() == digest and (not png or (outdir / f"{name}.png").exists()):
        return svg
    (work / f"{name}.tex").write_text(tex)
    res = subprocess.run(
        ["xelatex", "-interaction=nonstopmode", "-halt-on-error", f"{name}.tex"],
        cwd=work, capture_output=True, text=True,
    )
    if res.returncode != 0:
        errs = [l for l in res.stdout.splitlines() if l.startswith("!") or "error" in l.lower()]
        raise RuntimeError(f"xelatex failed for {name}:\n" + "\n".join(errs[:15]) +
                           f"\n(see {work / (name + '.log')})")
    pdf = work / f"{name}.pdf"
    subprocess.run(["pdftocairo", "-svg", str(pdf), str(svg)], check=True)
    if png:
        subprocess.run(["pdftocairo", "-png", "-r", "192", "-transp", "-singlefile",
                        str(pdf), str(outdir / name)], check=True)
    stamp.write_text(digest)
    return svg


# ----------------------------------------------------------------------------- primitives

def node(name: str, at, text: str, *, style: str = "box", w: float | None = None,
         h: float | None = None, anchor: str = "center", left: bool = False, extra: str = "") -> str:
    """A labelled box (style 'box', 'greybox', 'smallbox', 'tag', 'note', or any TikZ style).

    `text` is LaTeX: words in the body font, math in $...$. Use \\\\ for a line break.
    left=True sets the text flush left inside a box of width w (as text in a slide box).
    """
    opts = [style, f"anchor={anchor}"]
    if left and w is not None:
        opts += ["align=left", f"text width={_n(w - 24)}\\px"]
    if w is not None:
        opts.append(f"minimum width={_n(w)}\\px")
    if h is not None:
        opts.append(f"minimum height={_n(h)}\\px")
    if extra:
        opts.append(extra)
    return f"\\node[{', '.join(opts)}] ({name}) at {_pt(at)} {{{text}}};"


def arrow(*points, style: str = "arr", text: str | None = None, pos: str = "midway",
          side: str = "above", turn: str = "--") -> str:
    """An arrow through the points. turn='-|' or '|-' makes one right-angle bend between
    two points; pass more points for more bends. `text` labels the arrow."""
    pts = [_pt(p) for p in points]
    path = f" {turn} ".join(pts)
    lab = ""
    if text:
        lab = f" node[{pos}, {side}, note, font=\\fssmall] {{{text}}}"
        # attach the label to the first segment
        first, rest = pts[0], f" {turn} ".join(pts[1:])
        path = f"{first} {turn}{lab} {rest}"
    return f"\\draw[{style}] {path};"


def pin(at, to, text: str, *, anchor: str = "north west", width: float | None = None) -> str:
    """Dot at `at`, a straight leader line to `to`, the note at `to`.

    anchor: where the note sits relative to `to` ('north west' = note below-right of the end).
    """
    wopt = f", text width={_n(width)}\\px" if width else ""
    return (f"\\fill[ink] {_pt(at)} circle (4.5\\px);\n"
            f"\\draw[lead] {_pt(at)} -- {_pt(to)} node[note, anchor={anchor}{wopt}] {{{text}}};")


def zoom(p0, p1, name: str | None = None) -> str:
    """Dashed rectangle marking a region (to be enlarged, or discussed)."""
    nm = f" ({name})" if name else ""
    return f"\\draw[zoom] {_pt(p0)} rectangle {_pt(p1)};" + (
        f"\n\\coordinate{nm} at ($ {_pt(p0)}!0.5!{_pt(p1)} $);" if name else "")


def label(at, text: str, *, anchor: str = "center", size: str = "fssmall", extra: str = "") -> str:
    """Free text. size: fstick, fssmall, fslabel, fsbody, fslarge."""
    ex = f", {extra}" if extra else ""
    return f"\\node[inner sep=1\\px, anchor={anchor}, font=\\{size}, align=left{ex}] at {_pt(at)} {{{text}}};"


def brace(p0, p1, text: str = "", *, mirror: bool = False, anchor: str = "north") -> str:
    """Curly brace from p0 to p1 (the brace bulges to the left of the direction p0->p1;
    mirror=True flips it). The text sits at its middle."""
    m = ", mirror" if mirror else ""
    t = f" node[midway, note, anchor={anchor}, yshift={'-' if anchor == 'north' else ''}8\\px] {{{text}}}" if text else ""
    return f"\\draw[brace, decoration={{brace, amplitude=6\\px, raise=2\\px{m}}}] {_pt(p0)} -- {_pt(p1)}{t};"


def hrule_axis(x0: float, x1: float, y: float = 0, ticks: Iterable[float] = (),
               labels: dict[float, str] | None = None, *, scale: float = 1.0,
               tick: float = 12, arrow_end: bool = False) -> str:
    """A horizontal number line from x0 to x1 (values), ticks at the given values,
    labels {value: latex}. scale = px per unit."""
    out = [f"\\draw[line width=1.2bp{', -{Stealth[length=7.5bp, width=6bp]}' if arrow_end else ''}] {P(x0 * scale, y)} -- {P(x1 * scale, y)};"]
    for t in ticks:
        out.append(f"\\draw[line width=1.4\\px] {P(t * scale, y - tick / 2)} -- {P(t * scale, y + tick / 2)};")
    for v, s in (labels or {}).items():
        out.append(f"\\node[anchor=north, font=\\fsbody, inner sep=2\\px] at {P(v * scale, y - tick)} {{{s}}};")
    return "\n".join(out)


def vertex(name: str, at, text: str = "", *, style: str = "vertex", size: float | None = None,
           extra: str = "") -> str:
    """A circle node (style 'vertex', 'vertex hl' lavender, 'vertex hlc' cyan, 'vertex grey').
    `text` is LaTeX (an index such as '$3$' or a word); size = diameter in px (default 26)."""
    opts = [style]
    if size is not None:
        opts.append(f"minimum size={_n(size)}\\px")
    if extra:
        opts.append(extra)
    return f"\\node[{', '.join(opts)}] ({name}) at {_pt(at)} {{{text}}};"


def edge(a: str, b: str, *, directed: bool = False, bend: float = 0, style: str = "",
         text: str | None = None, side: str = "above") -> str:
    """An edge between two named nodes; it stops at their borders. bend > 0 bends left (degrees),
    which separates the two directions of a reciprocal pair. `text` labels it (15 px)."""
    opts = ["dedge" if directed else "edge"] + ([style] if style else [])
    lab = f" node[midway, {side}, note] {{{text}}}" if text else ""
    path = f"({a}) to[bend left={_n(bend)}]{lab} ({b})" if bend else f"({a}) --{lab} ({b})"
    return f"\\draw[{', '.join(opts)}] {path};"


def graph(pos: dict, edges: Iterable, *, directed: bool = False, labels: dict | None = None,
          highlight: dict | Iterable = (), size: float = 26, reciprocal_bend: float = 14) -> str:
    """A whole network: pos {name: (x, y)} in px, edges [(u, v), ...]. Vertices are labelled
    with their name in math unless `labels` gives another LaTeX string. highlight: names filled
    lavender ({name: 'hlc'} for cyan). In a directed graph, a pair u->v, v->u is drawn as two
    bent arrows. Edges are drawn on the background layer, under the vertices."""
    hl = highlight if isinstance(highlight, dict) else {v: "hl" for v in highlight}
    out = []
    for v, p in pos.items():
        sty = {"hl": "vertex hl", "hlc": "vertex hlc", "grey": "vertex grey"}.get(hl.get(v, ""), "vertex")
        txt = (labels or {}).get(v, f"${v}$")
        out.append(vertex(f"v{v}", p, txt, style=sty, size=size))
    es = list(edges)
    eset = set(es)
    out.append("\\begin{scope}[on background layer]")
    for u, v in es:
        bend = reciprocal_bend if directed and (v, u) in eset else 0
        out.append(edge(f"v{u}", f"v{v}", directed=directed, bend=bend))
    out.append("\\end{scope}")
    return "\n".join(out)


def vecdots(values: Sequence[float | None], *, labels: Sequence[str] | None = None,
            highlight: dict[int, str] | Iterable[int] = (), origin=(0, 0), unit: float = 36,
            step: float = 26, r: float = 4.5, yticks: Iterable[float] = (),
            ymin: float | None = None, ymax: float | None = None, ref: float | None = None,
            name: str = "v", ylabels: bool = True) -> str:
    """The entries of one vector as a dot plot: logits, probabilities, a gradient.

    One black dot per entry at its value, index labels under the axis. No bars (the user's rule).
    values: one number per entry; None leaves a gap labelled with labels[i] (e.g. '\\cdots').
    highlight: indices whose column gets a lavender band behind the dot ({i: 'hlc'} for cyan),
    the figure's version of \\hl{} on the slide. unit: px per 1.0 of value; step: px between
    entries; r: dot radius. ref: a dashed grey line at this value (1 for probabilities).
    Defines coordinates (name-i) at dot i and the bounding box node (name).
    """
    ox, oy = origin
    n = len(values)
    if labels is None:
        labels = [str(i + 1) for i in range(n)]
    hl = highlight if isinstance(highlight, dict) else {i: "hl" for i in highlight}
    vals = [v for v in values if v is not None]
    lo = min([0.0, *vals]) if ymin is None else ymin
    hi = max([0.0, *vals, *(x for x in [ref] if x is not None)]) if ymax is None else ymax
    lo_px = lo * unit - (8 if ymin is None and lo < 0 else 0)
    hi_px = hi * unit + 14
    right = (n + 0.6) * step
    out = [f"\\begin{{scope}}[shift={{{P(ox, oy)}}}, local bounding box={name}]"]
    for i, kind in hl.items():  # bands first, under everything
        x = (i + 1) * step
        col = {"hl": "hl", "hlc": "hlc"}.get(kind, "hl")
        out.append(f"\\fill[{col}] {P(x - step / 2 + 1.5, min(lo_px, 0) - 2)} rectangle {P(x + step / 2 - 1.5, hi_px - 6)};")
    if ref is not None:
        out.append(f"\\draw[refline] {P(0, ref * unit)} -- {P(right, ref * unit)};")
    out.append(f"\\draw[vaxis] {P(0, 0)} -- {P(right, 0)};")
    out.append(f"\\draw[vaxis] {P(0, lo_px)} -- {P(0, hi_px)};")
    for i, v in enumerate(values):
        x = (i + 1) * step
        if v is not None:
            out.append(f"\\fill[ink] {P(x, v * unit)} circle ({_n(r * 0.75)}bp);")
            out.append(f"\\coordinate ({name}-{i}) at {P(x, v * unit)};")
        out.append(f"\\node[font=\\fstick, anchor=north, inner sep=2\\px] at {P(x, min(lo_px, 0) - 3)} {{${labels[i]}$}};")
    if ylabels:
        for t in yticks:
            ty = t * unit
            out.append(f"\\draw[line width=0.8\\px] {P(-3, ty)} -- {P(3, ty)};")
            out.append(f"\\node[font=\\fstick, anchor=east, inner sep=2\\px] at {P(-3, ty)} {{${t:g}$}};")
    out.append("\\end{scope}")
    return "\n".join(out)


def lineplot(series: Sequence[dict], *, w: float = 520, h: float = 280, xlabel: str = "",
             ylabel: str = "", ymode: str = "normal", xmin=None, xmax=None, ymin=None,
             ymax=None, legend: str | None = "north east", title: str = "",
             at=(0, 0), name: str = "plot", extra: str = "", after: str = "") -> str:
    """A data figure with pgfplots in the slide-math style (thin black frame, ticks outside,
    legend without a frame). Each series: {"x": [...], "y": [...], "style": "base"|"new"|"third"
    or TikZ options, "label": "..."}. Axis coordinates are available inside `after` as
    (axis cs:x,y). Series 'base' = the standard method (vermillion), 'new' = the proposal (blue).
    """
    opts = ["slidemath", f"width={_n(w)}\\px", f"height={_n(h)}\\px", f"name={name}",
            f"at={{{P(*at)}}}"]
    if ymode == "log":
        opts.append("ymode=log")
    for k, v in (("xmin", xmin), ("xmax", xmax), ("ymin", ymin), ("ymax", ymax)):
        if v is not None:
            opts.append(f"{k}={v}")
    if xlabel:
        opts.append(f"xlabel={{{xlabel}}}")
    if ylabel:
        opts.append(f"ylabel={{{ylabel}}}")
    if title:
        opts.append(f"title={{{title}}}")
    if legend:
        opts.append(f"legend pos={legend}")
    if extra:
        opts.append(extra)
    out = [f"\\begin{{axis}}[{', '.join(opts)}]"]
    for s in series:
        xs, ys = list(s["x"]), list(s["y"])
        if len(xs) > 1500:  # keep the SVG small
            k = len(xs) // 1500 + 1
            xs, ys = xs[::k], ys[::k]
        coords = " ".join(f"({x:.6g},{y:.6g})" for x, y in zip(xs, ys))
        out.append(f"\\addplot[{s.get('style', 'base')}] coordinates {{{coords}}};")
        if legend and s.get("label"):
            out.append(f"\\addlegendentry{{{s['label']}}}")
    if after:
        out.append(after)
    out.append("\\end{axis}")
    return "\n".join(out)
