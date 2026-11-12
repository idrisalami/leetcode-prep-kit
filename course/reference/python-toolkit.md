# The Python toolkit

**Answering "how am I supposed to know the collections library?"**

You're not supposed to know the standard library. You're supposed to know **five things from it**. That's the whole list. It's an afternoon of memorisation, not a body of knowledge, and it covers almost every coding interview problem.

**Which Python.** Everything here targets the Python 3 that LeetCode runs: pick **"Python3"** in the language dropdown, not "Python", which is Python 2. Nothing below needs a recent release; it all works on any Python 3.8 or later. LeetCode pre-imports most of these modules, but write the import anyway, since an interviewer's editor won't.

Everything here is **allowed in every interview** unless the interviewer explicitly says "implement it yourself." Using them is a *positive* signal: it says you know your language. Hand-rolling a hash map when `dict` exists is not impressive, it's slow.

---

## The five

```python
from collections import deque, defaultdict, Counter
import heapq
from functools import lru_cache      # occasional
```

### 1. `deque`: the queue

Pronounced "deck", short for *double-ended queue*. A list where you can add and remove at **both** ends in O(1).

```python
from collections import deque

q = deque()           # empty
q = deque([root])     # containing one item
q = deque([1, 2, 3])  # containing three

q.append(x)      # add to the RIGHT
q.popleft()      # remove & return from the LEFT  — O(1)
q.appendleft(x)  # add to the LEFT
q.pop()          # remove & return from the RIGHT
len(q)           # how many
```

**Use it for:** BFS (always), sliding windows, anything needing FIFO.

**Why not a plain list?** `list.pop(0)` works but is **O(n)**: removing the front shifts every other element left one slot. Inside a loop over n items that turns your O(n) algorithm into O(n²). `deque.popleft()` is O(1). Interviewers notice this.

**Gotcha:** `deque([root])`, not `deque(root)`. The constructor takes an *iterable* and copies its items. `deque(root)` tries to iterate a TreeNode and raises TypeError.

### 2. `defaultdict`: the dict that fills itself in

```python
from collections import defaultdict

graph = defaultdict(list)    # missing key → []
graph[1].append(2)           # just works, no setup

counts = defaultdict(int)    # missing key → 0
counts['a'] += 1             # just works
```

Without it you write `if k not in d: d[k] = []` everywhere. **Use it for:** graph adjacency lists, grouping, counting.

#### Which counting tool? Two rules

> **Counting frequencies → `Counter`. Grouping into lists → `defaultdict(list)`.**

`defaultdict(int)` is not wrong, just redundant: anywhere you'd reach for it, `Counter` is the same code and safer.

**Why `Counter` and not `defaultdict(int)`:** `defaultdict` **inserts on read**.

```python
d = defaultdict(int)
if d['a'] == 0:      # ← CREATES key 'a' with value 0
    pass
len(d)               # 1, not 0 — a phantom key you never counted
```

A stray read pollutes `len()`, iteration, and anything you return. `Counter` returns `0` for a missing key **without** storing it, so it has the convenience and not the footgun. (Both insert normally when you *write*: `c[x] += 1` is a read then a write. The difference is reads only.)

**`d.get(k, default)`: keep this one for *reading*, not writing.** You'll never need to write `d[k] = 1 + d.get(k, 0)`, but it appears in a large share of editorial solutions, so recognise it. It's a non-inserting read on a plain `dict`.

> **The reason to use any of these over `if k in d: ... else: ...` is that they delete the branch.** A branch you never write is a branch you can't get wrong. It is easy to test the index in the `if` line (`if i in d`) while the line below it correctly updates the character (`d[s[i]] += 1`). With `Counter`, there is no `if` line to get wrong.

### 3. `Counter`: frequency counting in one line

```python
from collections import Counter

c = Counter("aabbbc")          # {'a':2, 'b':3, 'c':1}
c = Counter([1,1,2])           # {1:2, 2:1}
c.most_common(2)               # [('b',3), ('a',2)]
c['z']                         # 0 for a missing key, and nothing is inserted
```

A `Counter` is a `dict` underneath, so `==`, `.items()`, `.keys()` and `in` behave exactly as they do on a dict.

**Use it for:** frequency counts, top-K, "how many times does X appear".

### 4. `heapq`: the min-heap

**What it is:** a binary tree where every parent is ≤ both children. Two consequences: **the root is the global minimum** (peek is O(1)), and **nothing else is ordered**.

> **A heap is *partially* ordered. That's the whole trade:** you pay only for knowing where the minimum is, not for arranging everything else.

Stored as a **plain list**, not nodes: the children of index `i` live at `2i+1` and `2i+2`, which is why `heapq` works directly on a list.

**Why push/pop are O(log n):** push appends at the end and swaps upward while smaller than its parent; pop takes the root, moves the last element there, and swaps downward. Either way you walk one root-to-leaf path, and a complete binary tree over n nodes has height log₂ n.

```python
import heapq

h = []
heapq.heappush(h, 5)            # O(log n)
smallest = heapq.heappop(h)     # O(log n) — always the MINIMUM
h[0]                            # peek, O(1), no removal
heapq.heapify(lst)              # list → heap, in place, O(n)  ← not n log n
len(h)

heapq.nlargest(k, lst)                     # does the whole job
heapq.nlargest(k, words, key=len)          # …with a key function
heapq.nsmallest(k, lst)
```

**Python has no max-heap.** Negate on the way in and out: `heapq.heappush(h, -x)` → `-heapq.heappop(h)`.

**It compares tuples lexicographically:** `(count, value)` orders by count first. That's how you attach a payload to a priority.

> ⚠️ **Order matters, and getting it backwards fails silently.** Write the tuple as **`(what_you_are_minimising, what_you_need_back)`**. With the reversed form, `(point, cost)`, the heap orders by the point's x-coordinate. It still runs, still terminates, often still passes the example in the prompt, and is wrong on a large share of random inputs.
>
> **Payloads must be comparable too.** If two entries tie on element 0, Python compares element 1. `list` and `tuple` compare fine; a custom object raises `TypeError: '<' not supported`. Insert a tiebreaker counter, `(priority, next(counter), obj)`, when the payload isn't orderable.

#### The top-K pattern: use a MIN-heap for the k LARGEST

Keep a min-heap that never holds more than k items: push each new item, and whenever the size passes k, pop the smallest. What is left is the k largest, unordered. Module 10 (heaps) builds this out.

> **The heap's minimum is the weakest member of your current top-k**, exactly the one to discard when a better candidate arrives. That's why a min-heap yields the maximums.

**O(n log k):** n pushes and pops on a heap that never exceeds size k.

| | Cost | k=10, n=10⁶ |
|---|---|---|
| Sort everything | O(n log n) | log n ≈ 20 |
| Heap of size k | **O(n log k)** | log k ≈ 3.3 |

Also O(k) space instead of O(n); it matters when n doesn't fit in memory.

**Use it for:** top-K, kth largest, merging sorted lists, Dijkstra, "repeatedly pull the smallest".

**The signal:** *"k largest / k smallest / k most frequent / kth largest."*

### 5. `sorted` and `set`: builtins, no import

```python
sorted(nums)                       # new sorted list, O(n log n)
sorted(words, key=len)             # sort by a computed key
sorted(pts, key=lambda p: p[1])    # sort by second element
sorted(nums, reverse=True)
nums.sort()                        # in place, no return value

set(nums)                          # dedupe / O(1) membership
seen = set(); seen.add(x); x in seen
```

**Sorting is a solution tool, not just a utility.** A large share of array problems become easy once sorted. If you're stuck on an array problem, "what if it were sorted?" is one of the highest-yield questions you can ask.

> ⚠️ **`set(x)` *iterates* `x`. It does not wrap it.** A set holding one tuple is `{(r, c)}`, never `set((r, c))`:
>
> ```python
> set((0, 1))      # {0, 1}      ← two INTEGERS. (0, 1) not in it
> {(0, 1)}         # {(0, 1)}    ← one tuple. What you meant
> set("ab")        # {'a', 'b'}  ← same trap with a string
> set()            # empty — the only way. {} is an empty DICT
> ```
>
> In a grid search, `visited = set((r, c))` leaves the start cell unmarked, so a path can step back onto it. No error, just wrong answers. The same rule covers `list(x)`, `tuple(x)` and `dict(x)`: **the constructor consumes an iterable; the literal wraps.**

---

## Empty-safe built-ins: the anti-special-case set

Every one of these turns *"handle the empty case"* into *"there is no case."*

```python
max(xs, default=0)          # ✗ ValueError on empty without it
min(xs, default=0)
sum(xs)                     # already 0 on empty — no default needed
any(xs) · all(xs)           # False / True on empty. all([]) is True — know this one
next(it, None)              # ✗ StopIteration without the fallback
d.get(k, 0)                 # ✗ KeyError with d[k]
d.setdefault(k, []).append(x)
''.join(parts)              # '' on empty
```

> **`max()` and `min()` raise on an empty sequence. That is a common source of a hand-written `if xs:` branch.** `default=` deletes it.

**Why this matters beyond the syntax:** a trailing `if xs: return max(xs)` / `else: return 0` is a **special case you're handling**. `default=` is a special case you **designed away**, the same principle as a `float('-inf')` sentinel, and the rule from binary search: *every branch is a place to be wrong.*

Don't build a parallel structure to dodge a keyword you half-remember. Look it up.

### If you don't remember the keyword: say it, never build around it

> *"I want the max of these, defaulting to 0 when it's empty. I think it's `max(x, default=0)`, I'd check the exact keyword."*

**Three seconds, and it scores.** Knowing the operation should exist is the signal being tested. Constructing a parallel data structure to avoid a keyword you're 80% sure of is the *worse* answer even when it works: it reads as not knowing the language, and it multiplies the branches you have to get right.

Same family as hand-writing merge sort instead of calling `sort()`, and hand-rolling a character-class test instead of `.isalnum()`. The rule is **if the helper has a stdlib name, type the stdlib name**, and its corollary is **if you're unsure of the name, say the name you think it is and move on.**

## Index of the min / max: argmin without a loop

```python
nums = [4, 1, 3, 1]

i = nums.index(min(nums))                        # 1 — two passes, still O(n). The default
i = min(range(len(nums)), key=lambda j: nums[j]) # 1 — one pass, index only
i, v = min(enumerate(nums), key=lambda p: p[1])  # (1, 1) — one pass, index AND value
```

| Case | Behaviour |
|---|---|
| Ties | all three return the **first** occurrence |
| Empty list | `ValueError`: guard it, or `min(..., default=...)` (see above) |
| Last occurrence | `len(nums) - 1 - nums[::-1].index(min(nums))` |
| `max` | same three forms; ties also give the first |
| Repeated queries while the list changes | each scan is O(n), so reach for a heap or a monotonic structure |

> **`key=` decides what is compared; the thing returned is still the element you iterated.** Iterate indices → you get an index back. Iterate `enumerate` pairs → you get a pair back.

## Comparing and sorting sequences: Python already does it

**Strings, lists and tuples compare directly.** You never need to convert characters to numbers first.

```python
'a' < 'b'                  # True  — strings compare lexicographically
sorted("banana")           # ['a','a','a','b','n','n']
[1,2,3] == [1,2,3]         # True  — lists compare ELEMENTWISE, not by identity
[1,2,3] < [1,2,4]          # True  — element by element, first difference decides
(1,'a') < (1,'b')          # True  — same for tuples
```

**No `ord()`, no manual index loop.** Converting to `ord` values before sorting costs an extra O(n) pass and O(n) memory to produce numbers that sort in exactly the same order the characters already did.

> **`==` on two lists is a full elementwise comparison.** Writing `for i in range(len(a)): if a[i] != b[i]` reimplements it.

**Sorting a string returns a *list* of characters**, not a string. `sorted("cat")` is `['a','c','t']`. To get a string back: `''.join(sorted("cat"))`, which gives `'act'`.

## `zip`: sorting two parallel arrays together

**The problem it solves.** When a problem hands you two arrays where index `i` of one belongs with index `i` of the other, such as `names[i]` and `scores[i]`, the correspondence is held **by position and by nothing else**. Sort one array on its own and the correspondence is destroyed, silently.

> **Parallel arrays are records that were never assembled. Zip them into records first, then sort the records.**

```python
rows = sorted(zip(scores, names))                 # by score, then name as tiebreak
rows = sorted(zip(scores, names), reverse=True)   # descending
rows = sorted(zip(a, b), key=lambda p: p[1])      # by the SECOND field
```

`zip` pairs elementwise and yields **tuples**; tuples compare element by element, so `sorted(zip(a, b))` sorts by the first field and breaks ties on the second. No `key=` needed for the common case.

**Unpacking:**

```python
for score, name in rows:         # unpack in the loop — no p[0]/p[1]
    ...
a, b = zip(*pairs)               # unzip, back to two sequences (of TUPLES, not lists)
```

⚠️ **`zip` returns an iterator and is consumed once.** `z = zip(a, b)`; iterate it twice and the second pass is empty. Wrap in `list(...)` or `sorted(...)` if you need it more than once.

⚠️ **`zip` stops at the shorter input, silently.** No error, no warning: the tail of the longer one is dropped. Same family as `while a and b` dropping the longer sequence's tail.

**And the same move without `zip`:** `sorted(range(n), key=lambda i: scores[i])` sorts the *indices*, which is what you want when you need to write the answer back into a per-index output array.

## Dict keys must be immutable: convert, don't invent

Anything used as a `dict` key or put in a `set` must be **hashable**, which in practice means **immutable**.

| Hashable ✓ | Not hashable ✗ |
|---|---|
| `int`, `str`, `float`, `bool`, `tuple`, `frozenset` | `list`, `dict`, `set` |

When the thing you naturally want as a key is mutable, there is a one-call conversion:

| Mutable | Immutable equivalent | Hashable? |
|---|---|---|
| `list` | `tuple(lst)` | ✓ |
| `set` | `frozenset(s)` | ✓ |
| `dict` | `tuple(sorted(d.items()))` or `frozenset(d.items())` | ✓ |

```python
d[[1, 2]] = x                # ✗ TypeError: unhashable type: 'list'
d[(1, 2)] = x                # ✓
d[tuple(lst)] = x            # ✓ a list's contents as a key
```

**Why the rule exists:** a mutable key could change after insertion, changing its hash, leaving it in the wrong slot, permanently unfindable.

> **Never write your own hash function.** "This list never changes, so morally it's immutable" is the right *instinct*, and `tuple()` makes it structurally true in one call.

`tuple` preserves order and costs O(k); `frozenset` ignores order and duplicates. Pick by whether order matters to identity.

### When `ord` / `chr` *are* the right tool

```python
ord('a')       # 97   character → its integer code
chr(97)        # 'a'  integer code → character
```

Exactly one common use: **indexing into a fixed-size array of counts**, when the alphabet is known to be 26 lowercase letters.

```python
count = [0] * 26
for c in s:
    count[ord(c) - ord('a')] += 1      # 'a'→0, 'b'→1, … 'z'→25
```

That buys **O(1) space** instead of a dict's O(k), the answer to "can you do it without a hash map?" Outside that pattern, reach for the characters themselves.

---

## String methods: the ten that come up

Same principle as the five collections: you're not supposed to know the string API, you're supposed to know **ten methods**. Every one below has appeared in a standard interview problem.

```python
s.lower()  ·  s.upper()          # case-fold, for case-insensitive comparison
s.isalnum()                      # letter or digit?
s.isalpha()  ·  s.isdigit()      # letter? / digit?
s.strip()                        # drop leading/trailing whitespace
s.split()                        # → list of words, splits on any whitespace
s.split(',')                     # → list, splits on a specific separator
''.join(parts)                   # list of strings → one string   ← the anti-quadratic
s.replace(a, b)                  # ALL occurrences
s.startswith(p)  ·  s.endswith(p)
s.count(x)                       # non-overlapping occurrences
s.find(x)                        # index, or -1 if absent
```

**`find` vs `index`:** `s.find(x)` returns `-1` when absent; `s.index(x)` **raises** `ValueError`. Reach for `find` unless you want the exception.

**Converting both ways:** `list(s)` → list of characters · `''.join(chars)` → back to a string.

### The one rule that makes all of them make sense

> **Strings are immutable, so no string method ever mutates. Every one returns a new string.**

```python
s.lower()            # ✗ computes a lowercase string and throws it away
s = s.lower()        # ✓ you have to reassign
```

Contrast with lists, which is where the confusion comes from:

| Call | Mutates? | Returns |
|---|---|---|
| `lst.sort()` | ✓ in place | `None` |
| `sorted(lst)` | ✗ | a new list |
| `s.lower()`, `s.replace(...)`, `s.strip()` | ✗ (**impossible**, strings are immutable) | a new string |

### The list methods that don't exist on a string

Reach for `s.remove(ch)` and you get **`AttributeError: 'str' object has no attribute 'remove'`**.

> **"No string method mutates" has a stronger consequence that is easier to use: the mutating methods are not there at all.** You will not get a wrong answer; you get an `AttributeError`, which is at least loud.

| You reach for | On a `str` | Do instead |
|---|---|---|
| `s.remove(ch)` | ✗ **doesn't exist** | `s.replace(ch, '', 1)`, which returns a **new** string |
| `s.append(ch)` | ✗ | `s + ch`, or build a `list` and `''.join` it |
| `s.pop()` | ✗ | `s[:-1]` |
| `s.sort()` | ✗ | `sorted(s)` → a **list** · `''.join(sorted(s))` → a string |
| `s[i] = ch` | ✗ **TypeError** | `lst = list(s); lst[i] = ch; s = ''.join(lst)` |
| `del s[i]` | ✗ | `s[:i] + s[i+1:]` |

> **If you need to mutate characters, convert once at the top and join once at the bottom:** `lst = list(s)` … `''.join(lst)`. **Doing it any other way inside a loop is the O(n²) trap below, one verb along.**

Note why this deserves its own table: the immutability rule above is phrased as a fact about *return values*, so it doesn't fire when you reach for a method that doesn't exist. Learn both phrasings.

**And this is exactly why `s += c` in a loop is O(n²):** each `+=` allocates a fresh string and copies everything so far. Build a **list** and `''.join` it once: O(n).

```python
parts = []
for c in s:
    parts.append(c.lower())      # O(1) each
return ''.join(parts)            # O(n) once
```

### Costs

| Operation | Cost |
|---|---|
| `s.lower()`, `s.strip()`, `s.replace()`, `s[::-1]` | **O(n)**: each builds a whole new string |
| `c.isalnum()`, `c.lower()` on **one** character | O(1) |
| `x in s` (substring search) | **O(n·m)**, not a hash lookup. `in` on a *set* is O(1); on a string it scans |
| `''.join(parts)` | O(total length), once |

**The trap:** these read like one-step operations and sit innocently inside loops. A one-line call is not a one-step operation.

### If you blank on the name

Say what you mean and move on: *"I want the is-alphanumeric check here, `.isalnum()`, I think."* Interviewers do not care about spelling. **Knowing that a built-in should exist is the scored signal**; reconstructing `if 'a' <= c <= 'z' or '0' <= c <= '9'` by hand is the one that costs you.

## Python truthiness: why `while queue:` works

Empty containers are **falsy**. These pairs are identical:

```python
while queue:            while len(queue) > 0:
if not root:            if root is None:
if not nums:            if len(nums) == 0:
```

Falsy: `None`, `0`, `""`, `[]`, `{}`, `set()`, `False`.

The short forms are idiomatic and what interviewers expect to read.

**One catch:** `if not node` is also true when `node` is `0`. Fine for tree nodes (an object is always truthy), dangerous for integers. When the value could legitimately be 0, write `if node is None`.

---

## Everyday syntax

### Loop control: `continue`, `break`, `pass`, `return`

`continue` does not "do nothing". It is a **jump**.

| Keyword | Effect |
|---|---|
| **`continue`** | abandon the rest of **this** iteration, jump to the next one |
| **`break`** | stop the loop **entirely** |
| **`return`** | leave the whole **function** (so inside a loop it's a `break` that also exits) |
| **`pass`** | do nothing: a placeholder so a block isn't empty. **The only one that truly does nothing** |

```python
for x in items:
    if x in skip:
        continue                  # ← every line below is SKIPPED for this x
    if is_bad(x):                 # ← only reached when x is not skipped
        return False
```

**The `continue` form is a *guard clause*:** handle the uninteresting case first, leave the main path unindented. It is exactly equivalent to nesting:

```python
for x in items:                   # identical behaviour, no continue
    if x not in skip:
        if is_bad(x):
            return False
```

Same style as the guards at the top of a grid DFS: bounds, cell value, visited, *then* the work. Cheapest disqualifying test first.

⚠️ **`return` inside a loop is a `break` that also ends the function.** See `bug-checklist.md`, §`return` inside the neighbour loop.

⚠️ **`break` where you meant `continue` fails quietly.** Write `else: break` meaning "skip this index" inside a backtracking loop, and every recursion level stops at its first skipped index, so whole branches of the answer are never built. No crash, no obviously wrong answer, just a *subset* of the answers: the hardest kind to spot on a small test.

**In a backtracking loop the `for` is the child list**, so the three words have tree meanings:

| Word | Tree meaning | When it's right |
|---|---|---|
| `continue` | *not this child, try the next one* | skipping one sibling for a reason that says nothing about the siblings after it |
| `break` | *no later child can work either* | **only when the children are sorted**, so failing this one implies failing all after it |
| `return` | *this node is done* | the base case; never inside the loop unless the whole subtree is finished |

**The test before typing either:** *does my reason for skipping this child also apply to every child after it?* Yes, and sorted → `break`. Otherwise → `continue`. Module 07 (backtracking) develops this.

```python
for i in range(n)              # 0 .. n-1
for i in range(1, n)           # 1 .. n-1
for i in range(n-1, -1, -1)    # n-1 down to 0
for i, x in enumerate(nums)    # index and value together
for a, b in zip(xs, ys)        # two lists in parallel

n // 2        # INTEGER division  ← what you want for a midpoint
n % 2         # remainder         ← NOT a midpoint
float('inf'), float('-inf')    # sentinels for min/max tracking
a, b = b, a                    # swap
```

`//` and `%` are one keystroke apart and mean different things. A midpoint is always `(lo + hi) // 2`. See `bug-checklist.md`, §`%` where you meant `//`.

### Comprehensions: the loops, in the same order, body first

The classic slip is a two-level comprehension written with one `for`.

> **Write the nested loops. Then move the body to the front. Nothing else changes position.**

```python
for r in range(rows):                     # [(r, c)
    for c in range(cols):                 #  for r in range(rows)
        if board[r][c] == target:         #  for c in range(cols)
            out.append((r, c))            #  if board[r][c] == target]
```

```python
[(r, c) for r in range(rows) for c in range(cols) if board[r][c] == target]
```

**The five forms:**

```python
[f(x) for x in xs]                    # map
[f(x) for x in xs if cond]            # map + filter        ← `if` goes at the END
[f(x, y) for x in xs for y in ys]     # nested — leftmost `for` is the OUTER loop
{k: v for k, v in pairs}              # dict comprehension
{f(x) for x in xs}                    # set comprehension — dedups for free
```

#### ⚠️ The two `if`s are different things

```python
[x for x in xs if x > 0]              # FILTER — at the end, no else. Drops elements
[x if x > 0 else 0 for x in xs]       # TERNARY — at the front, needs else. Keeps every element
```

**A filter changes the length; a ternary changes the values.** Putting the filter at the front is a `SyntaxError` (it wants an `else`); putting a ternary at the end silently isn't what you meant.

#### ⚠️ Traps

- **Order of `for` clauses is outer-to-inner, left to right**, the same order you'd type the loops. Reversing them iterates the wrong nesting.
- `[[0] * n for _ in range(m)]`, **never** `[[0] * n] * m`. The second form makes m references to *one* row, so writing to `grid[0][0]` changes every row.
- A comprehension **builds the whole list**. When you only need to iterate once, a generator (`any(...)`, `sum(...)`, `max(...)` with no brackets) allocates nothing.

```python
if any(dfs(r, c) for r, c in starts):     # ✓ short-circuits, allocates nothing
if True in [dfs(r, c) for r, c in starts]: # ✗ runs every call, then searches the list
```

### Slicing: `lst[start:stop:step]`

```python
nums[2:5]      # indices 2,3,4 — stop is EXCLUSIVE
nums[:k]       # first k
nums[k:]       # from k to the end
nums[-1]       # last element
nums[-k:]      # last k
nums[:]        # the WHOLE thing — i.e. a COPY. Both ends omitted
nums[::-1]     # reversed COPY
nums[::2]      # every second element
s[::-1]        # strings slice the same way
```

#### `lst[:]`: the copy idiom, and the bug it exists to prevent

You will type this line constantly in backtracking.

> **One colon, two slots: `lst[start : stop]`, both optional. Omit both and you've asked for the whole thing, which is a *new list* containing everything `lst` currently holds. The word doing the work is *new*.**

```python
res.append(path)      # ✗ files away a LABEL. The next path.pop() edits what you stored
res.append(path[:])   # ✓ files away a NEW BOX with today's contents
```

**A list variable is a label stuck on a box, not the box itself**, so *storing* a list is the same act as *binding* one: neither copies. `path[:]` · `list(path)` · `path.copy()` are three spellings of the same thing.

⚠️ **Shallow.** `grid[:]` copies the outer list and shares every row. For a grid of rows use `[row[:] for row in grid]`.

⚠️ **Not needed for strings.** `s + c` already makes a new string, because strings are immutable, which is why a string-valued path never shows this bug and a list-valued one always does.

#### Reading `[::-1]`: count the colons

Don't memorise the symbol; derive it.

> **Two colons means three slots.** `lst[start : stop : step]`, and every slot is optional.

```
lst[ : : -1]
     ↑ ↑  ↑
     │ │  └── step  = -1  → walk BACKWARDS, one at a time
     │ └───── stop  omitted → all the way
     └─────── start omitted → from the far end
```

So `[::-1]` reads as **"the whole thing, one at a time, backwards."**

**Why the omitted ends still work with a negative step:** the defaults *flip*. With `step > 0`, omitted `start` means the beginning and omitted `stop` means the end. With `step < 0` they reverse: `start` defaults to the **last** element and `stop` to just past the **first**. That's the whole mechanism, and it's why you never write the endpoints for a reversal.

| Slice | Means |
|---|---|
| `lst[::-1]` | reversed, whole thing |
| `lst[::2]` | every second element, forwards |
| `lst[::-2]` | every second element, backwards |
| `lst[3:]` | from index 3 to the end |
| `lst[:3]` | the first three (stop is **exclusive**) |

### ⚠️ `-1` means two completely different things

The single most confusable pair, and it's the index-vs-value confusion in punctuation (see `bug-checklist.md`, §Index vs value):

```python
nums[-1]        # NO colon  → an INDEX. The last element. Returns ONE VALUE.
nums[::-1]      # two colons → a SLICE, step -1. Returns the WHOLE SEQUENCE, reversed.
```

**Count the colons before you read the `-1`.** No colon → position. Colons → direction.

**And it copies.** `lst[::-1]` allocates a whole new sequence: O(n) time, O(n) space. When you only need to *iterate* backwards, `reversed(lst)` is a lazy iterator and allocates nothing. For strings `s[::-1]` is the idiom (shorter than `''.join(reversed(s))`), but it's still a copy.

**Slicing clamps; it never raises.** Indexing does.

```python
s = "abc"
s[10:]      # ''     no error
s[1:99]     # 'bc'   clamped to the end
s[5:2]      # ''     empty when start >= stop
s[10]       # ✗ IndexError — *indexing* raises, *slicing* doesn't
```

Convenient, and dangerous: an out-of-range slice returns something plausible instead of failing loudly. **An omitted upper bound runs to the very end:** `s[k:]` grabs everything after `k`, including positions you haven't processed yet. In a left-to-right scan, slicing `s[j+1:]` when you meant the window `s[j+1:i+1]` silently includes the unread tail.

**Every slice makes a copy: O(n) time and O(n) space.** That matters:

```python
nums[::-1]        # ✗ allocates a whole new list
reversed(nums)    # ✓ lazy iterator, allocates nothing
```

> ⚠️ **Reversing the data does NOT reverse the indices.** `enumerate(nums[::-1])` numbers the *new* list from 0, so `i` walks forwards while the values walk backwards: they disagree from the first step. When you need positions in the **original** array, reverse the indices instead:
> ```python
> for i in range(len(nums) - 1, -1, -1):    # i and nums[i] can never disagree
> for i in reversed(range(len(nums))):      # same, more readable
> ```

---

## Rules

1. **Built-ins are always allowed.** Don't hand-roll what the language gives you.
2. **Say what you're reaching for out loud**: "I'll use a deque so the pops are O(1)." That's a scored signal even if the code is imperfect.
3. **If you blank on a method name**, say what you mean ("I want to pop from the front here") and keep going. Interviewers don't care about exact spelling. They care that you knew a queue was the right structure.
