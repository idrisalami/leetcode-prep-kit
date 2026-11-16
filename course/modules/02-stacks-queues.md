# Module 02: Stacks and queues

<!-- toc -->
**Contents**

- [0.1 Prerequisites and the one question](#01-prerequisites-and-the-one-question)
- [0.2 The structure and how it works](#02-the-structure-and-how-it-works)
  - [A list used as a stack](#a-list-used-as-a-stack)
  - [A deque used as a queue](#a-deque-used-as-a-queue)
- [0.3 Vocabulary](#03-vocabulary)
- [0.4 Operations and their cost](#04-operations-and-their-cost)
- [0.5 The primitives](#05-the-primitives)
  - [Say the sentence before the loop body](#say-the-sentence-before-the-loop-body)
- [0.6 Inputs that break it](#06-inputs-that-break-it)
- [0.7 Complexity, out loud](#07-complexity-out-loud)
  - [The amortised argument](#the-amortised-argument)
- [0.8 Signals](#08-signals)
- [0.9 Self-check](#09-self-check)
- [Resolve against the top: matching and collapsing](#resolve-against-the-top-matching-and-collapsing)
  - [The naive version, and why it's quadratic](#the-naive-version-and-why-its-quadratic)
  - [The stack version](#the-stack-version)
  - [The matching shape, as a checklist](#the-matching-shape-as-a-checklist)
- [The path stack: when empty means skip](#the-path-stack-when-empty-means-skip)
- [The operand stack: expressions](#the-operand-stack-expressions)
  - [Postfix, and why it exists](#postfix-and-why-it-exists)
- [Carried state: a slot that holds more than the item](#carried-state-a-slot-that-holds-more-than-the-item)
- [The monotonic stack](#the-monotonic-stack)
  - [The question it answers](#the-question-it-answers)
  - [The insight, and why the stack ends up sorted](#the-insight-and-why-the-stack-ends-up-sorted)
  - [The shape](#the-shape)
  - [Next Greater Element I, in full](#next-greater-element-i-in-full)
  - [When the answer is a width](#when-the-answer-is-a-width)
  - [A missing precondition is a missing first line](#a-missing-precondition-is-a-missing-first-line)
- [When the stack is only a counter](#when-the-stack-is-only-a-counter)
- [The queue: first in, first out](#the-queue-first-in-first-out)
  - [FIFO against LIFO](#fifo-against-lifo)
  - [`pop(0)` against `popleft`](#pop0-against-popleft)
  - [Which item comes out: newest, oldest, smallest](#which-item-comes-out-newest-oldest-smallest)
  - [A queue in action](#a-queue-in-action)
  - [Two stacks make a queue](#two-stacks-make-a-queue)
- [When not to reach for a stack](#when-not-to-reach-for-a-stack)
- [Common stack and queue mistakes](#common-stack-and-queue-mistakes)
- [Not covered here](#not-covered-here)
- [Drill set — cold, no IDE, no running](#drill-set--cold-no-ide-no-running)
  - [The stack half](#the-stack-half)
  - [The queue half](#the-queue-half)
- [Before you submit anything](#before-you-submit-anything)
- [Self-check answers](#self-check-answers)
<!-- /toc -->

This module covers the two structures that hand you an item by **when it arrived**: the **stack**, which hands back the newest, and the **queue**, which hands back the oldest. Both are the cheapest retrieval there is, because arrival order is recorded for free by the act of arriving. The container is small: a Python `list` used at one end, or a `deque` used at both. The idea worth the module is the **monotonic stack**, the one genuinely new algorithm here.

Underneath every problem here is one sentence:

> **What is on the stack, and why is the top the one I need next?**

For a monotonic stack the sentence has a second half, **and why is it sorted?** Without it, the `while` comparison gets written by feel, and an increasing stack answers a different question from the one asked.

The drill set at the bottom is deliberately **not solved anywhere in this file**. Every example the sections walk through uses a problem outside the drill set.

**How to use it.** Read §0, then answer the self-check in §0.9 and re-read the parts of §0 behind any question you miss. Then work through the sections from matching to the queue, and do the drill set cold.

| Section | What it gives you |
|---|---|
| §0, the foundation | the one question, the self-restriction, the vocabulary, what each operation costs, the four primitives, the inputs that break them, the amortised argument, the signals |
| Resolve against the top | collapsing adjacent pairs, and the matching checklist |
| The path stack | the same structure where an empty stack means "skip" |
| The operand stack | peek against pop, and why postfix needs no parentheses |
| Carried state | a stack whose slots hold more than one value |
| The monotonic stack | the insight, the shape, a full example, and widths |
| When the stack is only a counter | when every item is identical |
| The queue | first in first out, `pop(0)` against `popleft`, and a full example |
| When not to reach for a stack | the neighbouring structures |
| Common stack and queue mistakes | the bugs, each linked to its checklist entry or section |
| Not covered here | related problems, and where they come back |
| Drill set | the problems, with the checkpoints |
| Before you submit anything | the checklist |

---

## 0.1 Prerequisites and the one question

| You need | From | Used here for |
|---|---|---|
| Counting cost, and amortised cost | [00-before-you-start.md](00-before-you-start.md#big-o-from-zero), §Big-O from zero | §0.7: why the monotonic stack's nested `while` is still linear |
| The call stack | [00-before-you-start.md](00-before-you-start.md#recursion-and-the-call-stack), §Recursion and the call stack | §0.2: the call stack is a stack |
| `list`, `append`, `pop`, `for`, `enumerate` without an IDE | [00-before-you-start.md](00-before-you-start.md#the-python-interview-subset), §The Python interview subset | every code block here |
| The list as a row of numbered slots | [01-arrays-hashing.md](01-arrays-hashing.md#the-list-a-row-of-numbered-slots) | §0.4: why `pop()` is O(1) and `pop(0)` is O(n) |
| `dict` and `set`, and what a key demands | [01-arrays-hashing.md](01-arrays-hashing.md#02-the-structure-and-how-it-works), §0.2 The structure and how it works | the table below, and the map in §The monotonic stack |
| The three escapes: Remember, Order, Reuse | [01-arrays-hashing.md](01-arrays-hashing.md#the-three-escapes-remember-order-reuse) | §The monotonic stack: why none of the three fires |

**The one question this module answers:**

> *Of everything I've already seen, which item is the one that matters right now?*

Every container is an answer to that question. The criterion is the choice; the structure follows from it. Sorted by how much each one demands from you, most to least:

| The answer to *"which one?"* | Structure | Get it with | What the structure demands of you | Reads in a problem as |
|---|---|---|---|---|
| "The **nearest one by value**" | sorted sequence plus binary search | `bisect_left(a, x)`, O(log n) | **a total order, maintained**: insertion is O(n), because the order has to be kept, not just computed | *"largest ≤ x"*, *"the closest"*, *"in this range"* |
| "The **largest**, or smallest" | heap, `heapq` | `heappop(h)`, O(log n) | **a comparison** between any two items, run O(log n) times per operation | *"k largest"*, *"top k"*, *"next to expire"* |
| "An **arbitrary** one, and I know its key" | `dict` / `set` | `d[k]`, O(1) average | **a hashable key**; hashing destroys order, so it only answers *exact* | *"have I seen it"*, *"how many times"*, *"look it up by"* |
| "The **oldest** one I haven't finished with" | queue, `deque` | `q.popleft()`, O(1) | **nothing** | *"level by level"*, *"fewest steps"*, *"in arrival order"* |
| "The **most recent** one I haven't finished with" | **stack, a plain `list`** | `s.pop()`, O(1) | **nothing** | *"the last one"*, *"undo"*, *"nesting"*, *"next greater"* |

You'll see the sorted sequence again in module 04 ([04-binary-search.md](04-binary-search.md)) and the heap in module 10 ([10-heaps.md](10-heaps.md)). The `dict` and `set` are module 01's.

> **The bottom two rows are the only ones that demand nothing at all**: no key, no comparison, no maintained order. *Recency* and *antiquity* aren't properties of the items; they are properties of **when the items arrived**, and arrival order was recorded for free by the act of arriving. Nothing has to be computed, compared or hashed to find the oldest or the newest, because the structure's own shape already knows.

This module is the bottom two rows. The last row's criterion comes up constantly, because *"the most recent one I haven't finished with"* is what nesting means (§0.2), and a structure that only ever hands you that item turns a search into a read.

## 0.2 The structure and how it works

### A list used as a stack

A stack is a Python `list` on which you have agreed to use exactly one position: **the end**.

```python
stack = []
stack.append(x)      # push
stack[-1]            # peek
stack.pop()          # pop
```

Nothing has been added. `list` already does all of this and much more: indexing, slicing, `insert`, `remove`, iteration. Choosing "a stack" doesn't give you a new capability. It **takes capabilities away**.

So the question that makes the topic click:

> **Why would anyone deliberately give up random access?**

The weak answer: a smaller interface is easier to reason about. True, and not a reason anyone picks it under time pressure.

The real answer: **the restriction is what carries the information.**

> **"The most recent thing I haven't resolved yet" is the exact shape of nesting.** If that is always the item you need next, then a structure whose only reachable element *is* that item isn't a limitation. It's a free index.

Read a sentence with a parenthesis in it (and a quoted phrase "inside the parenthesis" like this one). At every moment, the thing you must close first is the most recently opened thing. You already run this algorithm; the data structure is only its name.

The formal version of nesting:

> **If A opens before B, and B closes before A, then B is entirely inside A. Regions never partially overlap.** That property is precisely what makes "most recent unresolved" always the correct next item.

So the trade is:

| I gave up | I bought |
|---|---|
| `s[i]`, slicing, searching the middle | the relevant item is **always at a known place**: the end |
| any notion of "look at the third from the top" | O(1) instead of O(n) to find the item that matters |
| nothing else: the underlying list is untouched | a structure whose *shape* encodes the nesting depth |

> **Discipline about what you're allowed to touch is what turns "search the past for the relevant item" into "read the top."** The restriction isn't the cost of the technique. It *is* the technique.

**LIFO reverses order, FIFO preserves it.** Push A then B and a stack hands back B first. A queue hands back A first. That one difference is the whole distance between this subsection and the next.

**The call stack is a stack.** Every function call pushes a frame and every return pops one, which is why the most recently called function is always the one that finishes first ([00-before-you-start.md](00-before-you-start.md#recursion-and-the-call-stack), §Recursion and the call stack). You'll see this again in module 08 ([08-graphs.md](08-graphs.md)), where it is why recursion is depth-first for free, and "write this iteratively" means "make the stack explicit."

### A deque used as a queue

A queue is the other discipline: items join at the **back** and leave from the **front**, so the item handed back is always the **oldest** one still waiting. First in, first out.

```python
from collections import deque

q = deque()
q.append(x)          # join at the back
q[0]                 # peek at the front
q.popleft()          # leave from the front
```

The container is a `deque`, not a `list`, for one reason: a list's front is its expensive end. §0.4 has the costs, and §The queue has the full section.

## 0.3 Vocabulary

| Term | Meaning |
|---|---|
| **stack** | a collection you add to and remove from at the same end only; here, a `list` used at its right end |
| **push** | add an item on top: `stack.append(x)` |
| **pop** | remove and return the top item: `stack.pop()` |
| **peek** | read the top item without removing it: `stack[-1]` |
| **top** | the most recently pushed item still on the stack |
| **LIFO** | last in, first out: the stack's order |
| **queue** | a collection you add to at the back and remove from at the front |
| **FIFO** | first in, first out: the queue's order |
| **front / back** | where a queue's items leave / where they join |
| **`deque`** | *double-ended queue*, from `collections`: O(1) adds and removes at both ends |
| **unresolved** | an item still waiting for whatever will finish it: a closer, a greater element, an operator |
| **leftovers** | the items still on the stack when the loop ends: the ones that were never resolved |
| **monotonic stack** | a stack whose values stay sorted from bottom to top, because each push first pops everything that would break the order |
| **next greater element** | for an element, the nearest element to its right that is larger than it |
| **carried state** | extra values stored in a slot alongside the item, because they will be needed at pop time |
| **sentinel** | an extra input value chosen so that a special case disappears, such as one that pops everything left on the stack |
| **amortised** | averaged over the whole run: one step may do a lot of work, the total is still bounded |

## 0.4 Operations and their cost

**n** is the number of items pushed or enqueued over the run.

| Operation | Python | Big-O | Trap |
|---|---|---|---|
| Push | `stack.append(x)` | O(1) amortised | none: the right end is the cheap end |
| Peek | `stack[-1]` | O(1) | on an empty list it raises `IndexError` |
| Pop | `stack.pop()` | O(1) | destructive, with no undo except pushing back; if the decision might be "keep it", peek first |
| Is it non-empty? | `if stack:` | O(1) | `if stack[-1]:` asks something else: it is `False` when the top is `0`, `""` or `[]`, all legal items |
| Depth | `len(stack)` | O(1) | a separate `depth` counter kept alongside the stack is dead code |
| Search the stack | `x in stack`, or a loop over it | **O(n)** | breaks the restriction; if a query needs it, the answer belongs in the slot (§0.5, primitive 3) |
| A stack of characters back to a string | `''.join(stack)` | O(n) | join once at the end, bottom to top |
| Remove from the **front** of a list | `lst.pop(0)` | **O(n)** | every other element shifts left one slot; inside a loop over n items it is O(n²) |
| Add to the front of a list | `lst.insert(0, x)` | **O(n)** | the same shift, the other way |
| Enqueue | `q.append(x)` | O(1) | none |
| Dequeue | `q.popleft()` | O(1) | on an empty deque it raises `IndexError` |
| Peek at the front | `q[0]` | O(1) | `IndexError` when empty, the same as `stack[-1]` |
| Index into the middle of a deque | `q[i]` | **O(n)** | a `deque` is cheap at its ends only; for the middle, use a `list` |

**Peek versus pop is a decision, not a style.** Pushing back what you just popped is the smell that says you should have peeked:

```python
if stack and stack[-1] == c:      # ✓ inspect, THEN decide
    stack.pop()

top = stack.pop()                 # ✗ if the decision is "keep it", you now have to push it back
if top != c:
    stack.append(top)
```

⚠️ **On a non-empty list, `values[-1]` is the last element. On an empty list there is nothing to read, so it raises.** Same syntax, two behaviours, and which one you get depends on a runtime condition. `pop()` on an empty list raises the same way. Every peek and every pop needs `if stack` in front of it unless you can prove the stack is non-empty.

⚠️ **Truthiness: test the stack, not its top.**

```python
if stack[-1]:              # ✗ False when the top is 0, "" or []: all legal stack items
if stack:                  # ✓ asks the question you meant: is the stack non-empty?
```

On a stack of integers where `0` is a valid value, the first version treats a real item as an empty stack. It never crashes ([python-toolkit.md](../reference/python-toolkit.md#python-truthiness-why-while-queue-works), §Python truthiness: why `while queue:` works).

## 0.5 The primitives

Four building blocks cover the module. Each has an invariant: a statement true at the top of every iteration. Choose it before writing the body; every line of the body then has one job, which is to leave it still true.

**1. The stack of unresolved items.** Every stack algorithm has the same invariant, and you get it for free:

*Invariant:* the stack holds every item still waiting to be resolved, in the order they were opened, most recent on top.

Every problem is a specialisation of that: *what counts as an item*, and *what counts as resolved*. That is all you have to fill in.

**2. The monotonic stack.** For "what is the nearest element to the right that is greater than this one?", walk left to right. When a new element `x` arrives, every waiting element smaller than `x` has found its answer, which is `x`, and can never be anybody else's answer, because anything further right meets `x` first and `x` is bigger. So they are popped.

*Invariant:* the stack holds the indices of the elements still waiting for their next greater element, and their values are **non-increasing from bottom to top**: decreasing, except that equal values can sit together.

The sortedness is a consequence, not a rule: everything smaller than the newcomer is removed, so everything that survives is greater than or equal to it, and then the newcomer goes on top. **The top is the smallest waiting element, so it is the first one a newcomer can answer; and if the newcomer can't answer the top, it can't answer anything underneath either**, which is why the `while` stops the moment the comparison fails. §The monotonic stack builds this up in full.

Push **indices**, not values. A distance or a width needs a position, and the conversion only runs one way: `nums[i]` gets the value from the index, and nothing gets the index back from a value. Values are safe only when they are distinct **and** no position is ever needed.

**3. Carried state.** Sometimes one value per slot isn't enough. Push a tuple, or a small list.

*Invariant:* each slot holds everything that will be needed when it is popped. **Whatever you'll need at pop time has to be on the stack at push time**: you can't look at anything but the top, and you can't go back for it later.

Three flavours, in increasing order of cleverness:

- **`(item, index)`**: you'll need to know where it was. Any answer that is a distance or a width needs positions, and by pop time the loop variable that knew the position is long gone. On monotonic stacks this is so common that the default is to push the index alone and read the value through it.
- **`[item, count]`**: collapsing runs. Instead of pushing `'a'` three times, push `['a', 3]` once and increment the count in place.
- **`(item, the answer for everything below me)`**: the summary shape. The principle generalises far beyond stacks:

> **A stack pops in exactly the reverse of push order. So the state of the stack at the moment an item was pushed is exactly the state it returns to when that item is popped.** Anything you computed at push time about "everything underneath me" is still true at pop time. Compute it once, store it in the slot, and pops need no recomputation.

The alternative, scanning the stack on every query to recompute the summary, is O(n) per query and throws away the one property that makes a stack a stack. This is module 01's **Remember** escape one level up: you're not storing more items, you're storing a fixed extra value per item. The space is O(n) either way; the query goes from O(n) to O(1).

The principle is here; the code is yours. If you find yourself about to write a loop over the stack to answer a query, stop: the answer belongs in the slot. And before writing any of it, ask whether the storage you chose can even hold the answer at every step. One variable can't hold an answer that has to change back on every pop ([bug-checklist.md](../reference/bug-checklist.md#bounds-or-state-that-cant-express-the-answer), §Bounds or state that can't express the answer).

**4. The queue of waiting items.**

*Invariant:* the deque holds every item still waiting, in the order they arrived; the front is the oldest of them.

`append` keeps it true for a new arrival, and `popleft` keeps it true when the oldest is finished. Nothing else may touch the deque.

### Say the sentence before the loop body

The invariant, specialised to the problem, is one sentence. Say it before writing the body, not after the code compiles in your head:

> **What is on the stack, and why is the top the one I need next?**

What a real one looks like, on the problems this module walks through:

| Problem | The sentence |
|---|---|
| Adjacent-duplicate removal (§Resolve against the top) | *"The stack holds the fully reduced prefix of the string; the top is the only character the next one could cancel."* |
| Path simplification (§The path stack) | *"The stack holds the directories of the canonical path so far, root first; the top is the one `..` removes."* |
| A score record (§The operand stack) | *"The stack holds every score that still counts; every operation refers to the one or two most recent scores and nothing deeper."* |
| Runs of length k (§Carried state) | *"The stack holds the reduced string as `[character, run length]` pairs, adjacent pairs always differing; the top is the only run the next character could extend."* |
| Next greater element (§The monotonic stack) | *"The stack holds the elements still waiting for their next greater element, non-increasing from bottom to top; the top is the smallest of them, so it's the first one a new element can answer."* |
| Turn order (§The queue) | *"Each queue holds its side's members still in the game, in the order they act; the front is the next to act."* |

The monotonic row has a **second half**, *and why is it decreasing?* On any monotonic-stack problem, the sentence is not complete without it.

**The two obligations of any invariant:**

1. **Is it true before iteration 1?** The stack starts empty, and an empty stack says "nothing is unresolved", which is true before you've seen anything. On this topic the initial state is almost always trivially correct; the initialisation is not where it bites.
2. **Does the body leave it true?** Every `append` must be an item that is now genuinely unresolved. Every `pop` must be an item that has just been resolved. **If you pop something that isn't finished, you've lost it**: there is no way back to it.

> ⚠️ **You'll see these two obligations again in module 04 ([04-binary-search.md, §Progress and safety](04-binary-search.md#progress-and-safety))**, where the initial state is not free and is the whole difficulty.

**And the question that catches the classic bug, which follows directly from the sentence:**

> **If the top is the one I need next, what does it mean when there is no top?**

An empty stack in the middle of a loop always means something specific, and it is different in every problem. Answer it *before* you write the guard. §The path stack has the table.

## 0.6 Inputs that break it

| Input | What breaks | Check |
|---|---|---|
| Empty input: `""`, `[]` | anything that peeks or pops before the loop | the loop doesn't run; is an empty stack at the end the right answer? Usually it is |
| A pop on an empty stack | `IndexError`, the module's crash | guard with `if stack`, and know what the empty case *means* here |
| Input that never closes: `"((("` | **nothing**: no crash, the loop completes, and a naive version reports success | leftovers on the stack are unresolved forever; the check at the end is not optional |
| Input that closes what was never opened: `")"` | `pop()` on an empty stack | the guard *is* the logic: decide what the empty case answers |
| An element with no answer: nothing greater to its right | nothing crashes; the answer is silently missing | whatever is still on the stack at the end has no answer: initialise the output to the "no answer" value |
| A strictly decreasing array, `[5, 4, 3, 2, 1]`, on a next-greater stack | the inner `while` never fires and nothing is popped | every element must come back as "no answer"; anything else means the default was wrong or the leftovers were dropped |
| A stack of integers containing `0` | `if stack[-1]:` reads a real item as an empty stack | test `if stack:`, never the top |
| A large input through a queue built on `list.pop(0)` | nothing visible on small tests; a time limit on big ones | `deque.popleft()` |
| An empty queue | `q.popleft()` and `q[0]` raise `IndexError` | `while q:` as the loop condition |

> **Two of those rows are the same bug wearing different clothes: the loop ends and the stack isn't empty.** Anything still on the stack was never resolved and never will be. **The stack at the end is part of the answer, not a leftover**: decide what it means before you write the loop.

The strictly decreasing array is the fifteen-second trace for every monotonic stack. Run it before submitting.

## 0.7 Complexity, out loud

**The easy half.** Push, pop and peek are each O(1). One pass that pushes every element once is O(n). Space is O(n), and say **what** is on the stack in the worst case, not just the letter.

| Shape | Time | Space |
|---|---|---|
| One pass, each item pushed at most once | O(n) | O(n): the stack, worst case every item at once |
| Monotonic stack: a `while` that pops inside the `for` | O(n), amortised | O(n): worst case a strictly decreasing input, nothing ever popped |
| A queue, n items each enqueued and dequeued once with a `deque` | O(n) | O(n) |
| The same queue built on `list.pop(0)` | **O(n²)** | O(n) |
| A queue built from two stacks | O(1) amortised per operation | O(n) |

### The amortised argument

This shape:

```python
for x in nums:
    while stack and <some test against stack[-1]>:
        stack.pop()
    stack.append(x)
```

A `while` nested inside a `for`. It **looks** quadratic. It is **O(n)**, and an interviewer will probe exactly this, because it's the fastest way to find out whether you understand your own solution.

> **The argument, to say cold:**
>
> *"Each element is pushed exactly once, one push per `for` iteration, and once it's popped it is never pushed again. So there are at most n pushes, therefore at most n pops: the `while` body runs at most n times **in total**, not n times per iteration. That's at most 2n stack operations overall, each O(1). The cost belongs to the element, not to the iteration that removes it."*

The bound comes from the pushes. "The `while` pops, so it runs at most n times" is the claim; "because each element was pushed only once" is the reason, and it is the link an interviewer pushes on.

**The test for whether the argument applies:**

> **Can the inner loop do n units of work on an iteration where those n units weren't already paid for earlier?**

- Monotonic stack: **no.** To pop n things it must first have pushed n things, and each push happened on its own outer iteration. Amortised O(n).
- `for i in range(n): for j in range(n):`: **yes.** The inner loop does full work every time, funded by nothing. Genuinely O(n²).

The same argument covers a queue built from two stacks: each element is pushed onto each stack at most once and popped from each at most once, so n operations cost O(n) in total, O(1) amortised each.

You'll see the same argument again in module 03 ([03-two-pointers-sliding-window.md](03-two-pointers-sliding-window.md)), where the window's `left` only moves forward, and in module 08 ([08-graphs.md](08-graphs.md)) later, as O(V + E) for breadth-first search.

⚠️ **Reporting a monotonic stack as O(n²) is the worst version of underselling a solution**: it is optimal, and you'd be describing it as the brute force.

**Fill the template, both lines, unprompted:**

> **"O(\_\_) time, because \_\_ runs \_\_ times and each one costs \_\_."**
>
> **"O(\_\_) space, because the only thing I allocate is \_\_, and it grows with \_\_."**

The space blank asks **what you allocate**, not how many names you wrote. For a stack the honest answer is usually *"the stack, which holds at most one entry per element: O(n), and the worst case is an input where nothing is ever popped."*

**The template is a check, not a formality.** O(1) space means "does not grow with n", not "is small". If your space line comes out as "the stack never holds more than two items" on a problem whose input can nest arbitrarily deep, the next question is *why isn't my stack growing?*, and the answer is usually a bug.

## 0.8 Signals

| In the statement | Reach for | Where |
|---|---|---|
| brackets, tags, nesting, "is it valid" | a matching stack | §Resolve against the top |
| "most recent", "the last one", "undo", "cancel the previous" | a stack: the word *recent* is the whole signal | §0.2 |
| adjacent items cancel or collapse, repeatedly | a stack: popping re-exposes the previous item for free | §Resolve against the top |
| an expression to evaluate | an operand stack | §The operand stack |
| a path with `.` and `..` | a stack of components | §The path stack |
| "next greater", "next smaller", "the first one to the right that…" | a monotonic stack | §The monotonic stack |
| "how far until…", a distance or a width to the next larger or smaller | a monotonic stack | §The monotonic stack |
| nesting depth with a single bracket type | a counter: the stack compresses to its length | §When the stack is only a counter |
| a recursion you're asked to write iteratively | an explicit stack | §0.2 |
| "level by level", "fewest steps", "in arrival order", "in turn" | a queue | §The queue |
| the largest or smallest so far, regardless of when it arrived | **not** a stack or a queue: a heap | §0.1 |
| "generate all valid…" | **not** a stack: backtracking | §When the stack is only a counter |

## 0.9 Self-check

Answer each in a sentence or two, without looking back. The answers are at the bottom of the module. Read the part behind any question you miss.

1. A stack is a `list` with capabilities taken away. What is taken away, and what does the restriction buy you?
2. Why is `lst.pop()` O(1) while `lst.pop(0)` is O(n), and what do you use when you need the front?
3. You need, in turn, the newest unfinished item, the oldest unfinished item, and the smallest item. Which structure gives each, and why do two of them cost nothing to maintain?
4. A loop has a `while` that pops inside a `for` over n elements. Why is it O(n) and not O(n²)?
5. On a next-greater-element stack scanned left to right, why are the values non-increasing from bottom to top, and why can the `while` stop the moment its comparison fails?
6. When may a monotonic stack hold values instead of indices?
7. A stack of integers is tested with `if stack[-1]:` to see whether it is empty. On what input is that wrong, and what is the fix?
8. The loop ends and the stack isn't empty. What does that mean, and what should the code do about it?

---

## Resolve against the top: matching and collapsing

**Worked on [Remove All Adjacent Duplicates In String](https://leetcode.com/problems/remove-all-adjacent-duplicates-in-string/) (LC 1047)**, which is not in the drill set.

*Repeatedly remove two adjacent equal letters until none remain.* `"abbaca"` → `"aaca"` → `"aca"`.

### The naive version, and why it's quadratic

Scan for an adjacent equal pair, delete it, start over. Each scan is O(n), each deletion from a Python string or list is O(n), and there can be n/2 deletions: **O(n²)**.

Look at *why* it has to start over: deleting `bb` from `abbaca` makes `a` and `a` adjacent, **a pair that didn't exist before, formed behind the one just removed.** The naive version restarts because it has no way to look backwards.

### The stack version

```python
def removeDuplicates(s):
    stack = []
    for c in s:
        if stack and stack[-1] == c:
            stack.pop()              # c and the top cancel: both are gone
        else:
            stack.append(c)          # nothing to cancel against: c is now the top
    return ''.join(stack)
```

*The sentence:* **"The stack holds the fully reduced prefix of the string; the top is the only character the next one could cancel, because if it could cancel anything deeper, that pair would already have been removed."**

Eight lines, one pass, O(n) time and O(n) space for the stack.

> **The idea that unifies this whole module: popping doesn't just remove, it REVEALS.**

After `bb` cancels, the character now on top is the `a` from before, ready to be compared against the next `a`. **The stack automatically re-exposes the previous unresolved item.** That is what the naive restart was paying O(n) for, and the stack gives it away for free. The same property is why the structure works for bracket matching, for paths, and for the monotonic stack: in each, resolving one item is what makes the *next* candidate reachable.

### The matching shape, as a checklist

Bracket matching is in the drill set, so the code is not here. The shape is three decisions. Answer all three in writing before you type:

1. **What is an opener, and what goes on the stack for it?** The bracket itself? Its index? The closer it expects?
2. **When I hit a closer, what must the top be, and what does it mean if the stack is EMPTY?** Decide it from the meaning of the input, not from the last problem you solved.
3. **What does the loop ending with a non-empty stack mean?** **`"((("` is the input that catches every solution that forgot to ask question 3**: it crashes nothing and returns the wrong answer.

If a helper you need has a standard-library name, type the standard-library name: a lookup table is a `dict`, not an `if`/`elif` chain three deep. And **branch on the thing that determines the action.** If the kind of character decides what happens, split on the kind of character first; whether the stack is empty only matters inside the branch that reads the top. Splitting on emptiness first is what produces two arms that do the same thing ([bug-checklist.md](../reference/bug-checklist.md#dead-branching-both-arms-assign-the-same-value), §Dead branching: both arms assign the same value).

---

## The path stack: when empty means skip

**Worked on [Simplify Path](https://leetcode.com/problems/simplify-path/) (LC 71)**, which is not in the drill set.

*Convert a Unix path to canonical form.* `"/a/./b/../../c/"` → `"/c"`. `"/../"` → `"/"`. `"/home//foo/"` → `"/home/foo"`.

```python
def simplifyPath(path):
    stack = []
    for part in path.split('/'):
        if part == '' or part == '.':
            continue                       # "//" produces '', "." goes nowhere
        if part == '..':
            if stack:
                stack.pop()                # step up one directory
        else:
            stack.append(part)             # a real directory name
    return '/' + '/'.join(stack)
```

*The sentence:* **"The stack holds the directories of the canonical path so far, root first; the top is the one `..` removes, because `..` always cancels the most recent step down."**

**Three things worth taking from this problem:**

**1. `split('/')` does the parsing.** Hand-rolling a character scan to find the components is slower to write and easier to get wrong. The empty strings that `split` produces from `//` and from the leading `/` are not a nuisance: the same `continue` that handles `.` handles them, because *"a component that means nothing"* is one case, not two.

**2. The return handles the empty stack for free.** `'/' + '/'.join([])` is `"/"`, exactly the right answer for `"/../"`. **A special case you can design away beats a special case you handle**, and here the string concatenation does it with no branch at all ([python-toolkit.md](../reference/python-toolkit.md#empty-safe-built-ins-the-anti-special-case-set), §Empty-safe built-ins: the anti-special-case set).

**3. ⚠️ The empty-stack guard means something different in every problem.** This is the most important table in the section:

| Problem | Empty stack when you need the top | Correct action |
|---|---|---|
| Bracket matching | a closer with nothing open | **fail, immediately** |
| Simplify Path | `..` at the root | **do nothing, and continue** |
| Adjacent-duplicate removal | nothing to cancel against | **push the character** |
| Next greater element | nothing waiting | **push and move on** |

Same structure, same `if stack:` guard, different semantics. **This is why you don't copy a guard from the last problem.** Ask what the empty stack *means here*, and the guard writes itself ([bug-checklist.md](../reference/bug-checklist.md#guards-copied-from-another-problem), §Guards copied from another problem).

**Complexity.** *"O(n) time, because `split` walks the string once, each component is then pushed at most once and popped at most once, and the final `join` walks what's left. O(n) space, because the only things I allocate are the list of components and the stack, and each holds at most one entry per component of the input."*

---

## The operand stack: expressions

**Worked on [Baseball Game](https://leetcode.com/problems/baseball-game/) (LC 682)**, which is not in the drill set.

*A list of operations. An integer means "record this score". `"+"` records the sum of the previous two. `"D"` records double the previous. `"C"` cancels the previous. Return the sum of all records.*

```python
def calPoints(operations):
    stack = []
    for op in operations:
        if op == '+':
            stack.append(stack[-1] + stack[-2])    # PEEK twice: both still count
        elif op == 'D':
            stack.append(2 * stack[-1])            # PEEK: the previous score stays
        elif op == 'C':
            stack.pop()                            # POP: the previous score is void
        else:
            stack.append(int(op))
    return sum(stack)
```

*The sentence:* **"The stack holds every score that still counts, most recent on top; every operation refers to the one or two most recent scores and nothing deeper."**

**What this problem teaches:**

**1. Peek versus pop, made concrete.** `D` and `+` **read** the top without consuming it: the previous score is still a score. `C` **consumes** it. Getting these backwards is a silent wrong answer: the code runs, the arithmetic is right, and the total is wrong. **Before every `stack[-1]`, ask: is this item finished, or am I just reading it?** A read that quietly removes is a query that mutates ([bug-checklist.md](../reference/bug-checklist.md#a-query-that-mutates), §A query that mutates).

**2. The constraints are a guard you don't have to write.** The statement guarantees the operations are always valid: there are always enough scores for `+`, `C` and `D`. So `stack[-2]` needs no bounds check. **A guarantee in the problem statement is a guard you delete**; writing it anyway defends against a state the input can't reach. Read the constraints.

**3. ⚠️ `"-3".isdigit()` is `False`.** The minus sign is not a digit. Using `isdigit()` to decide "is this token a number" quietly misclassifies every negative number as an operator. **Discriminate on the operator set, not on the shape of the number**: test whether the token is one of the operators, and otherwise hand it to `int()`, which handles the sign. The trap transfers to any expression problem whose input contains negative numbers.

### Postfix, and why it exists

Replace `+ D C` with real arithmetic operators and you have **postfix notation**, also called **Reverse Polish Notation**.

```
infix:     3 + 4 * 5          needs precedence rules and parentheses
postfix:   3 4 5 * +          needs neither
```

> **Postfix exists so that no parentheses are ever needed.** In infix, precedence and brackets tell you which operands belong to which operator. In postfix the rule is unconditional: **an operator's arguments are always the most recent unconsumed values.** That is precisely what a stack hands you.

Postfix is *nesting expressed as recency*, and a stack is the structure for recency.

⚠️ **Three traps that pass on the happy path, for any expression problem:**

1. **Operand order.** A stack hands back the most recent value first, and in an expression the most recent value is the **right-hand** operand. Get it backwards and `+` and `*` still pass while `-` and `/` are wrong: a half-correct submission, which is the worst kind.
2. **Names after arrival order.** Name each popped value after its **role**, never after the order it came off. A pair named for the order they arrived in makes the wrong subtraction read as the right one ([bug-checklist.md](../reference/bug-checklist.md#names-that-describe-arrival-order-not-role), §Names that describe arrival order, not role).
3. **Python's `//` floors toward −∞.** `-7 // 2` is `-4`, not `-3`. If a problem asks for division that truncates toward zero, `//` passes on all-positive inputs and fails on the test set. Find the truncating form yourself.

---

## Carried state: a slot that holds more than the item

**Worked on [Remove All Adjacent Duplicates in String II](https://leetcode.com/problems/remove-all-adjacent-duplicates-in-string-ii/) (LC 1209)**, which is not in the drill set. *Remove every run of exactly `k` identical adjacent characters, repeatedly.*

This is the `[item, count]` flavour of §0.5, primitive 3.

```python
def removeDuplicates(s, k):
    stack = []                              # [char, count] pairs, adjacent chars always differ
    for c in s:
        if stack and stack[-1][0] == c:
            stack[-1][1] += 1
            if stack[-1][1] == k:
                stack.pop()                 # the run is complete: it disappears
        else:
            stack.append([c, 1])
    return ''.join(c * n for c, n in stack)
```

*The sentence:* **"The stack holds the fully reduced string so far as `[character, run length]` pairs, with every adjacent pair differing; the top is the only run the next character could extend."**

**List, not tuple.** `stack[-1][1] += 1` mutates in place, and tuples are immutable. **A `[char, count]` list is the right call precisely because you intend to mutate it**: a deliberate choice worth saying out loud.

**Complexity.** *"O(n) time, because each character is pushed at most once and popped at most once, and the final join writes at most n characters. O(n) space, because the stack holds at most one pair per character."*

The same carried-state shape on a genuinely nested input is a stack of `(count, string so far)` pairs; §Not covered here names the problem.

---

## The monotonic stack

**The one genuinely new idea in this module.** Everything before this section was a container used carefully. This is an algorithm.

**Worked on [Next Greater Element I](https://leetcode.com/problems/next-greater-element-i/) (LC 496)**, which is not in the drill set.

### The question it answers

> **"For each element, what is the nearest element to its right that is greater than it?"**

Plus its three siblings: nearest **smaller** to the right, nearest greater to the **left**, nearest smaller to the left. Four questions, one algorithm, one comparison flipped between them.

Problems rarely use those words. They say things like *"the next larger price"*, *"how far until something blocks this one"*, *"the first item to the right that beats it."*

**The brute force:** for each `i`, scan right until you find something bigger. O(n²), and quadratic on inputs that genuinely occur: a decreasing array makes every scan run to the end.

Run module 01's three escapes: **Remember** (store what?), **Order** (sorting destroys the "to its right" relationship, so no), **Reuse** (does the answer at `i` overlap with the answer at `i − 1`? Partly). None of the three quite fires. The right question here is a fourth one:

> **Which elements can I throw away, and when do I learn that I can?**

If a problem has no signal word, run this test: **does a new element permanently eliminate ones I'm still holding?** If yes, it is a monotonic stack.

### The insight, and why the stack ends up sorted

Walk left to right. When a new element `x` arrives, ask what `x` does to the elements behind it that are **still waiting** for their next greater element.

**Two things happen at once, and the second is the one people miss:**

> **1. If `x` is greater than a waiting element `y`, then `x` IS `y`'s answer.** It's to the right of `y`, it's greater than `y`, and it's the *nearest* such element, because we're scanning left to right and nothing in between qualified. `y` is finished, permanently.
>
> **2. And `y` can never be anybody else's answer either.** Any element further right that might have been answered by `y` will meet `x` first: `x` is closer to them *and* bigger than `y`. So `y` is not just finished; it is **useless**. Discard it.

So every new element does two jobs: it **answers** everyone it's bigger than, and it **removes** them.

**The sortedness is not imposed; it is derived:**

> **Every waiting element smaller than the newcomer gets removed. So everything that survives is greater than or equal to the newcomer. Then the newcomer goes on top. Therefore the stack is non-increasing from bottom to top, always, automatically: decreasing, except that equal values can sit together.** Not because anything was sorted, but because the smaller ones have already been answered and thrown away.

**And that is what makes the top the one you need next:**

> **The top is the SMALLEST of all the waiting elements**, so it is the first one any future element could answer. **And if the newcomer can't answer the top, it can't answer anything underneath it either**: everything below is bigger still. So the `while` loop can stop the moment the comparison fails.

That last sentence is the correctness proof of the early exit, **and** the reason the whole thing is O(n) instead of a repeated search. Say it out loud on every monotonic problem.

### The shape

```python
answer = [-1] * len(nums)        # the "no answer" default, decided up front
stack  = []                      # INDICES of elements still waiting, values non-increasing

for i, x in enumerate(nums):
    while stack and nums[stack[-1]] < x:
        j = stack.pop()
        answer[j] = x            # x is the next greater element of nums[j]
    stack.append(i)

# anything still on the stack has NO next greater element: answer[j] stays -1
```

Learn the shape, but derive the comparison from the sentence every time.

**⚠️ Store indices, not values.** You almost always need the position: for distances, for widths, for writing into `answer[j]`. And the conversion only runs one way: `nums[i]` gets the value from the index; nothing gets the index back from a value. Pushing values and then discovering you needed positions means starting over.

**The order you answer in is not the order you report in.** Elements are resolved in pop order, which is not their order in the input. An `answer` array indexed by position reconciles the two for free: `answer[j]` writes into a labelled box, so resolution order stops mattering. That is another reason to push the index: you need `j` to address the box.

> ⚠️ **`stack[-1]` is an index. `nums[stack[-1]]` is a value.** They appear one line apart, and comparing the wrong one produces code that runs and lies. Say which one every expression holds ([bug-checklist.md](../reference/bug-checklist.md#index-vs-value), §Index vs value).

**One pass, two answers.** With this stack (pop while `nums[stack[-1]] < x`) scanned left to right:

| At this moment | The answer you get |
|---|---|
| When `j` is **popped** by `x` | `x` is `j`'s **next greater element to the right** |
| When `i` is **pushed**, whatever is left on top | that is `i`'s **previous greater-or-equal element to the left** |

And the mirror image: an **increasing** stack answers *next smaller to the right* on pop and *previous smaller to the left* on push.

| Want | Pop while | Stack, bottom → top |
|---|---|---|
| Next **greater** to the right | `nums[stack[-1]] < x` | **non-increasing** |
| Next **smaller** to the right | `nums[stack[-1]] > x` | **non-decreasing** |

⚠️ **`<` against `<=` decides how ties behave.** With `<`, an equal element does not pop its twin, so "greater" means *strictly* greater and equal elements stay stacked. With `<=`, equal elements pop each other, and you get *greater or equal*. The push-time answer flips the opposite way: with `<` the top left behind is greater **or equal**, with `<=` it is strictly greater. Read the problem statement: *"a larger value"* is strict; *"at least as tall"* is not. **Decide it from the words; don't guess and patch.**

### Next Greater Element I, in full

*`nums1` is a subset of `nums2`, all values distinct. For each value in `nums1`, return its next greater element in `nums2`, or −1.*

```python
def nextGreaterElement(nums1, nums2):
    nxt   = {}                       # value -> its next greater element
    stack = []                       # values still waiting, decreasing bottom to top
    for x in nums2:
        while stack and stack[-1] < x:
            nxt[stack.pop()] = x
        stack.append(x)
    return [nxt.get(v, -1) for v in nums1]
```

```steps
title: Next Greater Element I: the monotonic stack
array: 2 1 4 3
- i=0 stack=[] nxt=[] | `nums2` is `[2, 1, 4, 3]`. This code pushes values, not indices. The top of the stack is on the right.
- i=0 stack=[2] | The stack is empty, so nothing pops. Push 2.
- i=1 stack=[2, 1] | 2 is not less than 1, so the `while` stops at once. Push 1.
- i=2 stack=[2] nxt=[1→4] | 4 is greater than the top, 1. Pop 1: its next greater element is 4.
- i=2 stack=[] nxt=[1→4, 2→4] | 4 is greater than 2 too. Pop 2: its next greater element is 4. The stack is empty, so the `while` stops.
- i=2 stack=[4] nxt=[1→4, 2→4] | Push 4.
- i=3 stack=[4, 3] nxt=[1→4, 2→4] | 4 is not less than 3, so nothing pops. Push 3.
- i=3 stack=[4, 3] nxt=[1→4, 2→4] | The loop ends. 4 and 3 were never popped, so they have no entry in `nxt`. `nxt.get(v, -1)` gives them −1.
```

**This one pushes values, not indices, and it's the exception that proves the rule.** The values are guaranteed distinct, so a value identifies an element uniquely; and the answer is a value, not a distance, so no position is ever needed. **Both conditions have to hold.** Drop either one and this breaks. A problem that asks *how far* to the answer needs indices, whatever else it says.

**The full sentence, delivered:**

> *"The stack holds the values of `nums2` that are still waiting for a next greater element, decreasing from bottom to top. It's decreasing because anything smaller than the current element has already been answered and removed. The top is the smallest of them, so it's the first one the current element can answer; and if the current element isn't greater than the top, it isn't greater than anything underneath either, so I can stop."*

Produce your own version of it, out loud, before the loop, on every problem in this family.

**⚠️ The leftovers.** `nxt.get(v, -1)`: the default is not defensive coding; **it is the answer for every element that was never popped.** On a decreasing `nums2` like `[5, 4, 3, 2, 1]`, the `while` never fires, `nxt` stays empty, and every answer is −1. That is correct. **Trace it.** If the code returns anything else, either the default is wrong or the survivors were dropped.

**Complexity, both lines:**

> *"O(n + m) time, where n is `len(nums2)` and m is `len(nums1)`. The `while` looks as if it makes the first loop quadratic, and it doesn't: each element of `nums2` is pushed exactly once and popped at most once, so across the whole run there are at most n pops. That's n pushes plus at most n pops, each O(1). Then one O(1) dict lookup per element of `nums1`."*
>
> *"O(n) space, because the only things I allocate are the stack and the dict, and each holds at most one entry per element of `nums2`. The worst case for the stack is a strictly decreasing `nums2`, where nothing is ever popped and all n elements are on it at once."*

⚠️ **Two input lengths make "O(n)" ambiguous.** Say O(n + m) and name what each letter is.

### When the answer is a width

If the question is *"how far"* rather than *"which one"*, the stack holds indices, and the arithmetic happens at **pop time**, from indices you hold at that moment. Nothing has to be tracked in a counter while an element waits. When an element is popped, two indices bound it: the one doing the popping, and the new top of the stack underneath it. A distance and a width are not the same arithmetic, and the new top may not exist: draw the stack at the moment of a pop and work out the off-by-one, and the empty-stack case, on paper.

And the leftovers problem gets an elegant escape:

> **A sentinel at the end of the input, chosen so that it pops everything, deletes the entire "what about the survivors" branch.** A special case you can design away beats a special case you handle.

Work out for yourself what the sentinel has to be: it follows directly from the pop condition.

### A missing precondition is a missing first line

Some monotonic problems only become monotonic once the input is in the right order. If the algorithm you have in mind needs an order the input doesn't come in, **that is not a flaw in the algorithm: it is a missing first line.** *"What if this were sorted?"* is one of the highest-yield questions there is. Establish the precondition, pay the O(n log n), and finish the move; don't abandon the algorithm because the input didn't arrive ready for it.

---

## When the stack is only a counter

> **When every item on a stack is identical, the stack is just a counter.** `"((("` needs no characters stored, only the depth, `3`.

**If you catch yourself pushing the same value over and over, ask whether an integer would do.** It applies to validity with a single bracket type and to nesting depth.

It is also the reason one problem that sits in many stack lists has no stack in it at all. Generating every valid arrangement of `n` pairs of parentheses is backtracking wearing a stack's name: the only stack involved is the call stack, and the "stack" it prunes against is two counters. You'll see it in module 07 ([07-backtracking.md](07-backtracking.md)), where it belongs.

---

## The queue: first in, first out

The other bottom row of §0.1's table. A stack hands back the newest unfinished item; a queue hands back the **oldest**.

### FIFO against LIFO

Push A, B, C onto a stack and it hands back C, B, A. Add A, B, C to a queue and it hands back A, B, C. **LIFO reverses order; FIFO preserves it.**

Say the right one out loud. Bracket matching is LIFO: `([)]` is invalid *precisely because* closing in first-in-first-out order isn't allowed. Saying "FIFO" while writing a stack reads as not knowing which structure you just chose.

### `pop(0)` against `popleft`

A Python `list` is a row of numbered slots ([01-arrays-hashing.md](01-arrays-hashing.md#the-list-a-row-of-numbered-slots)). Its right end is cheap: `append` writes past the last element and `pop()` drops it, and nothing shifts. Its left end is expensive: `pop(0)` removes slot 0, and **every other element shifts left one slot**. That is O(n) for one removal, and a loop that dequeues n items that way is **O(n²)**.

`deque.popleft()` is O(1). CPython's `deque` is a doubly linked list of fixed-size blocks, so adding or removing at either end touches one block and never shifts anything. The price is the middle: `q[i]` has to walk the blocks, O(n) toward the centre ([python-toolkit.md](../reference/python-toolkit.md#1-deque-the-queue), §1. `deque`: the queue).

| Need | Use | Why |
|---|---|---|
| Add at one end, remove at the **other** (a queue) | **`deque`** | `popleft()` is O(1); `pop(0)` is O(n) |
| Add and remove at the **same** end (a stack) | **`list`** | the right end was never the problem |
| Index into the middle | **`list`** | `deque` indexing is O(n) toward the middle |

⚠️ **`stack.pop()` and `stack.pop(0)` are one character apart and they are different data structures.** `pop()` is a stack, O(1). `pop(0)` is a queue, O(n), and it silently turns an O(n) algorithm into O(n²). No test on a small input will tell you.

A `deque` *works* as a stack, and `append` with `pop` on it is O(1) too. But a stack touches one end, and that end is a list's cheap one, so `list` is the plain choice. Reaching for `deque` on a stack problem usually means a tool carried from the last problem without re-deriving why it was needed.

### Which item comes out: newest, oldest, smallest

| You need the… | Structure | Python | Where |
|---|---|---|---|
| **newest** unfinished item | stack | `list`: `append`, `pop()` | this module |
| **oldest** unfinished item | queue | `deque`: `append`, `popleft()` | this module; breadth-first search is a queue |
| **smallest** item, whenever it arrived | heap | `heapq`: `heappush`, `heappop` | later, module 10 |

```compare
title: Which item comes out
option: Stack (LIFO)
  Hands back: the newest item
  Add at: the right end
  Remove from: the right end
  Python: `list` with `append` and `pop()`
  Drives: the monotonic stack and bracket matching
option: Queue (FIFO)
  Hands back: the oldest item
  Add at: the right end
  Remove from: the left end
  Python: `deque` with `append` and `popleft()`
  Drives: breadth-first search and Dota2 Senate
```

You'll see the queue again in module 06 ([06-trees.md](06-trees.md)), where it is the frontier of every breadth-first search, and the heap comes back in module 10 ([10-heaps.md](10-heaps.md)). Swapping the stack for a queue in the same loop is the whole difference between depth-first and breadth-first.

### A queue in action

**Worked on [Dota2 Senate](https://leetcode.com/problems/dota2-senate/) (LC 649)**, which is not in the drill set.

*Senators from two parties, `'R'` and `'D'`, act in turn, round after round, in the order of the string. On its turn, a senator may ban one opponent from all future rounds. When only one party is left, it wins. Every senator plays optimally.*

The optimal move is to ban the **next opponent due to act**, since that is the opponent who would otherwise act first against your side. So the question at every step is *who acts next on each side?*: the oldest senator still waiting, which is a queue.

```python
from collections import deque

def predictPartyVictory(senate):
    n = len(senate)
    radiant = deque(i for i, s in enumerate(senate) if s == 'R')   # turn positions, in order
    dire    = deque(i for i, s in enumerate(senate) if s == 'D')
    while radiant and dire:
        r, d = radiant.popleft(), dire.popleft()   # the next to act on each side
        if r < d:
            radiant.append(r + n)                  # r acts first, bans d, and acts again next round
        else:
            dire.append(d + n)
    return "Radiant" if radiant else "Dire"
```

*The sentence:* **"Each queue holds its side's senators still in the game, as turn positions in the order they act; the front is that side's next to act, and the earlier of the two fronts acts first."**

The `+ n` is the queue doing its job: a senator who acts goes to the **back**, behind everyone still waiting, with a position that sorts after the whole current round. Arrival order is turn order, so nothing has to be searched or compared beyond the two fronts.

**Complexity.** *"O(n) time, because each iteration of the `while` bans one senator for good, so it runs at most n times, and each iteration is two `popleft`s and one `append`, all O(1). O(n) space, because the two queues together hold at most n positions."* With `list.pop(0)` in place of `popleft`, the same code is O(n²).

### Two stacks make a queue

Row 8 of the drill set builds a queue from two stacks: an `in` stack that takes arrivals and an `out` stack that serves departures. The invariant to hold is **everything in `out` is older than everything in `in`, and, whenever `out` is non-empty, the top of `out` is the oldest item of all.** The rest is the drill. Its cost is §0.7's amortised argument in a second costume: each element moves from one stack to the other at most once.

---

## When not to reach for a stack

Half of choosing a tool is rejecting the neighbours:

| If you need | Use |
|---|---|
| the **oldest** unresolved item | a **queue** (`deque`) |
| the **largest** item, whenever it arrived | a **heap** |
| an **arbitrary** item, by key | a **dict** or **set** |
| both ends | a **deque** |
| the most **recent** unresolved item | **a stack** |

**Two self-checks that catch a stack you didn't need:**

- **If you push and pop within the same iteration**, you needed a variable, not a stack.
- **If the stack never holds more than one item**, you needed a variable, not a stack.

Both are a technique set up and not used: the setup line ran, the technique didn't. Ask of the stack what you ask of every other variable: *if I delete this and use a plain variable, does the answer change?*

---

## Common stack and queue mistakes

Ordered by how often each happens.

| Mistake | What you see | Entry |
|---|---|---|
| No invariant sentence before the loop | the `while` comparison written by feel; an increasing stack answering a next-greater question | §0.5, §Say the sentence before the loop body |
| Leftovers at the end ignored | `"((("` accepted; an element with no next greater element gets no answer | §0.6 |
| A guard copied from the last problem | a "fail when empty" guard in a problem where empty means "skip" | §The path stack; [bug-checklist.md](../reference/bug-checklist.md#guards-copied-from-another-problem), §Guards copied from another problem |
| `pop()` or `[-1]` on an empty stack | `IndexError` | §0.4; `and` short-circuits, so `stack and …` must come first ([bug-checklist.md](../reference/bug-checklist.md#the-guard-asymmetry), §The guard asymmetry) |
| `if stack[-1]:` where `0` is a legal item | a real item read as an empty stack; never crashes | §0.4 |
| Pushed values, needed indices | the distance can't be computed; the solution restarts | §The monotonic stack |
| `stack[-1]` and `nums[stack[-1]]` mixed up | an index compared against a value | [bug-checklist.md](../reference/bug-checklist.md#index-vs-value), §Index vs value |
| Popped when you meant to peek | the arithmetic is right and the total is wrong | §The operand stack; [bug-checklist.md](../reference/bug-checklist.md#a-query-that-mutates), §A query that mutates |
| Popped values named after arrival order | the wrong subtraction reads as the right one | [bug-checklist.md](../reference/bug-checklist.md#names-that-describe-arrival-order-not-role), §Names that describe arrival order, not role |
| One variable where each slot needs its own answer | correct until the first pop, then wrong | §0.5, primitive 3; [bug-checklist.md](../reference/bug-checklist.md#a-structure-that-cant-express-the-answer), §A structure that can't express the answer |
| A `<` where the statement wanted `<=`, or the reverse | ties handled the wrong way | §The monotonic stack |
| Claiming O(n²) for your own monotonic stack | optimal code described as the brute force | §0.7, §The amortised argument |
| `list.pop(0)` as a queue | works; quadratic, and times out on large inputs | §The queue |
| `deque` used as a stack | works; reads as a habit carried from the last problem | §The queue |
| `isdigit()` to detect a number | `"-3"` classified as an operator | §The operand stack |
| Operand order on `−` and `÷` | `+` and `*` pass, `−` and `/` are wrong | §The operand stack |
| `//` where truncation toward zero was wanted | passes on positive inputs, fails the test set | §The operand stack |
| A stack that never holds more than one item | the technique was set up and not used | §When not to reach for a stack |
| Both arms of an `if` push the same thing | duplicated code that hides which test matters | [bug-checklist.md](../reference/bug-checklist.md#dead-branching-both-arms-assign-the-same-value), §Dead branching: both arms assign the same value |
| Dead code | a `count` or `depth` maintained alongside the stack and never read; a cast that changes nothing; an `enumerate` index never used | [bug-checklist.md](../reference/bug-checklist.md#dead-code-in-disguise-the-no-op-cast-and-the-unused-index), §Dead code in disguise: the no-op cast and the unused index |

---

## Not covered here

**Deliberately absent, because they are drill material:** the running-summary stack (the principle is in §0.5, primitive 3), the histogram rectangle, and the fleet reading of a monotonic stack.

**Worth knowing exists:**

- **Iterative tree traversal** ([LC 94](https://leetcode.com/problems/binary-tree-inorder-traversal/), [LC 173 Binary Search Tree Iterator](https://leetcode.com/problems/binary-search-tree-iterator/)): *"write it without recursion"* means *"make the call stack explicit."* You'll see it in module 06 ([06-trees.md](06-trees.md)).
- **Decode String** ([LC 394](https://leetcode.com/problems/decode-string/)): a stack of `(count, string so far)` pairs, the carried-state shape of §0.5 on a genuinely nested input.
- **The calculator family** ([LC 224](https://leetcode.com/problems/basic-calculator/), [LC 227](https://leetcode.com/problems/basic-calculator-ii/)): infix with parentheses and precedence. Hard; the usual shape saves the running result and sign on a stack at each `(`.
- **The monotonic deque** ([LC 239 Sliding Window Maximum](https://leetcode.com/problems/sliding-window-maximum/)): the monotonic stack where elements also expire from the *other* end, because they've left the window. It is where `deque` comes back for a structure that isn't a plain queue, and the cleanest illustration of why a stack is the one-ended special case. You'll see it in module 03 ([03-two-pointers-sliding-window.md](03-two-pointers-sliding-window.md)).
- **Trapping Rain Water** ([LC 42](https://leetcode.com/problems/trapping-rain-water/)): solvable with a monotonic stack *and* with converging pointers, which you'll see in module 03 ([03-two-pointers-sliding-window.md](03-two-pointers-sliding-window.md)). A good "give two solutions and compare" problem once the monotonic stack is solid.

---

## Drill set — cold, no IDE, no running

**Solutions are not in this file.** Every shape you need is in §0 and the sections above, taught on other problems.

### The stack half

| # | Problem | Focus |
|---|---|---|
| 1 | [Valid Parentheses](https://leetcode.com/problems/valid-parentheses/) (LC 20) | **The canonical matching stack.** The three questions of §Resolve against the top, answered in writing first. ⚑ **Checkpoint** |
| 2 | [Min Stack](https://leetcode.com/problems/min-stack/) (LC 155) | **Carried state**, §0.5, primitive 3. The obligation: `getMin` in O(1), and still right after any sequence of pops. Design, not an algorithm. Name each structure after its role |
| 3 | [Evaluate Reverse Polish Notation](https://leetcode.com/problems/evaluate-reverse-polish-notation/) (LC 150) | The operand stack. Traps: operand **order** on `−` and `÷`, `//` against truncation, and negative numbers in the input |
| 4 | [Daily Temperatures](https://leetcode.com/problems/daily-temperatures/) (LC 739) | **The monotonic rep.** The answer is a distance, so indices are mandatory. ⚑ **Checkpoint** |
| 5 | [Car Fleet](https://leetcode.com/problems/car-fleet/) (LC 853) | **Monotonic in disguise.** Establish the precondition first, then work out what a "fleet" is in terms of arrival times |
| 6 | [Largest Rectangle in Histogram](https://leetcode.com/problems/largest-rectangle-in-histogram/) (LC 84) | **Stretch**, the hardest in the module. Widths, so indices *and* the sentinel |

### The queue half

| # | Problem | Focus |
|---|---|---|
| 7 | [Number of Recent Calls](https://leetcode.com/problems/number-of-recent-calls/) (LC 933) | **The queue, undisguised.** Only recent calls count: which end do old ones leave from, and why is that the cheap end? ⚑ **Checkpoint** |
| 8 | [Implement Queue using Stacks](https://leetcode.com/problems/implement-queue-using-stacks/) (LC 232) | Two stacks, one queue. Hold the invariant from §The queue, and give the amortised argument of §0.7 for each operation |
| 9 | [Implement Stack using Queues](https://leetcode.com/problems/implement-stack-using-queues/) (LC 225) | The mirror image. Decide which operation pays, and say its cost |
| 10 | [Design Circular Queue](https://leetcode.com/problems/design-circular-queue/) (LC 622) | A queue on a fixed-size list, with no `deque`. Decide how "full" is told apart from "empty" before writing anything |

**The order.** Rows 1 to 3 are the plain stack: matching, carried state, the operand stack. Rows 4 to 6 are the monotonic family, ramping in difficulty. Row 6 is a stretch, not a checkpoint: do it once rows 4 and 5 are clean. Rows 7 to 10 are the queue: the structure itself, then two designs that build one discipline out of the other, then a queue with no `deque` to lean on. Generate Parentheses, which many stack lists include, is backtracking; you'll see it in module 07 ([07-backtracking.md](07-backtracking.md)).

**⚑ Checkpoint at row 1.** LC 20 is the smallest problem that contains the whole stack topic: what goes on, what comes off, what an empty stack means mid-loop, and what a non-empty stack means at the end. Clean, with the sentence said first: move on. Not clean: reread §0.5 and §Resolve against the top rather than pushing on.

**⚑ Checkpoint at row 4.** The monotonic stack is the module's reason for existing. The bar is not "it passes": it is **the sentence, including the second half (*why is it decreasing?*), before the code, and the amortised argument out loud after it.** If that doesn't come out, do a second rep on [LC 901 Online Stock Span](https://leetcode.com/problems/online-stock-span/) before row 5.

**⚑ Checkpoint at row 7.** The queue half in one problem: the sentence for a queue (*what is at the front, and why is it the oldest I still need?*), `popleft` and not `pop(0)`, and the complexity in the template. If it doesn't come out clean, reread §The queue before rows 8 to 10.

**Spares, if a shape needs a second rep:** [LC 901 Online Stock Span](https://leetcode.com/problems/online-stock-span/) (monotonic, the cleanest second rep) · [LC 503 Next Greater Element II](https://leetcode.com/problems/next-greater-element-ii/) (monotonic on a *circular* array) · [LC 394 Decode String](https://leetcode.com/problems/decode-string/) (nested input, carried state) · [LC 921 Minimum Add to Make Parentheses Valid](https://leetcode.com/problems/minimum-add-to-make-parentheses-valid/) (the counter compression) · [LC 42 Trapping Rain Water](https://leetcode.com/problems/trapping-rain-water/) (two solutions, compare them) · [LC 1700 Number of Students Unable to Eat Lunch](https://leetcode.com/problems/number-of-students-unable-to-eat-lunch/) (a queue simulation).

*Solved in the sections above, so from memory only:* [LC 1047](https://leetcode.com/problems/remove-all-adjacent-duplicates-in-string/) · [LC 71](https://leetcode.com/problems/simplify-path/) · [LC 682](https://leetcode.com/problems/baseball-game/) · [LC 1209](https://leetcode.com/problems/remove-all-adjacent-duplicates-in-string-ii/) · [LC 496](https://leetcode.com/problems/next-greater-element-i/) · [LC 649](https://leetcode.com/problems/dota2-senate/).

## Before you submit anything

Every problem, no exceptions:

1. **Name the pattern and the signal that pointed to it**, before any code. If there is no signal word, run the test: *does a new element permanently eliminate ones I'm still holding?*
2. **Say the sentence, before the loop body:** *what is on the stack, and why is the top the one I need next?* On a monotonic problem it has a second half: *and why is it sorted?* On a queue: *what is at the front, and why is it the oldest I still need?*
3. **What does an EMPTY stack mean in this problem?** Fail, skip, or a default answer? Answer it before you write the guard, and never copy the guard from the last problem.
4. **What do LEFTOVERS on the stack at the end mean?** They are part of the answer. Pre-fill the output with the "no answer" value.
5. **Indices or values?** Values only if they're distinct *and* no position is ever needed.
6. **Name every variable after its role**, not its arrival order ([bug-checklist.md](../reference/bug-checklist.md#names-that-describe-arrival-order-not-role), §Names that describe arrival order, not role).
7. Write it. **Branch on the thing that determines the action**, so no arm duplicates another.
8. Run [bug-checklist.md](../reference/bug-checklist.md#the-30-second-pass), §The 30-second pass, then the mistakes table above, then: **for every variable I assigned, where is it read?** Casts and unused `enumerate` indices count.
9. **Trace the degenerate cases, not the happy path:** empty input · `"((("` · `")"` · one element · a strictly **decreasing** array.
10. **Say the complexity in the template, unprompted, time and space, with the worst case named.** If there's a `while` inside the `for`, give the amortised argument out loud: pushed once, popped at most once, at most 2n operations in total.

If you carry only two things into every submission, carry **the sentence and the complexity**.

---

## Self-check answers

1. **Everything except the end is taken away**: no indexing, no slicing, no searching the middle. What it buys is that the item you need next is **always at a known place**, the top, so finding it is O(1) instead of a search. That works because "the most recent unresolved item" is exactly the shape of nesting.
2. A `list` is a row of slots. **`pop()` drops the last slot and nothing moves; `pop(0)` removes slot 0 and every other element shifts left one place**, which is O(n), and O(n²) inside a loop over n items. For the front, use **`collections.deque`**, whose `popleft()` is O(1).
3. The newest: a **stack** (`list`). The oldest: a **queue** (`deque`). The smallest: a **heap** (`heapq`). The stack and the queue cost nothing to maintain because **recency and age are properties of when items arrived**, and arrival order is recorded for free by appending; a heap has to keep comparing items to stay in order.
4. **Each element is pushed exactly once and, once popped, never comes back**, so there are at most n pops across the whole run, not n per iteration. That is at most 2n O(1) operations in total: the `while` does n work overall, spread unevenly across the iterations.
5. **Every waiting element smaller than the newcomer is answered and removed before the newcomer is pushed**, so whatever survives is greater than or equal to it: the stack is non-increasing as a consequence. The top is therefore the **smallest** waiting element; if the newcomer can't beat it, it can't beat anything below it, so the loop can stop.
6. Only when **both** hold: the values are **distinct**, so a value identifies its element, **and** no position is ever needed, because the answer is a value rather than a distance or a width. Otherwise push indices and read values through them.
7. It is wrong whenever **the top is `0`** (or any other falsy item, such as `""`): a real item is read as an empty stack, and nothing crashes. The fix is to test the stack itself: **`if stack:`**.
8. The items still on the stack **were never resolved and never will be**. They are part of the answer, not debris: a check at the end ("anything left means failure") or a "no answer" default already in the output for each of them.
