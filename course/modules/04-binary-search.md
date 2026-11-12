# Module 04: Binary search

<!-- toc -->
**Contents**

- [0.1 Prerequisites and the one question](#01-prerequisites-and-the-one-question)
- [0.2 The structure and how it works](#02-the-structure-and-how-it-works)
  - [One boundary, two ways to name it](#one-boundary-two-ways-to-name-it)
  - [The three conditions](#the-three-conditions)
- [0.3 Vocabulary](#03-vocabulary)
- [0.4 Operations and their cost](#04-operations-and-their-cost)
  - [`bisect`: binary search on a sorted sequence](#bisect-binary-search-on-a-sorted-sequence)
  - [Searching part of an array: pass bounds, never slice](#searching-part-of-an-array-pass-bounds-never-slice)
- [0.5 The primitives](#05-the-primitives)
  - [Primitive 1: the invariant](#primitive-1-the-invariant)
  - [Primitive 2: the range convention, `\[lo, hi\]` or `\[lo, hi)`](#primitive-2-the-range-convention-lo-hi-or-lo-hi)
  - [Exit condition vs termination: `lo < hi` or `lo <= hi`](#exit-condition-vs-termination-lo--hi-or-lo--hi)
  - [`hi = len(nums)` or `len(nums) - 1`?](#hi--lennums-or-lennums---1)
  - [Which variable holds the answer when the loop ends](#which-variable-holds-the-answer-when-the-loop-ends)
  - [Primitive 3: the midpoint](#primitive-3-the-midpoint)
  - [Which branch keeps `mid`](#which-branch-keeps-mid)
  - [Progress and safety](#progress-and-safety)
  - [Index vs value](#index-vs-value)
- [0.6 Inputs that break it](#06-inputs-that-break-it)
- [0.7 Complexity, out loud](#07-complexity-out-loud)
- [0.8 Signals](#08-signals)
- [0.9 Self-check](#09-self-check)
- [Exact match: the canonical template](#exact-match-the-canonical-template)
- [Boundary search: `lower_bound` and `upper_bound`](#boundary-search-lower_bound-and-upper_bound)
  - [What the two bounds buy you](#what-the-two-bounds-buy-you)
- [Binary search without sortedness: the mountain array](#binary-search-without-sortedness-the-mountain-array)
- [Rotated sorted arrays](#rotated-sorted-arrays)
  - [The structure](#the-structure)
  - [The move: one half is always sorted](#the-move-one-half-is-always-sorted)
  - [Searching for a target](#searching-for-a-target)
  - [Finding the minimum: a question to answer before you write it](#finding-the-minimum-a-question-to-answer-before-you-write-it)
- [Binary search on an answer space](#binary-search-on-an-answer-space)
  - [The inversion](#the-inversion)
  - [Integer square root, in full](#integer-square-root-in-full)
  - [Minimum days to make m bouquets, in full](#minimum-days-to-make-m-bouquets-in-full)
  - [Is a True guaranteed to exist?](#is-a-true-guaranteed-to-exist)
  - [Never materialise the search space](#never-materialise-the-search-space)
  - [The two templates, and which to use](#the-two-templates-and-which-to-use)
- [Structure has to match the query](#structure-has-to-match-the-query)
- [The three loop shapes, side by side](#the-three-loop-shapes-side-by-side)
- [How to attack a binary search problem](#how-to-attack-a-binary-search-problem)
- [When not to reach for binary search](#when-not-to-reach-for-binary-search)
- [Common binary search mistakes](#common-binary-search-mistakes)
- [Not covered here](#not-covered-here)
- [Drill set — cold, no IDE, no running](#drill-set--cold-no-ide-no-running)
- [Before you submit anything](#before-you-submit-anything)
- [Self-check answers](#self-check-answers)
<!-- /toc -->

This module covers binary search. It is the narrowest topic in the course: there is essentially **one algorithm**, and it wears four costumes. Exact match in a sorted array, boundary search (`lower_bound` and `upper_bound`), rotated sorted arrays, and search over a range of possible answers are the same loop with a different search space and a different yes/no question.

**Read §0 before you attempt anything.** For arrays the irreducible thing was the hash table; for two pointers it was the pointer pair. Here it is **the invariant**, and this is the one module where the invariant isn't something you bolt on afterwards. It *is* the algorithm. The instinct, *"halve it"*, is the easy part. A search whose invariant was never stated moves `lo` and `hi` by feel, and no amount of care with the code saves it.

The drill set at the bottom is deliberately **not solved anywhere in this file**. Every example the sections walk through uses a problem outside the drill set.

**How to use it.** Read §0, then answer the self-check in §0.9 and re-read the parts of §0 behind any question you miss. Then work through the sections from the exact-match template to the three loop shapes, and do the drill set cold.

| Section | What it gives you |
|---|---|
| §0, the foundation | the one question, the false-then-true model, the vocabulary, what each operation costs, the primitives (invariant, range convention, midpoint, progress and safety, index vs value), the inputs that break a search, the signals |
| Exact match | the canonical template, traced on a hit and on a miss |
| Boundary search | `lower_bound` and `upper_bound`, one character apart, and what the two of them answer |
| The mountain array | binary search with no sorted order at all |
| Rotated sorted arrays | the structure, the one-half-is-sorted move, and the questions to answer before searching one |
| Answer space | searching the range of possible answers instead of an array |
| Structure has to match the query | when a sorted sequence beats a hash |
| The three loop shapes | exact match, first true, record and continue, side by side |
| How to attack a binary search problem | the steps, in order |
| Common binary search mistakes | the bugs, each linked to its checklist entry or section |
| Drill set | the problems, with the checkpoint |
| Before you submit anything | the checklist |

---

## 0.1 Prerequisites and the one question

| You need | From | Used here for |
|---|---|---|
| Counting cost: how many times it runs × what one run costs | [00-before-you-start.md](00-before-you-start.md#counting-loops) | §0.7: deriving the log instead of recalling it |
| Reading the constraints | [00-before-you-start.md](00-before-you-start.md#reading-the-constraints) | §0.8: a limit of 10⁹ on the values with a small array is a signal |
| The call stack | [00-before-you-start.md](00-before-you-start.md#recursion-and-the-call-stack) | §0.7: why the recursive form is not O(1) space |
| The three escapes: Remember, Order, Reuse | [01-arrays-hashing.md](01-arrays-hashing.md#the-three-escapes-remember-order-reuse) | the one question below: binary search is escape 2 |
| The list: a row of numbered slots | [01-arrays-hashing.md](01-arrays-hashing.md#the-list-a-row-of-numbered-slots) | reaching the middle element in O(1), which is what makes a probe cheap |
| Sorting costs O(n log n) | [01-arrays-hashing.md](01-arrays-hashing.md#sorting-as-a-tool) | sort once, then search many times |
| Space: total vs auxiliary | [01-arrays-hashing.md](01-arrays-hashing.md#space-total-vs-auxiliary) | §0.7: the call stack counts |
| The two obligations of an invariant: true before iteration 1, and kept by the body | [02-stacks-queues.md](02-stacks-queues.md#say-the-sentence-before-the-loop-body) | §0.5, §Progress and safety |
| The invariant, and off-by-ones as invariant violations | [03-two-pointers-sliding-window.md](03-two-pointers-sliding-window.md#the-invariant-is-the-correctness-tool) | §0.5: reading `lo < hi` or `lo <= hi` off the range convention |

Module 01's three escapes answered *"how do I avoid looking at every pair?"* Binary search is **escape 2, Order**, pushed to its limit. Its question is one step further down.

**The one question this module answers:**

> *The obvious solution examines every **element**: one loop, O(n). How do I get the same answer without doing that?*

For an unstructured array it is impossible: if the array tells you nothing, you have to look at everything. So the whole topic reduces to:

> **What structure lets me throw away half the search space after looking at one element?**

Answer that and the code is eight lines. Every bug in binary search is a bug in *that* answer, not in the eight lines.

---

## 0.2 The structure and how it works

Most people learn binary search as *"finding a value in a sorted array."* That definition is too small, and it's why the rotated and answer-space variants look like different algorithms. They aren't.

Here is the real requirement. You need **a search space** and **a yes/no question about each point in it**, the *predicate* `P`, such that:

> **Once `P` becomes true, it stays true.**

Lay the search space out in a line and evaluate `P` at every point, and it must look like this:

```
index:   0   1   2   3   4   5   6   7
P(i):    F   F   F   F   T   T   T   T
                       ↑
                 the boundary: the only interesting point
```

`P` is **monotone**: `F…F T…T`, never `F T F`. Under that condition, evaluating `P` at *one* point tells you which side the boundary is on, and you discard the other half. A halving per probe is what produces the log.

**Every variant in this module is a choice of search space and predicate:**

| Variant | Search space | Predicate `P(x)` |
|---|---|---|
| Exact match in a sorted array | the **indices** `0..n-1` | `nums[x] >= target` |
| `lower_bound` | the indices `0..n` | `nums[x] >= target` |
| `upper_bound` | the indices `0..n` | `nums[x] > target` |
| First bad version | version numbers | `is_bad(x)` |
| Peak in a mountain array | the indices | `nums[x] > nums[x+1]` ("I'm on the descending side") |
| Rotated array | the indices | "is the answer to my right?": **derived**, not read off |
| **Answer space** | the range of possible **answers** | `feasible(x)` |

**Sortedness is not the requirement. Sortedness is just the most common way to *get* monotonicity.** A sorted array makes `nums[x] >= target` monotone for free. A mountain array isn't sorted at all, and binary search still works, because `nums[x] > nums[x+1]` is monotone on it.

> **The question to ask on every binary-search problem, before writing anything:**
> **"What is my search space, and what is the yes/no question that is false-then-true across it?"**
> If you can't answer that in one sentence, you are not ready to write the loop. If you can, the loop writes itself.

### One boundary, two ways to name it

A natural question: *if the predicate goes false-then-true, am I always looking for the first T?*

A monotone `F…F T…T` predicate has **exactly one** boundary. Not "usually one": one, by definition. It flips, and it flips once. So locating it is always the same job, and the boundary loop (§The three loop shapes, shape B) returns **the first T**.

The distinction to keep: **the first T and the last F are the same boundary named from opposite sides**, one index apart.

```
index:   0   1   2   3   4   5
P(i):    F   F   F   T   T   T
                 ↑   ↑
            last F   first T          last F == first T − 1
```

| The problem asks for | Return |
|---|---|
| "the **first** / smallest / minimum X that works" | `lo`: the first T |
| "the **last** / largest / maximum X that still works" | `lo - 1`: the last F |

> **Monotone predicate ⇒ exactly one boundary ⇒ always locatable as "the first T."**
> **Which side of it the problem wants is a *reading* question, not an algorithm question.**

Decide it before writing the loop. Afterwards it's invisible: the search is perfect and the answer is one off.

**And if your predicate comes out `T…T F…F`, negate it.** `not P` is `F…F T…T`, and you are back to the only loop you need. (§The two templates, and which to use has the two alternatives, the mirrored loop and the record-and-continue form, for when negating is awkward.)

### The three conditions

1. **A search space you can address by number**: indices, or a range of integer values.
2. **A monotone predicate over it**: `F…F T…T`.
3. **The predicate is cheap to evaluate**: O(1) for an array lookup, O(n) for a "simulate this candidate" check. It multiplies your total cost, so it needs to be worth it.

## 0.3 Vocabulary

| Term | Meaning |
|---|---|
| **search space** | the set of points you are choosing between: the indices of an array, or a range of candidate answers |
| **predicate** | the yes/no question `P(x)` you ask about one point of the search space |
| **monotone** | once the predicate is true it stays true: `F…F T…T`, never `F T F` |
| **boundary** | the one place a monotone predicate flips; the first T, or equally the last F one step to its left |
| **probe** | one evaluation of the predicate, at `mid` |
| **`lo`, `hi`** | the ends of the range that can still hold the answer. Not "the ends of the array" |
| **closed range `[lo, hi]`** | `hi` is itself a candidate |
| **half-open range `[lo, hi)`** | `hi` is one past the last candidate |
| **invariant** | the sentence true at the top of every iteration: *the answer, if it exists, is inside the current range* |
| **down-biased midpoint** | `(lo + hi) // 2`: rounds down, so it can equal `lo` but never `hi` when `lo < hi` |
| **up-biased midpoint** | `(lo + hi + 1) // 2`: rounds up, so it can equal `hi` but never `lo` |
| **candidate** | a point not yet ruled out. A probe that tests true is still only a candidate |
| **converging loop** | `while lo < hi`: runs until one candidate survives, then returns it |
| **`lower_bound`** | the first index `i` with `nums[i] >= target`; `len(nums)` if there is none |
| **`upper_bound`** | the first index `i` with `nums[i] > target`; `len(nums)` if there is none |
| **rotated sorted array** | a sorted array cut once and its two pieces swapped: `[4, 5, 6, 7, 0, 1, 2]` |
| **run** | one of the two sorted pieces of a rotated array |
| **answer space** | a search space made of candidate answers rather than array positions |
| **feasible** | the predicate of an answer-space search: *"does this candidate work?"* |

## 0.4 Operations and their cost

**n** is the length of the array; **R** is the size of the range of candidate answers, `hi - lo`.

| Operation | Python | Big-O | Trap |
|---|---|---|---|
| Compute the midpoint | `mid = (lo + hi) // 2` | O(1) | `%` gives 0 or 1, and `hi // 2` ignores `lo` |
| Read the middle element | `nums[mid]` | O(1) | with `hi = len(nums)` and `while lo <= hi`, `mid` can reach `len(nums)`: `IndexError` |
| One whole search over a sorted array | the loop | O(log n) | only if each probe is O(1) |
| One probe of an answer-space check | `feasible(mid)` | the cost of the check, often O(n) | it multiplies the whole search: O(log R × check) |
| Library boundary search | `bisect.bisect_left(nums, x)` | O(log n) | returns an index in `[0, len(nums)]`; `len(nums)` is a legal answer, not a missing one |
| Insert keeping the list sorted | `bisect.insort(nums, x)` | **O(n)** | the search is O(log n), but the insert shifts every later element |
| Cut out the region to search | `nums[lo:hi]` | **O(hi − lo)** | a slice is a copy; pass `lo` and `hi` instead. §Searching part of an array |
| Sort before searching | `nums.sort()` | O(n log n) | worth it only if you search many times; for one query, a linear scan is cheaper |
| Membership on a list | `x in nums` | **O(n)** | a linear scan, even when the list is sorted |
| List every candidate | `list(range(lo, hi + 1))` | **O(R)** time and space | never: `lo` and `hi` already describe the range |

### `bisect`: binary search on a sorted sequence

**If the helper has a standard-library name, say the standard-library name.**

```python
import bisect

bisect.bisect_left(nums, x)      # == lower_bound: first index where nums[i] >= x
bisect.bisect_right(nums, x)     # == upper_bound: first index where nums[i] >  x
bisect.insort(nums, x)           # insert x keeping the list sorted (the insert is O(n))
```

Both searches are O(log n) and both return an **index in `[0, len(nums)]`**, `len(nums)` meaning "everything is smaller, it belongs at the end."

**How to play this in an interview:** *"This is a `lower_bound`; in Python I'd reach for `bisect.bisect_left`. Do you want me to write the search out?"* Naming the library function shows you know the language; offering to hand-write it shows you know the algorithm. **They nearly always want it written out**: binary search is being tested *as* the skill here, unlike `sorted()`, where the sort is only a means. That's the one exception to "always use the built-in."

`bisect_left` and `bisect_right` are also the honest way to say what your loop is doing, which is why they get their own section below (§Boundary search).

### Searching part of an array: pass bounds, never slice

The moment a problem splits an array into regions that you search separately, you need to search **part** of it. The obvious move is to cut the part out:

```python
left = nums[:index]        # ✗
right = nums[index:]       # ✗
```

Trace what that one decision causes:

| Consequence | The bug it produces |
|---|---|
| **Copies the array** | **O(n) time and O(n) space.** The O(log n) claim is now false: the slice alone costs more than the entire search it feeds |
| **Indices become relative to the slice, not `nums`** | forces `+ offset` on the result, and then **`-1 + offset`**, because "not found" is also a number |
| **An empty region becomes an empty list** | `region[lo]` on `[]` is an **`IndexError`** |

**All three vanish if the search takes bounds instead of a list:**

```python
def search(lo, hi, target):        # searches nums[lo..hi] in place
    ...                            # returns an index into NUMS: no offset to add
```

- No copy, so the complexity claim survives.
- It returns an absolute index, so there is no offset arithmetic and no `-1 + offset`.
- An empty region is just `lo > hi`. With the closed loop (`while lo <= hi`) that's *already* handled: the body never runs and you fall through to `return -1`. **No guard needed.**

> **The offset arithmetic was never a second problem to solve. It was a problem the slice created and then forced you to solve.** The cheapest bug to fix is the one your structure never permits.

This is the slice row of module 01's cost table ([01-arrays-hashing.md](01-arrays-hashing.md#04-operations-and-their-cost)): *`nums[i:j]` copies*. Here it costs an **asymptotic claim** rather than just being untidy. Stating the complexity out loud is what catches it: you cannot say "logarithmic" with `nums[:index]` on screen without one of the two being wrong.

⚠️ **Keep the parameter order `(lo, hi)`, in that order, always.** A helper whose signature is `(hi, lo)` and whose call site passes low-then-high produces a loop condition that is false on entry: the body never executes, on any input, and the function silently degenerates into checking nothing ([bug-checklist.md](../reference/bug-checklist.md#a-parameter-order-that-contradicts-the-caller), §A parameter order that contradicts the caller). Names that contradict what the caller passes are the index-vs-value bug one level up.

## 0.5 The primitives

Five primitives, and every one of them is decided **before** the loop body: the invariant, the range convention, the midpoint, progress and safety, and what each variable holds.

### Primitive 1: the invariant

This is the centre of the module. Everything else is bookkeeping.

> **The invariant of a binary search: *the answer, if it exists, is inside the current range.*** Nothing outside `[lo, hi]` can be the answer any more.

Say it in the specific form for the problem you're on, **before writing the loop body**:

| Problem | The invariant sentence |
|---|---|
| Exact match | *"If `target` is in `nums`, its index is in `[lo, hi]`."* |
| `lower_bound` | *"The boundary, the first index with `nums[i] >= target`, is in `[lo, hi]`."* |
| Minimum of a rotated array | *"The minimum's index is in `[lo, hi]`."* |
| Answer space, minimising | *"The smallest feasible candidate is in `[lo, hi]`."* |

Then **every line in the loop body has exactly one job: leave that sentence true.** When you write `hi = mid - 1`, you are claiming *"I have proved nothing at index `mid` or beyond can be the answer."* If you can't make that claim out loud, the line is wrong, however natural it looks.

**Three things fall out of the invariant, which is why it comes first:**

1. **The loop condition.** `while lo <= hi` or `while lo < hi` is *determined* by the range convention (primitive 2), not chosen by taste.
2. **The updates.** `hi = mid - 1` against `hi = mid` is determined by whether you've ruled `mid` out. Ruled out: skip it. Still a candidate: keep it.
3. **The return.** When the loop ends, the invariant plus the exit condition tells you what you're holding.

### Primitive 2: the range convention, `[lo, hi]` or `[lo, hi)`

Two conventions. Both are correct. **Mixing them is where most off-by-one and infinite-loop bugs in this topic come from.** Pick one per function, deliberately, and let it dictate all four decisions.

| | **Closed** `[lo, hi]` | **Half-open** `[lo, hi)` |
|---|---|---|
| Meaning | `hi` **is** a candidate | `hi` is **one past** the last candidate |
| Initialise | `lo, hi = 0, len(nums) - 1` | `lo, hi = 0, len(nums)` |
| Range is non-empty when | `lo <= hi`, so **`while lo <= hi`** | `lo < hi`, so **`while lo < hi`** |
| Discard the right half | `hi = mid - 1` | `hi = mid` |
| Range size | `hi - lo + 1` | `hi - lo` |
| Ends when | `lo > hi`: the range is **empty** | `lo == hi`: the range is **empty**, and `lo` is the boundary |

**Read the "range is non-empty" row again: that's the whole derivation of the loop condition.** The loop runs exactly while there is still something left to check. Under `[lo, hi]` a range with `lo == hi` still holds one element, so the loop must run: `<=`. Under `[lo, hi)` a range with `lo == hi` holds nothing: `<`.

> **You never guess `<` against `<=`. You state the convention and read the operator off it.** This is the concrete form of module 03's rule that *off-by-ones are invariant violations* ([03-two-pointers-sliding-window.md](03-two-pointers-sliding-window.md#the-invariant-is-the-correctness-tool); [bug-checklist.md](../reference/bug-checklist.md#off-by-ones-derive-never-freehand), §Off-by-ones: derive, never freehand).

**The length of an inclusive range is `end - start + 1`**, and this is where it earns its keep. `[3, 3]` holds one element: `3 - 3 + 1 = 1`. `[3, 2]` holds `2 - 3 + 1 = 0`. Empty. That's why `lo > hi` is the exit test.

#### Which one to use

| Use | When |
|---|---|
| **Closed `[lo, hi]`, `while lo <= hi`** | **Exact match.** You need `mid` compared for equality, and "not found" must be reachable: the empty range *is* the answer |
| **Half-open `[lo, hi)`, `while lo < hi`** | **Boundary search.** `lower_bound`, `upper_bound`, first true, answer space. The loop converges to one surviving candidate and you return `lo` |

**The second form is the one worth owning.** It generalises: it answers *"where is the F→T boundary"*, which covers exact match too (find the boundary, then check whether it holds your target). Most of the drill set is boundary search.

### Exit condition vs termination: `lo < hi` or `lo <= hi`

A common fused argument: *"the condition is `<` because `lo` keeps rising and will eventually be greater than `hi`."* That is a **termination** argument being used as an **exit-condition** derivation, and in the converging loop `lo` never does pass `hi`.

| Question | What it's called | Answered by |
|---|---|---|
| **When do I stop?** | the exit condition | *how many candidates remain.* The converging loop stops with one survivor, so `lo < hi`. The closed loop stops with zero, so `lo <= hi` |
| **Will I ever get there?** | termination, or progress | *does every branch strictly shrink the range.* `hi = mid` shrinks because `mid < hi`; `lo = mid + 1` shrinks because it strictly rises |

Both must hold, and they fail differently: break the first and you return the wrong thing, break the second and you hang (§Progress and safety).

> **The `<` comes from: "with one candidate left, the invariant already tells me it is the answer; there is no work left to do."** Not from `lo` overtaking `hi`.

### `hi = len(nums)` or `len(nums) - 1`?

The question that decides it is not about the array:

> **`lo` and `hi` are not "the ends of the array." They are the smallest and largest values the *answer* could take.**

So **name the most extreme legal answer, and check `hi` can hold it.**

| Can the answer be "past the last element" or "no such index"? | `hi` starts at |
|---|---|
| **No**: the answer is always a real, existing element | `len(nums) - 1` |
| **Yes**: "it belongs at the end", "there is no such index" | `len(nums)` |

| Problem | Most extreme answer | `hi` |
|---|---|---|
| Exact match, `-1` if absent | a real index: absence is signalled by the range going **empty**, not by a value of `lo` | `len(nums) - 1` |
| `lower_bound` / insert position | **`len(nums)`**: the target is bigger than everything | **`len(nums)`** |
| Peak of a mountain array | a real element, which always exists | `len(nums) - 1` |

Two searches can have identical loops and different `hi`, because their invariants differ. *"If present, the target's index is in `[lo, hi]`"* can be at most `n - 1`. *"The insert position is in `[lo, hi]`"* can be `n`.

**The one-line test, run it every time:** *"What if the target is bigger than every element?"* If that has an answer and the answer is `n`, `hi` must be able to reach `n`.

⚠️ **A range that cannot express the answer is a wrong answer, not a crash** ([bug-checklist.md](../reference/bug-checklist.md#bounds-or-state-that-cant-express-the-answer), §Bounds or state that can't express the answer). The invariant is false before the first iteration runs, and every correct line after it is wasted. This is the safety obligation, and it fails silently: no hang, no exception, just a confident off-by-one. **Justify both endpoints out loud before the loop.**

**And `hi = len(nums)` cannot cause an `IndexError`**, the thing that makes people flinch from it. With `while lo < hi` and a down-biased midpoint, `mid < hi` always, so every `nums[mid]` is in range and **`nums[hi]` is never read**. The half-open form isn't indexing one past the end; it's *naming* one past the end as a possible answer.

**This generalises past arrays**, which is the real reason to learn it this way rather than as a rule about `len`: in answer-space search (§Binary search on an answer space) there is no array at all, and `lo` and `hi` are still exactly "the smallest and largest values the answer could take."

⚠️ **Do not blend the conventions.** `lo, hi = 0, len(nums)` with `while lo <= hi` reads `nums[len(nums)]`: `IndexError`. `lo, hi = 0, len(nums) - 1` with `while lo < hi` silently never examines the last element on some inputs: no crash, wrong answer.

### Which variable holds the answer when the loop ends

| Shape | Exit state | The answer is |
|---|---|---|
| **B**, `while lo < hi` | `lo == hi` | **`lo`**, identical to `hi`, so the choice is pure convention |
| **A**, `while lo <= hi` | `lo == hi + 1` | **`mid`, returned from inside the loop.** After the loop the range is empty: there is no answer left to hold |
| either | n/a | **never `mid` after the loop.** `mid` is a probe, not a result |

**Why `lo` and `hi` can never cross in shape B:** with `lo < hi`, the midpoint always satisfies `lo <= mid < hi`. So `hi = mid` leaves `hi >= lo`, and `lo = mid + 1` leaves `lo <= hi`. **The two ends shrink toward each other and meet; they never pass.** Exit is exactly `lo == hi`: one surviving candidate.

**And what makes that survivor the answer is the invariant, not the monotonicity.** The invariant said the answer is inside `[lo, hi]`. The loop preserved it. The range is now one element. Therefore that element is the answer: one line of reasoning, no case analysis.

⚠️ **The converging loop always returns *something*.** It returns the **right** something only if the answer was guaranteed to be inside the *starting* range. If it wasn't, `lo` still converges, still looks like an answer, and is wrong, silently. §Is a True guaranteed to exist? is about exactly that.

**A bonus that unifies the two shapes:** when shape A *fails*, its exit state is `lo == hi + 1`, and at that moment `lo` is exactly the first T (the insertion point) and `hi` is the last F. The same boundary, located by a loop that was looking for something else.

### Primitive 3: the midpoint

```python
mid = (lo + hi) // 2          # ✓ integer division. Rounds DOWN.
mid = lo + (hi - lo) // 2     # ✓ identical in Python; overflow-safe in C/Java
mid = hi // 2                 # ✗ the midpoint of [0, hi]: right only on the first iteration
mid = (lo + hi) % 2           # ✗ this is 0 or 1. Always. It is never a midpoint.
```

`//` is *integer division*; `%` is *remainder*. `(0 + 7) // 2 == 3`. `(0 + 7) % 2 == 1`. **A midpoint is always `//`** ([bug-checklist.md](../reference/bug-checklist.md#-where-you-meant-), §`%` where you meant `//`).

**A midpoint splits *the current range*, and a range has two ends.** `hi // 2` is correct while `lo` is still `0`, so it passes the first iteration and goes wrong the moment `lo` moves ([bug-checklist.md](../reference/bug-checklist.md#a-midpoint-that-ignores-lo), §A midpoint that ignores `lo`). Both broken forms come from writing the formula from memory instead of reading it off the range you just described.

`lo + (hi - lo) // 2` is worth knowing as a *phrase*: in C or Java `lo + hi` can overflow a 32-bit int, and this form can't. Python integers are arbitrary-precision, so it changes nothing here, but saying *"in a fixed-width language I'd write it as `lo + (hi - lo) // 2` to avoid overflow"* is a free signal.

#### The bias, and the infinite loop it causes

`//` **rounds down**, so `mid` is biased toward `lo`. When `hi == lo + 1`:

```python
lo, hi = 0, 1
mid = (0 + 1) // 2            # 0.  mid == lo, and mid != hi
```

That gives you one hard rule:

> **`lo = mid` with a down-biased midpoint is an infinite loop.** `mid` can equal `lo`, so the range never shrinks, and `while lo < hi` spins forever.

```python
while lo < hi:
    mid = (lo + hi) // 2
    if ...:  lo = mid         # ✗ lo=0, hi=1, so mid=0, so lo=0, forever
    else:    hi = mid         # ✓ mid < hi always, so this always shrinks
```

**The safe pairings. Memorise the two rows; they are the whole termination story:**

| Midpoint | Safe updates | Converges to |
|---|---|---|
| `mid = (lo + hi) // 2`, down-biased | **`hi = mid`** and `lo = mid + 1` | the **first** true (leftmost boundary) |
| `mid = (lo + hi + 1) // 2`, up-biased | **`lo = mid`** and `hi = mid - 1` | the **last** true (rightmost boundary) |

**The rule underneath:** the branch that *keeps* `mid` must be the one that moves toward where `mid` can't land. A down-biased `mid` can equal `lo` but never `hi`, so `hi = mid` is always progress and `lo = mid` may not be.

(Under the closed convention with `while lo <= hi`, both updates skip `mid`, `mid ± 1`, so the range always shrinks and this trap can't fire. That is the closed form's one advantage.)

### Which branch keeps `mid`

> **A False is *proof of exclusion*. A True is only a *candidate*.**
>
> Proof: throw it away, `lo = mid + 1`.
> Candidate: keep it, `hi = mid`.

**Say what you just proved before writing the line.** *"`nums[mid] < target`, so `mid` is not the first index with a value ≥ target"* licenses `mid + 1`. *"`mid` passes, but I don't know whether anything before it does"* licenses `hi = mid` and nothing else. `hi = mid - 1` there throws away the answer the moment you find it.

### Progress and safety

Module 02's two obligations, true at the start and kept by the body, are both **safety** here; **progress** is the new one, because a binary search loop can fail to end.

A binary search loop is correct when it satisfies both, and you should check both explicitly before you say you're done:

| Obligation | Means | Failure |
|---|---|---|
| **Progress** | every iteration makes the range **strictly smaller** | **a hang** |
| **Safety** | every iteration leaves the invariant true: the answer is still inside the range | **a wrong answer, silently** |

Two properties, two failure modes. **Knowing which one you broke tells you which line to look at**, which beats re-reading the whole function. A hang is a `lo = mid`, or a branch that didn't shrink the range. A wrong answer is a bad predicate or bad bounds.

**Safety starts before the first iteration.** In module 02 the initial state was free: an empty stack is trivially correct. Here it isn't. The starting `lo` and `hi` are themselves a claim that the answer is inside them, and if that claim is false, every iteration after it preserves a lie.

### Index vs value

This is the most common binary-search bug ([bug-checklist.md](../reference/bug-checklist.md#index-vs-value), §Index vs value). **Say which one every variable holds, out loud, before the loop.**

| Holds a **position** | Holds a **value** |
|---|---|
| `lo`, `hi`, `mid` | `nums[lo]`, `nums[hi]`, `nums[mid]`, `target` |

```python
if mid == target:            # ✗ comparing a POSITION to a VALUE. Runs. Lies.
if nums[mid] == target:      # ✓

hi = nums[mid] - 1           # ✗ assigning a VALUE into a POSITION
hi = mid - 1                 # ✓

return nums[lo]              # ✗ or ✓: depends entirely on the signature. Read it.
```

**The comparison is always value against value; the assignment is always position to position.** One line of the loop body compares values, the rest move positions. If a line does both, it's wrong.

> ⚠️ **And then answer-space search inverts it.** There, `lo`, `hi` and `mid` are **values**, candidate answers, and there may be no array to index at all. `mid` means "a capacity of 4", not "position 4". **Name them for what they hold**: `lo, hi, mid` when they're positions; `lo, hi, cand`, or the noun of the problem, when they're candidate answers. See §Binary search on an answer space.

**And check the return type against the signature** ([bug-checklist.md](../reference/bug-checklist.md#returning-the-wrong-type), §Returning the wrong type). Two problems on the same rotated array can want different things: one the minimum's **value**, the other the target's **index**. Same array, different loops, different return types. Read the signature before you write the first line.

## 0.6 Inputs that break it

| Input | What breaks | Check |
|---|---|---|
| The empty array | closed: `hi = -1`, the loop never runs, `return -1` is right. Half-open: returns `0`, which is not an element | does the caller read `nums[result]` without a bounds check? |
| One element | the converging loop with `hi = len(nums) - 1` never runs and returns `lo = 0` without testing it | is index 0 really the answer, or does it still need a check after the loop? |
| Two elements | a down-biased `mid` equals `lo`, so `lo = mid` never moves | trace `lo, hi = 0, 1` through every branch |
| A target smaller than everything, or bigger | `lower_bound` returns `0` or `len(nums)`; `nums[len(nums)]` is an `IndexError` | test `i < len(nums)` **before** `nums[i]` |
| A target that lands between two stored values | "first ≥" and "last ≤" agree on an exact hit (with distinct values; with duplicates they bracket the run) and differ by one otherwise, so tests that only hit stored values pass | trace a value in a gap, not just one that is present |
| "Last F" when nothing is false | `lo - 1` is `-1`, and `nums[-1]` silently returns the **last** element | [bug-checklist.md](../reference/bug-checklist.md#a-negative-index-wraps-instead-of-crashing), §A negative index wraps instead of crashing; [python-toolkit.md](../reference/python-toolkit.md#️--1-means-two-completely-different-things), §⚠️ `-1` means two completely different things |
| A rotated array rotated by 0 | logic that assumes there is a drop somewhere finds none | the fully sorted array is a legal input; trace it |
| Duplicates in a rotated array | `nums[lo] == nums[mid] == nums[hi]` says nothing about which half is sorted | read the constraints: are the values distinct? §Not covered here |
| An answer space with no feasible candidate | the converging loop still returns a number, and it is wrong | check that `hi` passes the predicate, or handle "impossible" before the loop |
| An answer space starting at `lo = 0` | zero is often not a legal answer; a check that divides by the candidate crashes | §Never materialise the search space |

## 0.7 Complexity, out loud

**Time: O(log n).** Say **"logarithmic"**.

Compute it rather than recalling it, using module 00's method, *cost = how many times it runs × what one run costs* ([00-before-you-start.md](00-before-you-start.md#counting-loops)):

> The range starts at size `n` and at least halves every iteration: `n → n/2 → n/4 → …`. It stops at size 1. **How many halvings does that take? By definition, log₂ n.** Each iteration is O(1): one midpoint, one comparison, one assignment. So `log₂ n × O(1)` = **O(log n)**.

**Space: O(1)** for the iterative form: three scalars. *O(1) means "does not grow with n", not "is small".*

⚠️ **The recursive form is O(log n) space, not O(1)**: `log n` call frames are live at once, and the call stack counts as auxiliary space ([01-arrays-hashing.md](01-arrays-hashing.md#space-total-vs-auxiliary)). **Write binary search iteratively.** It's shorter, it's constant space, and there's no base-case shape to get wrong.

**The number to have ready:** log₂(1,000,000) ≈ 20. A million elements, twenty probes. That's the sentence that explains *why anyone cares*, and it's the right thing to say when you propose it: *"a linear scan is a million operations, binary search is twenty."*

**When the predicate isn't O(1)**, multiply. This is the answer-space case:

> **O(log(size of search space) × cost of one predicate evaluation).**

An answer-space search whose check is a full pass over the input is `O(n log R)`: `log R` probes over the range of candidate answers, each costing an O(n) pass.

⚠️ **Note what the log is over.** For an array it's `log n`, n = the number of elements. For an answer space it's `log(hi - lo)`, over the *range of values*, which has nothing to do with the array's length. Stating it as "log n" there is wrong, and interviewers notice.

## 0.8 Signals

| In the statement | Reach for | Where |
|---|---|---|
| **"sorted array"** anywhere | binary search, or converging pointers. Sortedness is a gift; not using it is the mistake | §Exact match, §Boundary search |
| **"O(log n)"** in the requirements or the follow-up | binary search: almost nothing else produces a log | §0.2 |
| "find the **first** / **last** X such that…" | boundary search, the `lower_bound` / `upper_bound` shape | §Boundary search |
| "**rotated** sorted array" | the one-half-is-sorted move | §Rotated sorted arrays |
| "**minimum** / **maximum** value such that [something] is possible" | **answer space**: the strongest signal in the module | §Binary search on an answer space |
| "minimise the maximum", "maximise the minimum" | answer space, near-certain | §Binary search on an answer space |
| "how few / how many at most, given a budget" | answer space | §Binary search on an answer space |
| values up to 10⁹ but a small array | you're searching the **value range**, not the array | §Binary search on an answer space |
| "guess the number", "an API you may call a limited number of times" | binary search on the API's domain | §0.2 |
| many queries for "largest ≤ x", "smallest ≥ x", "nearest" | a sorted sequence plus binary search, not a hash | §Structure has to match the query |

> **The tell for answer space, in one line: the thing you're asked to return is a number in a known range, and given a candidate you can *check* it much more easily than you can *find* it.** Checking is the predicate. Then you search.

## 0.9 Self-check

Answer each in a sentence or two, without looking back. The answers are at the bottom of the module. Read the part behind any question you miss.

1. Binary search does not need a sorted array. What does it need? Name the three conditions.
2. Under the half-open convention, why is the loop `while lo < hi`, and why can `hi = len(nums)` never cause an `IndexError`?
3. When does `hi` start at `len(nums)` rather than `len(nums) - 1`? Give the one-line test.
4. With `mid = (lo + hi) // 2`, why can `lo = mid` hang, and on which range? What do you change if a branch must keep `mid` on the `lo` side?
5. In a first-true search, the probe at `mid` comes back true. Why is the update `hi = mid` and not `hi = mid - 1`?
6. A binary search hangs on one input and returns a wrong answer on another. Which of progress and safety did each one break, and where do you look first?
7. Why is searching `nums[lo:hi]` instead of passing `lo` and `hi` a complexity bug, and not just a matter of style?
8. A search runs over the candidate answers `1..10⁹`, and checking one candidate takes a pass over an array of n elements. What is the complexity, and what is the log over?

---

## Exact match: the canonical template

The one to be able to write from muscle memory. Search space: the indices. Predicate: `nums[mid]` against `target`.

**Invariant: *"if `target` is in `nums`, its index is inside `[lo, hi]`."*** Closed range, so `while lo <= hi`.

```python
def search(nums, target):
    lo, hi = 0, len(nums) - 1          # closed range [lo, hi]
    while lo <= hi:                    # non-empty while lo <= hi
        mid = (lo + hi) // 2
        if nums[mid] == target:
            return mid                 # found: mid is a POSITION, and that's the return type
        elif nums[mid] < target:
            lo = mid + 1               # mid and everything left of it is too small: discard
        else:
            hi = mid - 1               # mid and everything right of it is too big: discard
    return -1                          # range went empty, so not present
```

**Why each line is what it is:**

- `hi = len(nums) - 1`: `hi` is a real index, because the range is closed.
- `while lo <= hi`: read off the convention. `lo == hi` is a range of one element, and it still has to be checked.
- `lo = mid + 1`, **not** `lo = mid`: `nums[mid] < target` *proves* `mid` isn't the answer, so keeping it would be dead weight and, once the range is down to one or two elements, an infinite loop under either loop condition.
- `return -1`: the empty range is the "not found" signal, which is why exact match wants the closed form.

**Trace: `nums = [2, 4, 7, 10, 13, 18]`, `target = 13`:**

| iter | `lo` | `hi` | `mid` | `nums[mid]` | vs 13 | action |
|---|---|---|---|---|---|---|
| 1 | 0 | 5 | 2 | 7 | too small | `lo = 3` |
| 2 | 3 | 5 | 4 | 13 | **equal** | `return 4` ✓ |

**And the not-found case, `target = 5`.** This is the one people never trace, and it's where the off-by-ones live:

| iter | `lo` | `hi` | `mid` | `nums[mid]` | vs 5 | action |
|---|---|---|---|---|---|---|
| 1 | 0 | 5 | 2 | 7 | too big | `hi = 1` |
| 2 | 0 | 1 | 0 | 2 | too small | `lo = 1` |
| 3 | 1 | 1 | 1 | 4 | too small | `lo = 2` |
| exit | 2 | 1 | n/a | n/a | n/a | `lo > hi`: empty, so `return -1` ✓ |

Six elements, three probes. `log₂ 6 ≈ 2.6`. And at the exit, `lo = 2` is where 5 would be inserted and `hi = 1` is the last element smaller than it: the bonus from §Which variable holds the answer when the loop ends. **Always trace the not-found path**: a binary search that finds present elements and loops forever on absent ones is the classic half-correct submission.

---

## Boundary search: `lower_bound` and `upper_bound`

The generalisation. Instead of *"is it here?"* you ask *"where does the F→T boundary sit?"*, and that answers far more questions than equality does.

**Both use the half-open range** `[lo, hi)` with `hi = len(nums)`, because **the answer may legitimately be `len(nums)`**: "everything is smaller than `target`, so it belongs off the end." A closed range whose `hi` starts at `n - 1` cannot express that.

```python
def lower_bound(nums, target):
    """First index i with nums[i] >= target.  Returns len(nums) if none."""
    lo, hi = 0, len(nums)              # half-open [lo, hi)
    while lo < hi:
        mid = (lo + hi) // 2
        if nums[mid] < target:
            lo = mid + 1               # mid is F: ruled out, the boundary is strictly right
        else:
            hi = mid                   # mid is T: still a candidate, KEEP it
    return lo                          # lo == hi: the boundary
```

```python
def upper_bound(nums, target):
    """First index i with nums[i] > target.  Returns len(nums) if none."""
    lo, hi = 0, len(nums)
    while lo < hi:
        mid = (lo + hi) // 2
        if nums[mid] <= target:        # the ONLY difference: < becomes <=
            lo = mid + 1
        else:
            hi = mid
    return lo
```

> **One character apart.** `lower_bound` treats "equal to target" as **T** (a candidate, keep it), `upper_bound` treats it as **F** (ruled out, move past it). That single choice is what makes one land at the start of the run of equal values and the other just past its end.

**Note the shape of this loop and how it differs from exact match:**

- There is **no `return mid` inside the loop.** It never exits early: it always runs the full `log n` probes and converges. Slightly more work, dramatically less to get wrong.
- **`hi = mid`, not `mid - 1`**, because `mid` tested T, and a T *might be the boundary itself*. Discarding it would break the invariant.
- **The exit is `lo == hi`, not "found."** The invariant said the boundary is in `[lo, hi)`; when that range collapses, `lo` *is* the boundary.

**Trace: `nums = [1, 2, 2, 2, 3, 5]`, `target = 2`.**

`lower_bound`:

| `lo` | `hi` | `mid` | `nums[mid]` | `< 2`? | action |
|---|---|---|---|---|---|
| 0 | 6 | 3 | 2 | no, so T | `hi = 3` |
| 0 | 3 | 1 | 2 | no, so T | `hi = 1` |
| 0 | 1 | 0 | 1 | yes, so F | `lo = 1` |
| 1 | 1 | n/a | n/a | n/a | exit: **1** ✓ |

`upper_bound`:

| `lo` | `hi` | `mid` | `nums[mid]` | `<= 2`? | action |
|---|---|---|---|---|---|
| 0 | 6 | 3 | 2 | yes, so F | `lo = 4` |
| 4 | 6 | 5 | 5 | no, so T | `hi = 5` |
| 4 | 5 | 4 | 3 | no, so T | `hi = 4` |
| 4 | 4 | n/a | n/a | n/a | exit: **4** ✓ |

### What the two bounds buy you

Everything below is O(log n), and none of it needs a new algorithm:

| Question | Expression |
|---|---|
| Does `x` exist? | `i = lower_bound(nums, x)`; `i < len(nums) and nums[i] == x` |
| **How many times does `x` occur?** | `upper_bound(nums, x) - lower_bound(nums, x)` |
| First index of `x` | `lower_bound(nums, x)` |
| Last index of `x` | `upper_bound(nums, x) - 1` |
| How many elements `< x` | `lower_bound(nums, x)` |
| Where would `x` be inserted? | `lower_bound(nums, x)` |

`[1, 2, 2, 2, 3, 5]`, `x = 2`: `4 - 1 = 3` occurrences. ✓ **And that count is `end - start`: half-open, no `+1`.** The `+1` belongs to *inclusive* ranges. Getting this backwards is the inclusive-length rule (`end - start + 1`) applied to the wrong convention, which is why the convention has to be stated rather than felt.

> ⚠️ **`lower_bound` never says "not found."** It returns where the value *would* go. The existence check is a separate line, and it needs the `i < len(nums)` guard **first**: `nums[len(nums)]` is an `IndexError`. That's a guard against a state your structure genuinely permits, unlike a guard carried over from a problem where the state was reachable ([bug-checklist.md](../reference/bug-checklist.md#guards-copied-from-another-problem), §Guards copied from another problem).

---

## Binary search without sortedness: the mountain array

Proof that §0.2 is the real definition, and the bridge to rotated arrays.

**A mountain array** strictly increases and then strictly decreases: `[1, 3, 5, 4, 2]`. Finding its peak is [LC 852 Peak Index in a Mountain Array](https://leetcode.com/problems/peak-index-in-a-mountain-array/). It is **not sorted**. `nums[mid] >= target` is *not* monotone on it. And binary search works anyway, because a *different* predicate is monotone:

> `P(i) = "nums[i] > nums[i+1]"`: *"I am on the descending side."*
> On the way up this is **F**; from the peak onwards it is **T**. `F…F T…T`. **The peak is the boundary.**

```python
def find_peak(nums):
    lo, hi = 0, len(nums) - 1          # closed on both ends, but a boundary-style loop
    while lo < hi:                     # converge to ONE survivor
        mid = (lo + hi) // 2           # mid < hi always, so mid + 1 is a valid index
        if nums[mid] < nums[mid + 1]:
            lo = mid + 1               # still ascending: the peak is strictly right
        else:
            hi = mid                   # descending (or at the peak): mid is a candidate
    return lo                          # lo == hi: a POSITION. nums[lo] is the value.
```

**Trace: `[1, 3, 5, 4, 2]`:**

| `lo` | `hi` | `mid` | `nums[mid]` vs `nums[mid+1]` | action |
|---|---|---|---|---|
| 0 | 4 | 2 | 5 > 4, descending | `hi = 2` |
| 0 | 2 | 1 | 3 < 5, ascending | `lo = 2` |
| 2 | 2 | n/a | n/a | exit: index **2**, value 5 ✓ |

**Three things to take from this:**

1. **`while lo < hi` with `hi = n - 1` is legal and common.** The range is closed, but the *loop* is boundary-style: it converges to one survivor rather than emptying out. Use it whenever **an answer is guaranteed to exist**: there's no "not found" case to represent, so you never want an empty range.
2. **`mid + 1` is safe precisely because `mid < hi`.** A down-biased midpoint plus `lo < hi` means `mid` can never be the last index. That's a structural guarantee, **so no `if mid + 1 < len(nums)` guard.** A guard against a state your own structure makes impossible is dead code; this is the positive version of the rule.
3. **The comparison is against a *neighbour*, not against a target.** That's the move that unlocks rotated arrays: when there's no global order to exploit, compare *local* structure and derive which side the answer is on.

---

## Rotated sorted arrays

Where the invariant bites hardest.

### The structure

Take a sorted array and rotate it: `[0, 1, 2, 4, 5, 6, 7]` becomes `[4, 5, 6, 7, 0, 1, 2]`. You get **two sorted runs**, and the key fact:

> **Every element of the left run is greater than every element of the right run.**

```
[4, 5, 6, 7, | 0, 1, 2]
 └─ run A ─┘   └─run B┘
 all > all of B     the minimum starts run B
```

So the array is not sorted, but it is *made of* sorted pieces, and the structure is rigid enough to binary-search. Two special cases to keep in mind at all times:

- **Rotation by 0**: `[0, 1, 2, 4, 5, 6, 7]`. Run B is empty; the array is fully sorted. **This is the case that breaks naive solutions**, and it will be in the test set. "Rotated `n` times" means the original array.
- **Duplicates**: `[3, 3, 3, 1, 3]`. Now `nums[lo] == nums[mid] == nums[hi]` tells you *nothing* about which side is which, and the worst case degrades to O(n). The usual versions promise distinct values; the follow-ups with duplicates don't (§Not covered here). Know that the distinction exists: it's a standard follow-up.

### The move: one half is always sorted

Cut anywhere. `mid` lands in run A or run B, and either way **at least one of the two halves is entirely within a single run, so at least one half is sorted.** Identify which, and you get a half where ordinary reasoning applies.

**The test:**

```python
if nums[lo] <= nums[mid]:
    ...   # the LEFT half [lo..mid] is sorted
else:
    ...   # the RIGHT half [mid..hi] is sorted
```

*Why:* if `mid` is in run A, then `lo` is too (run A is a prefix), and everything between them is one ascending stretch, so `nums[lo] <= nums[mid]`. If `mid` is in run B, then `nums[mid]` is from the small run and `nums[lo]` from the large one, so `nums[lo] > nums[mid]`, and `[mid..hi]` is entirely inside run B, hence sorted. If `lo` is in run B too, the range has no drop left in it; it is one ascending run, `nums[lo] <= nums[mid]`, and the left half is correctly called sorted.

**`<=` not `<`** matters: when `lo == mid` (a two-element range) the left "half" is a single element, which is trivially sorted, and `nums[lo] <= nums[mid]` correctly reports T.

### Searching for a target

Once you know which half is sorted, you can ask *"could the target be inside this half?"* **You can answer that only for a sorted half**, because a sorted run's contents are fully described by its two endpoints. **Test both ends.** A test against one end alone forgets that the target can lie beyond the other end of the sorted half, and therefore in the *other* half.

**The invariant is unchanged:** *"if `target` is present, its index is in `[lo, hi]`."* Every discard is a claim that the discarded half provably cannot contain it. **Say the claim before you write the line.**

The assembly is the drill: the comparisons, the loop convention, the equality check, the return value and the not-found case.

### Finding the minimum: a question to answer before you write it

Different problem, same array. Search space: the indices. You want the index (or value) of the minimum, which is **the first element of run B**.

The natural first instinct is to reuse the one-half-is-sorted test and compare `nums[mid]` against `nums[lo]`. **Test that instinct before trusting it.** Here are two arrays, and the same probe:

```
A = [1, 2, 3, 4, 5]     lo=0, hi=4, mid=2: nums[lo]=1 <= nums[mid]=3   minimum at index 0  (LEFT)
B = [3, 4, 5, 1, 2]     lo=0, hi=4, mid=2: nums[lo]=3 <= nums[mid]=5   minimum at index 3  (RIGHT)
```

**Same test result. Opposite conclusions.** So a comparison against `nums[lo]` cannot decide which half to keep: it isn't a monotone predicate for *this* question, whatever it does for finding a target.

Three questions to answer, in order, before writing a line:

1. **Which endpoint is a reliable reference?** There are only two candidates. Run the counterexample above against the other one.
2. **What is the predicate, stated as `F…F T…T`?** Fill in *"P(i) = ..."*, and check it's monotone on both A and B above.
3. **Does an answer always exist?** If yes, you want the converging `while lo < hi` form from §The mountain array, with no early return and no `-1` case to handle.

Get those three right and the loop is four lines. Get question 1 wrong and the code can be flawless and the answer still wrong: the right instinct, with the wrong invariant.

---

## Binary search on an answer space

The variant that most looks like a different algorithm and isn't. **This is the one that turns up as the hard-round question.**

### The inversion

Every search so far has had `lo`, `hi`, `mid` as **positions in an array**. Now:

> **The search space is the range of possible *answers*. `lo`, `hi` and `mid` are candidate answers: values. There may be no array to index at all.**

The enabling observation is always the same:

> **Finding the optimal answer is hard. Checking whether a *given* candidate works is easy.** So don't search for the answer: binary search over the candidates and test each one.

And it works exactly when the test is monotone, which for optimisation problems it usually is by nature:

> **If a capacity of `k` is enough, then `k + 1` is also enough.** `F F F F T T T T`. **The answer is the boundary.**

That sentence, with your problem's nouns substituted in, is the thing to say out loud. It *is* the justification for the whole approach, and it's what the interviewer is listening for.

### Integer square root, in full

`isqrt(x)` is the largest `m` with `m² <= x`. `isqrt(17) = 4`. This is [LC 69 Sqrt(x)](https://leetcode.com/problems/sqrtx/).

- **Search space:** the candidate answers `0 … x`. Not an array. Nothing to sort.
- **Predicate:** `m * m <= x`. **T T T T F F F**, true then *false*, so here you want the **last true** (§The two templates, and which to use has the "record it" idiom).

```python
def isqrt(x):
    lo, hi = 0, x                      # candidate ANSWERS. lo/hi/mid are VALUES.
    best = 0                           # the largest feasible candidate seen
    while lo <= hi:
        mid = (lo + hi) // 2
        if mid * mid <= x:
            best = mid                 # feasible: record it, then reach higher
            lo = mid + 1
        else:
            hi = mid - 1               # too big: the answer is strictly smaller
    return best
```

**Trace: `x = 17`:**

| `lo` | `hi` | `mid` | `mid²` | `<= 17`? | action | `best` |
|---|---|---|---|---|---|---|
| 0 | 17 | 8 | 64 | no | `hi = 7` | 0 |
| 0 | 7 | 3 | 9 | yes | `lo = 4` | 3 |
| 4 | 7 | 5 | 25 | no | `hi = 4` | 3 |
| 4 | 4 | 4 | 16 | yes | `lo = 5` | **4** |
| 5 | 4 | n/a | n/a | n/a | `lo > hi`, exit | **4** ✓ |

**O(log x) time, O(1) space.** Note the log is over **x**, the value, not over any array length. Here `lo = 0` is right: `isqrt(0)` is `0`, so zero is a legal answer. That is the exception, and you should be able to say why.

### Minimum days to make m bouquets, in full

[LC 1482 Minimum Number of Days to Make m Bouquets](https://leetcode.com/problems/minimum-number-of-days-to-make-m-bouquets/). `bloom_day[i]` is the day flower `i` blooms. A bouquet needs `k` **adjacent** bloomed flowers, and each flower can be used once. Return the smallest day on which you can make `m` bouquets, or `-1` if no day is enough.

**The three questions, answered first:**

1. **What is the answer, and what range does it live in?** A day. Before the earliest bloom nothing has bloomed, so `lo = min(bloom_day)`. Once the last flower has bloomed, waiting longer changes nothing, so `hi = max(bloom_day)`.
2. **Given a candidate day, how do I check it, and what does that cost?** Walk the flowers once, counting the current run of bloomed neighbours; each time the run reaches `k`, that's a bouquet and the run restarts. O(n).
3. **Is it monotone?** *"If `m` bouquets can be made by day `d`, they can be made by day `d + 1`"*: every flower bloomed by `d` is still bloomed a day later. `F…F T…T`. The answer is the first T.

And one question the three don't ask: **is a True guaranteed to exist?** Not always. With fewer than `m * k` flowers, even the last day fails. That case is handled before the search, so that `hi` is guaranteed to pass:

```python
def min_days(bloom_day, m, k):
    if m * k > len(bloom_day):
        return -1                          # not enough flowers: no day is ever enough

    def can_make(day):                     # O(n): one pass over the flowers
        bouquets = run = 0
        for bloom in bloom_day:
            if bloom <= day:
                run += 1
                if run == k:               # k adjacent bloomed flowers: one bouquet
                    bouquets += 1
                    run = 0
            else:
                run = 0                    # an unbloomed flower breaks adjacency
        return bouquets >= m

    lo, hi = min(bloom_day), max(bloom_day)   # candidate DAYS; hi is feasible (the early return guarantees it)
    while lo < hi:
        day = (lo + hi) // 2
        if can_make(day):
            hi = day                       # works: maybe an earlier day does too. KEEP it.
        else:
            lo = day + 1                   # fails: strictly later needed
    return lo                              # a VALUE: the smallest feasible day
```

**Trace: `bloom_day = [3, 1, 8, 2, 9, 4]`, `m = 2`, `k = 2`:**

| `lo` | `hi` | `day` | bloomed | bouquets | `>= 2`? | action |
|---|---|---|---|---|---|---|
| 1 | 9 | 5 | `[✓, ✓, ✗, ✓, ✗, ✓]` | 1 | no | `lo = 6` |
| 6 | 9 | 7 | `[✓, ✓, ✗, ✓, ✗, ✓]` | 1 | no | `lo = 8` |
| 8 | 9 | 8 | `[✓, ✓, ✓, ✓, ✗, ✓]` | 2 | yes | `hi = 8` |
| 8 | 8 | n/a | n/a | n/a | n/a | exit: **8** ✓ |

**Complexity, in English:** *"O(n log R) time, where R is the spread between the earliest and latest bloom: log R candidate days, and each check is one pass over n flowers. O(1) extra space."* Note that `lo`, `hi` and `day` are all **values** here; the only index in the function is the one the `for` hides from you.

### Is a True guaranteed to exist?

A monotone predicate is **necessary, not sufficient.** `F F F F F F` is monotone too, and it has no boundary. The converging loop doesn't notice: it shrinks to `lo == hi` and returns that, and it is wrong.

> **The reference must satisfy its own predicate.** Whatever you converge toward, `hi` in a first-true search, has to pass your own test. Check it in three seconds: plug `hi` into the predicate. If it can fail on a legal input, nothing guarantees a T exists.

In the bouquet search, `hi = max(bloom_day)` passes exactly when `m * k <= n`, and the early return makes sure it does. **A special case you can design away beats a special case you handle**: once `hi` is guaranteed to pass, the loop needs no guard, no sentinel and no check after it. Every branch is a place to be wrong.

### Never materialise the search space

```python
candidates = list(range(lo, hi + 1))     # ✗ a billion integers when hi is 10**9: gigabytes, never read
```

> **`lo` and `hi` *describe* the space. Nothing is ever built.** That's the entire reason the technique is O(1) space over a range of 10⁹: you probe about 30 values out of a billion and compute each one arithmetically ([bug-checklist.md](../reference/bug-checklist.md#materialising-every-candidate), §Materialising every candidate).

**A list of candidates is a linear scan waiting to happen; a `lo`, `hi` pair is a binary search.** Writing `feasible` and then trying each candidate in a loop is the brute force of answer-space search: the right check, without the escape.

⚠️ **`lo = 0` is an array-index reflex.** Every array search starts at index 0, so the hand writes it. In answer space `lo` is a **value**, and it must be the smallest value that could be the answer. A rate, a size or a capacity of zero is rarely legal, and when the check divides by the candidate, `lo = 0` is a `ZeroDivisionError`. Name the variables for what they hold, `cand` or the problem's own noun, and the wrong start becomes visible.

### The two templates, and which to use

**Minimise a feasible answer**, "smallest capacity, size or day that works". The common one:

```python
lo, hi = smallest_conceivable, largest_conceivable
while lo < hi:
    mid = (lo + hi) // 2
    if feasible(mid):
        hi = mid                       # works: maybe something smaller does too. KEEP mid.
    else:
        lo = mid + 1                   # doesn't work: strictly bigger needed
return lo                              # smallest feasible
```

**Maximise a feasible answer**, "largest X that still works". ⚠️ **Needs the up-biased midpoint**, or it hangs (§0.5, Primitive 3):

```python
lo, hi = smallest_conceivable, largest_conceivable
while lo < hi:
    mid = (lo + hi + 1) // 2           # the +1 is mandatory here
    if feasible(mid):
        lo = mid                       # works: try bigger. KEEP mid.
    else:
        hi = mid - 1
return lo                              # largest feasible
```

**Or sidestep the bias entirely with the record-and-continue form** (§Integer square root, in full): closed range, `while lo <= hi`, `best = mid` in the feasible branch, both updates skipping `mid`. It costs one variable and **cannot** infinite-loop, because the range always shrinks by at least one. **Under interview pressure, prefer it**: `best` is a real variable that gets read at the end, so it isn't dead code, and you never have to remember which way to bias the midpoint.

#### Setting the bounds

Both bounds must be **provably safe**, and you should say why:

- `lo` = the smallest value that could conceivably be the answer: often 1, or the largest single item when every item must fit in one unit.
- `hi` = a value that is **certainly** feasible, even if absurdly generous: `sum(nums)`, `10**9`. **Generous is free.** Widening the range by a factor of 1000 costs 10 extra probes.

⚠️ **A too-narrow `hi` is a wrong answer, not a slow one.** If the true answer is outside `[lo, hi]`, the invariant was false before the loop even started, and it returns a confidently wrong number. **Justify both endpoints out loud before the loop.**

#### The three questions for any answer-space problem

1. **What is the answer, and what range does it live in?** That gives `lo` and `hi`, both justified.
2. **Given a candidate, how do I check it, and what does that cost?** That gives `feasible`, and the second factor of the complexity.
3. **Is `feasible` monotone?** Say the sentence: *"if `k` works, `k + 1` works."* If it doesn't hold, binary search is invalid and you need a different tool.

Then the fourth, from §Is a True guaranteed to exist?: **does `hi` pass?**

---

## Structure has to match the query

The most transferable idea in the module, and it isn't about binary search.

| Query | Structure |
|---|---|
| "is exactly `x` present?" | **hash**: `set` / `dict`, O(1) |
| "largest ≤ `x`", "smallest ≥ `x`", "nearest", "everything in a range" | **sorted sequence plus binary search**, O(log n) |

**Hashing destroys order.** A `dict` can tell you whether `x` is a key, but not which key is just below it, so a boundary question asked of a hash turns into a linear scan over every key.

> **An O(1) operation asked O(n) times is O(n).** The lookup was never the problem; needing one per key was.

When the data arrives already in order, or can be sorted once, keep it as a sorted list and answer each boundary query with `bisect` (§`bisect`: binary search on a sorted sequence). This is the sorted sequence that module 02's table of structures pointed at.

---

## The three loop shapes, side by side

Everything in this module is one of these. **Choose deliberately, then let the convention dictate the rest.**

| | **A. Exact match** | **B. Boundary (first true)** | **C. Record and continue** |
|---|---|---|---|
| Range | closed `[lo, hi]` | half-open `[lo, hi)`, or closed with `lo < hi` | closed `[lo, hi]` |
| Init | `0, len(nums) - 1` | `0, len(nums)` | `min_ans, max_ans` |
| Loop | `while lo <= hi` | `while lo < hi` | `while lo <= hi` |
| Updates | `lo = mid + 1` / `hi = mid - 1` | `lo = mid + 1` / **`hi = mid`** | `lo = mid + 1` / `hi = mid - 1` |
| Exits when | range empty (`lo > hi`) | one survivor (`lo == hi`) | range empty |
| Returns | `mid` on the hit, else `-1` | `lo` | `best` |
| Early return | yes | **no** | no |
| Use for | is it present? | `lower_bound`, first true, a peak, answer space | answer space, "last true" |

```python
# A: exact match                         # B: first true                        # C: record and continue
lo, hi = 0, len(nums) - 1                lo, hi = 0, len(nums)                  lo, hi = LO, HI
while lo <= hi:                          while lo < hi:                         best = -1
    mid = (lo + hi) // 2                     mid = (lo + hi) // 2               while lo <= hi:
    if nums[mid] == target:                  if P(mid):                             mid = (lo + hi) // 2
        return mid                               hi = mid                           if feasible(mid):
    elif nums[mid] < target:                 else:                                      best = mid
        lo = mid + 1                             lo = mid + 1                           lo = mid + 1
    else:                                    return lo                              else:
        hi = mid - 1                                                                    hi = mid - 1
return -1                                                                        return best
```

For B, the last F is `lo - 1`. **If you only keep one, keep B.** It's the general form, since every question in this module is "where is the F→T boundary", and it has no early return to misplace.

---

## How to attack a binary search problem

1. **Read the signature.** Index or value? `-1`, `""` or a number on failure?
2. **Name the search space and the predicate.** *"I'm searching X; the question that goes false-then-true is Y."*
3. **Check both:** is `P` monotone, **and is a True guaranteed to exist?**
4. **Decide first T or last F**, from the wording, before writing.
5. **State the invariant**, then **justify both bounds out loud.** What is the most extreme legal answer, and can `hi` hold it?
6. **Read the loop condition off the convention.** Never guess `<` against `<=`.
7. Write it. `mid = (lo + hi) // 2`. Candidate: `hi = mid`. Proved out: `lo = mid + 1`.
8. **Run [bug-checklist.md](../reference/bug-checklist.md#the-30-second-pass), §The 30-second pass**, then check that every variable you assigned is read somewhere ([bug-checklist.md](../reference/bug-checklist.md#dead-code), §Dead code).
9. **Trace the miss, not the hit**: a value in a *gap*, the extremes, the un-rotated array, `n = 1`, `n = 2`.
10. **State the complexity in English, unprompted**, and say what the log is over.

## When not to reach for binary search

| Situation | Why not | Use instead |
|---|---|---|
| One query on unsorted data | sorting costs O(n log n) to save an O(n) scan you only do once | a linear scan |
| Repeated exact-membership queries | O(log n) per query where a hash gives O(1) | a `set` or `dict`, module 01 |
| The predicate isn't monotone | one probe no longer tells you which side the boundary is on | a scan, or a different technique |
| A linked list | reaching the middle costs O(n), so the log buys nothing | you'll see this again in module 05 ([05-linked-lists.md](05-linked-lists.md)) |

## Common binary search mistakes

Ordered by how often each happens.

| Mistake | What you see | Entry |
|---|---|---|
| Index vs value | `if mid == target`, `hi = nums[mid] - 1` | [bug-checklist.md](../reference/bug-checklist.md#index-vs-value), §Index vs value |
| The invariant never stated | `lo` and `hi` moved by feel; the code looks right and the answer is off by one | §0.5, Primitive 1 |
| `hi` that can't hold the answer | a confident off-by-one when the target is bigger than everything | [bug-checklist.md](../reference/bug-checklist.md#bounds-or-state-that-cant-express-the-answer), §Bounds or state that can't express the answer |
| `%` for `//` | `mid` is 0 or 1 forever | [bug-checklist.md](../reference/bug-checklist.md#-where-you-meant-), §`%` where you meant `//` |
| `mid = hi // 2` | right on the first iteration, wrong as soon as `lo` moves | [bug-checklist.md](../reference/bug-checklist.md#a-midpoint-that-ignores-lo), §A midpoint that ignores `lo` |
| Conventions blended | `hi = len(nums)` with `while lo <= hi` raises `IndexError`; `hi = len(nums) - 1` with `while lo < hi` never checks the last element | §0.5, Primitive 2 |
| `lo = mid` with a down-biased midpoint | hangs on a two-element range | §0.5, Primitive 3 |
| `hi = mid - 1` when `mid` might be the answer | boundary search overshoots by one | §0.5, §Which branch keeps `mid` |
| `mid` returned after the loop | a probe returned as if it were the result | §0.5, §Which variable holds the answer when the loop ends |
| The not-found path never traced | works on every example, wrong or hanging on an absent target | §Exact match: the canonical template |
| A one-sided range test on a rotated array | can pass the rotated example and fail on the un-rotated input | §Rotated sorted arrays |
| The wrong return type | the index returned where the value was asked for, or the reverse | [bug-checklist.md](../reference/bug-checklist.md#returning-the-wrong-type), §Returning the wrong type |
| Slicing to search a region | O(n) per search, `-1 + offset`, `IndexError` on an empty region | §0.4, §Searching part of an array |
| Parameters declared `(hi, lo)`, called low first | the loop body never runs, on any input | [bug-checklist.md](../reference/bug-checklist.md#a-parameter-order-that-contradicts-the-caller), §A parameter order that contradicts the caller |
| An answer-space `hi` that is too small, or never feasible | a confident wrong number | §Is a True guaranteed to exist?, §Setting the bounds |
| `lo = 0` in an answer space | a meaningless candidate, or `ZeroDivisionError` | §Never materialise the search space |
| The candidate list built | memory blows up, or a linear scan where a search was meant | [bug-checklist.md](../reference/bug-checklist.md#materialising-every-candidate), §Materialising every candidate |
| `lo - 1` when `lo == 0` | the last element returned, no crash | [bug-checklist.md](../reference/bug-checklist.md#a-negative-index-wraps-instead-of-crashing), §A negative index wraps instead of crashing |
| A recursive implementation | O(log n) space claimed as O(1) | §0.7 |
| "log n" on an answer-space problem | the log is over the value range, not the array | §0.7 |

## Not covered here

**Deliberately absent, because it is drill material:** the search behind the hard problem at the end of the drill set. Working out what it searches over is the problem.

**Worth knowing exists:**

- **Rotated arrays with duplicates** ([LC 81 Search in Rotated Sorted Array II](https://leetcode.com/problems/search-in-rotated-sorted-array-ii/), [LC 154 Find Minimum in Rotated Sorted Array II](https://leetcode.com/problems/find-minimum-in-rotated-sorted-array-ii/)): when `nums[lo] == nums[mid] == nums[hi]`, no half can be ruled out, and the worst case is O(n).
- **Maintaining a sorted list under inserts**: `bisect.insort` finds the place in O(log n) but inserts in O(n). Structures that do both in O(log n) are outside the standard library.
- **Real-valued answer spaces**: when the answer is a real number, the loop runs on a precision (`while hi - lo > 1e-6`) or a fixed number of iterations, not on integers.
- **Binary search on a tree**: a binary search tree makes the halving structural. You'll see it in module 06 ([06-trees.md](06-trees.md)).

---

## Drill set — cold, no IDE, no running

**Solutions are not in this file.** Every shape you need is in §0 and the sections above, taught on other problems.

The NeetCode 150 binary search list, reordered so the index-based problems come before the value-based one.

| # | Problem | Focus |
|---|---|---|
| 1 | [Binary Search](https://leetcode.com/problems/binary-search/) (LC 704) | **The from-memory rep** of §Exact match: the canonical template. It doesn't test discovery; it tests whether the template comes out cold, with the not-found path correct |
| 2 | [Search a 2D Matrix](https://leetcode.com/problems/search-a-2d-matrix/) (LC 74) | **Index arithmetic.** `//` and `%` both used, for different things. Say which is which before writing either |
| 3 | [Find Minimum in Rotated Sorted Array](https://leetcode.com/problems/find-minimum-in-rotated-sorted-array/) (LC 153) | The first boundary search on a rotated array. Answer the three questions of §Finding the minimum in writing first. ⚑ **Checkpoint** |
| 4 | [Search in Rotated Sorted Array](https://leetcode.com/problems/search-in-rotated-sorted-array/) (LC 33) | Which half is sorted; a range test on **both** ends; returns an **index** |
| 5 | [Koko Eating Bananas](https://leetcode.com/problems/koko-eating-bananas/) (LC 875) | The full answer-space move: name the range, write the check, argue monotonicity out loud. **`lo`, `hi` and `mid` become values** |
| 6 | [Time Based Key-Value Store](https://leetcode.com/problems/time-based-key-value-store/) (LC 981) | A binary search living **inside a data structure**: design plus search. Decide what each search runs over before writing the class |
| 7 | [Median of Two Sorted Arrays](https://leetcode.com/problems/median-of-two-sorted-arrays/) (LC 4) | **Hard.** Work out what the search space is before writing anything: it is not obvious, and it is the whole problem |

**The order.** Rows 1 to 4 all search **indices**: `lo`, `hi` and `mid` are positions throughout. Row 5 is the inversion, where they become **values** and the array stops being the search space; the NeetCode list puts it third, and it moves to fifth so you make that jump once, at the end, rather than jumping out and back. Row 6 puts a search inside a design, and row 7 is the hard one.

**⚑ Checkpoint at row 3.** LC 153 is the first boundary search on a rotated array: the predicate is not read off the input but derived, and the converging loop has to be right on the un-rotated input as well as the rotated one. If it comes out clean, with the three questions answered before the code, move on. If it doesn't, stop there and reread §0.5 and §Rotated sorted arrays rather than pushing on.

**Spares, if a shape needs a second rep:** [LC 35 Search Insert Position](https://leetcode.com/problems/search-insert-position/) (`lower_bound` under another name: written out in §Boundary search; a from-memory rep) · [LC 278 First Bad Version](https://leetcode.com/problems/first-bad-version/) (the predicate form undisguised; the natural bridge to row 5 if the answer-space jump lands badly) · [LC 34 Find First and Last Position of Element in Sorted Array](https://leetcode.com/problems/find-first-and-last-position-of-element-in-sorted-array/) (both bounds in one answer: written out in §Boundary search; a from-memory rep) · [LC 1011 Capacity To Ship Packages Within D Days](https://leetcode.com/problems/capacity-to-ship-packages-within-d-days/) (answer space, second rep) · [LC 162 Find Peak Element](https://leetcode.com/problems/find-peak-element/) (written out in §The mountain array; a from-memory rep).

*Solved in the sections above, so from memory only:* [LC 69](https://leetcode.com/problems/sqrtx/) · [LC 852](https://leetcode.com/problems/peak-index-in-a-mountain-array/) · [LC 1482](https://leetcode.com/problems/minimum-number-of-days-to-make-m-bouquets/).

## Before you submit anything

Every problem, no exceptions:

1. **Name the pattern and the signal that pointed to it**, before writing code.
2. **State the search space and the predicate.** One sentence: *"I'm searching X, and the question that goes false-then-true is Y."* Then: is a True guaranteed to exist?
3. **State the invariant and the range convention.** `[lo, hi]` or `[lo, hi)`, then read the loop condition off it; don't guess it. Justify both bounds out loud.
4. Write it.
5. Run [bug-checklist.md](../reference/bug-checklist.md#the-30-second-pass), §The 30-second pass. Then the mistakes table above.
6. **Trace it**, your value beside the ground truth. **Include the not-found case and, on a rotated array, the un-rotated one.** Two elements is usually enough to expose an infinite loop.
7. **Say the complexity in English, unprompted**, time *and* space. For an answer space, say **what the log is over.**

If you carry only two things into every submission, carry **the invariant and the bounds**.

---

## Self-check answers

1. A **search space you can address by number** (indices, or a range of integers), a **monotone predicate** over it (`F…F T…T`: once true, it stays true), and a predicate **cheap enough to evaluate** at each probe. Sortedness is only the most common way to get the monotone predicate.
2. Under `[lo, hi)` the range holds `hi - lo` elements, so it is non-empty exactly when `lo < hi`, and the loop runs while something is left. With `while lo < hi` and a down-biased midpoint, **`mid < hi` always**, so `nums[mid]` is always in range and `nums[hi]` is never read: `hi = len(nums)` only *names* one past the end as a possible answer.
3. When **the answer itself can be `len(nums)`**: "it belongs at the end", "no such index". `lo` and `hi` are the smallest and largest values the answer can take. The test: *"what if the target is bigger than every element?"* If the answer is then `n`, `hi` must be able to reach `n`.
4. `(lo + hi) // 2` rounds down, so on a **two-element range** (`hi == lo + 1`) `mid == lo`, and `lo = mid` leaves the range unchanged: the loop spins forever. If the branch that keeps `mid` is the `lo` side, use the **up-biased midpoint** `(lo + hi + 1) // 2` with `hi = mid - 1`, or switch to record-and-continue, where both updates skip `mid`.
5. A True is **only a candidate**: `mid` passes, but the first T may be `mid` itself. `hi = mid - 1` would throw it away and break the invariant. A False is proof of exclusion, which is why only that branch skips `mid` with `lo = mid + 1`.
6. The hang broke **progress**: some branch didn't shrink the range, usually `lo = mid` with a down-biased midpoint. The wrong answer broke **safety**: the answer left the range, or was never in the starting one, so look at the predicate, the updates, and the initial `lo` and `hi`.
7. A slice is a **copy**: O(n) time and space before the search starts, which makes the O(log n) claim false. It also makes the returned index relative to the slice, which forces offset arithmetic (and `-1 + offset`), and an empty region becomes an empty list to index. Passing `lo` and `hi` has none of those problems.
8. **O(n log R)**, with R about 10⁹: about 30 probes, each an O(n) check. The log is over the **range of candidate answers**, not over the array's length, so calling it "O(n log n)" is wrong.
