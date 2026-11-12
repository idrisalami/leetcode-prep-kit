# Module 01: Arrays and hashing

<!-- toc -->
**Contents**

- [0.1 Prerequisites and the one question](#01-prerequisites-and-the-one-question)
  - [The three escapes: Remember, Order, Reuse](#the-three-escapes-remember-order-reuse)
- [0.2 The structure and how it works](#02-the-structure-and-how-it-works)
  - [The list: a row of numbered slots](#the-list-a-row-of-numbered-slots)
  - [The hash table: compute where it must be](#the-hash-table-compute-where-it-must-be)
  - [Key design: the hard part of hashing](#key-design-the-hard-part-of-hashing)
- [0.3 Vocabulary](#03-vocabulary)
- [0.4 Operations and their cost](#04-operations-and-their-cost)
- [0.5 The primitives](#05-the-primitives)
- [0.6 Inputs that break it](#06-inputs-that-break-it)
- [0.7 Complexity, out loud](#07-complexity-out-loud)
  - [Space: total vs auxiliary](#space-total-vs-auxiliary)
- [0.8 Signals](#08-signals)
- [0.9 Self-check](#09-self-check)
- [Hashing in practice](#hashing-in-practice)
- [Running state](#running-state)
- [Prefix sums with a hash map](#prefix-sums-with-a-hash-map)
- [Sorting as a tool](#sorting-as-a-tool)
  - [The budget: O(n log n) is free against O(n²)](#the-budget-on-log-n-is-free-against-on²)
  - [Why comparison sorting costs n log n: merge sort](#why-comparison-sorting-costs-n-log-n-merge-sort)
  - [The Python tools](#the-python-tools)
  - [Sort, then one scan](#sort-then-one-scan)
- [Common array and hashing mistakes](#common-array-and-hashing-mistakes)
- [Drill set — cold, no IDE, no running](#drill-set--cold-no-ide-no-running)
- [Before you submit anything](#before-you-submit-anything)
- [Self-check answers](#self-check-answers)
<!-- /toc -->

This module covers arrays (Python's `list`), hash tables (`set` and `dict`), running state, prefix sums and sorting as a tool. Visiting every element of an array is never the hard part: `for x in nums` does it. The hard part is always the same one, and the whole module turns on it:

> **The obvious solution examines every *pair* of elements. How do you get the same answer without doing that?**

There are exactly three ways out of a nested loop, and every technique here is one of them. You'll learn the three, the hash table that powers the first, the running value and the prefix array that power the third, and why a sort costs O(n log n) and is almost always worth paying for.

The drill set at the bottom is deliberately **not solved anywhere in this file**. Every example the sections walk through uses a problem outside the drill set.

**How to use it.** Read §0, then answer the self-check in §0.9 and re-read the parts of §0 behind any question you miss. Then work through the sections from hashing in practice to sorting as a tool, and do the drill set cold.

| Section | What it gives you |
|---|---|
| §0, the foundation | the one question and the three escapes, how a list and a hash table work, the vocabulary, what each operation costs, the four primitives, the inputs that break array code, the signals |
| Hashing in practice | `Counter` and `defaultdict`, and when each one is the right tool |
| Running state | carrying one value forward instead of rescanning the past |
| Prefix sums with a hash map | the "record the past" idea applied to sums |
| Sorting as a tool | why sorting is O(n log n), what Python gives you, and the sort-then-scan shape |
| Common array and hashing mistakes | the bugs, each linked to its checklist entry or section |
| Drill set | the problems, with the checkpoints |
| Before you submit anything | the checklist |

---

## 0.1 Prerequisites and the one question

| You need | From | Used here for |
|---|---|---|
| Counting cost: loops, best and worst case, space | [00-before-you-start.md](00-before-you-start.md#big-o-from-zero), §Big-O from zero | §0.4 and §0.7 |
| Reading the constraints: what n up to 10⁵ rules out | [00-before-you-start.md](00-before-you-start.md#big-o-from-zero), §Big-O from zero | deciding that the double loop is too slow |
| Recursion, and the call stack as space | [00-before-you-start.md](00-before-you-start.md#recursion-and-the-call-stack), §Recursion and the call stack | merge sort in §Sorting as a tool, and the call stack in §0.7 |
| `list`, `dict`, `set`, `for`, `enumerate` without an IDE | [00-before-you-start.md](00-before-you-start.md#the-python-interview-subset), §The Python interview subset | every code block here |
| The five steps and the four-part submission | [00-before-you-start.md](00-before-you-start.md#how-to-work-a-problem), §How to work a problem | the drill set |

**The one question this module answers:**

> *The obvious solution examines every pair of elements, the double loop, O(n²). How do I get the same answer without doing that?*

Every technique in this module is an answer to that question. This is not "learn arrays"; it is **learn the ways out of a nested loop.**

### The three escapes: Remember, Order, Reuse

There are only three. Everything below is one of them, or a combination.

| | Escape | The move | What it costs | Techniques |
|---|---|---|---|---|
| **1** | **Remember** | Store what you've already seen. Ask the store instead of rescanning. | O(n) **space** | hash set, hash map, frequency counting, prefix-sum maps |
| **2** | **Order** | Sort first. Now one comparison rules out a whole region instead of one element. | O(n log n) **upfront** | sort then scan, two pointers, binary search |
| **3** | **Reuse** | Compute position *i*'s answer from position *i−1*'s, in O(1). | nothing | running min or max, prefix sums, the sliding window |

**How to use this table on a problem.** State the brute force, say *"that's quadratic"*, and then walk the three in order:

1. *"Is there something I could remember that would make the inner loop unnecessary?"*
2. *"Would sorting help?"*
3. *"Does the answer at i overlap with the answer at i−1?"*

That is the optimisation pass. It is three questions, it fits in twenty seconds, and most interviewers listen for it.

> **The trade is always the same shape: you buy time with space, or with a one-off sort, or with a cleverer loop.** Say which one you're buying, out loud.

**Remember and Reuse are easy to confuse**, because both "keep something from the past." The discriminator, because it sets your space complexity:

> **Does your storage grow with n?** A hash structure grows: **Remember**, O(n) space. A handful of scalars is fixed: **Reuse**, O(1) space.

Try Reuse first; it is strictly cheaper when it works. Remember is the escape this module teaches in full. Order gets its cost and its Python tools here, in §Sorting as a tool. The pointer and window forms of Order and Reuse come later, in module 03.

## 0.2 The structure and how it works

### The list: a row of numbered slots

A Python `list` is one contiguous block of memory holding references to its elements, in order. To read `nums[i]`, Python computes the slot's address from the start of the block and `i`: one arithmetic step, whatever the length. That is why indexing is O(1).

Everything else follows from "one contiguous block":

- **Appending is O(1) amortised.** The block is allocated with spare room at the end. When it fills, Python allocates a bigger block, larger by a constant factor, and copies everything across. That copy is O(n), but it happens rarely enough that the total over n appends is O(n), so O(1) each on average.
- **Inserting or deleting anywhere but the end is O(n).** `nums.insert(0, x)` and `nums.pop(0)` shift every later element one slot. The front of a list is the expensive end.
- **Searching is O(n).** `x in nums` and `nums.index(x)` have no way to know where `x` is, so they look at every slot until they find it.

The last point is the one that makes the double loop: "is the partner somewhere in this list?" is a scan. The hash table replaces that scan with a computation.

### The hash table: compute where it must be

`set` and `dict` are both hash tables. A `set` stores keys only; a `dict` stores keys and a value for each.

**What it is.** An array where the index is *computed from the value*. To store `k`, Python computes `hash(k) % capacity`, and that number is the slot. To look `k` up, it recomputes the same number and goes straight there.

> **That's the whole trick: you don't search for the element, you compute where it must be.** No scanning, so no loop, so O(1).

Three consequences worth knowing cold.

**a) Keys must be hashable, which in practice means immutable.** A mutable key could change after insertion, which would change its hash, and it would sit in the wrong slot, unfindable. So Python forbids it:

```python
d = {}
point = [3, 4]
d[point] = "a"            # ✗ TypeError: unhashable type: 'list'
d[tuple(point)] = "a"     # ✓ the same contents, as a tuple
```

**When your natural key is mutable, convert it; don't invent a hash.** `list` becomes `tuple(lst)`, `set` becomes `frozenset(s)`, and the full table is in [python-toolkit.md](../reference/python-toolkit.md#dict-keys-must-be-immutable-convert-dont-invent), §Dict keys must be immutable: convert, don't invent. You are not bypassing Python's rule, you are **satisfying** it: converting makes "this never changes" structural instead of a promise. Writing your own hash function is never the answer.

**`tuple` or `frozenset`?** Decide what "the same" means first. `tuple(lst)` keeps order and repeats: `(1, 2)` and `(2, 1)` are different keys. `frozenset(s)` ignores both: `frozenset([1, 2, 2])` equals `frozenset([2, 1])`. Each costs O(k) to build for k elements. Pick the conversion whose notion of equality matches the problem's.

**b) O(1) is *average*, not guaranteed.** Two keys can hash to the same slot, a **collision**. In a pathological case everything collides and a lookup degrades to O(n). "O(1) average" is the precise phrase, and it costs you one word.

**c) `set` or `dict`? Ask what you need to recover.**

| You need to know… | Use |
|---|---|
| *whether* you've seen it | `set` |
| *where* you saw it (an index), *how many times*, or *what it mapped to* | `dict` |

### Key design: the hard part of hashing

Membership questions are easy. The hard hashing problems all ask one question: **what do I use as the key?** The answer is always **the thing that is identical across everything you want to treat as the same**: the invariant of the group. Get the key right and the problem becomes a few lines.

[Isomorphic Strings](https://leetcode.com/problems/isomorphic-strings/) (LC 205), not in the drill set, asks whether the letters of one string can be renamed to give the other: `"egg"` and `"add"` can, `"foo"` and `"bar"` can't. The letters themselves differ, so they can't be the key. What two isomorphic strings share is their **shape**: which positions repeat a letter seen before. Number each letter by the order of its first appearance:

```python
def shape(s):
    first = {}                                        # letter → its number, in order of first appearance
    return tuple(first.setdefault(ch, len(first)) for ch in s)

shape("egg")    # (0, 1, 1)
shape("add")    # (0, 1, 1)   same shape: isomorphic
shape("bar")    # (0, 1, 2)   differs from shape("foo")
```

`setdefault(ch, len(first))` reads `len(first)` before inserting, so the first new letter gets 0, the next 1, and so on. The result is a `tuple`, so it can itself be a key: to put many words into groups of the same shape, use `shape(word)` as a `dict` key. **Two strings are the same kind of thing exactly when their keys are equal.** That sentence, with the right key, is every grouping problem.

## 0.3 Vocabulary

| Term | Meaning |
|---|---|
| **subarray** | a run of *adjacent* elements, `nums[i..j]`. A substring is the same thing in a string |
| **subsequence** | elements in their original order, gaps allowed. Not contiguous; not this module's sliding tools |
| **contiguous** | adjacent, with no gaps. The word that separates a subarray from a subsequence |
| **in place** | modifying the input instead of building a new structure; usually O(1) extra space |
| **hashable** | usable as a `dict` key or `set` member: has a fixed hash, in practice immutable |
| **collision** | two different keys landing in the same hash-table slot |
| **frequency map** | a `dict`, or a `Counter`, from value to the number of times it appears |
| **key design** | choosing what to hash so that "the same kind of thing" means "the same key" |
| **running state** | one or two variables carried through a single pass, standing in for the whole past |
| **prefix sum** | `prefix[i]`, the sum of everything before index `i` |
| **amortised** | averaged over a sequence of operations: one is occasionally expensive, the total is still cheap |
| **auxiliary space** | memory you allocate beyond the input and the required output |
| **stable sort** | a sort that keeps equal elements in their original relative order |

## 0.4 Operations and their cost

**n** is the length of the list or the number of entries in the table; **k** is the length of a slice, a key or a second list.

| Operation | Python | Big-O | Trap |
|---|---|---|---|
| Read or write by index | `nums[i]`, `nums[i] = x` | O(1) | `nums[-1]` is the last element, not an error: [bug-checklist.md](../reference/bug-checklist.md#a-negative-index-wraps-instead-of-crashing), §A negative index wraps instead of crashing |
| Length | `len(nums)` | O(1) | none: it is stored, not counted |
| Append, pop from the end | `nums.append(x)`, `nums.pop()` | O(1) amortised | none |
| Insert or pop at the front | `nums.insert(0, x)`, `nums.pop(0)` | **O(n)** | inside a loop it is O(n²); use a `deque` ([python-toolkit.md](../reference/python-toolkit.md#1-deque-the-queue), §1. `deque`: the queue) |
| Search a list | `x in nums`, `nums.index(x)`, `nums.count(x)` | **O(n)** | reads as one step; inside a loop it is the double loop again. Build a `set` or a `dict` once |
| Slice | `nums[i:j]`, `nums[:]` | **O(j − i)**: a copy | slicing at every step of a loop is O(n²) in total. Pass indices instead |
| Concatenate | `a + b`, `s + t` | O(len a + len b) | `s += ch` in a loop can be O(n²); collect parts and `''.join` them once |
| Min, max, sum of a list | `min(nums)`, `sum(nums)` | O(n) | recomputing it inside a loop. Carry it as running state (§0.5, primitive 2) |
| Sort | `sorted(nums)`, `nums.sort()` | O(n log n) | `.sort()` returns `None`: `nums = nums.sort()` throws the list away |
| Build a set or dict from n items | `set(nums)`, `Counter(nums)` | O(n) | `set((0, 1))` is `{0, 1}`, not `{(0, 1)}`: [python-toolkit.md](../reference/python-toolkit.md#5-sorted-and-set-builtins-no-import), §5. `sorted` and `set`: builtins, no import |
| Membership, insert, delete in a set or dict | `x in s`, `s.add(x)`, `d[k] = v`, `del d[k]` | **O(1) average**, O(n) worst | `x in d.values()` is a list scan, O(n) |
| Hash a key of length k | a `tuple` or `str` key | O(k) | the key is not free: `tuple(point)` for a point of k coordinates is O(k) to build and O(k) to hash, every time |
| Iterate a dict | `for k, v in d.items()` | O(n) | adding or deleting keys while iterating raises `RuntimeError` |

**The row people get wrong is search.** `x in nums` looks like one operation. On a list it is a loop, and putting it inside another loop over n elements is O(n²). The same check on a `set` built once beforehand is O(1). Most of this module is that substitution.

## 0.5 The primitives

Four moves build almost every solution in this module. Each has an invariant: a statement that is true at the top of every iteration of the loop. You choose it before writing the body, and every line of the body has one job, which is to leave it still true.

**1. Record the past, then query it (Remember).** Instead of asking *"does a partner exist somewhere ahead of me?"*, which forces a forward scan, walk once and ask *"has my partner already gone by?"* [Contains Duplicate II](https://leetcode.com/problems/contains-duplicate-ii/) (LC 219), not in the drill set, asks whether two equal values sit at most k apart:

```python
def containsNearbyDuplicate(nums, k):
    last_seen = {}                          # value → most recent index
    for i, n in enumerate(nums):
        if n in last_seen and i - last_seen[n] <= k:    # query first...
            return True
        last_seen[n] = i                    # ...then record yourself
    return False
```

*Invariant:* at the top of iteration `i`, `last_seen` holds every value in `nums[0..i-1]`, each mapped to its most recent index. O(n) time, O(n) space: one pass, because the past is in a dict instead of behind a second loop.

**The order of the two lines is part of the invariant.** Query *before* recording. Record first and every element finds itself: `i - last_seen[n]` is `i - i = 0`, which is always `<= k`, so `[1, 2, 3]` with `k = 1` returns `True`. An element must never be its own partner.

> This inversion, *"look backwards into a store"* instead of *"look forwards with a loop"*, is the single most reusable idea in the module.

**2. Carry the running state (Reuse).** One or two variables summarise the whole past, and each step updates them in O(1):

```python
best = nums[0]                  # never 0: the answer must come from the input
for n in nums[1:]:
    best = max(best, n)         # or min, or a sum, or a pair of values
```

*Invariant:* at the top of the iteration that reads `nums[i]`, `best` is the answer for `nums[0..i-1]`. The question that produces every algorithm of this shape is in §Running state.

**3. The prefix sum (Reuse).** Many "sum of `nums[i..j]`" questions cost O(n) each if you add up the range every time. Precompute the sum of everything before each index, and any range sum is one subtraction:

```python
prefix = [0]
for n in nums:
    prefix.append(prefix[-1] + n)      # prefix[i] = sum(nums[:i])

# sum of nums[i..j] inclusive:
prefix[j + 1] - prefix[i]
```

*Invariant:* `prefix[i]` is the sum of the first `i` elements, so `prefix` has one more entry than `nums` and `prefix[0]` is `0`, the empty prefix. O(n) to build, **O(1) per query** afterwards.

> **A prefix array turns "recompute a range" into "subtract two accumulated values."** It works for any operation you can undo: sum (subtract), XOR (XOR again), product (divide, but only if no element is zero). Not for max or min, which have no inverse: knowing the max of `nums[:j+1]` and of `nums[:i]` tells you nothing about the max of `nums[i..j]`.

**4. Sort first (Order).** After a sort, equal values are neighbours and everything to the left of a position is no larger than it. One comparison with your neighbour then answers questions that needed a set or a scan before.

*Invariant:* after `nums.sort()`, `nums[i - 1] <= nums[i]` for every `i`. The cost and the tools are in §Sorting as a tool.

## 0.6 Inputs that break it

| Input | What breaks | Check |
|---|---|---|
| The empty list, `nums = []` | `nums[0]` raises `IndexError`; `nums[1:]` silently does nothing; `max([])` raises `ValueError` | read the constraints: is `len(nums) >= 1` promised? If not, handle `[]` first |
| A single element | code that assumes a pair exists | trace it: does the loop run zero times and still return the right answer? |
| Every element the same | a set shrinks to one member; a key that ignores multiplicity merges things that differ | is `[2, 2]` the same as `[2]` for this problem? Then `set`; if not, a `Counter`, or a key that keeps every element |
| An element that could pair with itself | recording before querying lets one element act as both halves of a pair | §0.5, primitive 1: query first |
| All values negative | a running best that starts at `0` returns `0`, which is no element's sum | start from `nums[0]`, or `float('-inf')` |
| A zero in a product | the prefix-product inverse divides by zero | division is not a safe inverse once zero is allowed; read the constraints |
| A key that is a list | `TypeError: unhashable type: 'list'` | convert it: `tuple(...)` |
| An answer that is an index, after you sorted | the sort moved every element, so positions no longer match the input | keep the original index with each value before sorting: `sorted(enumerate(nums), key=...)` |
| n up to 10⁵ | the double loop is about 10¹⁰ steps and times out | O(n²) is out; aim for O(n) or O(n log n) |

## 0.7 Complexity, out loud

| Notation | Say | Typical cause |
|---|---|---|
| O(1) | "constant time" | a fixed number of operations, a hash lookup |
| O(log n) | "logarithmic" | halving the search space at each step |
| O(n) | "linear" | one pass |
| O(n log n) | "n log n" | **sorting** |
| O(n²) | "quadratic" | a nested loop over the same array |
| O(n³) | "cubic" | a triple nested loop |

**The sentence to have automatic**, delivered unprompted the moment you finish writing:

> *"This is linear time and linear space. The space is the hash set; if I needed constant space I'd sort first, which trades it for n log n time."*

That one sentence states the complexity, names the trade-off, and volunteers an alternative.

### Space: total vs auxiliary

| | Counts | Example: return the n running sums of `nums` in a new list, using one running total |
|---|---|---|
| **Total space** | everything allocated, **including** the output | O(n) |
| **Auxiliary space** | everything *except* the input and the required output | **O(1)** |

**Most interviewers mean auxiliary**, and the reason is worth having rather than memorising:

> Space complexity exists to **compare algorithms**. The output's size is dictated by the *problem*, not by your choices: every correct solution allocates the same output. Counting it discriminates between nothing. Auxiliary space measures what **your decisions** cost.

| Counts as auxiliary ✓ | Doesn't ✗ |
|---|---|
| a `seen` set or a `Counter` you built | the input array |
| a temporary array for a merge | the array you must return |
| **the recursion call stack**: one frame per level that is alive at once | |
| the extra space a sort uses | |

The call stack is the one people forget: a recursion that goes d levels deep holds d frames at once, so it is O(d) space even with no explicit container ([00-before-you-start.md](00-before-you-start.md#recursion-and-the-call-stack), §Recursion and the call stack).

**The phrase:** *"O(1) extra space, not counting the output array."* Say the caveat; without it, "O(n)" is what gets heard. Some statements spell the convention out themselves, with *"the output array does not count as extra space"*, so read the statement for it.

**Two facts specific to this module:**

- **Sorting costs O(n log n), and that is effectively free** when you're escaping O(n²) or O(n³). Never reject a sort on cost grounds. For n = 10⁵, n log n is about 1.7 million steps; n² is 10 billion.
- **Say space honestly.** A hash set over n elements is O(n) space. Python's sort can itself use up to O(n) extra space, so "sort, then O(1) extra" is O(n) auxiliary in the strict sense. Saying so is better than being corrected.

## 0.8 Signals

| In the statement | Escape | Reach for | Where |
|---|---|---|---|
| "are there duplicates", "has this been seen" | Remember | `set` | §0.5, primitive 1 |
| "how many times does X appear", "most frequent" | Remember | `Counter` or `dict` | §Hashing in practice |
| "group these by some shared property" | Remember | `defaultdict(list)` plus **key design** | §0.2, §Key design |
| "find a pair with some property", unsorted, the answer is indices | Remember | `dict` from value to index | §0.5, primitive 1 |
| "maximum, minimum or best so far" | Reuse | one pass, one tracker variable | §Running state |
| "sum of a range", many queries | Reuse | **prefix array** | §0.5, primitive 3 |
| "how many subarrays sum to k" | Remember and Reuse | prefix sums plus a hash map | §Prefix sums with a hash map |
| "except itself", "all the others" | Reuse | a prefix **and** a suffix pass | §0.5, primitive 3 |
| "overlapping", "intervals", "closest pair of values", "sort" anywhere in the statement | Order | sort first, then one scan | §Sorting as a tool |
| "sorted array", "pair or triplet summing to X", "contiguous subarray", "substring" | Order or Reuse | pointers and windows | you'll see these later, in module 03 |

## 0.9 Self-check

Answer each in a sentence or two, without looking back. The answers are at the bottom of the module. Read the part behind any question you miss.

1. A loop runs `while queue: x = queue.pop(0)` over a list of n items. What does it cost in total, and what do you use instead?
2. Two solutions both "keep something from the past": one keeps a `dict`, the other keeps two integers. Which escape is each, and what single question tells them apart?
3. What happens on `d[[1, 2]] = "x"`, why does Python forbid it, and what do you write instead?
4. In the record-the-past loop, why must you query the store before recording the current element? Give a small input where the reversed order returns the wrong answer for "are two equal values at most k apart?".
5. With `prefix[i] = sum(nums[:i])`, write the sum of `nums[i..j]` inclusive. Why can't the same trick answer "the maximum of `nums[i..j]`"?
6. A solution returns a new list of n values and otherwise uses two integer variables. What is its total space, what is its auxiliary space, and which one do most interviewers mean?
7. Why is a hash lookup "O(1) average" and not just O(1)? What is the worst case?
8. A running maximum is initialised to `0`. On which input is it wrong, and what should it start at?

---

## Hashing in practice

Two tools from `collections` cover almost every hashing problem, and both are `dict` subclasses, so everything a `dict` does, they do.

```python
from collections import Counter, defaultdict

counts = Counter("mississippi")      # {'i': 4, 's': 4, 'p': 2, 'm': 1}
counts["z"]                          # 0: a missing key reads as 0, no KeyError
counts.most_common(2)                # [('i', 4), ('s', 4)]

groups = defaultdict(list)           # a missing key starts as []
groups["key"].append("x")            # no "is the key there yet?" check
```

- **`Counter`** is a frequency map built in one O(n) call. Use it when the question is *how many*.
- **`defaultdict(list)`** is the grouping tool: `groups[key(x)].append(x)` for every `x`, and the key from §0.2, §Key design, decides what ends up together. `defaultdict(int)` counts one item at a time, when you need the counts *during* the pass rather than after it.

Which to use, with the two rules that decide it: [python-toolkit.md](../reference/python-toolkit.md#2-defaultdict-the-dict-that-fills-itself-in), §2. `defaultdict`: the dict that fills itself in, and [python-toolkit.md](../reference/python-toolkit.md#3-counter-frequency-counting-in-one-line), §3. `Counter`: frequency counting in one line.

**The plain-`dict` version still matters.** `d[k] = d.get(k, 0) + 1` is the same count with no import, and it is what you write if you blank on the names. Say the name you think it is and move on; never hand-build a frequency array to avoid an import.

---

## Running state

**Signal:** "maximum, minimum or best so far."

**Worked on [Maximum Subarray](https://leetcode.com/problems/maximum-subarray/) (LC 53)**, which is not in the drill set: the largest sum of any contiguous subarray. This is Kadane's algorithm.

```python
def maxSubArray(nums):
    best = current = nums[0]
    for n in nums[1:]:
        current = max(n, current + n)     # extend the run, or start fresh here
        best = max(best, current)
    return best
```

**Linear time, constant space.**

*Invariant:* after processing `nums[i]`, `current` is the best sum of a subarray that **ends exactly at `i`**, and `best` is the best sum of any subarray in `nums[0..i]`. A subarray ending at `i` either is `nums[i]` alone or extends one ending at `i − 1`, so `current` needs nothing else from the past.

The question that produces every algorithm of this shape:

> **"What is the minimum I must remember from the past in order to decide the present?"**

Almost always one or two numbers, never the whole history. Here it is *"the best subarray ending exactly at the previous position."* Carrying that one number replaces the inner loop.

**Starting values.** `best = current = nums[0]` handles an all-negative input: on `[-3, -1, -2]` the answer is `-1`. Starting at `0` would return `0`, a sum no subarray has (§0.6).

> ⚠️ **You'll see this again in module 06, on trees.** A value passed down from the root, such as the running total along a path, is the same running state carried along a path instead of along an array.

---

## Prefix sums with a hash map

Prefix sums combine with a hash map to handle a whole class of subarray problems. **Worked on [Subarray Sum Equals K](https://leetcode.com/problems/subarray-sum-equals-k/) (LC 560)**, which is not in the drill set: count the subarrays whose sum is exactly k.

A subarray `nums[i..j]` sums to k exactly when `prefix[j + 1] - prefix[i] == k`, that is, when an earlier prefix equals `running - k`. So walk once, keep the running total, and ask the store *"how many earlier prefixes equal `running - k`?"*. That is primitive 1, record the past, applied to sums instead of values:

```python
from collections import Counter

def subarraySum(nums, k):
    count = 0
    running = 0
    seen = Counter({0: 1})          # the empty prefix: sum 0, seen once
    for n in nums:
        running += n
        count += seen[running - k]  # query first: earlier prefixes that leave exactly k
        seen[running] += 1          # then record this one
    return count
```

*Invariant:* at the top of each iteration, `seen` counts every prefix sum that ends *before* the current element, including the empty one. O(n) time, O(n) space.

**Two details carry the whole solution.**

- **`Counter({0: 1})`.** Without the empty prefix, a subarray that starts at index 0 has no earlier prefix to subtract, and it is never counted. On `nums = [3]`, `k = 3` the answer would be `0`.
- **Query, then record.** The same order as primitive 1. Record first and, when `k = 0`, every position matches its own prefix and counts an empty subarray.

**Why not a sliding window?** Values can be negative, so extending a run can make its sum smaller and shrinking it can make it larger. The window's rule needs sums that only grow as the run grows. Prefix sums plus a hash map need no such promise, which is exactly when to reach for them. You'll see the window, and the property it needs, later in module 03.

---

## Sorting as a tool

### The budget: O(n log n) is free against O(n²)

A sort costs O(n log n). If the alternative is the double loop, the sort is effectively free: for n = 10⁵, about 1.7 million steps against 10 billion. And it changes what one comparison can tell you, because the array now has an order: equal values are neighbours, and anything to the left of a position is no larger than it.

**So "what if it were sorted?" is one of the highest-yield questions on any array problem.** Ask it as the second of the three questions in §0.1. The two exceptions to keep in mind: the answer is about **original positions** (sorting moves them, so carry the index along, §0.6), or the problem already promises O(n) is possible and expects it.

### Why comparison sorting costs n log n: merge sort

Merge sort is the sort that makes the cost visible. It is **divide and conquer** in three steps:

| Step | What merge sort does |
|---|---|
| **Divide** | split the array into its two halves, at the middle |
| **Conquer** | sort each half, recursively |
| **Combine** | merge the two sorted halves into one sorted array |

**The merge.** Two sorted halves, one read position in each. Compare the two elements under the positions, write out the smaller, and advance that position. When one half runs out, the rest of the other is already sorted and goes out as it is. Each step writes one element, so merging two halves of total size k costs **O(k)**.

*Invariant of the merge:* everything written so far is sorted, and is no larger than either element under the two read positions. Taking the smaller of the two keeps it true. When there is a tie, taking from the left half first is what makes merge sort **stable**: equal elements leave in the order they arrived.

**Adding it up.** The cost of any recursion is **the sum, over every call, of the work that call does on its own**, everything except its recursive calls. Draw the calls as a tree, with each call's range size in its node:

```
                [ n ]                    level 0: one range of n       → n work
             /         \
        [n/2]           [n/2]            level 1: two ranges of n/2    → n work
        /    \          /    \
    [n/4]  [n/4]    [n/4]  [n/4]         level 2: four ranges of n/4   → n work
      …      …        …      …
    [1] [1] [1]  …  [1] [1] [1]          last level: n ranges of 1
```

- **Each level's ranges add up to n**, because the halves of a range partition it. So each level does O(n) merge work in total.
- **There are about log₂ n levels**, because halving n reaches 1 after log₂ n steps.
- **Total: n per level times log n levels, O(n log n).**

**Why the split must be the middle.** The O(k) merge is only fine *because* the depth is log n. If each call split off just one element, the tree would be a chain of n levels with sizes n, n − 1, …, 1, and the same O(k) work per call would add up to about n²/2. **Merge sort chooses the middle, so the tree is always balanced and O(n log n) is guaranteed, on every input.** Quicksort splits around a pivot, so the data decides the shape; choosing the pivot at random makes O(n log n) the *expected* cost, with n² still possible on an unlucky run. The space is separate: merge sort's merge needs an O(n) buffer, and the recursion is log n deep.

**And no comparison sort can do better.** There are n! possible orders of n distinct values, each comparison has two outcomes, and the sort must distinguish all of them, so it needs at least log₂(n!) comparisons in the worst case, which is about n log₂ n. O(n log n) is the floor for sorting by comparisons. Beating it needs extra knowledge about the values, such as a small range of integers that can be counted instead of compared.

**You won't write merge sort to solve a problem; you'll call `sort()`.** Python's built-in sort, Timsort, is a merge-based sort: O(n log n) worst case, faster on input that is already partly sorted, and stable. Knowing the argument above is what lets you say *why* the sort costs what it does.

> ⚠️ **You'll see the merge step again in module 05, on linked lists**, where two sorted lists are merged by relinking nodes instead of copying values.

### The Python tools

The calls themselves are in [python-toolkit.md](../reference/python-toolkit.md#5-sorted-and-set-builtins-no-import), §5. `sorted` and `set`: builtins, no import, how strings, lists and tuples compare is in §Comparing and sorting sequences: Python already does it, and sorting two parallel arrays together is in §`zip`: sorting two parallel arrays together. What those sections don't spell out:

| Decision | Use | Why |
|---|---|---|
| Keep the input unchanged, or sort something that is not a list | `sorted(x)` | returns a new list, O(n) extra; works on any iterable, including a set or a dict's keys |
| Sort a list you own, in place | `x.sort()` | returns **`None`**: `x = x.sort()` throws your list away |
| Sort by something computed from each element | `key=lambda iv: iv[0]` | the key function runs **once per element**, not once per comparison |
| Sort by two fields | `key=lambda r: (r[1], r[0])` | tuples compare field by field, so the second field breaks ties in the first |
| One field descending, another ascending | `key=lambda r: (-r[1], r[0])` | negate the numeric field; `reverse=True` would reverse both |
| Descending on a field you can't negate, such as a string | two stable sorts: by the tie-breaker first, then by the main field | stability keeps the first sort's order among the second sort's ties |
| Largest first, all fields | `reverse=True` | still stable: equal elements keep their input order |

**Stability is what makes the two-pass trick work.** Python's sort is guaranteed stable, so after `rows.sort(key=name)` then `rows.sort(key=score, reverse=True)`, rows with equal scores are still in name order.

### Sort, then one scan

**Worked on [Merge Intervals](https://leetcode.com/problems/merge-intervals/) (LC 56)**, which is not in the drill set: merge every overlapping pair of intervals. Unsorted, any interval might overlap any other, which is the double loop. **Sorted by start, an interval can only overlap the one merged just before it**, because everything after it starts later.

```python
def merge(intervals):
    intervals.sort(key=lambda iv: iv[0])          # by start: overlaps become neighbours
    merged = []
    for start, end in intervals:
        if merged and start <= merged[-1][1]:     # overlaps the last merged interval
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return merged
```

*Invariant:* `merged` holds disjoint intervals, in order of start, covering exactly the intervals read so far, and only its last interval can overlap anything still to come.

- **Why `max`.** `[1, 10]` followed by `[2, 3]`: the second is inside the first, and the merged end must stay 10. Writing `merged[-1][1] = end` shrinks it to 3.
- **Why `merged and`.** The first interval has nothing to overlap; the guard makes it an ordinary append instead of a special case before the loop.
- **Cost.** O(n log n) for the sort plus O(n) for the scan: **O(n log n) time.** The output is O(n); the sort's own extra space is up to O(n).

**The shape generalises:** sort by the field that makes "only the neighbour matters" true, then one pass that compares each element with the last thing kept.

> ⚠️ **You'll see sorting again in three later modules.** In module 03, a sorted array lets two pointers walk in from both ends. In module 07, sorting the candidates first puts duplicates next to each other, so skipping them is a comparison with the neighbour. In module 10 ([10-heaps.md, §The O(n) answer: bucket sort by count](10-heaps.md#the-on-answer-bucket-sort-by-count)), bucket sort and quickselect show when you can avoid the full O(n log n).

---

## Common array and hashing mistakes

Ordered by how often each happens.

| Mistake | What you see | Entry |
|---|---|---|
| `x in some_list` inside a loop | correct output, O(n²) time | §0.4, the search row |
| Recording before querying | an element pairs with itself | §0.5, primitive 1 |
| Using a list as a key | `TypeError: unhashable type: 'list'` | [python-toolkit.md](../reference/python-toolkit.md#dict-keys-must-be-immutable-convert-dont-invent), §Dict keys must be immutable: convert, don't invent |
| Confusing the index with the value | an index returned where a value was expected, or the reverse | [bug-checklist.md](../reference/bug-checklist.md#index-vs-value), §Index vs value |
| `for n, i in enumerate(nums)` | the index and the value swapped | [bug-checklist.md](../reference/bug-checklist.md#unpacking-enumerate-in-the-wrong-order), §Unpacking `enumerate` in the wrong order |
| Off-by-one in a prefix array: `prefix[j] - prefix[i]` | each range sum misses its last element | [bug-checklist.md](../reference/bug-checklist.md#off-by-ones-derive-never-freehand), §Off-by-ones: derive, never freehand |
| A running best that starts at `0` | wrong answer on all-negative input | §0.6 |
| `nums = nums.sort()` | `nums` is `None` | §Sorting as a tool, §The Python tools |
| Slicing at every step of a loop | correct output, O(n²) time | [bug-checklist.md](../reference/bug-checklist.md#the-copy-reflex--where-only-a-read-was-needed), §The copy reflex: `[:]` where only a read was needed |
| Building every subarray or pair to test it | O(n²) memory before any work | [bug-checklist.md](../reference/bug-checklist.md#materialising-every-candidate), §Materialising every candidate |
| Adding to a dict while iterating over it | `RuntimeError: dictionary changed size during iteration` | [bug-checklist.md](../reference/bug-checklist.md#mutating-a-list-while-iterating-over-it), §Mutating a list while iterating over it |
| Sorting when the answer is original indices | the indices of the sorted array, not the input | §0.6 |

---

## Drill set — cold, no IDE, no running

**Solutions are not in this file.** Every shape you need is in §0 and the sections above, taught on other problems.

| # | Problem | Focus |
|---|---|---|
| 1 | [Contains Duplicate](https://leetcode.com/problems/contains-duplicate/) (LC 217) | Remember: a hash set. State the brute force first and call it quadratic |
| 2 | [Two Sum](https://leetcode.com/problems/two-sum/) (LC 1) | Remember: a `dict` from value to index. The order of query and record matters. ⚑ **Checkpoint** |
| 3 | [Valid Anagram](https://leetcode.com/problems/valid-anagram/) (LC 242) | Remember: `Counter`. Then say the O(1)-space alternative and what it costs |
| 4 | [Group Anagrams](https://leetcode.com/problems/group-anagrams/) (LC 49) | Remember: `defaultdict` plus **key design**. ⚑ **Checkpoint** |
| 5 | [Best Time to Buy and Sell Stock](https://leetcode.com/problems/best-time-to-buy-and-sell-stock/) (LC 121) | Reuse: a running minimum. Say what one number you carry from the past |
| 6 | [Product of Array Except Self](https://leetcode.com/problems/product-of-array-except-self/) (LC 238) | Reuse: a prefix **and** a suffix pass. Say the auxiliary space, with the output caveat |

**The order.** Rows 1 to 4 are Remember, from plain membership to the key you have to design. Rows 5 and 6 are Reuse, from one running value to two passes.

**⚑ Checkpoint at row 2.** Record the past, then query it, is the idea every other Remember problem builds on. If it doesn't come out clean, stop there and reread §0.5, primitive 1, rather than pushing on.

**⚑ Checkpoint at row 4.** The key is the whole problem. If you can't say in one sentence why two words get the same key, stop and reread §0.2, §Key design.

**Spares, if a shape needs a second rep:** [LC 383 Ransom Note](https://leetcode.com/problems/ransom-note/) (counting, like row 3) · [LC 448 Find All Numbers Disappeared in an Array](https://leetcode.com/problems/find-all-numbers-disappeared-in-an-array/) (a set, then the O(1)-space follow-up) · [LC 303 Range Sum Query - Immutable](https://leetcode.com/problems/range-sum-query-immutable/) (§0.5, primitive 3, undisguised) · [LC 1365 How Many Numbers Are Smaller Than the Current Number](https://leetcode.com/problems/how-many-numbers-are-smaller-than-the-current-number/) (sort, then a dict) · [LC 128 Longest Consecutive Sequence](https://leetcode.com/problems/longest-consecutive-sequence/) (a set, and why sorting is the slower answer here).

*Solved in the sections above, so from memory only:* [LC 219](https://leetcode.com/problems/contains-duplicate-ii/) · [LC 205](https://leetcode.com/problems/isomorphic-strings/) · [LC 53](https://leetcode.com/problems/maximum-subarray/) · [LC 560](https://leetcode.com/problems/subarray-sum-equals-k/) · [LC 56](https://leetcode.com/problems/merge-intervals/).

## Before you submit anything

Every problem, no exceptions:

1. **Name the escape and the signal that pointed to it**, before writing code.
2. **State the brute force and call it quadratic.** Then walk the three escapes out loud.
3. Write it.
4. Run [bug-checklist.md](../reference/bug-checklist.md#the-30-second-pass), §The 30-second pass, over your code.
5. **Trace it.** Three elements, then `[]`, then one element. Check the invariant survives one iteration.
6. **Say the complexity in words**, time *and* space, and say whether the space counts the output.

---

## Self-check answers

1. **O(n²)** in total. `pop(0)` removes from the front of a list, which shifts every remaining element one slot left, so each call is O(n). Use a **`deque`** and `popleft()`, which is O(1), or keep a read index into the list and never remove anything.
2. The `dict` is **Remember** and the two integers are **Reuse**. The question is **"does your storage grow with n?"**: a hash structure grows, O(n) space; a fixed handful of scalars doesn't, O(1) space.
3. It raises **`TypeError: unhashable type: 'list'`**. A list can change after insertion, which would change its hash and leave it in the wrong slot, unfindable. Convert it to an immutable equivalent and use that: `d[(1, 2)] = "x"`, or `d[tuple(lst)]` for a list you already have.
4. Recording first puts the current element in the store before you ask, so it finds **itself**: in the nearby-duplicate check, `i - last_seen[n]` becomes `i - i = 0`, which is always `<= k`. On `[1, 2, 3]` with `k = 1`, there are no duplicates, yet the reversed order returns `True` on the first element.
5. **`prefix[j + 1] - prefix[i]`**. Subtraction undoes addition, so the earlier prefix can be removed. Max has no inverse: knowing the max of a longer prefix and of a shorter one tells you nothing about the max of the part between them.
6. **Total space is O(n)**, because the returned list counts. **Auxiliary space is O(1)**: two integers, and the output is excluded. Most interviewers mean **auxiliary**, because every correct solution must allocate the same output, so only the auxiliary part compares solutions. Say *"O(1) extra space, not counting the output."*
7. Different keys can hash to the same slot, a **collision**. On average there are few, so a lookup is O(1). In a pathological case every key collides and a lookup degrades to **O(n)**.
8. It is wrong when **every value is negative**: the answer is the largest negative value, but the variable stays at `0`, which is not in the input. Start it at **`nums[0]`**, or at `float('-inf')`.
