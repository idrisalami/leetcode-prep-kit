# Bug checklist

The bugs that show up most often in interview code, and how to catch them before an interviewer does. Almost none of them are thinking failures. The idea is usually right and the scaffolding around it is wrong: the initial value, the guard, the loop condition, the return, a name, a line at the wrong indentation.

**Run the 30-second pass over any code before you show it. Then trace it.** The common bugs further down are the long version: what each one looks like, why it survives a re-read, and the check that finds it.

---

## The 30-second pass

1. Does every path `return`, and the right **type**?
2. Every recursive method call prefixed with `self.`?
3. Every attribute name checked against the stub: `.val`, not `.value`?
4. Every comparison in a condition written `==`, not `=`?
5. Every midpoint or division written `//`, not `%`?
6. Base case at the **top**, testing for `None`?
7. What happens on empty input, a single element, and `None`?
8. **Does every variable's name say the role it plays, not the order it arrived in?** `left`/`right`, `lo`/`hi`, `dummy`. See §Names that describe arrival order, not role.
9. **If the job was to modify a structure: does any line assign to a `.left`, `.right` or `.next`?** Assigning to the parameter is not an edit. See §Assigning to the parameter, expecting the structure to change.

## Then trace it: the two-column method

**Don't re-read the code hunting for the error. Put your variable next to the ground truth, step by step, and find the first row where they disagree.** The line that ran on that step is the broken line.

An example. This function should return the length of the longest run of equal consecutive characters (`"aabbb"` → 3). Assume `s` is non-empty.

```python
def longest_run(s):
    best = run = 1
    for i in range(1, len(s)):
        if s[i] == s[i - 1]:
            run += 1
        else:
            run = 0
        best = max(best, run)
    return best
```

`s = "aabbb"`, tracking `run`:

| i | char | your value | **true value** | |
|---|---|---|---|---|
| 1 | `a` | 2 | 2 | ✓ |
| 2 | `b` | **0** | **1** | ✗ **first divergence** |
| 3 | `b` | 1 | 2 | ✗ (inherited) |
| 4 | `b` | 2 | 3 | ✗ (inherited) |

Row 1 agrees, so everything up to there is sound. The break is at `i = 2`, the first step that entered the `else` branch. One line: a new run already has length 1, so it should be `run = 1`. Localised without reasoning about the algorithm at all.

> **You don't need to understand a bug to locate it. You need the first row where your value ≠ the truth.**

**The ground-truth column is the part that gets skipped, and it's the part that works.** Writing only your own variables tells you what the code *did*, never that it was wrong.

Pick the smallest input that reaches the branch you're unsure of. Three to five elements is usually enough.

### Off-by-ones: derive, never freehand

The length of an **inclusive** range is always:

> **`end - start + 1`**

Write that, substitute, *then* simplify. If a window runs `j + 1 … i`, its length is `i - (j + 1) + 1 = i - j`. The `+1` and `-1` cancel, and that cancellation is exactly where a hand-written `- 1` creeps in.

### Keep one source of truth

Storing `length` and deriving `left = i - length` means a wrong length also corrupts every guard that uses `left`: **one error becomes two, silently.** Store the primitive (`left`) and recompute the derived value (`i - left + 1`) fresh each iteration. Two variables that must stay consistent will eventually disagree.

### The general form

Pick the smallest non-trivial input and walk it line by line, out loud, writing down each variable's value.

Most bugs in interview code surface this way. You can't run code in most interviews, so tracing is the only quality control you have. Do it on a two-node tree, a two-element array and an empty input. It takes ninety seconds, and it is often the difference between "solved" and "not solved".

## Not on the checklist, but scored

**Say the complexity out loud, unprompted, in plain words.** "This is O(n squared) time and O(1) space." Have the vocabulary automatic: it comes up in every round, and hesitation there reads as uncertainty about the analysis itself.

---

## Common bugs: positions, values and names

An array has **positions** and **values**, a linked list has **nodes**, **payloads** and **links**, and a name can describe what a thing is or merely when it showed up. Mixing them produces code that runs and lies.

### Index vs value

Every variable holds a position or a value, never "it depends".

```python
lo = nums[i]        # ✗ lo is a POSITION; nums[i] is a VALUE → infinite loop
lo += 1             # ✓ move the pointer

if i != j:          # ✗ comparing positions when you meant distinct values (or the reverse)
seen.add(n + m)     # ✗ storing a derived sum where the values belonged
```

**The habit:** for every variable, say *"this holds a position"* or *"this holds a value"*, and name it accordingly: `i`, `lo`, `hi`, `idx` for positions; `n`, `val`, `price` for values. Then no line can silently mix them.

It changes costume with the topic. On a stack, `stack[-1]` may be an index and `nums[stack[-1]]` the value, one line apart. On a grid, `for r in grid` yields **rows**, not row numbers, and `for c in r` yields **cell values**. In binary search over an answer range, `lo` and `hi` are values, not positions.

### Unpacking `enumerate` in the wrong order

`enumerate` yields **`(index, value)`**, in that order, always.

```python
for v, i in enumerate(nums):      # ✗ v is the INDEX, i is the VALUE
    total += v                    #   → this sums indices, not values

for i, v in enumerate(nums):      # ✓ name them what they are
    total += v
```

The name you choose does not change what the built-in returns.

**The three to know cold:**

| Call | Yields |
|---|---|
| `enumerate(seq)` | `(index, value)` |
| `dict.items()` | `(key, value)` |
| `sorted(d.items(), key=...)` | still `(key, value)` tuples |

**Habit:** name loop variables after what they *are*: `i, v` or `idx, val`. Never `e` for something `enumerate` handed you first.

### Node vs value vs `.next`

Index-vs-value, linked-list edition.

| Expression | Is |
|---|---|
| `node` | your finger, pointing at a place |
| `node.val` | the payload |
| `node.next` | a **field of the list** |

```python
cur = cur.next        # moves YOUR FINGER. The list is unchanged.
cur.next = other      # moves A LINK. The list is now different.
```

> **Rebinding a local name walks. Rebinding a `.next` field edits.**

When the question is *"have I stood on this node?"*, store the node, not `node.val`: two different nodes can hold the same value. **Nodes are hashable by identity.**

### Names that describe arrival order, not role

**The wrong name is what makes the wrong line look right.**

```python
a = stack.pop(); b = stack.pop()   # ✗ a was pushed LAST; the names say nothing about that
cur = ListNode(0, head)            # ✗ a dummy head named like a walker
```

- With `a` and `b`, any later line that treats the two asymmetrically (compares them, subtracts them, puts one before the other) *reads* plausibly and can be backwards. Symmetric uses pass and asymmetric ones fail: **a half-correct submission, the worst kind**, because the examples you check first are the ones that hide it.

```python
newer = stack.pop()      # ✓ popped first, so it was pushed last
older = stack.pop()
```

> **Variables named after the order they arrived in, not the role they play, make every line downstream read plausibly and be silently wrong.**

This is index-vs-value one level up: not a position confused with a value, but a name confused with the role of the thing it holds.

### A parameter order that contradicts the caller

```python
def search(hi, lo, target):        # declared hi first
    while lo < hi: ...
search(start, len(nums) - 1, t)    # called low first  →  while high < low  →  FALSE ON ENTRY
```

**The body never executes, on any input.** The function silently degenerates into checking one element and returning.

> **`(lo, hi)`, in that order, in every signature you write.** Then the call site and the body read in the same order and cannot disagree.

### A rename where the old name still exists

The most dangerous kind, because nothing raises.

```python
def flood(r, c):
    stack = [(r, c)]
    while stack:
        sr, sc = stack.pop()
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc     # ✗ r, c are the function's PARAMETERS: the seed
```

`r` and `c` still exist and still hold valid coordinates, so every iteration computes the neighbours of the **starting** cell. The traversal never gets past distance 1.

> **The most dangerous rename is one where the old name still exists and still holds something plausible.** No crash: it silently answers a different question.

**Fix it structurally: in a recursive → iterative conversion, the popped item takes the recursive function's parameter names and the *seed* gets the new ones.** Then the loop body is character-for-character what was inside the recursive function, and there is nothing to rewrite.

### Stale names after a structural edit

```python
return head       # ✗ head still points at the node that USED to be first
```

Deleting, reversing or splicing does **not** update the names pointing at the old front. `return head` after reversing `[1,2]` returns `[1]`: no crash, a confident wrong answer.

| After | Return |
|---|---|
| a reversal | **`prev`**, the last node processed |
| any edit that can touch the front | **`dummy.next`**, permanently "whatever is currently first" |

> **And name the dummy `dummy`.** If you create it as `cur = ListNode(0, head)` and then walk `cur` forward, no name in scope means "the front", so `head` is the only thing that looks like an answer. `dummy = cur = ListNode(0, head)` fixes it.

The same bug at the call site: remove a parameter from a signature and leave it at a call, and you get a `TypeError` on arity.

---

## Common bugs: Python mechanics

### Missing `self.` on a recursive method call

**The mechanism:** Python resolves a bare name **Local → Enclosing function → Global → Builtins**. The class body is *not* in that chain, so a method's name is never found by bare lookup.

| | Lives in | Bare lookup finds it? | Call as |
|---|---|---|---|
| **Method** (class level, takes `self`) | class namespace | ❌ | `self.max_depth(...)` |
| **Nested function** (inside a function, no `self`) | enclosing function scope | ✅ | `depth(...)` |

One question answers it: *can a bare lookup reach it?*

```python
return find_min(nums)          # ✗ NameError
return self.find_min(nums)     # ✓
```

### Mixing a method and a nested function

Two conventions. Pick one; don't blend them.

```python
class Solution:                          # NESTED FUNCTION
    def solve(self, root):
        def depth(node):                 # no self
            if not node:
                return 0
            return 1 + max(depth(node.left), depth(node.right))   # bare call
        return depth(root)               # bare call

class Solution:                          # METHOD
    def depth(self, node):               # takes self, defined at CLASS level
        if not node:
            return 0
        return 1 + max(self.depth(node.left), self.depth(node.right))
    def solve(self, root):
        return self.depth(root)          # called on self
```

**If it's defined inside a function, it takes no `self` and is called bare.**

Blending them fails twice: `self.depth(...)` raises `AttributeError` (a nested function isn't an attribute of the class), and a nested `def depth(self, node)` called as `depth(x)` raises `TypeError`, missing argument.

Prefer **nested** in interviews: it can close over an accumulator (`best`, `output`), which a separate method can't without `self.`.

### Attribute names invented instead of read

The stub tells you the field names. Read it.

```python
root.value      # ✗ AttributeError: it's .val
node.val        # ✓
lst.delete(x)   # ✗ no such list method: it's .remove(x)
```

### A real method on the wrong type

```python
lst.remove(x)     # ✓ exists on a list
s.remove(x)       # ✗ AttributeError: strings are IMMUTABLE, so no mutating method exists
```

**Harder to catch than an invented name, because the method is real.** You've used it correctly many times, on the other type. The tell is not the method, it's **what it's being called on**.

> **Before any `.append` / `.pop` / `.remove` / `.sort` / `x[i] = …`, ask: is this thing mutable?** `list`, `dict`, `set` ✓ · **`str`, `tuple`, `frozenset`, `int` ✗**.
>
> **The same immutability fact forces `tuple(path)` for a set member and `tuple(sorted(d.items()))` for a dict key.** One property, three consequences.

What to write instead on a string: [`python-toolkit.md`](python-toolkit.md#the-list-methods-that-dont-exist-on-a-string), §The list methods that don't exist on a string.

### Typos that silently change meaning

```python
if a = b:        # ✗ SyntaxError: nothing runs at all
if a == b:       # ✓

root-right       # ✗ subtraction; NameError on `right`
root.right       # ✓

fast = head.next # ✗ inside the loop, where fast = fast.next was meant: fast never moves on
low = mid - 1    # ✗ when the variable is called lo
lo = mid - 1     # ✓
```

The last pair is the dangerous one: assigning to a misspelled name is legal Python. It creates a new variable, the real one never changes, and a loop that depends on it never ends.

### Assignment makes a name local for the whole function

```python
def count_visits(graph, start):
    visits = 0
    def dfs(u):
        if visits > LIMIT:      # ← READ.  UnboundLocalError
            ...
        visits += 1             # ← the assignment that made `visits` local
```

> **If a name is assigned *anywhere* in a function, Python treats it as local to that function for the whole function.** That is decided when the function is compiled, before a single line runs. It does not matter that the assignment is on line 20.

So the read on the first line looks for a local that has no value yet.

| You want to | Declaration |
|---|---|
| **Read** an outer name | none |
| **Mutate** the object an outer name points to, e.g. `lst.append(x)` | none |
| **Rebind** a name in an enclosing **function**: `x = ...`, `x += ...` | **`nonlocal x`** |

⚠️ **`+=` is both a read and an assignment**, which is why it's the form that always trips this.

⚠️ **The silent twin is worse:** if you only *assign* and never read, there's no error. Python makes a local, sets it, discards it, and the outer name is untouched. A `balanced = False` inside a nested helper, without `nonlocal`, leaves the outer `balanced` at `True` for every input.

> **In backtracking this never has to come up:** `path.append` / `path.pop` / `seen.add` / `seen.discard` are all **mutations**, so no declaration is needed. **The moment you write `visits += 1` on a closure variable, you have chosen the one form that requires `nonlocal`**, and usually the real fix is that the state should have been a parameter or a mutated container, not a rebound name.

### Assigning to the parameter, expecting the structure to change

```python
node = None            # ✗ deletes nothing
node = node.right      # ✗ replaces nothing
```

`node` is **your local name**. `parent.left` is the **tree's** name. Rebinding a parameter moves a sticky note, not a branch: the code runs, returns, and leaves the structure byte-for-byte identical. **No crash, no wrong answer, no visible change at all.**

> **Count the lines that assign to a `.left`, `.right` or `.next`. Zero → the structure cannot have changed.**

The fix is one of two, and the second is cheaper: write `parent.left = x` (needs `parent` carried), or **return the replacement and let the caller assign it**: `node.left = f(node.left)`.

**Same root as stale names and the `nonlocal` bug: binding a name is not mutating an object.**

---

## Common bugs: returns and recursion

### Missing `return`

A Python function with no `return` returns `None`. Silent, and fatal.

```python
result.append(item)
# ...function ends, returns None       ✗
return result                        # ✓
```

### Returning the wrong type

Check the signature. `-> int` means an int, not a list. `-> List[List[int]]` means a list *of lists*.

```python
if n == 1: return nums        # ✗ returns a list
if n == 1: return nums[0]     # ✓
```

### Wrong base-case shape

```python
if node.left is None and node.right is None:   # ✗ "am I a leaf": drops the leaf's
    return []                                  #   own value, crashes on one-child nodes

if not node:                                   # ✓ "am I None": at the TOP
    return
```

### `return` inside the neighbour loop

```python
for dr, dc in DIRS:
    if <valid>: return dfs(nr, nc, nodes)   # ✗ the FIRST valid neighbour ends the function
```

> **`return` does not mean "recurse". It means "leave this function now."** A `return` inside a loop is a `break` that also ends the function.

It *looks* like it works: the recursion happens for that one neighbour, so it explores a **path** instead of a **region**, and an outer loop then treats the orphaned cells as separate components.

> **The eye-check: does this function have a return value?** If its job is to mutate a shared accumulator, it returns nothing, **so no call to it is ever prefixed with `return`.**

Root cause: blending *accumulate-into-shared* (an accumulator the function mutates) with *return-up*. Pick one.

### When the function does return a value

The rule was never "don't return inside a loop." Getting it wrong in the other direction is just as broken.

A search function (*"does any choice work?"*) genuinely should leave early. **But there are two ways to write it and only one is correct:**

```python
return dfs(nr, nc, ...)          # ✗ "whatever the FIRST child says is my answer"
if dfs(nr, nc, ...): return True # ✓ "return on SUCCESS. On failure, keep looping"
```

> **A failed branch is not an answer. It is one option eliminated.** `return dfs(...)` hands the first child's *failure* back as the whole function's verdict, so the remaining directions are never tried: the same defect as above, wearing a legal-looking `return`.

**The complete decision, read off the signature:**

| Does this function return a value? | Inside the choice loop | After the loop |
|---|---|---|
| **No**: it mutates a shared accumulator | `dfs(...)` **bare**. Never prefixed with `return` | nothing |
| **Yes, a bool**: *"does any work?"* | **`if dfs(...): return True`** | **`return False`** |
| **Yes, a number**: *"what's the best?"* | `best = max(best, dfs(...))` | `return best` |

⚠️ **Row 2's `return False` is not optional.** A function that falls off the end returns `None`. It *behaves* correctly because `None` is falsy, which means it is correct because of a fact about the surrounding code. **An interviewer reads a missing `return` as not knowing what the function returns.**

### The un-mark must run on every exit

> **"At the end" is not a place when a function has more than one `return`.**

```python
def dfs(u, ...):
    on_path.add(u)                         # ← the mark
    for v in graph[u]:
        if v not in on_path and dfs(v, ...):
            return True                    # ← EXIT 1, after the mark
    return False                           # ← EXIT 2, after the mark
```

**Every `return` that executes after the mark has to un-mark first.** Two exits, two restores, or restructure so there is one:

```python
    on_path.add(u)                                                     # choose
    found = any(dfs(v, ...) for v in graph[u] if v not in on_path)     # explore: any() still short-circuits
    on_path.discard(u)                                                 # undo, on the ONE path out
    return found
```

> **The placement rule: the undo sits at the same indentation as the mark, and after it there must be no reachable `return` that skips it.** If the mark is the first line of the function, the undo is the last thing before every exit.

**The mechanical check, which beats "remember to undo":**

> **Count the mutations before the recursive call. Count the restores after it. Two and one is always a bug.**

⚠️ **It often still passes on small inputs**, because once the answer is `True` everything unwinds and nobody reads the stale marks again. **Passing is not evidence.** The predicate is wrong (*"used on any path I've tried"* instead of *"used on this path"*) and it fails the moment a failed branch shares nodes with a later one. A `used` array that is never cleared in a permutation generator produces one permutation instead of all of them.

The permanent-mark cousin lives in graph DFS: forgetting the line that marks a node finished. Both are one line, both sit at the end of the function, and neither raises.

---

## Common bugs: loops, guards and bounds

### `%` where you meant `//`

```python
mid = n % 2      # ✗ this is 0 or 1. Always.
mid = n // 2     # ✓ integer division: the midpoint
```

### A midpoint that ignores `lo`

```python
mid = hi // 2            # ✗ the midpoint of [0, hi]: correct only on iteration 1
mid = (lo + hi) // 2     # ✓ the midpoint of the CURRENT range
```

**A midpoint splits the range you just described, and a range has two ends.** Read it off the range; don't recall the formula.

### Bounds or state that can't express the answer

```python
lo, hi = 0, len(nums) - 1     # ✗ when the answer can be len(nums)
```

> **`lo` and `hi` are the smallest and largest values the *answer* could take, not the ends of the array.**

**The test:** *"what if the target is bigger than every element?"* If that has an answer and it's `n`, `hi` must reach `n`.

⚠️ **This never crashes.** The invariant is false *before the first iteration*, so every correct line afterwards is wasted and the function returns a confident wrong number. It can make a valid answer arithmetically unreachable on every input.

The same bug outside binary search: `prev = head` where reversing a list needs `prev = None` (the invariant is false before iteration 1), `return head` after a deletion that can remove the front, a single scalar minimum where the problem needs one per position, one counter where there are n distances.

### A structure that can't express the answer

The container cousin of the bug above. **Wrong bounds fail silently with a wrong number; this one fails by growing branches**, and that version you can *feel* while writing.

Say the answer is the largest value you computed for any item, and some items start with a value already known. If you record only the values that *changed*, the case where nothing changed looks like `[]`, which is indistinguishable from "no answer". Record every item's value, the starting ones included, and the empty case is no longer a case: it becomes `max(values, default=0)`.

| | Records | "Nothing changed" looks like |
|---|---|---|
| only the changes | changed items | `[]`, **indistinguishable from "no answer"** |
| every item's value | starting items included | starting values only → `max` is still right ✓ |

> **When you stack special cases at the end of a function, suspect the structure you're reading from, not the cases. Each branch is patching information the structure dropped.** A patch that fixes *most* of the failures is the tell that the structure is wrong.

### A negative index wraps instead of crashing

```python
return values[lo - 1]      # lo == 0  →  values[-1]  →  the LAST element
```

Python wraps. No `IndexError`, no warning: the "nothing qualifies" case silently returns the **last** value. A pointer set to a value by mistake (`lo = nums[i]`) can go negative the same way and read from the end, spinning a loop forever instead of raising.

**Whenever you write `x - 1` as an index, ask what happens at `x == 0`.**

### Guards copied from another problem

A guard that was load-bearing in one problem decays when it is carried to the next:

| Where | State |
|---|---|
| In the problem it was written for | **Load-bearing**: the bounds made the guarded state reachable, so the guard caught it |
| Carried to a problem whose bounds rule that state out | **Dead**: the condition can never be true |

> **A guard carried into a new problem is always one of two things: dead, or wrong.** The thing it depended on didn't come with it.

**Ask: what state does this defend against, and can my current code reach that state?** If no, delete it. Don't patch a bad state, and don't inherit a patch either.

The mirror image is just as common: a condition the new problem needs (a grid's `== '1'` cell check, say) **omitted** because the template it came from didn't have one. And it applies to analysis too: a complexity sentence carried from a different-shaped problem is a guard copied without re-deriving.

### The guard asymmetry

The impossible check written, the necessary one missing, in one line:

```python
while prev and cur:           # ✗
    after = cur.next.next
```

- `cur.next` is dereferenced and **never checked** → `AttributeError`
- `prev` trails `cur` and **cannot** be `None` while `cur` isn't → checked anyway

```python
while cur and cur.next:       # ✓ guards left to right, in DEREFERENCE order
```

> **Ask what must be true for the next line to be safe, and write those tests in the order the attributes are read.** `and` short-circuits, so each test protects the one after it.

⚠️ **`node.next.next` needs two guards, not one.**

Two more forms of the same asymmetry:
- `>= 0` where `> 0` was needed on a counter of "still missing". **Zero means exactly enough, which is still valid.** Decide what each boundary value means before choosing the comparison.
- `if stack[-1]:` reads `False` when the top is `0`, a legal item. Test emptiness with `if stack:` and compare values explicitly.

### The pointer advance belongs outside the guard

```python
while missing == 0:
    if c in need:            # ← guards the BOOKKEEPING only
        need[c] += 1
    left += 1                # ← ALWAYS. Not a decision. Not indented.
```

Put `left += 1` inside the `if` and the body does nothing whenever the leftmost item isn't one you track: **the header stays true forever.** Any input whose window starts with an untracked character hangs.

> **A guard decides whether there's state to update, never whether to move.** Any loop whose advance is conditional needs a separate proof that the condition eventually holds, and "eventually holds" is usually false.

**Test every loop this way: name the line that guarantees progress, then check that no branch can skip it.** For `while True` this isn't optional: the exit is reachable **if and only if** some quantity strictly moves toward it and never moves back.

**Also: a corrupt counter is unrecoverable.** `remaining -= 1` on release where `+= 1` was meant drives the counter to −1, and then **no loop header anywhere can recover**: `== 0` is false, `> 0` is false. When a trace shows a counter going negative, stop tracing and fix the update; the loop conditions aren't the bug.

### A `for` loop variable is not yours to move

```python
for lo in range(len(s)):
    ...
    lo += 1        # ✗ silently discarded at the top of the next iteration
```

Python rebinds the target from the iterator every iteration, so the `+= 1` dies at the end of the pass. In a sliding window this destroys correctness **and** the amortisation argument at once: with `left` restarting, the nesting really is quadratic.

> **Any pointer the body moves must be a plain variable declared before the loop.** When two pointers each advance under their own rule, **at most one** can be the `for` target, and only the one that advances unconditionally by exactly one.

### Reading a loop variable after the loop

```python
for i, v in enumerate(nums):
    ...
# later, in a DIFFERENT loop:
output.append([v, w, i])        # ✗ i and v still hold their LAST values
```

Python leaks loop variables into the enclosing scope, so this doesn't raise: it silently uses a stale value from the previous loop. **A variable defined in one loop and used in another is almost always a bug.** And if the loop ran zero times, the variable doesn't exist: `return token` after `for token in tokens` raises `UnboundLocalError` on empty input, or returns the wrong thing on a one-item input.

### Reading a header variable before the body assigns it

```python
while lo < n and c not in need:   # ✗ c is assigned inside the body
    c = s[lo]
    ...
```

On entry `c` doesn't exist yet (`NameError`), and on every later check the header reads last iteration's value. **Two spellings of one value (`c` and `s[lo]`) is the smell.** Use the expression in the header, or assign before the loop and again at the end of the body.

### De Morgan on a loop guard

```python
while hi < n or remaining == 0:    # ✗ "keep going while EITHER holds"
while hi < n and remaining > 0:    # ✓ what was meant
```

Negating a compound condition flips `and` ↔ `or` **and** each comparison. Getting one of the two flips wrong gives an `IndexError` on the smallest input. **Write the condition for staying in the loop directly, in words, before writing it in code.**

### Mutating a list while iterating over it

```python
for x in stack:
    output.append(0)
    stack.pop()          # ✗ length shrinks while the index advances
```

On a 4-element stack this appends **two** zeros, not four. **No crash, no warning.**

A `dict` or a `set` is the loud version: adding or removing a key while you loop over it raises `RuntimeError: dictionary changed size during iteration` (`Set changed size during iteration` for a set). Loop over `list(d)` instead.

> **Iterate over a copy, build a new list, or use `while stack:`.** Never iterate and mutate the same list at once.

### A query that mutates

```python
def peek(self) -> int:
    return self.stack.pop()     # ✗ "what's on top" is not "remove the top"
```

`pop` is destructive and there is no undo except pushing back, which is the smell that says you should have peeked.

> **Before every `stack[-1]` or `.pop()`: is this item finished, or am I only reading it?**

### The heap tuple in the wrong order

`heapq` compares tuples **left to right**. Element 0 decides the pop order; everything after it is a tiebreaker you did not ask for.

```python
heapq.heappush(heap, (point, cost))         # ✗ orders by the point's x-coordinate, then y
heapq.heappush(heap, (cost, point))         # ✓ orders by cost
```

> **Write it as `(what_you_are_minimising, what_you_need_back)`.** If element 0 is not the quantity named in the problem statement, the heap is sorting the wrong thing.

**Why it survives review:** it still pops, still terminates, still returns a plausible number, and can **pass the example in the prompt** while failing on many random inputs.

**The 30-second check:** read element 0 of every `heappush` in the function. They must all be the same quantity, and that quantity must be the one in the problem statement.

---

## Common bugs: placement and dead code

### Placement: the right line in the wrong scope

The line is correct. Only its indentation is wrong, which is why re-reading the code finds nothing.

The job: if no item in a group is bad, mark the whole group.

```python
all_good = True
for x in group:
    if is_bad(x):
        all_good = False
    if all_good:                         # ✗ INSIDE the loop: runs once per item
        for y in group:
            mark(y)
```

The loop is doing **two different jobs**, and one has to finish before the other starts:

| Job | Code |
|---|---|
| **Decide** | `if is_bad(x): all_good = False` |
| **Act** | `for y in group: mark(y)` |

With the action inside the decision loop, it fires **before the disqualifying evidence has been seen**:

| Iteration | x | bad? | `all_good` | `if all_good:` |
|---|---|---|---|---|
| 1 | first item | no | still **True** | **fires → marks everything** ✗ |
| 2 | second item | **yes** | set to False | too late: the group is already marked |

And if `group` is a `set`, the iteration order is arbitrary, so it fires on some inputs and not others.

> **Finish deciding before you act. A flag being computed by a loop is not trustworthy until that loop has ended.** Reading it inside the loop reads a half-computed value.

**The stronger fix is to remove the flag**, so there's nothing half-computed to read:

```python
if not any(is_bad(x) for x in group):
    for y in group:
        mark(y)
```

*A special case you can design away beats one you handle.*

### Once per node or once per level

In a level-order BFS, every line belongs to exactly one loop:

- `node = queue.popleft()` **outside** the `for` loop → pops once per level, then processes that same node `level_size` times
- `output.append(level)` **missing entirely** → the accumulator is built and then discarded; every input returns `[]`

**Ask of every line: does this run once per node, once per level, or once per call?** Then check it sits in the loop that matches.

### Dead code

```python
candidates = list(range(1, max(nums) + 1))   # ✗ hundreds of millions of ints, never read
```

When `max(nums)` is large, that one line costs gigabytes and a Time Limit Exceeded, on a line that contributes nothing to the answer. Dead code usually is a fossil from the brute force, left behind when the loop stopped consuming it.

> **The check: for every variable you assign, where is it read?** Two seconds per variable. If the answer is "nowhere", delete it.

An interviewer reads an unused variable as *"not sure what their own solution does."*

### Dead code in disguise: the no-op cast and the unused index

```python
stack.append(int(x))              # ✗ x is already an int. A cast that does nothing
for i, item in enumerate(items):  # ✗ i is never read. An unused assignment that looks like idiom
```

**A no-op cast reads as defensiveness. An unused `enumerate` index reads as idiom.** Neither is. *Where is it read?* still answers both.

### Dead branching: both arms assign the same value

```python
if node:                      # ✗ node is a node or None. There is no third case.
    nxt = node
else:
    nxt = None                # ...which IS node
```

Four lines collapse to `nxt = node`. **If both branches of an `if/else` assign the same thing, the `if/else` isn't choosing anything**: it protects against a difference that doesn't exist.

### Copy-paste replicates the defect

> **Three copies of the same logic is three places to be wrong and a fix that must be applied three times.**

**The cure is the generalisation, not the fix.** Summing two arrays of different lengths element by element: *"a missing element isn't a special case, it's a zero."* `while i < len(a) or j < len(b)`, with *"the element, or 0 if that array is exhausted"*, collapses a main loop, two drain loops and a trailing `if` into one block.

### The fix fossil

**A fix fossil is the scaffolding a *broken* approach needed, left standing after the fix.**

```python
res = set()                          # existed to dedup duplicate outputs
...                                  # then the prune stopped producing duplicates
return [list(u) for u in res]        # ✗ and the set stayed
```

> **After every fix, ask: what did this make unnecessary?** Planning fossils are built while thinking and never wired up. Repair fossils are harder to see, because they were load-bearing five minutes ago.

### The copy reflex: `[:]` where only a read was needed

`[:]` attached to a variable name instead of to a decision:

```python
len(path[:])   ·   sum(path[:])   ·   sorted(path[:])   ·   tuple(path[:])     # ✗ all four
```

Every one builds a whole new list so a function can walk it once and discard it: **an O(n) allocation at every node of an exponential tree.**

> **`[:]` is needed exactly where you *store* the list into something that outlives the next mutation.** `res.append(path[:])`: there, and nowhere else. **Reading never needs a copy.**

### Materialising every candidate

```python
candidates.append(s[lo:hi + 1])    # ✗ an O(n) slice for every candidate window
best = (hi - lo + 1, lo, hi)       # ✓ store the coordinates; slice once, at the end
```

A slice is a copy. Recording every candidate as a substring turns an O(n) scan into O(n²). **Store `(length, lo, hi)` and slice the winner once.**

### The right line kept for the wrong reason

A line that works is not a line you understand. Take `if done[u]: continue` in Dijkstra, explained as *"skip it in case of a cycle."*

| | |
|---|---|
| The stated reason | "cycles make it loop forever" |
| What happens without it on a **layered graph with no cycles** | the push count grows far past V, the number of nodes |
| So the line is | a **process-each-node-once** guard, the same role `visited` plays in BFS |

**Why it matters more than the bug:** the wrong reason predicts the wrong future edit. *"No cycles here, so I can drop it"* is the removal that this explanation licenses, and it is wrong.

> **After every fix, say what the line does in a sentence that does not name the symptom.** If the only justification you have is "it broke without it", you have a repair, not a rule. The same goes for a complexity bound: say what earns it (rounds, levels, pushes), not which algorithm it sounds like.
