#!/usr/bin/env python3
"""Contact sheets of rendered slides, 3 x 3 per sheet, numbered, for review.

    python3 sheet.py review/png review/sheet      # -> review/sheet-1.png, sheet-2.png, ...

Needs Pillow. Each slide is shown at 640 x 360; its number is printed in a strip above it, so
nothing on the slide is covered.
"""
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw

src, dst = Path(sys.argv[1]), sys.argv[2]
files = sorted(src.glob("*.png"), key=lambda p: int(re.findall(r"(\d+)\.png$", p.name)[0]))
W, H, PAD, STRIP, COLS, ROWS = 640, 360, 14, 18, 3, 3
for s in range(0, len(files), COLS * ROWS):
    chunk = files[s:s + COLS * ROWS]
    rows = (len(chunk) + COLS - 1) // COLS
    sheet = Image.new("RGB", (COLS * (W + PAD) + PAD, rows * (H + PAD + STRIP) + PAD), (120, 120, 120))
    d = ImageDraw.Draw(sheet)
    for j, f in enumerate(chunk):
        im = Image.open(f).convert("RGB").resize((W, H), Image.LANCZOS)
        x, y = PAD + (j % COLS) * (W + PAD), PAD + (j // COLS) * (H + PAD + STRIP)
        n = int(re.findall(r"(\d+)\.png$", f.name)[0])
        d.text((x + 2, y + 3), f"slide {n}", fill=(255, 255, 255))
        sheet.paste(im, (x, y + STRIP))
    out = f"{dst}-{s // (COLS * ROWS) + 1}.png"
    sheet.save(out)
    print(out)
