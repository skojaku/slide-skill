#!/usr/bin/env python3
"""Auto-fix mechanical issues in slide deck markdown.

Fixes applied (in order):
    1. Fragment syntax: convert static `-` bullets to `*` fragments
       when slide already has fragments
    2. KaTeX in HTML: strip $ delimiters inside <figcaption> and <div>
    3. Trailing whitespace on lines
    4. Missing demo link: move URL from speaker note to slide as <a> tag

NOT fixed (requires LLM judgment):
    - Answer leaks on question slides
    - Figure reuse with different captions
    - Deck structure (opening with definitions)
    - Bullet count > 4 (requires content splitting decision)
"""

import re
import sys


def fix_fragment_syntax(text):
    """Convert static `-` bullets to `*` fragments on slides that already
    have fragments. Mixed syntax causes inconsistent reveal behavior."""
    fixes = []
    slides = text.split("\n---\n")
    for i, chunk in enumerate(slides):
        stars = len(re.findall(r"^\* ", chunk, re.M))
        dashes = len(re.findall(r"^- ", chunk, re.M))
        if stars > 0 and dashes > 0:
            new_chunk = re.sub(r"^(-) ", r"* ", chunk, flags=re.M)
            if new_chunk != chunk:
                slides[i] = new_chunk
                fixes.append(f"slide {i}: converted {dashes} static bullets to fragments")
    return "\n---\n".join(slides), fixes


def fix_katex_in_html(text):
    """Strip $ delimiters inside <figcaption> and <div> blocks.
    KaTeX renders literally inside raw HTML in Marp."""
    fixes = []

    def strip_dollars(m):
        inner = m.group(0)
        new = inner.replace("$", "")
        if new != inner:
            fixes.append("stripped KaTeX $ from HTML block")
        return new

    # <figcaption>...</figcaption>
    new_text = re.sub(
        r"<figcaption>.*?</figcaption>",
        strip_dollars,
        text,
        flags=re.S,
    )
    # <div class="steps-list">...</div>
    new_text = re.sub(
        r'<div class="steps-list">.*?</div>',
        strip_dollars,
        new_text,
        flags=re.S,
    )
    return new_text, fixes


def fix_trailing_whitespace(text):
    """Remove trailing whitespace from lines."""
    lines = text.split("\n")
    fixed = 0
    for i, line in enumerate(lines):
        stripped = line.rstrip()
        if stripped != line:
            lines[i] = stripped
            fixed += 1
    fixes = [f"removed trailing whitespace from {fixed} lines"] if fixed else []
    return "\n".join(lines), fixes


def fix_demo_links(text):
    """Move URLs from speaker notes to slide as clickable links.

    If a slide's speaker notes contain a URL but the slide body has no <a> tag,
    add the URL as a link at the bottom of the slide body.
    """
    fixes = []
    slides = text.split("\n---\n")
    for i, chunk in enumerate(slides):
        # Find speaker notes
        notes = re.findall(r"<!--\s*(.*?)-->", chunk, re.S)
        note_urls = []
        for note in notes:
            note_urls.extend(re.findall(r"https?://\S+", note))

        if not note_urls:
            continue

        # Check if slide body already has a link
        body = re.sub(r"<!--.*?-->", "", chunk, flags=re.S)
        has_href = bool(re.search(r'href="http', body))
        if has_href:
            continue

        # Add link before the first speaker note
        for url in note_urls:
            # Clean URL (remove trailing punctuation from note)
            url = url.rstrip(".,;:)")
            link = f'\n\n<a href="{url}">Try it →</a>\n'
            # Insert before first <!--
            insert_pos = chunk.find("<!--")
            if insert_pos > 0:
                chunk = chunk[:insert_pos].rstrip() + link + "\n" + chunk[insert_pos:]
                fixes.append(f"slide {i}: added link {url[:50]}... from speaker note")
        slides[i] = chunk

    return "\n---\n".join(slides), fixes


def fix_all(deck_path, dry_run=False):
    """Apply all mechanical fixes to a deck.

    Args:
        deck_path: path to the deck .md file
        dry_run: if True, report fixes without writing

    Returns:
        list of fix descriptions
    """
    with open(deck_path) as fh:
        original = fh.read()

    text = original
    all_fixes = []

    fixers = [
        ("fragment syntax", fix_fragment_syntax),
        ("KaTeX in HTML", fix_katex_in_html),
        ("trailing whitespace", fix_trailing_whitespace),
        ("demo links", fix_demo_links),
    ]

    for name, fn in fixers:
        text, fixes = fn(text)
        if fixes:
            for f in fixes:
                all_fixes.append(f"[{name}] {f}")

    if text != original and not dry_run:
        with open(deck_path, "w") as fh:
            fh.write(text)

    return all_fixes


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("deck", help="deck .md file")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    fixes = fix_all(args.deck, dry_run=args.dry_run)
    if fixes:
        for f in fixes:
            print(f"  {f}")
        print(f"\n{len(fixes)} fix(es) {'(dry run)' if args.dry_run else 'applied'}")
    else:
        print("nothing to fix")
