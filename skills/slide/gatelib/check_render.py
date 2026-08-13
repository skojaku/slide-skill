#!/usr/bin/env python3
"""Shared render gate for all decks. Imported by each deck's thin check_render.py.

Single source of truth, so a check fixed in one deck's copy is never silently lost
when the next deck's thin wrapper is copied from an older one. This module carries
every check ever written; the per-deck script carries only that deck's constants
and filename.

Usage from a deck directory:

    # check_render.py (per deck, thin)
    import sys, os
    sys.path.insert(0, os.path.expanduser("~/.claude/skills/slide"))
    from gatelib.check_render import run
    run(deck="<slug>.md", fig_h={...}, exempt_figures=[...])

    # Only pass node_fills=[(R,G,B), ...] if the deck draws circular node-link
    # diagrams (network/graph figures) and you want their disc size checked.
    # It is off by default.
"""

import glob
import os
import re
import sys
from collections import deque

import numpy as np
from PIL import Image


# ── Defaults (overridable per module) ────────────────────────────────────────

SLIDES = "review/slide.*.png"

MIN_TEXT_XHEIGHT = 15
MIN_DRAWING_PX = 150
MAX_AXIS_MARGIN = 0.30
NODE_MIN_PX, NODE_MAX_PX = 26, 52
INK_FRACTION_FAIL = 0.15
INK_FRACTION_WANT = 0.35
CONTENT_BOTTOM = 660
COL_W = 537
FULL_IMG_W = 1080
DARK = 60
INK = 200
FILL_TOL = 46
MIN_DISC_AREA = 380

# ── Image utilities ──────────────────────────────────────────────────────────

def components(mask, min_px=120, step=2, with_origin=False):
    """Connected components of a boolean mask, as (h, w, area) triples.

    With `with_origin`, yields (h, w, area, y0, x0) so a caller can re-measure the same
    box against a different mask.
    """
    H, W = mask.shape
    seen = np.zeros_like(mask, bool)
    out = []
    for y in range(0, H, step):
        for x in range(0, W, step):
            if not mask[y, x] or seen[y, x]:
                continue
            q = deque([(y, x)])
            seen[y, x] = True
            ys, xs, n = [], [], 0
            while q:
                cy, cx = q.popleft()
                ys.append(cy)
                xs.append(cx)
                n += 1
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < H and 0 <= nx < W and mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        q.append((ny, nx))
            if n >= min_px:
                bh, bw = max(ys) - min(ys) + 1, max(xs) - min(xs) + 1
                out.append((bh, bw, n, min(ys), min(xs)) if with_origin else (bh, bw, n))
    return out


def _flood_from_border(mask):
    """Everything in `mask` reachable from the image border, four-connected."""
    H, W = mask.shape
    out = np.zeros_like(mask)
    q = deque()
    for x in range(W):
        for y in (0, H - 1):
            if mask[y, x] and not out[y, x]:
                out[y, x] = True
                q.append((y, x))
    for y in range(H):
        for x in (0, W - 1):
            if mask[y, x] and not out[y, x]:
                out[y, x] = True
                q.append((y, x))
    while q:
        cy, cx = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = cy + dy, cx + dx
            if 0 <= ny < H and 0 <= nx < W and mask[ny, nx] and not out[ny, nx]:
                out[ny, nx] = True
                q.append((ny, nx))
    return out


# ── Node disc detection ─────────────────────────────────────────────────────

def node_discs(rgb, node_fills, fill_tol=FILL_TOL):
    """Filled circles: near-square bounding box, fill ratio near pi/4.

    Takes an RGB array and masks on the theme's node fills.
    """
    a = np.asarray(rgb, dtype=np.int16)
    if a.ndim == 2:
        a = np.stack([a] * 3, axis=-1)
    mask = np.zeros(a.shape[:2], bool)
    for fill in node_fills:
        mask |= (np.abs(a - np.array(fill, dtype=np.int16)).max(axis=-1) <= fill_tol)
    mask[(mask.mean(axis=1) > 0.5)] = False
    filled = ~_flood_from_border(~mask)
    out = []
    for h, w, area, y0, x0 in components(filled, min_px=MIN_DISC_AREA, with_origin=True):
        if h < 8 or w < 8:
            continue
        if not (0.82 < h / w < 1.22 and 0.70 < area / (h * w) < 0.92):
            continue
        if mask[y0:y0 + h, x0:x0 + w].mean() < 0.45:
            continue
        c = max(2, int(min(h, w) * 0.12))
        corners = [filled[y0 + c, x0 + c], filled[y0 + c, x0 + w - 1 - c],
                   filled[y0 + h - 1 - c, x0 + c], filled[y0 + h - 1 - c, x0 + w - 1 - c]]
        if any(corners):
            continue
        out.append((h + w) / 2)
    return out


# ── Source-level checks ─────────────────────────────────────────────────────

def figure_containers(deck, col_w=COL_W, full_img_w=FULL_IMG_W, fig_h=None):
    """Which container each figure is USED in, per slide."""
    if fig_h is None:
        fig_h = {"": 380, "tight": 320, "stack": 190, "tall": 400}
    with open(deck) as fh:
        parts = fh.read().split("\n---\n")
    out = []
    for i, chunk in enumerate(parts[1:], start=1):
        in_cols = 'class="cols"' in chunk
        mod = ""
        for m in fig_h:
            if m and f'class="fig {m}"' in chunk:
                mod = m
        for f in re.findall(r"!\[[^\]]*\]\((figures/[^)]+)\)", chunk):
            out.append((i, f, col_w if in_cols else full_img_w, fig_h[mod], mod))
    return out


def figcaption_math(deck):
    """KaTeX does not process <figcaption>, or any other raw HTML block."""
    with open(deck) as fh:
        text = fh.read()
    bad = []
    for m in re.finditer(r"<figcaption>(.*?)</figcaption>", text, re.S):
        if "$" in m.group(1):
            bad.append(("figcaption", m.group(1).strip()[:60]))
    for m in re.finditer(r'<div class="steps-list">\n(.*?)\n\n</div>', text, re.S):
        for line in m.group(1).splitlines():
            if "$" in line:
                bad.append(("steps-list", line.strip()[:60]))
    return bad


def caption_colours(deck, colour_words=None):
    """A caption that names a colour the figure does not contain.

    Written for m02, lost across module boundaries. Recovered 2026-08-06.
    A stale caption naming a colour the figure no longer draws is invisible
    to both the generator and the deck — only this check spans the two.
    """
    if colour_words is None:
        colour_words = {"gold": (0xDA, 0xB1, 0x67), "red": (0xB1, 0x44, 0x34),
                        "blue": (0x39, 0x59, 0xA6), "gray": (0x6b, 0x6b, 0x6b),
                        "grey": (0x6b, 0x6b, 0x6b)}
    with open(deck) as fh:
        parts = fh.read().split("\n---\n")
    bad = []
    for i, chunk in enumerate(parts[1:], start=1):
        caps = re.findall(r"<figcaption>(.*?)</figcaption>", chunk, re.S)
        figs = re.findall(r"!\[[^\]]*\]\((figures/[^)]+)\)", chunk)
        if not caps or not figs:
            continue
        named = {w for cap in caps for w in colour_words if re.search(rf"\b{w}\b", cap, re.I)}
        if not named:
            continue
        try:
            im = np.array(Image.open(figs[0]).convert("RGB"), dtype=np.int16)
        except OSError:
            continue
        for w in sorted(named):
            hit = (np.abs(im - np.array(colour_words[w], dtype=np.int16)).max(axis=-1) <= 40).sum()
            if hit < 200:
                bad.append((i, w, figs[0]))
    return bad


def em_dashes(deck):
    """No em-dash anywhere in the deck.

    Written for m03, lost across module boundaries. Recovered 2026-08-06.
    Beside a formula it reads as a minus sign. The lecturer asked for them out.
    """
    with open(deck) as fh:
        text = fh.read()
    return [line.strip()[:60] for line in text.splitlines() if "\u2014" in line]


# ── Measurement ─────────────────────────────────────────────────────────────

def smallest_text(src_path):
    """Smallest glyph x-height in a figure, in source pixels."""
    im = np.array(Image.open(src_path).convert("L"))
    heights = []
    for h, w, area in components(im < INK, min_px=12, step=1):
        if 4 <= h <= 60 and 2 <= w <= 60 and 0.12 < area / (h * w) < 0.90 \
                and 0.45 <= h / w <= 4.0:
            heights.append(h)
    if len(heights) < 3:
        return None
    counts = {}
    for h in heights:
        for k in (h - 1, h, h + 1):
            counts[k] = counts.get(k, 0) + 1
    real = [h for h in sorted(set(heights)) if counts.get(h, 0) >= 3]
    if not real:
        return None
    max_count = max(counts[h] for h in real)
    real = [h for h in real if counts[h] >= max(3, 0.2 * max_count)]
    return float(real[0]) if real else None


def drawing_extent(src_path, container_w, hcap=None, max_fig_h=380):
    """How big the drawing lands on the slide, and what share of its box it fills."""
    im = np.array(Image.open(src_path).convert("L"))
    ys, xs = np.where(im < INK)
    if len(ys) == 0:
        return None
    ink_w = xs.max() - xs.min() + 1
    ink_h = ys.max() - ys.min() + 1
    sh, sw = im.shape
    scale = min(container_w / sw, (hcap or max_fig_h) / sh, 1.0)
    frac = (ink_w * ink_h) / float(sw * sh)
    return ink_w * scale, ink_h * scale, sw * scale, sh * scale, frac


def slides_with_figures(deck, fig_h=None):
    """Map slide number -> figure filename, from the deck itself."""
    if fig_h is None:
        fig_h = {"": 380, "tight": 320, "stack": 190, "tall": 400}
    with open(deck) as fh:
        text = fh.read()
    parts = text.split("\n---\n")
    out = {}
    for i, chunk in enumerate(parts[1:], start=1):
        hits = re.findall(r"!\[[^\]]*\]\((figures/[^)]+)\)", chunk)
        if hits:
            mod = ""
            for m in fig_h:
                if m and f'class="fig {m}"' in chunk:
                    mod = m
            out[i] = (hits, 'class="cols"' in chunk, fig_h[mod])
    return out


# ── Main entry point ────────────────────────────────────────────────────────

def run(deck, node_fills=None, fig_h=None, exempt_figures=None,
        col_w=COL_W, full_img_w=FULL_IMG_W, content_bottom=CONTENT_BOTTOM):
    """Run all render checks. Call from per-module check_render.py.

    Args:
        deck: path to the Marp deck markdown file
        node_fills: list of (R,G,B) tuples for node disc detection. Opt-in:
            this check only applies to decks with circular node-link diagrams
            (network/graph figures, flowcharts with round nodes, etc.). Leave
            unset (or pass []) to skip it entirely — the default is off.
        fig_h: dict of figure height caps by modifier class
        exempt_figures: filenames to skip (historical photos, etc.)
        col_w: column container width in px
        full_img_w: full-width image cap in px
    """
    if node_fills is None:
        node_fills = []
    if fig_h is None:
        fig_h = {"": 380, "tight": 320, "stack": 190, "tall": 400}
    if exempt_figures is None:
        exempt_figures = []
    max_fig_h = fig_h[""]

    files = sorted(glob.glob(SLIDES))
    if not files:
        sys.exit("no rendered slides found — run marp first")
    figs = slides_with_figures(deck, fig_h)

    fails = []
    warns = []
    diams = []

    # Source-level gates
    for kind, snippet in figcaption_math(deck):
        fails.append(f"deck: math inside a {kind} — KaTeX will print it literally: {snippet!r}")

    for slide_n, word, fig_src in caption_colours(deck):
        fails.append(
            f"slide {slide_n:03d}: figcaption names \"{word}\" but "
            f"{fig_src} has fewer than 200 pixels of it — stale caption?"
        )

    for line in em_dashes(deck):
        fails.append(f"deck: em-dash found (reads as minus beside math): {line!r}")

    for n, src, container, hcap, mod in figure_containers(deck, col_w, full_img_w, fig_h):
        try:
            sw, sh = Image.open(src).size
        except OSError:
            fails.append(f"slide {n:03d}: {src} is missing")
            continue
        authored = col_w if sw <= 3000 else full_img_w
        if authored != container:
            fails.append(
                f"slide {n:03d}: {src} is authored {sw}px wide (for a {authored}px "
                f"container) but used in a {container}px one — it renders at "
                f"{container / authored:.0%} of its intended scale")
        elif hcap / sh < container / sw:
            fails.append(
                f"slide {n:03d}: {src} is {sh}px tall, so the "
                f"{('`fig ' + mod + '`') if mod else '`fig`'} height cap of {hcap}px "
                f"binds before the width does — it lands "
                f"{min(container / sw, hcap / sh) * 4:.2f} slide px per bp instead of "
                f"{container * 4 / sw:.2f}, and the in-figure type shrinks with it")

    # Render-level gates
    for path in files:
        n = int(re.search(r"(\d+)", path.split("/")[-1]).group(1))
        im = Image.open(path).convert("RGB")
        rgb = np.array(im)
        gray = np.array(im.convert("L"))

        below = gray[content_bottom:, :1080] < INK
        if below.sum() > 8:
            rows = np.where(below.any(axis=1))[0]
            fails.append(
                f"slide {n:03d}: content runs to y={content_bottom + rows.max()} "
                f"in a 720px frame — the bottom of the slide is cut off"
            )

        d = node_discs(rgb, node_fills)
        if d:
            diams += d
            lo, hi = min(d), max(d)
            if lo < NODE_MIN_PX or hi > NODE_MAX_PX:
                fails.append(
                    f"slide {n:03d}: node diameter {lo:.0f}-{hi:.0f}px "
                    f"outside {NODE_MIN_PX}-{NODE_MAX_PX}px"
                )

        if n in figs:
            srcs, in_cols, hcap_val = figs[n]
            for src in srcs:
                container = col_w if in_cols else full_img_w
                if not os.path.exists(src):
                    fails.append(f"slide {n:03d}: {src} is referenced by the deck but "
                                 f"does not exist")
                    continue
                ext = drawing_extent(src, container, hcap_val, max_fig_h)
                if ext is None:
                    fails.append(f"slide {n:03d}: {src} is blank")
                    continue
                dw, dh, box_w, box_h, frac = ext
                name = src.split("/")[-1]
                if name in exempt_figures:
                    continue
                im_src = np.array(Image.open(src).convert("L"))
                sh, sw = im_src.shape
                scale = min(container / sw, hcap_val / sh, 1.0)

                xh = smallest_text(src)
                if xh is not None and xh * scale < MIN_TEXT_XHEIGHT:
                    warns.append(
                        f"slide {n:03d} ({name}): smallest ink measures {xh * scale:.0f}px "
                        f"x-height — check it is a glyph and not a dash before acting"
                    )

                has_nodes = bool(node_discs(np.array(Image.open(src).convert("RGB")), node_fills))
                if not has_nodes and max(dw, dh) < MIN_DRAWING_PX:
                    fails.append(
                        f"slide {n:03d} ({name}): drawing lands {dw:.0f}x{dh:.0f}px — "
                        f"too small to read regardless of how much of its box it fills"
                    )

                ys, xs = np.where(im_src < INK)
                mx = 1 - (xs.max() - xs.min() + 1) / sw
                my = 1 - (ys.max() - ys.min() + 1) / sh
                if max(mx, my) > MAX_AXIS_MARGIN:
                    axis, val = ("horizontal", mx) if mx > my else ("vertical", my)
                    warns.append(
                        f"slide {n:03d} ({name}): {val:.0%} {axis} white margin baked "
                        f"into the canvas"
                    )
                if frac < INK_FRACTION_FAIL:
                    fails.append(
                        f"slide {n:03d} ({name}): drawing lands {dw:.0f}x{dh:.0f}px = "
                        f"{frac:.0%} of its {box_w:.0f}x{box_h:.0f} box — the deck is scaling "
                        f"white margin; crop the canvas to its ink"
                    )
                elif frac < INK_FRACTION_WANT:
                    warns.append(f"slide {n:03d} ({name}): drawing fills {frac:.0%} of its box")

    print(f"checked {len(files)} rendered slides")
    if diams:
        print(
            f"node diameter: {min(diams):.0f}-{max(diams):.0f}px "
            f"(spread {max(diams)/min(diams):.1f}x) across {len(diams)} discs"
        )
    if warns:
        print(f"\n{len(warns)} warning(s):")
        for w in warns:
            print("  " + w)
    if fails:
        print(f"\n{len(fails)} problem(s) on the rendered slides:\n")
        for f in fails:
            print("  " + f)
        sys.exit(1)
    print("\nall checks pass")


if __name__ == "__main__":
    # Standalone test: find the deck in cwd
    candidates = [f for f in os.listdir(".") if f.endswith(".md")
                  and not f.startswith(("README", "REVIEW", "FIXES",
                                        "DECK_SPEC", "FIGURE_SPEC",
                                        "CHECKPOINT", "IMPROVEMENT"))]
    deck = None
    for c in candidates:
        with open(c) as fh:
            if "marp" in fh.read(500):
                deck = c
                break
    if not deck:
        sys.exit("usage: run from a module directory with a Marp deck")
    run(deck=deck)
