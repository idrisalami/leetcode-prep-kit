# Rich lesson pages: design

Date: 2026-11-15. Status: ready for the user's approval.

## 1. Intent

The kit's reader shows modules, reference sheets and my-prep notes as plain rendered
Markdown. The user wants those pages to read like a polished artifact: clear callouts,
colour that carries meaning, and a few interactive widgets that make an idea click
(step through a binary search, flip between two conventions, quiz yourself on a card).

The `.md` files stay the only source of truth. The rich page is built in the browser,
every time, from the same Markdown. Nothing is pre-rendered or checked in as HTML.

Why: the modules are long and dense. Today a rule, a trap and a spoken interview line
all look the same (a grey blockquote), so the eye cannot find what matters on a
second read. The user reads these pages many times before interviews; the page should
make the second and fifth read faster than the first.

## 2. Approved look (decided by the user)

The user approved the "A + B mix" mockup, saved next to this doc as
`2026-11-15-rich-lesson-pages-mockup.html`. It is authoritative for colours, sizes,
spacing and tints: copy its values into `app.css` freely. Its markup and inline
script are illustration only. Where the mockup is silent (dark mode, narrow widths),
the builder decides.

| Element | Spec from the mockup |
|---|---|
| Layout | Sticky side rail (220px) + one reading column, max-width 780px |
| Reading column | Surface `#fcfcfb`, border `#e3e1da`, radius 14px, padding 38px 48px |
| Eyebrow above each h2 | `§0.5 · The primitives · about 9 min` (section number, name, reading time) |
| Lead paragraph | First paragraph after an h2 gets the larger `.lead` style |
| Callouts | 4px left border, small uppercase label, tinted background |
| Rule callout | Blue `#2a78d6` on `#eef4fc`, statement in a larger weight |
| Trap callout | Amber `#c98a00` on `#fff6e0` |
| Tip callout | Green `#008300` on `#e9f5e7` |
| Widget box | White, 1px border, radius 12px, uppercase title, optional Big-O badge |
| Big-O badge | Green for `O(1)`/`O(log n)`, amber for `O(n)` and above |
| Code lines | `# ✗` lines tinted red with a `#e66767` left border; `# ✓` lines tinted green |
| Stepper | Array of cells; states out (grey), mid (purple `#5b4fd6` on `#ece9fd`), answer (green); pointer labels under cells; narration box; Back / Next; "Step k of N" |
| Toggle | Segmented control that swaps a definition list (two or more named variants) |
| Flip card | Front `#fff6e0`, back `#e2f3df`, 3D flip, "Got it" / "Missed it" buttons |
| Side rail | Module name, progress line, progress bar, section links with a dot (grey, green when read, blue when current) |

Dark mode: every new colour gets a dark counterpart in the existing
`@media (prefers-color-scheme: dark)` blocks of `app.css`. Tints become low-alpha
versions of the same hue on the dark surface; text stays readable at WCAG AA.

## 3. Goals

1. **Reader only.** Rich rendering applies to the pages `reader.js` shows: course
   modules, reference docs, and my-prep notes. Chat, problem statements, practice,
   setup and matrix evidence keep today's `renderMarkdown` output unchanged.
2. **Auto-detected styling, no authoring needed.** Every existing module looks better
   with zero edits to its `.md`. Detection rules are in section 5.
3. **Two authored widgets** that need a small fenced block in the `.md`: the stepper
   (`steps`) and the toggle (`compare`). Syntax in section 6.
4. **Flip-card self-check.** On modules, pair question N of `## 0.9 Self-check` with
   answer N of `## Self-check answers` and show them as flip cards inside §0.9.
5. **Progress rail** replacing today's ToC, keeping its behaviour (sticky, open on
   wide screens, active-section tracking).
6. **Example demos now, the rest later.** Ship the engine plus two authored demos:
   - Module 04, under `## Boundary search: lower_bound and upper_bound`: a `steps`
     block tracing `lower_bound` on a short sorted array.
   - Module 04, under `### Primitive 2: the range convention`: a `compare` block for
     Closed `[lo, hi]` vs Half-open `[lo, hi)`.
   - Module 03, under `### Shape A: converging`: a `steps` block tracing converging
     pointers on a sorted pair-sum.

   Demos for the other modules wait until the user has checked these.

## 4. Non-goals and anti-goals

Non-goals (not in this project):

- Authored demos for modules other than 03 and 04.
- Any change to how chat, statements or evidence render.
- Pre-rendered HTML, a build step, or a new dependency.
- Editing module prose to "fit" the new look. Only the three demo blocks are added.

Anti-goals (it fails even if it technically works):

- A module with few markers (00, 03, 06) looks worse or emptier than today.
- Something that works today breaks: drill tools ("Code it", status marks), the solve
  card, the module 00 read toggle, in-app links, heading anchors, the
  "N of M solved" header, code highlighting.
- A detection false positive that dresses ordinary text as a rule or trap.
- A malformed demo block blanks the page or throws. It must fall back to showing the
  block as plain code, with a console warning.
- Anything a learner relies on is hidden behind an interaction with no fallback
  (for example, self-check answers unreachable when the card pairing fails).

## 5. Auto-detection rules

All rules run on the sanitised DOM that `renderMarkdown` already returns, in a new
post-processing step. They match on structure and leading markers, never on free
text in the middle of a paragraph.

Rules are checked top to bottom; the first match wins.

| Source pattern (first element inside a `<blockquote>`) | Becomes | Label |
|---|---|---|
| Starts with `⚠` (with or without U+FE0F), then bold text that starts "You'll see" and contains "again" | Forward-pointer callout (neutral grey, link styled) | "Comes back later" (plus "in module NN" when a two-digit module number appears in the bold text) |
| Starts with `⚠` (any other case) | Trap callout (amber) | "Heads up" |
| The whole first child is a single `<em>`, inside `## 0.1` | "One question" callout (rule style, larger) | "The one question" |
| The whole first child is a single `<em>` whose text starts with a quote mark | Spoken-answer callout (green tip style) | "Say it like this" |
| Starts with `<strong>` (any bold-led blockquote) | Rule callout (blue); the bold run gets the larger `.big` weight | "Key idea" |
| Any other blockquote | Today's blockquote style, slightly refined | none |

Why "Heads up" and not "Watch out": a survey of every `⚠` blockquote in the course
shows a mix of traps ("The bug: advancing `prev` unconditionally") and notes ("And
then answer-space search inverts it"). "Heads up" is true for both. **My call.**

Why every bold-led blockquote is a rule: the course uses bold-led blockquotes as its
key statements (module 04 alone has 23, e.g. "Once `P` becomes true…", "You never
guess…"). A narrower match would leave most of them plain. **My call.**

Other auto rules:

| Pattern | Treatment |
|---|---|
| A line in a code block whose comment contains `✗` | `.bad` line |
| A line in a code block whose comment contains `✓` | `.good` line |
| Inline `<code>` whose whole text is a Big-O expression (`O(...)`) inside a table cell | Big-O badge, colour by class (below) |
| A paragraph that starts with `<strong>How to play this in an interview:</strong>` | Spoken-answer callout |
| First `<p>` after each h2 | `.lead` |
| Each h2 | Eyebrow line above it (below) |

Big-O badge colour, matched on the text inside `O(...)`, ignoring spaces and words
like "amortised" outside the parentheses. **My call.**

| Class | Matches | Colour |
|---|---|---|
| Fast | `1`, or a single `log` term (`log n`, `log R`, `log(n)`) | Green |
| Steep | any `^`, `²`, `2^n`, `n!`, or a product of two plain variables (`n*m`, `nm`, `n·m`) | Red `#c9302f` on a light red tint |
| Everything else | `n`, `n + m`, `k`, `n log n`, `min(n, m)`, … | Amber |

Eyebrow:

- It sits above the h2. The h2 stays visible and its `id` and `textContent` are
  unchanged (the rail and anchors depend on them).
- Numbered h2 (text starts with `0.N `): eyebrow is `§0.N · about M min`. The leading
  `0.N ` inside the h2 is wrapped in a span that is visually hidden, so the number
  is not shown twice while `textContent` stays the same.
- Unnumbered h2: eyebrow is `about M min`.
- Reading time covers the h2 and everything up to the next h2, h3 children included.
  Word count divided by 200, rounded up; code blocks count at half weight. **My call.**

Code-line marking must survive CodeMirror highlighting: mark lines after the
existing `runMode` pass, by splitting the highlighted block on newlines into line
wrappers. **My call.**

## 6. Authored blocks

Both are fenced code blocks with a custom language. `marked` already emits
`<pre><code class="language-steps">`, and the sanitiser keeps the class, so the
post-processor can find them. On GitHub and in any plain viewer they show as
readable text, which is the fallback.

### 6.1 `steps`: the stepper

````
```steps
title: lower_bound(nums, 7)
array: 1 3 5 7 7 9 11
- lo=0 hi=7 | Start: the boundary is somewhere in [0, 7).
- lo=0 hi=7 mid=3 | nums[3] = 7 >= 7, so mid is T. Keep it: hi = mid.
- lo=0 hi=3 mid=1 | nums[1] = 3 < 7, so mid is F. lo = mid + 1.
- lo=2 hi=3 mid=2 | nums[2] = 5 < 7. lo = mid + 1.
- lo=3 hi=3 ans=3 | lo == hi: the boundary is index 3.
```
````

| Line | Meaning |
|---|---|
| `title:` | Optional widget title |
| `array:` | Space-separated cell values (strings, shown as-is) |
| `- k=v k=v … \| text` | One step. Keys name pointers; values are cell indices. `\|` separates the narration. |

Key semantics (fixed set, so the look is consistent):

| Key | Rendering |
|---|---|
| `lo`, `hi`, `l`, `r`, `i`, `j`, `left`, `right` | Pointer label under that cell |
| `mid` | Pointer label plus the purple "mid" cell state |
| `ans` | Green "answer" cell state |
| A pointer equal to the array length | Label drawn in a ghost cell past the end (needed for half-open `hi`) |

Cells outside the live range are greyed out ("out") when both `lo` and `hi` (or
`l` and `r`) are present. Range is half-open when the block says `range: half-open`,
closed by default. **My call** on the default.

Controls: Back, Next, "Step k of N", and the left/right arrow keys when the widget
has focus. No autoplay.

### 6.2 `compare`: the toggle

````
```compare
title: Two ways to write the range
option: Closed [lo, hi]
  Means: every index from lo to hi, both ends included
  Start: lo, hi = 0, len(nums) - 1
  Loop: while lo <= hi
  Discard right: hi = mid - 1
  Ends when: lo > hi, the range is empty
  Use for: exact match
option: Half-open [lo, hi)
  Means: lo included, hi excluded
  Start: lo, hi = 0, len(nums)
  Loop: while lo < hi
  Discard right: hi = mid
  Ends when: lo == hi, lo is the answer
  Use for: boundaries, lower_bound
```
````

`option:` starts a variant; indented `Label: value` lines are its rows. Rows
render as a `<dl>`. The segmented control switches variants; the rows keep their
position so the eye sees what changed. Two to four options. Inline backticks in
values render as code.

### 6.3 Failure behaviour

If a block fails to parse (no `array:`, a pointer index out of range, zero steps,
fewer than two options), leave the original code block in place, add a small
"demo could not be read" note under it, and `console.warn` the reason. Never throw
out of the post-processor.

## 7. Flip-card self-check

- Applies to course modules only (path under `course/modules/`).
- Questions: the top-level `<ol>` items inside the `## 0.9 Self-check` section.
- Answers: the top-level `<ol>` items inside the `## Self-check answers` section.
- If both lists exist and have the same length, render one flip card per pair inside
  §0.9, after the intro text, in a responsive grid. Front shows the question; click
  or Enter/Space flips to the answer.
- The bottom `## Self-check answers` section stays as today (collapsed
  `<details class="answers">`), so answers remain reachable without the cards.
- If the lists are missing or the counts differ, skip the cards and keep today's
  behaviour exactly. `console.warn` the mismatch.
- "Got it" / "Missed it" on the back (**decided by the user: local tally only**):
  - Pressing one records that card's result in `localStorage` under
    `prep:selfcheck:<doc path>` (card index → "got" or "missed"; pressing again
    overwrites). No server call, no effect on the skills matrix.
  - The §0.9 section shows a tally line above the cards: "5 of 8 got · 2 missed".
  - Each card shows its last result as a small mark on its front.
  - A "Reset" link next to the tally clears that page's results.
  - Feeding the skills matrix is a possible later version, out of scope here.

## 8. Progress rail

Replaces `buildToc` for the reader; keeps the same container and sticky behaviour,
open by default at width ≥ 1100 (`WIDE`), collapsible below.

| Part | Content |
|---|---|
| Title | Module id and name (or doc title) |
| Progress line | Modules: "N of M sections read · K/D drills" (D from the existing solved count). Docs: "N of M sections read". |
| Bar | Sections read / total |
| Links | h2 links, h3 nested and smaller, as today. Dot per h2: grey, blue when current, green when read |

"Read" means the reader has scrolled to the end of that h2 section (its last
element has entered the viewport) at least once, **after a real scroll** (sections
visible on first load are not marked until the user scrolls). Short sections that
pass by quickly do get marked; that is accepted. Stored in `localStorage` under
`prep:read:<doc path>` as a list of heading ids. No server state, no effect on the
skills matrix. **My call.** It is a reading aid, not a record.

Which h2s count toward "N of M": every h2 except `Self-check answers` (collapsed by
default, so it would never be "read"). The drill set counts. The injected solve card
is not a heading and is not counted. **My call.**

Active-section tracking reuses `trackActive` and the `prep:anchor` event.

## 9. Architecture

| Piece | Responsibility |
|---|---|
| `app/static/js/lesson.js` (new) | `enrichLesson(root, { path, isModule })`: runs every rule in sections 5–7 on the `.md` element. Pure DOM, no fetches. |
| `app/static/js/lesson-widgets.js` (new) | `parseSteps(text)`, `parseCompare(text)` (pure, return data or throw a typed error) and the two widget builders |
| `app/static/js/reader.js` | Calls `enrichLesson` after `renderMarkdown` and before `collapseAnswers` / `addDrillTools`; swaps `buildToc` for the rail |
| `app/static/css/app.css` | New `.lesson` section: callouts, widgets, badges, cards, rail, eyebrow, dark-mode block |
| `md.js` | Unchanged |
| `course/modules/03-…md`, `04-…md` | The three demo blocks from goal 6 |

Order inside `enrichLesson` matters: flip cards read the `<ol>` before
`collapseAnswers` moves the answers into `<details>`.

## 10. Constraints

- No new dependencies. Vanilla JS modules, `marked`, CodeMirror as already vendored.
- Tests: `fake-dom.mjs` is small (it only supports `sanitizeHtml`), and a real DOM
  library would be a new dependency. So the logic is written to be testable without
  a DOM. **My call:**
  - Pure, node-tested: `parseSteps`, `parseCompare`, the Big-O classifier, the
    callout classifier (takes a plain description: first-child tag, its text, the
    enclosing h2 text; returns a kind and label), reading-time counting, self-check
    pairing (takes two arrays, returns pairs or null).
  - Thin DOM glue in `lesson.js` calls those and is verified by screenshots.
  - Extending `fake-dom.mjs` is allowed if a glue test needs a few more methods; do
    not rebuild a DOM in it.
- Python tests stay green.
- Visual checks: screenshots of modules 00, 03, 04 and 06 in light and dark mode
  plus one narrow width, taken on a copy of the kit served on a spare port, never on
  the user's running server.
- The kit repo keeps demo data only; nothing from `my-prep/` or statements enters it.
- Accessibility: widgets are keyboard reachable, flip cards expose both sides to
  screen readers (`aria-live` on flip), colour is never the only signal (callouts
  always carry a text label).

## 11. Left to the builder

- Exact class names, file split inside `lesson.js` if it grows.
- Animation timings (keep them short, respect `prefers-reduced-motion`).
- How the rail collapses on narrow screens, as long as it stays usable.
- The exact array and narration in the three demos, as long as they are correct
  traces of the code shown in the module.

## 12. Decisions log

| Decision | Who |
|---|---|
| A + B mix visual direction (the mockup) | User |
| Engine plus demos in modules 03 and 04 now; other demos after the user checks them | User |
| `.md` stays the source of truth, nothing pre-rendered | User |
| Self-check "Got it" / "Missed it" is a local tally only | User |
| Reader-only scope; chat and statements unchanged | Claude |
| Detection rules, labels, Big-O tiers, eyebrow, reading time | Claude |
| "Read" tracking in `localStorage`, after a real scroll | Claude |
| Pure-function testing, screenshots for the DOM glue | Claude |
| Dark-mode parity | Claude |
