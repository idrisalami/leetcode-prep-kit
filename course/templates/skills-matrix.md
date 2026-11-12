# Skills matrix

What you can do today, one row per skill, scored against the level criteria below. Claude fills it from the diagnostic and updates it at the end of every block. Every row starts at `?`.

## The columns

| Column | What goes in it |
|---|---|
| **Priority** | P0 comes up in most coding rounds, P1 in many, P2 only if time is left (discovery can use it for low rows). The defaults below are a starting point; discovery re-sets them from your target, level and timeline |
| **Start** | Set once, by the diagnostic or by the first block that touches the row. Never changed after that |
| **Now** | Your level today. It moves |
| **Evidence** | One line: the latest problem(s), the date and the result. The history goes in `learnings.md`, never here |
| **Last tested** | A date, `<YYYY-MM-DD>`. The rows that haven't been tested for a while are the first to revise |

## Level criteria

| Level | Observable test |
|---|---|
| `?` | Not yet tested |
| 0 | Can't start a standard problem on the topic |
| 1 | Solves with hints, or past the time limit |
| 2 | Solves a Medium unaided, but slowly or with bugs found late |
| 3 | Solves a Medium in ≤25 minutes, out loud, clean, complexity stated |

A working idea that didn't reach a correct solution unaided within the time limit scores 1; no working idea scores 0.

For sections B and C the same scale applies to the habit instead of the topic: 0 = never does it, 3 = does it every time without being asked.

## A. Topics, in module order

| # | Requirement | Module | Priority | Start | Now | Evidence | Last tested |
|---|---|---|---|---|---|---|---|
| A1 | Arrays and hashing, including sorting as a tool and prefix sums | 01 | P0 | ? | ? | | |
| A2 | Stacks and the monotonic stack | 02 | P1 | ? | ? | | |
| A3 | Queues and `deque` | 02 | P1 | ? | ? | | |
| A4 | Two pointers | 03 | P0 | ? | ? | | |
| A5 | Sliding window | 03 | P0 | ? | ? | | |
| A6 | Binary search, including rotated arrays and searching the answer space | 04 | P0 | ? | ? | | |
| A7 | Linked lists | 05 | P1 | ? | ? | | |
| A8 | Trees: traversals, BFS/DFS (when each applies), BST properties | 06 | P0 | ? | ? | | |
| A9 | Backtracking | 07 | P1 | ? | ? | | |
| A10 | Graphs: BFS/DFS, components, topological sort, weighted graphs | 08 | P0 | ? | ? | | |
| A11 | Dynamic programming, 1D and 2D | 09 | P1 | ? | ? | | |
| A12 | Heaps, top-K and selection | 10 | P1 | ? | ? | | |

**Outside the kit.** No module teaches these. Their priority is set at discovery, and a high priority here means "find material outside the kit".

| # | Requirement | Module | Priority | Start | Now | Evidence | Last tested |
|---|---|---|---|---|---|---|---|
| A13 | Intervals beyond merging (module 01 works Merge Intervals in full): inserting an interval, removing the fewest to end overlaps, sweep-line counts | — | set at discovery | ? | ? | | |
| A14 | Tries | — | set at discovery | ? | ? | | |
| A15 | Greedy | — | set at discovery | ? | ? | | |
| A16 | Matrix traversal and simulation | — | set at discovery | ? | ? | | |
| A17 | Bit manipulation | — | set at discovery | ? | ? | | |
| A18 | Design problems (e.g. LRU cache) | — | set at discovery | ? | ? | | |

## B. Craft

These cut across every topic and are scored on every problem, so they default to P0.

| # | Requirement | Module | Priority | Start | Now | Evidence | Last tested |
|---|---|---|---|---|---|---|---|
| B1 | Complexity stated unprompted, with the reason | all | P0 | ? | ? | | |
| B2 | Python without an IDE: no autocomplete, no running the code | all | P0 | ? | ? | | |
| B3 | Python stdlib toolkit: `deque`, `defaultdict`, `Counter`, `heapq`, `sorted` | all | P0 | ? | ? | | |
| B4 | Invariants: stated before the loop body, and maintained | all | P0 | ? | ? | | |
| B5 | Reading the problem signature and the given classes before coding | all | P0 | ? | ? | | |
| B6 | Reaching for built-ins instead of hand-writing them | all | P0 | ? | ? | | |

## C. Interview performance, by rubric dimension

These are scored in every round, so they default to P0. Row C9 counts only if discovery flags it.

### Problem solving

| # | Requirement | Module | Priority | Start | Now | Evidence | Last tested |
|---|---|---|---|---|---|---|---|
| C1 | Clarifies requirements and constraints first | all | P0 | ? | ? | | |
| C2 | Brute force → complexity → optimise, out loud | all | P0 | ? | ? | | |
| C3 | Gets unstuck without freezing | all | P0 | ? | ? | | |

### Coding

| # | Requirement | Module | Priority | Start | Now | Evidence | Last tested |
|---|---|---|---|---|---|---|---|
| C4 | Readable names and structure | all | P0 | ? | ? | | |
| C5 | Manages a 45-minute round to time | all | P0 | ? | ? | | |

### Communication

| # | Requirement | Module | Priority | Start | Now | Evidence | Last tested |
|---|---|---|---|---|---|---|---|
| C6 | Thinks aloud continuously | all | P0 | ? | ? | | |
| C7 | Takes a hint calmly | all | P0 | ? | ? | | |
| C8 | Asks good questions at the end | all | P0 | ? | ? | | |
| C9 | Interviewing in a non-native language (**only if discovery flags it**) | all | only if discovery flags it | ? | ? | | |

### Verification

| # | Requirement | Module | Priority | Start | Now | Evidence | Last tested |
|---|---|---|---|---|---|---|---|
| C10 | Hand-traces an example to find their own bugs | all | P0 | ? | ? | | |
| C11 | Tests edge cases before saying "done" | all | P0 | ? | ? | | |

## Known gaps

*Written after discovery and the diagnostic: the rows that matter most for your target and score lowest, one line each.*

## After the diagnostic

Fill Start and Now, then re-sort the plan. A row already at level 3 costs nothing to skip; a P0 row at level 0 is where the weeks go.
