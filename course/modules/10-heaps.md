# Module 10: Heaps, top-K and selection

<!-- toc -->
**Contents**

- [0.1 Prerequisites and the one question](#01-prerequisites-and-the-one-question)
- [0.2 The structure and how it works](#02-the-structure-and-how-it-works)
  - [How a list becomes a heap](#how-a-list-becomes-a-heap)
  - [Four things that bite](#four-things-that-bite)
  - [Partial order is the entire trade](#partial-order-is-the-entire-trade)
  - [The three structures, side by side](#the-three-structures-side-by-side)
  - [The array layout](#the-array-layout)
  - [Sift up and sift down](#sift-up-and-sift-down)
  - [Why heapify is O(n), not O(n log n)](#why-heapify-is-on-not-on-log-n)
  - [The mirror image](#the-mirror-image)
- [0.3 Vocabulary](#03-vocabulary)
- [0.4 Operations and their cost](#04-operations-and-their-cost)
- [0.5 The primitives](#05-the-primitives)
- [0.6 Inputs that break it](#06-inputs-that-break-it)
- [0.7 Complexity, out loud](#07-complexity-out-loud)
- [0.8 Signals](#08-signals)
- [0.9 Self-check](#09-self-check)
- [What you push: (priority, payload)](#what-you-push-priority-payload)
  - [There is no key=](#there-is-no-key)
  - [How tuple comparison works](#how-tuple-comparison-works)
  - [The three-line question to answer before you push anything](#the-three-line-question-to-answer-before-you-push-anything)
  - [The tie-breaking trap](#the-tie-breaking-trap)
  - [Why a missing tie-breaker is the worst shape of bug](#why-a-missing-tie-breaker-is-the-worst-shape-of-bug)
  - [The third fix: a wrapper class with `__lt__`](#the-third-fix-a-wrapper-class-with-__lt__)
  - [A tie-break that runs the wrong way](#a-tie-break-that-runs-the-wrong-way)
- [Max-heaps and negation](#max-heaps-and-negation)
  - [Three ways negation breaks](#three-ways-negation-breaks)
  - [Going from a min-heap to a max-heap once one exists](#going-from-a-min-heap-to-a-max-heap-once-one-exists)
  - [The decision that makes conversion unnecessary](#the-decision-that-makes-conversion-unnecessary)
- [The size-k heap: why a min-heap gives the k largest](#the-size-k-heap-why-a-min-heap-gives-the-k-largest)
  - [Push then pop, in that order](#push-then-pop-in-that-order)
  - [The rank sentence](#the-rank-sentence)
- [Choosing among the four answers](#choosing-among-the-four-answers)
  - [The log k does not come from stopping early](#the-log-k-does-not-come-from-stopping-early)
  - [Quicksort vs quickselect: the name carries the complexity](#quicksort-vs-quickselect-the-name-carries-the-complexity)
  - [The four answers, with the arithmetic](#the-four-answers-with-the-arithmetic)
  - [Choosing, in one pass](#choosing-in-one-pass)
  - [Why selection can be linear when sorting can't](#why-selection-can-be-linear-when-sorting-cant)
  - [The degenerate ends, which are also the test cases](#the-degenerate-ends-which-are-also-the-test-cases)
  - [The space sentence, in this topic's nouns](#the-space-sentence-in-this-topics-nouns)
- [Top-K with a tie-break that runs the wrong way](#top-k-with-a-tie-break-that-runs-the-wrong-way)
  - [Worked: Top K Frequent Words (LC 692)](#worked-top-k-frequent-words-lc-692)
- [The O(n) answer: bucket sort by count](#the-on-answer-bucket-sort-by-count)
  - [Worked: Sort Characters By Frequency (LC 451)](#worked-sort-characters-by-frequency-lc-451)
- [Quickselect](#quickselect)
  - [One signal, four answers](#one-signal-four-answers)
  - [One side only](#one-side-only)
  - [The allocating version](#the-allocating-version)
  - [The two classic bugs](#the-two-classic-bugs)
  - [Why the allocating version is not space-optimal](#why-the-allocating-version-is-not-space-optimal)
  - [In place, and where the O(1) comes from](#in-place-and-where-the-o1-comes-from)
  - [The ways it breaks](#the-ways-it-breaks)
  - [Duplicates: the three-way partition](#duplicates-the-three-way-partition)
  - [What to say in a room](#what-to-say-in-a-room)
- [k-way merge](#k-way-merge)
  - [The reasoning, from the one question](#the-reasoning-from-the-one-question)
  - [The state, and it is the whole algorithm](#the-state-and-it-is-the-whole-algorithm)
  - [Complexity](#complexity)
  - [The shapes one delta away](#the-shapes-one-delta-away)
- [Two heaps](#two-heaps)
  - [The balanced partition](#the-balanced-partition)
  - [The rebalance has no cases](#the-rebalance-has-no-cases)
  - [Worked: IPO (LC 502)](#worked-ipo-lc-502)
- [What a heap can't do](#what-a-heap-cant-do)
  - [When a heap is the wrong tool](#when-a-heap-is-the-wrong-tool)
  - [Lazy deletion](#lazy-deletion)
  - [A sliding window min or max](#a-sliding-window-min-or-max)
  - [Heapsort](#heapsort)
- [Every template, in one place](#every-template-in-one-place)
- [How to attack a heap problem](#how-to-attack-a-heap-problem)
- [Common heap mistakes](#common-heap-mistakes)
- [Drill set — cold, no IDE, no running](#drill-set--cold-no-ide-no-running)
- [Not covered here](#not-covered-here)
- [Before you submit anything](#before-you-submit-anything)
- [Self-check answers](#self-check-answers)
<!-- /toc -->

This module covers the heap. Module 02 sorted the structures by which item comes out ([02-stacks-queues.md](02-stacks-queues.md#which-item-comes-out-newest-oldest-smallest), §Which item comes out: newest, oldest, smallest), and taught two of them in full. The third row of that table is this module:

| Structure | Hands back | Cost of taking it out | Taught in |
|---|---|---|---|
| a stack, a `list` | the **newest** unfinished item | O(1), `pop()` | [02-stacks-queues.md](02-stacks-queues.md#a-list-used-as-a-stack), §A list used as a stack |
| a queue, a `deque` | the **oldest** item | O(1), `popleft()` | [02-stacks-queues.md](02-stacks-queues.md#the-queue-first-in-first-out), §The queue: first in, first out, and [§A deque used as a queue](02-stacks-queues.md#a-deque-used-as-a-queue) |
| **a heap, `heapq`** | **the smallest so far, whenever it arrived** | **O(log n), `heappop(h)`** | this module |

The stack and the queue cost nothing to keep in order, because arrival order is recorded by the act of arriving. A heap has to compare items to stay in order, and everything in this module is about what those comparisons buy and what they cost.

> ⭐ **"k largest / k smallest / k closest / k most frequent / kth largest" is ONE problem with FOUR answers, and the scored skill is naming all four and the trade between them.** The four are sort, heapify and k pops, a size-k heap, and quickselect (§Choosing among the four answers), and a fifth when the key is a bounded integer: bucket by count (§The O(n) answer: bucket sort by count).

The one idea underneath all of it:

> *"What is the smallest thing right now — and what if I keep asking?"*
>
> **A heap answers exactly that and nothing else. It is *partially* ordered, and that partial order is the entire trade.**

Everything in §0 is a consequence of that sentence: why push and pop cost log n, why building costs n and not n log n, why a **min**-heap gives you the **largest** k, why the thing you push is almost never a bare value, and why a heap can't answer *"is 7 in here"* or *"delete 7"*.

**This module doesn't re-teach the `heapq` API.** [python-toolkit.md](../reference/python-toolkit.md#4-heapq-the-min-heap), §4. `heapq`: the min-heap has the calls, and you're expected to have them cold. Module 08 used two of them, `heapq.heappush(h, (key, x))` and `heapq.heappop(h)`, as a black box for Dijkstra and Prim ([08-graphs.md](08-graphs.md#weighted-graphs-dijkstra-and-prim), §Weighted graphs: Dijkstra and Prim); here is why they work, and what to put in the heap, which is where every bug in this topic lives.

The drill set at the bottom is not solved anywhere in this module. Every worked example uses a different problem.

**How to use it.** Read §0, then answer the self-check in §0.9 and re-read the parts of §0 behind any question you miss. Then work through what you push, the size-k heap, the choice between the four answers, the worked problems, quickselect, the k-way merge and the two heaps, and do the drill set cold.

| Section | What it gives you |
|---|---|
| §0, the foundation | how a list becomes a heap, the partial order, the array layout, the two repairs and why `heapify` is O(n); the vocabulary, what each operation costs, the five primitives, the inputs that break it, the signals |
| What you push: (priority, payload) | the tuple, its comparison rules, and the tie-breaker that keeps it from crashing |
| Max-heaps and negation | why Python has one direction, and how to get the other |
| The size-k heap | why a **min**-heap keeps the k **largest** |
| Choosing among the four answers | sort, heapify and pop, the size-k heap, quickselect: when each wins, and the bound under all of them |
| Two worked problems | a tie-break that runs the wrong way, and an O(n) answer by counting |
| Quickselect | the O(n) average answer, the two classic bugs, and the ways it breaks |
| k-way merge, two heaps | a heap of k cursors, and a heap on each side of a split |
| What a heap can't do | the wrong-tool table, lazy deletion, the sliding window, heapsort |
| Every template, in one place | one structure and twelve deltas |
| How to attack a heap problem | the steps, in order |
| Common heap mistakes | the bugs, each linked to its entry |
| Drill set | the problems, with the checkpoints |
| Before you submit anything | the checklist |

---

## 0.1 Prerequisites and the one question

| You need | From | Used here for |
|---|---|---|
| Big-O, and what log n means | [00-before-you-start.md](00-before-you-start.md#big-o-from-zero), §Big-O from zero | every cost here is n, log n or log k |
| Best, worst and average case | [00-before-you-start.md](00-before-you-start.md#best-worst-and-average-case), §Best, worst and average case | quickselect is O(n) on average and O(n²) in the worst case |
| Space | [00-before-you-start.md](00-before-you-start.md#space), §Space | the O(k) of a size-k heap, and the Counter you also hold |
| Reading the constraints | [00-before-you-start.md](00-before-you-start.md#reading-the-constraints), §Reading the constraints | n = 10⁶ with k = 10 decides between the four answers |
| Remember, Order, Reuse | [01-arrays-hashing.md](01-arrays-hashing.md#the-three-escapes-remember-order-reuse), §The three escapes: Remember, Order, Reuse | a heap is Order, bought one root at a time |
| Why comparison sorting costs n log n | [01-arrays-hashing.md](01-arrays-hashing.md#why-comparison-sorting-costs-n-log-n-merge-sort), §Why comparison sorting costs n log n: merge sort | the bound quickselect escapes, and why |
| A list used as a stack, a deque used as a queue | [02-stacks-queues.md](02-stacks-queues.md#a-list-used-as-a-stack), §A list used as a stack | the two structures a heap is the third of |
| The amortised argument | [02-stacks-queues.md](02-stacks-queues.md#the-amortised-argument), §The amortised argument | lazy deletion pays for each pop once |
| Merging two sorted lists | [05-linked-lists.md](05-linked-lists.md#merging-two-sorted-lists), §Merging two sorted lists | the k-way merge is that with a heap of heads |
| Dijkstra | [08-graphs.md](08-graphs.md#dijkstra), §Dijkstra | the heap you used there as a black box |
| `heapq`: push, pop, heapify, `nlargest` | [python-toolkit.md](../reference/python-toolkit.md#4-heapq-the-min-heap), §4. `heapq`: the min-heap | every call in this module |

**Every module so far had one irreducible thing.** For trees it was the traversal, for binary search the invariant, for graphs the `visited` set, for backtracking choose, explore, undo, and for DP the state. Here it is one question and its consequence.

| Module | Asks | The answer is |
|---|---|---|
| 04, binary search | *"which half can I throw away?"* | a predicate |
| 08, graphs | *"how do I stop arriving at the same node twice?"* | a mark |
| 09, DP | *"how do I stop solving the same subproblem twice?"* | a memo |
| **10, heaps** | ***"what is the smallest thing right now, and what if I keep asking?"*** | **a partial order** |

**The one question this module answers:**

> *What is the smallest thing right now, and what if I keep asking?*

Read the second half carefully, because it is the whole reason the structure exists. **"What is the smallest thing right now"** on its own is `min(xs)` in O(n), and you'd never build anything. It is **"and what if I keep asking"**, repeatedly, while the collection changes underneath you, that rules out every simpler option:

| If you … | … then |
|---|---|
| call `min(xs)` each time | O(n) per query; m queries cost O(nm) |
| sort once | O(n log n) once, then O(1) per query, **but only if nothing is inserted afterwards** |
| **keep a heap** | **O(log n) per insert and per extract, for as long as the collection keeps changing** |

> **A sorted array is the right answer to "give me everything in order, once." A heap is the right answer to "give me the next one, repeatedly, while I keep adding."**

## 0.2 The structure and how it works

### How a list becomes a heap

You need this line in every problem in this module, so it goes before the theory.

```python
import heapq

heapq.heapify(lst)          # in place · O(n) · returns None
```

**There is no heap type in Python.** A heap is an ordinary `list` that happens to satisfy the heap property, and `heapq` is a set of free functions that maintain it. Nothing is wrapped and nothing is subclassed; `len()` and `lst[0]` work as they always did.

The four ways you'll get one, and the cost of each:

| You have | Write | Cost | Use when |
|---|---|---|---|
| a list, already | `heapq.heapify(lst)` | **O(n)** | you have all the data up front |
| a list you must not mutate | `h = lst[:]`, then `heapq.heapify(h)` | O(n) | the caller still needs `lst` |
| items arriving one at a time | `h = []`, then `heapq.heappush(h, x)` per item | O(n log n) for n items | a stream: you never had them all |
| a list, and you want a **max**-heap | `h = [-x for x in lst]`, then `heapq.heapify(h)` | O(n) | negate on the way out too (§Max-heaps and negation) |

> ⭐ **If you already hold the whole list, `heapify` it. Never loop pushes over a list you're already holding**: that is O(n log n) to build the identical structure. §Why heapify is O(n), not O(n log n) proves the gap.

### Four things that bite

In the order they'll bite you:

1. **`heapify` returns `None`.** It mutates in place, like `list.sort()`.
   ```python
   h = heapq.heapify(lst)      # h is None, and the next heappop(h) raises TypeError
   heapq.heapify(lst)          # right: lst is the heap now
   ```
2. **It mutates the list you were handed.** If that list is the function's input and the caller reads it afterwards, you've changed their data. Copy with `lst[:]` first when in doubt; it's O(n), and you were already paying O(n).
3. **The result looks scrambled, and that is correct.** After `heapify([5, 1, 9, 3, 7])` the list is `[1, 3, 9, 5, 7]`. Only index 0 is guaranteed. Printing the list and deciding "it didn't work" is the standard first reaction (§Partial order is the entire trade).
4. **Heapifying a list of lists or tuples works, by lexicographic comparison.** `heapq.heapify([[3, 'c'], [1, 'a']])` gives `[[1, 'a'], [3, 'c']]`: it orders on the first element, then the second. That is the whole mechanism behind `(priority, payload)`, and it is also the trap when the payload turns out not to be comparable (§What you push: (priority, payload)).

The one place this choice changes your complexity answer. Both of these return the k largest, and interviewers ask which is better:

| | Build | Then | Total | Space |
|---|---|---|---|---|
| **heapify, then k pops** | O(n) | k pops × log n | **O(n + k log n)** | O(n), or O(1) extra if you may mutate the input |
| **a size-k heap, one pass** | nothing | n pushes × log k | **O(n log k)** | **O(k)** |

> **Neither dominates.** Heapify and k pops wins when k is close to n; the size-k heap wins when k is small, and it is the only one of the two that works on a stream or on data too big to hold. Say both, then pick (§Choosing among the four answers).

### Partial order is the entire trade

A heap is a binary tree with **one** property:

> **Every parent is ≤ both of its children.** That is a min-heap; a max-heap flips it.

That is a weaker promise than sorted, and the weakness is deliberate. What it does and doesn't buy:

| | You get | You do **not** get |
|---|---|---|
| the root, `h[0]` | the **global minimum**, O(1) to read | |
| `h[1]`, `h[2]` | the two children of the root | **they are not ranks 2 and 3.** The second smallest is `min(h[1], h[2])`, and only because of the property |
| the list | a valid heap | **it is not sorted.** `list(h)` is in array order, which means nothing |
| any other element | | you can't find it, delete it, or tell whether it's there without a linear scan |

**The list is not sorted, and it is not "nearly sorted".** `[0, 5, 1, 8, 6, 2]` is a valid min-heap: every parent is ≤ its children, `h[1]` is 5, and the second smallest is `h[2]`, which is 1.

> ⚠️ **The bug this causes:** returning the heap and expecting an order. A size-k heap of the k largest is correct as a **set** and meaningless as a **sequence**. If the problem wants them ordered, that is `sorted(h)`, an extra O(k log k), and you should say so rather than hope.

**Why the weaker promise is cheaper.** Sorted means every one of the n elements knows its exact rank, and any comparison sort pays Ω(n log n) for that (§Choosing among the four answers gives the argument). The heap property only constrains each node against its parent, one comparison per node, and repairing it after a change touches **one root-to-leaf path**. That is the whole complexity story; the rest of §0.2 is this sentence written out.

### The three structures, side by side

| | Build | Insert | Read min | Extract min | Find or delete an arbitrary item | Full order |
|---|---|---|---|---|---|---|
| unsorted list | O(1) | O(1) | **O(n)** | O(n) | O(n) | no |
| sorted list | O(n log n) | **O(n)** | O(1) | O(1) from the end of a list sorted largest first | O(log n) to find, O(n) to delete | yes |
| **heap** | **O(n)** | **O(log n)** | **O(1)** | **O(log n)** | **O(n)** | **no** |

```compare
title: Three structures for a min
option: Unsorted list
  Build: O(1)
  Insert: O(1)
  Read min: O(n)
  Extract min: O(n)
  Find or delete any item: O(n)
  Full order: no
option: Sorted list
  Build: O(n log n)
  Insert: O(n)
  Read min: O(1)
  Extract min: O(1) from the end, if sorted largest first
  Find or delete any item: O(log n) to find, O(n) to delete
  Full order: yes
option: Heap
  Build: O(n)
  Insert: O(log n)
  Read min: O(1)
  Extract min: O(log n)
  Find or delete any item: O(n)
  Full order: no
```


**Every bold entry in that table is a decision rule.** The heap wins exactly one pair of columns, insert and extract-min together, and it loses the last two outright (§When a heap is the wrong tool).

### The array layout

A heap is drawn as a tree and **stored as a flat list.** There are no node objects and no pointers, which is why `heapq` works directly on an ordinary Python `list`.

```
index:      0   1   2   3   4   5   6
value:    [ 1,  3,  2,  7,  4,  9,  8 ]

                    1                     ← index 0
                  /   \
                3       2                 ← indices 1, 2
               / \     / \
              7   4   9   8               ← indices 3, 4, 5, 6
```

Sorted, that list is `[1, 2, 3, 4, 7, 8, 9]`; the heap is not. The three lines of arithmetic, which you should be able to write without thinking:

```python
left(i)   = 2*i + 1
right(i)  = 2*i + 2
parent(i) = (i - 1) // 2
```

**Why this works at all:** the tree is **complete**. Every level is full except the last, which fills left to right. A complete tree has no holes, so numbering it level by level is dense, and dense numbering is exactly an array index. The heap property is what you maintain; **completeness is what you must never break**, and it is why insertion appends at the end and deletion moves the *last* element to the root instead of leaving a gap.

Two facts fall straight out of the layout:

- **The height is ⌊log₂ n⌋.** A complete tree over n nodes can't be taller: 1 node has height 0, 2 or 3 nodes height 1, 4 to 7 nodes height 2, 8 to 15 nodes height 3. This is where every log n in this module comes from; there is only one.
- **The leaves are the second half of the array.** Indices `n//2` to `n - 1` have no children, because `2*(n//2) + 1 ≥ n`. So `n//2 - 1` is the **last internal node**, and that is where `heapify` starts. For n = 7 the leaves are indices 3 to 6 and the last internal node is 2; for n = 6 the leaves are 3 to 5 and the last internal node is still 2.

> ⭐ **Half of a heap is leaves.** It is the most useful number in this module, and it explains both `heapify`'s cost and why building by repeated push is worse.

### Sift up and sift down

Every heap operation is one of two repairs, and each walks **one root-to-leaf path**.

**Sift up, used by push:**

```
append x at the end                  ← keeps the tree complete
while x < parent(x):  swap them      ← walk UP toward the root
```

The new element starts at a **leaf** and can travel the full height: O(log n).

```steps
title: Push 0, sift up
array: 1 3 2 7 4 9 8
- n=7 | The heap has 7 items. A push appends at index 7, which keeps the tree complete.
- array=[1, 3, 2, 7, 4, 9, 8, 0] i=7 parent=3 | Append 0 at `i=7`. The parent of `i` is `(i - 1) // 2`, here 3, holding 7. 0 is smaller, so swap.
- array=[1, 3, 2, 0, 4, 9, 8, 7] i=3 parent=1 | 0 is now at index 3. Its parent is `(3 - 1) // 2 = 1`, holding 3. 0 is smaller, so swap.
- array=[1, 0, 2, 3, 4, 9, 8, 7] i=1 parent=0 | 0 is at index 1. Its parent is index 0, holding 1. 0 is smaller, so swap.
- array=[0, 1, 2, 3, 4, 9, 8, 7] i=0 | 0 is at the root and has no parent. The heap property holds again.
```


**Sift down, used by pop:**

```
answer = h[0]                        ← the minimum, which is what you wanted
move the LAST element to the root    ← keeps the tree complete
while it is > either child:
    swap it with the SMALLER child   ← walk DOWN toward the leaves
```

The displaced element starts at the **root** and can travel the full height: O(log n).

```steps
title: Pop, sift down
array: 1 3 2 7 4 9 8
- i=0 | Pop: the answer is `h[0] = 1`, the minimum. The root is the hole to fill.
- array=[8, 3, 2, 7, 4, 9] i=0 | Move the last item, 8, to the root. The array is one shorter and still complete.
- array=[8, 3, 2, 7, 4, 9] i=0 child=2 | The children of `i` are `2*i + 1 = 1`, holding 3, and `2*i + 2 = 2`, holding 2. The smaller is at index 2. 8 is larger than 2.
- array=[2, 3, 8, 7, 4, 9] i=2 child=5 | Swap with the smaller child. 8 is at index 2. Its left child, `2*2 + 1 = 5`, holds 9, and there is no right child.
- array=[2, 3, 8, 7, 4, 9] i=2 | 8 is not larger than 9, so it stays. The new minimum is 2.
```


> ⚠️ **Swap with the *smaller* child, not with either.** Swapping with the larger one puts a bigger value above its smaller sibling and breaks the property you're repairing. This is the one line people get wrong when asked to write sift-down on a whiteboard.

### Why heapify is O(n), not O(n log n)

This is the piece worth being able to argue, because it is the standard follow-up and it sounds wrong.

`heapify` calls **sift-down** on every internal node, from `n//2 - 1` down to `0`. Naively that is n/2 sift-downs at O(log n) each, so O(n log n). **The naive count is wrong because it charges every node the full height, and almost no node is near the root.** A sift-down costs at most the node's height above the leaves, so count by that height:

| Height above the leaves | How many nodes, at most | Cost each, at most | Total |
|---|---|---|---|
| 0, the leaves | n/2 | **0**: no children, nothing to do | 0 |
| 1 | n/4 | 1 | n/4 |
| 2 | n/8 | 2 | 2n/8 |
| 3 | n/16 | 3 | 3n/16 |
| j | n/2^(j+1) | j | j·n/2^(j+1) |

The total is n/2 × (1/2 + 2/4 + 3/8 + …) = n/2 × 2 = **n**. The series Σ j/2^j sums to 2: write it as (1/2 + 1/4 + 1/8 + …) + (1/4 + 1/8 + …) + (1/8 + …) + …, which is 1 + 1/2 + 1/4 + … = 2. For n = 10⁶, the exact total of the heights of all the nodes, the most work heapify can do, is 999,993: under n.

**The sentence to say in a room, no algebra:**

> **"Sift-down's cost is the distance to the leaves, and half the nodes *are* leaves and cost nothing. The nodes that cost log n, the ones near the root, are only a handful. The series n/4 + 2n/8 + 3n/16 + … converges to n."**

### The mirror image

Building the same heap with n `heappush` calls is **O(n log n)**, and the contrast is exact:

| | Starts at | The expensive nodes are | How many of them |
|---|---|---|---|
| **sift-down** (`heapify`) | an internal node, walking toward the leaves | **near the root** | **rare**: 1, then 2, then 4 |
| **sift-up** (`push`) | a leaf, walking toward the root | **the leaves** | **half of everything** |

> **Both walk a path whose length is "the distance to the far end". `heapify` puts the long walks on the rare nodes; pushing puts them on the common ones.** Same tree, same property, a factor of log n apart.

Pushing n items one at a time is Θ(n log n) in the worst case: on a decreasing input every new item is the new minimum and sifts all the way to the root, and the last n/2 of them each climb at least ⌊log₂(n/2)⌋ levels. So if you already have the whole list, `heapify` it. Build by pushing only when the items **arrive over time**.

## 0.3 Vocabulary

| Word | Meaning |
|---|---|
| **heap** | a complete binary tree, stored as a list, in which every parent is ≤ its children |
| **heap property** | that one rule, *parent ≤ children*; it says nothing about siblings or cousins |
| **min-heap, max-heap** | the root is the smallest, or the largest; `heapq` only builds the first |
| **root** | `h[0]`: the one element a heap can locate in O(1) |
| **complete tree** | every level full except the last, which fills from the left; why the list has no holes |
| **sift up** | the repair after a push: swap the new item with its parent while it is smaller |
| **sift down** | the repair after a pop: swap the moved item with its *smaller* child while it is larger |
| **heapify** | turning a whole list into a heap in place, in O(n) |
| **priority** | the field the heap orders by; it must be field 0 of what you push |
| **payload** | what you need back when the item comes out; it rides behind the priority |
| **tie-breaker** | a field between priority and payload that is never equal for two entries, so the payload is never compared |
| **size-k heap** | a heap capped at k items by evicting the root on every overflow |
| **top-k** | the k largest (or smallest, or closest) items, as a set |
| **kth largest** | the item with exactly k − 1 items above it; for k = 1 it is the maximum |
| **selection** | finding the kth item, or the k best, without sorting the rest |
| **quickselect** | selection by partitioning around a pivot and recursing into one side only |
| **pivot** | the element a partition compares everything else against |
| **partition** | rearranging a range so everything smaller than the pivot comes before it and the rest after |
| **k-way merge** | merging k sorted sequences with a heap holding one cursor per sequence |
| **two heaps** | a max-heap of the lower half beside a min-heap of the upper half, so both middle values sit at roots |
| **lazy deletion** | marking an item dead instead of removing it, and discarding it when it reaches the root |
| **decrease-key** | changing an item's priority in place; `heapq` doesn't have it |
| **bucket sort** | sorting by using a small integer key as a list index, with no comparisons |

## 0.4 Operations and their cost

**n** is the number of items in the heap. **k** is the cap on a size-k heap.

| Operation | Python | Big-O | Trap |
|---|---|---|---|
| Build from a list | `heapq.heapify(lst)` | **O(n)** | returns `None`, and mutates `lst` |
| Push | `heapq.heappush(h, x)` | O(log n) | on a max-heap, forgetting to push `-x` |
| Pop the minimum | `heapq.heappop(h)` | O(log n) | `IndexError: index out of range` on an empty heap |
| Read the minimum | `h[0]` | O(1) | `IndexError` on an empty heap; `h[1]` is **not** the second smallest |
| Push, then pop | `heapq.heappushpop(h, x)` | O(log n), one sift | returns `x` itself when `x` is no larger than the root |
| Pop, then push | `heapq.heapreplace(h, x)` | O(log n), one sift | returns the old root, whatever `x` is, so it drops the root even when `x` is worse than it: on `[3, 5]`, `heapreplace(h, 1)` returns 3 and leaves `[1, 5]`, while `heappushpop(h, 1)` returns 1 and leaves `[3, 5]` |
| The k largest or smallest | `heapq.nlargest(k, xs, key=f)`, `heapq.nsmallest(k, xs, key=f)` | O(n log k) | returns a **sorted list**, so it can't serve a stream |
| Check membership | `x in h` | **O(n)** | a heap is not a set |
| Remove an arbitrary item | `h.remove(x)`, then `heapq.heapify(h)` | **O(n)** | without the `heapify`, the heap property is broken and nothing says so |
| Merge sorted iterables | `heapq.merge(*its)` | O(N log k) for N items over k inputs | returns a lazy iterator, not a list |
| Size | `len(h)` | O(1) | none |

**The row people get wrong is `heapify`.** It is O(n), not O(n log n), and the gap is the standard follow-up (§Why heapify is O(n), not O(n log n)). The second row people get wrong is `h[0]` read as "sorted": only the root is placed.

## 0.5 The primitives

Five moves build almost every heap solution. Each has an invariant: the thing that is true every time it runs.

**1. Push and pop.**

```python
heapq.heappush(h, x)
smallest = heapq.heappop(h)          # IndexError if h is empty
```

*Invariant:* `h[(i - 1) // 2] <= h[i]` for every `i ≥ 1`, before and after each call, so `h[0]` is the minimum of everything in `h`. On an empty heap there is no root, and both `h[0]` and `heappop` raise `IndexError`; check `if h` first.

**2. Negation, for a max-heap.**

```python
heapq.heappush(h, -x)
largest = -heapq.heappop(h)          # the minus on the way OUT is the one that gets forgotten
```

*Invariant:* `h` holds the negatives of the items, so `-h[0]` is the maximum of the items. Every value that goes in is negated and every value that comes out is negated back, in the same expression.

**3. The priority tuple, with a tie-breaker.**

```python
tie = itertools.count()
heapq.heappush(h, (priority, next(tie), item))
priority, _, item = heapq.heappop(h)
```

*Invariant:* field 0 is the quantity you're ordering by, and field 1 is different for every entry ever pushed, so a comparison never reaches `item`. Ties in priority come out in the order they were pushed.

**4. The size-k eviction.**

```python
heapq.heappush(h, x)
if len(h) > k:
    heapq.heappop(h)                 # throw away the weakest survivor
```

*Invariant:* after each item, `h` holds the k largest items seen so far, or all of them if fewer than k have been seen, and `len(h) <= k`. The root is the one item that would be evicted next (§The size-k heap: why a min-heap gives the k largest).

**5. The lazy skip.**

```python
while h and dead[h[0]]:              # dead: a Counter of items marked removed
    dead[h[0]] -= 1
    heapq.heappop(h)
```

*Invariant:* after the loop, `h` is empty or its root is a live item, so `h[0]` is the minimum of the live items. Dead items deeper in the heap are allowed; only the root has to be clean (§Lazy deletion).

`dead` is a `Counter`, not a `set`, because of duplicates: a set records only that a value is dead, so removing one 5 would kill every 5 in the heap. The count lets each purge spend exactly one.

## 0.6 Inputs that break it

| Input | What breaks | Check |
|---|---|---|
| An empty heap | `heappop(h)` or `h[0]` raises `IndexError` | guard with `if h`, or decide what the problem returns when nothing is left |
| k = 1 | every method is doing the work of `max()` | trace it; it is also the test that catches an off-by-one in a kth-element index |
| k = n | the size-k heap never evicts; it is a slow sort | the answer is the whole input; trace it |
| k > n | `len(h) > k` never fires, and the heap holds fewer than k items | decide what the problem wants for too few items, explicitly |
| Duplicate priorities with a payload that has no `__lt__` | `TypeError: '<' not supported between instances of …`, on the inputs with a tie only | can field 0 tie? Then add a tie-breaker (§What you push: (priority, payload)) |
| An already sorted input | a fixed-pivot quickselect goes O(n²) | take a random pivot (§The ways it breaks) |
| Every element equal | a two-way partition puts everything on one side: O(n²) even with a random pivot | a three-way partition (§Duplicates: the three-way partition) |
| The caller's list, heapified | the caller's data comes back scrambled | `h = lst[:]` first, or say that you mutate it |
| An object whose priority changes while it is in the heap | the heap property breaks silently, and later pops are wrong | push a new entry and skip the stale one (§Lazy deletion) |
| A tuple negated for a max-heap | `TypeError: bad operand type for unary -: 'tuple'` | negate field 0 only (§Max-heaps and negation) |
| A tie-break that runs opposite to the main order | the right counts and the wrong items | §Top-K with a tie-break that runs the wrong way |

## 0.7 Complexity, out loud

Say these as sentences, with the reason:

- **The size-k heap:** *"O(n log k) time, because the loop runs n times and each push-and-pop costs log of the heap's size, and the heap never holds more than k."* The load-bearing clause is the last one: **a heap operation costs log of the number of items in the heap, not in the input.**
- **The log k does not come from stopping early.** The loop reads every one of the n items, and it has to, because the last one might be the largest. Say it as a product: n × log n against n × log k. The left factor is the same; only the price of each step moved.
- **Space:** *"O(k), because the only thing I allocate is the heap, and I cap it at k."* If you counted frequencies first, add O(u) for the u distinct keys in the `Counter`; it usually dominates, and it is the term people forget. If you heapified the input in place, it is O(1) extra and you destroyed the caller's list: say which.
- **Heapify and k pops:** *"O(n + k log n): O(n) to build, because half the nodes are leaves and cost nothing, then k pops at log n each."*
- **Quickselect, average and worst, every time:** *"O(n) average, O(n²) worst, and I take a random pivot so the worst case needs bad luck rather than bad input."* Naming only the average is the tell that you memorised the result.
- **Ordered output costs a term.** Any of the four answers gives a set; ranking it is another O(k log k), and you say so.
- **Optimality:** *"Any correct algorithm has to read every item at least once, because an unread item could be the largest, so Ω(n) is a floor. Quickselect meets it on average."* Then the reason the sorting bound doesn't apply: selection asks for a set, not an arrangement. A comparison sort must tell apart all n! orderings, and each comparison at best halves the candidates, so it needs log₂ n! ≈ n log n comparisons. Selection only has to tell apart C(n, k) ≤ 2ⁿ possible sets, so the same argument demands at most n comparisons, and the floor left standing is Ω(n), from reading every item (§Why selection can be linear when sorting can't).

## 0.8 Signals

| In the statement | Reach for | Where |
|---|---|---|
| "k largest", "k smallest", "k closest", "k most frequent", "kth largest", "top k" | sort, a size-k heap, quickselect, and their variants, named together | §Choosing among the four answers |
| "as numbers arrive", "a stream", input that never ends | a size-k heap: you can't sort what hasn't arrived | §The size-k heap: why a min-heap gives the k largest |
| "the median" of something that keeps growing | two heaps | §Two heaps |
| "merge k sorted …" | a k-way merge: a heap of one cursor per input | §k-way merge |
| "the next, the cheapest, the highest priority", repeatedly, while new items arrive | a plain heap, usually inside a simulation | §0.5, primitives 1 and 2 |
| "shortest path" with non-negative weights | Dijkstra: a BFS whose queue is a heap | [08-graphs.md](08-graphs.md#weighted-graphs-dijkstra-and-prim), §Weighted graphs: Dijkstra and Prim |
| "schedule", "rooms", "intervals that overlap" | a heap of end times: a pop means *"this one has finished"* | §0.5, primitive 1 |
| a brute force that sorts, takes the front, and sorts again | the heap is the incremental version of that loop | §0.1 |
| "take the two smallest, combine them, put the result back" | pop, pop, push; Huffman coding is the same program | §0.5, primitive 1 |
| n huge and k small | O(n log k) time and, more to the point, O(k) space | §0.7 |
| a sort key that is a small bounded integer, such as a count | not a heap: bucket by the key, O(n) | §The O(n) answer: bucket sort by count |
| the kth item, once, with the whole array in hand | not a heap first: quickselect is O(n) on average | §Quickselect |
| "delete this item", "is x in here", "change this item's priority" | not a heap alone: a second structure, or lazy deletion | §What a heap can't do |
| the min or max of a window that slides | not a heap: a monotonic deque, O(n) | §A sliding window min or max |

## 0.9 Self-check

Answer each in a sentence or two, without looking back. The answers are at the bottom of the module. Read the part behind any question you miss.

1. `heapify` calls sift-down on n/2 nodes, and sift-down is O(log n). Why is `heapify` O(n) and not O(n log n)?
2. `h = [0, 5, 1, 8, 6, 2]` is a valid min-heap. Is `h[1]` the second smallest item? Where is the second smallest, in general?
3. Why does a **min**-heap keep the k **largest** items, and what does it evict?
4. You push `(cost, task)`, where `task` is an object with no `__lt__`, and every test passes. Which input breaks it, with what error, and what is the fix?
5. *"The size-k heap is O(n log k) instead of O(n log n) because it stops once it has seen the kth value."* What is wrong with that sentence, and what is the right one?
6. Comparison sorting is Ω(n log n). Why doesn't that bound stop quickselect from being O(n)?
7. In lazy deletion, why are the dead items kept in a `Counter` and not a `set`?
8. `h = [3, 5]`. What do `heapq.heappushpop(h, 1)` and `heapq.heapreplace(h, 1)` each return, and what does `h` hold after each, starting from `[3, 5]` both times?

---

## What you push: (priority, payload)

This is index vs value ([bug-checklist.md](../reference/bug-checklist.md#index-vs-value), §Index vs value) in a heap's clothes. Here it is **value vs (priority, payload)**: you push the number you're comparing, and then discover you needed to know which item it belonged to.

**`heapq` compares tuples lexicographically**: field 0, then field 1 on a tie, and so on. That is the entire mechanism for attaching a payload to a priority:

```python
heapq.heappush(h, (cost, task))          # ordered by cost; task comes along for the ride
heapq.heappush(h, (-count, word))        # a max-heap on count; word ascending within a count
heapq.heappush(h, (cost, node))          # Dijkstra
```

### There is no key=

Unlike `sorted`, the ordering must live **inside** the element. This is the most common first attempt in this topic, and it doesn't run:

```python
heapq.heapify(dist, key=lambda x, y, d: d)
# TypeError: _heapq.heapify() takes no keyword arguments
```

**Two separate mistakes are stacked in that line.**

1. **`heapify` has no `key` parameter at all**, and neither does any other heap *operation*:

   | Function | `key=`? |
   |---|---|
   | `heapify`, `heappush`, `heappop`, `heappushpop`, `heapreplace` | **no** |
   | `nlargest`, `nsmallest` | yes |
   | `merge` | yes |

   **The reason is structural, not an oversight.** `sorted` calls your key **once per element** and keeps the computed values. A heap re-compares on **every sift-up and sift-down for the whole life of the structure**, so it compares elements directly with `<` and never calls anything.

   > ⭐ **`sorted` takes a key because it decorates once. A heap can't, so you decorate it yourself, by making the element *be* the tuple.**

2. **The lambda could never bind anyway.** A key function is handed **one element**, not its fields. `lambda x, y, d: d` demands three arguments; the right shape is `lambda t: t[2]`. If you find yourself writing a multi-argument lambda for a collection, the mental model has slipped from "elements" to "columns".

The three legitimate fixes, in the order to reach for them:

| Fix | Shape | When |
|---|---|---|
| **put the key at field 0** | `(cost, x, y)` instead of `(x, y, cost)` | almost always: one line, nothing to remember |
| `nsmallest` or `nlargest` with `key=` | `heapq.nsmallest(k, items, key=f)` | you may use the batteries and you don't need a stream |
| a wrapper class with `__lt__` | the class holds the payload, and `__lt__` compares the derived value | the key isn't numeric, or the tie-break runs the wrong way (below) |

The first row has its own entry: [bug-checklist.md](../reference/bug-checklist.md#the-heap-tuple-in-the-wrong-order), §The heap tuple in the wrong order. Read element 0 of every `heappush` you write, and check it is the quantity the statement names.

### How tuple comparison works

Four rules, and each of them shows up as a bug.

1. **Field 0 decides.** Field 1 is consulted **only** when field 0 is exactly equal, and field 2 only when fields 0 and 1 both are.
2. **So the field you order by must be first.** `(x, y, cost)` is a heap ordered by **x**; `cost` is never looked at unless two entries share both coordinates. It is the same error as [bug-checklist.md](../reference/bug-checklist.md#index-vs-value), §Index vs value: the value you meant against the value the code reaches.
3. **A shorter tuple that is a prefix of a longer one is smaller.** `(1, 2) < (1, 2, 0)` is `True`. Mixing tuple lengths in one heap is silently legal and almost never what you meant.
4. **A `TypeError` fires only when a comparison reaches a field that can't be compared.** That depends on the input: it can pass every test you tried and fail on the one with a tie.

**Lists compare by exactly the same rules**, which is why a list of `[priority, item]` pairs heapifies without complaint: useful, and a common accident.

### The three-line question to answer before you push anything

> 1. **What am I ordering by?** That is field 0.
> 2. **What do I need to still have when it comes back out?** That is the payload.
> 3. **Can field 0 tie, and if it does, is field 1 comparable?**

Question 3 is the trap.

### The tie-breaking trap

When two priorities are equal, Python moves to field 1 **and compares it**. If field 1 isn't comparable, you get a `TypeError` at runtime, on *some* inputs, which is worse than always:

```python
h = []
heapq.heappush(h, (1, [3, 4]))
heapq.heappush(h, (2, [1, 2]))       # fine: 1 < 2, field 1 never consulted
heapq.heappush(h, (1, [0, 0]))       # fine: lists ARE comparable
heapq.heappush(h, (1, Point(0, 0)))  # TypeError: '<' not supported between instances of 'Point' and 'list'
```

**Safe as field 1:** `int`, `float`, `str`, and a `tuple` or `list` of comparables. **Not safe:** any class without `__lt__`, a `dict`, a `set`, and `None` against a number.

**The fix is a tie-breaker that can never tie:**

```python
h = []
for i, item in enumerate(items):
    heapq.heappush(h, (priority(item), i, item))   # i is unique, so field 2 is never reached
```

**That buys two things at once:** the payload is never compared, **and** ties resolve by insertion order, first in, first out, which is often exactly the behaviour the problem wanted. Push `x`, `y`, `z`, `w` with priorities 2, 1, 2, 1 and they come out `y`, `w`, `x`, `z`.

### Why a missing tie-breaker is the worst shape of bug

Measured, not reasoned. This is what Python does with a `ListNode` that has no `__lt__`:

| You push | Result |
|---|---|
| `node` | `TypeError: '<' not supported between instances of 'ListNode' and 'ListNode'` |
| `(node.val, node)`, **all values distinct** | **no error** |
| `(node.val, node)`, **one tie** | `TypeError`, the same message |
| `(node.val, i, node)`, **all values tied** | fine |

Row 2 is the whole problem. **Leaving out the tie-breaker passes every test whose priorities happen to be distinct.** A two-element smoke test can't see it; the failure arrives on submission, on an input you never typed.

> ⭐ This is [bug-checklist.md](../reference/bug-checklist.md#the-guard-asymmetry), §The guard asymmetry: **the necessary guard that looks like an unnecessary one.** You can't justify the middle field by running the code, because the code runs. You justify it by asking whether field 0 *can* tie. If it can, the field is mandatory, whatever the tests say.

What to use as the tie-breaker:

| Situation | Use | Why it can never tie |
|---|---|---|
| a k-way merge, one entry per input at a time | the **input's index** `i` | the heap holds **at most one entry per input** at any moment, so two entries can't carry the same index |
| everything else | `tie = itertools.count()`, then `next(tie)` | unique by construction, whatever is in the heap |

Say that reason out loud. *"The index is unique because only one entry per input is in the heap"* is a statement about the invariant; *"I always add an index"* is a ritual. In a heap where several entries share an origin, the index **does** tie, and you need the counter.

### The third fix: a wrapper class with `__lt__`

The two options above put the ordering in the *element*. A wrapper puts it in the *type*:

```python
class NodeWrapper:
    def __init__(self, node):
        self.node = node
    def __lt__(self, other):
        return self.node.val < other.node.val

h = []
heapq.heappush(h, NodeWrapper(head))   # head: the first node of one list
smallest = heapq.heappop(h).node
```

`heapq` only ever calls `<`, so defining `__lt__` is enough. You don't need `__eq__`, `__gt__` or `functools.total_ordering`.

| | the tuple `(val, i, node)` | `NodeWrapper` |
|---|---|---|
| tie-breaker needed | **yes, mandatory** | no: `__lt__` decides ties itself and never reaches the payload |
| priority visible at the push site | yes | no, hidden in the class |
| extra object per push | a tuple | an instance, heavier |
| a tie-break running **opposite** to the main key | impossible by negation | **this is the case it exists for** (below) |

> **Default to the tuple.** It is the shorter thing to write under pressure, and the priority reads off the push site. Reach for the wrapper when the order can't be written as "compare these fields ascending", which in practice means §Top-K with a tie-break that runs the wrong way.

⚠️ Don't solve this by patching the class you were handed. `ListNode.__lt__ = lambda a, b: a.val < b.val` works, and silently changes `sorted`, `min` and `max` on nodes everywhere else in the program.

### A tie-break that runs the wrong way

Sometimes the main key wants descending and the tie-break wants ascending: *"the most frequent words, ties broken alphabetically."* One negation can't express that:

- `(-count, word)` is count descending and word ascending. **Right for a full sort.**
- But a **size-k min-heap evicts its minimum**, so it needs the *reverse* of the final order: the worst item must be the smallest. The worst is the lowest count and, among equal counts, the **alphabetically last** word. `(count, word)` gets the count right and the word backwards.

> **When the tie-break runs opposite to the main key, a size-k heap needs a wrapper class with `__lt__`.** Say that, then write `heapq.nsmallest(k, items, key=lambda w: (-cnt[w], w))`: full marks for knowing the constraint, and none of the risk of writing a comparator cold. §Top-K with a tie-break that runs the wrong way works this in full.

## Max-heaps and negation

**Python's public `heapq` has no max-heap.** It is a min-heap, and there is no `reverse=True`. The fix is to negate on the way in and on the way out (§0.5, primitive 2).

**Why it works:** `a < b` exactly when `-a > -b`. Negation reverses the order, so the minimum of the negatives is the maximum of the originals. Nothing about the heap changes.

### Three ways negation breaks

1. **Forgetting the minus on the way out.** The values come back negative and the answer is sign-flipped. Every `heappop` on a negated heap should have a `-` glued to it in the same expression.
2. **`-x` on a tuple is a `TypeError`**: `bad operand type for unary -: 'tuple'`. Negate **the priority field only**: `(-count, word)`. That reverses the *first* field and leaves the second ascending, which is sometimes exactly right and sometimes exactly wrong (§A tie-break that runs the wrong way).
3. **You can't negate a string or an object.** For a non-numeric key there is no negation trick at all. The options are a wrapper class with `__lt__`, `sorted` or `nsmallest` with a `key=`, or reversing the *problem* instead of the key.

### Going from a min-heap to a max-heap once one exists

**You can't relabel it. You have to rebuild it.** A valid min-heap, negated element by element, is **not** a valid min-heap of the negatives: every parent is now ≥ its children, which is the exact opposite of what `heapq` needs.

```python
a = [3, 5, 4, 9, 7]          # a valid min-heap: every parent <= its children
n = [-x for x in a]          # [-3, -5, -4, -9, -7]: every parent >= its children, NOT a heapq heap
heapq.heapify(n)             # [-9, -7, -4, -5, -3]; this line is not optional
```

| Direction | Write | Cost |
|---|---|---|
| min to max | `h = [-x for x in h]`, then `heapq.heapify(h)` | **O(n)** |
| max to min | the same: negate again, heapify again | **O(n)** |
| min to max, tuple entries | `h = [(-p, *rest) for (p, *rest) in h]`, then `heapify`: **negate field 0 only** | O(n) |
| either way, a non-numeric key | a wrapper class with `__lt__` reversed; there is no negation | O(n) |

The first two rows are the same operation: it is its own inverse, and running it twice gets you home. **The cost is O(n) and not O(n log n)** because you're building a heap from a list you already hold, which is `heapify`, not a loop of pushes (§How a list becomes a heap).

> ⚠️ **`heapq._heapify_max` exists. Don't build on it.** Up to Python 3.13 the max family is private: `_heapify_max`, `_heappop_max` and `_heapreplace_max`, and **no push**. You can build a max-heap and drain it, but you can't grow it, so any streaming or size-k use collapses. Python 3.14 makes a full max family public; LeetCode and most interview environments run older versions, so negate.

### The decision that makes conversion unnecessary

Converting costs a full O(n) pass, and needing one usually means the direction was chosen by habit rather than by the job. Pick it before you build, with one question: **what sits at the root?**

| Your loop wants to … | The root must be … | So build a heap where … |
|---|---|---|
| **take** the next best item, repeatedly | the item you want **next** | the best item is the smallest |
| **evict** a loser to hold the best k | the item you want to **throw away** | the *worst of the survivors* is the smallest |

Those two point in **opposite directions for the same problem**, which is why "the k closest" and "the closest, then the next closest" want different heaps (§The size-k heap: why a min-heap gives the k largest).

> ⭐ **The escape that is almost always right in an interview:** `heapq.nlargest(k, xs, key=f)` and `heapq.nsmallest(k, xs, key=f)`. They take a `key`, they run the size-k heap for you, they return a **sorted** list, and they are O(n log k). On `[3, 5, 4, 9, 7]`, `nlargest(2, …)` is `[9, 7]` and `nsmallest(2, …)` is `[3, 4]`. Reach for them unless the problem is a *stream* or the interviewer asked for the mechanism.

## The size-k heap: why a min-heap gives the k largest

The most counter-intuitive line in the topic, and it is one sentence:

> **The heap's minimum is the *weakest member of your current top k*, which is exactly the one to throw away when something better arrives.**

You aren't maintaining "the biggest things". You're maintaining **the k survivors**, and the only element you ever need to touch is the one on the chopping block. A min-heap puts that element at the root: O(1) to look at and O(log k) to evict.

```python
def k_largest(items, k):
    h = []
    for x in items:
        heapq.heappush(h, x)
        if len(h) > k:
            heapq.heappop(h)         # evict the smallest: the weakest survivor
    return h                         # the k largest, UNORDERED
```

**Trace it on `[5, 1, 9, 3, 7]`, k = 2:**

| x | after push | len > k? | after pop | the heap means |
|---|---|---|---|---|
| 5 | `[5]` | no | `[5]` | the top 1 so far |
| 1 | `[1, 5]` | no | `[1, 5]` | the top 2 so far |
| 9 | `[1, 5, 9]` | **yes** | `[5, 9]` | 1 was the weakest, so it goes |
| 3 | `[3, 9, 5]` | **yes** | `[5, 9]` | 3 arrived and was *immediately* the weakest, so it goes |
| 7 | `[5, 9, 7]` | **yes** | `[7, 9]` | 5 was the weakest, so it goes |

It returns `[7, 9]`, the set {7, 9}. Row 4 is worth a look: an element that doesn't belong is pushed and popped straight back out. That isn't a bug; it is the cost of not checking first.

### Push then pop, in that order

`push`, then `if len(h) > k: pop`, is right. `if len(h) == k: pop`, then `push`, is **not**: it evicts before knowing whether the new arrival is even better, so it can throw away a real survivor.

The one-call versions, and they matter for the same reason:

```python
heapq.heappushpop(h, x)    # push then pop: safe at size k, and one sift instead of two
heapq.heapreplace(h, x)    # pop then push: ONLY when you already know x belongs in
```

On `h = [3, 5]` with `x = 1`: `heappushpop` returns `1` and leaves `[3, 5]`, because 1 is no better than anything kept. `heapreplace` returns `3` and leaves `[1, 5]`: it threw out a survivor to keep the worse item.

> ⚠️ `heapreplace` on a size-k heap silently drops the wrong element unless you've already checked that `x` beats `h[0]`. `heappushpop` is the one that matches the pattern above.

### The rank sentence

This is the step that blocks people, and it blocks them on a wrong premise: *"I have the k largest, so now I need the biggest one of them, and a min-heap can't find its maximum in less than O(k)."* The premise about the heap is right (§Partial order is the entire trade): nothing but the root is located. The premise about what you want is not.

Lay the survivors out by rank. Run the loop on `[4, 8, 1, 6, 3]` with k = 2, and the heap ends holding 6 and 8:

| Survivor | Its rank in the whole input | Where it is in the heap |
|---|---|---|
| 8 | 1st largest | the **biggest** member |
| 6 | 2nd largest, which is the kth | the **smallest** member: the root |

Within the top k, **rank 1 is the biggest and rank k is the smallest.**

> ⭐ **The kth largest is the WEAKEST member of the top k.**
>
> ⭐ **The kth smallest is the STRONGEST member of the bottom k.**

And the mirror, in full; the two directions are the same machine reflected:

| | keeping the k **largest** | keeping the k **smallest** |
|---|---|---|
| The heap holds | the k **largest** seen so far | the k **smallest** seen so far |
| So it must be a … | **min**-heap | **max**-heap: push `-x`, or a wrapper |
| On overflow you evict | the **smallest** survivor: it can't be in the top k | the **largest** survivor: it can't be in the bottom k |
| The root is | the weakest of the top k | the strongest of the bottom k |
| Cost | O(n log k) time, O(k) space | the same |

> ⭐ **The consistency check that catches a wrong-direction heap at once: the element you evict and anything you read about the boundary of the top k are the same slot, the root.** If your loop ever needs a scan of the heap, its eviction needed one too, and the loop is secretly O(nk). A correct top-k loop never looks at anything except the root.

**Why eviction is always safe, stated once:** if an element is the smallest of k + 1 candidates for the top k, there are already k items beating it, so it can't be in the final answer. Nothing arriving later can help it, because later items only add competitors. That is the whole correctness argument.

**The direction, chosen without thinking:** *what sits at the root is what you throw away.* Keeping the largest means throwing away the smallest, so a min-heap. Keeping the smallest means throwing away the largest, so a max-heap.

## Choosing among the four answers

> **"O(n log k) time because the loop runs n times and each push-and-pop costs log of the heap's size, and the heap never holds more than k."**

That is the sentence, and the load-bearing clause is the last one. **A heap operation costs log of the number of items in the heap, not in the input.** The size-k heap is the whole reason this beats sorting.

| | Time | Extra space | Ordered? |
|---|---|---|---|
| `sorted(xs)[-k:]` | O(n log n) | O(n) | yes |
| **a size-k heap** | **O(n log k)** | **O(k)** | no |
| `heapify`, then k pops | O(n + k log n) | O(1) if in place, else O(n) | yes, as you pop |
| **quickselect** | **O(n) average**, O(n²) worst | O(1) in place | no |

**With n = 10⁶ and k = 10:** log₂ n ≈ 19.9 and log₂ k ≈ 3.3. A factor of six on time, and, far more important, **O(k) space instead of O(n)**, which is what lets the size-k heap run on a stream that never fits in memory. Say the space line; it is the stronger half of the argument.

**Heapify and k pops is a real third option, and it wins when k is large.** O(n + k log n) beats O(n log k) as k approaches n: at k = n both are O(n log n), but you skipped the n pushes. Reach for it when you have the whole array in hand and k isn't small.

### The log k does not come from stopping early

This is the wrong explanation, and it is the one that gets challenged:

> *"It's n log k instead of n log n because we stop sorting once we reach the kth value."* (wrong)

**Nothing stops early.** The size-k heap reads **every one of the n elements**. It never skips one, and it can't, because the last element it reads might be the largest. There is no early exit anywhere in the loop.

> **The log k comes from the heap being SMALL, not from the loop being SHORT.** The loop still runs n times. What changed is the **price of each step**: a heap operation costs log of *the heap's* size, and you evict on every overflow, so the heap never exceeds k. That is n steps at log k each.

**And sorting can't stop early**, which is the deeper point. A comparison sort doesn't know the kth largest is settled until the whole array is settled. Heapify and k pops *is* the "stop early" idea done correctly, and look at what it still costs: the n is there, as an O(n) build.

### Quicksort vs quickselect: the name carries the complexity

| | Recurses into | Cost | Produces |
|---|---|---|---|
| **quicksort** | **both** sides | O(n log n) average, O(n²) worst | the whole array, sorted |
| **quickselect** | **one** side only | **O(n) average**, O(n²) worst | the kth element in place, with the k smallest, unordered, before it |

**Quicksort is not linear and never was.** The linear one is quickselect, and the only structural difference is the one-sided recursion: n + n/2 + n/4 + … ≤ 2n, against quicksort's n per level across log n levels (§One side only).

> ⭐ **In a room, say the whole thing: "quickselect, O(n) average, O(n²) worst, and I'd take a random pivot so the worst case needs bad luck rather than bad input."** Average *and* worst, every time.

### The four answers, with the arithmetic

One question, *k largest, k smallest, k closest, k most frequent, kth largest*, and four answers, each best somewhere:

| | Time | Extra space | Output ordered? | Works on a stream? | Mutates the input? |
|---|---|---|---|---|---|
| `sorted(xs)[-k:]` | O(n log n) | O(n) | yes | no | no |
| **a size-k heap** | **O(n log k)** | **O(k)** | no | **yes** | no |
| `heapify`, then k pops | **O(n + k log n)** | O(1) extra if in place | yes, as you pop | no | yes |
| **quickselect** | **O(n) average**, O(n²) worst | **O(1)** in place | no | no | yes |

**The order of magnitude in comparisons, n = 10⁶**, counting n log₂ n for the sort, n log₂ k for the size-k heap, n + k log₂ n for heapify and pops, and 2n for quickselect:

| | k = 10 | k = 1,000 | k = 500,000 |
|---|---|---|---|
| sort | 2.0·10⁷ | 2.0·10⁷ | 2.0·10⁷ |
| a size-k heap | 3.3·10⁶ | 1.0·10⁷ | 1.9·10⁷ |
| `heapify`, then k pops | **1.0·10⁶** | **1.0·10⁶** | 1.1·10⁷ |
| quickselect | 2.0·10⁶ | 2.0·10⁶ | **2.0·10⁶** |

**Three things to read off that grid:**

1. **Sorting is never the winner.** It is the fallback that is always acceptable and never optimal. Naming it first and then improving on it is a good answer; naming it *only* is not.
2. **The size-k heap's advantage collapses as k grows.** At k = n/2, log k is within 1 of log n, and you're doing sorting's work with extra steps. Its real claim is the **space column and the stream column**, not the time column.
3. **Quickselect is flat in k.** It is the only row that doesn't care what k is, which is why it wins outright at the large-k end.

> ⚠️ **Heapify and k pops is the row people forget.** On a fixed in-memory array it matches or beats the size-k heap at every k in that grid: O(n) to build, plus k cheap extractions. It loses only where it can't run: a stream, or an input you aren't allowed to destroy.

### Choosing, in one pass

Ask these in order and stop at the first yes:

| Question | If yes |
|---|---|
| Do the items **arrive over time**, or is n too large to hold? | **a size-k heap.** Nothing else runs |
| Are you forbidden to **mutate** the input, with no budget for a copy? | **a size-k heap**: the only O(k)-space option |
| Is the sort key a **bounded integer**, such as a count, an age or a score out of 100? | **bucket or counting sort, O(n)** (§The O(n) answer: bucket sort by count). It beats all four rows above |
| The whole array in hand, k **small**, and you want it simple? | heapify and k pops, or `nsmallest` |
| The whole array in hand, k **large or unknown**, and they asked for optimal? | **quickselect**: O(n) average |
| Do you need the answer **in order**? | any of them, **plus O(k log k)** to sort k items at the end. Say the extra term |

### Why selection can be linear when sorting can't

This is the follow-up that separates people, and it is short.

> **Any comparison sort needs Ω(n log n) comparisons in the worst case.** Each comparison has two outcomes, so c comparisons can tell apart at most 2^c inputs. A sort must tell apart all n! orderings of its input, because each needs a different rearrangement, so 2^c ≥ n! and c ≥ log₂(n!). And log₂(n!) ≥ (n/2) log₂(n/2), because n! has n/2 factors that are each at least n/2. That is Ω(n log n): **a lower bound on the problem**, not a weakness of a particular algorithm.
>
> **Selection is a different problem with a weaker requirement.** "Which k are the largest" asks for a **set**, not an arrangement. There are C(n, k) possible sets, and C(n, k) ≤ 2ⁿ, so the same counting argument only demands log₂ C(n, k) ≤ n comparisons. The n log n bound doesn't apply, and quickselect's O(n) violates nothing.

The bound is close to n log₂ n even at small n:

| n | log₂(n!) | n log₂ n |
|---|---|---|
| 10 | 21.8 | 33.2 |
| 100 | 524.8 | 664.4 |
| 10⁶ | 1.849·10⁷ | 1.993·10⁷ |

**And the floor under selection is Ω(n):** any correct algorithm must read every item, because an item it never read could be the largest. Quickselect meets that floor on average.

Two corollaries worth carrying:

- **The heap does the same thing partially.** It refuses to order the k items it holds, which is exactly the work it declines to pay for (§Partial order is the entire trade).
- **Counting sort escapes the bound a second way, by not comparing at all.** It uses the key as a list index. The Ω(n log n) bound is about *comparison* sorts and says nothing about algorithms that do arithmetic on keys. That is the whole licence for §The O(n) answer: bucket sort by count.

### The degenerate ends, which are also the test cases

| | What happens | Watch for |
|---|---|---|
| **k = 1** | every method degenerates to `max()`: O(n), no structure needed | quickselect's n + n/2 + … is doing real work for nothing |
| **k = n** | the answer is the whole input; a size-k heap is now O(n log n), a sort | a heap that never evicts is a slow list |
| **k > n** | usually "return everything"; decide it explicitly rather than letting `len(h) > k` decide for you | an eviction guard that never fires |
| **an already sorted input** | free for the heap, and **the worst case for a fixed-pivot quickselect**: O(n²) | this is what makes the random pivot non-optional |

### The space sentence, in this topic's nouns

> **"O(k) space, because the only thing I allocate is the heap, and I cap it at k."**

⚠️ If you `heapify` the input in place, that is O(1) **extra**, and you've destroyed the caller's list: say which you did. And if you built a `Counter` first, the space is O(u) for u distinct values **plus** O(k) for the heap; the `Counter` usually dominates, and it is the one people forget to count.

## Top-K with a tie-break that runs the wrong way

This section works one problem whose tie-break defeats the plain size-k heap. It is the case §A tie-break that runs the wrong way warned about, written out.

### Worked: Top K Frequent Words (LC 692)

> Given `words` and `k`, return the k most frequent words. **Ties are broken alphabetically.** The answer is sorted by frequency, highest first, then alphabetically.

**The state, before any code:**

- **The heap holds `(count, word)` tuples**, not words: you order by count and you need the word back.
- **At the top of every iteration** it holds **at most k entries, and they are the k best of everything seen so far**; its root is the weakest of them.
- **When it returns**, it holds exactly k entries, and every discarded word was beaten by all k.

The first line already contains the decision. A heap of bare counts can't answer *"which word?"*: that is [bug-checklist.md](../reference/bug-checklist.md#a-structure-that-cant-express-the-answer), §A structure that can't express the answer.

**The first attempt, and why it's wrong:**

```python
from collections import Counter
import heapq

def top_k_words_wrong(words, k):
    cnt = Counter(words)
    h = []
    for w, c in cnt.items():
        heapq.heappush(h, (c, w))
        if len(h) > k:
            heapq.heappop(h)               # evict the smallest (count, word)
    return [w for c, w in sorted(h, reverse=True)]
```

The count half is right. **The tie-break is backwards.** Trace it on `words = ["a", "a", "b", "b", "c"]`, `k = 1`. The counts are `a: 2, b: 2, c: 1`.

| push | heap after the push | evicted |
|---|---|---|
| `(2, 'a')` | `[(2, 'a')]` | nothing |
| `(2, 'b')` | `[(2, 'a'), (2, 'b')]`, size 2 > 1 | `(2, 'a')`: **the minimum, because `'a' < 'b'`** |
| `(1, 'c')` | `[(1, 'c'), (2, 'b')]`, size 2 > 1 | `(1, 'c')` |

It returns `['b']`. **The answer is `['a']`**: the same count, and `'a'` comes first alphabetically.

> ⭐ **The diagnosis, and it generalises past this problem:** the size-k heap evicts its **minimum**, so *the heap's order must be the reverse of the answer's order*. A count reverses under negation. **A string doesn't.** No tuple of `(number, str)` is descending in both fields.

**Fix A, the one to write in a room.** Say the constraint, then use the built-in:

```python
def top_k_words(words, k):
    cnt = Counter(words)
    return heapq.nsmallest(k, cnt, key=lambda w: (-cnt[w], w))
```

`nsmallest` with a `key` runs the size-k heap internally, takes the composite key, and **returns the k in sorted order**, which this problem also wants. On the trace input it returns `['a']`.

**Fix B, the mechanism, if you're asked for it.** A wrapper that defines the comparison you want:

```python
class Weakest:                                    # "smallest" means first to be evicted
    def __init__(self, word, count):
        self.word, self.count = word, count
    def __lt__(self, other):                      # heapq only ever calls __lt__
        if self.count != other.count:
            return self.count < other.count       # a lower count is weaker
        return self.word > other.word             # the SAME count: later alphabetically is weaker

def top_k_words_b(words, k):
    cnt = Counter(words)
    h = []
    for w, c in cnt.items():
        heapq.heappush(h, Weakest(w, c))
        if len(h) > k:
            heapq.heappop(h)                      # evicts the weakest, by the rule above
    return [e.word for e in sorted(h, reverse=True)]
```

On the trace input, the second push makes `Weakest('b', 2)` the root, because `'b' > 'a'`, so `'b'` is evicted and the function returns `['a']`. **One method is enough**: `heapq` never calls `__gt__` or `__eq__`, and `sorted` only calls `__lt__` too.

**Complexity, out loud:**

> **"O(n + u log k) time: the `Counter` is one pass over the n words, then the u distinct words each do a push and a pop on a heap capped at k, and each of those is log k, not log u.**
> **O(u) space, because the `Counter` holds one entry per distinct word and the heap holds k, and the `Counter` dominates."**

⚠️ **The `Counter` is the space, not the heap.** "O(k) space, the heap is capped" is the heap's space, not the algorithm's. Name everything you allocated, then say which dominates.

**The shapes one delta away:**

| Problem shape | The delta |
|---|---|
| a tie-break the problem leaves open | ask first; whether field 1 is ever compared decides whether it needs to be comparable |
| a stream of words | the counts change as words arrive, so the heap's entries go stale: §Lazy deletion |

## The O(n) answer: bucket sort by count

The heap gives O(n log k). There is a **linear** answer whenever the thing you sort by is a **bounded integer**, and a *count* always is.

> **A count of items drawn from a list of length n is an integer in `[0, n]`. There are only n + 1 possible counts. So you don't have to sort them: you can index by them.**

### Worked: Sort Characters By Frequency (LC 451)

> Sort a string so that the characters appearing most often come first; equal characters stay together.

That is counting sort, and it is the whole trick:

```python
from collections import Counter

def frequency_sort(s):
    cnt = Counter(s)

    buckets = [[] for _ in range(len(s) + 1)]     # buckets[c]: every char seen exactly c times
    for ch, c in cnt.items():
        buckets[c].append(ch)

    out = []
    for c in range(len(s), 0, -1):                # walk DOWN: most frequent first
        for ch in buckets[c]:
            out.append(ch * c)
    return "".join(out)
```

`frequency_sort("tree")` is `"eetr"`, `frequency_sort("cccaaa")` is `"cccaaa"`, and `frequency_sort("Aabb")` is `"bbAa"`.

**The three things to get right:**

1. **The bucket list is indexed by COUNT, not by item.** `buckets[3]` is *"everything that appeared 3 times"*. The value becomes the index: [bug-checklist.md](../reference/bug-checklist.md#index-vs-value), §Index vs value, used on purpose.
2. **Length `n + 1`, not `n`.** One character repeated n times has count n, and `buckets[n]` must exist. Derive it: the largest index you need is n, so the length is n + 1 ([bug-checklist.md](../reference/bug-checklist.md#off-by-ones-derive-never-freehand), §Off-by-ones: derive, never freehand).
3. **Walk down from n, and stop at 1.** `buckets[0]` is always empty, because nothing in the `Counter` appears zero times.

**Why it's O(n), stated properly:**

> **"O(n) time, because the `Counter` is one pass, filling the buckets is one pass over the distinct items, and the final walk visits n + 1 buckets and touches each item once, so it is O(n + n) and not O(n log n). There is no comparison anywhere in the algorithm.**
> **O(n) space, because I allocate n + 1 buckets plus the `Counter`."**

**The last clause of the time sentence earns the point.** Ω(n log n) is a lower bound on *comparison* sorts; bucket sort escapes it by never comparing two elements (§Why selection can be linear when sorting can't).

⚠️ **The honest trade:** it spends O(n) space on a mostly empty list to save a log factor. **On a top-k problem the heap is O(k) space and this is O(n).** If the interviewer says "the input doesn't fit in memory", bucket sort is the wrong answer and the size-k heap is the right one.

**When it applies, in one test:**

> **Is the sort key a bounded integer with a range comparable to n?**

Counts, ages, scores out of 100 and grid coordinates pass. **Distances** fail, because they are floats with no bound, and so do **arbitrary values**: keys in `[1, 10⁹]` need 10⁹ buckets.

## Quickselect

### One signal, four answers

> **"k largest", "k smallest", "k closest", "k most frequent", "kth largest": these are ONE problem.**

They differ only in what the key is. When you hear any of them, what is scored is not which answer you pick but **whether you know all of them and can say why**:

| | Time | Extra space | Ordered? | Reach for it when |
|---|---|---|---|---|
| **sort** | O(n log n) | O(n) | yes | k is close to n, the output must be ordered anyway, or you want the shortest correct code |
| **a size-k heap** | **O(n log k)** | **O(k)** | no | k is much smaller than n, the input is a **stream**, or you want **no bad case** |
| **bucket or counting** | **O(n)** | O(n) | no | the key is a **bounded integer** (§The O(n) answer: bucket sort by count) |
| **quickselect** | **O(n) average**, **O(n²) worst** | **O(1)** in place | no | the **optimum** matters, the whole array is in hand, and you may mutate it |

**Four sentences that turn the table into speech:**

1. **"Of the comparison methods, only quickselect is linear."** That is the whole argument for it, and it is why it is the expected answer to *"can you do better than n log n?"*
2. **"But the heap wins on space and has no adversarial input."** O(k) against O(n), and O(n log k) is a *guarantee* where quickselect's O(n) is an average.
3. **"Quickselect needs the whole array, and mutates it."** It can't run on a stream. If the input arrives over time, the heap is the only one of the four that works.
4. ⭐ **"I'd write the heap unless you want the optimal average, and then I'd write quickselect."** That names the trade and picks a side.

> ⚠️ **Say average and worst every time.** *"O(n) average, O(n²) worst, and the worst case is a real input: sorted data with a fixed last-element pivot hits it every time."* O(n) alone invites *"and the worst case?"*

### One side only

**The partition is identical to quicksort's.** The difference is what you do afterwards:

```
QUICKSORT                                  QUICKSELECT
partition                                  partition
  ↓                                          ↓
recurse LEFT and recurse RIGHT             recurse into the ONE side that holds k
```

**And that single change turns n log n into n:**

```
QUICKSORT    every level touches all n elements, and there are log n levels
             n + n + n + … + n   (log n terms)        =  n log n

QUICKSELECT  each level touches only the surviving half
             n + n/2 + n/4 + n/8 + …                  ≤  2n  =  O(n)
```

> **The geometric series is the proof, and it is short enough to say: "each level is half the size of the one above, and n + n/2 + n/4 + … is at most 2n, so the total work is linear. The recursion adds a constant factor, not a log factor."**

**Two consequences to have ready:**

- **The average is O(n) because a random pivot splits *well enough*.** It doesn't need to split evenly: any split that keeps at most a constant fraction c < 1 gives a geometric series n + cn + c²n + … = n / (1 − c). Even a 90/10 split, kept on the 90 side every time, gives n / 0.1 = 10n.
- **The worst case is O(n²)**, because a pivot that peels off one element gives n + (n − 1) + … + 1 = n(n + 1)/2. That is **exactly what a last-element pivot does to a sorted array**, and sorted arrays are a common test.

### The allocating version

This is the version to write first, on a plain list of numbers:

```python
def k_smallest(a, k):                    # the k smallest of a, unordered
    if k <= 0:        return []
    if len(a) <= k:   return a           # the base case, and it must come before the split

    pivot, rest = a[-1], a[:-1]          # ⭐ the pivot is held OUT: every branch is smaller
    small = [x for x in rest if x <  pivot]
    large = [x for x in rest if x >= pivot]

    if len(small) == k: return small                    # an exact hit
    if len(small) >  k: return k_smallest(small, k)     # ⭐ the answer is a SUBSET: do not prepend
    return small + [pivot] + k_smallest(large, k - len(small) - 1)
```

`k_smallest([7, 2, 9, 4, 1, 8], 3)` returns `[1, 2, 4]`. `k_smallest([5, 5, 5, 5], 2)` returns `[5, 5]`, and `k = 0` returns `[]`.

**It is a genuine quickselect.** It recurses into one side only, and it is O(n) average. The last line counts the pivot: `small` and the pivot are all in, so `k - len(small) - 1` are still owed from `large`.

### The two classic bugs

Both are one line away from the version above, and each starred line is the fix for one of them.

**(a) The pivot left inside the branch, so the input never shrinks.** Write the split as `small = [x for x in a if x < pivot]` and `large = [x for x in a if x >= pivot]`, with the pivot still in `a`, so it is counted inside `large` and the last line becomes `return small + k_smallest(large, k - len(small))`. On `[3, 2, 1]` with k = 1, the pivot is 1, `small` is `[]` and `large` is `[3, 2, 1]`: the call is `k_smallest([3, 2, 1], 1)` again, and it never ends. **The fix:** `pivot, rest = a[-1], a[:-1]`. `rest` is one shorter, and `small` and `large` are subsets of it, so **every recursive call gets a strictly smaller list.**

**(b) Returning a superset.** Write the middle branch as `return small + k_smallest(small, k)`. On `[7, 2, 9, 4, 1, 8]` with k = 1, the pivot is 8 and `small` is `[7, 2, 4, 1]`, four items for a k of 1; the recursion correctly finds `[1]`, and the prepend turns the answer into `[7, 2, 4, 1, 1]`. **The fix:** when `len(small) > k`, the answer lies entirely inside `small`, so return `k_smallest(small, k)` alone. Prepend `small` only in the branch where *all* of it survives.

### Why the allocating version is not space-optimal

Say this before you're asked:

> **"O(n) extra space, not O(1), because I allocate `small` and `large` at every level and rebuild the answer by concatenation on the way back out."**

Be precise about *why* it is O(n):

- The allocations total n + n/2 + n/4 + … ≤ 2n on average, which is O(n) of allocation.
- The **peak live** memory is also O(n): a parent's `small` and `large` stay alive while the child runs, so the frames stack up to n + n/2 + n/4 + … = O(n).
- The **call stack** is only O(log n) on average. **The lists cost you**, not the recursion.
- `small + [pivot] + k_smallest(...)` builds a new list at every level on the way out.

**None of that makes it wrong.** It makes it *"O(n) average time, O(n) extra space, and the in-place version is O(1)"*, which is a complete and honest answer.

### In place, and where the O(1) comes from

```python
import random

def partition(a, lo, hi):
    """Lomuto. Returns p, and a[p] is in its FINAL sorted position."""
    r = random.randint(lo, hi)
    a[r], a[hi] = a[hi], a[r]              # ⭐ a random pivot, parked at the end, held OUT of the scan
    pivot = a[hi]
    i = lo                                  # invariant: a[lo:i] < pivot, a[i:j] >= pivot
    for j in range(lo, hi):
        if a[j] < pivot:
            a[i], a[j] = a[j], a[i]
            i += 1
    a[i], a[hi] = a[hi], a[i]              # the pivot lands at i, its final position
    return i

def quickselect(a, k):
    """a[k] becomes the kth smallest, 0-indexed, and a[:k] the k smallest."""
    lo, hi = 0, len(a) - 1
    while lo < hi:                          # ⭐ the tail recursion, unrolled
        p = partition(a, lo, hi)
        if   p == k: break
        elif p <  k: lo = p + 1             # ⭐ p is EXCLUDED: the range shrinks every time
        else:        hi = p - 1
    return a[k]
```

`quickselect([7, 2, 9, 4, 1, 8], 2)` returns `4`, the third smallest, whatever pivots the random draws pick.

**Two points carry the section.**

**1. The invariant: after a partition, `a[p]` is in its final sorted position.** Everything before `p` is smaller, everything after is at least as large, **and no later partition moves it**, because every later call works strictly on one side of it. That is what makes `p == k` a *stop*, not a step: the element you were asked for is already where it belongs, and `a[:k]` is the answer as a set.

> **Read the invariant as the loop's exit condition and the algorithm reads itself:** *"partition puts one element home; if home is `k`, I'm done; otherwise the answer is on the side that holds `k`."*

**2. It recurses one way only, so it is tail-recursive, so the call stack disappears.** Here is the same algorithm written recursively:

```python
def select_rec(a, lo, hi, k):          # afterwards, a[k] is the kth smallest
    if lo >= hi:
        return
    p = partition(a, lo, hi)
    if p == k:
        return
    if p < k:
        select_rec(a, p + 1, hi, k)    # the LAST thing this call does
    else:
        select_rec(a, lo, p - 1, k)    # the LAST thing this call does
```

**A recursive call in the last position has nothing to come back for**, so its frame is dead weight: replace it by reassigning `lo` or `hi` and looping. That is the `while` loop in `quickselect`, and it is where **O(1) extra space** comes from: no lists, no frames, just `lo`, `hi` and `p`.

> ⭐ **This is exactly what quicksort can't do.** Quicksort makes *two* calls, and the first has to return before the second can start, so at least one of them is a real recursion. **One-sided recursion is the property that both the O(n) and the O(1) fall out of.**

**Everything above finds the kth smallest, 0-indexed.** A problem may ask for the kth largest, or count from 1. Derive the index yourself, and check it on k = 1 and k = n before you trust it ([bug-checklist.md](../reference/bug-checklist.md#off-by-ones-derive-never-freehand), §Off-by-ones: derive, never freehand).

### The ways it breaks

| Failure | What it looks like | The fix |
|---|---|---|
| **A branch that is not strictly smaller** | a hang, or `RecursionError`. §The two classic bugs, (a): `[3, 2, 1]` with k = 1 recurses on a list that still holds the pivot | ⭐ **Hold the pivot OUT.** `rest = a[:-1]` in the allocating form; `lo = p + 1` and `hi = p - 1`, never `p`, in place. **Check that every branch is strictly smaller than its input before you write the recursive call** |
| **Returning a superset** | more than k items out. §The two classic bugs, (b): `small + k_smallest(small, k)` | **If `small` is too big, the whole answer is inside it**: return `k_smallest(small, k)` alone |
| **O(n²) on sorted input** | a TLE on a large sorted test. `a[-1]` on `[1, 2, …, n]` peels off one element per level | ⭐ **A random pivot.** `random.randint(lo, hi)`, swapped to the end. One line, and it turns a guaranteed worst case into a vanishingly unlikely one |

### Duplicates: the three-way partition

A **two-way** partition sends every element equal to the pivot to one side. On `[5, 5, 5, 5, 5, 5, 5, 5]` that is the peel-one-element case again, and a random pivot **doesn't help**, because every pivot is the same value. With k = 7, the two-way loop partitions ranges of 8, 7, …, 2 and makes 7 + 6 + … + 1 = 28 comparisons, which is n(n − 1)/2.

**The robust form is a three-way partition**, the Dutch national flag: `< pivot`, `== pivot`, `> pivot`.

```python
def quickselect3(a, k):
    lo, hi = 0, len(a) - 1
    while True:
        if lo == hi: return a[lo]
        pivot = a[random.randint(lo, hi)]
        lt, i, gt = lo, lo, hi                    # a[lo:lt] < p, a[lt:i] == p, a[gt+1:hi+1] > p
        while i <= gt:
            if   a[i] < pivot: a[lt], a[i] = a[i], a[lt]; lt += 1; i += 1
            elif a[i] > pivot: a[gt], a[i] = a[i], a[gt]; gt -= 1
            else:              i += 1
        if   k < lt: hi = lt - 1
        elif k > gt: lo = gt + 1
        else:        return a[k]                  # k is inside the equal band: done
```

**Why it terminates even on all-equal input:** the `==` band is excluded from *both* branches, and it always holds at least the pivot, so every branch is strictly smaller. On `[5] * 8` the first pass puts everything in the band, 8 steps of the inner loop, and it returns `5` at once: **O(n), from what was the two-way version's worst case.**

### What to say in a room

> **Write the allocating version.** It is far easier to get right with no IDE, list comprehensions instead of two cursors and three swaps, and a correct O(n)-space quickselect beats a buggy O(1)-space one.
>
> **Then say the sentence, unprompted:** *"This is O(n) average, O(n²) worst. I've written the allocating form for clarity, which is O(n) extra space. In place with a random pivot it's O(1) extra space, and because it only recurses one way it's tail-recursive, so it becomes a while loop and the stack goes away too."*

**That gets you credit for knowing the in-place form without the risk of writing it.** If the interviewer says *"go on, write it in place"*, §Every template, in one place, row 12 is the template, and you have just said what you're about to do.

⚠️ **One more line to have ready, because it is the standard follow-up:** *"a median-of-medians pivot makes the worst case O(n) deterministically, but its constant is bad enough that randomised quickselect beats it in practice; I'd mention it and not write it."*

## k-way merge

This section uses *merge k sorted arrays into one sorted array*, the plain version of the shape.

The linked-list version is row 7 of the drill set, and the two-list version is [05-linked-lists.md](05-linked-lists.md#merging-two-sorted-lists), §Merging two sorted lists: with two lists you compare two fronts, and with k lists that comparison becomes a heap.

### The reasoning, from the one question

You have k sorted lists. **The smallest element overall is the front of one of them**; you just don't know which. That is *"what is the smallest thing right now"*, asked n times, which is a heap by definition.

**And the heap holds one entry per list, not one per element.** That is the whole design decision:

```python
import heapq

def merge_k(lists):
    h = [(lst[0], i, 0) for i, lst in enumerate(lists) if lst]   # (value, which list, which index)
    heapq.heapify(h)                                              # O(k)

    out = []
    while h:
        val, i, j = heapq.heappop(h)
        out.append(val)
        if j + 1 < len(lists[i]):                                 # ⚠️ the guard: is there a successor?
            heapq.heappush(h, (lists[i][j + 1], i, j + 1))
    return out
```

`merge_k([[1, 4, 7], [2, 5], [3, 6, 9]])` returns `[1, 2, 3, 4, 5, 6, 7, 9]`. `merge_k([[], [1], []])` returns `[1]`, and `merge_k([])` returns `[]`.

### The state, and it is the whole algorithm

- **The heap holds `(value, list index, position)` triples**, **one per list** that isn't exhausted, never more.
- **At the top of every iteration**, the heap holds the current **front** of every list that isn't exhausted, so **its root is the smallest of everything not yet emitted**.
- **When it returns**, `out` holds every element, in order, and the heap is empty because every list ran out.

> ⭐ **"One entry per list" is the sentence.** The naive version pushes all n elements and is O(n log n): correct, and it throws away the sortedness you were given. **O(n log k) is the point of the problem**, and the difference is one design choice about what goes in the heap.

**This is the payload rule in its purest form** (§What you push: (priority, payload)): push bare values and you pop the smallest without knowing *which list to advance*. The payload is how the loop makes progress. And the list index `i` is a tie-breaker that can never tie, because only one entry per list is in the heap at a time.

### Complexity

> **"O(n log k) time, because each of the n elements is pushed once and popped once, and the heap never holds more than k entries, one per list, so each operation is log k.**
> **O(k) extra space for the heap; the output is O(n), but that is the answer, not working memory."**

⚠️ **`heapify` on the k initial fronts is O(k)**, not O(k log k). It is free, and worth saying.

### The shapes one delta away

| Problem | The delta |
|---|---|
| Merge k sorted **linked lists** | row 7 of the drill set. Work out what the payload is, what replaces `j + 1`, and the answer to question 3 of the three-line question |
| The **smallest range** covering an element from each list | the same heap; also track the largest of the current fronts |
| The **kth smallest in a sorted matrix** | each row is a sorted list. Merge the rows and stop after k pops: O(k log rows) |
| Merge k sorted **streams** | identical. This is the shape that makes external merge sort possible |

## Two heaps

### The balanced partition

> **You need to know something about the MIDDLE of a collection that keeps growing.**

One heap gives you one end. The median is at neither end, so **cut the collection in half and put a heap on each side of the cut, facing inward.** Then both halves' inner edges are roots, and the median is one or two O(1) reads.

```
        lower half                    upper half
   [ … 1, 3, 4, 6 ]              [ 8, 9, 11, 15 … ]
                  ↑ MAX-heap      ↑ MIN-heap
                  root            root
                  └──── the median lives here ────┘
```

**For this pattern the state sentence is the algorithm.** Write it and the code is transcription; skip it and there is nothing to write.

1. **`lower` is a MAX-heap**, of negated numbers, holding the smaller half. **`upper` is a MIN-heap** holding the larger half.
2. **Two invariants, both true between operations:**
   - **Order:** every element of `lower` is ≤ every element of `upper`. The version you can check in O(1): **`-lower[0] <= upper[0]`**, whenever both are non-empty.
   - **Size:** the two lengths are equal, or one side holds exactly one more. *Pick which side gets the extra, and never change your mind.*
3. **On return:** the median reads off the roots, and the formula depends on the side you picked in line 2. Derive it from that choice, for an even count and an odd count.

> ⚠️ **Fixing which side holds the odd element is a decision, and it must happen before line one.** Both choices work, and they give **different median formulas**. Choosing halfway through is how this problem produces an answer that is right on even-length input and wrong on odd.

### The rebalance has no cases

The tempting insert is *"compare the new number to the roots and decide which heap it goes in"*: a branch, then another branch for the sizes, and now there are four cases and two of them are subtle.

**There is a version with no case analysis**: a fixed sequence of pushes and pops that runs on every insert, whatever the new number is, followed by one `if`. The fixed sequence repairs the order invariant without comparing the new number to anything; the `if` restores the size invariant. Finding that sequence is the work of row 8 of the drill set.

> ⭐ **The move that generalises: when a branch has four cases and two of them are subtle, look for a sequence of unconditional operations that lands in the same place.** It is the same instinct as [08-graphs.md](08-graphs.md#multi-source-bfs), §Multi-source BFS: replace *"which one?"* with *"always the same steps"*.

**Complexity:** *"O(log n) per insert, because each one does a constant number of heap operations, and O(1) per median query, because both middle values are roots. O(n) space: every element is stored once, in one of the two heaps."*

**The code is deliberately not here.** [Find Median from Data Stream](https://leetcode.com/problems/find-median-from-data-stream/) (LC 295) is row 8 of the drill set, and its state sentence is above.

### Worked: IPO (LC 502)

Not every two-heap problem is a balanced partition. This is the other family, two structures with different *jobs*, and it is worth one read because it looks nothing like the median.

> You can do at most `k` projects. Project `i` needs `capital[i]` to start and pays `profits[i]`, which is added to your capital. Starting from capital `w`, maximise the final capital.

```python
import heapq

def find_maximized_capital(k, w, profits, capital):
    projects = sorted(zip(capital, profits))       # by capital, ascending
    available = []                                  # a MAX-heap of profits, by negation
    i = 0
    for _ in range(k):
        while i < len(projects) and projects[i][0] <= w:
            heapq.heappush(available, -projects[i][1])   # everything you can now afford
            i += 1
        if not available:                           # ⚠️ the necessary guard: nothing affordable
            break
        w -= heapq.heappop(available)               # take the most profitable: -= a negative
    return w
```

`find_maximized_capital(2, 0, [1, 2, 3], [0, 1, 1])` returns `4`: the only affordable project pays 1, and then the best of the two that cost 1 pays 3. With k = 3 and capitals `[0, 1, 2]` it returns `6`, and `find_maximized_capital(1, 0, [5], [1])` returns `0`, through the guard.

**The two structures have different roles, and that is the pattern:** a list sorted by **eligibility** (can you afford it yet?) and a heap ordered by **desirability** (which of the eligible ones is best?). The `while` moves items from one to the other as the threshold rises, and **`i` never resets**: every project is admitted once, which keeps it O(n log n) rather than O(kn).

> ⭐ **The signal for this shape: two different orderings matter, and one of them is a moving threshold.** Sort by the threshold, heap by the objective. It is the same skeleton as a sweep line.

⚠️ `if not available: break` is the **necessary** guard: popping an empty heap is an `IndexError`, and it happens whenever every remaining project costs more than you have ([bug-checklist.md](../reference/bug-checklist.md#the-guard-asymmetry), §The guard asymmetry).

## What a heap can't do

### When a heap is the wrong tool

Read this off the last two columns of the table in §The three structures, side by side. **A heap answers one question. If your problem asks a second one, the heap is not the structure.**

| What you need | Heap? | Reach for |
|---|---|---|
| The min (or max), repeatedly, while inserting | **yes** | the heap: this is the whole use case |
| The kth largest, **once**, with the whole array in hand | works | **quickselect**, O(n) average (§Quickselect). The heap is O(n log k) |
| Everything, in order | no | `sorted()`. n pops *is* heapsort: the same O(n log n), with worse constants and more code (§Heapsort) |
| **Delete an arbitrary element** | **can't** | O(n) just to find it. **Lazy deletion** (§Lazy deletion), or a different structure |
| **"Is x in here?"** | **can't** | a `set` alongside, or a different structure |
| **Change an item's priority** | **can't** | `heapq` has no decrease-key: push a duplicate, discard stale entries on pop (§Lazy deletion) |
| **The min AND the max** | no | two heaps, or a sorted container |
| The min or max of a **window** that slides | no | a **monotonic deque**, O(n) against the heap's O(n log n) (§A sliding window min or max) |
| The median of a stream | **two** heaps | §Two heaps: one heap is not enough, and knowing that is the problem |

> ⭐ **The discriminator, in one line: a heap knows where its minimum is and nothing else. The moment you need to say anything about a specific element, you need a second structure or a different one.**

### Lazy deletion

A heap can't find `x`, so it can't delete `x`, and `heapq` has **no decrease-key**. The universal workaround:

> **Don't delete. Mark it dead, leave it in the heap, and skip it when it reaches the root.**

Here it is on the self-contained shape, *a collection you can add to, remove from, and ask for the minimum of*:

```python
import heapq
from collections import Counter

class MinTracker:
    def __init__(self):
        self.h = []
        self.dead = Counter()          # value: how many copies have been removed

    def add(self, x):
        heapq.heappush(self.h, x)

    def remove(self, x):               # O(1): the heap isn't touched; x must be present
        self.dead[x] += 1

    def get_min(self):
        while self.h and self.dead[self.h[0]]:      # ⚠️ `self.h and` FIRST: h[0] on empty is IndexError
            self.dead[self.h[0]] -= 1
            heapq.heappop(self.h)
        return self.h[0] if self.h else None
```

Add 5, 3, 8 and 3, and `get_min()` is 3. Remove one 3 and it is still 3, because the second copy is live. Remove the other 3 and it is 5; remove 5 and it is 8; remove 8 and it is `None`.

**The three things that make it correct:**

1. **The purge loop lives where you *read*, not where you remove.** A dead entry costs nothing until it reaches the root, and if it never does, you never pay for it.
2. **A `Counter`, not a `set`.** Duplicates are real: removing one 5 must not remove all of them. The trace above is that case.
3. ⚠️ **`self.h and …` comes first in the `while`.** `self.h[0]` on an empty heap is an `IndexError`: ask what must be true for the next line to be safe ([bug-checklist.md](../reference/bug-checklist.md#the-guard-asymmetry), §The guard asymmetry).

**Complexity:** *"`add` is O(log n) and `remove` is O(1). `get_min` is O(log n) amortised: every entry is pushed once and popped at most once, so the purge work across the whole run is bounded by the number of pushes."* That is the same argument as [02-stacks-queues.md](02-stacks-queues.md#the-amortised-argument), §The amortised argument: each element enters once and leaves once, so a loop inside a loop is still linear overall.

⚠️ **The one thing to say about its space:** the heap can hold entries that are logically gone, so it is O(number of pushes), not O(current size). If removals dominate, say *"I'd rebuild when the dead fraction gets large"* rather than pretending it is free.

**The decrease-key version is the same trick:** push `(new_priority, node)` without removing the old entry, and on pop, skip any entry that is stale. **That is what Dijkstra does** ([08-graphs.md](08-graphs.md#done-is-not-a-cycle-guard), §`done` is not a cycle guard): module 08 skips a stale pop with `if done[u]: continue`, and `if d > dist[u]: continue` is the other lazy check, comparing the popped distance with the best known one.

### A sliding window min or max

*"The maximum of every window of size k"* is *"what is the biggest thing right now, repeatedly, while the collection changes"*. That reads like a heap, and a max-heap with lazy deletion does solve it, in **O(n log n)**.

**But a window changes in a special way: things leave in the order they arrived.** That extra structure buys a **monotonic deque** and **O(n)**, by the argument in [02-stacks-queues.md](02-stacks-queues.md#the-monotonic-stack), §The monotonic stack.

**Not written here.** The deque version is [Sliding Window Maximum](https://leetcode.com/problems/sliding-window-maximum/) (LC 239), a drill in module 03 ([03-two-pointers-sliding-window.md, §When the window needs its maximum](03-two-pointers-sliding-window.md#when-the-window-needs-its-maximum)); this is its signal, not its solution.

> ⭐ **What to say in a room:** *"a max-heap with lazy deletion gives O(n log n); because window elements expire in arrival order, I can use a monotonic deque instead and get O(n)."* Naming the better answer is most of the credit, even if you write the heap.

### Heapsort

`heapify`, then pop everything, is a correct O(n log n) sort. **`sorted()` is the same complexity, one line, and stable.** The only reason to say the word "heapsort" is that it explains why n pops cost n log n. **Never write it as an answer.**

---

## Every template, in one place

Thirteen templates, in this order, because each is a row above it with a single change. The skeleton is §0.5, primitive 1.

| Row | Template | The delta from the row above | Invariant | Time · space |
|---|---|---|---|---|
| 1 | the min-heap | (§0.5, primitive 1): push, pop, peek, and `heapify` for a whole list | `h[(i - 1) // 2] <= h[i]` for every `i ≥ 1`, so `h[0]` is the minimum | O(log n) push and pop, O(1) peek, O(n) `heapify` · O(n) |
| 2 | the max-heap | every value negated on the way in and on the way out | `h` holds negatives, so `-h[0]` is the maximum | as row 1 |
| 3 | `heapify`, then k pops | the whole list is in hand: build once, then pop k times | after j pops, the popped list is the j smallest, in order | O(n + k log n) · O(1) extra, and the input is destroyed |
| 4 | the size-k heap | push everything, and pop on every overflow | `h` holds the k largest seen so far, or all of them if fewer than k have been seen | O(n log k) · O(k) |
| 5 | with a payload and a tie-breaker | push `(priority, i, item)` instead of the bare item | field 1 is unique, so a comparison never reaches `item` | as row 4 |
| 6 | by frequency | a `Counter` first: frequency is the key; the item is the payload | as row 4, over the u distinct items | O(n + u log k) · O(u), and the `Counter` dominates |
| 7 | bucket by count | the bounded integer key becomes a list index, and the heap goes | `buckets[c]` holds every item seen exactly `c` times | O(n) · O(n) |
| 8 | k-way merge | the heap holds one cursor per input, not one entry per element | the root is the smallest element not yet emitted | O(n log k) · O(k) |
| 9 | two heaps | a second heap, facing the first across a cut | order: `-lower[0] <= upper[0]`; size: equal, or your chosen side one larger | O(log n) insert, O(1) median · O(n) |
| 10 | lazy deletion | removal marks; the read purges | after the purge, `h` is empty or its root is live | O(log n) amortised per read, O(1) remove · O(pushes) |
| 11 | quickselect, allocating | no heap: partition around a pivot held out, and recurse into one side | every branch is strictly smaller than its input, and the answer is a subset of the branch you recurse into | O(n) average, O(n²) worst · O(n) |
| 12 | quickselect, in place | the lists become an index range, and the recursion a loop | after a partition `a[p]` is final, and `lo ≤ k ≤ hi` always | O(n) average, O(n²) worst · O(1) |
| 13 | quickselect, three-way | the partition gains an `==` band | `a[lo:lt] < pivot`, `a[lt:gt + 1] == pivot`, `a[gt + 1:hi + 1] > pivot` | O(n) average, including all-equal input · O(1) |

> **Read it as one algorithm and twelve deltas.**

Notes on the rows:

- **Every row has a state sentence, and you say it before you write the row.** *"The heap holds ⟨values, or which tuple⟩, at the top of every iteration ⟨what is true of it⟩, and when it returns ⟨where the answer is⟩."*
- **Rows 3 to 7 and 11 to 13 all answer the one top-k question**; §Choosing among the four answers and §One signal, four answers are the decision between them.
- **Rows 11 to 13 leave the heap.** They are here because they answer the same signal, and an interviewer who hears row 4 will ask for one of them next.

**Row 1, the min-heap:**

```python
import heapq

h = []
heapq.heappush(h, x)              # O(log n)
smallest = h[0]                   # O(1), a peek with no removal: IndexError if h is empty
smallest = heapq.heappop(h)       # O(log n), removes it
heapq.heapify(lst)                # O(n), in place: lst becomes a heap
```

**Row 2, the max-heap:**

```python
heapq.heappush(h, -x)
largest = -h[0]
largest = -heapq.heappop(h)       # ⚠️ the minus on the way OUT
```

**Row 3, `heapify`, then k pops:**

```python
heapq.heapify(nums)                                   # O(n), and nums is now the heap
k_smallest = [heapq.heappop(nums) for _ in range(k)]  # O(k log n), and ORDERED
```

**Row 4, the size-k heap:**

```python
def k_largest(nums, k):
    h = []
    for x in nums:
        heapq.heappush(h, x)
        if len(h) > k:
            heapq.heappop(h)      # evict the weakest survivor
    return h                      # the k largest, UNORDERED
```

`k_largest([5, 1, 9, 3, 7], 2)` returns `[7, 9]`, the trace in §The size-k heap: why a min-heap gives the k largest.

**Row 5, with a payload and a tie-breaker:**

```python
def k_largest_by(items, k, priority):
    h = []
    for i, item in enumerate(items):
        heapq.heappush(h, (priority(item), i, item))    # i is unique, so item is never compared
        if len(h) > k:
            heapq.heappop(h)
    return [item for _, _, item in h]
```

**Row 6, by frequency,** is row 5 with a `Counter` in front of it: frequency is the key; the item is the payload. It is written out in §Top-K with a tie-break that runs the wrong way, together with the tie-break that defeats it.

**Row 7, bucket by count,** is a change to the structure: the heap goes, and a list indexed by count replaces it. It is written out in §The O(n) answer: bucket sort by count, with the three things to get right.

**Row 8, k-way merge:**

```python
def merge_k(lists):
    h = [(lst[0], i, 0) for i, lst in enumerate(lists) if lst]
    heapq.heapify(h)                                      # O(k)

    out = []
    while h:
        val, i, j = heapq.heappop(h)
        out.append(val)
        if j + 1 < len(lists[i]):                         # is there a successor?
            heapq.heappush(h, (lists[i][j + 1], i, j + 1))
    return out
```

**Row 9, two heaps,** is a change to the structure, not to the loop. The state is the template:

```python
lower, upper = [], []   # lower: a MAX-heap (negated) of the smaller half. upper: a MIN-heap of the larger half
                        # INVARIANT 1, order: -lower[0] <= upper[0], whenever both are non-empty
                        # INVARIANT 2, size:  the lengths are equal, or your chosen side holds one more
```

Every insert repairs invariant 1 first, with a fixed sequence of pushes and pops that runs whatever the new number is, and then invariant 2, with the only `if` in the method. Which steps those are is the work of row 8 of the drill set (§Two heaps).

**Row 10, lazy deletion:**

```python
from collections import Counter

class MinTracker:
    def __init__(self):
        self.h, self.dead = [], Counter()

    def add(self, x):
        heapq.heappush(self.h, x)

    def remove(self, x):                             # O(1): the heap isn't touched
        self.dead[x] += 1

    def get_min(self):
        while self.h and self.dead[self.h[0]]:       # ⚠️ `self.h and` FIRST
            self.dead[self.h[0]] -= 1
            heapq.heappop(self.h)
        return self.h[0] if self.h else None
```

**Row 11, quickselect, allocating:**

```python
def k_smallest(a, k):                    # the k smallest of a, unordered
    if k <= 0:        return []
    if len(a) <= k:   return a

    pivot, rest = a[-1], a[:-1]          # ⭐ the pivot held OUT: every branch is smaller
    small = [x for x in rest if x <  pivot]
    large = [x for x in rest if x >= pivot]

    if len(small) == k: return small
    if len(small) >  k: return k_smallest(small, k)     # ⭐ the answer is a SUBSET: do not prepend
    return small + [pivot] + k_smallest(large, k - len(small) - 1)
```

**Row 12, quickselect, in place:**

```python
import random

def partition(a, lo, hi):
    r = random.randint(lo, hi)
    a[r], a[hi] = a[hi], a[r]                       # ⭐ a random pivot, parked out of the scan
    pivot, i = a[hi], lo
    for j in range(lo, hi):
        if a[j] < pivot:
            a[i], a[j] = a[j], a[i]
            i += 1
    a[i], a[hi] = a[hi], a[i]
    return i                                        # a[i] is in its FINAL sorted position

def quickselect(a, k):                              # a[k] becomes the kth smallest, 0-indexed
    lo, hi = 0, len(a) - 1
    while lo < hi:                                  # ⭐ the tail recursion, unrolled
        p = partition(a, lo, hi)
        if   p == k: break
        elif p <  k: lo = p + 1                     # ⭐ p excluded
        else:        hi = p - 1
    return a[k]
```

**Row 13, quickselect, three-way:**

```python
def quickselect3(a, k):
    lo, hi = 0, len(a) - 1
    while True:
        if lo == hi: return a[lo]
        pivot = a[random.randint(lo, hi)]
        lt, i, gt = lo, lo, hi
        while i <= gt:
            if   a[i] < pivot: a[lt], a[i] = a[i], a[lt]; lt += 1; i += 1
            elif a[i] > pivot: a[gt], a[i] = a[i], a[gt]; gt -= 1
            else:              i += 1
        if   k < lt: hi = lt - 1                    # the == band is in NEITHER branch, so it terminates
        elif k > gt: lo = gt + 1
        else:        return a[k]
```

---

## How to attack a heap problem

1. **Name the pattern and the signal that pointed to it**, before any code. *"'k most frequent', with the whole array in hand"* is a signal, and it has more than one answer (§0.8).
2. **Name the answers and pick one, out loud.** *"Sorting is O(n log n), a size-k heap is O(n log k) time and O(k) space, quickselect is O(n) average with an O(n²) worst case. I'll write \_\_ because \_\_."* This is the sentence the topic is scored on (§Choosing among the four answers).
3. **Write the state, three lines, before any code:**
   - **The heap holds ⟨values, indices, or `(priority, payload)` tuples⟩**: say which, and what the payload is for.
   - **At the top of every iteration it is true that ⟨…⟩**, for example *"it holds at most k items, and its root is the weakest of the current top k."*
   - **When it returns, ⟨…⟩ is true**, for example *"it holds exactly k items, and every discarded item was beaten by all k."*

   For a two-heap problem, that is the algorithm: both invariants, order and size, and which side holds the odd element (§Two heaps).
4. **Min-heap or max-heap, and do you negate on the way out?** *What sits at the root is what you throw away* (§The size-k heap: why a min-heap gives the k largest).
5. **Can field 0 tie? If it can, is field 1 comparable?** If not, insert a unique middle field (§What you push: (priority, payload)).
6. Write it.
7. **Run [bug-checklist.md](../reference/bug-checklist.md#the-30-second-pass), §The 30-second pass**, then §Common heap mistakes below. Then, specific to here: *is every `heappop` guarded by a non-empty check?* · *is it push then pop, and `> k`?* · *am I reading `h[1]` as a rank?* · *for quickselect: is every branch strictly smaller than its input, and is the answer a subset or a superset?* · *what did my last fix make unnecessary?*
8. **Trace the degenerate inputs, not the happy path:** k = n, k = 1, an empty heap popped, duplicate priorities, and already sorted input, which is a fixed-pivot quickselect's worst case (§0.6).
9. **Say the complexity unprompted, time and space:** *"O(\_\_) time because \_\_ runs \_\_ times and each costs \_\_."* For a size-k heap the last blank is log k, and say why: a heap operation costs log of the heap's size, and the heap never exceeds k. Count the `Counter` in the space. For quickselect, say average and worst, every time (§0.7).
10. **Then: is it optimal?** What must any correct algorithm do at minimum? Usually: *"Ω(n), because I have to look at every element, and quickselect meets it on average"* (§Why selection can be linear when sorting can't).

---

## Common heap mistakes

Ordered by how often each happens.

| Mistake | What you see | Entry |
|---|---|---|
| The heap holds bare values, and you needed to know which item | you pop the smallest distance and have no point; you pop the smallest front and can't tell which list to advance | [bug-checklist.md](../reference/bug-checklist.md#a-structure-that-cant-express-the-answer), §A structure that can't express the answer |
| Heap positions read as ranks | `h[1]` used as the second smallest; the heap returned as an ordered list | §Partial order is the entire trade |
| Popping an empty heap | `IndexError: index out of range` | [bug-checklist.md](../reference/bug-checklist.md#the-guard-asymmetry), §The guard asymmetry |
| The minus on the way out missing from a max-heap | every answer negative, or `max` behaving like `min` | §Max-heaps and negation |
| A tuple negated | `TypeError: bad operand type for unary -: 'tuple'` | §Three ways negation breaks |
| A payload with no `__lt__` and no tie-breaker | `TypeError: '<' not supported between instances of …`, only on inputs that tie | §The tie-breaking trap, and [bug-checklist.md](../reference/bug-checklist.md#the-heap-tuple-in-the-wrong-order), §The heap tuple in the wrong order |
| A tie-break that runs the wrong way in a size-k heap | the right counts and the wrong items | §Top-K with a tie-break that runs the wrong way |
| Pop before push at size k | a real survivor evicted before the newcomer is compared | §Push then pop, in that order |
| `> k` against `>= k` | the answer has k − 1 or k + 1 items | [bug-checklist.md](../reference/bug-checklist.md#off-by-ones-derive-never-freehand), §Off-by-ones: derive, never freehand: trace k = 1 on two items |
| A quickselect that doesn't terminate | a hang on `[3, 2, 1]` with k = 1 | §The two classic bugs |
| A quickselect that returns a superset | more than k items out | §The two classic bugs |
| O(n²) on sorted input | a TLE on a large sorted test | §The ways it breaks |
| The kth-largest index derived wrong | off by one, on every input | [bug-checklist.md](../reference/bug-checklist.md#off-by-ones-derive-never-freehand), §Off-by-ones: derive, never freehand: check k = 1 and k = n |
| An object mutated while it is in the heap | the heap silently stops being a heap; wrong answers, no crash | §Lazy deletion |
| n pushes when the whole list was in hand | O(n log n) where O(n) was available | §Why heapify is O(n), not O(n log n) |
| The `Counter` left out of the space | *"O(k) space, the heap is capped"*, on an algorithm that allocated u entries | §0.7 |
| A dead structure left after the fix | a `seen` set, a parallel list, or a `sorted()` that the heap made redundant | [bug-checklist.md](../reference/bug-checklist.md#the-fix-fossil), §The fix fossil |

---

## Drill set — cold, no IDE, no running

Each problem is ordered so that it adds exactly one new thing to the one before. The shapes are taught above on problems outside this table (Top K Frequent Words, Sort Characters By Frequency, IPO, and merging k sorted arrays).

| # | Problem | Template | Focus |
|---|---|---|---|
| 1 | [Kth Largest Element in a Stream](https://leetcode.com/problems/kth-largest-element-in-a-stream/) (LC 703) | row 4 | **The size-k heap, and nothing else.** The word "stream" tells you why sorting isn't available. Decide what the object keeps between calls. ⚑ **Checkpoint** |
| 2 | [Last Stone Weight](https://leetcode.com/problems/last-stone-weight/) (LC 1046) | row 2 | **+ negation, and a simulation loop.** Pop two, push what is left. Decide the loop condition and the empty case before you write the loop |
| 3 | [Top K Frequent Elements](https://leetcode.com/problems/top-k-frequent-elements/) (LC 347) | rows 6 and 7 | **+ a `Counter`, and a payload.** Frequency is the key; the item is the payload. Do it both ways, heap then bucket, and say why the bucket version escapes the n log n bound |
| 4 | [K Closest Points to Origin](https://leetcode.com/problems/k-closest-points-to-origin/) (LC 973) | row 5 | **+ a computed key and a non-numeric payload.** Decide which direction the heap evicts before you write it, and ask whether field 0 can tie |
| 5 | [Kth Largest Element in an Array](https://leetcode.com/problems/kth-largest-element-in-an-array/) (LC 215) | row 11, then row 12 | **Pure quickselect, with nothing in the way.** No `Counter`, no key function, no payload. Write row 11 first, then convert it to row 12. ⚑ **Checkpoint** |
| 6 | [Task Scheduler](https://leetcode.com/problems/task-scheduler/) (LC 621) | row 2, plus one more structure | **+ a second structure beside the heap.** Work out where a task waits between runs. There is also a pure-counting answer; find it after the heap version works |
| 7 | [Merge k Sorted Lists](https://leetcode.com/problems/merge-k-sorted-lists/) (LC 23) | row 8 | **+ k-way merge on linked lists.** ⚠️ `ListNode` has no `__lt__`, so the tie-breaker is mandatory, not optional. It is also in module 05's drill set |
| 8 | [Find Median from Data Stream](https://leetcode.com/problems/find-median-from-data-stream/) (LC 295) | row 9 | **+ two heaps and a rebalance.** The state sentence in §Two heaps is the algorithm. Decide which side holds the odd element before you write a line. ⚑ **Checkpoint** |
| 9 | [Design Twitter](https://leetcode.com/problems/design-twitter/) (LC 355) | row 8 | **+ a heap inside a design problem.** The feed is a k-way merge over the people you follow, and the hard part is choosing the data model, not the heap |

**Why this order:** the list is NeetCode 150's heap and priority-queue problems, which run 703, 1046, 973, 215, 621, 355, 295. Three changes. Row 3 is inserted: it is on NeetCode's arrays list, but it is the cleanest introduction of `(priority, payload)`. Row 8 moves after row 7, because two heaps is the hardest idea in the module and k-way merge is a gentler second heap, and row 9 goes last because it is the same k-way merge inside a design problem, so it is a review of row 7 more than a new idea. Row 7 is pulled in from the linked-list module: it is a k-way merge wearing a linked list.

**⚑ Checkpoint at row 1.** It is the size-k heap with nothing around it. If it comes out clean, with the complexity said unprompted, go on. If not, reread §The size-k heap: why a min-heap gives the k largest and §0.7 before row 2.

**⚑ Checkpoint at row 5.** It is quickselect with nothing in the way, and it is where §The two classic bugs get tested. Trace sorted input, `[1, 2, 3, 4, 5]` with k = 1, before you submit: sorted input is a fixed-pivot quickselect's worst case, and it is a common test.

**⚑ Checkpoint at row 8.** It is the two-heap pattern, and it can't be brute-forced into working. If the state sentence isn't written down, stop and write it.

**Watch row 3.** Do row 3 both ways, heap then bucket. It doesn't count as done until both are written and you can say which is O(n) and why.

**Spares, if a shape needs a second rep:** [Top K Frequent Words](https://leetcode.com/problems/top-k-frequent-words/) (LC 692, written out in §Top-K with a tie-break that runs the wrong way; a from-memory rep) · [Sort Characters By Frequency](https://leetcode.com/problems/sort-characters-by-frequency/) (LC 451, written out in §The O(n) answer: bucket sort by count; a from-memory rep) · [IPO](https://leetcode.com/problems/ipo/) (LC 502, written out in §Two heaps; a from-memory rep) · [Kth Smallest Element in a Sorted Matrix](https://leetcode.com/problems/kth-smallest-element-in-a-sorted-matrix/) (LC 378: a k-way merge over the rows, and a binary-search answer too) · [Reorganize String](https://leetcode.com/problems/reorganize-string/) (LC 767: greedy on a max-heap, the sibling of row 6) · [Find the Kth Largest Integer in the Array](https://leetcode.com/problems/find-the-kth-largest-integer-in-the-array/) (LC 1985: row 5's problem where the key is a string of digits, so the comparator is the problem) · [Meeting Rooms II](https://leetcode.com/problems/meeting-rooms-ii/) (LC 253) 🔒 (a heap of end times) · [Sliding Window Maximum](https://leetcode.com/problems/sliding-window-maximum/) (LC 239: the deque, not the heap; a drill in module 03, [§When the window needs its maximum](03-two-pointers-sliding-window.md#when-the-window-needs-its-maximum))

🔒 = LeetCode Premium.

## Not covered here

- **Dijkstra.** It is a heap, but it lives in [08-graphs.md](08-graphs.md#dijkstra), §Dijkstra.
- **Huffman coding:** pop two, push their combination, repeat (§0.8).
- **`heapq.merge`**, which is row 8 as a standard-library generator.
- **Indexed and Fibonacci heaps**, which have a real decrease-key.
- **d-ary heaps.**
- **Order-statistic trees**, and `SortedList` from `sortedcontainers`, which is not in the standard library and so not available in most interviews.
- **Median-of-medians**, beyond the one sentence in §What to say in a room.

Interview loops mostly ask top-K, the kth largest, merge-k, the median of a stream, and one simulation that is *"repeatedly take the smallest"*. Quickselect comes up as the follow-up to top-K, nearly always. Everything past that is rare enough that naming it is enough.

## Before you submit anything

Run [bug-checklist.md](../reference/bug-checklist.md#the-30-second-pass), §The 30-second pass, over your code. Thirty seconds.

---

## Self-check answers

1. **A sift-down costs the node's height above the leaves, not log n**, and almost every node is near the bottom: half are leaves and cost nothing, a quarter cost at most 1, an eighth at most 2. The total is n/2 × (1/2 + 2/4 + 3/8 + …), and **that series sums to 2, so the total is n.**
2. **No.** `h[1]` is 5, and the second smallest is 1, at `h[2]`. **Only the root is placed.** The second smallest is a child of the root, so in general it is **`min(h[1], h[2])`**.
3. **The root is the weakest survivor, and it is what you evict on every overflow.** To keep the largest you must throw away the smallest, so the smallest has to be at the root: a min-heap. Eviction is safe because **the evicted item already has k items beating it**, and later arrivals only add competitors.
4. **Two entries with equal `cost`.** The tuple comparison falls through to `task` and raises **`TypeError: '<' not supported between instances of …`**, on that input only. The fix is a unique middle field: **`(cost, next(tie), task)`** with `tie = itertools.count()`.
5. **Nothing stops early: the loop reads all n items**, and it has to, because the last one might be the largest. **The log k comes from the heap's size**: each push and pop costs log of what is in the heap, and the heap never holds more than k. *"O(n log k), because n items each pay log k."*
6. **The bound is about telling apart n! arrangements; selection outputs a set.** There are C(n, k) possible sets and **C(n, k) ≤ 2ⁿ**, so the counting argument only demands log₂ C(n, k) ≤ n comparisons. The real floor is **Ω(n), from reading every item**, and quickselect meets it on average.
7. **Duplicates.** A `set` records only that a value is dead, so removing one 5 would kill every 5 in the heap. **A `Counter` keeps the count**, and each purge spends exactly one.
8. **`heappushpop(h, 1)` returns 1 and leaves `[3, 5]`**: it pushes first, and 1 is the new minimum, so it comes straight back out. **`heapreplace(h, 1)` returns 3 and leaves `[1, 5]`**: it pops the root first, whatever `x` is, then pushes 1.
