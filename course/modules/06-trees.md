# Module 06: Trees, DFS and BFS

<!-- toc -->
**Contents**

- [0.1 Prerequisites and the one question](#01-prerequisites-and-the-one-question)
- [0.2 The structure and how it works](#02-the-structure-and-how-it-works)
- [0.3 Vocabulary](#03-vocabulary)
- [0.4 Operations and their cost](#04-operations-and-their-cost)
- [0.5 The primitives](#05-the-primitives)
- [0.6 Inputs that break it](#06-inputs-that-break-it)
- [0.7 Complexity, out loud](#07-complexity-out-loud)
- [0.8 Signals](#08-signals)
- [0.9 Self-check](#09-self-check)
- [DFS vs BFS](#dfs-vs-bfs)
- [DFS](#dfs)
  - [The shape — memorise this](#the-shape--memorise-this)
  - [The three orders](#the-three-orders)
  - [The same three, iteratively](#the-same-three-iteratively)
  - [When to go iterative](#when-to-go-iterative)
  - [Returning a value up the tree](#returning-a-value-up-the-tree)
- [BFS](#bfs)
  - [The shape — memorise this](#the-shape--memorise-this-1)
  - [Level order — the one trick worth knowing](#level-order--the-one-trick-worth-knowing)
  - [Level order via DFS](#level-order-via-dfs)
- [Seeing the difference: the same tree, both ways](#seeing-the-difference-the-same-tree-both-ways)
  - [FIFO — `popleft()`, oldest first](#fifo--popleft-oldest-first)
  - [LIFO — `pop()`, newest first](#lifo--pop-newest-first)
  - [Push order matters only for stacks](#push-order-matters-only-for-stacks)
- [Discover vs. visit](#discover-vs-visit)
- [Common tree mistakes](#common-tree-mistakes)
- [Drill set — cold, no IDE, no running](#drill-set--cold-no-ide-no-running)
- [Before you submit anything](#before-you-submit-anything)
- [Self-check answers](#self-check-answers)
<!-- /toc -->

This module covers binary trees. You'll learn what a tree node is, how to build one by hand, the words interviewers use about trees, and the two ways to visit every node: depth-first (DFS), which uses a stack, usually the call stack, and breadth-first (BFS), which uses a queue. Every tree problem in an interview is a variation of one of the two.

**How to use it.** Read §0, then answer the self-check in §0.9 and re-read the parts of §0 behind any question you miss. Then work through the DFS and BFS sections and do the drill set cold.

| Section | What it gives you |
|---|---|
| §0, the foundation | what a tree is, its vocabulary, what each operation costs, the four primitives, the inputs that break tree code, the signals |
| DFS vs BFS | which traversal, decided in one read |
| DFS | the shape, the three orders and what each guarantees, the same three written iteratively, when to go iterative, returning a value up the tree |
| BFS | the shape, level by level, level order via DFS |
| Seeing the difference | the same tree served FIFO and LIFO |
| Discover vs. visit | the two moments of every traversal |
| Common tree mistakes | the bugs, each linked to its checklist entry |
| Drill set | the problems, with the checkpoint |
| Before you submit anything | the checklist |

---

## 0.1 Prerequisites and the one question

| You need | From | Used here for |
|---|---|---|
| Recursion: base case, trusting the recursive call, returning a value vs updating an answer on the side, stack depth | [00-before-you-start.md](00-before-you-start.md#recursion-and-the-call-stack), §Recursion and the call stack | every DFS in this module |
| Counting cost, and space as the deepest the stack gets | [00-before-you-start.md](00-before-you-start.md#big-o-from-zero), §Big-O from zero | §0.4 and §0.7 |
| The queue: first in, first out, `deque` with `popleft` in O(1) | [02-stacks-queues.md](02-stacks-queues.md#the-queue-first-in-first-out), §The queue: first in, first out | every BFS in this module |
| The stack: last in, first out | [02-stacks-queues.md](02-stacks-queues.md) | iterative DFS |
| Node objects, following a pointer, `None` at the end | [05-linked-lists.md](05-linked-lists.md) | reading and building a `TreeNode` |

**A tree is a linked list with two `next` pointers.** A list node has one `next`, so a `while node:` loop can follow it: there is only ever one way forward. A tree node has a `left` and a `right`. The moment you step into one child, the other is still owed, and you have to remember it somewhere. That somewhere is the whole topic: **remember the other branch on a stack** (recursion does this for you) and you get DFS. **Remember it in a queue** and you get BFS. A linked list is the special case of a tree in which every node has at most one child.

**The one question this module answers:**

> *If you trust the recursive calls on the two subtrees, what does this node do with their answers, and what does it hand its parent?*

Answer that and most tree problems are written. The rest ask about levels or distance from the root, and those go to BFS.

## 0.2 The structure and how it works

A **binary tree** is a set of nodes in which each node has a value and at most two children, a left one and a right one. One node, the root, has no parent. Every other node has exactly one parent.

```
            1
          /   \
         2     3
          \
           5
```

LeetCode defines the node class for you, in this form:

```python
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left      # a TreeNode, or None if there is no left child
        self.right = right    # a TreeNode, or None if there is no right child
```

You receive `root`, a `TreeNode`, or `None` for an empty tree. A missing child is `None`, exactly as the end of a linked list is `None`.

**Building one by hand.** To test your code, build the tree yourself. Nest the constructors, inside out:

```python
root = TreeNode(1,
                TreeNode(2, None, TreeNode(5)),   # 2 has no left child, a right child 5
                TreeNode(3))
```

Or create the root and assign children one at a time:

```python
root = TreeNode(1)
root.left = TreeNode(2)
root.right = TreeNode(3)
root.left.right = TreeNode(5)
```

Both build the tree in the drawing.

**Reading LeetCode's notation.** A problem statement writes that same tree as `root = [1,2,3,null,5]`. The list is the tree read **level by level, left to right**, with `null` for a missing child. Read it in pairs: `1` is the root. Its children are `2, 3`. The children of `2` are `null, 5`. The list stops when the remaining entries would all be `null`, and a `null` gets no children of its own. So `[1,2,3,4,null,null,5]` is:

```
            1
          /   \
         2     3
        /       \
       4         5
```

**A binary search tree (BST)** adds one rule: for every node, **every** value in its left subtree is smaller than the node's value, and **every** value in its right subtree is larger. The rule is about whole subtrees, not just the two children.

```
            8
          /   \
         3     10
        / \      \
       1   6      14
```

Because of the rule, a search can throw one whole subtree away at each step: smaller goes left, larger goes right. That is half the tree only when the tree is balanced. How much it buys you depends on the height, which is the subject of §0.4.

## 0.3 Vocabulary

| Word | Meaning |
|---|---|
| **root** | the one node with no parent; where every traversal starts |
| **parent, child** | a node and the node one link below it |
| **leaf** | a node with no children: `node.left is None and node.right is None` |
| **subtree** | a node together with everything below it. Every node is the root of its own subtree |
| **ancestor, descendant** | an ancestor is any node on the path from this node up to the root; a descendant is any node in its subtree |
| **path** | a sequence of nodes, each linked to the next |
| **depth of a node** | the number of edges from the root down to it. The root has depth 0 |
| **level** | all the nodes with the same depth |
| **height** | the number of edges on the longest path from a node down to a leaf. A single node has height 0. **LeetCode's "maximum depth" counts nodes instead**, so it is one more. Say which convention you're using before you code |
| **balanced** | for every node, the heights of its two subtrees differ by at most 1. A balanced tree of n nodes has height about log₂ n |
| **degenerate (skewed)** | every node has at most one child, so the tree is a chain: height n − 1. A BST built by inserting sorted values comes out like this |
| **complete** | every level is full except possibly the last, which fills from the left |
| **BST** | binary search tree: left subtree smaller, right subtree larger, at every node |
| **pre-order, in-order, post-order** | the three DFS orders: the node before, between, or after its two subtrees |
| **DFS, BFS** | depth-first search (go deep, use a stack) and breadth-first search (go level by level, use a queue) |
| **frontier** | the nodes discovered but not yet visited: what sits in the stack or queue |

## 0.4 Operations and their cost

**h** is the height of the tree. **w** is its width, the most nodes on any one level.

| Operation | Python | Big-O | Trap |
|---|---|---|---|
| Read a node's value or a child | `node.val`, `node.left` | O(1) | `None.val` raises `AttributeError`: test for `None` first |
| Visit every node, any DFS order or BFS | recursion, or `while queue:` | O(n) time | none: each node is handled once |
| The call stack during a recursive DFS | the interpreter's stack | **O(h) space**: O(log n) only if the tree is balanced, O(n) for a chain | a chain of 10⁵ nodes passes the default limit of about 1,000 frames |
| An explicit stack during an iterative DFS | `stack = []`, `append`, `pop` | O(h) space | it is not smaller than the call stack, only under your control |
| The queue during a BFS | `deque`, `append`, `popleft` | O(w) space, up to about n/2 on a complete tree | `list.pop(0)` is O(n) per pop: use `popleft` |
| Search a plain binary tree for a value | any traversal | O(n) | no order to exploit |
| Search or insert in a BST | step left or right from the root | O(h) | O(log n) only if balanced; O(n) on a skewed BST |
| Slice the traversal lists at every call | `preorder[1:k]` | O(n) per slice, O(n²) in total | pass index ranges instead |
| Call a helper that walks the whole subtree, at every node | recompute a subtree's size at each node | O(n · h), O(n²) on a chain | return the value up the tree instead, one pass |

**The row people get wrong is the third.** "Recursion on a tree is O(log n) space" is true only for a balanced tree. The safe statement is **O(h)**, then say what h is for the input you were given.

## 0.5 The primitives

Four moves build almost every tree solution. Each has an invariant: the thing that is true every time it runs.

**1. The `None` base case.** The first line of every recursive tree function tests for `None` and returns the answer for an empty tree.

```python
def dfs(node):
    if node is None:          # the empty tree
        return ...
```

*Invariant:* below that line, `node` is a real node, so `node.val`, `node.left` and `node.right` are safe. You met this in [00-before-you-start.md](00-before-you-start.md#a-tiny-tree-by-hand), §A tiny tree, by hand. It must not be "am I a leaf?": a node with one child is not a leaf, so a leaf-only check recurses into both children, one call receives `None`, and reading `None.left` raises `AttributeError`. The empty tree crashes the same way.

**2. Return a value up.** A call returns one fact about its own subtree. The parent combines its children's facts with its own value. The number of nodes in a tree:

```python
def size(node):
    if node is None:
        return 0
    return 1 + size(node.left) + size(node.right)
```

*Invariant:* `size(x)` returns the answer for the subtree rooted at `x` and nothing else. This is `tree_sum` from module 00 with `1` in place of `node.val`. When the parent needs one thing and the problem asks for another, the answer goes on the side instead, as in `largest_subtree_sum`: see [00-before-you-start.md](00-before-you-start.md#returning-a-value-vs-updating-an-answer-on-the-side), §Returning a value vs updating an answer on the side.

**3. Pass a value down.** A parameter carries what the path from the root has gathered so far. [Path Sum](https://leetcode.com/problems/path-sum/) (LC 112) asks whether any root-to-leaf path adds up to a target:

```python
def has_path_sum(node, remaining):
    if node is None:
        return False
    remaining -= node.val
    if node.left is None and node.right is None:   # a leaf: the path ends here
        return remaining == 0
    return has_path_sum(node.left, remaining) or has_path_sum(node.right, remaining)
```

*Invariant:* `remaining` is the target minus the sum of the values from the root down to, and including, `node`. Each call gets its own copy, so the left branch can't spoil what the right branch sees. The leaf test here is part of the question, "root-to-leaf", and it sits *below* the `None` base case, not in place of it.

**4. The BFS frontier, one level at a time.** Start a queue with the root. Repeatedly take the oldest node from the front and append its children at the back.

*Invariant:* the queue never holds a node of depth d + 1 in front of one of depth d. So when you begin a new level, the queue holds **exactly one complete level**, left to right. Read its length then, before you take anything, and you know how many nodes belong to this level. Read it later and the count is wrong, because each node you take off appends its children at the back. §BFS shows it on a tree.

## 0.6 Inputs that break it

| Input | What breaks | Check |
|---|---|---|
| The empty tree, `root = None` | code that reads `root.val` before testing; BFS that starts `deque([root])` and then reads `None.left` | does the function return the right answer for `None`? |
| A single node | code that assumes a child exists | trace it: both children are `None` |
| A node with exactly one child | a base case of "am I a leaf?" recurses into the `None` side and crashes; a `None` base case that answers "path ends here" counts the missing side as a leaf | for root 1 with only a left child 2 and target 1, `has_path_sum` must return `False` |
| A chain of 10⁵ nodes, such as a BST built from sorted input | recursion passes the default limit of about 1,000 frames; "O(log n) space" is wrong | say the depth out loud; offer an explicit stack |
| A complete tree | the BFS queue grows to about n/2 | state the space as O(w) |
| Negative values, zero, duplicates | "stop once the running sum passes the target" is wrong when later values are negative; a BST rule that assumed distinct values | ask whether values can be negative, and how a BST stores duplicates |
| A BST node that is right for its parent and wrong for its grandparent | checking each node only against its two children | root 5, left child 3, and 6 as the right child of 3: 6 > 3, yet 6 sits in 5's left subtree. Carry the allowed range down instead, or check that the in-order sequence is strictly increasing |

## 0.7 Complexity, out loud

Say these as sentences, with the reason:

- **Time:** *"O(n), because each node is visited once and does O(1) work."* If each node does more, multiply: a helper that walks the subtree at every node is O(n · h).
- **DFS space:** *"O(h) for the recursion stack, where h is the height. That's O(log n) if the tree is balanced and O(n) in the worst case, a chain."* Never say O(log n) without the word "balanced".
- **BFS space:** *"O(w) for the queue, where w is the widest level. On a complete tree the last level holds about half the nodes, so that's O(n) in the worst case."*
- **Output space:** a returned list of all n values is O(n) on its own. Say it separately from the stack or queue.
- **BST operations:** *"O(h): O(log n) on a balanced BST, O(n) on a skewed one."*

## 0.8 Signals

| In the statement | Reach for | Where |
|---|---|---|
| `TreeNode`, `root`, `left`, `right` | this module | all of it |
| height, size, "is it balanced", a value computed from both subtrees | post-order, return a value up | §0.5 primitive 2, §DFS |
| the answer can sit at any node, but the parent needs something else | return one thing, keep the answer on the side | module 00, §Returning a value vs updating an answer on the side |
| root-to-leaf path, "along the path from the root" | pass a value down | §0.5 primitive 3 |
| level, row, "seen from one side", nearest, minimum depth | BFS one level at a time | §0.5 primitive 4, §BFS |
| BST, sorted, kth smallest, predecessor | in-order: a BST gives sorted order | §The three orders |
| "construct the tree from these traversals" | index ranges over the traversals | §A subtree is always a contiguous block |
| iterator, `next()`, "without recursion" | an explicit stack | §The same three, iteratively |
| up to 10⁵ nodes, with no promise of balance | say the recursion depth out loud; have the iterative version ready | §When to go iterative |

## 0.9 Self-check

Answer each in a sentence or two, without looking back. The answers are at the bottom of the module. Read the part behind any question you miss.

1. Why does a recursive tree function test `if node is None` at the top instead of "am I a leaf?" at the bottom? What happens on a node with exactly one child?
2. A recursive DFS runs on a tree of n nodes. What is its stack space, when is that O(log n), and when is it O(n)?
3. Draw the tree LeetCode writes as `[1,null,2,3]`. What is its height?
4. You insert the values 1, 2, …, n, in that order, into an empty BST. What is the tree's height, and what does a search cost?
5. In a BFS that handles one level at a time, what does the queue hold when a new level begins, and why must its length be read before you take any node off it?
6. Someone checks a BST by testing, at every node, that the left child is smaller and the right child is larger. Give a tree that passes this test and is not a BST.
7. At every node, a solution calls a helper that walks that node's whole subtree to count its size. What does that cost on a balanced tree and on a chain, and what is the fix?
8. Does an iterative DFS with an explicit stack use less memory than the recursive version? When is going iterative the right call?

---

## DFS vs BFS

There are exactly **two** ways to visit every node in a tree or graph. Everything else is a variation.

| | DFS — Depth-First Search | BFS — Breadth-First Search |
|---|---|---|
| Idea | Go as deep as possible down one path, then back up and try the next | Visit everything one step away, then everything two steps away |
| Structure | A **stack**, usually the call stack, i.e. recursion | A **queue**, the one from module 02 |
| Written as | Recursive function | `while queue:` loop |
| Order | Root, then all of the left subtree, then all of the right | Level by level, left to right |
| Use for | Subtree-dependent answers, paths, exhaustive exploration, cycles, topological sort | Levels, shortest path in an unweighted graph, "nearest" anything |

**The maze analogy.** DFS: walk down one corridor until you hit a dead end, back up, take the next corridor. BFS: take one step down every corridor, then a second step down every corridor — a ripple spreading outward.

**You've already seen a DFS.** `tree_sum` in module 00 handles a node and recurses into both children: that is DFS. This module gives the tool its name, its three orders, and its iterative form.

---

## DFS

### The shape — memorise this

```python
def dfs(node):
    if not node:          # base case FIRST, guards against None
        return
    # ... do something with node.val ...
    dfs(node.left)
    dfs(node.right)
```

The base case is **"am I None?"** at the top. It is *not* "am I a leaf?" at the bottom. Two reasons: a leaf-check version drops the leaf's own value, and it crashes the moment a node has one child, because you recurse into the `None` one. See [bug-checklist.md](../reference/bug-checklist.md#wrong-base-case-shape), §Wrong base-case shape.

### The three orders

Same traversal, different placement of the work:

```python
def preorder(node):          # node BEFORE children
    if not node: return
    visit(node)
    preorder(node.left)
    preorder(node.right)

def inorder(node):           # node BETWEEN children
    if not node: return
    inorder(node.left)
    visit(node)              # on a BST this yields SORTED order
    inorder(node.right)

def postorder(node):         # node AFTER children
    if not node: return
    postorder(node.left)
    postorder(node.right)
    visit(node)              # use when a node's answer needs its children's answers
```

**Pick by dependency.** Height, diameter, "is this balanced", subtree sums — all need the children's answers before the node's, so all are post-order. In-order on a BST giving sorted output is a fact worth memorising outright; it's the basis of several problems.

#### The formula

Each order is one concatenation. `L` and `R` are the left and right subtrees:

```
pre(T)  =  [root]  +  pre(L)   +  pre(R)
in(T)   =  in(L)   +  [root]   +  in(R)
post(T) =  post(L) +  post(R)  +  [root]
```

`L` always comes before `R` in all three. **The only thing that moves is `[root]`.** That is the entire difference, and every property below falls out of it.

#### What each one guarantees

| | Where the root lands | Ancestor vs descendant | The property you lean on |
|---|---|---|---|
| **Pre** | **first** element, always | ancestor before descendant | you know the root before you've seen the subtree → **build top-down** |
| **In** | somewhere in the middle | no guarantee | everything left of the root is `L`, everything right is `R` → **it splits** |
| **Post** | **last** element, always | descendant before ancestor | you've seen the whole subtree before the root → **combine bottom-up** |

#### Where the work lands in the recursion

This is the split from [00-before-you-start.md](00-before-you-start.md#returning-a-value-vs-updating-an-answer-on-the-side), §Returning a value vs updating an answer on the side, plus the pass-down channel from §0.5, seen from the side of the three orders:

| Order | Work happens | So it can | Natural mechanism |
|---|---|---|---|
| Pre | on the way **down**, before recursing | hand context to the children | an extra **parameter** (pass-down) |
| In | **between** the two calls — `L` done, `R` not | remember the previous element | a **closure variable** (`prev`), an answer on the side |
| Post | on the way **up**, after both return | use both children's answers | the **return value** (return-up) |

That middle row is why in-order pairs with a `prev` variable so often: at the moment you `visit(node)`, the previously visited node is the in-order predecessor. LC 98 (validate a BST) and LC 530 (minimum absolute difference in a BST) both rest on that one observation.

#### A subtree is always a contiguous block

In every order, the nodes of any subtree occupy one unbroken run. Only the root's position inside that run changes:

```
tree:        1                 pre :  1 | 2 4 5 | 3 6 7
           /   \               in  :  4 2 5 | 1 | 6 3 7
          2     3              post:  4 5 2 | 6 7 3 | 1
         / \   / \
        4   5 6   7            (bars mark the L / root / R groups)
```

This is the fact that makes reconstruction by **index ranges** work, with no slicing and no membership tests — see LC 105 (construct a tree from pre-order and in-order).

#### Which pairs rebuild the tree

With distinct values:

| Pair | Unique tree? | Why |
|---|---|---|
| pre + in | ✅ always | pre names the root, in says where it splits |
| post + in | ✅ always | same, root read from the back |
| **pre + post** | ❌ **not when any node has exactly one child** | both name the root; neither says where it splits |

The smallest counterexample: `pre = [2, 1]`, `post = [1, 2]` describes both `2` with a left child `1` and `2` with a right child `1`. A node with exactly one child is invisible to pre and post together: move that child to the other side and neither list changes.

> **The rule: you need one order that identifies the root and one that locates the split.** In-order is the only one of the three that locates the split, so it must be in the pair.

**On a BST, pre-order alone is enough** — in-order is just `sorted(preorder)`, so it carries no new information.

#### Post-order is pre-order in a mirror

```
reverse(post(T))  ==  pre(mirror(T))
```

Reading post-order backwards gives root → right → left, which is pre-order on the tree with every left and right swapped. That identity **is** the reverse trick used by the iterative post-order below: run the easy pre-order loop with the children pushed the other way, then reverse the output.

### The same three, iteratively

Recursion already uses a stack — the call stack. Writing it iteratively means **managing that stack by hand**, with the list-as-stack from [02-stacks-queues.md](02-stacks-queues.md). Nothing else changes.

The thing that makes these three feel unequal: **pre-order is the only order whose work happens at first contact.** You visit a node the instant you touch it and never need it again. In-order and post-order both have to *come back* to a node after its children — and "come back" is what all the extra machinery below pays for.

#### Pre-order iteratively — pop *is* visit

```python
def preorder(root):                       # the easy one
    stack = [root] if root else []
    while stack:
        node = stack.pop()
        visit(node)
        if node.right: stack.append(node.right)   # RIGHT first —
        if node.left:  stack.append(node.left)    # a stack reverses
```

**Invariant: the stack holds exactly the subtrees you still owe, top = next one.** Since pre-order emits a node before either child, popping and visiting are the same event. Nothing is ever pushed back.

**Why right is pushed first:** a stack is LIFO, so the *last* push comes out *first*. Push right then left → left pops first → left subtree is fully drained before right is ever touched. Push them in the natural order and you get a mirrored traversal.

On the balanced tree `1..7`:

| pop / visit | push | stack after |
|---|---|---|
| 1 | 3, 2 | `[3, 2]` |
| 2 | 5, 4 | `[3, 5, 4]` |
| 4 | — | `[3, 5]` |
| 5 | — | `[3]` |
| 3 | 7, 6 | `[7, 6]` |
| 6 | — | `[7]` |
| 7 | — | `[]` |

Result `[1, 2, 4, 5, 3, 6, 7]`. Note `[3, 5, 4]` — the stack is a stack of *pending right siblings*, one per level. That is the O(h) bound.

#### In-order iteratively — the one worth memorising

```python
def inorder(root):
    stack, node = [], root
    while stack or node:
        while node:                       # 1. dive left, parking every node
            stack.append(node)
            node = node.left
        node = stack.pop()                # 2. deepest node with no unexplored left
        visit(node)
        node = node.right                 # 3. hand the right subtree to the loop
```

**Two pieces of state, and they mean different things:**

| | Holds | Meaning |
|---|---|---|
| `stack` | ancestors | *parked* — value not yet emitted, right subtree not yet explored |
| `node` | one subtree | *unexplored* — the loop's next job |

**The three phases per iteration:**

1. **Dive left**, parking each node you pass. You are deliberately deferring them: in-order says their value comes *after* their left subtree.
2. **Pop.** The top of the stack is the deepest parked node, and you only stop diving when `node` is `None` — so **the popped node's left subtree is fully emitted.** That is the invariant, and it is exactly what licenses `visit(node)` right there.
3. **Go right.** Its left is done and it is emitted; all that remains is its right subtree. Assign it to `node` and let the loop re-dive.

Trace, balanced `1..7` — watch `stack` and `node` move independently:

| step | action | stack after | `node` after | out |
|---|---|---|---|---|
| 1 | dive, park 1 | `[1]` | 2 | `[]` |
| 2 | dive, park 2 | `[1,2]` | 4 | `[]` |
| 3 | dive, park 4 | `[1,2,4]` | `None` | `[]` |
| 4 | pop+visit 4, go right | `[1,2]` | `None` | `[4]` |
| 5 | pop+visit 2, go right | `[1]` | 5 | `[4,2]` |
| 6 | dive, park 5 | `[1,5]` | `None` | `[4,2]` |
| 7 | pop+visit 5, go right | `[1]` | `None` | `[4,2,5]` |
| 8 | pop+visit 1, go right | **`[]`** | **3** | `[4,2,5,1]` |
| 9–14 | same again on the right half | | | `[4,2,5,1,6,3,7]` |

**Step 8 is why the condition is `while stack or node`.** The stack is empty and the traversal is barely half done — node `3` and everything under it is still owed. `while stack` alone is wrong twice over: the stack starts empty, so the loop never even enters and returns `[]` for every tree — and if you force the first entry, it still exits at step 8, truncating `1..7` to `[4, 2, 5, 1]`. On the tree `1` with children `2` and `3` that is `[2, 1]` instead of `[2, 1, 3]`.

> This is the template to memorise, because it is the only one that can be **paused**: freeze it between step 2 and step 3 and you have the `next()` of LC 173 (BST iterator).

#### Post-order iteratively — don't write it directly

```python
def postorder(root):
    stack, out = [root] if root else [], []
    while stack:
        node = stack.pop()
        out.append(node.val)              # this is node -> right -> left
        if node.left:  stack.append(node.left)     # LEFT first now —
        if node.right: stack.append(node.right)    # the pushes are swapped
    return out[::-1]                      # reversed = left -> right -> node
```

**It is the pre-order loop with two lines swapped.** Swap the two pushes and left/right come out the other way round, so the loop emits `node -> right -> left`. That is pre-order on the *mirrored* tree — the identity from §Post-order is pre-order in a mirror, above. Reverse it and `node, right, left` becomes `left, right, node`, which is post-order.

On `1..7` the loop produces `[1, 3, 7, 6, 2, 5, 4]`; reversed, `[4, 5, 2, 6, 7, 3, 1]`. ✅

**What the trick costs you:** nothing is in post-order until the loop ends, so you cannot stream results and you hold all `n` values in `out`. Fine for "return the traversal", useless the moment you need to stop early or emit as you go.

**The loop does not visit in post-order — it visits in *reverse* post-order and then reverses a list.** Reversing a list cannot un-fire a side effect, so you never put the work in that loop. **Split it in two:**

```python
def postorder_work(root):
    stack, out = [root] if root else [], []
    while stack:                              # loop 1 — build the ORDER only
        node = stack.pop()
        out.append(node)                      # the NODE, not node.val
        if node.left:  stack.append(node.left)
        if node.right: stack.append(node.right)

    for node in reversed(out):                # loop 2 — the real post-order visit
        visit(node)                           # children are already done
```

`reversed(out)` is the genuine post-order sequence, node for node. So `visit` in loop 2 can be anything recursion could do: print, mutate shared state, or combine children, because both children were visited earlier in the same loop.

The bottom-up computations become a dict lookup instead of a return value. The size of every subtree:

```python
size = {None: 0}
for node in reversed(out):
    size[node] = 1 + size[node.left] + size[node.right]   # children already in size
```

Any bottom-up value fits the same loop: whatever the recursive version would return becomes a dict entry, read by the parent.

**What you give up:**

| | |
|---|---|
| **Combining inside loop 1** | ❌ impossible — when you pop a node there, neither child has been touched |
| **Space** | `n` node references, not O(h). Same as holding `n` values, but recursion held O(h) |
| **Early exit** | ⚠️ worthless — you can `break` out of loop 2, but loop 1 already walked all `n` nodes |
| **Pause / resume** | ❌ the one real casualty — an iterator's `next()` (LC 173) needs a little work per call, and loop 1 is O(n) up front |

> If the work genuinely has to happen at the moment of the post-order visit, the reverse trick is out and you need the `last_visited` version below.

**The direct version needs a second pointer.** Post-order arrives at each node **twice** — once coming from the left subtree, once from the right — and the node must know which. So you either push `(node, visited_flag)` pairs, or keep a `last_visited` pointer and *peek* rather than pop:

```python
# sketch — know it exists, don't memorise it
node = stack[-1]                          # peek
if node.right and last_visited is not node.right:
    ...descend right...                   # second arrival still pending
else:
    visit(stack.pop()); last_visited = node
```

Know the reverse trick cold; mention the flag version exists if the interviewer pushes.

### When to go iterative

| Reason | Real? |
|---|---|
| The interviewer said *"now without recursion"* | ✅ the usual reason |
| You must **pause** mid-traversal (BST iterator, LC 173) | ✅ recursion can't be paused and resumed |
| The depth can pass the default limit of about 1,000 frames (a chain-shaped tree of 10⁵ nodes) | ✅ see [00-before-you-start.md](00-before-you-start.md#stack-depth), §Stack depth |
| "It saves space" | ❌ **no** — your stack holds the same O(h) nodes the call stack did |

That last row is the one people get wrong. Iterative is not an optimisation. It is a **control** choice: you go iterative when you need to stop, inspect, or resume the traversal, or when the frames won't fit.

> **The tell for LC 173:** `next()` must return one value and come back later. A recursive in-order runs to completion or not at all. The moment a problem needs the traversal *suspended*, the stack has to be yours.

### Returning a value up the tree

Almost every tree problem has one of the two shapes from [00-before-you-start.md](00-before-you-start.md#returning-a-value-vs-updating-an-answer-on-the-side), §Returning a value vs updating an answer on the side:

- **Return a value.** `tree_sum` and `size` (§0.5) return the answer for their own subtree, and the root's return value is the answer.
- **Update an answer on the side.** `largest_subtree_sum` returns what the parent needs, a sum, and keeps the answer, a maximum, in a variable outside the recursion.

Either way, the method is the same: **define in one sentence what a call returns to its parent, then trust the recursion** for the two children. Write that sentence down before the code. If you can't, you don't know yet which shape the problem is.

---

## BFS

### The shape — memorise this

The queue is the one from [02-stacks-queues.md](02-stacks-queues.md#the-queue-first-in-first-out), §The queue: first in, first out: `append` adds at the back, `popleft` takes from the front, both O(1).

```python
from collections import deque

def bfs(root):
    if not root:
        return []

    queue = deque([root])
    while queue:
        node = queue.popleft()
        # ... do something with node.val ...
        if node.left:
            queue.append(node.left)
        if node.right:
            queue.append(node.right)
```

`while queue:` stops when the queue is empty, because an empty `deque` is falsy: see [python-toolkit.md](../reference/python-toolkit.md#python-truthiness-why-while-queue-works), §Python truthiness: why `while queue:` works.

### Level order — the one trick worth knowing

The template above serves nodes in level order, but it can't tell where one level ends and the next begins. To handle the tree **one level at a time**, add an inner loop:

- At the start of each pass of the outer loop, **read how many nodes the queue holds.** That count is the size of the current level.
- Take exactly that many nodes off the front, appending each one's children at the back.
- When the inner loop ends, the current level is consumed, and what's left in the queue is precisely the next level.

**Why the count works.** At the top of each outer iteration, everything sitting in the queue is *exactly one complete level* — because a node's children are only ever added after that node is removed, and they go in behind every node already waiting. That is the invariant from §0.5, primitive 4.

You must read the count **before** the inner loop. Reading `len(queue)` inside it would see the queue grow as you push children.

**Trace on `[1,2,3,4,null,null,5]`** (the second tree in §0.2):

| Queue at top | Count | Taken off | Appended |
|---|---|---|---|
| `[1]` | 1 | 1 | 2, 3 |
| `[2, 3]` | 2 | 2, then 3 | 4 (from 2), then 5 (from 3) |
| `[4, 5]` | 2 | 4, 5 | — |
| `[]` | — | loop ends | |

Each row is one level: `1`, then `2 3`, then `4 5`. Notice that 4 and 5 have different parents and still arrive together, because the inner loop runs across the whole level, not one parent at a time.

Every line in this loop belongs to exactly one scope: once per level, or once per node. Putting a line in the wrong one is the classic bug here: see [bug-checklist.md](../reference/bug-checklist.md#once-per-node-or-once-per-level), §Once per node or once per level.

Complexity, both traversals: **O(n) time**, every node touched once. **Space: O(w) for BFS**, the widest level, up to about n/2 on a complete tree. **O(h) for DFS**, the height, up to n on a chain.

### Level order via DFS

Level order is also reachable with DFS. Pass the depth down as a parameter, the pass-down channel from §0.5, and use it to decide which level a value belongs to. Pre-order visits each level's nodes left to right, so within a level the order comes out right. Also O(n).

**Knowing both and being able to say why you'd choose one is a strong interview signal** — BFS if you might exit early at a given level, DFS if the recursion is more natural or the tree is very wide.

---

## Seeing the difference: the same tree, both ways

The clearest demonstration that **the frontier's discipline is the algorithm**. Identical code, one method name changed: first in, first out against last in, first out, the two disciplines from module 02.

```
            1
          /   \
         2     3
        / \   / \
       4   5 6   7
```

### FIFO — `popleft()`, oldest first

| Frontier | Serve | Add | Depth served |
|---|---|---|---|
| `[1]` | 1 | 2, 3 | 0 |
| `[2, 3]` | 2 | 4, 5 | 1 |
| `[3, 4, 5]` | 3 | 6, 7 | 1 |
| `[4, 5, 6, 7]` | 4 | — | 2 |
| `[5, 6, 7]` | 5 | — | 2 |
| `[6, 7]` | 6 | — | 2 |
| `[7]` | 7 | — | 2 |

**Order: 1, 2, 3, 4, 5, 6, 7.** Depths: 0, 1, 1, 2, 2, 2, 2 — **never decreases**.

Look at step 2: node 2 is served and its children 4, 5 are appended *behind* node 3. They wait, because 3 arrived first. **That waiting is what keeps the traversal flat.**

### LIFO — `pop()`, newest first

| Frontier | Serve | Add | Depth served |
|---|---|---|---|
| `[1]` | 1 | 2, 3 | 0 |
| `[2, 3]` | **3** | 6, 7 | 1 |
| `[2, 6, 7]` | 7 | — | 2 |
| `[2, 6]` | 6 | — | 2 |
| `[2]` | 2 | 4, 5 | 1 |
| `[4, 5]` | 5 | — | 2 |
| `[4]` | 4 | — | 2 |

**Order: 1, 3, 7, 6, 2, 5, 4.** Depths: 0, 1, 2, 2, 1, 2, 2 — **bounces up and down**.

Node 2 sat untouched for four steps while the entire right subtree was explored. It was the *oldest* item, and LIFO always ignores the oldest.

### Push order matters only for stacks

A stack **reverses**; a queue **preserves**. So in an iterative DFS, the child you push *second* is visited *first*. To get conventional pre-order (`1, 2, 4, 5, 3, 6, 7`) you must push **right first, then left**. The table above pushes left-then-right, which is why it comes out right-heavy.

Recursive DFS has no such inversion — `dfs(node.left)` before `dfs(node.right)` genuinely goes left first, because the call fires immediately instead of being parked on a stack you manage by hand.

---

## Discover vs. visit

Two distinct moments in every traversal, worth separating in your head:

| Moment | Code | Meaning |
|---|---|---|
| **Discover** | `queue.append(child)` | "I now know this node exists." Not yet examined. |
| **Visit / process** | `node = queue.popleft()` | "I'm handling this node now" — read `.val`, discover its children. |

**The node you remove is the node you explore.** A node lives in the frontier precisely during the gap between being discovered and being visited. The frontier *is* the set of nodes in that in-between state.

In the FIFO table: node 4 was discovered at step 2 and visited at step 4. It waited two rounds in the frontier.

> ⚠️ **You'll see this again in module 08, on graphs.** In a *graph* (unlike a tree) several nodes can discover the same neighbour, so you must mark a node as seen when you **push** it, not when you pop it — otherwise it enters the frontier multiple times. Trees don't have this problem because every node has exactly one parent. In graph BFS this is the single most common bug.

---

## Common tree mistakes

| Mistake | What you see | Entry |
|---|---|---|
| Base case "am I a leaf?" instead of "am I `None`?" | `AttributeError` on a node with one child, or on the empty tree | [bug-checklist.md](../reference/bug-checklist.md#wrong-base-case-shape), §Wrong base-case shape |
| Calling the recursive method without `self.` inside `class Solution` | `NameError` | [bug-checklist.md](../reference/bug-checklist.md#missing-self-on-a-recursive-method-call), §Missing `self.` on a recursive method call |
| Computing the recursive result and not returning it | `None` comes back from the root | [bug-checklist.md](../reference/bug-checklist.md#missing-return), §Missing `return` |
| Returning a node where a value is expected, or the reverse | a list of `TreeNode` objects, or `int` has no attribute `left` | [bug-checklist.md](../reference/bug-checklist.md#node-vs-value-vs-next), §Node vs value vs `.next` |
| Rebinding an outer variable from a nested helper without `nonlocal` | `UnboundLocalError` | [bug-checklist.md](../reference/bug-checklist.md#assignment-makes-a-name-local-for-the-whole-function), §Assignment makes a name local for the whole function |
| In a level-at-a-time BFS, a line in the wrong loop | each node handled several times, or every input returns `[]` | [bug-checklist.md](../reference/bug-checklist.md#once-per-node-or-once-per-level), §Once per node or once per level |
| `list.pop(0)` as the queue | correct output, O(n²) time | [python-toolkit.md](../reference/python-toolkit.md#1-deque-the-queue), §1. `deque`: the queue |
| `while stack:` in the iterative in-order | `[]`, or only the left half of the tree | §In-order iteratively, above |
| Checking a BST node only against its two children | accepts trees that are not BSTs | §0.6, last row |
| "O(log n) space" for a recursion on a tree with no balance promise | a wrong complexity claim | §0.7 |

---

## Drill set — cold, no IDE, no running

| # | Problem | Focus |
|---|---|---|
| 1 | [Maximum Depth of Binary Tree](https://leetcode.com/problems/maximum-depth-of-binary-tree/) (LC 104) | Simplest recursion. Write it **both** ways |
| 2 | [Invert Binary Tree](https://leetcode.com/problems/invert-binary-tree/) (LC 226) | Recursion muscle memory |
| 3 | [Binary Tree Level Order Traversal](https://leetcode.com/problems/binary-tree-level-order-traversal/) (LC 102) | From scratch, no notes. ⚑ **Checkpoint** |
| 4 | [Binary Tree Right Side View](https://leetcode.com/problems/binary-tree-right-side-view/) (LC 199) | BFS variation — proves you own it |
| 5 | [Binary Tree Zigzag Level Order Traversal](https://leetcode.com/problems/binary-tree-zigzag-level-order-traversal/) (LC 103) | Second variation |
| 6 | [Diameter of Binary Tree](https://leetcode.com/problems/diameter-of-binary-tree/) (LC 543) | Post-order: return one thing, track another |

**⚑ Checkpoint:** if the level order traversal in row 3 doesn't come out clean and compiling without notes, stop there. Reread §BFS and §0.5, primitive 4, and don't push on to row 4 until it does.

## Before you submit anything

Run [bug-checklist.md](../reference/bug-checklist.md#the-30-second-pass), §The 30-second pass, over your code. Thirty seconds.

---

## Self-check answers

1. A leaf-only check recurses into both children of a node that has one, so one call receives `None`, which is not a leaf either, and reading `None.left` raises `AttributeError`. The empty tree crashes the same way. Testing `None` at the top handles both: below that line, `node` is always a real node.
2. **O(h)**, where h is the height, because only one root-to-node path of frames is alive at a time. It is O(log n) when the tree is balanced and O(n) when the tree is a chain, such as a BST built from sorted input. A chain of 10⁵ nodes passes the default limit of about 1,000 frames.
3. Root `1` has no left child (`null`) and a right child `2`. The children of `2` are `3` on the left and nothing on the right (the trailing `null` is omitted). So 1 → right 2 → left 3, a chain of three nodes: **height 2** in edges, or a "maximum depth" of 3 in LeetCode's node count.
4. Every value is larger than all before it, so each goes to the right of the last: the tree is a **chain, height n − 1**. A search may walk the whole chain, so it costs **O(n)**: BST operations are O(h), and h here is n − 1, not log n.
5. **Exactly one complete level**, left to right, because children are appended behind every node already waiting. Read the length first, because as you take nodes off you append their children, so `len(queue)` changes during the level.
6. Root 5, left child 3, and 6 as the right child of 3. Every parent-child pair passes, yet 6 sits in 5's left subtree and is larger than 5. The rule is about whole subtrees: pass the allowed range down, or check that an in-order traversal is strictly increasing.
7. Each call walks O(size of that subtree), and a node sits in the subtree of each of its ancestors, so the total is **O(n · h)**: about O(n log n) on a balanced tree and **O(n²)** on a chain. The fix is to return the size up the tree, `1 + left size + right size`, so one pass computes every node's size in **O(n)**.
8. **No.** The explicit stack holds the same O(h) nodes the call stack did. Go iterative when the interviewer asks for no recursion, when you must pause the traversal (an iterator's `next()`), or when the depth can pass the default recursion limit.
