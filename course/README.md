# The course

<!-- toc -->
**Contents**

- [The modules](#the-modules)
- [What each module builds on](#what-each-module-builds-on)
- [How a module is laid out](#how-a-module-is-laid-out)
- [No solutions to drills](#no-solutions-to-drills)
- [The four-part submission](#the-four-part-submission)
- [Module vs. lesson](#module-vs-lesson)
- [Reference files](#reference-files)
- [The other files](#the-other-files)
<!-- /toc -->

Everything in `course/` is the same for every user: eleven modules, a diagnostic, three reference files and the templates for your own notes. Your own work goes in `my-prep/`, never here.

## The modules

Work them in this order. Each module builds on the ones before it, so the order matters (see [What each module builds on](#what-each-module-builds-on)).

| # | Module | What it covers |
|---|---|---|
| 00 | [Before you start](modules/00-before-you-start.md) | Big-O from zero, recursion and the call stack, the Python interview subset, how to work a problem. No drill set: take its self-check, read what you missed, write the toolkit sections it names from memory, then take the [diagnostic](diagnostic.md) |
| 01 | [Arrays and hashing](modules/01-arrays-hashing.md) | Hashing, running state, prefix sums with a hash map, sorting as a tool |
| 02 | [Stacks and queues](modules/02-stacks-queues.md) | The stack and what it resolves, the monotonic stack and its amortised argument, the queue and `deque` |
| 03 | [Two pointers and the sliding window](modules/03-two-pointers-sliding-window.md) | Converging pointers, the sliding window, the window that needs its maximum |
| 04 | [Binary search](modules/04-binary-search.md) | Exact match, boundary search, rotated sorted arrays, binary search on an answer space |
| 05 | [Linked lists](modules/05-linked-lists.md) | The dummy head, in-place reversal, two pointers on a list, Floyd's cycle detection, building a new list |
| 06 | [Trees, DFS and BFS](modules/06-trees.md) | Tree DFS and BFS, when each applies, level order, discover vs. visit |
| 07 | [Backtracking](modules/07-backtracking.md) | Choose, explore, undo on a recursion tree: the choice loop, the per-path mark, the return rule, pruning |
| 08 | [Graphs](modules/08-graphs.md) | The visited set, grids, components, shortest paths, cycles, topological sort, union-find, weighted graphs |
| 09 | [Dynamic programming](modules/09-dp.md) | The state and the recurrence, top-down and bottom-up, 1-D, grids, two sequences, the rolling array, when it is not DP |
| 10 | [Heaps, top-K and selection](modules/10-heaps.md) | `heapq`, the size-k heap, quickselect, k-way merge, two heaps, what a heap can't do |

## What each module builds on

Each module's §0.1 lists what it takes from earlier modules, and its text links back to them. This table collects those links. **Builds on** is what a module needs before you start it; **Used later by** is who loses something if you skip it. The cells list direct prerequisites only; a module named there brings its own row.

| Module | Builds on, and what it takes from each | Used later by |
|---|---|---|
| 01 | **00**: Big-O, recursion, the Python subset, the five steps and the four-part submission | 02, 03, 04, 05, 07, 09, 10 |
| 02 | **00**: Big-O, the call stack, the Python subset · **01**: the list as a row of numbered slots, what a `dict` or `set` key demands, the three escapes (Remember, Order, Reuse) | 03, 04, 06, 07, 08, 10 |
| 03 | **00**: Big-O · **01**: the three escapes, sorting as a tool, the frequency map and prefix sums · **02**: the deque, and the monotonic stack's amortised argument (the window that needs its maximum) | 04, 05, 10 |
| 04 | **00**: counting loops, reading the constraints, the call stack · **01**: the three escapes, the list's numbered slots, sorting, total vs. auxiliary space · **02**: the two obligations of an invariant · **03**: the invariant as the correctness tool, off-by-ones as invariant violations | 05, 07, 09 |
| 05 | **00**: Big-O, recursion · **01**: the hash set and the escapes · **03**: same-direction and converging pointers, the window · **04**: boundary choices, such as which middle to take | 06, 08, 09, 10 |
| 06 | **00**: recursion, return a value vs. update an answer on the side, stack depth, Big-O · **02**: the queue (`deque.popleft`) for BFS, the stack for iterative DFS · **05**: node objects, following a pointer, `None` at the end | 07, 08 |
| 07 | **00**: recursion, return vs. side answer, stack depth, constraints · **06**: the tree DFS shape, passing a value down, one parent per node · **01**: sorting puts equal values together (skipping duplicates) · **04**: a monotone predicate (which prunes are safe) · **02**: one mention | 08, 09 |
| 08 | **00**: recursion, stack depth, return vs. side answer, constraints · **06**: the DFS and BFS shapes, returning a value up the tree, freezing a level, discover vs. visit, when to go iterative, one parent per node · **02**: a list as a stack, a deque as a queue, the amortised argument · **07**: the per-path mark, which becomes the GREY colour · **05**: node objects, following a pointer, a node is hashable by identity | 09, 10 |
| 09 | **00**: recursion, return vs. side answer, stack depth, constraints · **07**: the subsets tree, the per-path mark · **08**: BLACK as a permanent mark, the O(V + E) argument, recursion depth, Dijkstra · **01**: the escapes (a memo is Remember, a rolling array is Reuse) · **04**, **05**: one mention each | — |
| 10 | **00**: Big-O, best and worst case, space, constraints · **02**: the stack and the queue (its opening recap), the amortised argument (lazy deletion) · **01**: the escapes, why comparison sorting costs n log n · **05**: merging two sorted lists (the k-way merge) · **08**: Dijkstra · **03**: one mention | — |

**Reading it for a skip or a reorder.** To start module N early, read N's row: every module in **Builds on** that you haven't done is a bridge that breaks, and the listed items are what you'd meet unexplained. Starting N early defers the modules between: you do them after N, in order, unless you choose to drop them. To skip module N for good, or to drop a module you deferred, read its **Used later by** column: each of those modules loses what it takes from N. The cheap fix is usually to read the named sections of the skipped module first, not the whole block.

## How a module is laid out

Modules 01–10 share one shape. Module 00 has the same ending, with no drill set.

| Part | What it holds |
|---|---|
| **§0.1–0.9, the foundations** | 0.1 Prerequisites and the one question · 0.2 The structure and how it works · 0.3 Vocabulary · 0.4 Operations and their cost · 0.5 The primitives · 0.6 Inputs that break it · 0.7 Complexity, out loud · 0.8 Signals · **0.9 Self-check**: short concept questions answerable from §0 alone |
| **The teaching sections** | The techniques, each worked on a problem that is not in the drill set, then the common mistakes |
| **The drill set** | `## Drill set — cold, no IDE, no running`: LeetCode problems in order, each adding one thing, with ⚑ checkpoints. 🔒 marks a LeetCode Premium problem |
| **Before you submit anything** | The checks to run on your own code |
| **Self-check answers** | Always the last section, so you can't see them while answering |

Every module opens with a clickable contents block.

## No solutions to drills

**The kit never shows the solution to a drill problem.** The worked examples are always problems outside the drill set, and a drill row says at most what to reach for. If you want a full solution, ask Claude for it; it won't give one unless you ask.

## The four-part submission

Every problem you submit has four parts, in this order (taught in [module 00, §The four-part submission](modules/00-before-you-start.md#the-four-part-submission)):

| Part | What it is |
|---|---|
| **1. The pattern, and the signal that pointed to it** | Said before any code |
| **2. The code, written cold** | No IDE, no running, no lookups |
| **3. Time and space complexity, with the reason** | *"O(\_\_) because \_\_ runs \_\_ times and each costs \_\_"*, for both |
| **4. A hand trace on the degenerate input** | Empty, one element, all equal: the inputs the example doesn't reach |

Before you send it, check the top 5 of `my-prep/bugs.md` against your code.

## Module vs. lesson

| | Module | Lesson |
|---|---|---|
| **When** | Read before a block | Written after it |
| **Where** | `course/modules/0N-*.md` | `my-prep/lessons/0N-*.md`, from `templates/lesson.md` |
| **Whose** | The same for everyone | Yours: your drills, your mistakes, the rules you earned |

The module teaches the topic. The lesson records what the block taught you, from your own work, and it's the file you revise from.

## Reference files

| File | Use it for |
|---|---|
| [reference/decision-rules.md](reference/decision-rules.md) | Which tool to reach for: [signals and what they point to](reference/decision-rules.md#signals--what-to-reach-for), choosing a traversal, a container, a loop condition |
| [reference/python-toolkit.md](reference/python-toolkit.md) | The standard library you're expected to write from memory, and the syntax that bites without an IDE |
| [reference/bug-checklist.md](reference/bug-checklist.md) | [The 30-second pass](reference/bug-checklist.md#the-30-second-pass) before every submission, the two-column trace, and the common bugs |

## The other files

| File | What it is |
|---|---|
| [diagnostic.md](diagnostic.md) | Seven timed problems, taken once after module 00's self-check. It sets the Start levels in your skills matrix |
| [templates/](templates/) | The starting versions of every file in `my-prep/`. The app copies them the first time it starts, or Claude does at discovery if you start there. Neither copies over files that exist |
