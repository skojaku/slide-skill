// Marp CLI config for slide-math decks. Use it for every render:
//   marp --config ~/.claude/skills/slide-math/marp.config.mjs --no-stdin deck.md -o deck.html
// (tools/render.sh wraps this.) It registers the theme, turns on raw HTML (needed by every
// component) and defines the KaTeX macros listed in COMPONENTS.md section 6.
import { fileURLToPath } from 'node:url'

const here = (p) => fileURLToPath(new URL(p, import.meta.url))

// `##` is a literal `#` inside a KaTeX macro body (a single `#` starts an argument).
const box = (colour) =>
  `\\mathchoice{\\colorbox{##${colour}}{$\\displaystyle #1$}}{\\colorbox{##${colour}}{$\\textstyle #1$}}` +
  `{\\colorbox{##${colour}}{$\\scriptstyle #1$}}{\\colorbox{##${colour}}{$\\scriptscriptstyle #1$}}`

export default {
  html: true,
  allowLocalFiles: true,
  themeSet: [here('./theme/math.css'), here('./theme/math-fonts.css')],
  options: {
    math: {
      lib: 'katex',
      katexOption: {
        trust: true,
        strict: false,
        macros: {
          '\\hl': box('F4E6FF'),          // lavender highlight: the part to look at
          '\\hlc': box('E5FDFF'),         // cyan highlight: the alternative
          '\\why': '\\htmlClass{why}{\\text{#1}}', // reason on the right of a derivation step
          '\\lbl': '\\htmlClass{lbl}{\\text{#1}}', // a word in the body font inside a formula
          '\\key': '\\textcolor{##B70000}{#1}',    // red symbol (rare)
          '\\vb': '\\boldsymbol{#1}',              // vector
          '\\softmax': '\\operatorname{softmax}',
          '\\sigmoid': '\\operatorname{sigmoid}',
          '\\argmax': '\\operatorname*{arg\\,max}',
          '\\argmin': '\\operatorname*{arg\\,min}',
          '\\R': '\\mathbb{R}',
          '\\E': '\\mathbb{E}',
          '\\Pr': '\\operatorname{Pr}',
          '\\tr': '\\operatorname{tr}',
          '\\diag': '\\operatorname{diag}',
          '\\T': '^{\\top}',
          '\\given': '\\,\\middle|\\,',
          '\\d': '\\mathrm{d}',
        },
      },
    },
  },
}
