# Module 00: Before you start

<!-- toc -->
**Contents**

- [Big-O from zero](#big-o-from-zero)
  - [What O(n) means](#what-on-means)
  - [Counting loops](#counting-loops)
  - [Best, worst and average case](#best-worst-and-average-case)
  - [Space](#space)
  - [Reading the constraints](#reading-the-constraints)
- [Recursion and the call stack](#recursion-and-the-call-stack)
  - [A function that calls itself](#a-function-that-calls-itself)
  - [The call stack, drawn](#the-call-stack-drawn)
  - [Trust the recursive call](#trust-the-recursive-call)
  - [A tiny tree, by hand](#a-tiny-tree-by-hand)
  - [Returning a value vs updating an answer on the side](#returning-a-value-vs-updating-an-answer-on-the-side)
  - [Stack depth](#stack-depth)
- [The Python interview subset](#the-python-interview-subset)
  - [What "without an IDE" means](#what-without-an-ide-means)
  - [The subset](#the-subset)
  - [What to do when you blank](#what-to-do-when-you-blank)
  - [How to learn it](#how-to-learn-it)
- [How to work a problem](#how-to-work-a-problem)
  - [The five steps](#the-five-steps)
  - [The four-part submission](#the-four-part-submission)
  - [Worked example: first unique character](#worked-example-first-unique-character)
- [Self-check](#self-check)
- [Self-check answers](#self-check-answers)
<!-- /toc -->

This module holds the basics that no single topic owns: how to count the cost of code, how recursion runs, which Python you're expected to write from memory, and the routine for working any problem from statement to submission. Every later module opens by naming the sections of this one it builds on.

**How to use it.** Take the self-check at the bottom first. Read the sections whose questions you missed and skip the rest. Then take the diagnostic.

| Section | What it gives you | Where it's first needed |
|---|---|---|
| Big-O from zero | What O(n) means, counting loops, best and worst case, space | You'll see it first in module 01 |
| Recursion and the call stack | Base case, trusting the recursive call, returning a value vs updating an answer on the side, stack depth | You'll see it first in module 01, in merge sort, then in most modules after it |
| The Python interview subset | What you're expected to write without an IDE, and where the reference lives | You'll see it first in module 01 |
| How to work a problem | Clarify → brute force → optimise → code → trace, and the four-part submission | The diagnostic, and every problem after it |

There is no drill set here. The problems start with the diagnostic.

---

## Big-O from zero

### What O(n) means

**n is the size of the input**: the length of the list, the number of characters, the number of nodes. Big-O describes **how the work grows as n grows**. It ignores constant factors and smaller terms, because for large n the biggest term decides everything.

| Work done | Big-O | Why |
|---|---|---|
| `3n + 5` steps | O(n) | constants and the `+ 5` stop mattering as n grows |
| `n² + n` steps | O(n²) | at n = 1,000, n² is a million and n is a thousand |
| `n²/2` steps | O(n²) | halving the work is a constant factor |
| 20 steps whatever the input | O(1) | the work doesn't grow at all |

**The doubling test** is the fastest way to feel each class: double n and ask what happens to the work.

| Big-O | Name you say out loud | Double n and the work… | Typical cause |
|---|---|---|---|
| O(1) | constant | stays the same | arithmetic, a dict or set lookup |
| O(log n) | logarithmic | goes up by one step | halving the range on every step |
| O(n) | linear | doubles | one pass over the input |
| O(n log n) | n log n | slightly more than doubles | sorting |
| O(n²) | quadratic, "n squared" | quadruples | a loop inside a loop over the same input |
| O(2ⁿ) | exponential | squares | trying every subset |

**Name your n.** When there are two inputs, keep two letters: a loop over a list of length n with a loop over a list of length m inside it is O(n · m), not O(n²). For a grid, say "rows × cols".

### Counting loops

The rule: **work = how many times each line runs × what one run of it costs.** Then add the pieces.

```python
def sum_all(nums):                 # O(n): the loop runs n times, each step is O(1)
    running = 0
    for x in nums:
        running += x
    return running

def count_equal_pairs(nums):       # O(n²): every pair (i, j) with i < j
    count = 0
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            if nums[i] == nums[j]:
                count += 1
    return count

def halvings(n):                   # O(log n): n is cut in half on every step
    steps = 0
    while n > 1:
        n //= 2
        steps += 1
    return steps
```

| Shape | Cost | Why |
|---|---|---|
| One loop, O(1) body | O(n) | n runs × O(1) |
| Two loops **one after the other** | O(n) + O(n) = O(n) | sequential pieces **add** |
| A loop **inside** a loop | O(n) × O(n) = O(n²) | nested pieces **multiply** |
| Inner loop starting at `i + 1` | still O(n²) | it runs n(n−1)/2 times, which is n²/2 minus smaller terms |
| A value halved or doubled each step | O(log n) | it reaches 1 (or n) after about log₂ n steps |

**Some single lines are loops.** This is where most wrong complexity answers come from: the line looks like O(1) and hides a scan.

| Line | Looks like | Costs | Why |
|---|---|---|---|
| `x in some_list` | one check | O(n) | it compares against each element in turn |
| `x in some_set`, `key in some_dict` | one check | O(1) on average | it hashes `x` and jumps to its slot |
| `some_list.index(x)`, `some_list.count(x)` | one call | O(n) | a scan |
| `some_list[a:b]` | one expression | O(b − a) | a slice copies |
| `some_list.pop(0)` | one call | O(n) | every element behind it shifts left |
| `sorted(some_list)` | one call | O(n log n) | it sorts |

So this function is not O(n):

```python
def common(a, b):
    found = []
    for x in a:            # runs n times
        if x in b:         # b is a list of length m: a scan of up to m items
            found.append(x)
    return found
```

It is **O(n · m)**. Build `b_set = set(b)` once before the loop, at O(m), and test `x in b_set` at O(1): the whole function becomes **O(n + m)**. You'll see the full cost table for `list`, `dict` and `set` again in module 01.

**Say it as a sentence, with the reason.** The template:

> *"O(\_\_) time because \_\_ runs \_\_ times and each run costs \_\_."*

Filled in for `common` after the fix: *"O(n + m) time, because building the set touches each of the m items once, and the loop runs n times with an O(1) lookup each time."* A bare "O(n)" is a guess as far as the listener can tell. The reason is what shows you know.

### Best, worst and average case

The same function can cost different amounts on different inputs of the same size.

```python
def find(nums, target):
    for i, x in enumerate(nums):
        if x == target:
            return i
    return -1
```

| Case | Input | Cost |
|---|---|---|
| Best | `target` is at index 0 | O(1) |
| Worst | `target` is absent | O(n) |

**When you state a complexity without a qualifier, it means the worst case.** That is what interviewers ask for unless they say otherwise. Two standard exceptions: `dict` and `set` operations are **O(1) on average**, and `list.append` is **O(1) amortised** (an occasional append costs O(n) to resize, but averaged over many appends each one is O(1)). Say "average" or "amortised" when it matters.

### Space

Space complexity counts the memory **your algorithm allocates that grows with n**.

| Counts | Doesn't count |
|---|---|
| a set, dict, list or `Counter` you build | the input you were given |
| a copy, including a slice | the output you're required to return (by the usual convention) |
| **the call stack, when you recurse** | a fixed number of plain variables: that's O(1) |

The usual convention is **auxiliary space**: everything except the input and the required output. Say the caveat when it applies: *"O(1) extra space, not counting the output."* The call stack is the item people forget, and it gets its own part in the next section.

### Reading the constraints

The constraints under a problem statement tell you how fast the answer has to be. Problem setters choose their limits assuming roughly 10⁸ simple operations per second, so the size of n tells you the complexity they intend:

| If n is at most about… | The intended complexity is usually… | Because |
|---|---|---|
| 10 | O(n!), trying every ordering | 10! ≈ 3.6 × 10⁶ |
| 20 | O(2ⁿ), trying every subset | 2²⁰ ≈ 10⁶ |
| 500 | O(n³) | 500³ ≈ 1.25 × 10⁸ |
| 5,000 | O(n²) | 5,000² = 2.5 × 10⁷ |
| 10⁵ to 10⁶ | O(n log n) or O(n) | 10⁶ × 20 ≈ 2 × 10⁷ |
| more than that | O(log n) or O(1) | even one pass is too many |

The table reads one way: from the limit to the complexity the setter had in mind. Python is slower than the languages those limits assume, so a solution at the edge of a row can still time out. These are rough guides, not hard limits. They still settle most questions of the form "is my brute force good enough?". You'll see O(log n) searches again in module 04, and O(2ⁿ) "try every subset" problems again in module 07.

---

## Recursion and the call stack

### A function that calls itself

A recursive function solves a problem by solving **a smaller copy of the same problem** and doing a little work on top. It has two parts, and it needs both:

```python
def factorial(n):
    if n == 0:                      # base case: small enough to answer directly
        return 1
    return n * factorial(n - 1)     # recursive case: a smaller input, then one multiplication
```

| Part | Job | What breaks without it |
|---|---|---|
| **Base case** | answers the smallest input directly, with no recursive call | the calls never stop, and Python raises `RecursionError` |
| **Recursive case** | calls itself on a **smaller** input and combines the result | nothing gets computed |

**Every call has to move toward the base case.** `factorial(-1)` calls `factorial(-2)`, then `factorial(-3)`, and never reaches 0. The base case exists, but the input never gets there.

### The call stack, drawn

Each call gets its own **frame**: its own copy of `n` and the line it's waiting on. Frames pile up on the **call stack**, and only the top one runs. Here is `factorial(3)` at its deepest point:

```
factorial(0)    ← top: the only one running. Returns 1
factorial(1)    waiting for factorial(0), will return 1 * that
factorial(2)    waiting for factorial(1), will return 2 * that
factorial(3)    waiting for factorial(2), will return 3 * that
```

Then it unwinds, top first:

| Frame finishes | It computes | It returns to |
|---|---|---|
| `factorial(0)` | base case | `factorial(1)` gets 1 |
| `factorial(1)` | `1 * 1` | `factorial(2)` gets 1 |
| `factorial(2)` | `2 * 1` | `factorial(3)` gets 2 |
| `factorial(3)` | `3 * 2` | the caller gets **6** |

Calls go down until the base case answers. Results come back up, one frame at a time.

```steps
title: factorial(3), call by call
- stack=[f(3)] | Call `factorial(3)`. One frame. The top of the stack is on the right.
- stack=[f(3), f(2)] | `n` is not 0, so it calls `factorial(2)` and waits.
- stack=[f(3), f(2), f(1)] | `factorial(1)` calls `factorial(0)` and waits.
- stack=[f(3), f(2), f(1), f(0)] | Deepest point. `n == 0`, the base case, no more calls.
- stack=[f(3), f(2), f(1)] | `f(0)→1`. The top frame returns 1 and is gone. `factorial(1)` computes `1 * 1`.
- stack=[f(3), f(2)] | `f(1)→1`. `factorial(2)` computes `2 * 1`.
- stack=[f(3)] | `f(2)→2`. `factorial(3)` computes `3 * 2`.
- stack=[] | `f(3)→6`. The last frame returns 6 to the caller. The stack is empty.
```

### Trust the recursive call

Tracing every frame is fine for `factorial(3)` and impossible for a tree of a thousand nodes. So you don't. You write the recursive case **assuming the smaller call already returns the right answer**, and you check three things instead:

1. **The base case** returns the right value for the smallest input.
2. **Every call shrinks the input** toward that base case.
3. **The combine step is right**, *if* the smaller call is right.

If all three hold, the function is correct for every size. This is induction: true for the smallest case, and true for n whenever it's true for n − 1.

Here it is on the sum of a list:

```python
def list_sum(nums, i=0):
    if i == len(nums):                      # base case: nothing left, the sum is 0
        return 0
    return nums[i] + list_sum(nums, i + 1)  # trust: list_sum(nums, i + 1) sums everything after i
```

1. **Base case:** when `i == len(nums)` there's nothing left to add, so 0 is right. It also makes the empty list work with no special case.
2. **Shrinking:** `i` goes up by one per call, so it reaches `len(nums)`.
3. **Combine:** if `list_sum(nums, i + 1)` is the sum of everything after position `i`, then adding `nums[i]` gives the sum from `i` on.

**Why pass an index instead of a slice.** `nums[0] + list_sum(nums[1:])` reads well, but every `nums[1:]` copies the rest of the list. Across n calls that's n + (n−1) + … + 1 copied elements: **O(n²) time**, and since each waiting frame keeps its slice alive, O(n²) memory at the deepest point as well. The index version is O(n) time.

### A tiny tree, by hand

A tree is where recursion becomes the natural tool, because each node can have two children. Each node holds a value and links to a left and a right child, either of which can be missing (`None`):

```
          -10
         /    \
        4      5
       / \
      1   2
```

```python
class TreeNode:
    def __init__(self, val, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

root = TreeNode(-10,
                TreeNode(4, TreeNode(1), TreeNode(2)),
                TreeNode(5))
```

LeetCode defines this class for you. You'll see trees properly again in module 06. Here the tree is only something to recurse on.

**The sum of every value in the tree:**

```python
def tree_sum(node):
    if node is None:            # base case: an empty tree sums to 0
        return 0
    return node.val + tree_sum(node.left) + tree_sum(node.right)
```

The same three checks. The empty tree sums to 0. Each call goes to a child, so it gets closer to `None`. And if each child's call returns that child's whole subtree sum, adding the node's own value gives this node's subtree sum.

| Call | Left child returns | Right child returns | This call returns |
|---|---|---|---|
| `tree_sum(1)` | 0 (`None`) | 0 (`None`) | 1 |
| `tree_sum(2)` | 0 | 0 | 2 |
| `tree_sum(4)` | 1 | 2 | 4 + 1 + 2 = **7** |
| `tree_sum(5)` | 0 | 0 | 5 |
| `tree_sum(-10)` | 7 | 5 | −10 + 7 + 5 = **2** |

The base case tests for `None` at the top. It does not test "am I a leaf?". Here is why: take a node with only a left child. A function whose only base case is "am I a leaf?" sees that this node is not a leaf, so it recurses into both children, including the missing right one. That call receives `None`, which is not a leaf either, so it reads `None.left` and raises `AttributeError`. See [bug-checklist.md](../reference/bug-checklist.md#wrong-base-case-shape), §Wrong base-case shape.

### Returning a value vs updating an answer on the side

`tree_sum` hands its parent exactly the thing the problem asks for. Now change the question: **what is the largest subtree sum anywhere in the tree?** In the drawing, the subtree rooted at 4 sums to 7, more than any other. The root's whole tree sums to only 2.

To compute its own subtree sum, a parent needs **each child's subtree sum**. It does not need the largest sum found so far. The two quantities differ, so they travel by different channels:

```python
def largest_subtree_sum(root):
    best = float('-inf')                 # the answer, kept on the side

    def subtree_sum(node):               # returns what the PARENT needs: this subtree's sum
        nonlocal best
        if node is None:
            return 0
        total = node.val + subtree_sum(node.left) + subtree_sum(node.right)
        best = max(best, total)          # the answer: updated on the side, never returned
        return total

    subtree_sum(root)
    return best
```

On the drawing, `subtree_sum` returns 1, 2, 7, 5 and 2 in the order of the table above, and `best` ends at **7**.

| Shape | What each call returns | Where the answer lives | Use when |
|---|---|---|---|
| **Return a value** | the answer for its own subtree | the root's return value | the answer for the whole input is the same kind of thing a call hands its parent |
| **Update an answer on the side** | what the parent needs to compute its own value | a variable outside the recursion, updated at every node | the answer can be found at any node, and the parent needs something else from its children |

**The question that decides it:** *is what a call hands its parent the same thing as the final answer?* For `tree_sum`, yes. For `largest_subtree_sum`, no: the parent needs a sum, and the answer is a maximum over every node.

Three details in that code:

- **`nonlocal best`** is required because the helper *rebinds* `best` (`best = ...`). Without it, Python treats `best` as a new local variable for the whole helper, and the read inside `max` fails with `UnboundLocalError`. See [bug-checklist.md](../reference/bug-checklist.md#assignment-makes-a-name-local-for-the-whole-function), §Assignment makes a name local for the whole function. Inside a LeetCode `class Solution`, `self.best` does the same job.
- **Each quantity uses exactly one channel.** The sum only goes up by `return`. The best only goes on the side. The bug is sending the same quantity both ways, or prefixing a call with `return` when that call's job was to update something.
- **Returning a pair also works:** `subtree_sum` could return `(total, best_inside)`. The side variable is usually shorter, and both are correct.

You'll see this split again in module 06, where many tree answers have this shape.

### Stack depth

**A recursive function's space is the deepest the call stack ever gets**, not the total number of calls. Frames that have returned are gone. `tree_sum` makes a call for every node and every `None` child, yet at any moment only one root-to-node path of frames is alive.

| Function | Deepest stack | Stack space |
|---|---|---|
| `factorial(n)` | n + 1 frames | O(n) |
| `list_sum(nums)` | n + 1 frames | O(n) |
| `tree_sum` on a balanced tree | about log₂ n frames | O(log n) |
| `tree_sum` on a tree that is one long chain | n frames | O(n) |

For trees the general statement is **O(h) space, where h is the height of the tree**. You'll see that again in module 06.

**A plain Python interpreter stops at about 1,000 frames by default.** Past that it raises `RecursionError`, however correct the logic is. An online judge may raise the limit, and an interviewer's environment may not, so plan for the default. With it, `list_sum` on a list of 50,000 numbers fails, and so does recursion on a long chain. When the input can be that deep:

- **say it out loud**: *"this recursion is n deep, and Python's limit is about 1,000, so for large inputs I'd write it with a loop or an explicit stack";*
- don't reach for `sys.setrecursionlimit` as the fix. Raising it past what the interpreter can hold crashes the process outright instead of raising an error, and to an interviewer it reads as working around the problem.

You'll see recursion again in module 05, on linked lists, and again in module 07, where every choice is a recursive call, and later in module 09, where the same call gets asked for many times over.

---

## The Python interview subset

### What "without an IDE" means

In most interviews you write in a plain editor or a shared document: no autocomplete, no running the code, no documentation. Everything below has to come out of your head, as valid Python, at typing speed.

You are **not** expected to know the standard library. You're expected to know a short, fixed list, and the toolkit has all of it: [python-toolkit.md](../reference/python-toolkit.md). This section tells you what is on the list and where in the toolkit each part lives. It doesn't repeat the toolkit.

### The subset

| Area | What you write cold | Where it's covered |
|---|---|---|
| LeetCode's frame | `class Solution:` with a method taking `self`; type hints such as `List[int]` and `Optional[TreeNode]`; calling a helper method as `self.helper(...)` | [bug-checklist.md](../reference/bug-checklist.md#missing-self-on-a-recursive-method-call), §Missing `self.` on a recursive method call, and [bug-checklist.md](../reference/bug-checklist.md#mixing-a-method-and-a-nested-function), §Mixing a method and a nested function |
| The core types | `list`, `dict`, `set`, `tuple`, `str`: create, index, add, remove, test membership, `len` | Assumed: the toolkit doesn't teach these basics. It covers sets in [python-toolkit.md](../reference/python-toolkit.md#5-sorted-and-set-builtins-no-import), §5. `sorted` and `set`: builtins, no import, and which types can be dict keys in §Dict keys must be immutable: convert, don't invent |
| Five standard-library tools | `deque`, `defaultdict`, `Counter`, `heapq`, and the builtins `sorted` and `set` | [python-toolkit.md](../reference/python-toolkit.md#the-five), §The five |
| Loops | `for i in range(...)`, counting down with `range(n - 1, -1, -1)`, `enumerate`, `zip`, `while`, `break`, `continue` | [python-toolkit.md](../reference/python-toolkit.md#everyday-syntax), §Everyday syntax, and [python-toolkit.md](../reference/python-toolkit.md#zip-sorting-two-parallel-arrays-together), §`zip`: sorting two parallel arrays together |
| Comprehensions | `[f(x) for x in xs if cond]`, and the dict and set forms | [python-toolkit.md](../reference/python-toolkit.md#comprehensions-the-loops-in-the-same-order-body-first), §Comprehensions: the loops, in the same order, body first |
| Slicing and negative indices | `s[a:b]`, `s[::-1]`, `s[-1]`, and what each costs | [python-toolkit.md](../reference/python-toolkit.md#slicing-lststartstopstep), §Slicing: `lst[start:stop:step]`, and [python-toolkit.md](../reference/python-toolkit.md#️--1-means-two-completely-different-things), §⚠️ `-1` means two completely different things |
| Built-ins on empty input | `min`, `max`, `sum`, `any`, `all` and what each does on an empty sequence | [python-toolkit.md](../reference/python-toolkit.md#empty-safe-built-ins-the-anti-special-case-set), §Empty-safe built-ins: the anti-special-case set |
| Truthiness | `while queue:`, `if not node:` | [python-toolkit.md](../reference/python-toolkit.md#python-truthiness-why-while-queue-works), §Python truthiness: why `while queue:` works |
| Sorting | `sorted(xs, key=..., reverse=True)`, sorting tuples | [python-toolkit.md](../reference/python-toolkit.md#comparing-and-sorting-sequences-python-already-does-it), §Comparing and sorting sequences: Python already does it |
| Strings | `split`, `join`, `strip`, `isalnum`, `lower`, and the rest of the common ten | [python-toolkit.md](../reference/python-toolkit.md#string-methods-the-ten-that-come-up), §String methods: the ten that come up |
| Nested functions | a helper defined inside the method, and `nonlocal` when it rebinds an outer name | the Recursion section above, and [bug-checklist.md](../reference/bug-checklist.md#assignment-makes-a-name-local-for-the-whole-function), §Assignment makes a name local for the whole function |
| Numbers | `//` for integer division, `%` for remainder, `float('inf')` as a starting minimum, and integers that never overflow | [bug-checklist.md](../reference/bug-checklist.md#-where-you-meant-), §`%` where you meant `//` |

On LeetCode, pick **Python3** in the language menu. The toolkit's opening explains why.

### What to do when you blank

You will blank on a method name at some point. **Say what you mean and keep going**: *"I want to remove from the front here, I believe that's `popleft`."* Write your best guess and flag it. Interviewers score knowing that a queue is the right structure, not the exact spelling. What costs you is building a workaround in silence. See [python-toolkit.md](../reference/python-toolkit.md#rules), §Rules, and [python-toolkit.md](../reference/python-toolkit.md#if-you-dont-remember-the-keyword-say-it-never-build-around-it), §If you don't remember the keyword: say it, never build around it.

### How to learn it

Read the toolkit's §The five and §Everyday syntax before the diagnostic. Then write each item from memory, once, on paper, and check it against the toolkit. Read the rest of the toolkit when a module points you to it.

---

## How to work a problem

### The five steps

The same routine for every problem, from the diagnostic on. Each step has something you **say out loud**, because in an interview the talking is scored along with the code.

| Step | What you do | What you say |
|---|---|---|
| **1. Clarify** | Restate the problem. Ask about input size, empty input, duplicates, negatives, whether you may change the input, and what to return when there's no answer. Write two or three small examples, one of them degenerate | *"So the input is…, and I return… Can it be empty?"* |
| **2. Brute force** | Find the most direct correct method, even a slow one, and give its complexity. You usually don't code it | *"The direct way checks every pair, which is O(n²)."* |
| **3. Optimise** | Find the work the brute force repeats, and the cue in the statement that points to a technique. Check the target complexity against the constraints | *"It recounts the same thing for every position. If I count once up front, it's linear."* |
| **4. Code** | Before the loop, say what it keeps true. Name each variable by the role it plays | *"At the top of each iteration, `best` holds the answer for everything before `i`."* |
| **5. Trace** | Walk the code by hand on the degenerate input and one small normal input, writing each variable's value down | *"On the empty list the loop doesn't run, and I return 0, which is right."* |

**Why the brute force is worth saying.** It proves you understand the problem, it gives you a correct fallback if the clever version stalls, and its repeated work is usually what tells you how to optimise.

**The degenerate input** is the smallest or most extreme legal input. Bugs live there, and the example in the statement is designed not to show them. Read the constraints to see which of these are legal:

| Input type | Degenerate cases to trace |
|---|---|
| List or string | empty, one element, all elements equal |
| Number | 0, 1, negative |
| Tree | `None`, a single node, a chain |
| Grid | 1 × 1, a single row |
| Sorted input | already sorted, reverse sorted |

For the trace itself, see [bug-checklist.md](../reference/bug-checklist.md#then-trace-it-the-two-column-method), §Then trace it: the two-column method. Before you show any code, run its §The 30-second pass.

### The four-part submission

Every problem you submit has four parts, in this order. The format matters as much as the answer, because it is what an interviewer hears.

| Part | What it is | Why |
|---|---|---|
| **1. The pattern, and the signal that pointed to it** | *"Hashing: I need to know how often each character appears, and I'd otherwise recount."* Said before any code | it shows the method was chosen, not stumbled into |
| **2. The code, written cold** | No IDE, no running, no lookups | that's the interview condition |
| **3. Time and space complexity, with the reason** | The sentence from the Big-O section, for both time and space, unprompted | a complexity with no reason sounds like a guess |
| **4. A hand trace on the degenerate input** | Done on paper, before you submit | it catches the bugs the example doesn't reach |

Three habits run through all four parts:

- **State the invariant before the loop body**: what the loop keeps true at the top of every iteration.
- **Say the complexity with the reason**: *"O(\_\_) because \_\_ runs \_\_ times and each costs \_\_."*
- **Name variables by their role** (`left`, `best`, `counts`), not by the order they showed up (`x`, `y`, `temp`).

When you submit to Claude, expect the review to **run** your code, not only read it: against the examples, the edge cases and many random inputs. If something fails, you get a concrete failing input. Claude doesn't write your code unless you ask it to.

### Worked example: first unique character

[LC 387 First Unique Character in a String](https://leetcode.com/problems/first-unique-character-in-a-string/) is not in any drill set, so here it is all the way through. *Given a string of lowercase English letters, return the index of the first character that appears exactly once, or −1 if there is none.*

**1. Clarify.** The constraints say the length is between 1 and 10⁵, so the empty string isn't legal. Only lowercase letters. The degenerate inputs are one character (`"a"` → 0) and every character repeated (`"aabb"` → −1).

**2. Brute force.** For each position, count how often its character appears in the whole string. The first count of 1 is the answer. That's n positions × an O(n) count = **O(n²)**. At n = 10⁵ that's 10¹⁰ steps, far too slow.

**3. Optimise.** The repeated work: the same character gets recounted at every position where it appears. Count every character once, up front, then scan for the first one whose count is 1. Two passes, **O(n)**.

**4. Code.** The scan's invariant: *every character before `i` appears more than once.*

```python
from collections import Counter

class Solution:
    def firstUniqChar(self, s: str) -> int:
        counts = Counter(s)                  # character -> how many times it appears in s
        for i, ch in enumerate(s):
            if counts[ch] == 1:              # invariant: no character before i was unique
                return i
        return -1
```

**5. Trace**, on the degenerate inputs:

| Input | `counts` | Loop | Returns | Expected |
|---|---|---|---|---|
| `"a"` | `{a: 1}` | `i = 0`: count 1 | 0 | 0 ✓ |
| `"aabb"` | `{a: 2, b: 2}` | every count is 2, the loop finishes | −1 | −1 ✓ |

**The four-part submission**, as you'd deliver it:

1. **Pattern and signal:** *"Hashing. 'Appears exactly once' is a frequency question, and the brute force recounts the same characters."*
2. **Code:** above.
3. **Complexity:** *"O(n) time, because building the counter touches each of the n characters once, and the scan runs at most n times with an O(1) lookup each. O(1) extra space, because the counter holds at most 26 keys, one per lowercase letter, however long the string is."*
4. **Trace:** the table above, on `"a"` and `"aabb"`.

Notice the space answer. A counter over the input is usually O(n), but here the alphabet bounds it at 26 keys. Saying *why* it's O(1) is what makes it an answer instead of a guess.

---

## Self-check

Answer each in a sentence or two, without looking back. The answers are below. Read the section behind any question you miss.

1. A loop runs over a list `a` of length n, and inside it tests `if x in b`, where `b` is a list of length m. What is the time complexity, and what one change makes it O(n + m)?
2. What is the time complexity of `i = 1` followed by `while i < n: i *= 2`, and why?
3. A recursive function on a tree must return the largest subtree sum found anywhere in the tree. What does each call return to its parent, where does the largest-so-far live, and why can't it be the return value?
4. In a plain Python interpreter with the default recursion limit, a recursive sum over a list of 50,000 numbers raises `RecursionError`, though the logic is correct. Why, what is the recursive version's space complexity, and what do you say to the interviewer?
5. Which standard-library tools are you expected to write from memory, with no lookup?
6. Mid-interview, you can't remember the name of the method that removes from the front of a `deque`. What do you do?
7. Name the four parts of a submission, in order.
8. For a function that takes a list of numbers, what are the degenerate inputs, and why trace those rather than the example from the statement?

---

## Self-check answers

1. **O(n · m)**, because `x in b` scans up to m items and it runs n times. Build `set(b)` once before the loop (O(m)) and test membership against the set, which is O(1) on average: O(n + m) in total.
2. **O(log n)**, because `i` doubles on every step, so it passes n after about log₂ n steps.
3. Each call returns **its own subtree's sum**, because that's what the parent needs to compute its own sum. The largest-so-far lives **on the side**, in a variable outside the recursion (with `nonlocal`, or `self.best`), updated at every node. It can't be the return value because the parent needs a sum, not a maximum, and the largest subtree can sit anywhere, not only at the root.
4. Each element adds a frame, so the stack is about **50,000 frames deep**, past the default limit of about 1,000 in a plain Python interpreter. The space is **O(n)** for the call stack. Say that the recursion is n deep and the default limit is about 1,000, so for large inputs you'd write it as a loop or with an explicit stack.
5. `deque`, `defaultdict`, `Counter`, `heapq`, and the builtins `sorted` and `set`. The toolkit's §The five covers them.
6. **Say what you mean and keep going**: "I want to remove from the front, I believe that's `popleft`." Write your best guess, flag it, and don't build a workaround in silence.
7. **The pattern and the signal that pointed to it → the code, written cold → time and space complexity with the reason → a hand trace on the degenerate input.**
8. **The empty list, a single element, and all elements equal** (plus 0 and negative values if the numbers matter). The statement's example is the happy path, and the bugs live at the boundaries, where loops run zero or one times.
