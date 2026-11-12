# Decision Rules

<!-- toc -->
**Contents**

- [Signals → what to reach for](#signals--what-to-reach-for)
- [Choosing a traversal: BFS or DFS](#choosing-a-traversal-bfs-or-dfs)
- [Choosing a DFS order](#choosing-a-dfs-order)
- [Where to guard against `None`](#where-to-guard-against-none)
- [Comparing two structures: walk them in lockstep](#comparing-two-structures-walk-them-in-lockstep)
- [The three shapes of recursion](#the-three-shapes-of-recursion)
- [The three forms of a recursive call — and when each is right](#the-three-forms-of-a-recursive-call--and-when-each-is-right)
- [Detail: return-up vs accumulate-into-shared](#detail-return-up-vs-accumulate-into-shared)
- [Ordered, not exclusive](#ordered-not-exclusive)
- [Which *item* matters? — the question that names the container](#which-item-matters--the-question-that-names-the-container)
- [Choosing a container](#choosing-a-container)
- [Stack vs queue behaviour](#stack-vs-queue-behaviour)
- [Array problems: ask the sorted question](#array-problems-ask-the-sorted-question)
- [Graphs: mark on push, not on pop](#graphs-mark-on-push-not-on-pop)
- [Arrays, lists and hashes](#arrays-lists-and-hashes)
  - [The cascade — run this when an array or string problem stalls](#the-cascade--run-this-when-an-array-or-string-problem-stalls)
  - [Remember vs Reuse — the discriminator](#remember-vs-reuse--the-discriminator)
  - [Hashing only pays if you build and query in the *same* pass](#hashing-only-pays-if-you-build-and-query-in-the-same-pass)
  - [Choosing the hash structure](#choosing-the-hash-structure)
  - [Key design — the actual skill in hashing](#key-design--the-actual-skill-in-hashing)
  - [The silent quadratics](#the-silent-quadratics)
  - [Aliasing and copying — lists bite harder than trees](#aliasing-and-copying--lists-bite-harder-than-trees)
  - [Editing a linked structure — there is no "delete", only "repoint"](#editing-a-linked-structure--there-is-no-delete-only-repoint)
  - [State the invariant before writing the loop](#state-the-invariant-before-writing-the-loop)
  - [Is it a sliding window? Four checks](#is-it-a-sliding-window-four-checks)
  - [Neither window pointer is ever a choice](#neither-window-pointer-is-ever-a-choice)
  - [Window direction: shrink while valid, or while invalid?](#window-direction-shrink-while-valid-or-while-invalid)
  - [Two pointers: which shape?](#two-pointers-which-shape)
- [Binary search](#binary-search)
  - [When to reach for it](#when-to-reach-for-it)
  - [The definition that makes every variant one algorithm](#the-definition-that-makes-every-variant-one-algorithm)
  - [The four setup decisions — where the bugs live](#the-four-setup-decisions--where-the-bugs-live)
  - [The one template to keep](#the-one-template-to-keep)
  - [Answer space](#answer-space)
  - [Searching part of an array](#searching-part-of-an-array)
  - [Rotated arrays](#rotated-arrays)
- [Linked lists](#linked-lists)
  - [The trade, and what it kills](#the-trade-and-what-it-kills)
  - [The four moves](#the-four-moves)
  - [The five rules](#the-five-rules)
  - [Which loop condition](#which-loop-condition)
  - [Replacing a hash set — the five escapes](#replacing-a-hash-set--the-five-escapes)
  - [Complexity — the template](#complexity--the-template)
- [Stacks and monotonic stacks](#stacks-and-monotonic-stacks)
  - [The container](#the-container)
  - [The sentence, before the loop body](#the-sentence-before-the-loop-body)
  - [The empty stack means something different in every problem](#the-empty-stack-means-something-different-in-every-problem)
  - [Monotonic stack — the four variants](#monotonic-stack--the-four-variants)
  - [The amortised sentence — say it unprompted](#the-amortised-sentence--say-it-unprompted)
  - [Carrying state in the slot](#carrying-state-in-the-slot)
  - [When it is *not* a stack](#when-it-is-not-a-stack)
- [Graphs — the decision tree](#graphs--the-decision-tree)
  - [First: the derivation runs one way, and it isn't the way it feels](#first-the-derivation-runs-one-way-and-it-isnt-the-way-it-feels)
  - [Q1 — Is this a graph problem?](#q1--is-this-a-graph-problem)
  - [Q2 — What is the OUTPUT? This is the top-level split](#q2--what-is-the-output-this-is-the-top-level-split)
  - [Q3a — Connectivity](#q3a--connectivity)
  - [Q3b — Shortest path](#q3b--shortest-path)
  - [Q3c — Ordering](#q3c--ordering)
  - [Q3d — Cycle detection](#q3d--cycle-detection)
  - [Q3e — Plain traversal](#q3e--plain-traversal)
  - [Q3f — MST](#q3f--mst)
  - [Q3g — The inversion: "for EVERY node, can it reach X?"](#q3g--the-inversion-for-every-node-can-it-reach-x)
  - [Q4 — What is a node? → the representation](#q4--what-is-a-node--the-representation)
  - [Q5 — What does `visited` mean? Read it off the row](#q5--what-does-visited-mean-read-it-off-the-row)
  - [The three reading questions, not algorithm questions](#the-three-reading-questions-not-algorithm-questions)
- [Backtracking](#backtracking)
  - [The one-line definition](#the-one-line-definition)
  - [The acid test — is this module 08 or module 07?](#the-acid-test--is-this-module-08-or-module-07)
  - [Signals](#signals)
  - [Before writing anything: name the node, the edge, the leaf](#before-writing-anything-name-the-node-the-edge-the-leaf)
  - [The skeleton, and the contract](#the-skeleton-and-the-contract)
  - [Which loop — the index is two independent switches](#which-loop--the-index-is-two-independent-switches)
  - [Two dedup mechanisms, not interchangeable](#two-dedup-mechanisms-not-interchangeable)
  - [Pruning — rank it before you write it](#pruning--rank-it-before-you-write-it)
  - [The `return` rule — read it off the signature](#the-return-rule--read-it-off-the-signature)
  - [Complexity of an exponential algorithm](#complexity-of-an-exponential-algorithm)
  - [When it stops being backtracking](#when-it-stops-being-backtracking)
- [Dynamic programming](#dynamic-programming)
  - [Two pointers or DP? — the discard test](#two-pointers-or-dp--the-discard-test)
  - ["How would I have known?" — four signals, three of them free](#how-would-i-have-known--four-signals-three-of-them-free)
- [Top-K and selection](#top-k-and-selection)
  - [The signal, and the four answers](#the-signal-and-the-four-answers)
  - [The rank rule — which heap, and where the answer is](#the-rank-rule--which-heap-and-where-the-answer-is)
  - [Quickselect — what makes it quickselect](#quickselect--what-makes-it-quickselect)
<!-- /toc -->

**"Which tool do I reach for?"** — the file that turns problems into patterns.

This file is the pattern vocabulary: a map from signal to tool. Solving every problem from first principles with nested loops is how everything comes out O(n²). Interviews are pattern recognition under time pressure, not invention, and the modules teach each pattern in depth. This file collects the decisions in one place, so you can find the right module section from what the problem says.

**How to use it:** reread it before every mock. When you're stuck in an interview, walk the [Signals](#signals--what-to-reach-for) table.

---

## Signals → what to reach for

The highest-value table here. Read the problem statement, find the signal, reach for the tool.

| Signal in the problem | Reach for | Why |
|---|---|---|
| "Are there duplicates", "has it been seen" | **`set`** | O(1) membership beats O(n) scanning |
| "How many times does X appear" | **`Counter`** | One line, O(n) |
| "Shortest path", "fewest steps", "minimum moves", "nearest" | **BFS** | When every edge costs the same, it visits in order of distance, so the first arrival is optimal |
| "Level by level", "each row of the tree" | **BFS** with `level_size` | Frontier holds exactly one level per round |
| "All paths", "every combination", "does a cycle exist" | **DFS** | Exhaustive exploration; the call stack tracks the current path |
| A node's answer depends on its children's answers | **DFS, post-order** | Children must resolve before the parent |
| "Sorted array" in the statement | **Binary search** or **two pointers** | Sortedness is a gift — using it is the point |
| "Find a pair / triplet summing to X" | **Sort, then two pointers** | O(n log n + n²) beats O(n³); dedup falls out free |
| "K largest / smallest / most frequent" | **`heapq`** | O(n log k) instead of sorting everything |
| "Contiguous subarray / substring" | **Sliding window** | Extend right, shrink left — O(n) not O(n²) |
| "Longest / shortest run satisfying X" | **Variable sliding window** | Shrink while invalid; each index enters and leaves once |
| ⚠️ …but the property is **not monotone** under extending/shrinking — *"ab"* no, *"aba"* yes, *"abab"* no | **DP, not a window** | a window needs *"valid stays valid when you shrink"*. Without it there is no rule for when to move either pointer |
| "Running max/min so far" | **One pass with a tracker variable** | Almost never needs nested loops |
| "Group these by a shared property" | **`defaultdict(list)`** | The work is choosing the key, not the loop |
| "Sum/product of a range", "all except me" | **Prefix (and suffix) arrays** | Turns "recompute a range" into "subtract two accumulations" |
| Grid, islands, regions, flood fill | **DFS or BFS on the grid** | A grid is just a graph; neighbours are up/down/left/right |
| ⭐ **"For EVERY node, can it reach X?"** · "which regions never touch the border" | **The inversion** — reverse the edges, seed from **X** | Per-node reachability can't share a `visited`, so forward is O(V·(V+E)). Reversed it's one pass. See *Q3g* |
| ⭐ **"For EVERY node, compute X"** where X depends on the whole graph | **Stop asking per-node.** Find the structure that yields all answers at once | n traversals that can't share state cost **O(V·(V+E))** in the worst case: V starts, each a full traversal. Two structures that answer all at once: the inversion (seed from the special thing), and peeling leaves from the boundary ([Minimum Height Trees](https://leetcode.com/problems/minimum-height-trees/), LC 310) |
| A node becomes available only when **ALL** its predecessors are done ("prerequisites", "ingredients", "every neighbour but one") | **A COUNTER, not a boolean** — Kahn's family | **ANY needs a boolean (`visited`); ALL needs a counter (`indeg`).** See *Q3c* |
| Anything that can delete or insert at the **front** of a list | **Dummy head** | The head is the only node with no predecessor. One line deletes the whole special case |
| "k-th from the end", "remove the n-th from the end" | **Two pointers with a fixed gap** | You can't compute `n − k` without the length. Arrange for a pointer to be there instead |
| "Middle of the list", "second half", "does it have a cycle" | **Fast/slow pointers** | One pass, no length, O(1) space |
| "Does this sequence ever repeat?" — even with no list in sight | **Floyd** | A function applied repeatedly to a finite set of states *is* a linked list |
| "Valid", "balanced", "matching" · brackets, tags, nesting | **Stack** | Nesting means the most recently opened thing is always the first that must close |
| "Undo", "cancel the last one", "the most recent" · adjacent items that collapse | **Stack** | The word *recent* is the entire signal. And popping doesn't just remove — it **re-exposes** the previous unresolved item for free |
| **"O(1) space"** in a statement or follow-up | you're being told **not** to use a hash set | See *Replacing a hash set*, below |
| ⭐ **"How many ways"** · **"the best / longest / fewest X"** — a count or an optimum, **not** the candidates themselves | **DP** | the answer doesn't need the path, so the path leaves the state — and a memo becomes legal. Contrast *"return all …"* → backtracking |
| ⭐ A converging two-pointer stalls because **neither side can be proved dead** | **DP**, and **the state becomes the *piece*, not the position** | *"I must try both, and the two overlap"* **is** overlapping subproblems. See *Two pointers or DP?* |

---

## Choosing a traversal: BFS or DFS

> ⭐ **DFS vs BFS is about the *order* you visit things. It is not about *how many* you visit.**
>
> **Both visit everything.** DFS goes down one branch completely, then comes back for the next. BFS takes them in rings. **Neither one skips a branch.**

**So "my traversal only explored one path" is never fixed by switching to BFS** — it means the code isn't a traversal at all. The tell is structural: *can more than one branch fire on the same node?* An `if/else` between neighbours, or a `return` inside the neighbour loop, makes two branches **impossible**, and that's a path walk in either container.

The instinct, when a traversal misses part of the structure, is "use the other traversal". The fix is to stop cutting the branches off.

| Need | Use |
|---|---|
| Shortest path, fewest steps, nearest anything, level-by-level | **BFS** |
| Explore everything, path enumeration, cycle detection, subtree-dependent answers | **DFS** |

**Why:** when every edge costs the same, BFS visits in non-decreasing order of distance from the start: everything at distance d leaves the queue before anything at distance d + 1 enters it, because a node at d + 1 is only pushed while a node at d is being popped. So the first time it touches a target it got there in the fewest possible steps. **BFS finds shortest paths; DFS does not** — DFS may arrive by a long winding route and never know a shorter one existed.

**The cost trade:** BFS memory scales with the *widest* level; DFS with the *height*. On a wide shallow graph DFS is far cheaper; on a deep narrow one BFS is.

**Implementation default:** DFS via recursion (the call stack is free). BFS via `deque` (nothing gives you a queue for free).

## Choosing a DFS order

Pick by **dependency** — when does the node's work need to happen relative to its children's?

| Order | Shape | Use when |
|---|---|---|
| **Pre-order** | node → left → right | The node's work is independent of its children |
| **In-order** | left → node → right | **On a BST this yields sorted order.** Memorise this outright |
| **Post-order** | left → right → node | The node's answer *needs* its children's — height, diameter, balance, subtree sums |

## Where to guard against `None`

`node.left` and `node.right` **always exist** — the TreeNode constructor assigns them, defaulting to `None`. Reading them is always safe. **Chaining off them is not**: `node.left.val` raises AttributeError when `node.left` is `None`.

So the question is never "does the attribute exist," it's "who checks for `None`, and where."

| Context | Guard where | Why |
|---|---|---|
| **Recursive call** | Inside the function — `if not node: return 0` | The callee defends itself, so calls can be unconditional |
| **Push to queue/stack** | At the push site — `if node.left: queue.append(node.left)` | Nothing downstream checks; a `None` in the frontier is a time bomb |

```python
left = size(node.left)           # ✓ unconditional — size() guards itself
if node.left:                    # ✓ must guard — the queue guards nothing
    queue.append(node.left)
```

**Recursion is self-defending; a container is not.** Guarding at the top of the recursive function also handles `root = None` for free, which is why an extra outer check is usually redundant.

*The failure this prevents: appending `None` to a queue, then crashing on `node.val` several iterations later — far from the actual mistake.*

## Comparing two structures: walk them in lockstep

> **Traverse *pairs* of corresponding positions — and treat absence as a value you compare, not a case you skip.**

Two parallel traversals with **separate** frontiers lose positional correspondence. Comparing their *sizes* is not enough: equal counts ≠ equal structure.

```
p:   1          q:   1        ← different trees
    /                 \
   2                   2      ← but both queues hold exactly one node at every level
```

**One queue of pairs** keeps positions bound together:

```python
queue = deque([(p, q)])
while queue:
    a, b = queue.popleft()
    if not a and not b: continue        # both absent here — fine
    if not a or not b:  return False    # structural mismatch
    if a.val != b.val:  return False
    queue.append((a.left,  b.left))     # push pairs, None INCLUDED
    queue.append((a.right, b.right))
```

Pushing `None` is deliberate here — it's how a missing child gets compared against a present one. The usual "never enqueue `None`" rule is suspended *because* the pair-check at the top handles it.

Recursion is usually cleaner for this shape, since the base cases *are* the structural checks:

```python
if not p and not q: return True
if not p or not q:  return False
if p.val != q.val:  return False
return same(p.left, q.left) and same(p.right, q.right)
```

**The tell for recursion:** the problem restates itself on subparts — *"the trees match if the roots match AND the left subtrees match AND the right subtrees match."* Self-similar definition → recursion. If nothing in the problem cares about levels, `level_size` is dead weight.

## The three shapes of recursion

Pick one deliberately. Mixing them silently loses all your work. Many problems combine two.

| Shape | Direction | Mechanism | Example |
|---|---|---|---|
| **Return-up** | child → parent | the return value | subtree size, subtree sum, lowest common ancestor |
| **Accumulate-into-shared** | into an outer container | closure + `nonlocal` | collecting every leaf, counting the nodes that pass a test |
| **Pass-down** (pre-order) | parent → child | an extra parameter | [Count Good Nodes in Binary Tree](https://leetcode.com/problems/count-good-nodes-in-binary-tree/) (LC 1448) |

### 3. Pass-down — when a node needs to know about its ancestors

When "is this node valid?" depends on the path *above* it, the parent hands the child what it needs:

```python
def dfs(node, max_so_far):
    if not node:
        return 0
    count = 1 if node.val >= max_so_far else 0    # decide using inherited context
    new_max = max(max_so_far, node.val)           # what my children inherit
    return count + dfs(node.left, new_max) + dfs(node.right, new_max)

return dfs(root, float('-inf'))                   # sentinel makes the root a normal case
```

> **You rarely need the whole ancestor list — usually one summary value.** "No ancestor greater than me" compresses to a single running max. Same idea as the running-min in LC 121: *what's the minimum I must remember from the past to decide the present?*

**Why DFS:** the call stack **is** the root-to-current path. When a problem is defined over that path, recursion carries the context for free. (BFS can do it by queueing `(node, context)` pairs — you're just rebuilding by hand what recursion gives you.)

**Sentinels make edge cases disappear:** starting with `float('-inf')` means the root passes its own check with no special-casing. Same trick as `-1` for "unbalanced" and `inf` for "not found."

### Carrying state through a recursion — parameter or closure?

**The failure:** a local variable is re-created on every call, so it never carries.

```python
def goodNodes(self, root):
    max_so_far = 0            # ✗ reset to 0 in EVERY call — carries nothing
```

**The discriminator:**

> **Does the state differ per branch, or is it global to the whole traversal?**

| State | Mechanism | Why |
|---|---|---|
| **Per-branch** — running max along the path, current path, depth, visited-on-this-path | **Parameter** | Each call frame gets its own copy; siblings can't contaminate each other, and unwinding discards it automatically |
| **Global** — a count, a best-so-far, an output list | **`nonlocal` / mutable container / return value** | One shared cell is what you want |

**Parameters give you backtracking for free.** The left call's value and the right call's value are independent; when the left branch returns, its state is gone without any manual undo.

**`nonlocal` would be wrong for per-branch state** — one shared cell leaks across siblings:

```
      2          All three are good (answer 3).
     / \         Shared max: visit 2 → max=2; visit 9 → good, max=9;
    9   3        then visit 3 → 3 >= 9 false → missed. Answer 2. ✗
```
The left subtree contaminated the right, and they were never on the same path.

**The helper-wrapper shape.** When the required signature has no room for the state — which is most of the time — the outer method sets up and delegates:

```python
class Solution:
    def goodNodes(self, root):
        def dfs(node, max_so_far):        # state lives here
            ...
        return dfs(root, float('-inf'))   # outer just kicks it off
```

Same rule in backtracking (current path = parameter, results list = shared) and graph DFS.

### Anti-pattern: enumerating cases instead of stating the rule

```python
if left and right:  ...        # ✗ doing the recursion's job by hand
if left:            ...
if right:           ...
```

**Write the rule for ONE node, then let recursion apply it everywhere.** The base case `if not node: return` absorbs every missing-child case at once.

**What it costs when you don't:** an early `return` on the first child skips the entire other subtree, and a hand-written case list tends to test the condition on the root only, or on every node except the root.

---

## The three forms of a recursive call — and when each is right

Applies to **every** recursion, not just trees. Pick the wrong one and a correct answer found deep in the recursion evaporates on the way back up.

| Form | Name | Use when |
|---|---|---|
| `return f(child)` | **Delegate** | The child's answer **is** my answer and there is nothing left to do |
| `x = f(child)` · `if not f(child): ...` | **Capture** | I need the value **and** I have more work — other children, a combination, a check |
| `f(child)` | **Fire-and-forget** | The function returns nothing meaningful; the work lands via **mutation** or a **closure** |

### The discriminator

> **Does this function answer by *returning*, or by *side effect*?**
>
> Side effect → **fire-and-forget**. Returns a value → **delegate** if you're finished, **capture** if you're not.

`return f(child)` is not wrong in principle — it's wrong when there is a *second* child, because returning the first never looks at the second. That's a fact about the problem, not about recursion.

### These two are identical — `and` short-circuits the same way

```python
if not f(node.left,  low, node.val): return False
if not f(node.right, node.val, high): return False
return True
                    # ≡
return f(node.left, low, node.val) and f(node.right, node.val, high)
```

Read both fluently: editorials write the second, and the first is easier to debug.

### Across the topics

```python
# DELEGATE — the answer is the sub-answer
return find(node.next, target)                  # linked list search, tail position
return valid(l, low, v) and valid(r, v, high)   # LC 98 — both children, one expression

# CAPTURE — value needed, work continues
left  = height(node.left)                       # balance check: combine children
if not dfs(nxt): return False                   # early exit on failure
best  = max(best, solve(i - 1))                 # DP / memo

# FIRE-AND-FORGET — side effect is the point
reset(node.left)                                # mutates nodes in place (zeroes every value)
dfs(node.left, depth + 1)                       # writes into a closure `output`
dfs(neighbour)                                  # graph DFS — `visited` is shared
backtrack(path + [x])                           # results list is shared
```

### The eye-check

> **Scan for any line that is *only* a function call** — no `return`, no `if`, no `=`.

If that function returns something meaningful, that line is a bug. Two seconds, and it catches the whole class.

### Why this pairs with the state rule

The two questions together fully specify a recursive call:

| Question | Answers |
|---|---|
| **What travels *down*?** | parameter (per-branch) vs closure (global) — see *Carrying state through a recursion* |
| **What comes back *up*?** | delegate / capture / fire-and-forget — this section |

Get both right and the recursion is correct by construction.

## Detail: return-up vs accumulate-into-shared

Both examples run on this tree:

```
        1
       / \
      2   3
     / \
    4   5
```

**1. Return-up** — each call returns a value, the parent combines them.

```python
def tree_sum(node):
    if not node:
        return 0
    return node.val + tree_sum(node.left) + tree_sum(node.right)
```

On the tree above it returns `15`. Use when a node's answer is a *function of* its children's answers: height, diameter, balance, subtree sums.


**2. Accumulate-into-shared** — an inner helper writes into one structure in the enclosing scope.

```python
def leaves(root):
    output = []                     # created ONCE
    def dfs(node):
        if not node:
            return
        if not node.left and not node.right:
            output.append(node.val)
        dfs(node.left)
        dfs(node.right)
    dfs(root)
    return output                   # the OUTER function returns
```

On the tree above it returns `[4, 5, 3]`. Use when building a list/count across the whole tree. **The nested `def` is the mechanism, not a style choice** — it makes the accumulator exist in exactly one place.

> ⚠️ **The failure mode:** writing `output = []` inside the recursive function itself. Every call then gets its own fresh list, writes one value, and discards it. Nothing accumulates. If you're accumulating, the accumulator lives *outside* the recursion.

## Ordered, not exclusive

When a traversal should *prefer* one side, that means **visit both, in a chosen order** — not `if/else`.

```python
if node.left: dfs(node.left)        # ✗ else-branch abandons an entire subtree
else:         dfs(node.right)

dfs(node.left)                      # ✓ left first, but right still happens
dfs(node.right)
```

A preference is an order, not a filter. If the answer can come from either subtree, an `if/else` between them is a path walk, and a path walk can never find what sits in the branch it skipped.

## Which *item* matters? — the question that names the container

**Upstream of *Choosing a container* below.** That table asks *"what operation do I need?"*, which you can only answer once you've half-designed the solution. This one asks *"which item do I need?"*, which you can answer straight off the problem statement.

> **Of everything I've already seen, which one is the item that matters right now?**

Sorted by how much each structure demands of you, most to least:

| The answer to *"which one?"* | Structure | Get it with | What it demands of you |
|---|---|---|---|
| "The **nearest one by value**" | sorted sequence + binary search | `bisect_left(a, x)` — O(log n) | **A total order, maintained.** Insertion is O(n) — the order has to be *kept*, not just computed |
| "The **largest** (or smallest)" | heap — `heapq` | `heappop(h)` — O(log n) | **A comparison** between any two items, run O(log n) times per operation |
| "An **arbitrary** one, and I know its key" | `dict` / `set` | `d[k]` — O(1) | **A key**, and a hashable one. Hashing destroys order, so it can only ever answer *exact* |
| "The **oldest** one I haven't finished with" | queue — `deque` | `q.popleft()` — O(1) | **Nothing** |
| "The **most recent** one I haven't finished with" | **stack — a plain `list`** | `s.pop()` — **O(1)** | **Nothing** |

> ⭐ **The bottom two demand nothing at all — no key, no comparison, no maintained order.** Recency and antiquity aren't properties of the *items*, they're properties of **when the items arrived** — and arrival order was recorded for free, by the act of arriving. Nothing has to be hashed, compared or re-sorted to find the newest or the oldest, because the structure's own shape already knows.

### "It's LIFO, so use a stack" is not a rule — it's a definition

It runs from the structure back to itself and fires on nothing. Worse:

> **You are never handed a LIFO structure.** You are handed a string, an array, a stream of operations. **LIFO is a property of the order in which the answers become available**, never of the input. *"This is LIFO"* is the conclusion, not the trigger.

**The trigger, which does fire on a problem statement:**

> **The next thing I need is the most recent thing I haven't finished with.**

Three ways that shows up, and they're the three stack families:

| It looks like | Because |
|---|---|
| **Nesting** — brackets, tags, paths, `..` | Regions never *partially* overlap, so the innermost unfinished one is always the one that resolves next |
| **Undo / collapse** — cancel the last, remove adjacent duplicates | Resolving one item re-exposes the one before it, which is the next candidate |
| **"Next greater / next smaller"** | Each new element answers everything smaller that's still waiting — and kills it *(the monotonic stack)* |

**And the negative test, which catches a stack you didn't need:**

- If it **never holds more than one item**, it was a variable.
- If you **push and pop within the same iteration**, it was a variable.

### Spotting a stack when the problem never says "stack"

Every trigger above is a **word** in the statement. Some stack problems contain none of them — no brackets, no "most recent", no "next greater", no nesting. This is what to run when the vocabulary isn't there.

**The question to ask, and it's the only one you need:**

> **As I process the elements in order, does a new element PERMANENTLY eliminate some of the ones I'm still holding?**

| Answer | Reach for |
|---|---|
| Yes, and it eliminates them **by a comparison** | **Monotonic stack** |
| Yes, and it eliminates them **by an exact match** | **Matching stack** |
| No — nothing is ever eliminated | It isn't a stack. You're just scanning |

**The word doing the work is *permanently*.** A stack is only legal when you can *prove* a popped item is never needed again — and that proof **is** the technique. Without it you're not discarding, you're losing answers.

**Three surface forms it wears when the word is absent:**

| It reads like | Underneath |
|---|---|
| "The answer for `i` depends on the **nearest** element in one direction satisfying a comparison" | next/previous greater-or-smaller — a monotonic stack by definition |
| Elements **absorb**, **block**, **hide**, or **merge into** a neighbour | absorbed = eliminated = popped |
| The brute force is *"for each `i`, scan one direction until a condition holds"* | the inner scan keeps re-examining elements an earlier scan already proved irrelevant |

**That last row is the most practical one**, because you'll have written the brute force anyway (brute force, then complexity, then optimise, out loud) — so the trigger arrives for free.

**The derivation, when the statement has no vocabulary at all:**

1. **Find the one direction an element's fate depends on.** If it depends only on what is to one side of it, the problem is a sweep in that direction.
2. **If the input doesn't arrive in that order, sorting it is the missing first line**, not a reason to drop the idea.
3. **Find the elimination:** what makes an element stop mattering, permanently, once a later one arrives.
4. Sweep, and each new element either eliminates the survivors it beats or becomes a survivor itself. **That is a stack.**

The sentence to say out loud in the room: *"Each element's outcome depends only on the nearest survivor on one side, and once it's eliminated it never matters again — so I only ever need the most recent survivor. That's a stack."*

Full treatment in [02-stacks-queues.md](../modules/02-stacks-queues.md#the-monotonic-stack), §The monotonic stack, and [02-stacks-queues.md](../modules/02-stacks-queues.md#a-missing-precondition-is-a-missing-first-line), §A missing precondition is a missing first line.

## Choosing a container

**Downstream of the table above** — once you know *which item* you need, this says which structure gives you the *operations*.

| Need | Use | Not |
|---|---|---|
| Add/remove at both ends | **`deque`** | `list` — `pop(0)` is O(n) → turns O(n) into O(n²) |
| Index into the middle | **`list`** | `deque` — indexing is O(n) |
| Membership / dedup | **`set`** | scanning a list, which is O(n) per check |
| Key → value | **`dict`** / **`defaultdict`** | manual `if k not in d` boilerplate |
| Repeatedly pull the min (or max) | **`heapq`** | re-sorting each time |
| **"largest ≤ x", "nearest", "range"** | **sorted list + binary search** | a `dict` — **hashing destroys order**, so a hash can only answer *exact* membership |

Full API in [python-toolkit.md](python-toolkit.md#the-five), §The five. See also [The silent quadratics](#the-silent-quadratics) — the operations that look O(1) and aren't.

### Ordered *and* changing — the row the table above can't fill

The last row assumes the data is **static**. Sorting is a one-off O(n log n); binary search is O(log n). But an insert into a sorted list is **O(n)** — `bisect` finds the slot in O(log n) and then every later element shifts. That is [a silent quadratic](#the-silent-quadratics) when it sits inside a loop.

| Data changes? | Need order? | Structure | Search | Insert |
|---|---|---|---|---|
| No | Yes | sorted list + `bisect` | O(log n) | — |
| **Yes** | **Yes** | **balanced BST** (`TreeMap`, `SortedList`) | O(log n) | **O(log n)** |
| Yes | No | `dict` / `set` | O(1) avg | O(1) avg |
| Yes | Min only | `heapq` | — | O(log n) |

> **A sorted array keeps order in its layout; a BST keeps it in its pointers.** Layout is cheap to read, expensive to change. Pointers are the reverse. That single trade is the entire reason BSTs exist.

**Python has no built-in balanced BST.** Say so out loud rather than writing `bisect.insort` and calling it logarithmic — that is a wrong complexity claim, and it is the kind an interviewer is listening for. The cost table for `bisect` and `insort` is in [04-binary-search.md](../modules/04-binary-search.md#04-operations-and-their-cost), §0.4 Operations and their cost.

## Stack vs queue behaviour

⚠️ **This pair is easy to invert under pressure, and both halves can flip at once** (*"`pop()` is FIFO, like BFS"* is backwards twice). Drill this table until it's automatic.

| Call | Removes | Order | Container | Traversal |
|---|---|---|---|---|
| `list.pop()` | the **newest** | **LIFO** | stack | **DFS** |
| `deque.popleft()` | the **oldest** | **FIFO** | queue | **BFS** |

**The mnemonic:** **LIFO = Last In, First Out** — a pile of plates, you take the one you just put down. **FIFO = First In, First Out** — a queue in a shop, first to arrive is first served.

**Then the line that connects it to traversal:**

> **A node's children are always the *newest* things in the frontier, and always the *deepest*.**

So *"serve the newest"* = *"go deeper"* = **DFS**. *"Serve the oldest"* = *"everything at my own level is served before any of their children"* = **BFS**. That is also why **recursion is automatically DFS** (the call stack is a to-do list where new items go on top) and why **BFS needs an explicit queue** — nothing gives you a queue for free.

| | Sibling order | Consequence |
|---|---|---|
| **Queue** (FIFO) | **Preserves** | Push left then right → visits left first. Natural. |
| **Stack** (LIFO) | **Reverses** | Push left then right → visits **right** first. Push backwards to get the order you want. |

Only bites when hand-rolling a stack. Recursion has no inversion.

### Guard and mark belong on adjacent lines

Put the guard `(nr, nc) not in visited` at the push and the mark `visited.add((r, c))` at the pop, and the traversal is still correct, but a cell can be pushed by several neighbours before its first copy is popped, so it is pushed, popped and expanded more than once.

```python
if <valid> and (nr, nc) not in visited:
    visited.add((nr, nc))        # ← mark IMMEDIATELY after the guard
    stack.append((nr, nc))
```

> **If the guard and the mark are far apart, ask what can happen in between.** Here it costs repeated work. On a **BFS that writes distances at the push**, the same separation is a *wrong answer*: a node first pushed at distance d + 1 can be pushed again by a node at distance d + 1 before its first copy is popped, and the second write overwrites d + 1 with d + 2.

## Array problems: ask the sorted question

**"What if this were sorted?"** — one of the highest-yield questions when stuck on an array problem. A large share collapse once sorted, and O(n log n) to sort is usually free relative to the O(n²) or O(n³) you're trying to escape. It's the entire unlock for 3Sum.

**Corollary:** sorting is a *solution tool*, not a utility. And built-ins — `sorted`, `set`, `dict`, `deque`, `Counter`, `heapq` — are **always allowed** unless the interviewer explicitly says otherwise.

## Graphs: mark on push, not on pop

In a graph (not a tree), several nodes can discover the same neighbour. Mark a node as seen when you **push** it, or it enters the frontier multiple times and gets processed more than once. Trees are immune — every node has exactly one parent.

*The most common bug in grid flood fills.* The full argument is in [08-graphs.md](../modules/08-graphs.md#mark-on-push-or-mark-on-pop), §Mark on push, or mark on pop?

---

# Arrays, lists and hashes

## The cascade — run this when an array or string problem stalls

Stop at the first match. Two steps, and step 1 is nearly free.

**Step 1 — scan the statement for a trigger word.**

| Word in the problem | Tool |
|---|---|
| "duplicate", "unique", "distinct", "already seen" | `set` |
| "how many times", "frequency", "most common" | `Counter` |
| "group", "bucket", "categorise", "anagram" | `defaultdict(list)` + **key design** |
| **"contiguous"**, **"subarray"**, **"substring"**, "window" | **sliding window** |
| "sorted" — anywhere, describing the input | binary search or converging pointers |
| "pair", "triplet", "two numbers that…" | sorted → two pointers · unsorted + need indices → `dict` |
| "range sum", "except itself", "all others" | prefix / suffix arrays |
| "k largest", "k most frequent", "top k" | `heapq` |
| "maximum/minimum/best so far", "profit" | one pass, one tracker |

**Step 2 — no trigger word? Write the brute force, say "that's quadratic", then walk the four escapes out loud.**

1. **Remember** — *is there something I could store that makes the inner loop unnecessary?* → hash
2. **Order** — *would sorting help?* → two pointers / binary search
3. **Reuse** — *does the answer at `i` overlap with the answer at `i−1`?* → running state / window / prefix
4. **Discard** — *of the things I've already seen, can I **prove** some will never be needed again?* → **monotonic stack**

> Saying these four out loud **is** the optimisation pass: brute force, then complexity, then optimise, out loud. It is scored whether or not it succeeds.

**Escape 4 is the one that fires when the other three don't.** Remember, Order and Reuse all ask *what should I keep?* Discard asks the opposite — and it's the right question whenever the brute force is *"for each `i`, scan one direction until a condition holds"*, because that inner scan is re-walking elements an earlier scan already proved irrelevant. See [Spotting a stack when the problem never says "stack"](#spotting-a-stack-when-the-problem-never-says-stack).

## Remember vs Reuse — the discriminator

Both escapes "keep something from the past," which is why they're easy to confuse. **The label determines your space complexity**, so getting it wrong means misreporting the quality of your own solution.

| Escape | What you store | Space | Examples |
|---|---|---|---|
| **Remember** | a *collection* of past values, queryable by key — `set`, `dict`, `Counter` | **O(n)** | Contains Duplicate, Two Sum, Group Anagrams |
| **Reuse** | a *fixed number of summary values* carried forward | **O(1)** | running min/max, Kadane, Best Time to Buy/Sell |

> **The test: does your storage grow with n?**
> Hash structure → grows → **Remember**, O(n) space.
> A handful of scalars → fixed → **Reuse**, O(1) space.

**And O(1) means "does not grow with n" — not "is small".** Two variables is O(1). Fifty variables is O(1). One list of length n is O(n).

**Which to try first:** Reuse, always. It's strictly cheaper when it works. The question that finds it —

> *"What is the minimum I must remember from the past in order to decide the present?"*

— and if the honest answer is "a single number or two," it's Reuse. If it's "any of the values I've seen, and I don't know which one I'll need," you need a hash: that's Remember.

**Why the label matters:** calling a running-minimum solution "Remember" means reporting O(n) space on an O(1) solution, which throws away the exact property that makes it good.

## Hashing only pays if you build and query in the *same* pass

> **Materialising every pair is not "Remember" — it's the brute force with extra memory.**

There are n² pairs. Precomputing them into a dict costs **O(n²) time and O(n²) space before you've answered anything**. Then each query has to walk the pairs filed under its sum, and when many sums coincide that list holds up to O(n²) pairs, so n queries cost O(n³) in the worst case. You've made it worse, not better.

The escape works when the store is built **incrementally, as you walk**, and queried on the same pass:

```python
seen = set()
for x in nums:
    if partner(x) in seen:    # query what's already there
        ...
    seen.add(x)               # then add yourself
```

Here `partner(x)` stands for whatever earlier value would complete `x`. Query before you add, or `x` can pair with itself.

**One pass. O(n) entries, never O(n²).**

**For triplets, the shape is: fix an anchor with an outer loop, then run a linear pair search on the remainder.** O(n) inside O(n) = O(n²) — and the same "outer anchor + linear inner scan" skeleton works whether the inner scan is a hash or a pair of converging pointers.

| Approach to a triplet sum | Time | Space |
|---|---|---|
| Precompute all pairs | O(n³) worst case ✗ | O(n²) ✗ |
| Anchor + hash pair search | O(n²) | O(n) |
| Sort + anchor + two pointers | O(n²) | **O(1)** beyond the sort ✓ |

## Choosing the hash structure

| I need | Use | Note |
|---|---|---|
| *Whether* I've seen it | `set()` | membership only |
| *Where* I saw it | `dict` — value → index | the "record the past" pattern |
| *How many* times | `Counter(iterable)` | missing keys read as `0`, never `KeyError` |
| To collect items under a key | `defaultdict(list)` | `d[k].append(x)`, no boilerplate |
| To accumulate a number per key | `defaultdict(int)` | `d[k] += 1` |
| Membership *and* order of insertion | `dict` (keys are ordered in Python 3.7+) | a `set` is **not** ordered |

## Key design — the actual skill in hashing

> **The key is whatever is identical across everything you want grouped together.**

| Group by | Key |
|---|---|
| Same pattern of repeats (`"egg"`, `"add"`) | the letters numbered by first appearance, as a `tuple`: see [01-arrays-hashing.md](../modules/01-arrays-hashing.md#key-design-the-hard-part-of-hashing), §Key design: the hard part of hashing |
| Same set of letters, repeats ignored | `frozenset(word)` |
| Same value, ignoring position | the value itself |
| Points on the same line | the slope as a *reduced fraction* `tuple`, not a float |
| Cells in the same 3×3 box | `(row // 3, col // 3)` |

**Constraint:** keys must be hashable, which means immutable. `int`, `str`, `tuple`, `frozenset` ✓ · `list`, `dict`, `set` ✗. This is *the* reason grouping code is full of `tuple(...)` and `''.join(...)` — a mutable key could change after insertion and become unfindable, so Python forbids it outright.

## The silent quadratics

**The highest-value table in this section.** Every line looks innocent, costs O(n), and turns an O(n) algorithm into O(n²). None of them raise an error — the code passes on the example and times out on the real input.

| Looks innocent | What it costs | Instead |
|---|---|---|
| `x in my_list` | **O(n)** — scans | `x in my_set` — O(1) |
| `lst.pop(0)` | **O(n)** — shifts everything | `deque.popleft()` |
| `lst.insert(0, x)` | **O(n)** | `deque.appendleft(x)` |
| `lst.remove(x)` · `del lst[i]` · `lst.pop(i)` | **O(n)** — find, then shift everything after it | **a write pointer** — overwrite in place, see [The write pointer](#the-write-pointer--you-cannot-delete-in-o1-but-you-can-overwrite) |
| `nums[i:j]` inside a loop | **O(j−i)** — slicing *copies* | pass indices, not slices |
| `s += ch` inside a loop | **O(n)** — strings are immutable, each `+=` rebuilds | `parts.append(ch)` then `''.join(parts)` |
| `max(lst)` / `sum(lst)` inside a loop | **O(n)** each time | carry a running max/sum |
| `sorted(...)` inside a loop | **O(n log n)** each time | sort once, before the loop |

> **The tell: any built-in that has to *look at every element* is O(n), even when it's one short line.** A one-line call is not a one-step operation. When you say your complexity out loud, check every line inside the loop against this table first.

*Row 2 (`pop(0)` in a BFS) is the one most often written. The others are the same mistake wearing different clothes.*

## Aliasing and copying — lists bite harder than trees

On trees, `=` binds a name and never copies. On lists the consequences are worse, because lists are mutated constantly.

```python
b = a                  # ✗ ONE list, two names. b.append(1) changes a.
b = a[:]               # ✓ a real (shallow) copy
b = list(a)            # ✓ same thing

grid = [[0] * n] * m   # ✗ m references to ONE row. grid[0][0] = 1 sets it in EVERY row.
grid = [[0] * n for _ in range(m)]   # ✓ m independent rows
```

The `[[0] * n] * m` trap is a classic, and grid and DP code is where it appears. `*` on a list repeats **references**, not contents.

> ⭐ **Storing a list is the same act as binding one — neither copies.**
>
> ```python
> res.append(path)      # ✗ files away a LABEL. A later path.pop() edits what you "stored"
> res.append(path[:])   # ✓ files away a NEW BOX with today's contents
> ```
>
> **A list variable is a label stuck on a box, not the box itself.** `b = a` is the simplest form of this; `res.append(path)` is the same fact one verb along, and it's the signature bug of backtracking — the output has the **right number of entries and all of them are empty**, which reads as a printing problem and isn't. **The test: after this line, if I change the list, does what I just stored change too?** See [07-backtracking.md](../modules/07-backtracking.md#the-copy), §The copy.

**Also: never mutate a list while iterating over it.** Removing an element shifts everything left while the loop's index keeps advancing, so you silently skip elements. Build a new list, or iterate over a copy.

## Editing a linked structure — there is no "delete", only "repoint"

A node is in the structure **if and only if a pointer chain reaches it from the root.** Nothing "holds" a set of nodes; the pointers *are* the structure. So:

> **Deleting node X is not an operation on X. It is a change to whoever points at X.**

Break the last incoming pointer and the node is gone — Python reclaims it. This is why the instinct below is the single most common way to write a delete that does nothing:

```python
node = None            # ✗ repoints YOUR LOCAL NAME. The parent has never heard of it.
node = node.right      # ✗ same. You moved a sticky note, not a branch.
```

`node` is your name for the object. `parent.left` is the structure's name for it. Only the second one is load-bearing.

### The two mechanisms, and only two

| | How | Looks like | Cost |
|---|---|---|---|
| **Direct** | reach into the parent and overwrite its field | `parent.left = x` | you must **carry `parent` and which side you came from**, and handle "the target is the root" as a special case |
| **Return-up** ⭐ | hand the replacement back; the parent's own line assigns it | `node.left = delete(node.left, key)` | none — the recursion already knows who the parent is |

**Prefer return-up.** The parent frame is already sitting on `node`, so `node.left = f(node.left)` *is* the parent reaching down — you get the direct version for free, without a `parent` parameter, without a `direction` parameter, and without the root being special (`return f(root)` handles it).

> **That assignment line is the deletion.** Everything else is bookkeeping.

### The contract sentence — say it before writing

> **`f(node, ...)` means: here is a subtree; give me back what this subtree should be afterwards.**

Once that sentence is said, every case is a one-word answer to *"what should sit here now?"* — and the code falls out:

| Case | What should sit here now | Code |
|---|---|---|
| empty | nothing | `return None` |
| recurse left | still me, with a new left subtree | `node.left = f(node.left); return node` |
| target, no children | nothing | `return None` |
| target, one child | that child | `return node.left or node.right` |

### The one-second check — run it on any mutation code

> **Count the lines that assign to a `.left`, a `.right`, or a `.next`. If the answer is zero, the structure cannot have changed.**

Assigning to the *parameter* is never an edit. Assigning to a **field of an object someone else can reach** is the only edit there is — or returning the replacement so a caller does it.

### Where this shows up

| Problem | The repoint |
|---|---|
| [450 Delete Node in a BST](https://leetcode.com/problems/delete-node-in-a-bst/) | `node.left = delete(node.left, key)` |
| [203 Remove Linked List Elements](https://leetcode.com/problems/remove-linked-list-elements/) | `prev.next = curr.next` — or the return-up form |
| [19 Remove Nth Node From End of List](https://leetcode.com/problems/remove-nth-node-from-end-of-list/) | why a **dummy head** exists: it manufactures a parent for the real head |
| [814 Binary Tree Pruning](https://leetcode.com/problems/binary-tree-pruning/) | `node.left = prune(node.left)`, then `return node if ... else None` |

**The dummy head is this rule's corollary.** In a linked list the head has no parent, so direct-repoint has no field to write — you invent one. In a tree, return-up already solves it, which is why trees rarely need a sentinel node.

## State the invariant before writing the loop

Cross-topic — this also carries binary search.

> **An invariant is a statement true at the top of every iteration.** Choose it *first*; then every line in the body has one job: leave it true.

| Technique | Invariant |
|---|---|
| Converging pointers | "if an answer exists, it's inside `[lo, hi]`" |
| Sliding window | "`nums[left..right]` currently satisfies the rule" |
| Running min/max | "`best` is the answer for `nums[0..i]`" |
| Binary search | "the target, if present, is inside `[lo, hi]`" |
| Frequency map | "`count` holds exact counts for everything before `i`" |

**Two payoffs:**

1. **Tracing gets fast.** You don't verify the algorithm — you check that one iteration preserves the invariant, and induction covers the rest. Thirty seconds instead of five minutes.
2. **It's what you say out loud.** *"I keep everything between left and right valid, so when extending right breaks it, I shrink from the left until it's valid again."* That sentence proves the code isn't an accident.

### The falsifiability test — is that an invariant at all?

Three state sentences that sound like invariants, for [Minimum Window Substring](https://leetcode.com/problems/minimum-window-substring/) (LC 76), and **all three are circular**: *"the solution is within those bounds"*, *"the solution is within it"*, *"look at the bounds of the current minimum"*. They describe the **answer**, not the variables.

> **The test: hand the sentence to a stranger mid-run. Show them only the input and the current values. Can they verify it in ten seconds?**
>
> **If checking it requires already knowing the answer, it is not an invariant.**

And the circular one is usually also **false**. On `s = "ADOBECODEBANC"`, `t = "ABC"` the answer sits at indices 9–12, so while the window is at 0–5 the answer is nowhere inside it. **Most windows do not contain the answer** — which is precisely why the sentence has to be about something checkable instead.

| ✗ Circular — unverifiable | ✅ Checkable in seconds |
|---|---|
| "the solution is in `[lo, hi]`" | "`s[lo:hi]` is the single substring currently under consideration" |
| "the window is correct" | "`missing > 0` holds at the top of every grow step" (for a non-empty `t`) |
| "record at the minimum" | "`missing` = how many required characters the window is still short of" |

**Converging pointers are the one honest exception** — *"if an answer exists it's inside `[lo, hi]`"* is legitimate there, because it's maintained by an explicit discard: each step **proves** one side can't hold the answer and drops it. No such argument, no such invariant.

**Off-by-one errors are invariant violations.** `while lo < hi` vs `while lo <= hi` is *determined* by whether your range is closed `[lo, hi]` or half-open `[lo, hi)`. Decide the invariant and the operator follows, instead of being guessed and then patched.

## Is it a sliding window? Four checks

| # | Check | Its opposite |
|---|---|---|
| 1 | **The word** — "contiguous subarray", "substring", "consecutive" | **"subsequence" / "not necessarily contiguous" → NOT a window.** Usually DP |
| 2 | **The ask** — "longest / shortest / max / min ⟨run⟩ such that ⟨constraint⟩" | a question about individual elements, not runs |
| 3 | **Fixed or variable** — a size `k` is given → fixed, both ends move together; the size is what you're optimising → variable | |
| 4 | **Monotone?** extending `right` may only *break* validity; advancing `left` may only *restore* it | if not, `left` would have to rewind — not a window |

**The brute force a window replaces** is "check every substring": nested loops over start and end, **O(n²)**. If that's your brute force's shape, a window is the candidate.

> ⚠️ **Check 4 is not optional.** *"Shortest subarray with sum ≥ target"* (LC 209) is a window **only because the values are positive**. Allow negatives and adding an element can *lower* the sum — monotonicity dies, and the answer needs prefix sums plus a monotonic deque. Never stop at the word "subarray."

## Neither window pointer is ever a choice

The misconception: *"if the window is too long, do I drop from the left or the right?"*

**Neither pointer is a decision.**

- **`right` advances every iteration, unconditionally** — it's the `for` loop variable.
- **`left` advances only when the window is invalid**, and only forward.

**Where the false dilemma comes from:** imagining the window starts at size n and shrinks — that's enumerating window *sizes*, where both ends are free. A window enumerates **right endpoints** instead:

> For each `right`, the question is *"what's the longest valid window ENDING HERE?"* — **`right` is pinned by the question.** The only free end is `left`.

Shrinking from the right isn't wrong, it's **redundant**: every window ending at `right - 1` was already examined when the loop was there.

**A count to have ready:** substrings are **n(n+1)/2 ≈ n²/2**, not 2ⁿ — a substring is fixed by two endpoints. Subsets are 2ⁿ. *"Too many possibilities" is usually a counting error, not a fact about the problem.*

## Window direction: shrink while valid, or while invalid?

The classic sliding-window bug, and the invariant tells you which:

| Goal | Shrink | Record the answer |
|---|---|---|
| **Maximise** the window | while **invalid** | after shrinking, when it's valid again |
| **Minimise** the window | while **valid** | inside the shrink loop, before removing |

Getting this backwards produces code that runs, returns a number, and is wrong.

**Why the record moves with the direction.** Maximising, the valid window is what you hold *after* the shrink. Minimising, it's what you hold *before* the removal that breaks it — so the record is the **first line of the shrink body**. Placed after the loop it is dead code by construction: the loop only exits once the window is invalid.

### Two counters, and the consume/release mirror

A minimising window must be able to **break**, so the bookkeeping runs in both directions. That needs two separate quantities:

| Counter | Meaning | Job |
|---|---|---|
| `need[c]` | copies of `c` still wanted. **Allowed to go negative — negative = surplus** | remembers that a duplicate was consumed |
| `missing` | number of unmet requirements | **the whole validity test, in O(1)** |

```python
# consume s[right]                  # release s[left]
if c in need:                       if c in need:
    if need[c] > 0: missing -= 1        need[c] += 1
    need[c] -= 1                        if need[c] > 0: missing += 1
right += 1                          left += 1
```

1. **Decrement unconditionally.** Guard it with `if need[c] > 0` and surplus copies leave no trace, so the release can't distinguish *"I had a spare"* from *"that was the last one."*
2. **Test *before* the change on consume, *after* it on release.** Both ask **"did this cross zero?"** — you check the side you're leaving. The threshold is `> 0`, never `>= 0`: landing on **zero** means *exactly enough*, still valid.
3. **The pointer advance goes outside the `if`.** The guard decides whether there's a count to touch, never whether to move. `left += 1` inside it spins forever on any character absent from the target.

**Don't collapse the two counters.** Reading validity off the dict directly costs a scan per step — an extra O(m) factor, which is exactly what breaks the required O(n + m).

## Two pointers: which shape?

| Signal | Shape | Requires |
|---|---|---|
| Sorted (or sortable) · pair/triplet sum · palindrome · merge | **Converging** — `lo=0`, `hi=n-1`, move toward each other | sortedness or symmetry |
| "Contiguous" · "substring" · "longest run such that…" | **Window** — `left`, `right` both from 0 | contiguity + a monotone rule |
| "In place" · "return the new length" · "O(1) extra space" · remove/filter/partition | **Write pointer** — `r` reads, `l` writes, `l ≤ r` | nothing; works on any array |

**Why the window is O(n) despite a nested `while`** — have this sentence ready, interviewers probe it deliberately:

> *"It's linear, not quadratic — `left` only ever increases and can never pass `right`, so its total movement across the entire run is bounded by n."*

### The write pointer — you cannot delete in O(1), but you can overwrite

**The trap:** *"remove them in place"* invites `nums.pop(i)`. Each `pop` shifts every later element down a slot — O(n) — so n removals is **O(n²)**. No error, correct output, TLE.

> ⭐ **Don't delete. Overwrite.** Build the answer in place, left to right, on top of input you have already read.

| Pointer | Job | Moves |
|---|---|---|
| `r` — read | touches every element exactly once | every iteration, unconditionally |
| `l` — write | next slot to fill, **and** the count of keepers | only when an element is kept |

`l ≤ r` always, so the write head never reaches unread input. **That one inequality is the whole correctness proof.** Only the keep-test changes between problems — [LC 27](https://leetcode.com/problems/remove-element/) tests `!= val`, [LC 283](https://leetcode.com/problems/move-zeroes/) tests `!= 0`, [LC 26](https://leetcode.com/problems/remove-duplicates-from-sorted-array/) tests against `nums[l-1]`.

**Two free consequences:** `l` *is* the returned length, so nothing separate is counted; and everything past `l` is garbage the judge never reads, so don't spend a pass cleaning it.

⚠️ **Never change the length of a list you are indexing into.** Every index you hold goes stale the moment an element is removed, and `len()` has to be re-read every iteration. **A shrinking container under a moving index is a bug factory.**

### The aggregate count — the general form of that sentence

The question that stalls people is *"how many inner iterations per outer iteration?"* It has **no answer** — some passes shrink nothing, one might shrink half the array. Ask the other question:

> **Over the whole run of the program, how many times does this line execute?**

Four independent counts, added, never multiplied:

| Line | Bounded by | Total |
|---|---|---|
| grow body | ends in `right += 1`; `right` rises only, capped at n | ≤ n |
| shrink body | ends in `left += 1`; `left` rises only, can't pass `right` | ≤ n |
| outer pass | each raises `right` by ≥ 1 | ≤ n + 1 |
| each body | dict lookup, compare, add | O(1) |

> ⭐ **Nested loops multiply only when the inner counter RESTARTS. If it carries forward and moves one way, you add.** `left += 1` **is** the linear update — there is no smarter one to find.

**Second payoff: the same argument proves termination.** A `while True` is safe exactly when you can name a quantity that strictly moves toward the exit and never moves back. **Termination and the time bound are one fact.** Write the loop, then name that quantity out loud; if you can't, the loop is wrong.

⚠️ **And check the setup line.** `{c: t.count(c) for c in set(t)}` is **O(m × distinct(t))** — a full scan of `t` per distinct character. `Counter(t)` is one pass. A linear main loop preceded by a quadratic preprocessing line is not a linear solution.

---

# Binary search

Full treatment in [04-binary-search.md](../modules/04-binary-search.md#module-04-binary-search).

## When to reach for it

| Signal | Note |
|---|---|
| **"sorted array"** anywhere | binary search or converging pointers |
| **"O(log n)"** required, in the statement or the follow-up | binary search. Essentially nothing else produces a log |
| "find the **first** / **last** X such that…" | boundary search |
| "**rotated** sorted array" | two sorted runs; one half is always sorted |
| **"minimum/maximum value such that [something] is possible"** | **answer space** — the strongest signal in the topic |
| "minimise the maximum", "maximise the minimum", "given a budget" | answer space, near-certain |
| Input range is huge (10⁹) but the array is small | you're searching the **value range**, not the array |

> **The tell for answer space:** the thing you must return is a number in a known range, and given a candidate you can **check** it far more easily than you can **find** it. Checking is the predicate. Then you search.

## The definition that makes every variant one algorithm

> **You need a search space and a yes/no question `P` that is `F…F T…T` across it.** Sortedness is not the requirement — it's the most common way to *get* monotonicity.

**Before writing anything, one sentence:** *"I'm searching X, and the question that goes false-then-true is Y."*

**A monotone predicate has exactly one boundary**, always locatable as **the first T**. Whether the problem wants the first T or the last F (`lo - 1`) is a **reading question, not an algorithm question** — decide before the loop. If `P` comes out `T…T F…F`, **negate it**.

## The four setup decisions — where the bugs live

| Decision | Rule |
|---|---|
| **`lo`, `hi`** | **the range of the *answer*, not the ends of the array.** Name the most extreme legal answer; can `hi` hold it? |
| **Loop condition** | read off the convention. Closed `[lo,hi]` → `while lo <= hi`. Half-open `[lo,hi)` → `while lo < hi`. **Never guessed** |
| **Which branch keeps `mid`** | **a False is proof of exclusion → `lo = mid + 1`. A True is only a candidate → `hi = mid`** |
| **The return** | first-true search → `lo`. Exact match → `mid` from *inside* the loop. **Never `mid` after the loop** |

⚠️ **Bounds that can't express the answer are a wrong answer, not a crash** — the invariant is false before iteration one, and it fails silently.

⚠️ **Monotone is necessary, not sufficient — a True must *exist*.** Three-second check: **does my reference satisfy its own predicate?** Plug the value you converge toward (`hi`, in a first-true search) into the predicate. If it can come out False on a legal input, nothing guarantees a boundary exists.

⚠️ **`lo = mid` with `mid = (lo+hi)//2` is an infinite loop.** The branch that keeps `mid` must move toward where `mid` can't land.

## The one template to keep

```python
lo, hi = 0, len(nums)              # or the ANSWER's range
while lo < hi:
    mid = (lo + hi) // 2
    if P(mid): hi = mid            # candidate — keep it
    else:      lo = mid + 1        # proved out — discard it
return lo                          # "last true" → return lo - 1
```

Covers `lower_bound`, first-bad-version, min-of-rotated, and answer space. Exact match is this plus one equality check.

## Answer space

> **`lo`, `hi`, `mid` are candidate *answers* — values. There may be no array at all.**

**Never materialise the space.** `lo`/`hi` describe it; nothing is built. A list of candidates is a linear scan waiting to happen, and on a range of 10⁹ values the list's pointer array alone is 8 GB (8 bytes a slot) before the first check runs.

**`lo = 0` is an array-index reflex.** In a value space the smallest legal answer is whatever the problem says — often 1, sometimes `max(nums)`.

**Complexity: `O(log(range) × cost of one check)`.** ⚠️ **Say what the log is over** — the value range, not `n`.

## Searching part of an array

**Pass bounds, never slice.** `def search(lo, hi, target)` searching `nums` in place. Slicing costs an O(n) copy, forces offset arithmetic (then `-1 + offset`), and turns an empty region into an IndexError. All three vanish. **Parameter order is `(lo, hi)`, always.**

## Rotated arrays

**Two sorted runs; every element of the left run exceeds every element of the right.** Cut anywhere and **at least one half is sorted** — `nums[lo] <= nums[mid]` tells you which. For a sorted half you can test whether the target is in its value range, **using both endpoints**; the one-sided test is the standard wrong answer.

⚠️ **The non-rotated array is in the test set.** "Rotated n times" is the original.

---

# Linked lists

Full treatment in [05-linked-lists.md](../modules/05-linked-lists.md#module-05-linked-lists).

## The trade, and what it kills

> **An array gives O(1) random access and no pointers. A list gives pointers and no random access.**

| Dies on a list | Survives |
|---|---|
| **Converging** two pointers — you can't walk backwards | **Same-direction** two pointers — the gap, and different speeds |
| Binary search — each probe costs O(n) to reach | Hashing — **nodes are hashable by identity** |
| `nums[i-1]` — no way to look back | Running state in one pass — a carry, a tail, a count |
| Prefix sums, index arithmetic | Merging two sorted sequences — and it gets **cheaper** |

**A linked list is a degenerate tree** (one child per node). Three consequences: recursion over it is **O(n) space** and dies at ~1000 frames · a list with a cycle is a graph · `while cur: cur = cur.next` *is* a DFS. What doesn't transfer is the tree machinery about *choices* — with one child there is never a choice.

## The four moves

| Move | When | The line that matters |
|---|---|---|
| **Dummy head** | the front can change | `dummy = ListNode(0, head)` … `return dummy.next` |
| **Three-pointer reversal** | reverse, in whole or in part | **save, rewire, advance, advance** |
| **Fixed gap** | k-th from the end | open the gap, **then slide both** |
| **Fast/slow** | the middle, cycles | `while fast and fast.next` |

## The five rules

1. ⭐ **Save before you destroy.** Overwriting a `.next` makes everything after it unreachable. Three facts at the moment you flip an arrow — came from, am at, was going to — so three names. **Two pointers is a shortage, not a style choice.**
2. ⭐ **Flip the link behind you** (`cur.next = prev`), never ahead. The forward version loses the save *and* never terminates the head.
3. ⭐ **`prev = None` is not an empty initialiser** — it's the future tail's `.next`. `prev = head` makes the invariant false before iteration 1.
4. ⭐ **Names go stale.** `return prev` or `return dummy.next`, **never `head`**. And *name the dummy `dummy`*, or no name will mean "the front".
5. ⭐ **Guards left to right, in dereference order.** `while fast and fast.next`. `.next.next` needs two guards. And the **equality test goes after the moves** — they start equal.

## Which loop condition

| Write | When | Dies on |
|---|---|---|
| `while cur` | inspecting nodes | — |
| `while cur.next` | **editing the link ahead**, or you need the tail | `head is None` |
| `while fast and fast.next` | fast/slow | — |
| `while a and b` | comparing two lists — you can only compare while both exist | — |
| `while a or b` | consuming two lists of **different lengths** — and anything still pending once both run out needs its own term in the condition | — |

> **A missing element isn't a special case, it's a zero.** `while a and b` silently drops the longer list's tail.

## Replacing a hash set — the five escapes

> ***"Can you do it in O(1) space?"* means something other than memory has to do the remembering.**

| The O(n) memory | What replaces it | Cost |
|---|---|---|
| set of seen **nodes/states** | **two pointers at different speeds** | nothing |
| set of seen **values** | **sort first** — duplicates become adjacent | O(n log n) |
| set / count array | **mutate the input as the mark** | destroys the input |
| set of what's needed | **arithmetic** — sum formula, XOR | needs constrained values |
| set of seen characters | **a bitmask in one int** | needs a small alphabet |

**On a linked list it collapses to pointers**, because the other four all need indices, a small domain, or a destructible input. Elsewhere it doesn't — don't carry the reflex into an array problem where sorting was the answer.

This is **Remember vs Reuse one level up**, and the question that finds the conversion is: ***"what does the structure already know, that makes remembering unnecessary?"***

⚠️ **Giving the hash version first is not a failure.** It's the expected first answer. Brute force, then complexity, then optimise, out loud: stating the hash version with its cost before optimising is part of the answer, not a detour.

## Complexity — the template

> **"O(\_\_) time, because \_\_ runs \_\_ times and each one costs \_\_."**
>
> **"O(\_\_) space, because the only thing I allocate is \_\_, and that doesn't grow with n."**

The space slot asks **what you allocate**, not how many names you wrote. *"O(1) because only two pointers"* is the wrong test — **O(1) means "does not grow with n", not "few".**

| Situation | Say |
|---|---|
| Reversal, Floyd, the gap | *"O(1) space — three pointers, and three is three whether the list has 2 nodes or 5,000."* |
| Merging two lists | *"O(1) even in total — built from the **existing** nodes, spliced, not copied."* |
| Building a new list | *"O(n) total — a node per element — but **O(1) auxiliary**, since that's the required output."* |

⚠️ **When the problem already uses `n` for a parameter, say "O(L) where L is the number of nodes."**

---

# Stacks and monotonic stacks

Full treatment in [02-stacks-queues.md](../modules/02-stacks-queues.md#module-02-stacks-and-queues).

## The container

**A plain `list`.** `append` / `pop` / `stack[-1]` / `if stack`. Both operations are at the **right** end, which is the cheap end — the reason you learned `deque` (`pop(0)` is O(n)) doesn't exist here. **Reaching for `deque` is a tool carried from the last problem.**

⚠️ `stack.pop()` vs `stack.pop(0)` — one character, two data structures, and the second is a silent quadratic.

## The sentence, before the loop body

> **What is on the stack, and why is the top the one I need next?**
> Monotonic → **and why is it sorted?**

## The empty stack means something different in every problem

| Problem | Empty stack when you need the top | Do |
|---|---|---|
| Bracket matching | a closer with nothing open | **fail immediately** |
| Simplify Path | `..` at the root | **nothing — continue** |
| Monotonic | nothing waiting | **push and move on** |

**Never copy the guard from the last problem** — ask what empty *means here*. And the mirror question: **what do leftovers at the end mean?** They were never resolved and never will be. **The stack at the end is part of the answer** — pre-fill the output with the "no answer" value and the leftover branch disappears.

⚠️ `if stack[-1]` is `False` when the top is `0`. Test the **stack**, not the top.

## Monotonic stack — the four variants

| Want | Pop while | Stack, bottom → top |
|---|---|---|
| Next **greater** to the right | `nums[stack[-1]] < x` | **non-increasing** |
| Next **smaller** to the right | `nums[stack[-1]] > x` | **non-decreasing** |

**One left-to-right pass answers both directions:** at **pop** time you learn the popped element's *next greater to the right*; at **push** time whatever is left on top is the current element's *previous greater-or-equal to the left*, because the pop condition `<` is strict and an equal element stays on the stack. Pop with `<=` instead and the push-time answer becomes strictly greater; the tie rule is in [02-stacks-queues.md](../modules/02-stacks-queues.md#the-monotonic-stack), §The monotonic stack.

```python
answer = [-1] * len(nums)         # the "no answer" default, decided up front
stack  = []                       # INDICES
for i, x in enumerate(nums):
    while stack and nums[stack[-1]] < x:
        j = stack.pop()
        answer[j] = x             # x is the next greater element of nums[j]
    stack.append(i)
```

⚠️ **Push indices, not values** — `nums[i]` converts index→value, nothing converts value→index. Values are legal only when they're **distinct** *and* no position is ever needed. Both, or it's indices.

⚠️ **`<` vs `<=` decides ties.** With `<`, an equal element doesn't pop its twin, so the answer is *strictly* greater; with `<=`, equals pop each other. *"A larger value"* is `<`. Read it off the statement.

## The amortised sentence — say it unprompted

> *"Each element is pushed exactly once and once popped never returns — so at most n pushes, at most n pops, and the `while` body runs at most n times **in total**. ≤ 2n O(1) operations. **The cost belongs to the element, not to the iteration.**"*

**The test for whether it applies:** *can the inner loop do n work on an iteration where n work wasn't already paid for?* Monotonic stack — no. `for i: for j in range(n)` — yes, genuinely quadratic.

Same argument as the sliding window (`left` only increases) and `O(V+E)` (each edge relaxed once).

## Carrying state in the slot

> **Whatever you'll need at pop time has to be on the stack at push time.** You can't look at anything but the top, and you can't go back for it.

`(item, index)` for distances and widths · `(item, count)` for runs · `(item, the answer for everything below me)` for a running min — because **a stack returns to the exact state an item was pushed in**, so anything computed about "everything underneath me" is still true at pop time.

## When it is *not* a stack

- Pushed and popped in the **same iteration** → it's a variable.
- **Never holds more than one item** → it's a variable.
- Needs the **oldest** → queue. The **largest** → heap. **Arbitrary by key** → dict.

---

# Graphs — the decision tree

Full treatment in [08-graphs.md](../modules/08-graphs.md#module-08-graphs).

## First: the derivation runs one way, and it isn't the way it feels

The natural assumption is *"find the invariant, and the invariant tells me which algorithm."* **It's backwards, and believing it leaves you stuck on question one of every problem** — because you cannot state an invariant about `visited` before you know whether there's a queue, a heap, or no container at all.

> **The question picks the algorithm. The algorithm picks the container. The container picks the marking moment. The marking moment *is* the invariant.**
>
> ```
> what is asked  →  algorithm  →  container  →  when to mark  →  the invariant sentence
> ```

**So the invariant is derived LAST and stated FIRST.** You work the tree below in your head (thirty seconds), and the sentence you say out loud before writing code is the *output* of that work, not the input to it.

That's the same shape as binary search: you don't guess `while lo < hi`, you state the range convention and read the operator off it. Here you don't guess where `visited.add` goes — you name the algorithm and read the position off it.

---

## Q1 — Is this a graph problem?

| Signal | |
|---|---|
| A grid, and the words *island / region / area / flood / surrounded / rot* | yes |
| An explicit `edges` list, `adjacency`, `isConnected`, "n nodes" | yes |
| *connected · component · province · network · group* | yes |
| *prerequisite · order · dependency · schedule · before* | yes — directed |
| *shortest · fewest steps · minimum moves · nearest · in how many rounds* | yes |
| A start state, a goal state, and legal **moves** (words, puzzles, jumps) | yes — **implicit graph** |

## Q2 — What is the OUTPUT? This is the top-level split

| The problem asks for | Family | → |
|---|---|---|
| "how many groups", "are u and v connected", "is it one piece" | **connectivity** | Q3a |
| "shortest", "fewest", "minimum steps", "nearest", "how many rounds" | **shortest path** | Q3b |
| "a valid order", "can all of them be finished" | **ordering** | Q3c |
| "does a cycle exist", "the redundant edge", "is it a valid tree" | **cycle** | Q3d |
| "mark / count / transform everything reachable" | **plain traversal** | Q3e |
| "minimum total cost to connect everything" | **MST** | Q3f |

### "minimum" is in four of those six rows — it carries no information

| Family | Its "minimum" phrase |
|---|---|
| shortest path | "**minimum** number of steps / minutes / moves" |
| MST | "**minimum** total cost to connect everything" |
| connectivity | "**minimum** operations to connect" (LC 1319) |
| ordering | "**minimum** semesters" (LC 1136) 🔒 |

🔒 = LeetCode Premium.

> **The discriminating question is *minimum what?* — a number of STEPS, or a total EDGE COST?**
>
> **MST asks which edges to keep. Shortest path asks how far.**

**The three-second test: is there a weight on the edges, and do I get to *choose* which edges exist?** If the adjacency is fixed and free — a grid, an unweighted `edges` list — it is **never** MST. There is nothing to minimise over.

**Independent kill-switch:** union-find (and therefore Kruskal) **knows *whether*, never *how far*.** Any problem whose answer is a distance, a path, or an ordering is not a union-find problem ([08-graphs.md](../modules/08-graphs.md#union-find-or-dfs), §Union-find or DFS?). On an unweighted grid, that check alone rules MST out without Q2 needing to be right.

---

## Q3a — Connectivity

> **Is the graph fixed, or are edges arriving?**

| | Reach for |
|---|---|
| Fixed graph, count the components once | **DFS or BFS**, outer loop over all nodes, **one shared `visited`** |
| Edges arrive over time · "are u,v connected?" asked repeatedly · "which edge closes the cycle" · MST | **Union-find** |

**Tie-break when both work** (e.g. count components of a fixed edge list): DFS is less code and needs no second structure. Union-find wins the moment the graph changes or you need *which* edge.

### "DFS or BFS" is a family, not an answer — one more choice to make

Q3a hands you a **family**; Q5's table is indexed by a **specific algorithm**. You cannot read the row until you have picked one.

> **When nothing in the problem depends on distance, DFS and BFS return the same answer.** There is no correctness reason to prefer either. You choose on **code length** and **stack depth**.

| Ask | If yes |
|---|---|
| Do I need **distance**, **fewest steps**, or **level order**? | **BFS** — it's not a preference, it's the only one that works |
| Do I need a node's answer to depend on its **descendants'** (area, sum, post-order, cycle colours)? | **DFS** — same as trees |
| Neither — I'm only marking or counting | **Either.** Default to **recursive DFS**: fewer lines, no explicit container |
| …but can the recursion go deeper than ~1000 frames? | **BFS or an explicit stack** |

**The depth question is arithmetic, not intuition: the deepest possible recursion is the size of the largest component.** On a grid that's `rows × cols`.

| Problem | Worst-case depth | Verdict |
|---|---|---|
| [Number of Provinces](https://leetcode.com/problems/number-of-provinces/) (LC 547), `n ≤ 200` | 200 | recursion is fine |
| **A grid with `m, n ≤ 300`** | **90,000** — one snaking region | over the limit *in principle* |

Whether a judge's tests contain a snake that long is luck. **Naming the risk out loud is what the interviewer listens for**:

> *"I'll write it recursively; if the grid were larger I'd switch to an explicit stack or BFS to avoid Python's recursion limit."*

That sentence costs three seconds and shows you computed the depth rather than hoped. The arithmetic is in [08-graphs.md](../modules/08-graphs.md#recursion-depth-is-arithmetic), §Recursion depth is arithmetic.

## Q3b — Shortest path

> **1. Are the edges weighted?**

| | Reach for | Mark |
|---|---|---|
| No — every step costs 1 | **BFS** | on push |
| Yes, non-negative | **Dijkstra** — min-heap instead of a queue | **on pop** |
| Yes, negatives allowed | Bellman-Ford *(out of scope)* | — |

> ⭐⭐ **Why the marking column changes — `visited` is a *claim*, and weights withdraw it.**
> `visited` asserts *"the first time I arrive at a node is the best way to arrive."* BFS earns that claim: every edge costs 1, so the frontier expands in distance order. Weights break it — a 3-edge route can be cheaper than a 1-edge route. So on a weighted graph the boolean **must come out**, replaced by `dist[]` and the relaxation test `if d + w < dist[v]`. The min-heap then *restores* the claim at pop time, which is why `done` goes back in and why it is marked **on pop**.
>
> **marker → no marker → a different marker.** If you cannot say which of the three you are in, you are guessing.

> ⭐⭐ **`done` in Dijkstra is not a cycle guard.** It is a **process-each-node-once** guard, identical in role to `visited` in BFS: it skips the stale copies left in the heap when a distance improved. Without it the answers stay correct and the work grows ([08-graphs.md](../modules/08-graphs.md#done-is-not-a-cycle-guard), §`done` is not a cycle guard). Removing it because "there are no cycles here" is the same error as removing `visited` from a tree traversal with shared children.

> ⭐ **Heap tuples: `(what_I_am_minimising, what_I_need_back)`.** `heapq` compares left to right. The reversed form `(point, cost)` orders the heap by **x-coordinate**: it can pass a small example by luck and is wrong in general. If element 0 is not the quantity named in the problem statement, the heap is sorting the wrong thing.

> ⚠️ **A bound that mentions the *magnitude* of the weights is not a bound.** A relaxation DFS with no rounds and no marker is correct but **exponential** in the worst case: [08-graphs.md](../modules/08-graphs.md#why-the-relaxation-dfs-is-exponential), §Why the relaxation DFS is exponential, builds the chain that proves it; on bounded integer weights it is merely *pseudo-polynomial*, a bound in the size of the weights, not the size of the graph. **O(V·E) is Bellman-Ford's, and Bellman-Ford earns it with V−1 rounds**, each relaxing all E edges once. Remove the rounds and the bound goes with them.

> ⚠️ **"Fewest steps" is unweighted even when the graph looks expensive.** Ask whether the cost is *per edge* or *uniform*. A grid where every move costs 1 is BFS, not Dijkstra — reaching for the heap there is the classic over-engineering tell.

> **2. How many starting points?**

| | |
|---|---|
| One | plain BFS |
| Many, and I want the distance to the **nearest** one | **multi-source BFS** — seed the queue with *all* of them at distance 0, before the loop |

> **3. Do I need the length, or the actual path?** Length → a level counter. Path → a `parent` map, then walk back from the goal.

## Q3c — Ordering

→ **Topological sort.** Then one sub-question:

| | Use |
|---|---|
| **Default** | **Kahn's** (indegree + queue) |
| You need "how many rounds / semesters / levels" | **Kahn's** — one queue level *is* one round. DFS post-order **cannot** produce this |
| The graph can be deeper than ~1000 | **Kahn's** — iterative. A node count of a few thousand already qualifies, because one chain can use all of them |
| You need the **lexicographically smallest** valid order | **Kahn's**, `deque` → `heapq`. **A one-line swap.** DFS with sorted adjacency does *not* do this: on two nodes and no edges, reversed post-order gives `[1, 0]` |
| You need to know whether the order is **unique** | **Kahn's** — `len(q) == 1` at *every* pop ⟺ unique: two ready nodes can go in either order, and if only one is ever ready, every step is forced. DFS has no equivalent |
| The graph is cyclic and you want **the nodes not affected by it** | **Kahn's** — the partial `order` it returns is exactly the nodes with **no cycle upstream**. Run it on the **reversed** graph and you get the nodes with no cycle downstream, the [Find Eventual Safe States](https://leetcode.com/problems/find-eventual-safe-states/) (LC 802) answer |
| You need **which nodes form the cycle** | **three-colour DFS** — at detection time the GREY nodes are the current path, and the part of it from the GREY node you just hit down to the current node is exactly the cycle |
| You need the post-order for something else anyway (memoised DFS on a DAG, Kosaraju SCC) | **DFS** |
| You want to **stop at the first cycle** and return nothing else | **DFS** — it returns up the stack the instant it hits GREY; Kahn's always drains the whole queue |

⚠️ **NOT a rule: "cycle detection → DFS, ordering → Kahn's."** **Both do both** — DFS gives a topological order via post-order-then-reverse, and Kahn's detects cycles via `len(order) != n`. **The choice is driven by constraints and extras, never by which of the two things you're computing.** A problem that is pure cycle detection can still favour Kahn's, when its constraints allow a chain past the recursion limit — depth attaches to the graph, not to the question.

**Why Kahn's is the default, in three lines:** the cycle test is free (`len(order) != n`); it's immune to the recursion limit; and it handles disconnected graphs by construction, because it seeds *every* indegree-zero node at once — no outer loop, no WHITE guard.

**Why `len(order) != n` works:** every node in a cycle permanently has indegree ≥ 1, each waiting on another member of the cycle, so none ever enters the queue and the loop drains short.

> ⭐ **Every Kahn's-wins row above is a *one-line* change to the same template** — `deque`→`heapq` for lex-smallest, `for _ in range(len(q))` for rounds, `len(q) == 1` for uniqueness, `return order` instead of `[]` for the safe nodes. **That's the real argument: the template is a platform.** DFS post-order gives you one thing, in reverse.

> ⚠️ **Two things that are *not* reasons.** **(1) Speed** — both are **O(V+E) time and O(V+E) space**; the choice is never asymptotic. **(2) "Which one gives an order"** — both do, and the two orders often differ while both being valid. *DFS finalises the **last** node first (hence `[::-1]`); Kahn's finalises the **first** node first (no reversal).* Disagreement is not a bug.

### Kahn's vs BFS — three differences

| | A node joins the frontier when… | Bookkeeping | Level k means |
|---|---|---|---|
| **BFS** | **ANY** neighbour reaches it | a **boolean** | the **shortest** path from the source |
| **Kahn's** | **ALL** its prerequisites are done | a **counter** | the **longest** chain ending here |

```
A → B,  A → C,  B → C      C is at BFS level 1 and Kahn's round 3, same graph
```

> **ANY needs a boolean. ALL needs a counter.** And **Kahn's rounds ARE longest-path depth** — which is why "minimum semesters" is the longest path in the DAG.

Third difference: BFS is seeded by a **given** source; Kahn's by a **structural property** (`indeg == 0`). That's why it needs no outer loop for disconnected graphs, and why the cycle test is free — **a node in a cycle never reaches indegree 0.**

**The family — same invariant, different threshold.** [LC 310](https://leetcode.com/problems/minimum-height-trees/) is Kahn's on an undirected tree: counter = `degree`, threshold = `== 1` (a leaf), stop when **≤ 2 remain** (the centre *is* the answer). **The counter is the invariant; the threshold is the problem.**

⭐ **And it's cheap to learn: Kahn's is multi-source BFS with a counter.** Seed with every indegree-zero node instead of every source; **the indegree array is the visited set** — `indeg[v] == 0` means "every prerequisite of v is already in `order`". Same lesson as *the marking can live in the data*.

> ⚠️ **Write the arrow before you build `adj`:** *"edge X → Y means X must come before Y."* Then check the input's pair order against it: statements use both orders, and the algorithm can't tell.

## Q3d — Cycle detection

> **Directed or undirected?** These are genuinely different algorithms.

| | Reach for |
|---|---|
| **Directed** | **Three-colour DFS** — GREY = on the current path. Or Kahn's + `len(order) != n` |
| **Undirected** | DFS with a `parent` **parameter**, or union-find (first `union` returning `False`) |

> ⚠️ **Two states is not enough for a directed graph.** Arriving at a visited node is *not* a cycle — a diamond `A→B→D, A→C→D` reaches D twice with no cycle anywhere. A cycle is an edge to a node **still on the current path**.
>
> *"Have I ever been here?"* and *"am I here **right now**?"* are two different questions. GREY answers the second; BLACK says "finished, and proven clean" — and doubles as the memo that keeps a dense DAG from going exponential. **Omitting `color[u] = BLACK` collapses three states back to two.**

> ⚠️⚠️ **Start from EVERY node — the graph may be disconnected.** A DFS from one start only sees what that node can reach, so a cycle in another component is invisible. `[[1,0],[3,2],[2,3]]` starting at 1 reports "no cycle." **`for u in range(n)`** — never `for u in adj`, which misses nodes with no edges — with **one shared colour array**, and a `WHITE` guard so each node is explored once overall. *Kahn's needs no such loop: it seeds every indegree-zero node at once, so components are covered by construction. A real argument for preferring it.*

**"Is it a valid tree?"** → a tree is defined by two properties at once. Write both down before coding, and build a counterexample for each one checked alone.

## Q3e — Plain traversal

→ **Recursive DFS.** Switch to BFS or an explicit stack when the depth can exceed ~1000 (Python's limit) — a 200×200 grid path is 40,000 deep.

## Q3f — MST

→ **Kruskal** (sort edges, union-find, skip the ones that close a cycle) or **Prim** (heap).

### "Return the answer that occurs LAST in the input" ≠ "iterate backwards"

When a statement says *"if several answers qualify, return the one that occurs last in the input"*, reversing the loop is a reflex, not a reason. **What decides the direction is the moment your algorithm can know an item qualifies.**

- An **incremental** algorithm judges each item against only what came before it. Ask what it can know at item k, and whether an earlier qualifying item can even be detected before the later ones have arrived.
- An algorithm that **already knows the whole answer set** before it scans can walk in either direction, and walking backward to the first match is then correct.

**The check:** build a small input with two qualifying items, trace your loop, and see which one it returns.

> **Same tie-break, possibly opposite loops. Decide the direction by reasoning about when your algorithm can know, not by the word "last".** Same family as first-T vs last-F.

## Q3g — The inversion: "for EVERY node, can it reach X?"

Full treatment in [08-graphs.md](../modules/08-graphs.md#the-inversion-start-from-the-special-thing), §The inversion: start from the special thing.

**Reachability is per node**, so the forward version cannot share a `visited` set — and a shared `visited` is exactly what makes traversal linear.

| | Traversals | Time | 200×200 grid |
|---|---|---|---|
| Forward, one per node | **V** | O(V·(V+E)) | ≈ 5 × 10⁹ ✗ |
| **Reverse, seeded from X** | **1 or 2** | **O(V + E)** | ≈ 1.2 × 10⁵ ✓ |

> **"A can reach X" is the same statement as "X can reach A in the reversed graph."** Reverse the edges and seed the traversal with all of X. One multi-source pass answers it for every node at once.

| Shape | Answer | Example |
|---|---|---|
| **Intersect** — reach X₁ **and** X₂ | `A & B` | two special sets, one traversal from each |
| **Complement** — everything that *cannot* reach X | traverse from X, flip what you didn't mark | [Number of Enclaves](https://leetcode.com/problems/number-of-enclaves/) (LC 1020) |

⚠️ **Reversing the edges flips every direction-dependent test.** A rule for "may I move from `cur` to `nei`?" becomes, walking backward, the same rule read from `nei` to `cur`. **Say which way you're walking before writing the operator** — the algorithm is blind to the error, same class as first-T vs last-F.

⭐ **What disappears is the real argument: no flags.** The forward version needs a *"did I reach it"* flag per node, propagated up through the recursion — and that is where the bugs live: flags as locals that never escape their frame, a missing `nonlocal`, a reset per start. **Set membership replaces every flag, and "and" becomes `&`.**

**The question to ask:** *"Is the set I want defined by reaching something special? Then start from the special thing."* It's usually named in the statement and sitting on a boundary — the border, the ocean, the terminals, the leaves, the gates, the exits.

---

## Q4 — What is a node? → the representation

| Input | Node ids | Build |
|---|---|---|
| **Grid** | `(r, c)` tuples | nothing — neighbours are **computed** from `DIRS` |
| Edge list + `n`, ids `0..n-1` | ints | `adj = [[] for _ in range(n)]` |
| Edge list, ids are **strings or tuples** | str/tuple | `adj = defaultdict(list)` |
| Adjacency **matrix** given | ints | use it directly — and complexity is **O(V²)** |
| No edges given (words, states, moves) | whatever the state is | `neighbours()` is a **function** |

**Then, always:** *directed or undirected?* → one `append` or two.

## Q5 — What does `visited` mean? Read it off the row

By this point it's determined. This is the table to memorise.

**Full templates — code, invariant, traps, complexity — are in [08-graphs.md](../modules/08-graphs.md#every-template-in-one-place), §Every template, in one place.** Each row below links the module section for its template.

| Algorithm | Container | Mark when | `visited` is | Time |
|---|---|---|---|---|
| **[Recursive DFS](../modules/08-graphs.md#bfs-and-dfs-on-a-graph)** | the call stack | **first line of the function** | a `set`, or a mutated grid | O(V+E) |
| **[Iterative DFS](../modules/08-graphs.md#why-an-explicit-stack-survives)** | `list` as stack | **on push** | a `set` | O(V+E) |
| **[BFS](../modules/08-graphs.md#bfs-and-dfs-on-a-graph)** | `deque` | **on push** | a `set`, or a `dist` map | O(V+E) |
| **[Multi-source BFS](../modules/08-graphs.md#multi-source-bfs)** | `deque`, pre-seeded | on push — **all sources at init** | the `dist` map | O(V+E) |
| **[Dijkstra](../modules/08-graphs.md#dijkstra)** | min-heap | **on pop** *(a distance can improve while queued)* | the finalised set | O(E log V) |
| **[Kahn's topo sort](../modules/08-graphs.md#kahns-algorithm)** | `deque` | when **indegree hits 0** | **the indegree array** | O(V+E) |
| **[3-colour DFS](../modules/08-graphs.md#directed-cycles-three-colours)** | the call stack | GREY on entry, **BLACK on exit** | **the colour array** | O(V+E) |
| **[Union-find](../modules/08-graphs.md#union-find)** | **none** | — | **`find(x)` is the membership test** | O(E·α(n)) |
| **[Kruskal (MST)](../modules/08-graphs.md#union-find)** | **none** | — | union-find + a sort | O(E log E) |
| **[Prim (MST)](../modules/08-graphs.md#prim-is-dijkstra-with-one-line-changed)** | min-heap *(or a plain array)* | **on pop** | the tree set | O(E log V) — **O(V²) array form** |

> ⭐ **Prim is Dijkstra with one line changed:** `total += cost` accumulates the **edge weight** instead of the distance from a source. Heap, pop, skip-if-seen, mark, expand — all verbatim.
>
> ⚠️ **On a dense graph the heap is the wrong container.** If E = V² (every pair connected, e.g. LC 1584's points), O(E log V) = **O(V² log V)** with O(V²) space, while **array Prim is O(V²) time and O(V) space**: V rounds, each scanning V best-cost entries. Ask *"is E closer to V or to V²?"* before reaching for `heapq`.

> **The bottom two rows are why "always use a visited set" is wrong advice.** In a topological sort the indegree counter does the job; in union-find there is no traversal to guard.

### Define `visited` by a PROPERTY, never by the ROUTE

| Bad definition | What it silently excludes |
|---|---|
| *"we arrived here through an edge"* | the **start node** of every component |
| *"we reached it from a source"* | every node that **starts** as a source |
| *"it came off the queue"* | everything still **in** the queue |

All three define `visited` by **how you got there**, and all three have the same hole: **the nodes nobody got to** — the outer loop's start, the BFS seeds, the roots of a forest.

> **Define `visited` by a property the node *has*, not by the route that brought you there.**
>
> ✗ *"reached via an edge"* · ✓ *"already assigned to a component"* · ✓ *"already has a distance"*

**The three-second test: does my start node satisfy my own definition?** If not, the definition is wrong and something gets processed twice.

Same move as binary search's *"does my reference satisfy its own predicate?"* — a predicate written with `<` can be false on the reference itself. **Check the boundary case against your own sentence before trusting it.**

And it's *why* multi-source BFS works: multi-source is **defined** by having seeds nobody reached, so a route-based definition cannot express it.

### What Q5 gives you: a line position

*This is the part that reads as mysterious and isn't.* Q5 introduces **no new idea**. It tells you **which line `visited.add` goes on** — and putting it on the wrong line is the double-processing bug, which is silent.

```python
# Recursive DFS  →  "first line of the function"
def dfs(r, c):
    visited.add((r, c))          # ← here. BEFORE the neighbour loop
    for dr, dc in DIRS:
        ...

# BFS  →  "on push"
        visited.add((nr, nc))    # ← next to the append …
        q.append((nr, nc))       #    … NOT after the popleft
```

> **Every row of the Q5 table resolves to one of those two pictures**, or to "there is no line, because the counter/`find` already does it."

## The three reading questions, not algorithm questions

Decide each **before** writing, because afterwards they're invisible — the code is perfect and the answer is wrong:

1. **Directed or undirected?** → one `append` or two.
2. **Which way does the edge point?** → `[a, b]` means what, exactly?
3. **Does the answer count nodes or steps?** → a 1×1 grid answers `1` or `0`. The off-by-one lives in the statement, not the algorithm.

Same class as *first-T or last-F* in binary search.

---

# Backtracking

Full treatment in [07-backtracking.md](../modules/07-backtracking.md#module-07-backtracking).

## The one-line definition

> **Backtracking is graph DFS whose `visited` mark is GREY instead of BLACK** — per-path, and taken off at exit.

**And the undo is what makes it exponential.** BLACK is a memo; without a memo, the same node is entered again and again on different paths. *Delete the undo and you get a linear algorithm that answers a different question.*

## The acid test — is this module 08 or module 07?

> ### **Can two different explorations disagree about the same node?**

| Answer | | |
|---|---|---|
| **No** — a node's state is a fact about the node | *"cell (2,3) is in component 4"* · *"its distance from the source is 5"* | **global mark, O(V+E)** |
| **Yes** — a node's state depends on how you got there | *"used on this path"* · *"this letter is consumed"* | **per-path mark, exponential** |

> **When two explorations can disagree, the state belongs to the *path*, not to the *node*. Then you cannot share the marking — and once you cannot share it, you cannot be linear.**

⚠️ **This kills "why not multi-source BFS?"** Multi-source is fast **because all sources share one `visited`.** Here sharing is the bug. And BFS at any price fails too: a queue entry would carry **its own** used-set, O(L) per entry, copied on every push.

> ⭐ **Backtracking needs an *exit* moment, so it is always recursion.** A queue entry waits; a stack frame returns — and the return is where the un-mark goes. It's the same property that makes three-colour cycle detection awkward on an explicit stack: BLACK needs an exit moment too.

## Signals

| Signal | |
|---|---|
| **"Return all …"**, "generate all", "every possible" | ✓ the strongest signal |
| Return type `List[List[int]]` / `List[str]` with a combinatorial count | ✓ read the signature |
| subsets · permutations · combinations · partitions · arrangements | ✓ named outright |
| "Place n things so none conflict" | ✓ constraint satisfaction |
| A path through a grid where a cell can't be reused **within one path** | ✓ grid backtracking |
| **`n ≤ 20`, `n ≤ 9`, `word ≤ 15`** | ⭐ **a tiny bound is permission to be exponential** |
| "**How many** ways" · "the **best** X" | ✗ **DP** — you don't need the candidates, only the number |
| n is 10⁵ | ✗ not backtracking |

## Before writing anything: name the node, the edge, the leaf

The first question is always *"what tree am I walking?"* ([07-backtracking.md](../modules/07-backtracking.md#what-tree-am-i-walking), §What tree am I walking?). **This is the version of that question that produces code.** "Draw the tree" on its own fails the same way *"state the invariant"* failed: it's a picture, not a blank to fill. **Three blanks, in sentences:**

| Blank | Fill it with | What it becomes in code |
|---|---|---|
| **A node is** ___ | *"`path` holds one ___"* | **what you copy into `res`** |
| **An edge is** ___ | *"from here, the legal next choices are ___"* | **the `for` loop and its guards** |
| **A leaf is** ___ | *"a node is a complete answer when ___"* | **the base case** |

> **Blanks 2 and 3 are not preparation for the code. They *are* the code.** Fill all three in words and the skeleton below writes itself.

| Problem | A node is | An edge is | A leaf is |
|---|---|---|---|
| Every subset of distinct items | a subset drawn from indices `< start` | pick any index `i ≥ start` | none — **every node is an answer** |
| [Combinations](https://leetcode.com/problems/combinations/) (LC 77), choose k of 1..n | an increasing run of fewer than k numbers | add any number above the last one | `len(path) == k` |
| [Combination Sum III](https://leetcode.com/problems/combination-sum-iii/) (LC 216) | distinct digits, increasing, with `sum ≤ n` | add any digit above the last one, up to 9 | `len(path) == k` and `sum == n` |
| Every ordering of distinct items | an ordering of *some* of the items | append any item **not already used** | `len(path) == n` |
| [Path with Maximum Gold](https://leetcode.com/problems/path-with-maximum-gold/) (LC 1219) | a cell path from one start | step to an adjacent cell with gold **not on the path** | none — every node is a candidate for the maximum |

**Column 3 is where the two index switches live, and where most of the bugs are.**

### The fourth question — the one the tree has no column for

> ### **What do I mutate that isn't `path`?**

`used` · `seen` · `board` · a running `count`. **Every one of them needs its own undo.** The node/edge/leaf blanks say nothing about these, and forgetting one doesn't crash: an orderings search that never clears `used` returns **1 ordering out of 6** on three items, because the first completed path leaves every item marked. **So it is four questions, and the fourth is the expensive one.**

### The checking move

**Draw two levels on the smallest real input, then read your loop and confirm it produces exactly those children.**

On the subsets of `[1,2,3]`: level 1 has **3** children, level 2 under `[1]` has **2**. `range(len(nums))` gives 3 at every level forever. *Two drawn levels and one look at the loop catches it before submitting.*

> Not useful on a grid search — that tree is too big to draw. **There you name a node and an edge in words and skip the picture.** The sentences transfer; the drawing doesn't.

## The skeleton, and the contract

```python
for choice in <legal choices>:
    make(choice)          # CHOOSE
    backtrack(...)        # EXPLORE
    unmake(choice)        # UNDO — same block, same indentation as the choose
```

> **Every call leaves the world exactly as it found it.** That postcondition is what makes siblings independent.

**The check, and it beats "remember to undo":**

> ⭐ **Count the mutations before the recursive call. Count the restores after it. Two and one is always a bug.**

⚠️ **"At the end" is not a place when a function has two `return`s.** Every `return` that runs after the mark must un-mark first — or use `any(...)` so there is one exit.

## Which loop — the index is two independent switches

> **Having a `start` parameter forbids REORDERING. Adding `+ 1` to it forbids REUSE.**

| | Reuse | Reorder | |
|---|---|---|---|
| `dfs(i + 1)` | ✗ | ✗ | subsets, combinations |
| **`dfs(i)`** | ✓ | ✗ | a target sum with reuse |
| no index + **`used[]`** | ✗ | ✓ | orderings, permutations |
| **`dfs(level)`** | — | — | one slot per level, each with its own choice set ([07-backtracking.md](../modules/07-backtracking.md#slots-with-their-own-choices), §Slots with their own choices) |

⚠️ **"I need to allow reuse" means drop the `+ 1`, never the parameter.** Dropping `start` flips both switches: reuse *and* every ordering of every answer. Full treatment: [07-backtracking.md](../modules/07-backtracking.md#the-index-is-two-switches), §The index is two switches.

**And it's a reading question, answered by the statement:** *"two answers are different if they **use different counts**"* → `start`. *"every possible **arrangement**"* → `used[]`.

⚠️ **Something must shrink** — index, budget, or level — or the recursion doesn't terminate. Name it.

## Two dedup mechanisms, not interchangeable

| The duplicate | Cause | Fix |
|---|---|---|
| `[1,2]` vs `[2,1]` | choices can be made in any order | **the start index** |
| the same output twice from equal inputs | the **input** has equal values | **`sort()`, then skip equal siblings** |

```python
if i > start and nums[i] == nums[i - 1]: continue
```

> **`i > start` ⟺ `nums[i-1]` is also a choice at THIS level** — a sibling already tried. `i == start` means it's an **ancestor**, on the path, and stacking a second equal value is legitimate.

⚠️ **`i > 0` deletes correct answers silently.**

## Pruning — rank it before you write it

> **Prune only on a constraint that is *monotone along the path*: once violated, always violated.** Same test as the `F…F T…T` predicate in binary search.

| Prune | Kind |
|---|---|
| duplicate-sibling skip | ⭐ **changes the complexity class** |
| `if nums[i] > remaining: break` *(sorted)* | constant factor |
| `return` once a hit is recorded | constant factor |
| `if total > target: return` with reuse | **load-bearing for termination** — not an optimisation |

⚠️ **A budget prune caps the tree's DEPTH and does nothing about its WIDTH.** `[1]*100, target 30`: about 10²⁵ nodes (C(100, 30) ≈ 2.9 × 10²⁵ paths reach depth 30) for 1 distinct answer, versus 31 nodes with the sibling skip ([07-backtracking.md](../modules/07-backtracking.md#depth-versus-width), §Depth versus width).

⚠️ **Sorting for `break` is a constant factor, not an exponent.** Sorting never changes how many answers exist. When it changes a complexity class it's because it enabled a different *algorithm* — including the adjacency that licenses the duplicate skip.

> ⭐ **A set on the output is the receipt for a prune you didn't do.** Deduping deletes one leaf; skipping a sibling deletes the subtree.

## The `return` rule — read it off the signature

| Function returns | Inside the choice loop | After it |
|---|---|---|
| **nothing** (mutates an accumulator) | `dfs(...)` **bare** — never prefixed with `return` | nothing |
| **a bool** | **`if dfs(...): return True`** | **`return False`** |
| **a number** | `best = max(best, dfs(...))` | `return best` |

> **`return dfs(...)` hands the first child's *failure* back as the whole function's verdict.** Return on success; keep looping on failure. Full rule in [07-backtracking.md](../modules/07-backtracking.md#the-return-rule-collect-all-or-find-one), §The return rule: collect all, or find one?

## Complexity of an exponential algorithm

> **"O(\_\_) time because the tree has \_\_ leaves and each costs \_\_."**
> **"O(\_\_) space because the only thing I allocate is \_\_, bounded by the depth."**

| Shape | Count |
|---|---|
| subsets | **2ⁿ** |
| permutations | **n!** |
| choose k | **C(n,k)** |
| strings over an alphabet of k | **kⁿ** |
| balanced / nested structures | **Catalan ≈ 4ⁿ/n^1.5** |

⚠️ **Cost per leaf is not 1** — `path[:]` is O(n).
⚠️ **The output is exponential; auxiliary space is O(depth)**, not O(answers).
⚠️ **Depth isn't always n** — with reuse it's `target/min`, and the path can be longer than the input.
⚠️ **Where a cost sits decides add vs multiply.** A sort at the top is a term you add.

**Optimality:** *"any algorithm must write down every answer, so Ω(output size) is a lower bound and I match it."* — **output-sensitive**, and the frame that makes generate-and-dedup's verdict precise.

## When it stops being backtracking

| | Backtracking | DP / memoised DFS |
|---|---|---|
| Asks for | *"all the candidates"* | *"how many"* / *"the best"* |
| Future depends on the path? | **yes** | **no** — only on the state |
| The mark | GREY, undone | **BLACK is back** — a memo |

> ⭐ **You cannot memoise a search whose state includes "everything used so far"** — that state *is* the path, so no two nodes share it. **Memoisation becomes possible exactly when the remaining problem has a small key.**

---

# Dynamic programming

Full treatment in [09-dp.md](../modules/09-dp.md#module-09-dynamic-programming).

## Two pointers or DP? — the discard test

> ### **A converging two-pointer is legal only when you can *prove* one side can be discarded.**

From `(lo, hi)`, if the ends don't settle the question, the answer could be in `s[lo+1..hi]` **or** in `s[lo..hi-1]`. **If you cannot prove one of them is dead, you must try both.**

> ⭐⭐ **"I must try both, and the two branches overlap" is the literal definition of overlapping subproblems. The reason the two-pointer fails IS the reason DP applies.** Both branches contain `s[lo+1..hi-1]`, so trying both by plain recursion re-solves that middle piece again and again.

**What supplies the proof, and what doesn't:**

| The proof comes from | Then | Example |
|---|---|---|
| **Sortedness** | `sum < target` ⟹ `lo` can never work with anything smaller. **One side is dead** | 3Sum, two-sum on a sorted array |
| **A monotone property of the pair** | moving the shorter wall is the only move that can improve | Container With Most Water |
| ⭐ **The question has ONE candidate** | a mismatch is a **final verdict**, not the elimination of one option | [LC 125 Valid Palindrome](https://leetcode.com/problems/valid-palindrome/) |
| **Nothing** | a mismatch eliminates **one** candidate and says nothing about the others | [LC 516 Longest Palindromic Subsequence](https://leetcode.com/problems/longest-palindromic-subsequence/) → **DP** |

### The contrast to memorise — same predicate, opposite tool

| | Asks | A mismatch at the ends means | Tool |
|---|---|---|---|
| **LC 125** Valid Palindrome | *"is **the string** a palindrome?"* | **the answer is No.** Done | **two pointers**, O(1) space |
| **LC 516** Longest Palindromic Subsequence | *"which of the **2ⁿ subsequences** is the longest palindrome?"* | **the two ends can't both be in it.** Drop the left end or drop the right end, and nothing says which | **DP over intervals** |

> **One candidate → a converging walk. Many candidates → a table.** The predicate is identical; what differs is how many questions are being asked.

**This is *Discard*, escape 4 of [the cascade](#the-cascade--run-this-when-an-array-or-string-problem-stalls), applied one level up.** The word doing the work is still **prove**: *"of the things I've already seen, can I **prove** some will never be needed again?"* — without the proof you aren't discarding, you're losing answers.

### And the corollary that names the state

**When you can't discard, you have to ask about every piece — so the state becomes the piece.**

> ⭐ **If the problem is about a *substring / subarray / range*, and the property of that piece must be checked in its own right, the state is TWO indices, not one.** One index can only describe a prefix or a suffix.

⚠️ **The tell that you're in this case:** you try to write *"how does the answer at `i` give me the answer at `i+1`?"* and it has no answer. **That's not a failure — it's the diagnosis.** Ask instead: *"how does a **shorter piece** help me decide a **longer** one?"*

### What the DP buys, in one line

> **It doesn't find the answer differently. It makes the CHECK O(1).**

When the question is *"the best of the n² pieces `s[i..j]`"* and each piece needs an O(n) check, brute force is **O(n³)**. If the check on `s[i..j]` can be read off a shorter piece's stored answer plus O(1) work, the table makes each check O(1) and the whole thing **O(n²)**. *The loop over candidates is unchanged; only the body got cheaper.* Full treatment: [09-dp.md](../modules/09-dp.md#interval-dp), §Interval DP.

## "How would I have known?" — four signals, three of them free

All four run off the statement and the constraints, before a line of code.

### 1. Count the answers the question needs

> ### **Two pointers computes ONE answer by moving. A table computes MANY answers by storing them.**

| | The question | Answers needed |
|---|---|---|
| **LC 125** | *"**is `s`** a palindrome?"* | **one** |
| *"the longest substring with property P"* | *"which of the **n²** substrings is the longest one with P?"* | **n²** |

**A converging two-pointer holds exactly one interval — the one between the pointers.** If the answer is *"the best over all intervals"*, **one interval is not enough state to hold the problem.** Structural, and visible before you choose anything.

> ⭐ **The tell in the wording: a superlative — *longest / shortest / maximum / minimum / fewest* — applied to a PIECE of the input.**
> ***"Is X"* → evaluate, one walk. *"The best X"* → rank, and ranking needs a table, unless a window or a greedy rule can prove most pieces irrelevant (signal 4).**

### 2. Read the constraint bound

> ⭐ **`n ≤ 1000` is permission to be O(n²)** — the same reading move as `n ≤ 20` being permission to be exponential. **The setter's bound names the intended complexity class.**

At n = 10⁵ a quadratic is ruled out and you know to look for structure instead. **Five seconds.**

### 3. Run the two-pointer legality test

**Can I *prove* one side is dead?** See [Two pointers or DP?](#two-pointers-or-dp--the-discard-test) above. No proof → try both → they overlap → **DP**.

### 4. And check why a sliding window fails too

*"Contiguous" + "longest"* normally means **sliding window**. When the property is *"is a palindrome"* it doesn't, and the reason generalises:

> **A sliding window needs the property to be monotone under extension or shrinking** — *"if the window is valid, every sub-window is valid"* — so that shrinking always helps and there is a rule for when to move.

```
"ab"    not a palindrome
"aba"   IS      ← extending a bad window made it good
"abab"  is not  ← extending a good window made it bad
```

**Palindromicity is monotone in neither direction. There is nothing to shrink *while*, and nothing to extend *while*. The window has no rule.**

> ⭐⭐ **Sliding window, two pointers and greedy all need a monotone or provable local rule. Checking for one and finding none IS the DP signal.**

### And the route that gets you there anyway: brute force, then complexity, then optimise, out loud

**Write the brute force**: *"for each of the n² substrings, test it in O(n)"* → **O(n³)**. Then walk the four escapes:

> **1. Remember — *is there something I could store that makes the inner loop unnecessary?***

The inner loop is the check on one piece, and **checking `s[i..j]` re-walks characters that checking a shorter piece inside it already walked.** That's the escape; the thing you store is the table.

> ⭐ **The generalisable trigger: your brute force's inner loop is re-deriving something an earlier iteration already computed.** Same sentence that finds a monotonic stack under *Discard* — here it finds a **memo**.

---

# Top-K and selection

Full treatment in [10-heaps.md](../modules/10-heaps.md#module-10-heaps-top-k-and-selection).

## The signal, and the four answers

**"k largest / k smallest / k closest / k most frequent / kth largest"** — all one problem. Four solutions, and knowing all four *plus the trade* is the answer.

| | Time | Extra space | Output ordered? | Reach for it when |
|---|---|---|---|---|
| `sorted(xs, key=…)[:k]` | O(n log n) | O(n) | ✓ | k is close to n · you want them ordered anyway · you want the shortest correct code |
| **heap of size k** | **O(n log k)** | **O(k)** | ✗ | k ≪ n · streaming/unbounded input · you may not mutate the input · **no bad case** |
| `heapify`, then k pops | O(n + k log n) | O(1) if in place, else O(n) | ✓, as you pop | the whole array in hand and you may destroy it |
| **quickselect** | **O(n) average**, O(n²) worst | O(1) in place | ✗ | the optimum matters and a worst case is acceptable |

**Only quickselect is linear for every k**, on average. That's the whole argument for it. But the size-k heap runs on a stream, never touches the input, and has no adversarial input, so *"I'd write the heap unless you want the optimal average"* is a legitimate, well-received answer. The arithmetic per row is in [10-heaps.md](../modules/10-heaps.md#choosing-among-the-four-answers), §Choosing among the four answers.

**Min-heap for the k LARGEST.** The heap's minimum is the weakest member of your current top-k — exactly the one to evict when a better candidate arrives.

## The rank rule — which heap, and where the answer is

> ### **The kth largest is the WEAKEST member of the top k.**
> ### **The kth smallest is the STRONGEST member of the bottom k.**

Within the k survivors, rank 1 is the extreme end and **rank k is the near end** — the one on the chopping block. So the answer is the **root**, in O(1), never a scan.

| | kth **largest** | kth **smallest** |
|---|---|---|
| Heap holds | the k largest so far | the k smallest so far |
| Which heap | **min**-heap | **max**-heap → push `-x` |
| Evict on overflow | the smallest survivor | the largest survivor |
| Return | `h[0]` | `-h[0]` |

**Choosing the direction, one question:** *what sits at the root is what you throw away.* Keeping the largest → evict the smallest → min-heap. Keeping the smallest → evict the largest → max-heap.

> ⭐ **The consistency check: the element you EVICT and the element you RETURN are the same slot, `h[0]`.** If the return needs a scan, the eviction needed one too and the loop is secretly O(nk). A correct top-k loop never touches anything but the root.

**Why eviction is safe:** the smallest of k+1 candidates for the top k cannot be in the answer — k things already beat it, and nothing arriving later helps it.

⚠️ **The same pattern runs with opposite signs, depending on which end you keep.** Keeping the k smallest of any key (a distance, a cost) evicts the largest → max-heap → **negate the key**. Keeping the k largest evicts the smallest → min-heap → **no negation**. Full treatment: [10-heaps.md](../modules/10-heaps.md#the-rank-sentence), §The rank sentence.

**Push then check.** `heappush` then `if len(h) > k: heappop` — never evict before seeing whether the arrival is better ([10-heaps.md](../modules/10-heaps.md#push-then-pop-in-that-order), §Push then pop, in that order).

## Quickselect — what makes it quickselect

> **You recurse into ONE side only.**

That single property is the whole difference from quicksort, and it's what turns `n log n` into `n`:

```
n + n/2 + n/4 + … ≤ 2n         ← one side, halving on average
n per level × log n levels     ← both sides (quicksort)
```

**Because it only recurses one way it's tail-recursive** — convert it to a `while` loop and the call stack disappears, giving true O(1) extra space. Quicksort can't do this; it genuinely needs both branches.

**The invariant:** after a partition, `A[p]` is in its **final sorted position** — nothing before it is larger, nothing after it is smaller. When `p == k`, `A[:k]` is the k smallest, unordered.

### The three things that go wrong

| | Fix |
|---|---|
| **Non-terminating recursion** — the pivot lands inside the partition you recurse on, so it never shrinks | **Hold the pivot out** before partitioning: `pivot, rest = a[-1], a[:-1]`. Every branch must be *strictly* smaller |
| **Returning too many** — `small + f(small, k)` when the answer is a *subset* of `small` | If `len(small) > k`, return `f(small, k)` **alone**. Only prepend `small` when all of it is in the answer |
| **O(n²) on sorted input** — a deterministic `a[-1]` pivot is adversarial to sorted data | **Random pivot.** Turns a guaranteed worst case into a vanishingly unlikely one |

The first two, each on a small input, are in [10-heaps.md](../modules/10-heaps.md#the-two-classic-bugs), §The two classic bugs.

**Ties:** a two-way partition sends all equal keys to one side, so an input of all-equal keys is O(n²) even with a random pivot. A three-way split (`<`, `==`, `>`) is the robust form ([10-heaps.md](../modules/10-heaps.md#duplicates-the-three-way-partition), §Duplicates: the three-way partition).

**In an interview:** write the allocating version (new `small`/`large` lists) — far easier to get right with no IDE — then *say* **"in place with a random pivot and a three-way partition this is O(1) extra space, and the worst case needs bad luck rather than bad input."** Full credit for knowing the proper form, none of the risk of writing it.
