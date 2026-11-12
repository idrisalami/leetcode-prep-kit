# Coding diagnostic

**Time:** ~2h50 including breaks. Do it in one sitting, after the self-check in [module 00](modules/00-before-you-start.md#self-check) and the toolkit reading it names.
**Purpose:** calibrate the plan. Not a test you pass: a measurement. An inflated result buys you a plan aimed at the wrong problems, which costs you time you may not have.

The seven problems and the rules are the same for everyone, whatever discovery found, so a score means the same thing for every user.

## Rules — these matter more than the problems

1. **No IDE.** A plain text editor or a shared doc. No syntax highlighting, no autocomplete, no linter.
2. **You may not run your code.** Not once. This is the single biggest difference from normal practice and the most common source of failure in a real round.
3. **Hard timer per problem.** When it rings, stop and write down where you got to. Do not run over.
4. **Talk out loud the entire time, and record it** (a phone voice memo is fine). Most interviewers score what you say as much as the code. If you go silent for four minutes, that's data.
5. **No lookups.** No docs, no search engine, no LLM, no editorial. If you don't remember a syntax detail, write your best guess and flag it.
6. **Log honestly.** Half-solved is a more useful data point than solved-with-a-peek.

Between problems: 5 minutes off the screen.

## The problems

The links go to LeetCode: read the problem there, then write your answer in your editor. The same problems are on neetcode.io under the same names, if you prefer it; they aren't linked here because its URLs couldn't be verified.

The tables don't say which pattern each problem uses. Spotting the pattern from the statement is part of what the diagnostic measures, so what each problem tests is at the bottom of this file. Read it after you finish.

### Block 1 — warm-up (25 min)

| # | Problem | Difficulty | Time |
|---|---|---|---|
| 1 | [Contains Duplicate](https://leetcode.com/problems/contains-duplicate/) (LC 217) | Easy | 10 min |
| 2 | [Best Time to Buy and Sell Stock](https://leetcode.com/problems/best-time-to-buy-and-sell-stock/) (LC 121) | Easy | 15 min |

### Block 2 — core (65 min)

| # | Problem | Difficulty | Time |
|---|---|---|---|
| 3 | [3Sum](https://leetcode.com/problems/3sum/) (LC 15) | Medium | 25 min |
| 4 | [Binary Tree Level Order Traversal](https://leetcode.com/problems/binary-tree-level-order-traversal/) (LC 102) | Medium | 20 min |
| 5 | [Find Minimum in Rotated Sorted Array](https://leetcode.com/problems/find-minimum-in-rotated-sorted-array/) (LC 153) | Medium | 20 min |

### Block 3 — stretch (50 min)

| # | Problem | Difficulty | Time |
|---|---|---|---|
| 6 | [Number of Islands](https://leetcode.com/problems/number-of-islands/) (LC 200) | Medium | 25 min |
| 7 | [Implement Trie (Prefix Tree)](https://leetcode.com/problems/implement-trie-prefix-tree/) (LC 208) | Medium | 25 min |

**Why these seven.** Together they span the topics most coding rounds draw on, from hashing to graphs, and each one discriminates something different. Two are warm-ups, three are the core Mediums, and two are a stretch: one on a grid and one where you build the structure yourself.

## Report back

Write your report in `my-prep/diagnostic-report.md`, which Claude copied from [templates/diagnostic-report.md](templates/diagnostic-report.md) at discovery. Fill in one block per problem, straight after its timer rings.

Then paste your code for each, including the broken ones. **Especially** the broken ones: where the code breaks says more than where it works.

## Overall, at the end

- Which problem felt worst, and why?
- At any point did you know the *idea* but not how to write it? (That's a very different gap from not seeing the idea.)
- How did talking out loud feel: natural, or did it interfere with thinking?

That last question matters more than it looks. If narrating breaks your concentration, that's a trainable skill with a known fix, and it's better to start training it in the first block than to discover it in a mock later.

## What happens next

Claude reviews each answer by running it, not by reading it. Then it fills Start, Now, Evidence and Last tested in `my-prep/skills-matrix.md` for every row the diagnostic touched, and writes `my-prep/plan.md` against them. Topics you already own can be shortened or skipped, with your agreement; the P0 rows sitting at level 0 or 1 get the hours.

## For scoring — read after you finish

What each problem discriminates, and the matrix rows it scores. Every problem also scores the craft rows (B) and the interview rows (C) that you showed or didn't.

| # | Problem | What it tests | Rows |
|---|---|---|---|
| 1 | Contains Duplicate | whether you reach for a hash set by reflex, and state the brute force and its cost first | A1 |
| 2 | Best Time to Buy and Sell Stock | whether you see a one-pass version or default to nested loops | A1 |
| 3 | 3Sum | the classic sort-then-two-pointers problem; the duplicate handling is where most people lose time | A4, A1 |
| 4 | Binary Tree Level Order Traversal | plain BFS mechanics | A8, A3 |
| 5 | Find Minimum in Rotated Sorted Array | whether you can reason about binary-search invariants when the array isn't plainly sorted, which is where most binary-search failures live | A6 |
| 6 | Number of Islands | treating a grid as a graph and walking it without revisiting a cell | A10 |
| 7 | Implement Trie (Prefix Tree) | whether you can design a data structure rather than call one | A14, A18 |
