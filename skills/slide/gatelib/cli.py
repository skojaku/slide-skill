#!/usr/bin/env python3
"""deckgate — slide deck QA pipeline.

Single entry point for all automated slide checks and fixes.

Usage:
    deckgate check <module_dir>           # run all checks (render + source)
    deckgate check-render <module_dir>    # pixel-level checks only
    deckgate check-deck <module_dir>      # source-level checks only
    deckgate fix <module_dir>             # auto-fix mechanical issues
    deckgate prepare <module_dir>         # prepare review images
    deckgate review <module_dir>          # full review pipeline
    deckgate render <module_dir>          # render deck + run checks

Exit codes:
    0 — all checks pass / fixes applied
    1 — blockers or majors found
    2 — usage error
"""

import argparse
import os
import re
import subprocess
import sys


# ── Module discovery ─────────────────────────────────────────────────────────

def find_deck(module_dir):
    """Find the deck markdown file in a module directory."""
    candidates = []
    for f in os.listdir(module_dir):
        if not f.endswith(".md"):
            continue
        if f.startswith(("README", "REVIEW", "FIXES", "DECK_SPEC",
                         "FIGURE_SPEC", "CHECKPOINT", "IMPROVEMENT")):
            continue
        path = os.path.join(module_dir, f)
        try:
            with open(path) as fh:
                head = fh.read(500)
            if "marp" in head:
                candidates.append(f)
        except:
            pass
    if not candidates:
        return None
    return candidates[0]


def marp_render_cmd(deck_path, module_dir, out_pattern):
    """Build the marp CLI invocation, registering module_dir's theme.css if present.

    Without --theme-set, marp-cli silently falls back to its built-in default
    theme when a deck's `theme:` front matter names a theme it hasn't been told
    to load -- every theme.css rule (colours, fonts, custom layout blocks like
    .band/.steps-list) then goes missing with no error.
    """
    # --no-stdin: without it marp waits on stdin forever when not attached to a
    # terminal, which looks exactly like a slow render (REVIEW_PLAYBOOK.md).
    cmd = ["marp", deck_path, "--images", "png", "-o", out_pattern,
           "--allow-local-files", "--no-stdin"]
    theme_css = os.path.join(module_dir, "theme.css")
    if os.path.isfile(theme_css):
        cmd += ["--theme-set", theme_css]
    return cmd


def find_module_dir(path="."):
    """Resolve to a module directory containing a deck."""
    path = os.path.abspath(path)
    if os.path.isfile(path):
        path = os.path.dirname(path)
    deck = find_deck(path)
    if deck:
        return path
    # Try subdirectories
    for d in sorted(os.listdir(path)):
        sub = os.path.join(path, d)
        if os.path.isdir(sub) and find_deck(sub):
            return sub
    return None


# ── Subcommands ──────────────────────────────────────────────────────────────

def cmd_check(module_dir, args):
    """Run all checks."""
    from .check_deck import run as check_deck_run
    from .check_render import run as check_render_run

    deck = find_deck(module_dir)
    if not deck:
        print(f"no deck found in {module_dir}", file=sys.stderr)
        return 2

    deck_path = os.path.join(module_dir, deck)

    print("── source checks ──")
    try:
        check_deck_run(deck_path)
    except SystemExit as e:
        deck_code = e.code or 0

    print("\n── render checks ──")
    review_dir = os.path.join(module_dir, "review")
    if os.path.isdir(review_dir):
        # Import module-specific check_render if it exists
        module_script = os.path.join(module_dir, "check_render.py")
        if os.path.exists(module_script):
            r = subprocess.run(
                [sys.executable, os.path.abspath(module_script)],
                cwd=os.path.abspath(module_dir),
                capture_output=True, text=True
            )
            print(r.stdout)
            if r.stderr:
                print(r.stderr, file=sys.stderr)
            render_code = r.returncode
        else:
            render_code = 0
            print("(no check_render.py in module)")
    else:
        print("no review/ directory — run render first")
        render_code = 0

    return max(deck_code, render_code)


def cmd_check_render(module_dir, args):
    """Render checks only."""
    module_script = os.path.join(module_dir, "check_render.py")
    if not os.path.exists(module_script):
        print(f"no check_render.py in {module_dir}", file=sys.stderr)
        return 2
    r = subprocess.run([sys.executable, os.path.abspath(module_script)],
                        cwd=os.path.abspath(module_dir))
    return r.returncode


def cmd_check_deck(module_dir, args):
    """Source checks only."""
    from .check_deck import run
    deck = find_deck(module_dir)
    if not deck:
        print(f"no deck found in {module_dir}", file=sys.stderr)
        return 2
    try:
        run(os.path.join(module_dir, deck))
    except SystemExit as e:
        return e.code or 0
    return 0


def cmd_fix(module_dir, args):
    """Auto-fix mechanical issues."""
    from .fix_deck import fix_all
    deck = find_deck(module_dir)
    if not deck:
        print(f"no deck found in {module_dir}", file=sys.stderr)
        return 2

    deck_path = os.path.join(module_dir, deck)
    fixes = fix_all(deck_path, dry_run=args.dry_run)

    if not fixes:
        print("nothing to fix")
        return 0

    print(f"\n{len(fixes)} fix(es) {'(dry run)' if args.dry_run else 'applied'}:")
    for f in fixes:
        print(f"  {f}")
    return 0


def cmd_prepare(module_dir, args):
    """Prepare review images."""
    from .review_images import prepare
    result = prepare(
        module_dir,
        changed_only=args.changed_only,
        contact=args.contact_sheet,
        scale=args.scale,
    )
    if "error" in result:
        print(result["error"], file=sys.stderr)
        return 2

    print(f"slides: {result['review_slides']}/{result['total_slides']} to review")
    print(f"tokens: ~{result['review_tokens']:,} (vs ~{result['full_tokens']:,} full)")
    print(f"savings: {result['savings_pct']}%")
    if "contact_sheet" in result:
        print(f"contact: {result['contact_sheet']} (~{result['contact_tokens']:,} tokens)")

    # Print changed slide numbers for reviewer
    if args.changed_only and result["paths"]:
        nums = []
        for p in result["paths"]:
            m = re.search(r"(\d+)", os.path.basename(p))
            if m:
                nums.append(int(m.group(1)))
        print(f"changed: {sorted(nums)}")
    return 0


def cmd_render(module_dir, args):
    """Render deck and run checks."""
    deck = find_deck(module_dir)
    if not deck:
        print(f"no deck found in {module_dir}", file=sys.stderr)
        return 2

    deck_path = os.path.join(module_dir, deck)
    review_dir = os.path.join(module_dir, "review")
    os.makedirs(review_dir, exist_ok=True)

    # Render with marp
    out_pattern = os.path.join(review_dir, "slide.png")
    print(f"rendering {deck}...")
    r = subprocess.run(
        marp_render_cmd(deck_path, module_dir, out_pattern),
        capture_output=True, text=True
    )
    if r.returncode != 0:
        print(f"marp failed: {r.stderr}", file=sys.stderr)
        return 1
    print(f"rendered to {review_dir}/")

    # Run checks
    return cmd_check(module_dir, args)


def cmd_review(module_dir, args):
    """Full review pipeline: fix → render → check → prepare images."""
    print("═══ 1/4 auto-fix ═══")
    fix_code = cmd_fix(module_dir, args)

    print("\n═══ 2/4 render ═══")
    deck = find_deck(module_dir)
    deck_path = os.path.join(module_dir, deck)
    review_dir = os.path.join(module_dir, "review")
    os.makedirs(review_dir, exist_ok=True)
    out_pattern = os.path.join(review_dir, "slide.png")
    r = subprocess.run(
        marp_render_cmd(deck_path, module_dir, out_pattern),
        capture_output=True, text=True
    )
    if r.returncode != 0:
        print(f"marp failed: {r.stderr}", file=sys.stderr)
        return 1
    n_slides = len([f for f in os.listdir(review_dir) if f.startswith("slide.") and f.endswith(".png")])
    print(f"rendered {n_slides} slides")

    print("\n═══ 3/4 checks ═══")
    check_code = cmd_check(module_dir, args)

    print("\n═══ 4/4 prepare review images ═══")
    prepare_args = argparse.Namespace(
        changed_only=True,
        contact_sheet=n_slides <= 20,
        scale=0.5,
        dry_run=False,
    )
    cmd_prepare(module_dir, prepare_args)

    print("\n═══ summary ═══")
    if check_code == 0:
        print("all automated checks pass")
        print("next: LLM review of changed slides (Tier 1)")
    else:
        print("BLOCKERs or MAJORs remain — fix before LLM review")

    return check_code


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        prog="deckgate",
        description="slide deck QA pipeline",
    )
    parser.add_argument("--version", action="version", version="0.1.0")
    sub = parser.add_subparsers(dest="command", help="command")

    # check
    p = sub.add_parser("check", help="run all checks")
    p.add_argument("module_dir", nargs="?", default=".")

    # check-render
    p = sub.add_parser("check-render", help="pixel-level checks only")
    p.add_argument("module_dir", nargs="?", default=".")

    # check-deck
    p = sub.add_parser("check-deck", help="source-level checks only")
    p.add_argument("module_dir", nargs="?", default=".")

    # fix
    p = sub.add_parser("fix", help="auto-fix mechanical issues")
    p.add_argument("module_dir", nargs="?", default=".")
    p.add_argument("--dry-run", action="store_true", help="show fixes without applying")

    # prepare
    p = sub.add_parser("prepare", help="prepare review images")
    p.add_argument("module_dir", nargs="?", default=".")
    p.add_argument("--changed-only", action="store_true")
    p.add_argument("--contact-sheet", action="store_true")
    p.add_argument("--scale", type=float, default=0.5)

    # render
    p = sub.add_parser("render", help="render deck + run checks")
    p.add_argument("module_dir", nargs="?", default=".")

    # review
    p = sub.add_parser("review", help="full pipeline: fix → render → check → prepare")
    p.add_argument("module_dir", nargs="?", default=".")
    p.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 2

    module_dir = find_module_dir(args.module_dir)
    if not module_dir:
        print(f"no module found at {args.module_dir}", file=sys.stderr)
        return 2

    commands = {
        "check": cmd_check,
        "check-render": cmd_check_render,
        "check-deck": cmd_check_deck,
        "fix": cmd_fix,
        "prepare": cmd_prepare,
        "render": cmd_render,
        "review": cmd_review,
    }
    return commands[args.command](module_dir, args)


if __name__ == "__main__":
    sys.exit(main())
