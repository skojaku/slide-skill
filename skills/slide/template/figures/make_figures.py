"""Build every figure of this deck:  python3 figures/make_figures.py  (from the deck directory).

See ~/.claude/skills/slide/FIGURES.md, and gallery/figures/make_figures.py in the skill for
one example of each figure type.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".claude/skills/slide/figkit"))
from figkit import P, arrow, brace, build, hrule_axis, label, lineplot, node, pin, raw, vecdots, zoom  # noqa: E402,F401

OUT = Path(__file__).resolve().parent


def example():
    # the entries of one vector as dots; the entry the slide is about on a lavender band
    build("example", vecdots([0.5, -0.8, 2.6, 0.2, -1.2, 1.1, None, -0.6],
                             labels=["1", "2", "3", "4", "5", "6", r"\cdots", "K"],
                             highlight=[2], yticks=[-1, 0, 1, 2], unit=40, step=34),
          outdir=OUT)


if __name__ == "__main__":
    example()
    print("figures written to", OUT)
