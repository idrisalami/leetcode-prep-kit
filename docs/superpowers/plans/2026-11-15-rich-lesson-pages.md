# Rich Lesson Pages Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The reader turns each course .md into a rich lesson page in the browser: auto-styled callouts, code-line marks, Big-O badges, eyebrows, two authored widgets (`steps`, `compare`), flip-card self-checks and a progress rail. The .md files stay the source of truth.

**Architecture:** `renderMarkdown` (unchanged) returns the sanitised DOM. A new post-processor `enrichLesson` in `lesson.js` rewrites it. All decisions sit in pure functions with node tests; the DOM glue around them is checked by screenshots. A new `rail.js` replaces `buildToc` and feeds the existing `trackActive`.

**Tech Stack:** Vanilla ES modules, the vendored `marked` and CodeMirror runMode, `node --test`, Python `unittest`, and Playwright-core with the cached Chromium for screenshots. Playwright lives in `/tmp` and is never a kit dependency.

**Spec:** `docs/superpowers/specs/2026-11-15-rich-lesson-pages-design.md`. Mockup: `docs/superpowers/specs/2026-11-15-rich-lesson-pages-mockup.html`. The mockup is authoritative for colours, radii and spacing.

## Global Constraints

- No new dependencies in the kit. Playwright stays under `/tmp/pw`.
- `md.js` is not modified. `renderMarkdown` keeps serving coach, practice, setup and matrix unchanged.
- Only the reader changes: `reader.js`, plus the new `lesson.js`, `lesson-widgets.js` and `rail.js`, plus a new `/* ---- lesson ---- */` section in `app/static/css/app.css`. The section goes after the reader section, around line 491, and ends with its own dark-mode `@media (prefers-color-scheme: dark)` block.
- Use existing tokens where one matches the mockup. Examples: `--surface`, `--line`, `--accent`, `--accent-soft`, `--lvl-*-ink/bg/line`, `--code-bg`, `--bad`, `--good`, `--mono`. Only use literal mockup hex values where no token exists, such as the purple `#5b4fd6` / `#ece9fd`.
- Mockup values:
  - Reading column: max-width 780px, surface `#fcfcfb`, border `#e3e1da`, radius 14px, padding 38px 48px.
  - Callouts: border-left 4px, radius `0 10px 10px 0`. Rule `#2a78d6`/`#eef4fc`, trap `#c98a00`/`#fff6e0`, tip `#008300`/`#e9f5e7`.
  - Callout labels: 11px, weight 800, letter-spacing .08em, uppercase.
  - Widget box: radius 12px.
  - Code lines: `.bad` is `rgba(201,48,47,.2)` with a 3px `#e66767` left border. `.good` is `rgba(0,160,0,.14)` with a 3px `#5fbf5f` left border.
  - Flip cards: front `#fff6e0` with a `#e3c25a` border, back `#e2f3df` with a `#9fd19a` border.
- Callouts always carry a text label, so colour is never the only signal.
- Animations are off under `prefers-reduced-motion: reduce`.
- `enrichLesson` never throws. Each rule runs in its own try/catch, and a failure leaves that element as it was and calls `console.warn`.
- The rewritten DOM keeps every h2/h3 `id` and `textContent` unchanged.
- localStorage keys are exactly `prep:read:<doc path>` and `prep:selfcheck:<doc path>`. There are no server calls.
- The kit repo holds demo data only. Nothing from `my-prep/` or `app/data/statements/` is ever staged.
- Git commits:
  - Command: `git -c user.name="LeetCode Prep Kit" -c user.email="kit@localhost" commit`.
  - Messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
  - Stage files by name; never use `git add -A` or `git add .`.
  - Never push.
- Visual checks run only on the copy at `/tmp/vid/kit`, served on port 8797. Never use the user's server on port 8765.
- macOS shell: use `sed -i ''`, quote globs, and never run `sleep` or `timeout` in the foreground.

## Review Focus

1. **The eyebrow breaks DOM-order code.**
   - `collapseAnswers` moves siblings until the next h1/h2, so it would swallow the eyebrow that belongs to the following h2.
   - The solve card anchors on `drill.previousElementSibling === hr`, and the eyebrow now sits in that spot.
   - Expected: the answers `<details>` holds only answers, and the solve card sits above the drill set's eyebrow.
   - Pinned in Task 4, Step 6.
2. **localStorage is missing, throws (private mode), or holds corrupt JSON.**
   - Expected: the page renders as if nothing was stored, and nothing throws.
   - Pinned in Task 3 (`parseStored` tests).
3. **A long flip-card answer** (a code block, two paragraphs, a nested list) must not be clipped.
   - Expected: the card grows to the taller face.
   - Pinned in Task 6, Step 5 (module 04 has long answers).
4. **A malformed `steps` block**: a typo key, a non-integer index, an index past the array length, or a narration without `|`.
   - Expected: a specific error message and the original code block plus a note, never a half-drawn widget.
   - Pinned in Task 2 tests.
5. **Code-line marking on a highlighted block whose token spans cross lines** (Python docstrings).
   - Expected: the same text, the same highlighting and the same line count after splitting. If the split changes `textContent`, revert it and warn.
   - Pinned in Task 4, Step 6 (module 04 `lower_bound` has a docstring) and the guard in Task 4, Step 3.

---

### Task 1: Tooling (screenshot helper, test copy, ignore the SDD workspace)

This task has no product code. Every later visual step depends on it.

**Files:**
- Create (outside the repo): `/tmp/pw/` (npm install target), `/tmp/vid/shot.mjs`, `/tmp/vid/sync.sh`
- Modify: `.gitignore` (add `.superpowers/`)

**Interfaces:**
- Produces:
  - `bash /tmp/vid/sync.sh`
    - Copies `app/` and `course/` from `~/leetcode-prep-kit` into `/tmp/vid/kit` with `rsync -a --delete`, excluding `app/data/statements/`.
    - Then restarts the copy's server: `python3 app/server.py --port 8797 --no-open`, in the background, logging to `/tmp/vid/serve-lesson.log`. It kills only a process listening on 8797.
  - `node /tmp/vid/shot.mjs <route> <out.png> [--dark] [--width N] [--scroll <css-selector>] [--click <css-selector>]`
    - Opens `http://127.0.0.1:8797/<route>` in headless Chromium. The default width is 1440 and the full page is captured.
    - `--dark` sets `colorScheme: "dark"`.
    - `--scroll` scrolls the selector into view and captures the viewport only.
    - `--click` clicks the selector, then waits 600ms.
    - Prints the out path.

- [ ] **Step 1:** Run `cd /tmp/pw && npm init -y >/dev/null && npm i playwright-core`. Confirm that `ls ~/Library/Caches/ms-playwright` shows `chromium-1228`, and launch with that cache.
- [ ] **Step 2:** Write `sync.sh` and `shot.mjs` to the interfaces above. Screenshots go under `/tmp/vid/lesson-shots/`.
- [ ] **Step 3:** Verify the baseline. Run `bash /tmp/vid/sync.sh && node /tmp/vid/shot.mjs "#/module/04" /tmp/vid/lesson-shots/before-04.png`, then open the PNG. Expected: today's module 04 page. Keep it as the "before" reference.
- [ ] **Step 4:** Add the line `.superpowers/` to `.gitignore`. Commit with message `Ignore the SDD workspace`.

---

### Task 2: `steps` and `compare` parsers (pure)

**Files:**
- Create: `app/static/js/lesson-widgets.js` (parsers only in this task)
- Test: `app/static/js/tests/lesson-widgets.test.mjs`

**Interfaces:**
- Produces:
  - `export class BlockError extends Error`. Its message is shown in the note and in the warning.
  - `parseSteps(text: string) -> { title: string, array: string[], range: "closed"|"half-open", steps: { ptrs: Record<string, number>, text: string }[] }`. Throws `BlockError`.
  - `parseCompare(text: string) -> { title: string, options: { name: string, rows: { label: string, value: string }[] }[] }`. Throws `BlockError`.
  - `stepCells(data, k: number) -> { value: string, index: number, ghost: boolean, state: "in"|"out"|"mid"|"ans", labels: string[] }[]`
    - Returns the cells for step k.
    - It adds a ghost cell only when some pointer in step k equals `array.length`.
- The pointer keys are exactly `lo hi l r i j left right mid ans`.
- Range pairs are (`lo`,`hi`), (`l`,`r`) and (`left`,`right`).
- A cell is "out" when the step has a pair and the index lies outside it:
  - closed: `[a, b]`
  - half-open: `[a, b)`
- State precedence: ans > mid > out > in.
- `labels` lists the pointer names at that index, in key order, without `ans`.

- [ ] **Step 1: Write the failing tests.** Use the spec §6.1 lower_bound block (`range` omitted) and the §6.2 compare block verbatim as fixtures.

```js
test("parseSteps reads the spec example", () => {
  const d = parseSteps(LOWER_BOUND);
  assert.equal(d.title, "lower_bound(nums, 7)");
  assert.deepEqual(d.array, ["1","3","5","7","7","9","11"]);
  assert.equal(d.range, "closed");
  assert.equal(d.steps.length, 5);
  assert.deepEqual(d.steps[1].ptrs, { lo: 0, hi: 7, mid: 3 });
  assert.equal(d.steps[1].text, "nums[3] = 7 >= 7, so mid is T. Keep it: hi = mid.");
});
test("range: half-open is read", ...)                      // "range: half-open" line -> "half-open"
test("stepCells: half-open greys outside [lo, hi), ghost at len", () => {
  const d = { ...parseSteps(LOWER_BOUND), range: "half-open" };
  const c = stepCells(d, 0);                                // lo=0 hi=7
  assert.equal(c.length, 8); assert.equal(c[7].ghost, true); assert.deepEqual(c[7].labels, ["hi"]);
  assert.ok(c.slice(0, 7).every((x) => x.state === "in"));
  const c2 = stepCells(d, 2);                               // lo=0 hi=3 mid=1
  assert.equal(c2.length, 7);                               // no ghost: no pointer equals 7
  assert.equal(c2[1].state, "mid"); assert.equal(c2[3].state, "out"); assert.equal(c2[0].state, "in");
  assert.equal(stepCells(d, 4)[3].state, "ans");
});
test("stepCells: closed range keeps hi inside", ...)       // lo=1 hi=4 closed -> index 4 "in", 5 "out"
test("stepCells: no pair means nothing is out", ...)       // ptrs { i: 2 } -> every cell "in"
test("parseSteps errors", () => {
  for (const [src, msg] of [
    ["- lo=0 | x", /array/],                                // no array:
    ["array: 1 2\n", /no steps/],
    ["array: 1 2\n- lo=0 hi=3 | x", /past the end/],        // 3 > len 2
    ["array: 1 2\n- lo=x | x", /lo/],                       // not an integer
    ["array: 1 2\n- low=0 | x", /unknown pointer "low"/],
    ["array: 1 2\n- lo=0", /\|/],                           // no narration separator
  ]) assert.throws(() => parseSteps(src), (e) => e instanceof BlockError && msg.test(e.message));
});
test("parseCompare reads the spec example", () => {
  const d = parseCompare(COMPARE);
  assert.equal(d.options.length, 2);
  assert.equal(d.options[1].name, "Half-open [lo, hi)");
  assert.deepEqual(d.options[0].rows[2], { label: "Loop", value: "while lo <= hi" });
});
test("parseCompare errors", ...)   // one option -> /two/; five options -> /four/; a row before any option -> BlockError
```

- [ ] **Step 2:** Run `cd ~/leetcode-prep-kit && node --test app/static/js/tests/lesson-widgets.test.mjs`. Expected: FAIL, because the module is not found.
- [ ] **Step 3:** Implement the three functions and `BlockError` in `lesson-widgets.js`. Parse line by line:
  - `title:`, `array:` and `range:` are header lines.
  - Step lines start with `- `. Split on the first ` | `; the left side is space-separated `k=v` pairs.
  - In compare, rows are lines indented under an `option:`. Split each row on its first `: `.
  - Blank lines are ignored.
- [ ] **Step 4:** Run the same command. Expected: PASS. Then run `node --test app/static/js/tests/`. Expected: all pass.
- [ ] **Step 5:** Commit `lesson-widgets.js` and the test with message `Lesson widgets: parse steps and compare blocks`.

---

### Task 3: Pure lesson classifiers

**Files:**
- Create: `app/static/js/lesson.js` (pure exports only in this task)
- Test: `app/static/js/tests/lesson.test.mjs`

**Interfaces:**
- Produces, all exported from `lesson.js`:
  - `classifyCallout({ first, text, bold, h2 }) -> { kind, label }`
    - Inputs:
      - `first` is `"strong"` when the blockquote's first child starts with `<strong>`.
      - `first` is `"em"` when that child's only content is a single `<em>`.
      - Otherwise `first` is `"text"`.
      - `text` is the child's trimmed `textContent`; `bold` is the first `<strong>`'s text or `""`; `h2` is the enclosing h2 text.
    - `kind` is one of `pointer`, `trap`, `question`, `say`, `rule`, `plain`. The first match wins:

      | Rule | `kind` | `label` |
      |---|---|---|
      | `text` starts with ⚠ (with or without U+FE0F) and `bold` matches `/^You['’]ll see/` and `/again/` | `pointer` | "Comes back later", with " in module NN" added when `bold` contains a two-digit number |
      | Any other ⚠ start | `trap` | "Heads up" |
      | `first === "em"` and `/^0\.1\b/.test(h2)` | `question` | "The one question" |
      | `first === "em"` and `text` starts with `"`, `“`, `'` or `‘` | `say` | "Say it like this" |
      | `first === "strong"` | `rule` | "Key idea" |
      | Anything else | `plain` | `""` |

  - `bigOClass(code: string) -> "fast"|"steep"|"mid"|null`.
    - Returns null unless the trimmed text is `O(…)`, optionally followed by words such as "amortised".
    - Classes follow spec §5: fast is `1` or a single log term; steep is `^`, `²`, `n!` or a product of two plain variables; everything else is mid.
  - `countWords(s: string) -> number`
  - `readingMinutes(proseWords: number, codeWords: number) -> number` returns `Math.max(1, Math.ceil((proseWords + codeWords / 2) / 200))`.
  - `pairSelfCheck(questions: T[], answers: U[]) -> [T, U][] | null` returns null when either list is empty or the lengths differ.
  - `tallyText(results: Record<string, "got"|"missed">, total: number) -> string`. Example: `"5 of 8 got · 2 missed"`. When nothing is recorded, return `"0 of 8 got"` with the missed part omitted.
  - `progressLine({ read, total, drills }) -> string`. `drills` is `{ solved, count }` or null. Output is `"3 of 11 sections read · 4/9 drills"` or `"3 of 11 sections read"`.
  - `countsAsSection(h2Text: string) -> boolean` is false only for `/^self-check answers$/i`.
  - `newlyRead(ends: { id: string, top: number }[], viewportH: number, read: Set<string>) -> string[]` returns the ids not yet read whose section end has `top < viewportH`.
  - `parseStored(raw: string|null, fallback)` returns parsed JSON or `fallback` on null or invalid JSON, and never throws.
  - `store(key, value)` and `load(key, fallback)` wrap localStorage in try/catch. When localStorage is undefined or throws, `load` returns the fallback and `store` is a no-op.

- [ ] **Step 1: Write the failing tests.**

```js
test("classifyCallout follows the spec table", () => {
  const c = (o) => classifyCallout({ first: "text", text: "", bold: "", h2: "", ...o });
  assert.deepEqual(c({ text: "⚠️ You'll see this again in module 07.", bold: "You'll see this again in module 07." }),
    { kind: "pointer", label: "Comes back later in module 07" });
  assert.deepEqual(c({ text: "⚠ You’ll see it again.", bold: "You’ll see it again." }),
    { kind: "pointer", label: "Comes back later" });
  assert.deepEqual(c({ first: "strong", text: "⚠ The bug: advancing prev", bold: "The bug:" }),
    { kind: "trap", label: "Heads up" });
  assert.equal(c({ first: "em", text: "What is the invariant?", h2: "0.1 The one question" }).kind, "question");
  assert.equal(c({ first: "em", text: "“I'll use two pointers…”", h2: "0.4 Patterns" }).kind, "say");
  assert.equal(c({ first: "em", text: "just a note", h2: "0.4 Patterns" }).kind, "plain");
  assert.deepEqual(c({ first: "strong", text: "Once P becomes true…", bold: "Once P becomes true" }),
    { kind: "rule", label: "Key idea" });
  assert.equal(c({ text: "plain words" }).kind, "plain");
});
test("bigOClass tiers", () => {
  const cases = { "O(1)": "fast", "O(log n)": "fast", "O(log(n))": "fast", "O(log R)": "fast",
    "O(n)": "mid", "O(n + m)": "mid", "O(n log n)": "mid", "O(k log n)": "mid", "O(min(n, m))": "mid",
    "O(V + E)": "mid", "O(n) amortised": "mid", "O(n^2)": "steep", "O(n²)": "steep", "O(2^n)": "steep",
    "O(n!)": "steep", "O(n*m)": "steep", "O(nm)": "steep", "O(n·m)": "steep", "O(m × n)": "steep" };
  for (const [s, want] of Object.entries(cases)) assert.equal(bigOClass(s), want, s);
  for (const s of ["n log n", "O", "lo(1)", "O(n) time and O(1) space"]) assert.equal(bigOClass(s), null, s);
});
test("readingMinutes", ...)   // (0,0)->1  (200,0)->1  (201,0)->2  (300,200)->2  (400,1)->3
test("pairSelfCheck", ...)    // equal lengths -> zipped pairs; [] or unequal -> null
test("tallyText", ...)        // {0:"got",1:"got",2:"missed"} of 8 -> "2 of 8 got · 1 missed"; {} of 8 -> "0 of 8 got"
test("progressLine", ...)     // both forms above
test("countsAsSection", ...)  // "Self-check answers" false; "Drill set" true; "0.9 Self-check" true
test("newlyRead", ...)        // ends [{a,100},{b,900},{c,50}], vh 800, read {c} -> ["a"]
test("parseStored and load survive bad storage", () => {
  assert.deepEqual(parseStored("{bad", {}), {}); assert.deepEqual(parseStored(null, []), []);
  const saved = globalThis.localStorage;
  globalThis.localStorage = { getItem() { throw new Error("denied"); }, setItem() { throw new Error("denied"); } };
  assert.deepEqual(load("prep:read:x", []), []); assert.doesNotThrow(() => store("prep:read:x", ["a"]));
  globalThis.localStorage = saved;
});
```

- [ ] **Step 2:** Run `node --test app/static/js/tests/lesson.test.mjs`. Expected: FAIL, because nothing is exported yet.
- [ ] **Step 3:** Implement the exports in `lesson.js`. `lesson.js` must import nothing from `ui.js` at module top level that touches the DOM at import time, so the node test can load it. If `h` from `ui.js` is needed later, check that `ui.js` imports cleanly in node, as the existing ui tests do.
- [ ] **Step 4:** Run `node --test app/static/js/tests/`. Expected: all pass.
- [ ] **Step 5:** Commit `lesson.js` and the test with message `Lesson: pure classifiers for callouts, Big-O, reading time, self-check, progress`.

---

### Task 4: `enrichLesson` static styling (callouts, lead, eyebrow, code lines, badges)

**Files:**
- Modify: `app/static/js/lesson.js` (add the DOM glue)
- Modify: `app/static/js/reader.js` (lines 268–289: call order, `collapseAnswers`, solve-card anchor)
- Modify: `app/static/css/app.css` (new lesson section after line 491)

**Interfaces:**
- Consumes: the Task 3 exports.
- Produces:
  - `export function enrichLesson(root: HTMLElement, { path: string, isModule: boolean }) -> void`.
    - In this task it runs: callouts, the "How to play this in an interview" paragraph, `.lead`, eyebrows, code-line marks and Big-O badges.
    - Task 5 adds widgets and Task 6 adds flip cards, both inside the same function.
    - Order inside the function: widgets, flip cards, callouts, paragraphs, lead, eyebrows, code lines, badges.
  - The reader's `article` gains the class `lesson`.
- Class names (fixed so later tasks and the CSS agree):
  - Callouts: `blockquote.call.call-<kind>` with a first child `span.call-lbl`. `rule` callouts put `.big` on the leading `<strong>`. `plain` gets no label.
  - `p.lead` and `div.eyebrow`, which contains `span.eyebrow-num` and `span.eyebrow-time`.
  - `span.sr-num` is the visually hidden number wrapper inside a numbered h2.
  - `span.code-line`, `span.code-line.bad`, `span.code-line.good`.
  - `code.bigo.bigo-fast|bigo-mid|bigo-steep`.
  - `div.call.call-say` wraps the "How to play" paragraph; its label is "Say it like this".
- The eyebrow text is `§0.N · about M min`, or `about M min` for an unnumbered h2. Reading time covers prose words plus code words, from the h2 up to the next h2.

- [ ] **Step 1:** Implement the glue in `lesson.js`.
  - Callouts: for each `blockquote`, derive `first`, `text`, `bold` and `h2` (the nearest preceding h2), call `classifyCallout`, then add the classes and the label span.
  - Badges: for each `td code`, call `bigOClass` on its text and add the classes.
  - Lead: the first `<p>` that directly follows an h2 (skipping nothing).
- [ ] **Step 2:** Implement the eyebrows. Insert `div.eyebrow` immediately before each h2. For a numbered h2, move its leading `0.N ` text into `span.sr-num`. The CSS for `.sr-num` is the usual visually-hidden clip rule. The h2's `textContent` must stay identical.
- [ ] **Step 3:** Implement code-line marking only for `pre > code` blocks whose text contains ✗ or ✓.
  - Split the highlighted children into `span.code-line` wrappers at each `\n`. A token span that contains a newline is cloned on both sides of the split.
  - Mark a line `bad` or `good` when its text after `#` contains ✗ or ✓.
  - Guard: if `code.textContent` differs after the split, restore the saved original children and call `console.warn`.
- [ ] **Step 4:** Wire it into `reader.js`.
  - Call `enrichLesson(md, { path, isModule })` right after `renderMarkdown` and `takeTitle`, before `collapseAnswers`. Add `lesson` to the article's classes.
  - Change the `collapseAnswers` loop condition so it also stops before an element with class `eyebrow`.
  - Change the solve-card anchor so that when `drill.previousElementSibling` is `.eyebrow`, it starts from the eyebrow (and from the `hr` before the eyebrow when there is one).
- [ ] **Step 5:** Add the CSS for every class above, using the Global Constraints values and the mockup lines 27–69. Add the dark-mode block in the same section:
  - Callout tints use the dark `--accent-soft` and `--lvl-*-bg` tokens.
  - Badges use the `--lvl-*` ink/bg pairs: easy for fast, medium for mid, hard for steep.
  - Code-line tints keep the mockup rgba values, because code blocks are dark in both modes.
- [ ] **Step 6: Screenshot check.** Run `bash /tmp/vid/sync.sh`. Then capture:
  - `#/module/04`, full page and `--scroll "#boundary-search-lower_bound-and-upper_bound"`
  - `#/module/03`
  - `#/module/02`, scrolled to the drill set

  Open each PNG next to the mockup and check:
  - callouts have labels and tints;
  - the eyebrow is above each h2 and the number is not shown twice;
  - ✗/✓ lines are tinted and the `lower_bound` docstring is still highlighted;
  - badges are coloured;
  - the `.lead` paragraph is visible.

  For Review Focus 1, click "Show answers" (`--click "details.answers summary"`) and check that only answers are inside. Check that the solve card sits above the drill-set eyebrow and divider. Fix and re-capture until all of this matches.
- [ ] **Step 7:** Run `node --test app/static/js/tests/`. Expected: all pass. Commit `lesson.js`, `reader.js` and `app.css` with message `Lesson pages: callouts, eyebrows, code marks and Big-O badges`.

---

### Task 5: Stepper and compare widgets, plus the three demos

**Files:**
- Modify: `app/static/js/lesson-widgets.js` (add the builders)
- Modify: `app/static/js/lesson.js` (call them from `enrichLesson`)
- Modify: `app/static/css/app.css` (lesson section)
- Modify: `course/modules/04-binary-search.md` (after the boundary-search intro paragraph, about line 606; after the range-convention table, about line 307)
- Modify: `course/modules/03-two-pointers-sliding-window.md` (after the Shape A code block, about line 84)

**Interfaces:**
- Consumes: `parseSteps`, `parseCompare`, `stepCells` and `BlockError` from Task 2.
- Produces:
  - `buildStepper(data) -> HTMLElement` is a `div.widget.stepper` with `tabindex="0"`. It contains:
    - the title;
    - a row of `div.cell` elements (state class `out|mid|ans`, `.ghost`) with `.v` value, `.i` index and `.p` pointer labels;
    - the narration in a `p` with `aria-live="polite"`;
    - Back and Next buttons;
    - a "Step k of N" counter.

    Behaviour: ArrowLeft and ArrowRight act as Back and Next when the widget has focus. Back is disabled at step 1 and Next at step N. There is no autoplay.
  - `buildCompare(data) -> HTMLElement` is a `div.widget.compare`. It contains a `div.seg` of `button`s with `aria-pressed`, the first one on, and a `<dl>` whose `dd` values swap and whose `dt` labels stay put.
    - Inline backticks in values become `<code>`, built with text nodes, never innerHTML.
  - `widgetFor(code: HTMLElement) -> HTMLElement|null` is used by `enrichLesson`. It handles `language-steps` and `language-compare`. On `BlockError` it returns null, appends `p.widget-note` with the text "demo could not be read" under the `pre`, and calls `console.warn(e.message)`. On success it replaces the `pre`.

- [ ] **Step 1:** Implement `buildStepper`, `buildCompare` and `widgetFor`. Call `widgetFor` for every `pre > code.language-steps, pre > code.language-compare` at the start of `enrichLesson`.
- [ ] **Step 2:** Add the CSS: `.widget` with radius 12px, `.cell` states from mockup lines 54–60 (mid `#5b4fd6`/`#ece9fd`/`#3b2fb0`, ans from `--lvl-easy-*`), and `.seg` from mockup lines 47–49. Dark mode uses its own surface and border tokens. Give mid a dark tint (`#2a2550` background, `#b3abf5` ink) and check its contrast by eye in Task 8.
- [ ] **Step 3:** Add the demo blocks. The module 04 `steps` block is spec §6.1 verbatim, with `range: half-open` added. The module 04 `compare` block is spec §6.2 verbatim. Add this module 03 block (trace checked: 1+11=12 > 10, so hi moves; 1+8=9 < 10, so lo moves; 2+8=10, found):

````
```steps
title: Pair sum on a sorted array, target 10
array: 1 2 4 6 8 11
- lo=0 hi=5 | Start at both ends.
- lo=0 hi=5 | 1 + 11 = 12 > 10: 11 is too big for any partner left. hi -= 1.
- lo=0 hi=4 | 1 + 8 = 9 < 10: 1 is too small for any partner left. lo += 1.
- lo=1 hi=4 | 2 + 8 = 10: found the pair (1, 4).
```
````

- [ ] **Step 4:** Add a temporary failure check. Put a `steps` block with no `array:` into the `/tmp/vid/kit` copy of module 06 only, not the repo. Sync with `rsync` excluded for that file, or edit the copy after the sync. Capture it and check that the original code block, the "demo could not be read" note and the console warning all appear. Then remove it.
- [ ] **Step 5: Screenshot check.** Sync, then capture:
  - module 04 scrolled to the stepper: step 1, and after `--click` on Next ×2;
  - module 04 scrolled to the compare widget: both options;
  - module 03 scrolled to the stepper.

  Check:
  - the ghost cell shows "hi" past the end at step 1;
  - the greyed cells match the half-open range;
  - mid is purple and the answer cell is green;
  - the compare rows keep their position across options.

  Iterate until all of this holds.
- [ ] **Step 6:** Run `node --test app/static/js/tests/`. Expected: all pass. Commit the five files with message `Lesson pages: steps and compare widgets with demos in modules 03 and 04`.

---

### Task 6: Flip-card self-check with local tally

**Files:**
- Modify: `app/static/js/lesson.js`
- Modify: `app/static/css/app.css`

**Interfaces:**
- Consumes: `pairSelfCheck`, `tallyText`, `load` and `store` from Task 3.
- Produces:
  - Inside `enrichLesson`, run only when `isModule`, before callouts so the cloned list items get styled too.
  - The questions are the top-level `li` items of the first `<ol>` in the `## 0.9 Self-check` section. The answers are those of the first `<ol>` in `## Self-check answers`.
  - Clone each answer's children into its card; the original answers stay where they are for `collapseAnswers`.
  - The card grid **replaces** the questions `<ol>`. This is my call: the questions live on the card fronts, and the answers stay at the bottom.
  - `div.flip-grid` holds `div.flip-tally`, which contains the `tallyText` output and a `button.link` labelled "Reset". After the tally come the cards.
  - Each card is a `div.flip` with `role="button"` and `tabindex="0"`. It contains `div.flip-in`, which holds `div.flip-f` (the question, plus `span.flip-mark` "✓ got" or "✗ missed") and `div.flip-b` (the answer, plus "Got it" and "Missed it" buttons).
    - Click, Enter or Space toggles the `.open` class. The answer buttons stop propagation.
    - The back face is `aria-hidden` until the card is open.
    - An `aria-live="polite"` region announces "Answer shown" and "Question shown".
  - Faces stack in a single grid cell (`grid-area: 1 / 1`), not `position: absolute`, so the card is as tall as the taller face.
  - Under `prefers-reduced-motion`, there is no rotate; open hides the front and shows the back.
  - Storage: `load("prep:selfcheck:" + path, {})`, written as `{ [index]: "got"|"missed" }`. Reset stores `{}` and redraws the marks and the tally.

- [ ] **Step 1:** Implement the above. On a count mismatch or a missing list, call `console.warn("self-check: N questions, M answers")` and change nothing.
- [ ] **Step 2:** Add the CSS: flip colours from the Global Constraints, the grid with `repeat(auto-fill, minmax(260px, 1fr))`, and dark mode with `--lvl-medium-*` on the front and `--lvl-easy-*` on the back.
- [ ] **Step 3: Screenshot check.** Sync and capture these from the module 04 §0.9 section:
  - the closed cards;
  - the first card after `--click ".flip"`;
  - after clicking "Got it", then reloading, so the mark persists.

  Check the tally text matches `"1 of N got"`.
- [ ] **Step 4:** Check the mismatch path. In the `/tmp/vid/kit` copy only, delete one answer item from module 03. Capture it and confirm the plain list plus the console warning. Then re-sync.
- [ ] **Step 5:** For Review Focus 3, find the longest module 04 answer (the one with code or several paragraphs), open it, and capture it. Check that nothing is clipped and the card grew.
- [ ] **Step 6:** Run the tests and commit with message `Lesson pages: flip-card self-check with a local tally`.

---

### Task 7: Progress rail

**Files:**
- Create: `app/static/js/rail.js`
- Modify: `app/static/js/reader.js` (replace `buildToc` at lines 98–110 and its call at line 307; make `trackActive` call an `onUpdate` hook)
- Modify: `app/static/css/app.css`

**Interfaces:**
- Consumes: `progressLine`, `countsAsSection`, `newlyRead`, `load` and `store` from Task 3, and `docRoute` from `md.js`.
- Produces:
  - `export function buildRail(root, { path, title, drills }) -> { toc, heads, links, onUpdate } | null`
    - Returns null when there are fewer than 2 headings, as today.
    - `toc` is the same `details.toc` element as today, so the existing sticky CSS, `WIDE` and collapse behaviour carry over. It also gets the class `rail`.
    - The summary shows the title. Below it sit `p.rail-progress`, which holds the `progressLine` text, and `div.rail-bar > span` with its width as a percentage.
    - The h2 links each get `span.rail-dot` (`.on` when current, `.read` when read). The h3 links keep `toc-3`.
    - `links` and `heads` keep `dataset.id` exactly as `trackActive` expects.
  - `onUpdate()`
    - It reads the section end tops: for each counted h2, the last element before the next h2, or the end of `root`.
    - It calls `newlyRead` with the current read set, stores the result under `prep:read:<path>`, then redraws the dots, the line and the bar.
    - It does nothing until the first scroll event in which `window.scrollY` differs from its value at render.
  - `trackActive(rail, container)` calls `rail.onUpdate?.()` at the end of `update()`.
  - In `reader.js`, pass `title` (`mod.id + " · " + mod.title`, or the doc title) and `drills` (`{ solved, count: list.length }` for modules that have a list, else null).

- [ ] **Step 1:** Implement `rail.js` and the `reader.js` changes. Delete `buildToc`.
- [ ] **Step 2:** Add the CSS: dots grey (`--line`), current blue (`--accent`), read green (`--good`); the bar track uses `--track` and the fill `--accent`. Add dark mode. Below `WIDE`, keep today's collapsed `details`.
- [ ] **Step 3: Screenshot check.**
  1. Clear storage with a new browser context. Load module 04 and confirm "0 of M sections read".
  2. Scroll to the bottom, then back to the top. Confirm the dots are green and the bar is full apart from the sections never reached.
  3. Reload and confirm the state persists.
  4. Click a rail link and confirm the `prep:anchor` pinning still highlights the clicked section.
  5. Load `#/module/00` and confirm the read toggle still works and the line has no drills part.
  6. Load a non-module doc, such as `#/doc/course/README.md`.
- [ ] **Step 4:** Run the tests and commit `rail.js`, `reader.js` and `app.css` with message `Lesson pages: progress rail with local read tracking`.

---

### Task 8: Dark mode, narrow width and the full sweep

**Files:**
- Modify: `app/static/css/app.css` (fixes only)

- [ ] **Step 1:** Capture modules 00, 03, 04 and 06 in light mode, in dark mode (`--dark`), and at `--width 760` (which sets narrow below `WIDE`) for 04 and 06. That makes 12 shots. Open every one.
- [ ] **Step 2:** Check against the spec §4 anti-goals:
  - modules 00 and 06, which have few rules, look no worse than `before-04.png`'s style;
  - the drill tools, the solve card, the 00 read toggle, the links and the code highlighting work;
  - dark text is readable on every tint;
  - the rail collapses at narrow width and the widgets fit without horizontal page scroll (the stepper row may scroll inside itself).
- [ ] **Step 3:** Fix and re-capture until every shot passes.
- [ ] **Step 4:** Run `cd ~/leetcode-prep-kit && node --test app/static/js/tests/ && python3 -m unittest discover -s app/tests -t .`. Expected: both green; the Python suite has about 464 tests and ends `OK`.
- [ ] **Step 5:** Check that nothing private is staged: `git status --short` shows no `my-prep/` or statements files. Commit with message `Lesson pages: dark mode and narrow-width fixes`. Stop here: the user reviews the result before the demos for other modules.
