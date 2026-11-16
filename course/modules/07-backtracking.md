# Module 07: Backtracking

<!-- toc -->
**Contents**

- [0.1 Prerequisites and the one question](#01-prerequisites-and-the-one-question)
- [0.2 The structure and how it works](#02-the-structure-and-how-it-works)
  - [A tree that exists: is there a clean path to a leaf?](#a-tree-that-exists-is-there-a-clean-path-to-a-leaf)
  - [Now return the path itself](#now-return-the-path-itself)
  - [The three moves](#the-three-moves)
  - [Trace it: what is in `path` at each instant](#trace-it-what-is-in-path-at-each-instant)
  - [The contract](#the-contract)
  - [Why there is no visited set](#why-there-is-no-visited-set)
  - [A generated tree: where 2ⁿ comes from](#a-generated-tree-where-2ⁿ-comes-from)
  - [Only one path exists at a time](#only-one-path-exists-at-a-time)
  - [What tree am I walking?](#what-tree-am-i-walking)
- [0.3 Vocabulary](#03-vocabulary)
- [0.4 Operations and their cost](#04-operations-and-their-cost)
- [0.5 The primitives](#05-the-primitives)
- [0.6 Inputs that break it](#06-inputs-that-break-it)
- [0.7 Complexity, out loud](#07-complexity-out-loud)
- [0.8 Signals](#08-signals)
- [0.9 Self-check](#09-self-check)
- [The three patterns](#the-three-patterns)
  - [Subsets](#subsets)
  - [Combinations: choose exactly k](#combinations-choose-exactly-k)
  - [Orderings: every arrangement](#orderings-every-arrangement)
  - [Which one is it?](#which-one-is-it)
- [The choice loop](#the-choice-loop)
  - [The index is two switches](#the-index-is-two-switches)
  - [Slots with their own choices](#slots-with-their-own-choices)
  - [Worked: Combination Sum III (LC 216)](#worked-combination-sum-iii-lc-216)
  - [Duplicates in the input](#duplicates-in-the-input)
  - [The copy](#the-copy)
- [The per-path mark](#the-per-path-mark)
  - [`used`: the mark for orderings](#used-the-mark-for-orderings)
  - [Grids: a tree of moves](#grids-a-tree-of-moves)
  - [Count the changes, count the restores](#count-the-changes-count-the-restores)
  - [Every exit un-marks](#every-exit-un-marks)
  - [Overwriting the input instead of keeping a set](#overwriting-the-input-instead-of-keeping-a-set)
  - [Why it has to be recursion](#why-it-has-to-be-recursion)
- [The return rule: collect all, or find one?](#the-return-rule-collect-all-or-find-one)
- [Pruning](#pruning)
  - [Only on a monotone constraint](#only-on-a-monotone-constraint)
  - [Sorting turns `continue` into `break`](#sorting-turns-continue-into-break)
  - [Depth versus width](#depth-versus-width)
  - [Rank a prune before writing it](#rank-a-prune-before-writing-it)
  - [A set on the output is the receipt for a prune you didn't do](#a-set-on-the-output-is-the-receipt-for-a-prune-you-didnt-do)
- [Complexity of an exponential tree](#complexity-of-an-exponential-tree)
- [Every template, in one place](#every-template-in-one-place)
- [How to attack a backtracking problem](#how-to-attack-a-backtracking-problem)
- [In depth](#in-depth)
  - [Why the mark has to come off: two counterexamples](#why-the-mark-has-to-come-off-two-counterexamples)
  - [`start`: one parameter, three jobs](#start-one-parameter-three-jobs)
  - [The aliasing bug, traced to the end](#the-aliasing-bug-traced-to-the-end)
  - [The version with no undo, and its price](#the-version-with-no-undo-and-its-price)
  - [What the tree picture shows, and what it hides](#what-the-tree-picture-shows-and-what-it-hides)
  - [Why not just dedup at the end?](#why-not-just-dedup-at-the-end)
  - [When it stops being backtracking](#when-it-stops-being-backtracking)
  - [The tree is never built](#the-tree-is-never-built)
- [Common backtracking mistakes](#common-backtracking-mistakes)
- [Drill set — cold, no IDE, no running](#drill-set--cold-no-ide-no-running)
- [Not covered here](#not-covered-here)
- [Before you submit anything](#before-you-submit-anything)
- [Self-check answers](#self-check-answers)
<!-- /toc -->

This module covers backtracking. It is the tree DFS of module 06, walked over a tree that nobody hands you: the tree is **generated** by your choices, one level per decision. Every solution is three moves at each node: **choose** a next step, **explore** everything below it, **undo** the step on the way back up. You'll learn the three shapes almost every "generate all" problem takes, the one line that changes between problems, when something besides the path needs undoing, and how to state the cost of a search that is exponential on purpose.

**How to use it.** Read §0, then answer the self-check in §0.9 and re-read the parts of §0 behind any question you miss. Then work through the three patterns, the choice loop and the per-path mark, and do the drill set cold.

| Section | What it gives you |
|---|---|
| §0, the foundation | backtracking on a tree that exists, then on one you generate; the vocabulary, what each operation costs, the four primitives, the inputs that break it, the signals |
| The three patterns | subsets, combinations, orderings: the tree, the template, and what every line means for the tree |
| The choice loop | the only line that changes between problems, a worked example, duplicates, the copy |
| The per-path mark | what to do when the path is not the only thing you change, grids included |
| The return rule | collect every answer, or stop at the first one |
| Pruning | which prunes are safe, and which ones change the complexity |
| Complexity of an exponential tree | leaves times cost per leaf, and the space that stays small |
| Every template, in one place | one algorithm and eight deltas |
| How to attack a backtracking problem | the steps, in order |
| In depth | the derivations and counterexamples behind the rules |
| Common backtracking mistakes | the bugs, each linked to its entry |
| Drill set | the problems, with the checkpoints |
| Before you submit anything | the checklist |

---

## 0.1 Prerequisites and the one question

| You need | From | Used here for |
|---|---|---|
| Recursion: the base case, trusting the recursive call | [00-before-you-start.md](00-before-you-start.md#recursion-and-the-call-stack), §Recursion and the call stack | every function in this module |
| Returning a value vs updating an answer on the side | [00-before-you-start.md](00-before-you-start.md#returning-a-value-vs-updating-an-answer-on-the-side), §Returning a value vs updating an answer on the side | `res` is the answer kept on the side; a search that returns a bool is the other shape |
| Stack space is the deepest the stack gets, and the default limit of about 1,000 frames | [00-before-you-start.md](00-before-you-start.md#stack-depth), §Stack depth | why an exponential search still uses O(depth) space |
| Reading the constraints: a tiny bound permits an exponential algorithm | [00-before-you-start.md](00-before-you-start.md#reading-the-constraints), §Reading the constraints | the strongest signal in §0.8 |
| Tree DFS: the `None` base case, then recurse into each child | [06-trees.md](06-trees.md#the-shape--memorise-this), §DFS, The shape — memorise this | §0.2 starts from it |
| Passing a value down: each call gets its own copy of a parameter | [06-trees.md](06-trees.md#05-the-primitives), §0.5 The primitives, primitive 3 | `start` and `remaining` |
| In a tree every node except the root has exactly one parent | [06-trees.md](06-trees.md#02-the-structure-and-how-it-works), §0.2 The structure and how it works | why a tree search needs no visited set, and why a grid does |
| Sorting costs O(n log n) and puts equal values next to each other | [01-arrays-hashing.md](01-arrays-hashing.md#sorting-as-a-tool), §Sorting as a tool | skipping duplicate choices; turning `continue` into `break` |
| A monotone predicate: once true, it stays true | [04-binary-search.md](04-binary-search.md#03-vocabulary), §0.3 Vocabulary | which prunes are safe |
| `continue` vs `break` inside a choice loop | [python-toolkit.md](../reference/python-toolkit.md#loop-control-continue-break-pass-return), §Loop control: `continue`, `break`, `pass`, `return` | §Pruning |
| `lst[:]` makes a new list | [python-toolkit.md](../reference/python-toolkit.md#lst-the-copy-idiom-and-the-bug-it-exists-to-prevent), §`lst[:]`: the copy idiom, and the bug it exists to prevent | recording an answer |

**Backtracking is tree DFS on a tree you generate.** In module 06 the tree was handed to you: a node's children were `node.left` and `node.right`. Here a node is a partial answer, such as the items chosen so far, and its children are the legal next choices. You never build that tree. You walk it with one list, `path`, that holds the choices from the root down to where you stand, and you take each choice back off on the way up so the next sibling starts clean.

**The one question this module answers:**

> *What is a node, what are its children, when is a node a complete answer, and what do I change on the way down that I must change back on the way up?*

Answer those four and the code is written. The first three are the tree; the fourth is where the bugs are.

## 0.2 The structure and how it works

### A tree that exists: is there a clean path to a leaf?

Start with a tree you can hold, from module 06. **Given a binary tree, is there a path from the root to a leaf with no zero on it?**

```python
def can_reach_leaf(node):
    if node is None or node.val == 0:
        return False                         # this node is unusable: a dead end
    if node.left is None and node.right is None:
        return True                          # a leaf, reached legally
    if can_reach_leaf(node.left):            # try left
        return True
    if can_reach_leaf(node.right):           # left failed, try right
        return True
    return False                             # both failed
```

That is plain DFS from [06-trees.md](06-trees.md#the-shape--memorise-this), §DFS, The shape — memorise this. It explores, it hits dead ends, it tries the other child. Nothing is undone, because nothing was recorded.

Read the last five lines. They are not `return can_reach_leaf(node.left)`: a failed left subtree is one option eliminated, not the answer. §The return rule comes back to this.

### Now return the path itself

Same question, but leave the winning path in `path`. One list is added, and with it two lines:

```python
def leaf_path(node, path):
    if node is None or node.val == 0:
        return False

    path.append(node.val)                    # CHOOSE: I am standing on this node

    if node.left is None and node.right is None:
        return True                          # a leaf: path IS the answer, keep it
    if leaf_path(node.left, path):
        return True
    if leaf_path(node.right, path):
        return True

    path.pop()                               # UNDO: both children failed, step back
    return False
```

> **`append` on the way in, `pop` on the way out. That is backtracking.**

The only reason `can_reach_leaf` needed no undo is that it kept no memory of where it had been. **The moment you record the path, you become responsible for un-recording it.**

### The three moves

```python
path.append(x)        # "I choose x"          : take a step
path.pop()            # "I take x back"       : step back
res.append(path[:])   # "record where I am"   : photograph the trail
```

`leaf_path` uses the first two. It doesn't need the third because it returns one path instead of collecting many. Picture breadcrumbs on the floor: at every instant the trail is the route from the entrance to your feet. `res` is a photo album, and a photo doesn't change when you walk on.

### Trace it: what is in `path` at each instant

```
        4
       / \
      0   1
         / \
        3   2
       /
      0
```

| Step | Call | What happens | `path` after |
|---|---|---|---|
| 1 | `leaf_path(4)` | choose `4` | `[4]` |
| 2 | `leaf_path(0)` | `val == 0`, so `False`, nothing chosen | `[4]` |
| 3 | `leaf_path(1)` | choose `1` | `[4, 1]` |
| 4 | `leaf_path(3)` | choose `3` | `[4, 1, 3]` |
| 5 | `leaf_path(0)`, then `leaf_path(None)` | `3` is not a leaf: its children give `False`, `False` | `[4, 1, 3]` |
| 6 | back in `leaf_path(3)` | both children failed, so **undo** | `[4, 1]` |
| 7 | `leaf_path(2)` | choose `2`, a leaf, so `True` | `[4, 1, 2]` |
| 8 | unwinding | `True` all the way up, **no pops** | `[4, 1, 2]` |

**Read step 6.** The `3` branch failed and put `path` back exactly as it found it, so the `2` branch started clean. Without the undo the answer would be `[4, 1, 3, 2]`.

**Read step 8.** On success nothing pops, on purpose: the filled-in `path` is what the caller wanted.

```steps
title: leaf_path on the tree: path at each instant
- path=[] stack=[] | Nothing chosen yet. The top of the stack is on the right.
- path=[4] stack=[4] | `leaf_path(4)`: CHOOSE 4. It is not a leaf, so try the left child.
- path=[4] stack=[4, 0] | `leaf_path(0)`: `val == 0`, so `False`. Nothing was chosen, so nothing is undone.
- path=[4, 1] stack=[4, 1] | Left failed. `leaf_path(1)`: CHOOSE 1, then try its left child.
- path=[4, 1, 3] stack=[4, 1, 3] | `leaf_path(3)`: CHOOSE 3. It has a child, so it is not a leaf. Try the left child.
- path=[4, 1, 3] stack=[4, 1, 3, 0] | `leaf_path(0)` under 3: `False`. The right child is `None`: `False` too.
- path=[4, 1] stack=[4, 1] | Both children of 3 failed. UNDO: pop 3 and return `False`.
- path=[4, 1, 2] stack=[4, 1, 2] | Back in `leaf_path(1)`, try the right. `leaf_path(2)`: CHOOSE 2. A leaf, so `True`.
- path=[4, 1, 2] stack=[] | `True` all the way up, no pops. `path` is the answer.
```

### The contract

> **Every call leaves the world exactly as it found it.**

Say that before you write a line. It is what makes siblings independent. State it as two halves:

1. *"`path` holds ___ at this point."*
2. *"When this call returns, ___ is back to what it was."*

### Why there is no visited set

`leaf_path` is **O(n) time and O(h) space**: every node is visited at most once, and the only things that grow are the recursion stack and `path`, both bounded by the height.

It has no visited set, and that is not an oversight. **In a tree a node has exactly one parent** ([06-trees.md](06-trees.md#02-the-structure-and-how-it-works), §0.2 The structure and how it works), so you can never arrive at the same node twice, and there is nothing to guard against. Keep that sentence. The moment a choice can be reached by more than one route, as a grid cell can from four sides, a mark has to appear. §The per-path mark is about that mark.

### A generated tree: where 2ⁿ comes from

`leaf_path` was O(n). Every problem in this module is exponential, and the reason is one change: **the tree stops being handed to you.**

| | `leaf_path` | every subset of n items |
|---|---|---|
| The tree is | **given**: you hold `root` | **not given**: nothing is allocated |
| A node's children come from | a field, `node.left` | a rule: *"the legal next choices"* |
| Size | n nodes, so you add | n levels, so you multiply |
| Cost | O(n) | O(2ⁿ) |

**Count it out.** For the subsets of `[1, 2, 3]`, each element is independently in or out:

```
level 1:  is 1 in?   2 ways
level 2:  is 2 in?   2 ways        ->  2 x 2 x 2  =  2³  =  8
level 3:  is 3 in?   2 ways
```

> **n independent binary decisions, one per level, so the leaf count is 2ⁿ.** The tree has n *levels*, not n nodes, and levels multiply.

Change the branching factor and you get the other counts:

| Choices per level | Levels | Leaves | Problem shape |
|---|---|---|---|
| 2 (in or out) | n | **2ⁿ** | subsets |
| n, then n − 1, then n − 2, … | n | **n!** | orderings (permutations) |
| k options per slot | n slots | **kⁿ** | every string of length n over k symbols |

`leaf_path` walks a structure. These problems generate one, and the structure is exponentially bigger than the input that describes it.

### Only one path exists at a time

There is no tree object anywhere. **The tree exists in time, not in space:** a node is the moment a call is running, an edge is a call, and both are gone once traced. Standing at node `[1, 3]` while enumerating the subsets of `[1, 2, 3, 4]`:

| In memory | Not in memory |
|---|---|
| `path = [1, 3]`: one list | `[2]`: explored, gone |
| 3 stack frames: the root-to-here path | `[1, 4]`: a sibling, not created yet |
| `res`: the answers found so far | the rest of the 2⁴ = 16 nodes |

> **Exactly one root-to-node path exists at a time. That path is `path`, and it is also the call stack.** Same information, two representations.

That is why the answer is "O(2ⁿ) time but O(n) space", and why recording an answer needs a copy: the one `path` is about to be re-pointed at the next node. §The tree is never built has the long version.

### What tree am I walking?

Not *"what tree do I build"*: nothing is built. Describe it in three sentences, and the three sentences are the code.

| Blank | Fill it with | What it becomes in code |
|---|---|---|
| **A node is** ___ | *"`path` holds one ___"* | what you copy into `res` |
| **An edge is** ___ | *"from here the legal next choices are ___"* | the `for` loop and its guards |
| **A leaf is** ___ | *"a node is a complete answer when ___"* | the base case |

And a fourth question the tree has no column for:

> **What do I change that isn't `path`?**

`used`, `seen`, the board itself, a running count. Every one needs its own undo. That is §The per-path mark, and it is where most of the bugs are.

## 0.3 Vocabulary

| Word | Meaning |
|---|---|
| **backtracking** | DFS over a tree of choices, where each choice is made on the way down and taken back on the way up |
| **state space tree** | the tree of partial answers: the root is "nothing chosen", each edge is one choice. Never built, only walked |
| **path** | the list of choices from the root to the node you're standing on. One list for the whole run |
| **choose, explore, undo** | the three steps at every node: make a choice, recurse into it, take it back |
| **complete, leaf** | a node that is a full answer. In subsets every node is one; in orderings only the nodes at depth n are |
| **branching factor** | how many children a node has: 2 for in-or-out, n − d at depth d for orderings |
| **depth** | how many choices the path holds. Usually at most n; with reuse it can be larger |
| **start index** | `start`: the index of the first item this call is still allowed to choose. The left edge of a shrinking window |
| **per-path mark** | a flag that is on exactly while its item or cell is on the current path: on when the choice enters the path, off when it leaves |
| **prune** | not creating a child you can already tell leads to no answer |
| **monotone constraint** | one that, once violated along a path, stays violated as the path grows. Only these are safe to prune on |
| **duplicate siblings** | two children of the same node that hold equal values: their subtrees are identical |
| **output-sensitive** | a cost measured against the size of the answer, not only the size of the input |
| **generate and filter** | build every candidate, then throw away the invalid or repeated ones. Correct and usually exponentially wasteful |

## 0.4 Operations and their cost

**k** is the length of the current path. **n** is the number of items to choose from.

| Operation | Python | Big-O | Trap |
|---|---|---|---|
| Make a choice, take it back | `path.append(x)`, `path.pop()` | O(1) | `path.pop(0)` is O(k), and it takes back the wrong choice |
| Record the current path | `res.append(path[:])` | O(k) | without `[:]` you store the list itself, and every later `pop` edits the stored answer |
| A new path per child instead | `dfs(..., path + [x])` | O(k) per call | correct, needs no undo, allocates a list on every edge (§The version with no undo, and its price) |
| Is this item already on the path? | `x in path` | O(k) | a `used` list indexed by position, or a set, is O(1) |
| The sum of the path so far | `sum(path)` | O(k) at every node | carry `remaining` as a parameter: O(1) |
| Take a cell off a set | `seen.remove(cell)`, `seen.discard(cell)` | O(1) | `remove` raises `KeyError` if the cell is not there |
| Sort the input once, before the search | `items.sort()` | O(n log n), once | it adds to the total, it doesn't multiply. `items = items.sort()` sets `items` to `None` |
| Remove repeated answers afterwards | `set(tuple(p) for p in res)` | O(total size of `res`) | every repeat was already generated; the waste happened before this line |
| Copy just to read | `len(path[:])`, `sum(path[:])` | O(k) for nothing | reading never needs a copy |
| Turn a path of characters into a string | `"".join(path)` | O(k) | do it at a leaf, not at every level |
| The call stack | one frame per choice on the path | O(depth) space | about 1,000 frames by default |

**The row people get wrong is the second.** The copy is O(k), so it multiplies the leaf count: recording 2ⁿ subsets costs O(n · 2ⁿ), not O(2ⁿ).

## 0.5 The primitives

Four moves build almost every backtracking solution. Each has an invariant: the thing that is true every time it runs.

**1. Choose, explore, undo.** The skeleton every template in this module fills in:

```python
def backtrack(state):
    if <complete>:
        res.append(<a copy>)
        return
    for choice in <legal choices>:
        make(choice)                         # CHOOSE
        backtrack(<state after choice>)      # EXPLORE
        unmake(choice)                       # UNDO: same indentation as the choose
```

*Invariant:* `path` holds the choices from the root to here, and when this call returns, every structure it touched is back to what it was on entry. The undo sits at the same indentation as the choose, so each loop iteration starts from the state the call was entered with.

**2. Record a copy.** `res.append(path[:])`, never `res.append(path)`.

*Invariant:* each entry of `res` is its own list, which no later `append` or `pop` can reach. There is one `path` for the whole run, so a stored reference to it would change with every later move. Without the copy, `res` ends with the right number of entries, every one `[]`: they are all the same `path` list, and every `append` was matched by a `pop`. Nothing crashes, because storing a reference is legal; the bug is silent. The test at every `append` into `res`: *does this list keep changing after I store it?* If yes, copy. See [python-toolkit.md](../reference/python-toolkit.md#lst-the-copy-idiom-and-the-bug-it-exists-to-prevent), §`lst[:]`: the copy idiom, and the bug it exists to prevent.

**3. The start index.** A selection problem passes `start`, loops `for i in range(start, n)`, and recurses on `i + 1`.

*Invariant:* every item on the path sits at an index below `start`, in increasing order, and this call may only choose from the window `[start, n)`. That one parameter forbids reordering (you can only go right), forbids reuse (because of the `+ 1`), and ends the recursion: once the window is empty the `for` runs zero times. Recursing on `i` instead of `i + 1` allows reuse and still forbids reordering. Deleting `start` allows both, and every answer comes out in every order.

**4. The per-path mark.** When something besides `path` records what is chosen, such as `used[i]` or a set of cells, set it with the choice and clear it with the undo.

*Invariant:* the mark is on exactly while its item is on the current path. Every exit from the call that runs after the mark is set must clear it first. Count the changes before the recursive call and the restores after it: the two numbers must match. §The per-path mark has the details.

## 0.6 Inputs that break it

| Input | What breaks | Check |
|---|---|---|
| Empty input | subsets must return `[[]]`, one empty answer, not `[]` | the root is a node, and it is an answer |
| `k = 0` | choosing k items must return `[[]]` | the base case fires at the root |
| One item | a loop or base case written for two or more | trace it: one answer or two? |
| Duplicates in the input, such as `[3, 3, 7]` | the same answer produced twice, from two equal items | sort, then skip a child equal to the sibling before it (§Duplicates in the input) |
| Negative values | a prune of the form "stop once the sum passes the target" deletes real answers, because a later negative can bring the sum back | ask whether values can be negative. Prune only on a monotone constraint |
| A zero when reuse is allowed | recursing on `i` with a value of 0 never shrinks `remaining`, so the recursion never ends | reuse terminates only because every value is positive |
| Reuse with a small value | the depth is not n: one candidate `2` and a target of 40 give a path of length 20 | depth = target ÷ smallest value |
| The branch that fails | state it changed and didn't restore poisons the next sibling | trace a failing branch, not the happy path: is every structure back to what it was? |
| n around 10⁵ | nothing works: 2^100000 is not a plan | this is not a backtracking problem |
| A one-row grid, `A B`, looking for `ABA` | without a mark the path walks back onto its own first cell and reports `True` | the answer is `False`: a cell on the path is not available again |

## 0.7 Complexity, out loud

Say these as sentences, with the reason:

- **Time:** *"O(\_\_) because the tree has \_\_ leaves and each one costs \_\_."* Subsets: *"O(n · 2ⁿ), because there are 2ⁿ subsets and each one is an O(n) copy."* The count alone, O(2ⁿ), leaves out the copy.
- **Space:** *"O(\_\_) because the only thing I allocate is \_\_, and it is bounded by the depth."* You stand on one root-to-node path at a time, so the auxiliary space is **O(depth)**: the stack plus `path`. The output is exponential; say it separately.
- **A cost before the search adds, a cost inside it multiplies.** One sort at the top makes it O(n log n + n · 2ⁿ), not O(n log n · 2ⁿ).
- **Depth is not always n.** With reuse it is target ÷ smallest value. Re-derive the numbers for each tree; don't carry them over from the last problem.
- **Optimality:** *"Any correct algorithm has to write down every answer, so the size of the output is a lower bound, and this matches it."*

## 0.8 Signals

| In the statement | Reach for | Where |
|---|---|---|
| "return all …", "generate all", "every possible" | backtracking: the strongest signal there is | this module |
| a return type that is a list of lists or a list of strings, with a combinatorial count | backtracking | this module |
| subsets, combinations, permutations named outright | one of the three patterns | §The three patterns |
| partitions, arrangements, "place n things so that no two conflict" | a pattern plus a legality test | §Every template, in one place |
| a path through a grid that may not use the same cell twice within one path | a per-path mark on a cell | §The per-path mark |
| `n ≤ 20`, `n ≤ 10`, a word of at most 15 letters | a tiny bound is permission to be exponential | [00-before-you-start.md](00-before-you-start.md#reading-the-constraints), §Reading the constraints |
| "may be chosen more than once", "unlimited" | recurse on `i`, not `i + 1` | §The index is two switches |
| the input may contain duplicates, and the answers must not | sort, then skip equal siblings | §Duplicates in the input |
| "return any one valid …", "does one exist" | backtracking that stops at the first success | §The return rule: collect all, or find one? |
| "how many ways", "the best", "the minimum" | probably not this: you need a number, not the candidates. A count lets every path that reaches the same state share one answer, which is memoisation; backtracking's state is the whole path, so nothing can be shared, and "return all" keeps every candidate, so nothing collapses. You'll see this again in module 09 | §When it stops being backtracking |
| a status that is the same whichever way you reach a cell, such as "which region is this cell in" | not this: one permanent mark, and a linear walk. You'll see this again in module 08 | §The per-path mark |
| n up to 10⁵ | not backtracking | §0.6 |

## 0.9 Self-check

Answer each in a sentence or two, without looking back. The answers are at the bottom of the module. Read the part behind any question you miss.

1. In `leaf_path`, the `pop` runs when both children fail and does not run when one succeeds. Why is each of those right?
2. You enumerate every subset of n distinct items. How many nodes does the tree have, what does the walk cost in time, and what does it cost in auxiliary space?
3. You write `res.append(path)` without a copy. What does the output look like, and why does nothing crash?
4. A selection loop runs `for i in range(start, n)` and recurses on `i + 1`. What does recursing on `i` instead allow? What does deleting `start` altogether allow?
5. Why does a prune that stops once the running sum passes the target delete real answers when the values can be negative?
6. A function marks a cell, loops over its neighbours with `if dfs(...): return True`, and ends with `return False`. How many exits run after the mark, and what must each one do?
7. Someone generates every subset of `[1] * 20` and then removes repeats with a set. How much work is that compared with the number of distinct answers?
8. A statement asks "how many ways" instead of "return all". Why is that a signal against backtracking?

---

## The three patterns

Almost every "generate all of something" problem is one of three trees. Learn the trees, and the templates differ by a line or two.

| | Subsets | Combinations | Orderings |
|---|---|---|---|
| Question | every sub-collection | every sub-collection **of size k** | every **arrangement** of all of them |
| Order matters | no | no | **yes** |
| Depth of the tree | 0 to n, varies | exactly k | exactly n |
| Answers | **2ⁿ** | **C(n, k)** | **n!** |
| The loop | `range(start, n)` | `range(start, n)` | `range(n)` plus `used` |
| The recursion | `dfs(i + 1)` | `dfs(i + 1)` | `dfs()`, no index |
| Record where | **every node** | where `len(path) == k` | where `len(path) == n` |

> **Subsets to combinations is one change: add a base case. Combinations to orderings is two: drop the index, add `used`.**

### Subsets

A set A is a subset of a set B if every element of A is in B. Every set is a subset of itself, and the empty set is a subset of everything, so `[]` and the whole input are both answers.

**The tree, for `[1, 2, 3]`.** Each node is a subset. A node's children extend it with **an element further right than anything already in it.**

```
                          []                        <- level 0
              +------------+------------+
             [1]          [2]          [3]          <- level 1
          +---+---+        |
       [1,2]   [1,3]    [2,3]                       <- level 2
          |
       [1,2,3]                                      <- level 3
```

8 nodes, 2³, and every one is an answer. There is no leaf test: a subset doesn't have to be finished to be valid.

```python
def all_subsets(items):
    res, path = [], []

    def dfs(start):
        res.append(path[:])                  # EVERY node is an answer
        for i in range(start, len(items)):   # my children
            path.append(items[i])            # CHOOSE: walk down the edge
            dfs(i + 1)                       # EXPLORE: that child's whole subtree
            path.pop()                       # UNDO: walk back up the edge

    dfs(0)
    return res
```

**What every line means for the tree.** This table is the same for all three patterns.

| Line | What it means for the tree |
|---|---|
| `def dfs(start)` | *"I am standing on a node. `start` is the leftmost child I am still allowed to take."* |
| `res.append(path[:])` | *"photograph this node."* `path` is the root-to-here route, so it is the node's contents |
| `for i in range(start, len(items))` | *"these, exactly these, are my children."* The loop is the edge set |
| `path.append(items[i])` | *"walk down the edge to child `i`"* |
| `dfs(i + 1)` | *"explore that child's entire subtree before I look at my next child."* This is what makes it depth-first |
| `path.pop()` | *"walk back up that edge."* I am on the parent again, ready for the next child |
| `i + 1` specifically | *"my children may only use elements to the right of `i`."* This is what stops `[2, 1]` from existing |
| `dfs(0)` | *"start at the root: nothing chosen, everything still allowed"* |

⚠️ **`i + 1` is the whole reason this is a subsets tree and not an orderings tree.** Pass `i` and items get reused; loop from `0` and they get reordered.

**Complexity:** 2ⁿ nodes, each doing an O(n) copy, so **O(n · 2ⁿ) time and O(n) auxiliary space.**

### Combinations: choose exactly k

The same tree as subsets, **cut off at depth k**. Only the nodes at exactly depth k are answers. Here is choosing 2 from `1 … 4`:

```
[]
├── [1]                  <- depth 1: not an answer, len != 2
│   ├── [1,2]  ✓
│   ├── [1,3]  ✓
│   └── [1,4]  ✓
├── [2]
│   ├── [2,3]  ✓
│   └── [2,4]  ✓
├── [3]
│   └── [3,4]  ✓
└── [4]                  <- dead: nothing to its right, so it can never reach depth 2
```

6 answers, C(4, 2). The structure is the subsets tree. **The only changes are which nodes count, and that the tree stops at depth k.**

```python
def choose_k(n, k):                      # every way to choose k numbers from 1..n
    res, path = [], []

    def dfs(start):
        if len(path) == k:               # a LEAF: depth k reached
            res.append(path[:])
            return                       # <- the return is not optional
        for i in range(start, n + 1):
            path.append(i)
            dfs(i + 1)
            path.pop()

    dfs(1)                               # 1..n, so the root's window starts at 1
    return res
```

| In the tree | In the code |
|---|---|
| only depth-k nodes are answers | `res.append` moves inside `if len(path) == k` |
| nothing below depth k exists | `return` ends the call, so the loop never runs |
| the root's window is `1 … n`, not `0 … n − 1` | `dfs(1)` and `range(start, n + 1)` |

⚠️ **A base case that doesn't `return` isn't a base case.** The loop runs anyway. On this shape the extra calls only waste time, because `len(path)` is already k and every child would be too long to record. On a shape that records at every node, they produce wrong answers.

**The prune worth knowing:** a node at depth d needs k − d more numbers. If fewer than that remain to its right, it is the `[4]` in the picture, dead on arrival. Looping over `range(start, n - (k - len(path)) + 2)` never creates it.

**Complexity:** **O(k · C(n, k)) time, O(k) auxiliary space.**

### Orderings: every arrangement

A permutation is an arrangement of **all** the elements, and order matters: `[1, 2, 3]` and `[3, 2, 1]` are different answers.

**The tree, for `[1, 2, 3]`:**

```
                              []
              +---------------+---------------+
             [1]             [2]             [3]        <- 3 children
          +---+---+       +---+---+       +---+---+
       [1,2]   [1,3]   [2,1]   [2,3]   [3,1]   [3,2]    <- 2 children each
          |       |       |       |       |       |
    [1,2,3] [1,3,2] [2,1,3] [2,3,1] [3,1,2] [3,2,1]     <- 1 child each. 3! = 6
```

Two things changed from the subsets tree, and they are the same change seen twice:

1. **The root's children are every element, not just the ones to the right.** So `[2, 1]` exists, and it is a different answer from `[1, 2]`.
2. **The branching factor shrinks 3, 2, 1**, not because of an index but because elements already on the path are unavailable.

```python
def all_orderings(items):
    res, path = [], []
    used = [False] * len(items)

    def dfs():
        if len(path) == len(items):      # a LEAF: all n placed
            res.append(path[:])
            return
        for i in range(len(items)):      # EVERY index, every time. No start
            if used[i]:
                continue                 # already on my path: not a child
            used[i] = True               # CHOOSE: two changes
            path.append(items[i])
            dfs()                        # EXPLORE
            path.pop()                   # UNDO: two restores
            used[i] = False

    dfs()
    return res
```

| In the tree | In the code |
|---|---|
| every element is available at every level | `range(len(items))`: the index parameter is gone |
| except the ones already on my path | `used`, and `if used[i]: continue` |
| the branching factor shrinks by 1 per level | that `continue` firing once more at each depth |
| leaves are at depth n | `if len(path) == len(items)` |

> **`used[i]` is True exactly while `items[i]` is on the path you are standing on.** That is the per-path mark. Subsets didn't need it, because the start index alone kept every path legal. Once you can reorder, the same item is reachable from every node above it, so something has to say which items are taken.

⚠️ **Two changes, two restores.** Forgetting `used[i] = False` gives **1 ordering instead of 6**, with no crash: the first completed path leaves every item marked, so no later node has a child. See §Count the changes, count the restores.

**Complexity:** n! leaves, each an O(n) copy, so **O(n · n!) time, O(n) auxiliary space.**

### Which one is it?

| The statement says | Pattern |
|---|---|
| "all subsets", "the power set", **"any number of"** | subsets |
| "**exactly k**", "choose k", "all pairs", "all triples" | combinations |
| "all permutations", "arrangements", "**order matters**", "rearrange" | orderings |
| "all combinations that sum to a target", "**may be reused**" | subsets, recursing on `i` (§The index is two switches) |
| "all …, and the input **has duplicates**" | that pattern plus the sibling skip (§Duplicates in the input) |

**It is a reading question, not a design question.** Name the pattern out loud, write its template, then apply the deltas below.

```compare
title: Which one is it?
option: Subsets
  Answer: every sub-collection
  Order matters: no
  Loop: `range(start, n)`
  Recurse: `dfs(i + 1)`
  Record where: every node
  Count: 2ⁿ
  Signal words: all subsets, power set, any number of
option: Combinations
  Answer: every sub-collection of size k
  Order matters: no
  Loop: `range(start, n)`
  Recurse: `dfs(i + 1)`
  Record where: `len(path) == k`, then return
  Count: C(n, k)
  Signal words: exactly k, choose k, all pairs
option: Orderings
  Answer: every arrangement of all items
  Order matters: yes
  Loop: `range(n)` plus `used`
  Recurse: `dfs()`, no index
  Record where: `len(path) == n`, then return
  Count: n!
  Signal words: permutations, order matters, rearrange
```

---

## The choice loop

The three patterns give you three trees. **Most other problems in the topic are one of them with the child-generating line edited.**

### The index is two switches

> **Having a `start` parameter forbids REORDERING. Adding `+ 1` to it forbids REUSE.**

| The loop | Reuse | Reorder | Pattern |
|---|---|---|---|
| `for i in range(start, n)`, then `dfs(i + 1)` | no | no | subsets, combinations |
| `for i in range(start, n)`, then `dfs(i)` | **yes** | no | a target sum with reuse |
| `for i in range(n)`, plus `used` | no | **yes** | orderings |
| `for i in range(n)`, no `used` | yes | yes | almost always a bug |

⚠️ **"I need to allow reuse" is answered by dropping the `+ 1`, never by dropping the parameter.** Deleting `start` flips both switches: you get reuse *and* every ordering of every answer, which then needs deduplicating. That is generate-and-filter at an exponential premium, for a one-character fix.

**`start` means something you can say:** *the index of the first element this call is still allowed to choose.* Every call gets a shrinking window, and `start` is its left edge.

> **The empty window is the base case.** There is no `if` to write: the `for` runs zero times. That is why the subsets template has no base case at all. A base case you design away beats one you handle. Delete `start`, though, and nothing shrinks: the recursion never ends and raises `RecursionError`.

§`start`: one parameter, three jobs has the long version.

### Slots with their own choices

Some problems have no single list to choose from. They have a fixed number of **slots**, and each slot has **its own** set of options: a combination lock whose first dial shows `0`–`2`, whose second shows `A` or `B`, whose third shows `w`, `x`, `y` or `z`.

The tree changes in two ways:

- **There is no `start` and no `used`.** The parameter is *which slot you are filling*. Each call fills one slot and recurses on the next.
- **The depth is fixed by the input** (one level per slot), and **the branching factor is read off the level**: a node at level d has as many children as slot d has options.

So the leaf count is the product of the per-slot counts: 3 × 2 × 4 = 24 settings for that lock. A leaf is the call where every slot is filled. Building the answer as a list of characters and joining it once at the leaf keeps each level O(1).

### Worked: Combination Sum III (LC 216)

[Combination Sum III](https://leetcode.com/problems/combination-sum-iii/) (LC 216): choose `k` different numbers from `1 … 9` that sum to `n`.

**Pattern:** combinations. **Deltas:** a second shrinking parameter, and a prune that reads it.

```python
def combination_sum_3(k, n):
    res, path = [], []

    def dfs(start, remaining):
        if len(path) == k:
            if remaining == 0:           # depth k reached: is it a valid leaf?
                res.append(path[:])
            return                       # k numbers used: a leaf either way
        for i in range(start, 10):
            if i > remaining:
                break                    # 1..9 is sorted, so every later i is worse
            path.append(i)
            dfs(i + 1, remaining - i)
            path.pop()

    dfs(1, n)
    return res
```

> **`remaining` is a second window, closing from the other side.** `start` bounds *which* numbers are still available; `remaining` bounds *how much* more can fit.

*Invariant:* `path` holds numbers in increasing order, all below `start`, and they sum to `n − remaining`. The `break` is safe because the numbers 1 to 9 come in increasing order and are all positive: once `i` is too big, every later `i` is too.

### Duplicates in the input

Duplicate answers have two different sources, and they need different fixes:

| The duplicate | Cause | Fix |
|---|---|---|
| `[1, 2]` and `[2, 1]`: the same set in a different order | **your traversal** | the start index (§The index is two switches) |
| `[3]` produced twice, once from each of two equal items | **your data** | **sort, then skip equal siblings** |

A problem with duplicate inputs needs both.

**The rule:** sort once, so equal values sit next to each other. Then, inside the choice loop, skip a child whose value equals that of the child immediately before it **at the same node**. In tree terms, two children of the same node holding the same value have identical subtrees: keep the leftmost and drop the rest.

**"At the same node" is the condition `i > start`, never `i > 0`.** `i > start` means `i − 1 ≥ start`, which means `items[i − 1]` is also a child of this node, a sibling. When `i == start`, `items[i − 1]` is not a sibling; it is the item the parent just chose, an ancestor on your path.

Take every subset of `[3, 3, 7]`. Index 1 gets two opposite verdicts:

| Where | `items[i − 1]` is | Verdict |
|---|---|---|
| `dfs(start=0)`, `i = 1` | a **sibling**, already tried at this node | **skip**: its subtree is a repeat of index 0's |
| `dfs(start=1)`, `i = 1` | an **ancestor**, on your path | **allow**: `[3, 3]` is a real answer |

⚠️ **`i > 0` treats both rows as "skip"** and silently deletes `[3, 3]` and `[3, 3, 7]`: 4 subsets instead of 6.

⚠️ **Without the sort the test means nothing.** Equal values aren't next to each other, so comparing with the neighbour can't see them. See [01-arrays-hashing.md](01-arrays-hashing.md#sorting-as-a-tool), §Sorting as a tool.

Orderings have the same problem and the same kind of fix: among equal values, allow one only if the equal copy just before it is already on the path. The clause is in §Every template, in one place, row 7. Both forms answer one question: *is the earlier equal copy on my path, or free?*

### The copy

`res.append(path[:])` is the most expensive one-line bug in the topic. Four lines show it:

```python
path = [1]; res = []
res.append(path)          # <- no copy
path.pop()
print(path, res)          # [] [[]]        <- the recorded answer changed
```

```python
path = [1]; res = []
res.append(path[:])       # <- a copy
path.pop()
print(path, res)          # [] [[1]]       <- the recorded answer survived
```

**`res.append(path)` stores a label, not a box.** `=` binds and never copies; `append` stores and never copies. Both names point at one list, so every later `append` and `pop` edits the "answer" too. The symptom is **the right number of answers, every one of them `[]`**, and nothing crashes. §The aliasing bug, traced to the end has the full trace.

The copy is unavoidable here because of §0.2: there is one `path`, re-pointed at each node in turn, so a photograph of a node has to be taken before the walk moves on.

| Line | Protects | Drop it and |
|---|---|---|
| `res.append(path[:])` | the answers **already recorded**, from future edits | every answer is `[]` |
| `path.pop()` | the **next sibling branch**, from this branch's choice | the trail only grows, and branches inherit each other's choices |

> **The copy looks backwards in time, the pop looks forwards.** You are recording a walk while still walking it, and neither line can do the other's job.

⚠️ **`[:]` is needed exactly where you store the list into something that outlives the next change.** Reading it, with `len`, `sum`, `max`, `sorted`, `tuple`, `in` or a loop, never needs a copy. `len(path[:])` is an O(k) allocation to answer an O(1) question. See [bug-checklist.md](../reference/bug-checklist.md#the-copy-reflex--where-only-a-read-was-needed), §The copy reflex: `[:]` where only a read was needed.

---

## The per-path mark

`path` is not always the only thing you change. When a second structure records what is chosen, it needs the same discipline as `path`:

> **The per-path mark is on exactly while its item is on the current path: it goes on when the choice enters the path and comes off when the choice leaves.**

It answers *"am I standing on this right now?"*, never *"have I ever been here?"*. A mark that stays on answers the second question, and you'll see this again in module 08 ([08-graphs.md](08-graphs.md)), where a mark that stays on is the graph's visited set.

### `used`: the mark for orderings

You met it in §Orderings: every arrangement. Orderings drop the start index, so something else must stop an item being chosen twice on one path. `used[i]` is True exactly while `items[i]` is on the current path. It goes on next to `path.append`, and comes off next to `path.pop`. Two changes, two restores.

### Grids: a tree of moves

A grid is not a tree, but a search through it is. Stand on a cell, and your choices are its four neighbours: up, down, left, right. That makes a tree of moves: the root is the start cell, each edge is one step, and a node is the path of cells walked so far.

A neighbour is a legal child when three tests pass, in this order:

1. **It is inside the grid.** Test the bounds first. `grid[-1][c]` doesn't raise; it reads the last row. See [bug-checklist.md](../reference/bug-checklist.md#a-negative-index-wraps-instead-of-crashing), §A negative index wraps instead of crashing.
2. **It passes the problem's own test for that cell**, such as holding the next letter you need.
3. **It is not already on the path.**

The third test is new. In `leaf_path`'s tree a node had one parent, so you could never arrive twice. A grid cell can be reached from up to four sides, and the first step back is always available: walk right, then walk left, and you're on the start cell again. So the per-path mark returns, on a cell. Put the cell in a set (or overwrite it on the board) when you step onto it, and take it out when you step back.

**Both ways to get the mark wrong, on one-row boards**, where "neighbour" just means left or right:

| Board | Looking for | With | Gives | Correct |
|---|---|---|---|---|
| `A B` | `ABA` | **no mark** | `True`: it walks back over its first cell | `False` |
| `A A A A B` | `AAAB` | **a mark that never comes off** | `False`: start 0's dead branch leaves cells 0, 1 and 2 marked, and the winning path 1 → 2 → 3 → 4 needs cells 1 and 2 | `True` |

Neither crashes. Both report the wrong answer silently. §Why the mark has to come off: two counterexamples traces them.

Three consequences of the mark:

- **The branching factor is 3, not 4,** after the first step: the cell you came from is on the path. Saying that clause shows you understood the mark.
- **The outer loop shares nothing between starts.** A search usually tries every cell as a start. Because each failed start takes all its marks back off, a set made once, outside the outer loop, is empty again at the next start. Rebuilding it for every start buys nothing. If the mark is a `rows × cols` grid of booleans instead of a set, rebuilding it also costs O(rows × cols) each time, O((rows × cols)²) in total.
- **A search that returns a bool still has to undo**, on every exit. See §Every exit un-marks.

### Count the changes, count the restores

```python
path.append(x); used.add(x)     # <- two changes
dfs(); path.pop()               # <- one restore     BUG
```

> **Count the changes before the recursive call. Count the restores after it. Two and one is always a bug.**

That is checkable by eye, unlike *"remember to undo everything."* A `used` that is never cleared gives one ordering instead of six, with no crash.

### Every exit un-marks

"At the end of the function" is not a place when the function has more than one `return`. A search that returns a bool has **two** exits after the mark: the `return True` inside the loop and the `return False` after it. **Every `return` that runs after the mark must clear it first**, or the function must be restructured to have one exit: compute the result into a variable (`any(...)` still stops at the first `True`), clear the mark, then return the variable. [bug-checklist.md](../reference/bug-checklist.md#the-un-mark-must-run-on-every-exit), §The un-mark must run on every exit, shows both forms.

> **The undo sits at the same indentation as the mark, and after it there is no reachable `return` that skips it.**

⚠️ **It often still passes on small inputs**, because once the answer is `True` everything unwinds and nobody reads the stale marks. **Passing is not evidence.** The mark now means *"used on some path I tried"*, and it fails the first time a failed branch shares a cell with a later one.

### Overwriting the input instead of keeping a set

You can mark a cell by overwriting it on the board, which saves the set. Then the undo must restore the original **value**, so save it first:

```python
saved, grid[r][c] = grid[r][c], "#"      # choose: remember what was there
...                                      # explore
grid[r][c] = saved                       # undo: put back the value, not a guess
```

Restoring a guessed value instead corrupts the input for every later start.

### Why it has to be recursion

| | Why not |
|---|---|
| BFS | every queue entry would need **its own copy** of the marks, O(L) for a path of length L, copied on every push |
| A plain iterative DFS | popping a node off an explicit stack gives you no *"I have finished everything below this node"* moment, so there is nowhere to put the undo unless you push one yourself |

> **Backtracking needs an exit moment, and recursion gives you one for free:** the line after the recursive call runs exactly when everything below the choice is done.

---

## The return rule: collect all, or find one?

`can_reach_leaf` returned a bool. `all_subsets` returns nothing from its helper and fills `res`. **That difference changes what goes inside the choice loop.** It is one of the most common bugs in any recursive search.

> **Does this function have a return value?**

| | Inside the choice loop | After the loop |
|---|---|---|
| **No**: it changes a shared `res` | `dfs(...)` **bare**, never prefixed with `return` | nothing |
| **Yes, a bool** | **`if dfs(...): return True`** | **`return False`** |
| **Yes, a number** | `best = max(best, dfs(...))` | `return best` |

> **`return dfs(...)` hands the first child's *failure* back as the whole function's verdict.** A failed branch is not an answer; it is one option eliminated. **Return on success; keep looping on failure.**

That is the shape of the last five lines of `can_reach_leaf` in §0.2, the first function in this module.

⚠️ An early `return True` must still undo whatever was marked: §Every exit un-marks.

⚠️ A function that falls off the end returns `None`. Relying on `None` being falsy makes it correct only because of a fact about the surrounding code: write the `return False`. See [bug-checklist.md](../reference/bug-checklist.md#when-the-function-does-return-a-value), §When the function does return a value, and [bug-checklist.md](../reference/bug-checklist.md#return-inside-the-neighbour-loop), §`return` inside the neighbour loop.

---

## Pruning

There are two ways to a correct answer: generate everything and filter, or **never build an invalid candidate**. The second is what's being scored.

### Only on a monotone constraint

> **Prune only on a constraint that, once violated along the path, stays violated.** It is the same test as binary search's predicate: `F F F T T T`, never back to `F`. See [04-binary-search.md](04-binary-search.md#03-vocabulary), §0.3 Vocabulary.

"The sum has passed the target" is monotone when every value is positive: adding more can't bring the sum back down. With a negative in the list it isn't, and the prune deletes real answers.

### Sorting turns `continue` into `break`

```python
if values[i] > remaining: continue       # unsorted: a later value might still fit
if values[i] > remaining: break          # sorted: every later value is too big as well
```

`continue` skips one child; `break` leaves the loop, which is only right when every later child would fail the same test. See [python-toolkit.md](../reference/python-toolkit.md#loop-control-continue-break-pass-return), §Loop control: `continue`, `break`, `pass`, `return`.

### Depth versus width

> **A budget prune caps the tree's DEPTH. It does nothing about its WIDTH**, and on input with many equal values the width is where all the waste is.

Every subset of `[1] * 100` that sums to 30:

| | Nodes visited | Answers recorded | Distinct answers |
|---|---|---|---|
| "stop once the sum passes 30" only | about 10²⁵ | about 10²⁵, all the same subset | 1 |
| plus the duplicate-sibling skip | 31 | 1 | 1 |

The budget prune correctly stops every branch at depth 30. All 10²⁵ of them: that is how many ways there are to pick 30 of the 100 equal items, and each is a different path to the same answer.

### Rank a prune before writing it

| Prune | Buys | Kind |
|---|---|---|
| the duplicate-sibling skip | removes whole subtrees | **changes the complexity class** |
| `if values[i] > remaining: break`, on sorted input | skips children that would return at once | a constant factor |
| `return` once an answer is recorded at a leaf | saves the calls that could only overshoot | a constant factor |
| stop when `remaining < 0` | caps the depth | **needed for termination** when reuse is allowed |

⚠️ **The last one is not an optimisation.** When you recurse on `i` and nothing else shrinks, it is the only thing that ends the recursion. Deleting it doesn't make the code slow; it makes it crash.

⚠️ **Sorting for `break` is a constant factor, not an exponent.** The `> remaining` test works on unsorted input; sorting only lets you leave the loop early. Sorting never changes how many answers exist, so it can never beat an output-sensitive bound. When sorting does change a complexity class, it is because it enabled a different technique: binary search, two pointers, or the **adjacency that makes the duplicate skip possible**.

### A set on the output is the receipt for a prune you didn't do

When you reach for a `set` to clean up the answers, ask what is producing the mess. There are two usual sources:

| The set exists because | It goes away when |
|---|---|
| the same answer comes out in several **orders** | the start index comes back (§The index is two switches) |
| equal inputs produce **identical subtrees** | the sibling skip goes in (§Duplicates in the input) |

And once the prune is in, delete the set. Left behind, it is scaffolding for a bug that no longer exists: see [bug-checklist.md](../reference/bug-checklist.md#the-fix-fossil), §The fix fossil. §Why not just dedup at the end? has the cost argument.

---

## Complexity of an exponential tree

> **"O(\_\_) time because the tree has \_\_ leaves and each one costs \_\_."**
> **"O(\_\_) space because the only thing I allocate is \_\_, and it's bounded by the depth."**

**The counts to know, derived in §0.2:**

| Tree | Leaves |
|---|---|
| subsets of n | 2ⁿ |
| orderings of n | n! |
| choose k of n | C(n, k) |
| strings of length n over k symbols | kⁿ |
| balanced or nested structures of n pairs | the Catalan number, about 4ⁿ / n^1.5 |

**The three blanks, and the one people skip:**

| Blank | Subsets |
|---|---|
| how many leaves | 2ⁿ |
| **× cost per leaf**, the skipped one | n, because `path[:]` copies |
| = time | **O(n · 2ⁿ)** |

⚠️ **Where a cost sits decides whether you add it or multiply by it.** A `sort()` at the top runs once, so the total is O(n log n + n · 2ⁿ), not O(n log n · 2ⁿ). Inside the loop, multiply; before it, add.

⚠️ **The output is exponential; your auxiliary space is not.** You stand on one root-to-node path at a time: **O(depth)**, the recursion stack plus `path`. Depth, not node count, is the same arithmetic as the recursion limit in [00-before-you-start.md](00-before-you-start.md#stack-depth), §Stack depth.

⚠️ **Depth is not always n.** With reuse the path can be longer than the input: one candidate `2` and a target of 40 give n = 1 and depth 20. **Depth = target ÷ smallest value.** When the shape of the tree changes, every number changes with it. Read the complexity off the code in front of you; don't carry the last problem's sentence over.

**Optimality, unusually clean here:**

> *"Any correct algorithm must write down every answer, 2ⁿ of them, each up to n long, so Ω(n · 2ⁿ) is a lower bound and this matches it."*

That is an **output-sensitive** argument: cost measured against how much answer there is. It is also what makes generate-and-dedup's verdict precise: optimal when every element is distinct, and exponentially non-optimal on exactly the inputs with many duplicates.

---

## Every template, in one place

Nine templates, in this order, because each is the one above it with a single change. The skeleton is §0.5, primitive 1.

| Row | Template | The delta from the row above | Invariant | Time · space |
|---|---|---|---|---|
| 1 | the skeleton | (§0.5) | `path` holds the choices from the root to here; on return, everything touched is back | leaves × cost per leaf · O(depth) |
| 2 | subsets | record at **every node** (`all_subsets`) | `path` is a subset in increasing index order; every node is a distinct subset | O(n · 2ⁿ) · O(n) |
| 3 | combinations, exactly k | record only where `len(path) == k`, and that branch returns (`choose_k`) | `path` holds numbers in increasing order; a leaf is reached exactly when it holds k | O(k · C(n, k)) · O(k) |
| 4 | a target sum, reuse allowed | sort once; carry `remaining`; recurse on `i`, not `i + 1`; `break` once a value exceeds `remaining` | `path` sums to `target − remaining`, and every item on it is at an index ≤ the current `start` | O(n^(target/min)) worst case · O(target/min) |
| 5 | duplicates in the input | sort once, then skip a child equal to the sibling before it: `i > start`, never `i > 0` | at every node each distinct value starts at most one child, so no two paths spell the same multiset | as the version without duplicates, minus the repeated subtrees |
| 6 | orderings | drop the start index, loop over every index, add `used` (`all_orderings`) | `used[i]` is True exactly while `items[i]` is on the path | O(n · n!) · O(n) |
| 7 | orderings with duplicates | rows 5 and 6 composed: the `not used[i − 1]` clause below | among equal values, copies are used left to right, so each arrangement comes from exactly one path | O(n · n!) worst case · O(n) |
| 8 | grid search | the mark is a cell: on when you step onto it, off when you step back; bounds, then the cell test, then the mark | the marked cells are exactly the cells on the current path, so a sibling branch starts from a clean board | O(rows × cols × 3^L) for a path of length L · O(L) |
| 9 | constraint sets | one level per item to place; one set per kind of conflict; legality is one lookup per set; every set changed and restored | the sets describe exactly the items placed on levels `0 … level − 1`, so a position passing every test is legal against all of them | O(n!) worst case · O(n) |

> **Read it as one algorithm and eight deltas.**

Notes on the rows:

- **Row 4** terminates only because `remaining` strictly decreases on every call. Positive values are what make that true, and what make the `break` safe.
- **Row 5's** first choice at each node is always allowed; only the later equal siblings are skipped.
- **Row 8's** outer loop shares nothing between start cells, and a bool-returning search must still undo on every exit.
- **Row 9:** one level per item makes one kind of conflict impossible by construction, a constraint you never have to test. With three sets there are three changes and three restores; forgetting one gives a wrong count and no crash.

**Row 7, the clause** (orderings with duplicates, inside row 6's loop, after a sort):

```python
items.sort()
for i in range(len(items)):
    if used[i]:
        continue
    if i > 0 and items[i] == items[i - 1] and not used[i - 1]:
        continue                         # the earlier equal copy is free: same branch as before
    ...
```

⚠️ `not used[i - 1]`, **not** `used[i - 1]`. If the earlier copy is on the path, you are legitimately deeper, using the second copy after the first. Here `i > 0` is right, not `i > start`: there is no start index in orderings, and `used` is what tells siblings from ancestors.

---

## How to attack a backtracking problem

1. **Is it backtracking?** "Return all …", a combinatorial output, and **a small bound** such as `n ≤ 20`. The tiny bound is permission to be exponential. "How many" or "the best" points elsewhere (§0.8).
2. **Is the answer a fact about the path?** If a cell or item is either usable or not whichever way you reached it, nothing needs undoing and the walk is linear. If it is "used on this path, free on another", you need a per-path mark, and the search is exponential.
3. **Name the pattern, a node and an edge**, one sentence each (§0.2, §Which one is it?).
4. **List the state, three lines, before any code:** what `dfs` must be **told**, and what each parameter means; what is **shared**, and what gets undone; what must be **true when it returns**.
5. **Which loop?** Recurse on `i + 1`, recurse on `i`, loop over every index with `used`, or fill slots by level. Read it off the statement, say it, then write it (§The index is two switches, §Slots with their own choices).
6. **What shrinks?** The index, the budget, or the level. Name it, or the recursion doesn't terminate.
7. **Am I pruning, and is the constraint monotone along the path?** Then rank the prunes: class-changing, constant-factor, or needed for termination. If you're not pruning, say why not.
8. Write it.
9. **Run [bug-checklist.md](../reference/bug-checklist.md#the-30-second-pass), §The 30-second pass**, then §Common backtracking mistakes below. Then, specific to here: *is that append copying?* · *count the changes, count the restores* · *does every `return` after the mark un-mark first?* · *what did my last fix make unnecessary?*
10. **Trace the miss and the degenerate cases**, not the happy path: empty input, one element, `k = 0`, a duplicate in the input, and **the branch that fails and must leave the state clean**.
11. **Say the complexity unprompted, time and space.** Leaves × cost per leaf; O(depth) auxiliary space, output not counted. Then: *is it optimal?* "Any algorithm must write down every answer."

---

## In depth

The derivations and counterexamples behind the rules above. Read them once, then come back when a rule stops making sense.

### Why the mark has to come off: two counterexamples

Both boards are one row, so "neighbour" means left or right, and there is no ordering of directions to argue about. Both report the wrong answer **silently**.

**No mark at all: the path walks back over itself.**

```
 A  B
 0  1
```

Looking for `"ABA"`. Start at cell 0: `A` matches. Cell 1: `B` matches. Back to cell 0: `A` matches. **`True`.** There is no third cell, so **the answer is `False`.**

> **A path can't reuse a cell, and nothing but a mark enforces that.**

**A mark that never comes off: a dead branch eats a cell the winner needs.**

```
 A  A  A  A  B
 0  1  2  3  4
```

Looking for `"AAAB"`. **The answer is `True`:** cells 1 → 2 → 3 → 4 spell `A A A B`.

| Start | What happens | Cells left marked |
|---|---|---|
| 0 | marks 0 → 1 → 2, then needs `B`: cell 1 is marked, cell 3 holds `A`: dead | 0, 1, 2 |
| 1 | already marked by start 0: dead at once | 0, 1, 2 |
| 2 | already marked by start 0: dead at once | 0, 1, 2 |
| 3 | marks 3, then needs `A`: cell 2 is marked, cell 4 holds `B`: dead | 0, 1, 2, 3 |
| 4 | holds `B`, the first letter is `A`: dead at once | 0, 1, 2, 3 |
| | **reports `False`** | |

> **Cells 1 and 2 are on the winning path, and start 0's failed branch ate them.**

**The general statement:** a mark that stays on records *"this cell was on some path I tried."* A per-path mark records *"this cell is on the path I am standing on."* The first is a fact about the cell. The second is a fact about the path, and it is the only one that is correct here.

### `start`: one parameter, three jobs

Say the sentence: *`start` is the index of the first element this call is still allowed to choose.* Every call gets a shrinking window `[start, n)`, and `start` is its left edge.

| Job | Mechanism |
|---|---|
| **Forbids reordering** | you can only ever go right, so `[2, 1]` is unreachable |
| **Forbids reuse** (with `+ 1`) | the window excludes the element you just took |
| **Ends the recursion** | the window empties, the `for` runs zero times, the call returns |

> **The third job means there is no base case to write.** A base case you design away beats one you handle, and it is why the subsets template has no `if` at the top.

**What the seed value means:** `dfs(0)` for 0-indexed input, `dfs(1)` for `choose_k`'s `1 … n`. It is *"nothing chosen yet, everything still allowed"*, not an off-by-one to guess at.

**And the cost of skipping the sentence:** dropping `start` to allow reuse flips **both** switches. You get reuse *and* every ordering of every answer, which then needs a `set` of tuples to clean up: generate-and-filter at an exponential premium, for a one-character fix.

### The aliasing bug, traced to the end

```python
res, path = [], []

def dfs(start):
    res.append(path)                     # <- no copy
    for i in range(start, 3):
        path.append(i)
        dfs(i + 1)
        path.pop()

dfs(0)
```

**Count the boxes.** After the first `res.append(path)` there is **one** list with **two** names: `res[0]` and `path` are the same object. Every later call appends the same object again, so `res` ends up holding eight references to it, one per node of the 2³ tree.

Trace it to the end: every `append` to `path` is matched by a `pop`, so when the top-level call returns, `path` is `[]`, and `res` is `[[], [], [], [], [], [], [], []]`. **The right count, no contents, no exception.**

> **`[:]` is not a ritual.** `path[:]` builds a **new** list with the same elements. So do `list(path)`, `path.copy()` and `[x for x in path]`: one new box each, and later changes to `path` can't reach them.

**The test, at every `append` into `res`: does this list keep changing after I store it?** If yes, copy. It takes two seconds, and the bug it catches never raises.

### The version with no undo, and its price

```python
def dfs(start, path):                    # path is a PARAMETER
    res.append(path)                     # no copy needed: nobody changes this list
    for i in range(start, len(items)):
        dfs(i + 1, path + [items[i]])    # a NEW list for each child
```

**It is correct, and it is shorter.** `path + [x]` builds a new list, so there is nothing to undo and nothing to copy. What it costs:

| | Lists allocated | Live memory |
|---|---|---|
| `append` and `pop`, copy at each record | one shared list, plus one copy per recorded answer | the shared list: O(depth) elements |
| `path + [x]` | one new list per edge | one list per frame on the stack, of lengths 0 to depth: O(depth²) elements |

For subsets the allocation counts are close: there are 2ⁿ − 1 edges, and the mutating version also makes one copy per node, because every node is an answer. The difference grows when only some nodes are recorded, as in orderings, where there are about e · n! edges but only n! leaves to copy. Either way, every new list costs O(k) to build.

> **Say the trade-off if asked, then write the mutating version.** It is the one that generalises to `used`, a set of cells, or the board itself, where there is no `+` to lean on.

**This is also the honest limit of "the undo is what makes it correct".** In the selection patterns (subsets, combinations, target sums) the start index alone keeps every path legal, so the shared list and its undo are an allocation choice. In orderings and on grids, something has to record which items or cells are on the path, and that record is what keeps the answer correct (§Why the mark has to come off: two counterexamples). With `path + [x]` that record is the new list itself, and asking it `x in path` costs O(k).

### What the tree picture shows, and what it hides

For the selection problems, the tree is the right picture. It shows the shape, the branching factor and the leaf count, and those are what the complexity answer is made of.

But the picture rests on one property:

> **In a tree a node has exactly one parent.** So you can never arrive twice, so there is nothing to guard against, so there is no mark, so there is no un-mark.

That is why `all_subsets` needs only `path` and its `pop`. The picture hides the mechanism that appears as soon as the property fails. In orderings, every item is reachable from every node above it; on a grid, a cell is reachable from four sides. Then a mark appears, and with it the rule that it comes off on the way out. Draw the tree to count; think about the mark to get it right.

A mark that stays on is the opposite tool: it lets two paths share what one of them learned. §When it stops being backtracking is about that.

### Why not just dedup at the end?

For duplicate inputs, `set(tuple(p) for p in res)` produces the right answer. It is also **exponentially worse than the one-line fix**, and the argument is worth having ready.

| | Nodes visited | Memory held |
|---|---|---|
| skip equal siblings | one per **distinct** answer | the distinct answers |
| dedup at the end | one per **path**, every repeat included | **every** answer, repeats included |

Every subset of `[1] * 20`: there are 21 distinct subsets (zero to twenty ones) and 2²⁰, about a million, paths. The filter does about 50,000 times the work to return the same list.

**The optimality argument is output-sensitive:**

> *"Any correct algorithm must write down every answer, so the size of the output is a lower bound. Skipping equal siblings visits one node per answer and so matches it. Generate-and-dedup does not: its cost depends on how many times each value repeats, not on the size of the answer."*

> **A `set()` on the output is the receipt for a prune you didn't do.** Whenever you reach for it, ask what is producing the mess.

### When it stops being backtracking

Backtracking and dynamic programming can walk the **same tree**. The difference is one line: whether the mark comes off.

| | The mark | Two paths reaching the same state |
|---|---|---|
| **Backtracking** | per-path, comes off | are **different**: the path is part of the state |
| **Memoised DFS** | stays on, as a cache of answers | are **the same**: answer the state once, reuse it |

> **You cannot memoise a search whose state *is* the path.** If "everything used so far" is part of the state, no two nodes share a state, and there is nothing to cache.

**Memoisation becomes possible exactly when the rest of the problem has a small key**, such as `(index, remaining)` instead of `(index, the whole set of things used)`. That reduction is the entire skill of module 09, and you'll see it there ([09-dp.md](09-dp.md)).

**The tell in the statement:** *"return all …"* needs the candidates themselves, and they can't be memoised away. *"How many"* or *"the best"* needs only a number, so the candidates can be thrown away, so paths that reach the same state collapse into one. **The word "all" is the line between the two topics.**

### The tree is never built

The phrase to avoid is "build the tree": it gets read literally. **The question is "what tree am I walking?"**

§0.2, §Only one path exists at a time, shows what is in memory at one node: one `path`, one stack frame per level, and `res`. Everything else exists only as calls that have finished or haven't started.

Building the tree would cost O(2ⁿ) space; walking it costs O(n). **That is why `pop()` exists**, because the single `path` has to be moved to the next node instead of a new node being allocated, **and why `res.append(path[:])` needs the copy**, because the thing being recorded is about to be moved.

DFS never had a number of children built into it: *"visit a node, then fully explore each child before moving to the next sibling."* A binary tree is the case where the child list has length 2 and the entries have names, so the loop is written out as two lines, `dfs(node.left)` and `dfs(node.right)`, instead of a `for` ([06-trees.md](06-trees.md#the-shape--memorise-this), §DFS, The shape — memorise this).

---

## Common backtracking mistakes

| Mistake | What you see | Entry |
|---|---|---|
| `res.append(path)` with no copy | the right number of answers, every one `[]` | §The copy; [python-toolkit.md](../reference/python-toolkit.md#lst-the-copy-idiom-and-the-bug-it-exists-to-prevent), §`lst[:]`: the copy idiom, and the bug it exists to prevent |
| The undo is missing | later branches see a poisoned state; "not found" on inputs that have an answer | §0.5, primitive 1 |
| Only one of two changes undone | orderings silently lost: one instead of all of them | §Count the changes, count the restores |
| An early `return` that skips the un-mark | passes small tests, fails when a dead branch shares a cell with a later one | [bug-checklist.md](../reference/bug-checklist.md#the-un-mark-must-run-on-every-exit), §The un-mark must run on every exit |
| The undo at the wrong depth, inside the inner loop | the mark is gone before the next direction is tried | §0.5, primitive 1: same indentation as the choose |
| `return dfs(...)` inside the choice loop | one path explored instead of all; a search that gives up after the first failed child | [bug-checklist.md](../reference/bug-checklist.md#return-inside-the-neighbour-loop), §`return` inside the neighbour loop, and [bug-checklist.md](../reference/bug-checklist.md#when-the-function-does-return-a-value), §When the function does return a value |
| Recursing on `i` where `i + 1` was meant, or deleting `start` | infinite recursion, or every ordering of every answer | §The index is two switches |
| A base case that doesn't `return` | extra calls, duplicated or over-long candidates | §Combinations: choose exactly k |
| `res = []` inside the recursive function | always empty | accumulators live outside the recursion |
| `i > 0` instead of `i > start` in the sibling skip | legitimate repeats of a value dropped one level down | §Duplicates in the input |
| The sibling skip without sorting | duplicates survive | §Duplicates in the input |
| A `set` on the output, kept after the real fix | correct, and exponentially slower on repeated input | [bug-checklist.md](../reference/bug-checklist.md#the-fix-fossil), §The fix fossil |
| `[:]` where only a read was needed | an O(k) allocation at every node | [bug-checklist.md](../reference/bug-checklist.md#the-copy-reflex--where-only-a-read-was-needed), §The copy reflex: `[:]` where only a read was needed |
| Pruning a constraint that isn't monotone | real answers deleted, output too short | §Only on a monotone constraint |
| `continue` where sorted input allows `break` | correct, and no faster than not pruning | §Sorting turns `continue` into `break` |
| A grid neighbour read before the bounds test | the search wraps to the other side of the grid instead of stopping | [bug-checklist.md](../reference/bug-checklist.md#a-negative-index-wraps-instead-of-crashing), §A negative index wraps instead of crashing |
| Overwriting a grid cell with no saved original | a guessed value restored; the input corrupted for later starts | §Overwriting the input instead of keeping a set |
| Complexity given as "exponential" and left there | reads as not having computed it | §Complexity of an exponential tree |
| The leaf count given with the cost per leaf left at 1 | O(2ⁿ) where the answer is O(n · 2ⁿ) | §Complexity of an exponential tree |
| A one-off cost multiplied instead of added | O(n log n · 2ⁿ) for a sort that runs once | §0.7 |
| "O(2ⁿ) space" | the output confused with what you allocate | §0.7 |

---

## Drill set — cold, no IDE, no running

Each problem is ordered so that it adds exactly one new thing to the one before. The patterns are taught above on problems outside this table (`leaf_path`, `choose_k`, Combination Sum III, the one-row boards), except the two template rows, which are marked.

| # | Problem | Focus |
|---|---|---|
| 1 | [Subsets](https://leetcode.com/problems/subsets/) (LC 78) | The first template: choose, explore, undo; the start index; `path[:]`. A from-memory rep of `all_subsets` in §The three patterns: write it without looking. ⚑ **Checkpoint** |
| 2 | [Subsets II](https://leetcode.com/problems/subsets-ii/) (LC 90) | **+ duplicates.** One delta from row 1: sort, then skip equal siblings. `i > start` |
| 3 | [Combination Sum](https://leetcode.com/problems/combination-sum/) (LC 39) | **+ a target and reuse.** Recurse on `i` instead of `i + 1`, and the first real pruning decision |
| 4 | [Combination Sum II](https://leetcode.com/problems/combination-sum-ii/) (LC 40) | **Both dedup mechanisms in one problem** |
| 5 | [Permutations](https://leetcode.com/problems/permutations/) (LC 46) | **The shape change.** No start index; the per-path mark `used` appears. Two changes, two undos. A from-memory rep of `all_orderings` in §The three patterns |
| 6 | [Generate Parentheses](https://leetcode.com/problems/generate-parentheses/) (LC 22) | **Pruning is the algorithm.** No list to choose from: two counters, and invalid strings are never built. [02-stacks-queues.md](02-stacks-queues.md#when-the-stack-is-only-a-counter), §When the stack is only a counter, says why it is here |
| 7 | [Letter Combinations of a Phone Number](https://leetcode.com/problems/letter-combinations-of-a-phone-number/) (LC 17) | **The choice set changes per level**, and the depth is fixed by the input. §Slots with their own choices |
| 8 | [Palindrome Partitioning](https://leetcode.com/problems/palindrome-partitioning/) (LC 131) | **The choice is a cut point**, not an element: *"where does this piece end?"* |
| 9 | [Word Search](https://leetcode.com/problems/word-search/) (LC 79) | **The flagship grid problem.** The per-path mark on a cell, the bounds test first, and the return rule for a search that returns a bool. ⚑ **Checkpoint** |
| 10 | [N-Queens](https://leetcode.com/problems/n-queens/) (LC 51) | **Constraint sets.** O(1) legality, three marks and three undos, and rendering the output |

**Why this order:** each variant sits right after the problem it differs from by one line, so the delta is the thing being drilled. Rows 1 to 5 are exactly the three patterns: do them until the templates are automatic, because rows 6 to 10 all assume them. Rows 6 to 8 change what a choice is: a counter, a slot, a cut point. Row 9 comes late because it is the bridge from tree DFS to a grid of moves, and it lands best once the undo is a reflex. Row 10 is last because it is the only one where the state is not just the path.

**⚑ Checkpoint:** if row 1 doesn't come out clean without notes, stop there. Every later row is this template with a line or two changed, so reread §0.2, §0.5 and §Subsets, and don't move on to row 2 until it does.

**⚑ Checkpoint:** row 9 is the first problem where the mark is needed for the answer to be right, not just for tidiness, and where the search returns a bool. If it doesn't come out clean, reread §The per-path mark and §The return rule: collect all, or find one? before row 10.

**Watch row 5.** It is a shape change, not a variant. If the `used` and `path` pair isn't clean, do a second rep with Permutations II from the spares.

**Spares, if a shape needs a second rep:** [Combinations](https://leetcode.com/problems/combinations/) (LC 77, written out in §The three patterns as `choose_k`; a from-memory rep) · [Combination Sum III](https://leetcode.com/problems/combination-sum-iii/) (LC 216, written out in §The choice loop; a from-memory rep) · [Permutations II](https://leetcode.com/problems/permutations-ii/) (LC 47; its extra clause is in §Every template, in one place) · [Path with Maximum Gold](https://leetcode.com/problems/path-with-maximum-gold/) (LC 1219) · [Letter Case Permutation](https://leetcode.com/problems/letter-case-permutation/) (LC 784, the simplest two-branch tree) · [Restore IP Addresses](https://leetcode.com/problems/restore-ip-addresses/) (LC 93, cut points and a fiddly validity rule) · [Unique Paths III](https://leetcode.com/problems/unique-paths-iii/) (LC 980, a grid where you count instead of asking whether one exists) · [Partition to K Equal Sum Subsets](https://leetcode.com/problems/partition-to-k-equal-sum-subsets/) (LC 698, where pruning stops being optional) · [Sudoku Solver](https://leetcode.com/problems/sudoku-solver/) (LC 37).

## Not covered here

- **Memoised DFS over these same trees.** Once the rest of the problem has a small key, paths that reach the same state can share one answer. You'll see this again in module 09 ([09-dp.md](09-dp.md)); §When it stops being backtracking is the bridge.
- **Bitmask state:** `used` stored as the bits of one integer instead of a list.
- **Iterative deepening:** repeated depth-limited searches with a growing limit.
- **Branch and bound with a real bound function**, and best-first search, which picks the most promising partial answer next. That needs a priority queue, and you'll see heaps later, in module 10 ([10-heaps.md](10-heaps.md)).
- **Constraint propagation:** shrinking the other slots' options after each choice, as serious Sudoku solvers do.

If one of these comes up, one sentence is enough: *"the worst case is exponential; the pruning cuts it hard in practice, and if the constraints were bigger I'd look for a DP formulation, or a bitmask over the used set."*

## Before you submit anything

Run [bug-checklist.md](../reference/bug-checklist.md#the-30-second-pass), §The 30-second pass, over your code. Thirty seconds.

---

## Self-check answers

1. When both children fail, the node is not on any winning path, so the undo puts `path` back as the parent left it and the next sibling starts clean. Without it, the failed node's value would stay in the answer, as `[4, 1, 3, 2]` in the trace. When a child succeeds, `path` holds the winning route, which is the result the caller wants, so popping would destroy it.
2. The tree has **2ⁿ nodes**, one per subset, and every one is an answer. Each is recorded with an O(n) copy, so the time is **O(n · 2ⁿ)**. Only one root-to-node path exists at a time, so the auxiliary space is **O(n)**, the stack plus `path`; the output itself is counted separately.
3. You get **the right number of answers, every one `[]`.** `res` holds many references to the one `path` list, and every `append` is matched by a `pop`, so the list is empty at the end. No exception, because nothing invalid ever happens: each stored reference just points at the same list.
4. Recursing on `i` **allows reuse** of the same item while still forbidding reordering: the window keeps its left edge. Deleting `start` allows **both reuse and reordering**, so every answer comes out in every order, and nothing shrinks, so without some other limit the recursion never ends.
5. The prune assumes that once the sum passes the target it can never come back. With a negative value later in the list it can, so the prune throws away paths that would have reached the target. The constraint isn't monotone, so it isn't safe to prune on.
6. **Two exits** run after the mark: the `return True` inside the loop and the `return False` after it. Each must clear the mark before it returns, or the function must be rewritten with one exit: compute the result into a variable, clear the mark, then return it.
7. There are **21 distinct answers** (zero to twenty ones) but **2²⁰, about a million, paths**, so generating everything and filtering does about 50,000 times the necessary work, and holds every repeat in memory. Skipping equal siblings visits one node per distinct answer.
8. "How many" needs only a number, not the candidates themselves. That usually means paths reaching the same state can share one answer, which is memoisation, and a search whose state is the whole path can't do that. "Return all" forces you to keep every candidate, so nothing collapses, and backtracking is the right tool.
