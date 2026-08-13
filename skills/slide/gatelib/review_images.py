#!/usr/bin/env python3
"""Prepare token-efficient images for LLM slide review.

Three strategies, in order of token savings:

1. **Downscale**: 1280x720 → 640x360. Claude's image token cost scales with
   pixel count (~width*height/750). A 640x360 slide costs ~307 tokens vs ~1,229
   at full size — 75% saving per slide. Text at 30px body remains readable at
   half scale (15px effective).

2. **Contact sheet**: tile N slides into one image. One image read instead of N.
   A 3x3 grid of 640x360 slides at 1920x1080 costs ~2,765 tokens for 9 slides
   (~307/slide) — same per-slide cost as individual downscaled reads, but saves
   N-1 tool call round-trips and their context overhead.

3. **Changed-only**: combine with check_deck.py's render hash to only prepare
   images for slides that changed since last review.

Usage:
    python3 -m gatelib.review_images prepare <module_dir> [--changed-only] [--contact-sheet N]
    python3 -m gatelib.review_images clean <module_dir>
"""

import glob
import os
import re
import sys

from PIL import Image


def downscale_slides(module_dir, scale=0.5, out_dir=None):
    """Downscale rendered slide PNGs for token-efficient review.

    Args:
        module_dir: path to module directory (e.g. docs/slide/new/m01)
        scale: downscale factor (0.5 = half size, ~75% token saving)
        out_dir: output directory (default: review/small/)

    Returns:
        list of output paths
    """
    review_dir = os.path.join(module_dir, "review")
    if out_dir is None:
        out_dir = os.path.join(review_dir, "small")
    os.makedirs(out_dir, exist_ok=True)

    slides = sorted(glob.glob(os.path.join(review_dir, "slide.*.png")))
    if not slides:
        print("no rendered slides found — run marp first", file=sys.stderr)
        return []

    out_paths = []
    for path in slides:
        name = os.path.basename(path)
        out_path = os.path.join(out_dir, name)

        # Skip if already downscaled and source hasn't changed
        if os.path.exists(out_path):
            if os.path.getmtime(out_path) >= os.path.getmtime(path):
                out_paths.append(out_path)
                continue

        im = Image.open(path)
        w, h = im.size
        new_w, new_h = int(w * scale), int(h * scale)
        im_small = im.resize((new_w, new_h), Image.LANCZOS)
        im_small.save(out_path, optimize=True)
        out_paths.append(out_path)

    return out_paths


def contact_sheet(image_paths, cols=3, out_path=None):
    """Tile multiple slide images into one contact sheet.

    Args:
        image_paths: list of image paths to tile
        cols: number of columns in the grid
        out_path: output path (default: review/contact_sheet.png)

    Returns:
        output path
    """
    if not image_paths:
        return None

    # Load all images to get dimensions
    images = []
    for p in image_paths:
        im = Image.open(p)
        images.append((p, im))

    w, h = images[0][1].size
    rows = (len(images) + cols - 1) // cols

    # Add slide number labels
    label_h = 30  # px for slide number label
    sheet_w = cols * w
    sheet_h = rows * (h + label_h)

    sheet = Image.new("RGB", (sheet_w, sheet_h), (255, 255, 255))

    from PIL import ImageDraw
    draw = ImageDraw.Draw(sheet)

    for idx, (path, im) in enumerate(images):
        row = idx // cols
        col = idx % cols
        x = col * w
        y = row * (h + label_h)

        # Extract slide number
        m = re.search(r"(\d+)", os.path.basename(path))
        num = m.group(1) if m else str(idx + 1)

        # Draw label
        draw.text((x + 10, y + 5), f"slide {num}", fill=(0, 0, 0))

        # Paste image
        sheet.paste(im, (x, y + label_h))

    if out_path is None:
        out_path = os.path.join(os.path.dirname(image_paths[0]), "contact_sheet.png")
    sheet.save(out_path, optimize=True)
    return out_path


def changed_slides_only(module_dir, all_paths):
    """Filter to only slides that changed since last hash save.

    Uses check_deck.py's render hash comparison.
    """
    try:
        from .check_deck import changed_slides
    except ImportError:
        # Standalone usage
        sys.path.insert(0, os.path.join(module_dir, ".."))
        from gatelib.check_deck import changed_slides

    changed = changed_slides(module_dir)
    if not changed:
        return all_paths  # first round: all slides

    filtered = []
    for p in all_paths:
        m = re.search(r"(\d+)", os.path.basename(p))
        if m and int(m.group(1)) in changed:
            filtered.append(p)
    return filtered


def estimate_tokens(image_paths):
    """Estimate Claude image token cost for a set of images."""
    total = 0
    for p in image_paths:
        im = Image.open(p)
        w, h = im.size
        total += (w * h) // 750
    return total


def prepare(module_dir, changed_only=False, contact=False, cols=3, scale=0.5):
    """Main entry: prepare review images.

    Returns dict with paths and token estimates.
    """
    # Downscale all slides
    small_paths = downscale_slides(module_dir, scale=scale)
    if not small_paths:
        return {"error": "no slides found"}

    # Filter to changed only if requested
    if changed_only:
        review_paths = changed_slides_only(module_dir, small_paths)
    else:
        review_paths = small_paths

    # Token estimates
    full_paths = sorted(glob.glob(os.path.join(module_dir, "review", "slide.*.png")))
    full_tokens = estimate_tokens(full_paths)
    small_tokens = estimate_tokens(small_paths)
    review_tokens = estimate_tokens(review_paths)

    result = {
        "total_slides": len(small_paths),
        "review_slides": len(review_paths),
        "full_tokens": full_tokens,
        "small_tokens": small_tokens,
        "review_tokens": review_tokens,
        "savings_pct": round((1 - review_tokens / full_tokens) * 100) if full_tokens else 0,
        "paths": review_paths,
    }

    # Contact sheet if requested
    if contact and review_paths:
        sheet_path = contact_sheet(review_paths, cols=cols)
        if sheet_path:
            sheet_tokens = estimate_tokens([sheet_path])
            result["contact_sheet"] = sheet_path
            result["contact_tokens"] = sheet_tokens

    return result


def clean(module_dir):
    """Remove downscaled images."""
    small_dir = os.path.join(module_dir, "review", "small")
    if os.path.isdir(small_dir):
        import shutil
        shutil.rmtree(small_dir)
        print(f"removed {small_dir}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Prepare token-efficient review images")
    parser.add_argument("command", choices=["prepare", "clean"])
    parser.add_argument("module_dir", help="module directory (e.g. docs/slide/new/m01)")
    parser.add_argument("--changed-only", action="store_true",
                        help="only prepare images for slides that changed since last review")
    parser.add_argument("--contact-sheet", action="store_true",
                        help="create a contact sheet of review images")
    parser.add_argument("--cols", type=int, default=3, help="contact sheet columns")
    parser.add_argument("--scale", type=float, default=0.5, help="downscale factor")
    args = parser.parse_args()

    if args.command == "clean":
        clean(args.module_dir)
    else:
        result = prepare(
            args.module_dir,
            changed_only=args.changed_only,
            contact=args.contact_sheet,
            cols=args.cols,
            scale=args.scale,
        )
        if "error" in result:
            print(result["error"], file=sys.stderr)
            sys.exit(1)
        print(f"slides: {result['review_slides']}/{result['total_slides']} to review")
        print(f"tokens: ~{result['review_tokens']:,} (vs ~{result['full_tokens']:,} full-size)")
        print(f"savings: {result['savings_pct']}%")
        if "contact_sheet" in result:
            print(f"contact sheet: {result['contact_sheet']} (~{result['contact_tokens']:,} tokens)")
