#!/usr/bin/env python3
"""Source-level deck checks — no LLM, no render needed for most checks.

Imported by each module's thin check_deck.py, or run standalone.

Some checks read the markdown source; others check the render hashes for change
detection. Markdown-source table/column/code detectors were removed after review
showed zero markdown table syntax in any shipped deck — surviving L1/L2/L3
violations live inside figure PNGs, which only render review catches.

What this checks:
  - Question slide answer leak (substantive notes on question slides)
  - Figure reuse across non-adjacent slides with different captions
  - Fragmented list followed by paragraph (L5)
  - Bullet count > 4 (L4)
  - KaTeX in raw HTML blocks (figcaption, steps-list)
  - Demo link on slide vs speaker note only (S5a)
  - Fragment syntax consistency (* vs -)
  - Bold overuse
  - Deck structure: four-act arc heuristic (S1)
  - Stale render detection
  - Render hash change detection (for tiered review scoping)
"""

import hashlib
import json
import os
import re
import sys
from collections import Counter


# ── Parsing ──────────────────────────────────────────────────────────────────

def parse_deck(path):
    """Split deck into (front_matter, [slide_dicts])."""
    with open(path) as fh:
        text = fh.read()
    parts = re.split(r"\n---\n", text)
    front = parts[0]
    slides = []
    for i, chunk in enumerate(parts[1:], start=1):
        slides.append({
            "num": i,
            "raw": chunk,
            "title": extract_title(chunk),
            "figures": re.findall(r"!\[([^\]]*)\]\((figures/[^)]+)\)", chunk),
            "has_cols_text": bool(re.search(r'class="cols"', chunk)),
            "fragments": re.findall(r"^\* ", chunk, re.M),
            "bullets": re.findall(r"^- ", chunk, re.M),
            "notes": re.findall(r'class="note"', chunk),
            "figcaptions": re.findall(r"<figcaption>(.*?)</figcaption>", chunk, re.S),
            "is_part_divider": bool(re.search(r'class="(?:part|lead)"', chunk)),
            "is_question": is_question_slide(chunk),
            "has_figcaption_katex": has_katex_in_html(chunk),
            "has_href": bool(re.search(r'href="http', chunk)),
            "speaker_notes": extract_speaker_notes(chunk),
        })
    return front, slides


def extract_title(chunk):
    m = re.search(r"^##\s+(.+)", chunk, re.M)
    if m:
        return m.group(1).strip()
    m = re.search(r"^#\s+(.+)", chunk, re.M)
    if m:
        return m.group(1).strip()
    for line in chunk.strip().split("\n"):
        if line.strip() and not line.strip().startswith("<!--"):
            return line.strip()[:60]
    return "(untitled)"


def is_question_slide(chunk):
    indicators = [
        r"\?\s*$", r"Can you", r"What", r"How many", r"How would",
        r"Predict", r"Your turn", r"Guess", r"考えて", r"予想",
    ]
    body = re.sub(r"<!--.*?-->", "", chunk, flags=re.S)
    return any(re.search(pat, body) for pat in indicators)


def has_katex_in_html(chunk):
    html_blocks = re.findall(r"<figcaption>(.*?)</figcaption>", chunk, re.S)
    html_blocks += re.findall(r'<div class="steps-list">(.*?)</div>', chunk, re.S)
    return any("$" in b for b in html_blocks)


def extract_speaker_notes(chunk):
    return re.findall(r"<!--\s*(.*?)-->", chunk, re.S)


# ── Individual checks ────────────────────────────────────────────────────────

def check_question_answer_leak(slides):
    """Question slide must not contain the answer — anywhere on the slide.

    LIMITATION: this checks text content only. A graphical leak (figure drawing
    the answer to a later quiz) walks through this check without touching it.
    Scope: 'no banned text pattern in question slide; figure content not examined.'
    """
    findings = []
    for s in slides:
        if not s["is_question"]:
            continue
        for note_match in re.finditer(
            r'<div class="note">(.*?)</div>', s["raw"], re.S
        ):
            note_text = note_match.group(1).strip()
            words = len(note_text.split())
            if words > 15:
                findings.append(
                    f"slide {s['num']:03d} \"{s['title']}\" — N4a BLOCKER: "
                    f"question slide has a {words}-word note that may leak the answer. "
                    f"Move the answer to the next slide. "
                    f"[scope: text only; figure content not examined]"
                )
    return findings


def check_figure_reuse_different_captions(slides):
    """Same figure file used on non-adjacent slides with different captions.

    Exception: consecutive slides in a build sequence legitimately reuse figures.
    """
    fig_usage = {}
    for s in slides:
        for alt, fpath in s["figures"]:
            caption = s["figcaptions"][0] if s["figcaptions"] else ""
            if fpath not in fig_usage:
                fig_usage[fpath] = []
            fig_usage[fpath].append((s["num"], caption.strip()))

    findings = []
    for fpath, uses in fig_usage.items():
        if len(uses) < 2:
            continue
        captions = set(c for _, c in uses if c)
        if len(captions) <= 1:
            continue
        slide_nums = sorted(n for n, _ in uses)
        is_build = all(
            slide_nums[i + 1] - slide_nums[i] <= 2
            for i in range(len(slide_nums) - 1)
        )
        if is_build and len(captions) <= 2:
            continue
        findings.append(
            f"figure {fpath} used on slides {slide_nums} with "
            f"{len(captions)} different captions — F6 MAJOR: "
            f"if two slides explain the same figure differently, emit two files"
        )
    return findings


def check_layout_rules(slides):
    """Layout checks that live in the markdown source.

    Note: markdown table/code/column detectors were removed — zero markdown
    table syntax exists in any shipped deck. Surviving L1/L2/L3 violations
    are inside figure PNGs and only render review catches them.
    """
    findings = []
    for s in slides:
        n, title = s["num"], s["title"]

        total_bullets = len(s["bullets"]) + len(s["fragments"])
        if total_bullets > 4:
            findings.append(
                f"slide {n:03d} \"{title}\" — L4 MINOR: "
                f"{total_bullets} bullet/fragment items (max 4)"
            )

        if s["fragments"]:
            lines = s["raw"].split("\n")
            last_frag_idx = -1
            for i, line in enumerate(lines):
                if re.match(r"^\* ", line):
                    last_frag_idx = i
            if last_frag_idx >= 0:
                after = lines[last_frag_idx + 1:]
                for line in after:
                    stripped = line.strip()
                    if (stripped
                            and not stripped.startswith("<")
                            and not stripped.startswith("!")
                            and not stripped.startswith("*")
                            and not stripped.startswith("-")
                            and not stripped.startswith("<!--")):
                        findings.append(
                            f"slide {n:03d} \"{title}\" — L5 MAJOR: "
                            f"paragraph after fragmented list."
                        )
                        break

        if s["has_figcaption_katex"]:
            findings.append(
                f"slide {n:03d} \"{title}\" — MAJOR: "
                f"KaTeX ($...$) inside <figcaption> or <div>. "
                f"Renders as literal source."
            )

    return findings


def check_fragment_syntax(slides):
    findings = []
    for s in slides:
        if s["is_part_divider"]:
            continue
        dashes = len(s["bullets"])
        stars = len(s["fragments"])
        if dashes > 0 and stars > 0:
            findings.append(
                f"slide {s['num']:03d} \"{s['title']}\" — MINOR: "
                f"mixed list syntax ({stars} fragment + {dashes} static)."
            )
    return findings


def check_demo_links(slides):
    findings = []
    for s in slides:
        for note in s["speaker_notes"]:
            urls_in_note = re.findall(r"https?://\S+", note)
            if urls_in_note and not s["has_href"]:
                findings.append(
                    f"slide {s['num']:03d} \"{s['title']}\" — S5a MAJOR: "
                    f"URL in speaker note but no clickable link on slide."
                )
    return findings


def check_deck_structure(slides):
    findings = []
    if slides:
        first = slides[0]
        definition_words = ["definition", "defined as", "is a", "are a", "定義", "とは"]
        story_words = ["In 1", "In 2", "century", "puzzle", "problem",
                       "story", "experiment", "found that"]
        # Strip speaker notes — they contain stage directions, not slide content
        first_text = re.sub(r"<!--.*?-->", "", first["raw"], flags=re.S).lower()
        has_definition = any(w.lower() in first_text for w in definition_words)
        has_story = any(w.lower() in first_text for w in story_words)
        if has_definition and not has_story:
            findings.append(
                f"slide 001 \"{first['title']}\" — S1 BLOCKER: "
                f"deck opens with definitions, not a story."
            )
    return findings


def check_bold_usage(slides):
    findings = []
    for s in slides:
        bolds = re.findall(r"\*\*([^*]+)\*\*", s["raw"])
        if len(bolds) > 5:
            findings.append(
                f"slide {s['num']:03d} \"{s['title']}\" — MINOR: "
                f"{len(bolds)} bold spans."
            )
    return findings


def check_staleness(deck_dir):
    findings = []
    fig_dir = os.path.join(deck_dir, "figures")
    review_dir = os.path.join(deck_dir, "review")
    if not os.path.isdir(review_dir):
        return findings
    renders = sorted(
        f for f in os.listdir(review_dir)
        if f.startswith("slide.") and f.endswith(".png")
    )
    if not renders:
        return findings
    first_render = os.path.join(review_dir, renders[0])
    render_mtime = os.path.getmtime(first_render)
    if os.path.isdir(fig_dir):
        for f in os.listdir(fig_dir):
            if f.endswith((".png", ".gif")):
                fpath = os.path.join(fig_dir, f)
                if os.path.getmtime(fpath) > render_mtime:
                    findings.append(
                        f"STALE RENDER: figures/{f} is newer than review/{renders[0]}. "
                        f"Re-render before reviewing."
                    )
                    break
    return findings


# ── Render hash change detection ─────────────────────────────────────────────

def compute_render_hashes(deck_dir):
    """Hash each rendered slide PNG. Used to detect which slides changed
    between rounds — the correct scope for Tier 1 LLM review.

    A figure edit propagates to every slide that uses it. A CSS edit propagates
    deck-wide. Both are caught by hashing the render, not the markdown source.
    """
    review_dir = os.path.join(deck_dir, "review")
    hashes = {}
    if not os.path.isdir(review_dir):
        return hashes
    for f in sorted(os.listdir(review_dir)):
        if f.startswith("slide.") and f.endswith(".png"):
            path = os.path.join(review_dir, f)
            h = hashlib.sha256()
            with open(path, "rb") as fh:
                while True:
                    chunk = fh.read(8192)
                    if not chunk:
                        break
                    h.update(chunk)
            slide_num = int(re.search(r"(\d+)", f).group(1))
            hashes[slide_num] = h.hexdigest()
    return hashes


def save_render_hashes(deck_dir, hashes):
    """Save hashes for comparison in the next round."""
    path = os.path.join(deck_dir, "review", ".render_hashes.json")
    with open(path, "w") as fh:
        json.dump({str(k): v for k, v in hashes.items()}, fh)


def load_render_hashes(deck_dir):
    """Load hashes from the previous round."""
    path = os.path.join(deck_dir, "review", ".render_hashes.json")
    if not os.path.exists(path):
        return {}
    with open(path) as fh:
        return {int(k): v for k, v in json.load(fh).items()}


def changed_slides(deck_dir):
    """Return slide numbers whose render hash changed since last save.

    This is the correct Tier 1 review scope: it catches figure edits that
    propagate to slides whose markdown did not change.
    """
    current = compute_render_hashes(deck_dir)
    previous = load_render_hashes(deck_dir)
    if not previous:
        return set(current.keys())  # first round: all slides are new
    changed = set()
    for num, h in current.items():
        if num not in previous or previous[num] != h:
            changed.add(num)
    # Also flag slides that existed before but are gone now
    for num in previous:
        if num not in current:
            changed.add(num)
    return changed


# ── Main ─────────────────────────────────────────────────────────────────────

def run(deck):
    deck_dir = os.path.dirname(os.path.abspath(deck)) or "."
    front, slides = parse_deck(deck)

    print(f"checking {len(slides)} slides in {deck}")

    all_findings = []

    checks = [
        ("question answer leak", check_question_answer_leak),
        ("figure reuse", check_figure_reuse_different_captions),
        ("layout rules", check_layout_rules),
        ("fragment syntax", check_fragment_syntax),
        ("demo links", check_demo_links),
        ("deck structure", check_deck_structure),
        ("bold usage", check_bold_usage),
    ]

    for name, fn in checks:
        findings = fn(slides)
        if findings:
            all_findings.extend(findings)
            print(f"  {name}: {len(findings)} finding(s)")
        else:
            print(f"  {name}: clean")

    stale = check_staleness(deck_dir)
    if stale:
        all_findings.extend(stale)
        print(f"  staleness: {len(stale)} finding(s)")
    else:
        print(f"  staleness: clean")

    # Change detection
    changed = changed_slides(deck_dir)
    total = len(slides)
    if changed:
        print(f"\n  changed slides (Tier 1 scope): {len(changed)}/{total} — "
              f"slides {sorted(changed)[:20]}{'...' if len(changed) > 20 else ''}")
    else:
        print(f"\n  changed slides: 0/{total} — no slides changed since last hash save")

    # Save current hashes for next comparison
    hashes = compute_render_hashes(deck_dir)
    if hashes:
        save_render_hashes(deck_dir, hashes)

    # Summary
    blockers = [f for f in all_findings if "BLOCKER" in f]
    majors = [f for f in all_findings if "MAJOR" in f]
    minors = [f for f in all_findings if "MINOR" in f]

    print(f"\n{'='*60}")
    print(f"BLOCKERS: {len(blockers)}  MAJORS: {len(majors)}  MINORS: {len(minors)}")

    if all_findings:
        print(f"\nFindings:\n")
        for f in all_findings:
            print(f"  {f}")

    if blockers:
        print(f"\n{len(blockers)} BLOCKER(s) — fix before review")
        sys.exit(1)
    elif majors:
        print(f"\n{len(majors)} MAJOR(s) — fix before lecture")
        sys.exit(1)
    else:
        print("\nall structural checks pass")
        sys.exit(0)


if __name__ == "__main__":
    if len(sys.argv) >= 2:
        run(sys.argv[1])
    else:
        # Find deck in cwd
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
            sys.exit("usage: python3 check_deck.py <deck.md>")
        run(deck)
