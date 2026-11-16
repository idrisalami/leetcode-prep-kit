# Module 03: Two pointers and the sliding window

<!-- toc -->
**Contents**

- [0.1 Prerequisites and the one question](#01-prerequisites-and-the-one-question)
- [0.2 The structure and how it works](#02-the-structure-and-how-it-works)
  - [Shape A: converging](#shape-a-converging)
  - [Shape B: same direction, the window](#shape-b-same-direction-the-window)
  - [Which shape?](#which-shape)
- [0.3 Vocabulary](#03-vocabulary)
- [0.4 Operations and their cost](#04-operations-and-their-cost)
- [0.5 The primitives](#05-the-primitives)
  - [The invariant is the correctness tool](#the-invariant-is-the-correctness-tool)
- [0.6 Inputs that break it](#06-inputs-that-break-it)
- [0.7 Complexity, out loud](#07-complexity-out-loud)
- [0.8 Signals](#08-signals)
- [0.9 Self-check](#09-self-check)
- [Converging pointers](#converging-pointers)
  - [The symmetric case: no sort needed](#the-symmetric-case-no-sort-needed)
  - [The limiting side: one end is finished](#the-limiting-side-one-end-is-finished)
  - [Sorted input, and triplets](#sorted-input-and-triplets)
- [The sliding window](#the-sliding-window)
  - [The variable window, minimising](#the-variable-window-minimising)
  - [The variable window, maximising](#the-variable-window-maximising)
  - [The fixed window](#the-fixed-window)
  - [The sentinel](#the-sentinel)
- [When the window needs its maximum](#when-the-window-needs-its-maximum)
- [Common pointer and window mistakes](#common-pointer-and-window-mistakes)
- [Drill set — cold, no IDE, no running](#drill-set--cold-no-ide-no-running)
- [Also on the practice list](#also-on-the-practice-list)
- [Before you submit anything](#before-you-submit-anything)
- [Self-check answers](#self-check-answers)
<!-- /toc -->

This module covers two indices moving through one array: **converging** pointers that walk in from both ends, and the **sliding window**, two pointers moving the same direction. Both are ways to look at the pairs, or the runs, of an array without a nested loop over all of them. Each is one of the escapes from module 01: converging pointers spend **Order**, and the window is **Reuse**.

The drill set at the bottom is deliberately **not solved anywhere in this file**. Every example the sections walk through uses a problem outside the drill set.

**How to use it.** Read §0, then answer the self-check in §0.9 and re-read the parts of §0 behind any question you miss. Then work through the sections from converging pointers to the window maximum, and do the drill set cold.

| Section | What it gives you |
|---|---|
| §0, the foundation | the one question, the two shapes and why each one is linear, the vocabulary, what each operation costs, the three templates, the inputs that break them, the signals |
| Converging pointers | the discard argument on two problems, and how it extends to triplets |
| The sliding window | the variable window in both directions, the fixed window, the sentinel |
| When the window needs its maximum | why `max(window)` is too slow, and the deque that replaces it |
| Common pointer and window mistakes | the bugs, each linked to its checklist entry or section |
| Drill set | the problems, with the checkpoint |
| Before you submit anything | the checklist |

---

## 0.1 Prerequisites and the one question

| You need | From | Used here for |
|---|---|---|
| Counting cost, and amortised cost | [00-before-you-start.md](00-before-you-start.md#big-o-from-zero), §Big-O from zero | §0.2 and §0.7: why the window's nested `while` is still linear |
| The three escapes: Remember, Order, Reuse | [01-arrays-hashing.md](01-arrays-hashing.md#the-three-escapes-remember-order-reuse) | naming which escape each shape spends |
| Sorting costs O(n log n), and that is free against O(n²) | [01-arrays-hashing.md](01-arrays-hashing.md#sorting-as-a-tool) | converging pointers on an array you sort first |
| A frequency map, and prefix sums | [01-arrays-hashing.md](01-arrays-hashing.md#05-the-primitives), §0.5 The primitives | the window's state, and the fallback when the window can't work |
| The deque, and the monotonic stack's amortised argument | [02-stacks-queues.md](02-stacks-queues.md) | §When the window needs its maximum |

**The one question this module answers:**

> *The obvious solution tries every pair (i, j), or every run `nums[i..j]`: O(n²) of them. How do I move two indices so that each one only ever goes forward, and every pair I skip is one I can prove doesn't matter?*

The answer has two shapes. Which one applies depends on a single word in the statement, and most of this module is learning to see it.

## 0.2 The structure and how it works

There is no new data structure here: the array is the structure, and you hold two indices into it. What changes is **how the two indices move**, and that comes in exactly two shapes. Confusing them is a common way to write plausible code that is wrong.

### Shape A: converging

`lo` starts at the left end, `hi` at the right, and they move toward each other until they meet.

```python
lo, hi = 0, len(nums) - 1
while lo < hi:
    ...                 # decide using nums[lo] and nums[hi]
    lo += 1             # or
    hi -= 1             # one of them, based on the decision
```

```steps
title: Pair sum on a sorted array, target 10
array: 1 2 4 6 8 11
- lo=0 hi=5 | Start at both ends.
- lo=0 hi=5 | 1 + 11 = 12 > 10: 11 is too big for any partner left. hi -= 1.
- lo=0 hi=4 | 1 + 8 = 9 < 10: 1 is too small for any partner left. lo += 1.
- lo=1 hi=4 | 2 + 8 = 10: found the pair (1, 4).
```

**Why it works.** Think of every pair `(lo, hi)` as a cell in an n × n grid. The brute force visits every cell. Converging pointers visit one cell per step, and each step **rules out a whole row or column** of the grid at once. On a sorted array looking for two values that add to a target: if `nums[lo] + nums[hi]` is too small, then `nums[lo]` paired with *anything* is too small, because `nums[hi]` was the largest partner still available. So `lo` is finished, and you discard it in one comparison.

**It needs an order, or a symmetry.** The discard argument only holds when the array is sorted, or when the property is symmetric from the two ends, like a palindrome, or when one side provably limits the answer, like the shorter of two walls. Without one of those, moving a pointer throws away pairs you never checked.

**Cost.** `hi - lo` shrinks by at least one per iteration, so the loop runs at most n − 1 times: **O(n)**, plus O(n log n) if you had to sort first.

### Shape B: same direction, the window

`left` and `right` both start at the left and both move right. Everything between them, `nums[left..right]`, is the **window**.

```python
left = 0
for right in range(len(nums)):
    ...                      # extend: bring nums[right] into the window
    while <window is invalid>:
        ...                  # shrink: remove nums[left]
        left += 1
    ...                      # record the answer for this window
```

**It needs two things.** The answer must be **contiguous**, a run of adjacent elements. And the rule that makes a window valid must be **monotone**: adding an element can only break validity, and removing one can only restore it. "Sum at most t, all values positive" is monotone. "Sum exactly t, values may be negative" is not: adding a negative value can turn an invalid window valid. Then the window can't decide when to shrink, and the fallback is prefix sums with a hash map from module 01.

**Cost.** There is a `while` inside a `for`, and the loop is still **O(n)**, because **`left` only ever increases, and it never runs past the end of the array.** Over the whole run, `left` advances at most n times *in total*, however those steps are spread across iterations of the `for`. Every index enters the window once, when `right` reaches it, and leaves at most once, when `left` passes it. That is at most 2n moves.

This is the same amortised argument as the monotonic stack in [02-stacks-queues.md](02-stacks-queues.md#the-amortised-argument), §The amortised argument, with two pointers instead of a stack: each element is pushed once and popped at most once, so the inner loop's total work is bounded by n, not by n per outer step.

> Most interviewers ask *"isn't that nested loop quadratic?"* to see whether you know this. The answer: *"No. The inner loop's total work across all iterations is bounded by n, because `left` never moves backwards."* Have that sentence ready.

### Which shape?

| In the statement | Shape |
|---|---|
| a sorted array, or one you may sort · "a pair or triplet summing to X" · "palindrome" · two ends that limit each other | **A, converging** |
| "contiguous subarray" · "substring" · "longest or shortest run such that…" · "every window of size k" | **B, the window** |

The word **"contiguous"** or **"substring"** in a statement is close to a guarantee that the window applies, provided the rule is monotone.

```compare
title: Which shape?
option: Shape A, converging
  Start: `lo` at the left end, `hi` at the right end
  Moves: toward each other, one of them per step
  Loop: `while lo < hi`
  Needs: sorted order, a symmetry, or one side that limits the answer
  Cost: O(n), plus O(n log n) if you had to sort
  Signal words: sorted array, pair or triplet summing to X, palindrome
option: Shape B, the window
  Start: `left` and `right` both at the left end
  Moves: both go right, `left` never moves back
  Loop: `for right in ...` with `while <window is invalid>` inside
  Needs: a contiguous answer and a monotone validity rule
  Cost: O(n), `left` advances at most n times in total
  Signal words: contiguous subarray, substring, longest or shortest run, window of size k
```


## 0.3 Vocabulary

| Term | Meaning |
|---|---|
| **pointer** | here, an index into the array: `lo`, `hi`, `left`, `right`. Not a memory address |
| **converging** | two pointers starting at opposite ends and moving toward each other |
| **same direction** | two pointers both moving left to right, `left` never ahead of `right` |
| **window** | the run `nums[left..right]` between two same-direction pointers |
| **valid** | the window satisfies the problem's rule: the sum is at most t, at most k zeros are inside, and so on |
| **monotone rule** | a rule where growing the window can only break validity and shrinking it can only restore it |
| **fixed window** | a window whose size k never changes: one element in, one out, every step |
| **variable window** | a window that grows on the right and shrinks on the left as validity demands |
| **window state** | the few values that describe the current window without rescanning it: a sum, a count, a frequency map |
| **discard** | moving a pointer past an index because every pair it could still form is provably no better |
| **anchor** | an element fixed by an outer loop while two pointers search the rest |
| **sentinel** | a starting value that no real answer can equal, such as `float('inf')` for a minimum |
| **amortised** | averaged over the whole run: one step may do a lot of work, the total is still bounded |

## 0.4 Operations and their cost

**n** is the length of the array; **k** is the window size.

| Operation | Python | Big-O | Trap |
|---|---|---|---|
| Read an element under a pointer | `nums[lo]`, `nums[right]` | O(1) | `nums[hi]` with `hi = len(nums)` is out of range; start at `len(nums) - 1` |
| Move a pointer | `lo += 1`, `hi -= 1` | O(1) | moving it inside the wrong branch, or in two branches in one iteration |
| Update the window state | `total += nums[right]`, `total -= nums[left]` | O(1) | forgetting the matching update when `left` moves |
| Recompute the window from scratch | `sum(nums[left:right + 1])` | **O(k)** | inside the loop it is O(n · k), which is the brute force again. Carry the state instead |
| Copy the window | `nums[left:right + 1]` | **O(k)** | a slice is a copy; record `left` and `right`, slice once at the end |
| Max or min of the window | `max(nums[left:right + 1])` | **O(k)** | the same trap; §When the window needs its maximum |
| Add or remove a count in the window's frequency map | `counts[c] += 1`, `counts[c] -= 1` | O(1) average | a count that reaches 0 is still a key, so `len(counts)` overcounts; `del counts[c]` when it hits 0 |
| Window length | `right - left + 1` | O(1) | `right - left` is one short for a closed window |
| Sort before converging | `nums.sort()` | O(n log n) | sorting moves elements: an answer in original indices needs them carried along |
| Deque push and pop at either end | `dq.append(i)`, `dq.pop()`, `dq.popleft()` | O(1) | `list.pop(0)` is the O(n) version |

## 0.5 The primitives

Three templates cover the module. Each has an invariant: a statement true at the top of every iteration. Choose it before writing the body; every line of the body then has one job, which is to leave it still true.

**1. Converging pointers.** The Shape A template from §0.2.

*Invariant:* if an answer exists, it lies inside `[lo, hi]`: every pair involving an index outside that range has been checked or ruled out.

**2. The variable window.** The Shape B template from §0.2, with the state kept in O(1) variables or a small map.

*Invariant:* when the loop reaches "record", `nums[left..right]` is valid, and the window state describes exactly that range.

**The direction of the shrink depends on the goal.** To **minimise** the window, shrink *while it is still valid*, recording inside the `while` before each shrink. To **maximise** it, shrink *while it is invalid*, and record after the `while`, once validity is restored.

**3. The fixed window.** Both ends move together, one element in and one out:

```python
window = sum(nums[:k])
best = window
for right in range(k, len(nums)):
    window += nums[right] - nums[right - k]     # add the new, drop the old
    best = max(best, window)
```

*Invariant:* at the end of each iteration, `window` is the sum of exactly the k elements `nums[right - k + 1..right]`. The first `sum` is O(k) once; every step after it is O(1), so the whole loop is O(n).

### The invariant is the correctness tool

| Technique | Its invariant |
|---|---|
| Converging pointers | *"If an answer exists, it lies inside `[lo, hi]`."* |
| Variable window | *"`nums[left..right]` satisfies the rule."* |
| Fixed window | *"`window` is the sum of the last k elements."* |
| Running state, from module 01 | *"`current` is the best sum of a subarray ending exactly at `i`."* |
| Frequency map | *"`counts` holds the exact count of every value inside the window."* |

It matters for two reasons.

**1. It makes tracing fast.** You don't verify the whole algorithm. You check one thing: *"the invariant held coming in; does it still hold going out?"* If yes, induction does the rest, and a five-minute trace becomes a thirty-second one.

**2. It's what you say out loud.** *"I'm keeping the invariant that everything between left and right is valid, so when I extend right and it breaks, I shrink from the left until it's valid again."* That sentence shows the code isn't an accident, and most interviewers weigh it as heavily as the code.

**Off-by-ones are invariant violations.** `while lo < hi` against `while lo <= hi` is decided by the invariant. With converging pointers looking for a *pair*, `lo == hi` would pair an element with itself, so the loop stops at `lo < hi`. A closed range `[lo, hi]` that can hold a single answer needs `<=`; a half-open `[lo, hi)` needs `<`. Decide the range, and the operator follows instead of being guessed ([bug-checklist.md](../reference/bug-checklist.md#off-by-ones-derive-never-freehand), §Off-by-ones: derive, never freehand).

> ⚠️ **You'll see this again in module 04, on binary search**, where the choice between `lo < hi` and `lo <= hi` is the whole difficulty.

## 0.6 Inputs that break it

| Input | What breaks | Check |
|---|---|---|
| The empty array | `len(nums) - 1` is `-1`; `sum(nums[:k])` is `0` and the loop never runs | does the code return the right thing when no pair or window exists? |
| One element | converging: `lo == hi` at once, so the loop body never runs | is "no pair" the right answer, or does a single element count? |
| k larger than the array | the fixed window's first `sum` covers fewer than k elements and returns a wrong "best" | read the constraints: is `k <= len(nums)` promised? |
| No valid window at all | a minimum that starts at `float('inf')` is returned as `inf` | convert the sentinel back before returning: `best if best != float('inf') else 0` |
| Negative values in a sum window | the rule is no longer monotone; shrinking can make the sum larger | prefix sums with a hash map, from module 01 |
| An unsorted array with converging pointers | the discard argument fails, and pairs are skipped unchecked | sort first, or confirm the property is symmetric |
| Repeated values with converging pointers | the same answer is reported more than once | after sorting, skip a value equal to its neighbour |
| A pair that must use two different indices | `lo == hi` pairs an element with itself | `while lo < hi`, never `<=`, when the answer is a pair |

## 0.7 Complexity, out loud

| Shape | Time | Space |
|---|---|---|
| Converging, input already sorted or symmetric | O(n) | O(1) |
| Converging after a sort | O(n log n) | O(1) extra, plus the sort's own up to O(n) |
| Anchor plus converging, for triplets | O(n²): O(n) inside O(n) | the same |
| Fixed or variable window, O(1) state | O(n) | O(1) |
| Window with a frequency map | O(n) | O(m), where m is the number of distinct values the window can hold: O(1) for a fixed alphabet |

**The sentence to have automatic:**

> *"Linear time: `right` moves n times and `left` moves at most n times in total, so it's 2n pointer moves. Constant extra space; the only state is the running total."*

**Say the alphabet.** A window over lowercase letters with a frequency map uses O(26) space, which is O(1). Over arbitrary integers it is O(n). Saying which, and why, is the difference between a claim and an answer.

**Triplets are not cubic.** Fix one element with an outer loop, and converge on the rest: O(n) work for each of n anchors is **O(n²)**, which beats the O(n³) triple loop. The sort, at O(n log n), disappears under it.

## 0.8 Signals

| In the statement | Reach for | Where |
|---|---|---|
| "sorted array", "find a pair with sum X" | converging pointers | §0.2, Shape A |
| "palindrome", "compare from both ends" | converging pointers, no sort | §Converging pointers |
| "triplet", "three numbers summing to X" | sort, an anchor, then converging pointers | §Converging pointers |
| "maximise the area or distance between two ends" | converging pointers, discard the limiting side | §Converging pointers |
| "longest or shortest contiguous run satisfying a condition" | variable window; decide what state the window keeps | §The sliding window |
| "every window of size k", "average of each k" | fixed window | §0.5, primitive 3 |
| "maximum or minimum of every window" | fixed window plus a decreasing deque | §When the window needs its maximum |
| "subarray sum equals k", negative values allowed | **not** a window: prefix sums plus a hash map | module 01 |

## 0.9 Self-check

Answer each in a sentence or two, without looking back. The answers are at the bottom of the module. Read the part behind any question you miss.

1. On a sorted array, `nums[lo] + nums[hi]` is smaller than the target. Why may you move `lo` without checking `nums[lo]` against any other partner?
2. The variable window has a `while` loop inside a `for` loop. Why is it O(n) and not O(n²)?
3. What two properties must a problem have before the sliding window applies?
4. Why does a window fail for "count the subarrays summing to k" when values may be negative, and what do you use instead?
5. Minimising a window and maximising a window shrink under different conditions. What is each condition, and when do you record the answer?
6. Converging pointers are looking for a pair of two different indices. Is the loop `while lo < hi` or `while lo <= hi`, and why?
7. A fixed window of size k needs the sum at each position. How do you update it in O(1), and what does `sum(nums[right - k + 1:right + 1])` at each step cost in total?
8. Which shape fits "is this string a palindrome?", and which fits "the shortest run of adjacent elements with sum at least t, all values positive"?

---

## Converging pointers

### The symmetric case: no sort needed

**Worked on [Reverse Only Letters](https://leetcode.com/problems/reverse-only-letters/) (LC 917)**, which is not in the drill set: reverse the letters of a string and leave every other character where it is.

```python
def reverseOnlyLetters(s):
    chars = list(s)                             # a str can't be changed in place
    lo, hi = 0, len(chars) - 1
    while lo < hi:
        if not chars[lo].isalpha():
            lo += 1                             # skip from the left
        elif not chars[hi].isalpha():
            hi -= 1                             # skip from the right
        else:
            chars[lo], chars[hi] = chars[hi], chars[lo]
            lo += 1                             # a swapped pair: both move
            hi -= 1
    return "".join(chars)
```

*Invariant:* every character outside `[lo, hi]` is already in its final place.

**One decision per iteration.** Each branch moves only the pointers it has to and then goes back to the `while`, which rechecks `lo < hi`. Skipping with an inner `while` instead needs its own `lo < hi` guard, or it runs off the end on a string of punctuation. The `elif` chain needs no extra guard. No sort: the job is symmetric from the two ends, the first letter trading places with the last, which is all the discard argument needs. Comparing the two ends instead of swapping them is the same walk.

### The limiting side: one end is finished

**Worked on [Boats to Save People](https://leetcode.com/problems/boats-to-save-people/) (LC 881)**, which is not in the drill set: each boat carries at most two people and at most `limit` in weight, and nobody weighs more than `limit`. Find the fewest boats that carry everyone.

```python
def numRescueBoats(people, limit):
    people.sort()
    lo, hi = 0, len(people) - 1
    boats = 0
    while lo <= hi:
        if people[lo] + people[hi] <= limit:
            lo += 1                     # the lightest shares the heaviest's boat
        hi -= 1                         # the heaviest leaves on this boat either way
        boats += 1
    return boats
```

**The discard argument.** Look at the heaviest person left, `people[hi]`. If they can't share with the lightest, they can't share with anyone, because everyone else weighs at least as much as the lightest: they take a boat alone. If they can share with the lightest, seating those two together is never worse: whoever else the lightest could have sat with is no heavier than `people[hi]`, so the seats can be swapped without overloading a boat. Either way `people[hi]` is finished after one comparison. The heavy end limits what a boat can take, so it is the end that decides.

**`lo <= hi`, not `lo < hi`.** When `lo == hi`, one person is still waiting, and they need a boat, so the loop runs once more. The pair template stops at `lo < hi` because an element can't pair with itself; here a single element left is real work. Read the operator off what one remaining element means (§The invariant is the correctness tool).

*Invariant:* everyone outside `[lo, hi]` is seated, and `boats` counts the boats used so far. O(n log n) time for the sort; the walk after it is O(n).

**The limit doesn't always need a sort.** Here the sort put the limiting element at one end. Some inputs come with the limit built in: when two ends bound a result together and one of them caps every pair it is in, comparing the two ends says which one is finished, and nothing has to be sorted. Working out which end that is, and why it can't do better, is left for the practice list.

### Sorted input, and triplets

On a sorted array the decision at each step is the comparison from §0.2: a sum that is too small moves `lo` up to a bigger value, a sum that is too big moves `hi` down to a smaller one, and a sum that matches is an answer.

**Extending to triplets.** Sort, then fix one element as the **anchor** with an outer loop, and converge on the part of the array to its right. That is O(n) work for each anchor: **O(n²)** in total, against O(n³) for the triple loop.

**Sorting also makes repeats cheap to skip.** Once sorted, equal values are adjacent, so "have I already used this value here?" is a comparison with the previous element, not a set of every answer found so far. A set of seen triplets works, and costs memory and code that the sort gives you for free.

---

## The sliding window

### The variable window, minimising

**Worked on [Minimum Size Subarray Sum](https://leetcode.com/problems/minimum-size-subarray-sum/) (LC 209)**, which is not in the drill set: the length of the shortest contiguous run with sum at least `target`, every value positive.

```python
def minSubArrayLen(target, nums):
    left = 0
    total = 0
    best = float('inf')
    for right, n in enumerate(nums):
        total += n                          # extend
        while total >= target:              # shrink while STILL valid (minimising)
            best = min(best, right - left + 1)
            total -= nums[left]
            left += 1
    return best if best != float('inf') else 0
```

*Invariant:* at the top of each `for` iteration, `total` is the sum of `nums[left..right - 1]`, and that sum is below `target`. The `while` records each valid window ending at `right`, then drops its leftmost element to try a shorter one.

**Positive values are what make it a window.** Adding a positive element only raises the sum, and removing one only lowers it, so the rule "sum at least target" is monotone.

### The variable window, maximising

**Worked on [Max Consecutive Ones III](https://leetcode.com/problems/max-consecutive-ones-iii/) (LC 1004)**, which is not in the drill set: the longest run of 1s in a binary array if you may flip at most k zeros.

```python
def longestOnes(nums, k):
    left = 0
    zeros = 0
    best = 0
    for right, n in enumerate(nums):
        if n == 0:
            zeros += 1                      # extend
        while zeros > k:                    # shrink while INVALID (maximising)
            if nums[left] == 0:
                zeros -= 1
            left += 1
        best = max(best, right - left + 1)  # record after: the window is valid here
    return best
```

*Invariant:* after the `while`, `nums[left..right]` holds at most k zeros, and `zeros` counts exactly the zeros inside it.

**Note the direction.**

| Goal | Shrink | Record |
|---|---|---|
| Minimise the window | *while valid* | inside the `while`, before each shrink |
| Maximise the window | *while invalid* | after the `while`, once it is valid again |

Getting this backwards is the classic window bug. The invariant tells you which: a maximising window is only worth recording when it is valid, so validity must be restored first.

**The state can be anything you can update in O(1)** when `right` brings an element in and when `left` lets one go. Here it is one counter. Choosing it is part of the problem: ask what the rule needs to know about the window, and keep exactly that.

### The fixed window

**Worked on [Maximum Average Subarray I](https://leetcode.com/problems/maximum-average-subarray-i/) (LC 643)**, which is not in the drill set: the largest average of any k consecutive elements.

```python
def findMaxAverage(nums, k):
    window = sum(nums[:k])
    best = window
    for right in range(k, len(nums)):
        window += nums[right] - nums[right - k]     # add the new, drop the old
        best = max(best, window)
    return best / k
```

This is §0.5, primitive 3, unchanged. Comparing sums is the same as comparing averages, since every window has the same size k, so divide once at the end. `best = window`, not `best = 0`: on an all-negative input, `0` is no window's sum.

### The sentinel

`float('inf')` as the starting best for a minimisation, converted back at the end, is the standard sentinel: any real window beats it, and if none ever did, the conversion turns "no answer" into what the problem asks for. For a maximisation the sentinel is `float('-inf')`, or the first real candidate.

> ⚠️ **You'll see the same-direction pair again in module 05, on linked lists**, where converging is impossible and the two same-direction pointers move at a fixed gap or at different speeds.

---

## When the window needs its maximum

A fixed window is cheap when its state is a sum: one addition, one subtraction. A **maximum** has no subtraction. When the old maximum leaves the window, you don't know the next largest without looking again, and `max(window)` at each step is O(k), so O(n · k) in total.

The fix is a **deque of indices whose values decrease from front to back**.

*Invariant:* the deque holds, in window order, only the indices that could still become the window's maximum, and their values are decreasing, so **the front is the maximum** of the current window.

Two kinds of index can't become the maximum, and those are the two pops. An index has **left the window**: it comes off the front. An index has a **larger value arriving after it**: the newcomer is bigger and outlasts it, so it comes off the back before the newcomer is appended.

Each index is appended once and removed at most once, so the work across the whole run is O(n). That is the monotonic-stack argument from [02-stacks-queues.md](02-stacks-queues.md), with removals at both ends.

---

## Common pointer and window mistakes

Ordered by how often each happens.

| Mistake | What you see | Entry |
|---|---|---|
| Recording a maximising window before restoring validity | an answer one or more too large | §The variable window, maximising |
| Moving `left` without undoing its contribution | the window state drifts from the window | §0.5, primitive 2 |
| Window length as `right - left` | every length one short | [bug-checklist.md](../reference/bug-checklist.md#off-by-ones-derive-never-freehand), §Off-by-ones: derive, never freehand |
| Recomputing `sum` or `max` of the window each step | correct output, O(n · k) time | §0.4 |
| Converging on an unsorted array | answers missed | §0.2, Shape A |
| `while lo <= hi` when the answer is a pair | an element paired with itself | §0.5, §The invariant is the correctness tool |
| `left += 1` inside the `if` that updates the window state | the loop never ends when the leftmost element isn't one you track | [bug-checklist.md](../reference/bug-checklist.md#the-pointer-advance-belongs-outside-the-guard), §The pointer advance belongs outside the guard |
| An inner skipping `while` with no `lo < hi` guard | `IndexError`, or pointers that cross | [bug-checklist.md](../reference/bug-checklist.md#the-guard-asymmetry), §The guard asymmetry |
| Returning the `float('inf')` sentinel | `inf` where the problem wants 0 | §The sentinel |
| A window over values that may be negative | wrong counts, no error | §0.6 |
| Leaving zero counts in the frequency map | `len(counts)` too large | §0.4 |

---

## Drill set — cold, no IDE, no running

**Solutions are not in this file.** Every shape you need is in §0 and the sections above, taught on other problems.

| # | Problem | Focus |
|---|---|---|
| 1 | [3Sum](https://leetcode.com/problems/3sum/) (LC 15) | Order: sort, an anchor, then converging pointers. Skip repeats with a neighbour comparison, not a set. ⚑ **Checkpoint** |
| 2 | [Longest Substring Without Repeating Characters](https://leetcode.com/problems/longest-substring-without-repeating-characters/) (LC 3) | Reuse: a variable window, maximising. Say what the window state is and when it is invalid |
| 3 | [Sliding Window Maximum](https://leetcode.com/problems/sliding-window-maximum/) (LC 239) | A fixed window whose state is a decreasing deque. Say the invariant before writing either pop |

**The order.** Row 1 is converging, row 2 the variable window, row 3 the fixed window with a structure from module 02 as its state.

**⚑ Checkpoint at row 1.** The anchor, the converging pair and the repeat skipping all have to come out together. If any of them doesn't come out clean, stop there and reread §0.2, Shape A, and §Converging pointers rather than pushing on.

**Spares, if a shape needs a second rep:** [LC 167 Two Sum II - Input Array Is Sorted](https://leetcode.com/problems/two-sum-ii-input-array-is-sorted/) (converging, undisguised) · [LC 977 Squares of a Sorted Array](https://leetcode.com/problems/squares-of-a-sorted-array/) (converging, writing from the back) · [LC 424 Longest Repeating Character Replacement](https://leetcode.com/problems/longest-repeating-character-replacement/) (a maximising window with a frequency map) · [LC 438 Find All Anagrams in a String](https://leetcode.com/problems/find-all-anagrams-in-a-string/) (a fixed window with a frequency map) · [LC 76 Minimum Window Substring](https://leetcode.com/problems/minimum-window-substring/) (a minimising window, harder state).

*Solved in the sections above, so from memory only:* [LC 917](https://leetcode.com/problems/reverse-only-letters/) · [LC 881](https://leetcode.com/problems/boats-to-save-people/) · [LC 209](https://leetcode.com/problems/minimum-size-subarray-sum/) · [LC 1004](https://leetcode.com/problems/max-consecutive-ones-iii/) · [LC 643](https://leetcode.com/problems/maximum-average-subarray-i/).

## Also on the practice list

These problems are on the app's practice list but are not drills in this module. Work them after the drill set if you want more reps.

| # | Problem | Focus |
|---|---|---|
| 1 | [Valid Palindrome](https://leetcode.com/problems/valid-palindrome/) (LC 125) | Converging, no sort. Decide what happens to a character that doesn't count before writing the loop |
| 2 | [Container With Most Water](https://leetcode.com/problems/container-with-most-water/) (LC 11) | Converging, no sort. After each measurement, say which end is finished and why before moving it |
| 3 | [Permutation in String](https://leetcode.com/problems/permutation-in-string/) (LC 567) | A fixed window with a frequency map |

## Before you submit anything

Every problem, no exceptions:

1. **Name the shape and the signal that pointed to it**, before writing code: converging or window, and which word in the statement said so.
2. **State the brute force and call it quadratic.** Then say which escape the shape spends: Order for converging, Reuse for the window.
3. **Say the invariant**, then write it.
4. Run [bug-checklist.md](../reference/bug-checklist.md#the-30-second-pass), §The 30-second pass, over your code.
5. **Trace it.** Three elements, then `[]`, then one element. Check the invariant survives one iteration, and name the line that moves a pointer on every path.
6. **Say the complexity in words**, time *and* space, and for the window say why the nested loop is linear.

---

## Self-check answers

1. Because the array is sorted, `nums[hi]` is the **largest partner still available** to `nums[lo]`. If even that sum is too small, `nums[lo]` with any other remaining partner is smaller still, so every pair `nums[lo]` can still form is ruled out in one comparison.
2. **`left` only ever increases and never runs past the end of the array**, so it advances at most n times *in total* over the whole run, not n times per step of the `for`. Every index enters the window once and leaves at most once: at most **2n** moves, O(n).
3. The answer must be **contiguous**, a run of adjacent elements, and the validity rule must be **monotone**: growing the window can only break it, shrinking can only restore it.
4. With negative values, adding an element can **lower** the sum and removing one can **raise** it, so the rule isn't monotone and the window can't know when to shrink. Use **prefix sums with a hash map** from module 01, which need no such property.
5. **Minimising:** shrink *while the window is valid*, recording inside the loop before each shrink. **Maximising:** shrink *while it is invalid*, and record after the loop, once it is valid again.
6. **`while lo < hi`.** When `lo == hi` both pointers are on the same element, and a pair of two different indices can't use one element twice. `<=` belongs to a closed range that can hold a single-element answer.
7. Add the element entering and subtract the one leaving: **`window += nums[right] - nums[right - k]`**. Recomputing the slice and its sum is O(k) at each of about n positions, **O(n · k)** in total, which is the brute force.
8. The palindrome is **converging**: it compares the two ends, a symmetric property, and needs no sort. The shortest run with sum at least t is the **window**, minimising: it is contiguous, and with positive values the rule is monotone.
