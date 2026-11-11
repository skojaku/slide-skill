#!/usr/bin/env python3
"""Check a slide-math deck in a real browser and list what is wrong, slide by slide.

    python3 ~/.claude/skills/slide-math/tools/check.py deck.md            # report, exit 1 on errors
    python3 ~/.claude/skills/slide-math/tools/check.py deck.md --boxes    # also print the box of
                                                                          # every element with an id

Marp clips whatever runs past the slide, silently; this tool measures the laid-out page.
ERROR (exit 1):
  - content below the bottom margin (y > 668 px, or into the .ref line), or past the right edge
  - a title longer than one line
  - a formula, code block or table wider than its box
  - a KaTeX error, or LaTeX printed as text (math inside raw HTML that Marp did not render)
  - an image that did not load
warn (exit 0):
  - a lead longer than two lines, a bullet longer than two lines
  - more than 130 words of text on a slide (formulas and code not counted)

Needs marp-cli and Chrome or Chromium (set SLIDE_MATH_CHROME to override the path).
Pure standard library.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
CONFIG = SKILL / "marp.config.mjs"

CHROMES = [
    os.environ.get("SLIDE_MATH_CHROME", ""),
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    shutil.which("google-chrome") or "",
    shutil.which("chromium") or "",
    shutil.which("chromium-browser") or "",
]

PROBE = r"""
<script>
(async () => {
  try { await document.fonts.ready; } catch (e) {}
  await new Promise(r => setTimeout(r, 300));
  const W = 1280, H = 720, BOTTOM = 668, RIGHT = 1256, LEFT = 18;
  const out = [];
  const secs = [...document.querySelectorAll('svg[data-marpit-svg] > foreignObject > section')];
  const desc = el => {
    let s = el.tagName.toLowerCase();
    if (el.classList.length) s += '.' + [...el.classList].join('.');
    if (el.dataset && el.dataset.tab) s += `[data-tab="${el.dataset.tab}"]`;
    const t = (el.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 50);
    return t ? `${s} "${t}"` : s;
  };
  secs.forEach((sec, i) => {
    const R = sec.getBoundingClientRect(), k = R.width / W;
    const rel = r => ({x: (r.left - R.left) / k, y: (r.top - R.top) / k, r: (r.right - R.left) / k,
                       b: (r.bottom - R.top) / k, w: r.width / k, h: r.height / k});
    const cls = sec.className || '';
    const special = /\b(title|divider|agenda)\b/.test(cls);
    const errors = [], warns = [], boxes = [];
    const exempt = el => el.closest('header, footer, .ref, svg.overlay, .art, .katex, mjx-container');
    const h2 = sec.querySelector(':scope > h2');
    if (h2 && !special && h2.scrollWidth > h2.clientWidth + 1)
      errors.push(`title longer than one line (${Math.round(h2.scrollWidth)} px of ${h2.clientWidth}): shorten it`);
    // bottom limit: the .ref line if there is one
    let limit = special ? H - 10 : BOTTOM;
    const ref = sec.querySelector(':scope > .ref');
    if (ref) limit = Math.min(limit, rel(ref.getBoundingClientRect()).y - 6);
    const reported = new Set();
    for (const el of sec.querySelectorAll('*')) {
      if (exempt(el) && !el.matches('.katex-display, .katex-display *')) continue;
      if (el.closest('.katex-display') && !el.matches('.katex-display')) continue;
      const cs = getComputedStyle(el);
      if (cs.position === 'absolute' && el.parentElement === sec) continue;
      const r = rel(el.getBoundingClientRect());
      if (r.w < 1 || r.h < 1) continue;
      let anc = el.parentElement, skip = false;
      while (anc && anc !== sec) { if (reported.has(anc)) { skip = true; break; } anc = anc.parentElement; }
      if (skip) continue;
      if (r.b > limit + 0.5) { errors.push(`runs ${Math.ceil(r.b - limit)} px below the bottom margin: ${desc(el)}`); reported.add(el); }
      else if (r.r > RIGHT + 0.5) { errors.push(`runs ${Math.ceil(r.r - RIGHT)} px past the right margin: ${desc(el)}`); reported.add(el); }
      else if (r.x < LEFT - 0.5) { errors.push(`starts ${Math.ceil(LEFT - r.x)} px left of the margin: ${desc(el)}`); reported.add(el); }
    }
    for (const el of sec.querySelectorAll('pre, .katex-display, .box, .cols > *, .split > *, td, .eqrow')) {
      if (el.scrollWidth > el.clientWidth + 2 && getComputedStyle(el).overflowX !== 'visible')
        errors.push(`content wider than its container by ${el.scrollWidth - el.clientWidth} px: ${desc(el)}`);
    }
    for (const el of sec.querySelectorAll('.katex-display')) {
      const p = el.parentElement.closest('.box, .cols > *, .split > *, section');
      const r = rel(el.querySelector('.katex-html, .katex').getBoundingClientRect()), q = rel(p.getBoundingClientRect());
      if (r.r > q.r + 1) errors.push(`formula ${Math.ceil(r.r - q.r)} px wider than its box: ${desc(el)}`);
    }
    for (const el of sec.querySelectorAll('.katex-error'))
      errors.push(`KaTeX error: ${(el.getAttribute('title') || '').slice(0, 120)}`);
    const walker = document.createTreeWalker(sec, NodeFilter.SHOW_TEXT);
    let n;
    while ((n = walker.nextNode())) {
      const p = n.parentElement;
      // not 'svg': Marp wraps every slide in an <svg>; only overlays are skipped
      if (p.closest('.katex, pre, code, svg.overlay, script, style')) continue;
      const t = n.textContent;
      if (/\$[^$\s][^$]*\$|\\(frac|sum|mathbf|boldsymbol|vb|hl|begin|left|right|partial)\b/.test(t))
        errors.push(`LaTeX printed as text (math inside raw HTML is not rendered; put a blank line after the opening tag): "${t.trim().slice(0, 60)}"`);
    }
    for (const img of sec.querySelectorAll('img'))
      if (img.complete && img.naturalWidth === 0) errors.push(`image did not load: ${img.getAttribute('src')}`);
    if (!special && h2) {
      const lead = sec.querySelector(':scope > h2 + p');
      if (lead) {
        const lh = parseFloat(getComputedStyle(lead).lineHeight) || 33;
        const lines = Math.round(lead.getBoundingClientRect().height / k / lh);
        if (lines > 2) warns.push(`lead has ${lines} lines (keep it to one sentence, two lines at most)`);
      }
    }
    for (const li of sec.querySelectorAll('li')) {
      let h = li.getBoundingClientRect().height;
      for (const sub of li.querySelectorAll(':scope > ul, :scope > ol')) h -= sub.getBoundingClientRect().height;
      const lh = parseFloat(getComputedStyle(li).lineHeight) || 31;
      if (h / k / lh > 2.4) warns.push(`bullet longer than two lines: "${li.firstChild && li.textContent.trim().slice(0, 50)}"`);
    }
    const clone = sec.cloneNode(true);
    clone.querySelectorAll('.katex, pre, code, header, footer, .ref, svg, script, style').forEach(e => e.remove());
    const words = (clone.textContent.match(/[A-Za-z0-9][\w'’-]*/g) || []).length;
    if (words > 130) warns.push(`${words} words of text (aim for at most 130; formulas and code not counted)`);
    for (const el of sec.querySelectorAll('[id]')) {
      if (el.closest('svg.overlay') || /^(SECTION|H[1-6])$/.test(el.tagName)) continue;
      const r = rel(el.getBoundingClientRect());
      boxes.push({id: el.id, x: Math.round(r.x), y: Math.round(r.y), r: Math.round(r.r), b: Math.round(r.b),
                  cx: Math.round((r.x + r.r) / 2), cy: Math.round((r.y + r.b) / 2)});
    }
    out.push({n: i + 1, cls, title: h2 ? h2.textContent.trim() : '', words, errors, warns, boxes});
  });
  const pre = document.createElement('pre');
  pre.id = '__slidemath_report';
  pre.textContent = JSON.stringify(out);
  document.body.appendChild(pre);
})();
</script>
"""


def find_chrome() -> str:
    for c in CHROMES:
        if c and Path(c).exists():
            return c
    sys.exit("check.py: no Chrome/Chromium found; set SLIDE_MATH_CHROME to its executable")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("deck", type=Path)
    ap.add_argument("--boxes", action="store_true", help="print the box of every element with an id")
    ap.add_argument("--json", action="store_true", help="print the raw report as JSON")
    args = ap.parse_args()
    deck = args.deck.resolve()
    if not deck.exists():
        sys.exit(f"check.py: {deck} not found")
    # The HTML must sit next to the deck so that relative image paths resolve.
    tmp = deck.parent / f".{deck.stem}.check.html"
    try:
        res = subprocess.run(
            ["marp", "--config", str(CONFIG), "--no-stdin", "--template", "bare", "--html",
             str(deck), "-o", str(tmp)], capture_output=True, text=True)
        if res.returncode != 0 or not tmp.exists():
            print(res.stdout, res.stderr, sep="\n")
            return 2
        page = tmp.read_text()
        page = page.replace("</body>", PROBE + "</body>") if "</body>" in page else page + PROBE
        tmp.write_text(page)
        with tempfile.TemporaryDirectory() as prof:
            dom = subprocess.run(
                [find_chrome(), "--headless=new", "--disable-gpu", "--no-first-run", "--hide-scrollbars",
                 f"--user-data-dir={prof}", "--allow-file-access-from-files", "--window-size=1280,720",
                 "--virtual-time-budget=15000", "--dump-dom", tmp.as_uri()],
                capture_output=True, text=True, timeout=180).stdout
    finally:
        tmp.unlink(missing_ok=True)
    m = re.search(r'<pre id="__slidemath_report">(.*?)</pre>', dom, re.S)
    if not m:
        print("check.py: the browser produced no report (did the page load?)")
        return 2
    report = json.loads(html.unescape(m.group(1)))
    if args.json:
        print(json.dumps(report, indent=1))
    n_err = n_warn = 0
    for s in report:
        lines = [f"  ERROR  {e}" for e in s["errors"]] + [f"  warn   {w}" for w in s["warns"]]
        if args.boxes and s["boxes"]:
            lines += [f"  box    #{b['id']}: x {b['x']}-{b['r']}, y {b['y']}-{b['b']} (centre {b['cx']},{b['cy']})"
                      for b in s["boxes"]]
        n_err += len(s["errors"])
        n_warn += len(s["warns"])
        if lines:
            print(f"slide {s['n']}: {s['title'] or '(' + s['cls'] + ')'}  [{s['words']} words]")
            print("\n".join(lines))
    print(f"\n{len(report)} slides, {n_err} errors, {n_warn} warnings")
    return 1 if n_err else 0


if __name__ == "__main__":
    sys.exit(main())
