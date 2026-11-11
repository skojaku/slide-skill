#!/usr/bin/env bash
# Render a slide-math deck with the skill's Marp config.
#   render.sh deck.md            -> deck.html (the shareable file)
#   render.sh deck.md pdf        -> deck.pdf  (the handout)
#   render.sh deck.md png        -> review/png/deck.NNN.png, one per slide, then a contact sheet
#   render.sh deck.md all        -> all three
set -euo pipefail
deck="${1:?usage: render.sh deck.md [html|pdf|png|all]}"
mode="${2:-html}"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cfg="$here/marp.config.mjs"
dir="$(cd "$(dirname "$deck")" && pwd)"
stem="$(basename "$deck" .md)"
run() { marp --config "$cfg" --no-stdin "$@"; }
case "$mode" in
  html) run "$deck" -o "$dir/$stem.html" ;;
  pdf)  run --pdf "$deck" -o "$dir/$stem.pdf" ;;
  png)  mkdir -p "$dir/review/png"
        rm -f "$dir/review/png/$stem".*.png
        run --images png "$deck" -o "$dir/review/png/$stem.png"
        python3 "$here/tools/sheet.py" "$dir/review/png" "$dir/review/sheet" ;;
  all)  "$0" "$deck" html; "$0" "$deck" pdf; "$0" "$deck" png ;;
  *) echo "unknown mode: $mode" >&2; exit 2 ;;
esac
