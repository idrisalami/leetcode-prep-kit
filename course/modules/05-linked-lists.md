# Module 05: Linked lists

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
- [The dummy head](#the-dummy-head)
  - [The problem the dummy solves](#the-problem-the-dummy-solves)
  - [The code, and the invariant](#the-code-and-the-invariant)
  - [The one-pointer form](#the-one-pointer-form)
  - [When to reach for it](#when-to-reach-for-it)
- [In-place reversal](#in-place-reversal)
  - [Derive it, don't memorise it](#derive-it-dont-memorise-it)
  - [The invariant, and the order it forces](#the-invariant-and-the-order-it-forces)
  - [What to return, and the cases that need no guard](#what-to-return-and-the-cases-that-need-no-guard)
  - [Reversing part of a list](#reversing-part-of-a-list)
- [Two pointers on a list](#two-pointers-on-a-list)
  - [The fixed gap](#the-fixed-gap)
  - [Different speeds: the middle](#different-speeds-the-middle)
  - [Which middle? Trace both parities](#which-middle-trace-both-parities)
- [Floyd's cycle detection](#floyds-cycle-detection)
  - [The question and the two answers](#the-question-and-the-two-answers)
  - [Why they must meet, and why speed 2](#why-they-must-meet-and-why-speed-2)
  - [Phase 2: where does the cycle *start*?](#phase-2-where-does-the-cycle-start)
  - [Floyd without a list: Happy Number](#floyd-without-a-list-happy-number)
  - [The implicit list: when an array *is* a linked list](#the-implicit-list-when-an-array-is-a-linked-list)
- [Building a new list: dummy and tail](#building-a-new-list-dummy-and-tail)
  - [The append skeleton](#the-append-skeleton)
  - [Two builders, one join](#two-builders-one-join)
  - [Merging two sorted lists](#merging-two-sorted-lists)
- [Replacing a hash set: the five escapes](#replacing-a-hash-set-the-five-escapes)
- [How to attack a linked-list problem](#how-to-attack-a-linked-list-problem)
- [Common linked-list mistakes](#common-linked-list-mistakes)
- [Not covered in this module](#not-covered-in-this-module)
- [Drill set — cold, no IDE, no running](#drill-set--cold-no-ide-no-running)
- [Before you submit anything](#before-you-submit-anything)
- [Self-check answers](#self-check-answers)
<!-- /toc -->

This module covers singly linked lists. It has the **smallest amount of new theory and the largest amount of new failure surface** in the course. There is no clever idea here. There is one data structure, four primitives (§0.5), and about nine ways to write a bug that runs without crashing and returns the wrong list. You'll learn what a list node is, how to build a list by hand, what each operation costs, and the moves almost every solution is made of: the dummy head, in-place reversal, two pointers at a fixed gap or at two speeds, Floyd's cycle detection, and building a new list out of existing nodes.

The whole module turns on one sentence:

> **What does each pointer point to, at the top of every iteration?**

Reversal is three pointers, and it can't be written reliably without that sentence. Not "harder": without it you get it right by accident or not at all.

The drill set at the bottom is deliberately **not solved anywhere in this file**. Every example the sections walk through uses a problem outside the drill set.

**How to use it.** Read §0, then answer the self-check in §0.9 and re-read the parts of §0 behind any question you miss. Then work through the sections from the dummy head to building a new list, and do the drill set cold.

| Section | What it gives you |
|---|---|
| §0, the foundation | the trade against arrays, what a list node is, its vocabulary, what each operation costs, the four primitives, the inputs that break list code, the signals |
| The dummy head | the node you invent so the head stops being a special case |
| In-place reversal | the three-pointer loop, derived rather than memorised, and reversing part of a list |
| Two pointers on a list | the fixed gap, and two speeds for the middle |
| Floyd's cycle detection | both phases, the proof, and the implicit list hiding in a problem with no list in it |
| Building a new list | dummy plus tail, and the one line everyone forgets |
| Replacing a hash set | what "do it in O(1) space" asks you to do |
| How to attack a linked-list problem | the steps, in order |
| Common linked-list mistakes | the bugs, each linked to its checklist entry or section |
| Drill set | the problems, with the checkpoints |
| Before you submit anything | the checklist |

---

## 0.1 Prerequisites and the one question

| You need | From | Used here for |
|---|---|---|
| Counting cost, and space as what you allocate | [00-before-you-start.md](00-before-you-start.md#big-o-from-zero), §Big-O from zero | §0.4 and §0.7 |
| Recursion and stack depth | [00-before-you-start.md](00-before-you-start.md#recursion-and-the-call-stack), §Recursion and the call stack | why a recursive list solution is O(n) space, §0.7 |
| A hash set of what you've seen, and the Remember / Order / Reuse escapes | [01-arrays-hashing.md](01-arrays-hashing.md) | cycle detection with a set, §Floyd's cycle detection; §Replacing a hash set |
| Same-direction and converging two pointers, the sliding window | [03-two-pointers-sliding-window.md](03-two-pointers-sliding-window.md) | which pointer shapes survive on a list, below |
| Binary search and its boundary choices | [04-binary-search.md](04-binary-search.md) | why it dies on a list; choosing which middle, §Two pointers on a list |

Module 01 asked *"how do I avoid looking at every pair?"* Module 04 asked *"what structure lets me throw away half the search space?"* Both questions were about **doing less work on data you can already reach**.

A linked list changes what you can reach.

> **An array gives you O(1) random access and no pointers. A linked list gives you pointers and no random access.**

That is the entire trade, and everything in this module is a consequence of it, including which techniques from modules 01, 03 and 04 come with you and which are now impossible.

**What you bought.** Splicing. Inserting or deleting in the middle of an array costs O(n), because everything after the gap has to shift. In a list it is **O(1)**: you change one `.next` field and the structure is different. Nothing moves, nothing is copied.

**What you paid.** To reach element *k* you must walk *k* links. There is no arithmetic that gets you there. `head + k` is not a thing.

> **In an array the position is computed. In a list the position is walked.**

**The one question this module answers:**

> *When the only operation I have is "follow one link", how do I answer questions that want a second place in the list at the same time?*

The answer, every time, is: **carry more than one pointer.** That is the topic.

**What transfers from arrays, and what does not.** This table is the whole delta. Read it before you reach for a technique you know.

| Technique from modules 01, 03 and 04 | On a linked list |
|---|---|
| **Same-direction two pointers** (an offset, or different speeds) | ✅ **Transfers, and becomes the main topic.** Fast/slow, and the fixed gap |
| **Remember**: a hash set of what you've seen | ✅ Transfers unchanged. Nodes are hashable (§0.6) |
| Running state in one pass (Reuse) | ✅ Transfers: a carry digit, a running tail, a count |
| Merging two sorted sequences | ✅ Transfers, and gets **cheaper**: splicing beats copying |
| **Converging two pointers**: `lo = 0`, `hi = n - 1`, moving toward each other | ❌ **Impossible.** You cannot walk backwards in a singly linked list. `hi -= 1` has no equivalent |
| **Binary search** | ❌ Reaching the midpoint costs O(n), so each probe costs O(n) and the log buys nothing |
| `nums[i-1]`: look at the previous element | ❌ You must have **carried** `prev`. There is no way to look back |
| Sliding window by index arithmetic (`right - left + 1`) | ⚠️ Only if you count as you go. There are no positions to subtract |
| Prefix sums indexed by position | ❌ No indexing |
| Sorting in place | ⚠️ Merge sort, and written recursively it uses O(log n) stack, not O(1) |

> **The converging-pointer shape dies and the same-direction shape survives.** That is why "two pointers" reappears here looking like a different technique. It's the same family; the list only kept one branch of it.

And the consequence that catches people:

> **Anything you want to know about "the end" you must reach by starting a second pointer at a different time or at a different speed.** There is no `nums[-1]` and no `len()`. "The 5th from the end" is not a position you can compute: it's a gap you have to *set up*.

## 0.2 The structure and how it works

A **singly linked list** is a chain of nodes. Each node holds a value and a reference to the next node. The last node's reference is `None`. You hold the list by holding its first node, the **head**: there is no separate object for "the list".

```
head
 ↓
[1] ──► [2] ──► [3] ──► None
```

LeetCode defines the node class for you, in this form:

```python
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val      # the payload
        self.next = next    # a ListNode, or None at the end of the list
```

Two fields. That is the entire data structure. **Read the stub in the problem**: some problems name the class `Node`, some add a `.random` field, some add `.child`. Use the names you are given, not the ones you expect.

You receive `head`, a `ListNode`, or `None` for an empty list.

**Building one by hand.** To test your code, build the list yourself. Nest the constructors, inside out:

```python
head = ListNode(1, ListNode(2, ListNode(3)))
```

Or create the nodes and link them one at a time:

```python
head = ListNode(1)
head.next = ListNode(2)
head.next.next = ListNode(3)
```

Both build the list in the drawing. To check a result, walk it and collect the values:

```python
def to_values(head):          # for testing only
    out = []
    cur = head
    while cur:
        out.append(cur.val)
        cur = cur.next
    return out
```

**Reading LeetCode's notation.** A problem statement writes that same list as `head = [1,2,3]`. That is the chain 1 → 2 → 3, not a Python list: your function receives the first node. `[]` means `head = None`. When a problem has a cycle, the statement adds `pos`, the index of the node the tail points back to, with `-1` for no cycle. `pos` is how the test is built; it is not passed to your function.

**A doubly linked list** gives each node a `.prev` field as well, pointing at its predecessor. It makes deleting a node you hold O(1) with no predecessor hunt, at the cost of two links to rewrite per edit instead of one. This module is about singly linked lists; §Not covered in this module says where the doubly linked one comes up.

**Drawing it: the one topic where a picture beats a table.** Do this on paper before you write, every time. Four nodes, one line, arrows:

```
prev      cur       nxt
 ↓         ↓         ↓
[1] ──►   [2] ──►   [3] ──►  [4] ──► None
```

Then write **one line under it** saying what each pointer means. That line is the invariant:

> *"`prev` is the head of the reversed prefix. `cur` is the head of the untouched suffix. Nothing connects them."*

**Why a picture and not a two-column trace here:** the state of a list problem is not a set of numbers, it's a set of *arrows*, and a table can't show you that node 2 now points backwards. When you trace, redraw the arrows after each iteration. Three iterations are enough to prove or kill any of the algorithms in this module.

> ⚠️ **You'll see this again in module 06, on trees.** A linked list is a tree in which every node has at most one child: a path. Trees have no random access either, so the trade in §0.1 is really contiguous memory against linked memory.

> ⚠️ **You'll see this again in module 08, on graphs.** A list with a cycle is a graph, and a visited set is the general way to stop a walk from looping; Floyd (§Floyd's cycle detection) is the O(1)-space alternative that works because every node has exactly one way out.

## 0.3 Vocabulary

| Word | Meaning |
|---|---|
| **node** | one element: a value and a `.next` reference |
| **head** | the first node. Holding it is holding the list |
| **tail** | the last node: `tail.next is None` in a list with no cycle |
| **`None` terminator** | the `None` in the last node's `.next`. Every walk without a cycle ends on it |
| **singly, doubly linked** | one reference per node (`.next`), or two (`.next` and `.prev`) |
| **predecessor, successor** | the node before this one and the node after it. A singly linked list stores only the successor |
| **walk** | move a name along the list: `cur = cur.next`. The list does not change |
| **rewire, splice** | change a `.next` field, so the list itself changes. Splicing is inserting or removing a run of nodes by rewiring its two ends |
| **dummy head (sentinel)** | a node you invent and place before the real head, so the head has a predecessor |
| **in place** | rewiring the existing nodes instead of building new ones |
| **cycle** | a node whose `.next` leads, after some steps, back to itself. A walk over it never ends |
| **ρ (rho) shape** | a list with a cycle: a straight run from the head into a loop |
| **entrance** | the first node of the loop in a ρ: the one node with two arrows into it from reachable nodes, one from the straight run and one from inside the loop |
| **fast/slow (tortoise and hare)** | two pointers moving one link and two links per step |
| **gap** | the number of links between two pointers moving at the same speed |
| **auxiliary space** | memory you allocate beyond the input and the required output |

## 0.4 Operations and their cost

**n** is the number of nodes.

| Operation | Python | Big-O | Trap |
|---|---|---|---|
| Read a value or follow one link | `cur.val`, `cur.next` | O(1) | `None.next` raises `AttributeError`: test for `None` first |
| Walk one step | `cur = cur.next` | O(1) | it moves your name, not the list |
| Reach the k-th node | k steps from the head | O(k) | there is no `head + k`. Inside a loop it is O(n²) in total |
| Length | count while you walk | O(n) | there is no `len(head)`. Count once, before the loop, never inside it |
| Insert after a node you hold | `new.next = cur.next`, then `cur.next = new` | O(1) | the other order loses the rest of the list (§0.5, primitive 2) |
| Delete the node after one you hold | `cur.next = cur.next.next` | O(1) | you must stand on the **predecessor** |
| Insert or delete at the front | a dummy head | O(1) | without a dummy, the head is a special case |
| Find the tail | walk until `cur.next is None` | O(n) | once per append is O(n²): carry `tail` and update it |
| Search for a value | walk | O(n) | the list may be sorted; binary search still doesn't apply |
| Test "have I stood on this node?" | `seen = set()`, `node in seen` | O(1) per test, O(n) space | with `seen` as a Python list, each test is O(n) and the loop is O(n²) |
| Copy the values into a Python list | `vals.append(cur.val)` | O(n) time and **O(n) space** | correct, and it throws away the O(1)-space point of most list problems |
| Recurse once per node | `f(node.next)` | **O(n) stack** | the default limit is about 1,000 frames; list constraints often go to 5·10⁴ nodes |

**The rows people get wrong are the hidden walks.** In an array the trap is a built-in that scans. **In a list the trap is that every position lookup scans.** The only O(1) operations are following a link you hold and rewriting a link you hold.

## 0.5 The primitives

Four moves build almost every linked-list solution. Each has an invariant: the thing that is true every time it runs.

**1. A node, its value, and its link are three different things.**

| Expression | What it is | Type |
|---|---|---|
| `node` | a **name bound to a node object**: your finger, pointing at a place in the list | `ListNode` or `None` |
| `node.val` | the **payload** at that place | `int` |
| `node.next` | the **next node object**, and it is a *field of the list*, not a local of yours | `ListNode` or `None` |

And the distinction that decides whether your code walks or edits:

```python
cur = cur.next        # moves YOUR FINGER. The list is unchanged.
cur.next = other      # moves A LINK. The list is now a different list.
```

> **Rebinding a local name walks the list. Rebinding a `.next` field edits the list.** The difference is the `.next` on the left of the `=`.

It is index vs value in new clothes: two kinds of thing, one syntax, and mixing them produces code that runs and lies (see [bug-checklist.md](../reference/bug-checklist.md#node-vs-value-vs-next), §Node vs value vs `.next`). **Name your pointers after where they stand**, `prev`, `cur`, `nxt`, `slow`, `fast`, `tail`, and never after what they hold.

⚠️ **`next` is a Python builtin.** Using `next` as a local name shadows it. Harmless in most solutions, but `nxt` is the convention and it costs one keystroke.

*Invariant:* every pointer you hold is a node or `None`, never a value, and you can say for each line whether it walks or edits.

**2. `=` binds a name and never copies: save before you destroy.** On a list you rewire constantly, so this rule has consequences:

```python
a = head          # ✓ two names, ONE node. Walking `a` doesn't move `head`
a = a.next        # ✓ rebinds YOUR name. head still points where it did
a.next = None     # ✗ this edits the shared object. head's list is now cut short
```

Both kinds of line are useful, and you must be able to say which one you're writing before you type it.

The productive half: **a second name is a free bookmark.** Keep `dummy` on the front, walk with `cur`, and `dummy` still points at the front when you're done. Every "return the head" answer depends on this.

The destructive half: **you have exactly one copy of the structure, and every `.next =` is a permanent edit to it.** There is no undo, and there is no second list unless you allocated new nodes.

> ⚠️ **The rewiring rule: the moment you overwrite `cur.next`, the rest of the list becomes unreachable, unless something else already points at it.**

Inserting a node after `cur` shows it in two lines:

```python
cur.next = new        # ✗ the old cur.next is gone: nothing points at the rest
new.next = cur.next   # ...and cur.next is now `new`, so new points at itself: a cycle
```

```python
new.next = cur.next   # ✓ save first: `new` holds on to the rest of the list
cur.next = new        # then rewire
```

**Save before you destroy.** Before a line that overwrites a link, list what you still need afterwards, and make sure each of those nodes has a name. Flipping one arrow in a reversal needs **three facts**: where you came from, where you are, and where you were going. Three facts, three names. Two pointers there isn't a style choice that went wrong, it's a shortage.

**And the cycle.** Point a node at a node earlier in the list and every walk over that list runs forever. It is a hang, not a crash, and it is the standard consequence of forgetting to end a list you built out of existing nodes (§Two builders, one join).

*Invariant:* every node you still need is reachable from a name you hold, at every line.

**3. The traversal loop: `while cur` or `while cur.next`.**

```python
cur = head
while cur:                 # visits every node, ends with cur = None
    ...
    cur = cur.next
```

```python
cur = head
while cur.next:            # stops ON the last node, ends with cur = the tail
    ...
    cur = cur.next
```

These are not stylistic variants. They end in different places and they have different preconditions.

| | `while cur:` | `while cur.next:` |
|---|---|---|
| Ends with `cur` = | `None` | **the last node** |
| Reads | `cur.val` | `cur.next.val`: one node **ahead** |
| Survives `head is None`? | ✅ yes, the loop just doesn't run | ❌ **`AttributeError` on its first test** |
| Use when | you're inspecting nodes | you're **editing a link**, or you need the tail |

> **To delete or insert at a position, you must be standing on its PREDECESSOR.** A singly linked list gives you no way back, so the pointer you need is always one *before* the node you care about. That is why deletion code either looks ahead, `cur.next.val` and `cur.next = cur.next.next`, which is the `while cur.next` form, or carries a `prev` one node behind a `while cur:` walk.

⚠️ **A look-ahead needs a guard for every link it crosses**, and here the guards are load-bearing:

```python
cur.next.next          # ✗ AttributeError the moment cur.next is None
fast.next.next         # ✗ same: the most common crash in list code
```

**The fix is ordering, and Python's short-circuit does the work:**

```python
while fast and fast.next:      # ✓ each test protects the next one
    fast = fast.next.next
```

`and` stops at the first falsy operand, so `fast.next` is only read once `fast` is known not to be `None` (`None` is falsy: see [python-toolkit.md](../reference/python-toolkit.md#python-truthiness-why-while-queue-works), §Python truthiness: why `while queue:` works). **Write the guards left to right, in the order the attributes are dereferenced**, and ask of each line: *what must be true for this line to be safe?* (See [bug-checklist.md](../reference/bug-checklist.md#the-guard-asymmetry), §The guard asymmetry.)

*Invariant:* inside the body of `while cur:`, `cur` is a real node. Inside the body of `while cur.next:`, both `cur` and `cur.next` are.

**4. The dummy head.** To unlink a node you write `predecessor.next = node.next`. Every node has a predecessor except the head, so without help every deletion splits into "is it the head?" and "is it not?". A dummy is a node you invent, placed before the real head, whose only job is to be a predecessor:

```python
dummy = ListNode(0, head)     # the real head now has a predecessor
...
return dummy.next             # never `head`
```

Return `dummy.next`, because `head` is a name, and deleting or moving the node it points at does not update it. If the first node was removed, `head` still points at it (see [bug-checklist.md](../reference/bug-checklist.md#stale-names-after-a-structural-edit), §Stale names after a structural edit). Name the dummy `dummy`, so a name that means "the front" is always in scope when you write the return.

*Invariant:* `dummy.next` is always whatever is currently first, including nothing (`None`). §The dummy head works it on a full problem.

## 0.6 Inputs that break it

| Input | What breaks | Check |
|---|---|---|
| **`head = None`**, the empty list | anything that dereferences before it checks: `head.next`, `while cur.next` | does the function return the right answer for `None`? |
| **One node**, `[1]` | the middle, the k-th from the end, swapping pairs: anything that assumes a second node exists | trace it: `head.next` is `None` |
| **Two nodes**, `[1,2]` | the **only** size where fast/slow behaves differently at the boundary, and where "the middle" is ambiguous | trace it, redrawing the arrows |
| **An edit at the head** | deleting or inserting at the front has no predecessor to stand on | is there a dummy, and which name do you return? |
| **An edit at the tail** | `cur.next` is `None`, so every look-ahead crashes exactly once, at the end; a list rebuilt from existing nodes keeps a stale `.next` on its last node | is the last node's `.next` set explicitly? |
| **Consecutive matches**, `[1,1,1,2]` deleting `1` | the head is deleted three times, not once; a pointer advanced after a deletion skips the next match | trace it: one deletion passes, consecutive ones catch the bug |
| **A long list**, 5·10⁴ nodes | recursion passes the default limit of about 1,000 frames | write it iteratively |

> **Trace those, not the happy path.** Naming the breaking input is not tracing it: a bug on `[1,2]` survives being named and dies being traced. `[1,2]` takes fifteen seconds.

**Nodes are hashable by identity.** `ListNode` defines no `__hash__` or `__eq__`, so it inherits object identity: `seen = set()` and `if node in seen` work, and they compare *which object*, not which value. That is what makes the O(n)-space cycle check legal, and it is what lets a dict map each old node to a new one when a problem asks you to copy a list. Two different nodes that both hold `1` are two different members of the set. `seen.add(node.val)` asks a different question: "have I seen this value?"

⚠️ **`a == b` on two `ListNode`s is identity, same as `a is b`**, because nothing overrode `==`. It works. **Write `is` anyway**, because you mean "the same node", not "equal nodes", and on a class that *does* define `__eq__` the two diverge silently.

## 0.7 Complexity, out loud

Say these as sentences, with the reason:

- **Time:** *"O(n), one pass."* Two passes are O(n). Three sequential passes are still O(n): constant factors, not growth. Say it out loud, because "I walk the list twice" sounds expensive and isn't.
- **Space, pointer solutions:** *"O(1) space: nothing I allocate grows with n; it's three pointers however long the list is."* Not *"only three variables."* **O(1) does not mean "few". It means "does not grow with n."** Three variables are O(1). Fifty are O(1). One list of length n is O(n).
- **Space, recursion:** *"O(n) space for the call stack, one frame per node."* The call stack is auxiliary space, and a list is the deepest shape recursion can walk: one frame per node, every time. Python's default recursion limit is about 1,000, while list constraints routinely go to 5·10⁴, so **a recursive reversal raises `RecursionError` on the real input.** Write it iteratively, and if you do recurse, say it is O(n) space.
- **When the problem already uses `n` for a parameter**, "O(n)" is ambiguous. Say *"O(L), where L is the number of nodes."*

On a list, the O(n)-space version of nearly every problem is easy, and the pointer version is the answer being asked for:

| Approach | Time | Space |
|---|---|---|
| Copy the values into a Python list, solve it as an array, rebuild | O(n) | **O(n)** ✗: throws away the point |
| Hash set of visited nodes | O(n) | **O(n)** |
| Pointer manipulation in place | O(n) | **O(1)** ✓ |
| **Recursion over the list** | O(n) | ⚠️ **O(n)**: one frame per node |

**The template.** Fill the blanks; it takes fifteen seconds:

> **"O(\_\_) time, because \_\_ runs \_\_ times and each one costs \_\_."**
>
> **"O(\_\_) space, because the only thing I allocate is \_\_, and that doesn't grow with n."**

The space blank asks **what you allocate**, not **how many names you wrote**.

| Situation | Say |
|---|---|
| Reversal, Floyd, the gap | *"O(1) space: three pointers, and three is three whether the list has 2 nodes or 5,000."* |
| Splicing existing nodes into a new order: merging, partitioning | *"O(1) space even in total: the result is built out of the existing nodes, spliced, not copied. I never allocate a node per element."* |
| A new node per element of the output | *"O(output) space in total, but O(1) auxiliary, since the output is required."* |

## 0.8 Signals

| In the statement | Reach for | Where |
|---|---|---|
| anything that might delete or insert at the **front** | **a dummy head**, reflexively: it costs one line | §The dummy head |
| "reverse", "backwards", "reverse in groups" | **three-pointer in-place reversal** | §In-place reversal |
| "middle of the list", "second half" | **fast/slow** | §Different speeds: the middle |
| "k-th from the end", "remove the n-th from the end" | **two pointers with a fixed gap** | §The fixed gap |
| "does it have a cycle", "does it terminate", "where does it repeat" | **Floyd** | §Floyd's cycle detection |
| "O(1) space" in the statement or the follow-up | you are being told **not** to use a hash set or an array: pointers | §Replacing a hash set |
| two (or k) **sorted** lists | **merge with a dummy and a tail**; for k lists, a heap of the current heads (you'll see heaps in full later, in module 10) | §Merging two sorted lists |
| "palindrome", "reorder", "fold" | **a composite:** find the middle, reverse the second half, then walk both | §Different speeds: the middle, §In-place reversal |
| a `.random` or other extra pointer, "deep copy" | **a dict from old node to new node**: the map is also the visited set | §0.6 |
| "O(1) get and put", "least recently used" | **a doubly linked list plus a dict**: the list gives O(1) unlink, the dict gives O(1) find | §Not covered in this module |
| values that are **valid indices into their own array**, and O(1) space | **Floyd on an implicit list**, `i → nums[i]` | §The implicit list |
| "does it eventually **repeat**", a function applied over and over to a finite set of states, no list in sight | **build the implicit list**: check the conditions, then Floyd | §The implicit list |

The same choices, cut down to four moves, are in [decision-rules.md, §The four moves](../reference/decision-rules.md#the-four-moves).

## 0.9 Self-check

Answer each in a sentence or two, without looking back. The answers are at the bottom of the module. Read the part behind any question you miss.

1. State the trade between an array and a linked list in one sentence. Which two-pointer shape survives on a list, and why does binary search die?
2. What is the difference between `cur = cur.next` and `cur.next = other`? Which one changes the list?
3. You want to insert `new` after `cur`. What goes wrong if you write `cur.next = new` first and `new.next = cur.next` second?
4. Where does `while cur:` leave `cur`, and where does `while cur.next:` leave it? Which survives `head = None`? Why does deletion code look ahead at `cur.next` or carry a `prev`, rather than act on `cur` alone?
5. Why does a dummy head remove the special case for deleting the head, and why do you return `dummy.next` rather than `head`?
6. Why is `while fast and fast.next:` safe while `while fast.next and fast:` is not?
7. A recursive solution walks a list of 5·10⁴ nodes, one call per node. What is its space, and what happens in Python?
8. `a = ListNode(1)` and `b = ListNode(1)`. What do `a == b` and `a is b` return? If you put both nodes in a set, how many members does it have, and how many if you put in `a.val` and `b.val`? Why write `is` when you mean "the same node"?

---

## The dummy head

**Worked on [LC 203 Remove Linked List Elements](https://leetcode.com/problems/remove-linked-list-elements/)**, which is not in the drill set. *Remove every node whose value equals `val`.*

### The problem the dummy solves

To unlink a node you write `predecessor.next = node.next`. Every node has a predecessor, **except the head**. So every deletion-or-insertion algorithm splits into two cases:

```python
if cur is head:               # ✗ the special case
    head = head.next
else:
    prev.next = cur.next
```

And it's worse than it looks, because the head can be deleted **repeatedly**: `[1,1,1,2]` with `val = 1` deletes the head three times, so the special case isn't even a single check at the top.

> **A dummy head is a node you invent, placed before the real head, whose only job is to be a predecessor.** Then the real head is an ordinary node, and there is no special case at all.

```python
dummy = ListNode(0, head)     # or: dummy = ListNode(); dummy.next = head
```

```
dummy ──► [1] ──► [1] ──► [2] ──► None
  ↑        ↑
 the      the real head, which now has a predecessor
invention
```

**And you return `dummy.next`, never `head`**, because `head` may be one of the nodes you deleted, and the name still points at it.

> ⚠️ **`return head` after a deletion is a name that can't express the answer** (see [bug-checklist.md](../reference/bug-checklist.md#stale-names-after-a-structural-edit), §Stale names after a structural edit). It doesn't crash. It returns a list starting at a node you removed. `dummy.next` is always the current front, by construction.

### The code, and the invariant

**The invariant, before the loop:** *"`prev` is the last node of the part I am keeping. `cur` is the node I am currently judging. Everything up to `prev` is final."*

```python
def removeElements(self, head, val):
    dummy = ListNode(0, head)
    prev = dummy                      # the kept part is empty, so its last node is the dummy
    cur = head
    while cur:
        if cur.val == val:
            prev.next = cur.next      # unlink. prev does NOT move: it's still the last kept node
        else:
            prev = cur                # cur survives, so it becomes the last kept node
        cur = cur.next                # cur always advances, in both branches
    return dummy.next
```

**Read the two branches against the invariant.** `prev` advances *only when the node it would advance to is being kept*. That asymmetry is the whole algorithm, and it's invisible unless you said the invariant first.

> ⚠️ **The bug: advancing `prev` unconditionally.** On `[1,1,2]` with `val = 1`: the first node is unlinked, then `prev` moves onto it anyway, a node no longer in the list, and the next `prev.next = cur.next` edits that detached node. The second `1` survives. **Consecutive deletions are the input that catches it; a single deletion passes.**

### The one-pointer form

Once the dummy exists you often don't need `prev` at all, because the dummy lets you look **ahead** from a single cursor:

```python
cur = dummy
while cur.next:                       # safe: dummy is never None
    if cur.next.val == val:
        cur.next = cur.next.next      # delete the node AHEAD; don't advance
    else:
        cur = cur.next                # keep it; advance
return dummy.next
```

Same algorithm, one pointer, and the "don't advance after a delete" asymmetry is now *structural*: the `else` makes it impossible to get wrong. **Prefer this shape.** It also shows why `while cur.next` and not `while cur`: the body edits the link ahead of `cur`, so `cur` must always be a real node with a link ahead to inspect.

```compare
title: Dummy head: two pointers or one
option: Two pointers: prev and cur
  Setup: `dummy = ListNode(0, head)`, `prev = dummy`, `cur = head`
  Loop test: `while cur:`
  On a match: `prev.next = cur.next`, and `prev` stays put
  On a keep: `prev = cur`
  Return: `dummy.next`
option: One pointer: look ahead
  Setup: `dummy = ListNode(0, head)`, `cur = dummy`
  Loop test: `while cur.next:`
  On a match: `cur.next = cur.next.next`, and `cur` stays put
  On a keep: `cur = cur.next`
  Return: `dummy.next`
```

### When to reach for it

> **If the problem can modify the front of the list, start with a dummy. One line, no thought required.**

Deletion, insertion, merging, partitioning, building any new list, reversing a *part* of a list. The cost is one node. The benefit is that a whole class of edge case stops existing, and *a special case you can design away beats a special case you handle*.

**Complexity:** *"O(n) time, one pass. O(1) space: I allocate one node, and one node does not grow with n."*

---

## In-place reversal

The single most important loop in the topic. Reversing in groups, checking a palindrome, reordering a list, and half the follow-ups are this loop with a wrapper. This section gives you the invariant and the questions that derive the loop, and leaves the code to you.

### Derive it, don't memorise it

The job: make every `.next` point at its predecessor instead of its successor.

Start with the obvious two-pointer attempt and watch it fail:

```python
while cur:
    cur.next = prev        # rewire
    cur = cur.next         # ✗ cur.next is now `prev`. You just walked BACKWARDS.
```

The second line reads the field the first line destroyed. **That is §0.5's rewiring rule firing: the moment you overwrite `cur.next`, the rest of the list is unreachable unless something else points at it.** Nothing else points at it. The remainder of the list is gone.

So: **save it first.** The third pointer is not cleverness, it's the direct consequence.

**And flip the link *behind* you, not the link ahead of you.** `cur.next = prev` points the current node back at the one you came from. Pointing the next node back at the current one destroys the link you need to advance with, *and* never terminates the original head.

### The invariant, and the order it forces

> **The invariant: `prev` is the head of the already-reversed prefix. `cur` is the head of the not-yet-touched suffix. The two are not connected.**

```
        reversed                    untouched
None ◄── [1] ◄── [2]        [3] ──► [4] ──► None
                  ↑           ↑
                prev         cur
```

The form for this topic, said before you write the body: *"`prev` is \_\_\_, `cur` is \_\_\_, `nxt` is \_\_\_, at the top of every iteration."* Then the two obligations: **is it true before the first pass, and does the body leave it true?**

The body has three jobs: **save** the link ahead of `cur`, **rewire** `cur` to point back, and **advance** both `prev` and `cur` by one node. The invariant forces their order. For each pair of lines, ask: *if these two swap, which name reads a value that the other line already destroyed or moved?* Work it out against the drawing, not from memory.

The mnemonic, once you've derived the order yourself: **save, rewire, advance, advance.**

**Before iteration 1**, what must `prev` hold so the invariant is already true? Nothing has been reversed yet, and the original head will end as the tail. If your answer is a node, check whether that node now sits in both halves at once, and where the old head's `.next` ends up (see [bug-checklist.md](../reference/bug-checklist.md#bounds-or-state-that-cant-express-the-answer), §Bounds or state that can't express the answer).

### What to return, and the cases that need no guard

Read the exit off the invariant: when the loop ends, the untouched suffix is empty. Three names are still in scope, `cur`, `prev` and `head`. **For each, say where it stands at exit. Which of the three is the new head?**

⚠️ **The tempting answer is `head`, because it's the name you were given.** Say which node it points at after the loop before you return it. Returning a name the loop has moved past is a silent wrong answer, the same shape as returning `head` from a deletion (see [bug-checklist.md](../reference/bug-checklist.md#stale-names-after-a-structural-edit), §Stale names after a structural edit).

**Trace it on two nodes, `[1,2]`, redrawing the arrows after each iteration.** Two nodes is the size that catches a loop that stops one node early: with `while cur.next`, the last arrow never flips. Then check the two degenerate cases, which a correct loop handles with no special-casing:

- `head = None`: the loop never runs, and the name you return must hold `None`.
- One node: one iteration, and that node's `.next` must end as `None`.

> **No guards needed. Check that before you write one**: a guard defending a state the loop already handles is dead or wrong (see [bug-checklist.md](../reference/bug-checklist.md#guards-copied-from-another-problem), §Guards copied from another problem).

```steps
title: Check your trace: reverse 1, 2, 3, 4 in place
array: 1→2 2→3 3→4 4→∅
- prev=4 cur=0 | Each cell is a node and the node its `.next` points at. `prev` starts as `None`, drawn as the ghost cell past the end. `cur` is the head.
- prev=4 cur=0 nxt=1 array=[1→∅, 2→3, 3→4, 4→∅] | Save `nxt = cur.next`, which is 2. Then rewire: `cur.next = prev` points 1 at `None`. The old head now ends the list.
- prev=0 cur=1 array=[1→∅, 2→3, 3→4, 4→∅] | Advance both: `prev = cur` is node 1, `cur = nxt` is node 2.
- prev=0 cur=1 nxt=2 array=[1→∅, 2→1, 3→4, 4→∅] | Save 3. Rewire: 2 now points back at 1.
- prev=1 cur=2 array=[1→∅, 2→1, 3→4, 4→∅] | Advance. The reversed prefix is 2, 1. The untouched suffix is 3, 4.
- prev=1 cur=2 nxt=3 array=[1→∅, 2→1, 3→2, 4→∅] | Save 4. Rewire: 3 now points back at 2.
- prev=2 cur=3 array=[1→∅, 2→1, 3→2, 4→∅] | Advance.
- prev=2 cur=3 nxt=4 array=[1→∅, 2→1, 3→2, 4→3] | Save `None`, drawn as the ghost cell. Rewire: 4 now points back at 3.
- prev=3 cur=4 array=[1→∅, 2→1, 3→2, 4→3] | Advance. `cur` is `None`, so the loop ends. `prev` is the last node reached, node 4, and it is the new head. Return `prev`, not `head`.
```

### Reversing part of a list

The generalisation you need for reversing in groups. Same loop, two changes:

- **Stop early:** `for _ in range(k)` instead of `while cur`, or `while cur is not stop_node`.
- **Reconnect both ends.** Reversing a part of a list leaves you holding four nodes that all need rewiring: the node before the part, the part's old head (now its tail), the part's old tail (now its head), and the node after the part.

> **The mistake is reversing correctly and reattaching wrongly.** Before you reverse, write down the names of all four boundary nodes, *including the two outside the part*, because the reversal destroys your way of finding them afterwards.

**Complexity of the whole family:** *"O(n) time: each node's `.next` is written exactly once. O(1) space: three pointers, and three is three no matter how long the list is."*

---

## Two pointers on a list

[03-two-pointers-sliding-window.md](03-two-pointers-sliding-window.md) gave you two shapes: **converging** and **window**. On a list, converging is impossible (§0.1), so what survives is the *same-direction* pair, and it splits into exactly two forms.

| Form | Setup | Answers |
|---|---|---|
| **Fixed gap** | one pointer starts *k ahead*, then both move at speed 1 | "the k-th from the end", "the node before the k-th from the end" |
| **Different speeds** | both start together, one moves 2 links per step | "the middle", "is there a cycle", "where does the cycle start" |

> **Both are the same idea: a second pointer whose position encodes information you cannot compute.** You can't compute "n − k" without knowing n, and you can't know n without a pass. So instead of computing it, you *arrange* for a pointer to be there.

### The fixed gap

**Worked on [LC 1721 Swapping Nodes in a Linked List](https://leetcode.com/problems/swapping-nodes-in-a-linked-list/)**, which is not in the drill set. *Swap the values of the k-th node from the start and the k-th node from the end.*

The k-th from the start is a walk. The k-th from the end is the interesting half:

> **If `runner` is exactly `k−1` links ahead of `second`, then when `runner` is standing on the last node, `second` is standing on the k-th node from the end.**

That sentence is the invariant, and it is also the proof. Nothing else is needed.

```python
def swapNodes(self, head, k):
    first = head
    for _ in range(k - 1):            # k-th from the start: walk k-1 links
        first = first.next

    second, runner = head, first      # the gap is now exactly k-1 links
    while runner.next:                # stop ON the last node
        second = second.next
        runner = runner.next

    first.val, second.val = second.val, first.val
    return head
```

**Why the gap is set up by *reusing* `first`:** it is already `k−1` links from the head, which is exactly the gap wanted. No second walk, no arithmetic. (And this problem swaps **values**, not nodes: read the statement. Swapping nodes is a harder rewiring job, and problems that want it say so.)

**Three things to get right, and they're where the bugs are:**

| Decision | Why |
|---|---|
| `range(k - 1)`, not `range(k)` | The k-th node is `k−1` **links** from the head. The off-by-one lives in the word "th" |
| `while runner.next`, not `while runner` | You want `runner` to stop **on** the tail, not past it. `while runner` overshoots by one and `second` lands one too far |
| The gap is `k−1` **links**, not `k` nodes | Count edges, not nodes (see [bug-checklist.md](../reference/bug-checklist.md#off-by-ones-derive-never-freehand), §Off-by-ones: derive, never freehand) |

**Opening the gap proves nothing; sliding it is what does the work.** A pointer walked `k` ahead and never followed is still "k from the front". Half a technique is not a partial answer, it's a different algorithm.

> ⚠️ **When the target is a node you want to DELETE, the gap has to be one larger**, because deletion needs the *predecessor*. How do you get one more link for free, instead of as arithmetic you have to get right?

### Different speeds: the middle

**Worked on [LC 876 Middle of the Linked List](https://leetcode.com/problems/middle-of-the-linked-list/)**, which is not in the drill set.

> **If `fast` moves twice as far as `slow`, then when `fast` has covered the whole list, `slow` has covered half of it.** One pass, no length computed, O(1) space.

```python
slow = fast = head
while fast and fast.next:
    slow = slow.next
    fast = fast.next.next
return slow
```

**`while fast and fast.next` is doing two different jobs**, and you need both:

- `fast` handles the **even**-length exit: `fast` steps past the end to `None`, and reading `fast.next` would crash.
- `fast.next` handles the **odd**-length exit: `fast` lands exactly on the last node, `fast.next` is `None`, stop.

Written in the other order, `while fast.next and fast`, it raises `AttributeError` as soon as `fast` is `None`. **Short-circuit order is the guard.**

### Which middle? Trace both parities

| List | `slow` ends on | |
|---|---|---|
| `[1,2,3]` | **2** | the middle, unambiguous |
| `[1,2,3,4]` | **3** | the **second** of the two middles |
| `[1,2]` | **2** | the second node |
| `[1]` | **1** | the loop never runs |

```steps
title: Which middle? Trace both parities
array: 1 2 3
- slow=0 fast=0 | List `[1,2,3]`, odd length. The loop is `while fast and fast.next`. Both pointers start on the head.
- slow=1 fast=2 | `fast` and `fast.next` both exist, so the body runs: `slow` moves one node, `fast` moves two.
- slow=1 fast=2 | `fast` is the last node and `fast.next` is `None`, so the loop stops. `slow` is on 2, the middle.
- slow=0 fast=0 array=[1, 2, 3, 4] | Now the even list `[1,2,3,4]`. Both pointers start on the head.
- slow=1 fast=2 | The body runs once: `slow` is on 2, `fast` is on 3.
- slow=2 fast=4 | The body runs again: `slow` is on 3, `fast` steps past the end to `None`, the ghost cell.
- slow=2 fast=4 | `fast` is `None`, so the loop stops. `slow` is on 3, the upper of the two middles.
```

**On an even list there are two middles, and this loop gives you the upper one.** Problems disagree about which they want, and the difference is invisible until you trace `[1,2,3,4]`.

**To get the *lower* middle**, which is what you want when you need "the last node of the first half", i.e. every problem that splits a list in two:

```python
while fast.next and fast.next.next:    # ✓ slow ends on the LAST node of the first half
    slow = slow.next
    fast = fast.next.next
```

`[1,2,3,4]` → `slow` = 2. `[1,2,3]` → `slow` = 2. Then `slow.next` is the head of the second half, and `slow.next = None` cleanly severs them.

⚠️ **This form dereferences `fast.next` immediately, so it dies on the empty list.** The first form survives it. **Pick by which one the problem needs, then check it against `head = None`. Don't assume.**

> **This is the same choice as `hi = len(nums)` against `hi = len(nums) - 1` in [04-binary-search.md](04-binary-search.md).** Two loops that look identical, differing in which boundary they can express, and choosing wrong is a silent off-by-one. **Say which middle you want before you write the condition.**

---

## Floyd's cycle detection

The O(1)-space follow-up to "does this list have a cycle?", and the second half of §Different speeds: the middle. It is worth knowing cold, because it's a named algorithm and most interviewers ask for it by name: *"Floyd's tortoise and hare"*.

### The question and the two answers

**"Does following `next` from here ever repeat?"**

**The O(n) answer, and it's a perfectly good first answer:** walk the list, put every node in a `set`, and you have a cycle the first time you see one twice. Say it out loud with its complexity, *then* say *"the follow-up is going to be O(1) space, and there's a pointer trick for that."* Giving the brute force and its cost first is the expected opening, not a failure; the follow-up is a cue for a second gear, not a correction.

**The O(1) answer:**

> **Put two runners on a track, one at twice the speed. If the track is a straight line, the fast one falls off the end. If it loops, the fast one laps the slow one and they collide.** There is no third possibility.

**The two exits are the proof of correctness, one sentence each:**

- **Fell out of the loop** → `fast` reached a `None`. A `None` is an end, and **a cycle has no end**, so there isn't one.
- **They met** → the faster runner came back round. On a straight track, ahead stays ahead. **You can only be lapped on a loop.**

⚠️ **Where the test goes.** The identity test must come **after** both moves. `slow` and `fast` start on the same node, so a test before the moves sees them equal at step zero, and every list of two or more nodes reports a cycle. The test asks *"has fast caught up?"*, and at step zero it hasn't moved.

### Why they must meet, and why speed 2

Once both pointers are inside the cycle, `fast` gains **exactly one link per step** on `slow`. A gap that shrinks by exactly 1 can never jump over 0, so within at most C steps (C = the cycle's length) the gap is 0 and they're on the same node.

> **Speed 2 is the only speed where the gap closes by exactly 1, which is the only speed where "they meet" needs no argument about skipping past each other.** With speed 3 the gap closes by 2, and whether they land on the same node depends on parity. It still works, but you'd have to argue it. Don't; use 2.

### Phase 2: where does the cycle *start*?

This is the part people don't know, and it is what any problem asking for the entrance needs.

**Draw this before you write a line of code.** The shape is a **ρ**, a straight run into a loop, and it needs three labels, every one of them a distance you never compute:

```
                       C − X
             ┌──────────────────────►  M
             │                         │
   P         │                         │
head ──►──► (E)                        │   ⎫
             ▲                         │   ⎬  X
             │                         ▼   ⎭
             └────────────◄────────────┘

   P     = links from head to the entrance E
   C     = length of the cycle
   M     = where slow and fast met in phase 1
   X     = links from M forward round to E          ⎫  X + (C − X) = C
   C − X = links from E forward to M                ⎭  the two arcs split the cycle
```

**The claim:**

> **Reset one pointer to the head, leave the other at the meeting point, and advance both one link at a time. They meet at the entrance to the cycle.**

**The proof is one equation, and you should know it.** Read the distances straight off the picture:

| pointer | path it walked to reach `M` | distance |
|---|---|---|
| `slow` | head → E → M | `P + C − X` |
| `fast` | head → E → M, **plus one whole lap** | `P + C − X + C` |

`fast` moves two links for every one of `slow`'s, so:

```
        2 * slow  =  fast
2 * (P + C − X)   =  P + C − X + C
   2P + 2C − 2X   =  P + 2C − X
          P − X   =  0
                            ⟹   P = X
```

> ⭐ **`P = X`. The walk from the head to the entrance is the same length as the walk from the meeting point round to the entrance.** Two pointers, same speed, same remaining distance: they land on `E` on the same step. You never compute `P`, `C` or `X`; you walk both and let them collide.

⚠️ **The "plus one whole lap" is the one assumption.** With a long straight run, `fast` can lap `k` times, and the algebra gives `P = (k − 1)·C + X` instead. Same conclusion: the extra `(k − 1)` laps are whole laps, and a whole lap from `E` returns to `E`, so the collision point is unchanged. Say *"fast is some whole number of laps ahead"* if you're pushed on it.

⚠️ **Phase 2 uses speed 1 for both pointers.** Leaving `fast` at speed 2 is the standard wrong answer, and it lands somewhere arbitrary in the cycle.

**Complexity:** *"O(n) time: phase 1 is at most a full pass plus one lap, phase 2 is at most one more pass. O(1) space: a few pointers, none of which grows with n."*

### Floyd without a list: Happy Number

**Worked on [LC 202 Happy Number](https://leetcode.com/problems/happy-number/)**, which is not in the drill set, and is not a linked list. That's the point. *Repeatedly replace n by the sum of the squares of its digits. Does it reach 1?*

> **There is a linked list here and nobody drew it.** The node is a number. `next(x)` is "the sum of the squares of x's digits". The sequence either reaches 1 (a self-loop, `1 → 1`) or falls into some other cycle forever.

**"Does this sequence repeat?" is a cycle-detection question**, so Floyd applies with no list in sight:

```python
def isHappy(self, n):
    def nxt(x):
        return sum(int(d) ** 2 for d in str(x))

    slow, fast = n, nxt(n)
    while fast != 1 and slow != fast:
        slow = nxt(slow)
        fast = nxt(nxt(fast))
    return fast == 1
```

Two exits, and each answers the question: `fast == 1` → happy. `slow == fast` with `fast != 1` → it's in a cycle that doesn't contain 1 → not happy. (`fast` starts one step ahead, so the two don't begin equal and the loop header can test them.)

**Note `!=` and not `is` here**: these are *integers*, compared by value. Small ints are cached in CPython, so `is` would often work, and that is exactly the kind of accident that fails on a large input. `is` is for nodes; `==` is for values.

> **The generalisation worth carrying:** *"a function you apply repeatedly to a finite set of states is a linked list, and it always eventually repeats."* You'll see the same move later, in module 08, as a graph whose neighbours are generated rather than stored. §The implicit list turns that sentence into a checklist you can run on a problem statement.

### The implicit list: when an array *is* a linked list

> **You do not need `ListNode` to have a linked list. You need a set of states and a function that maps each state to exactly one next state.** That's it. `next` can be a field, a formula, an array lookup or a digit computation: the two-pointer and Floyd algorithms never ask where it came from.

**The three conditions, and you must check all three:**

| Condition | What it buys | What breaks without it |
|---|---|---|
| **1. `next` is total**: defined for every state you can reach | the walk **never stops**, so there's no `None` case | you have an ordinary list with an end, and Floyd's `None` checks come back |
| **2. `next` is deterministic**: exactly one successor per state | it's a *list*, not a branching structure | with branching, two pointers no longer apply; you'll see those traversals later, in modules 06 and 08 |
| **3. The state space is finite** | by pigeonhole the walk **must** revisit a state: a cycle is **guaranteed**, not just possible | the walk can run forever without repeating, and Floyd never stops |

Conditions 1 and 3 together are the engine: **a total function on a finite set, applied over and over, always cycles.** You get a ρ for free and you never wrote a node.

⚠️ **A fourth condition is needed only for phase 2** (finding the cycle's *entrance*): **the start state must not be inside the cycle.** If it is, there's no straight run and `P = 0`: both phases return the start state itself, and the start has only one arrow into it from reachable states, so the "two arrows in" reading below fails. Prove the start is outside the cycle from the constraints. It is the step people skip.

⚠️ **On an implicit list, `slow` and `fast` usually both start on the same state**, so a loop header `while slow != fast:` exits before the first move. It is the "test after the moves" rule from §The question and the two answers in a different costume. §Floyd without a list dodges it another way, by starting `fast` one step ahead. That is fine for phase 1, but it shifts the meeting point by one link, so phase 2's `P = X` no longer holds as written. If you need the entrance, account for the offset.

**Reading a problem for it:**

| The statement says | The implicit list is |
|---|---|
| the values are **valid indices into their own array** | `i → nums[i]` |
| "repeatedly apply this transformation to a number" | `x → f(x)` (§Floyd without a list) |
| a state machine, a hash chain, a permutation, a `parent[]` array | `s → step(s)` |
| "does this eventually repeat / loop / stabilise" | anything: **"repeat" is the tell**, not "list" |

> ⭐ **The name for this object is a *functional graph*: every node has exactly one way out.** The part reachable from any one start is a ρ: a chain running into a single cycle. Say "functional graph" and you have said, in two words, why Floyd applies.

**What the entrance *means*.** This is the half people skip, and it is the half that turns "Floyd applies" into an answer.

> **The entrance `E` is the only node with two or more arrows into it from reachable nodes.** It is reached once from the straight run and once from inside the cycle. So whatever "two states lead to the same state" means *in your problem's language* is what the entrance is.

| The list | arrows into node `v` = | so the entrance is |
|---|---|---|
| `x → f(x)` for any `f` | how many reachable states `f` sends to `v` | the first collision of `f`: the first value reached from two different places |

For an array read as `i → nums[i]`, ask the same question: what does "two slots send you to `v`" say about the array?

---

## Building a new list: dummy and tail

**Worked on [LC 86 Partition List](https://leetcode.com/problems/partition-list/)**, which is not in the drill set. *Reorder the list so that all nodes with value `< x` come before all nodes `>= x`, keeping the original order within each group.*

### The append skeleton

Every "produce a list" problem is this shape, and it's four lines:

```python
dummy = tail = ListNode()      # two names, ONE node: §0.5, primitive 2, used deliberately
...
tail.next = node               # attach
tail = node                    # tail is the last node again
...
return dummy.next              # dummy never moved, so it still holds the front
```

> **`dummy` is the bookmark and `tail` is the cursor.** They start on the same object; `tail` walks away and `dummy` doesn't. That is the aliasing rule being *used* rather than being a bug.

**Why `tail`, and not "find the end each time":** finding the tail is an O(n) walk, and doing it once per node is the hidden quadratic from §0.4. **Carry it.**

### Two builders, one join

Partition is two of these skeletons running at once:

```python
def partition(self, head, x):
    before = before_tail = ListNode()
    after  = after_tail  = ListNode()

    cur = head
    while cur:
        if cur.val < x:
            before_tail.next = cur
            before_tail = cur
        else:
            after_tail.next = cur
            after_tail = cur
        cur = cur.next

    after_tail.next = None              # ⚠️ THE LINE. See below.
    before_tail.next = after.next       # join: the second list hangs off the first
    return before.next
```

**The invariant:** *"`before` holds every node seen so far with value `< x`, in order, and `before_tail` is its last node. `after` holds the rest, the same way. `cur` is the node being classified. No node is in both."*

**⚠️ `after_tail.next = None` is the whole lesson of this section.** The nodes are **reused, not copied**. Every node still carries whatever `.next` it had in the original list, and you only overwrite the ones you explicitly reattach. The last node of `after` was, in the original list, pointing at some node that has since moved into `before`.

**Trace `[1,4,3,2,5,2]` with `x = 3`:** `before` = 1→2→2, `after` = 4→3→5. But node `5`'s `.next` was never rewritten, and in the original list node 5 pointed at the final `2`, which is now `before_tail`. So without the line, the joined list runs `1→2→2→4→3→5→2→4→3→5→2→…` **forever.**

> **A stale `.next` is a cycle, and a cycle is a hang, not a crash.** The list looks correct for its first six nodes. Every test that only checks the first few values passes.
>
> **The rule: when you build a list out of existing nodes, set the last node's `.next` explicitly. Every time.** It is one line, it is at the end, and it is the most-forgotten line in this topic.

**Complexity:** *"O(n) time, one pass. O(1) space: I allocate two dummy nodes and reuse every real node; nothing I allocate grows with n."*

### Merging two sorted lists

The same skeleton, one decision different. It is in the drill set, so here are the decisions and not the code.

**The difference from partition:** there, the question at each step was *"which output list does this node join?"* In a merge it is *"which input list does the next node come from?"* Answer it by comparing the two current heads, and advance **only the list you took from**.

Two things to decide before you write it:

- **The loop condition.** While can you still compare? What must exist for the comparison to be safe?
- **The leftover.** When the loop exits, one input still holds a whole sorted remainder. **Do you need to walk it?** Splicing is O(1): one assignment attaches the entire remainder. That is something an array cannot do, and it's worth saying out loud.

> **This is the merge step of merge sort.** Concatenating two sorted halves is not merging them: on lists, the concatenation is the last line, not the algorithm.

---

## Replacing a hash set: the five escapes

> **"Can you do it in O(1) space?" means: something other than memory has to do the remembering.**

| The O(n) memory | What replaces it | Cost |
|---|---|---|
| a set of seen **nodes** | **two pointers at different speeds** | nothing: still O(n) time |
| a set of seen **values** | **sort first**, so duplicates become adjacent | O(n log n) time |
| a set or a count array | **mutate the input as the mark** | destroys the input |
| a set of what's needed | **arithmetic**: a sum formula, XOR | needs constrained values |
| a set of seen characters | **a bitmask in one int** | needs a small alphabet |

**On a linked list it collapses to pointers**, because sorting is expensive, arithmetic needs indices, a bitmask needs a small domain, and mutating destroys the thing being asked about. **Know why it collapses**, so the rule doesn't get carried into an array problem where sorting was the answer.

This is Remember against Order and Reuse from [01-arrays-hashing.md](01-arrays-hashing.md), one level up: a hash set is Remember, O(n), and the O(1)-space follow-up asks you to convert it into a Reuse or an Order. The question that finds the conversion:

> ***"What does the structure already know, that makes remembering unnecessary?"***

For cycles: the list **loops**. The structure is the memory.

---

## How to attack a linked-list problem

1. **Name the pattern and the signal that pointed to it** (§0.8), before writing code.
2. **Read the stub.** `ListNode`? `Node`? Is there a `.random` or a `.child`?
3. **Draw the list.** Four nodes and arrows, on paper. Ten seconds.
4. ⭐ **Say what every pointer points to at the top of the loop**, in one sentence, *before* the body. Check it's true before iteration 1, and that each branch of the body leaves it true.
5. **Can the front of the list change?** Then a dummy, one line, reflexively.
6. **Are you walking or editing?** `cur = cur.next` moves your finger; `cur.next = x` moves a link. Say which each line is.
7. **Which name will still mean "the front" at the end?** Decide the return before you write the loop.
8. Write it. **Save, rewire, advance, advance** wherever anything is being reversed.
9. **Guards left to right, in dereference order**: `while fast and fast.next`.
10. Run [bug-checklist.md](../reference/bug-checklist.md#the-30-second-pass), §The 30-second pass. Then the table in §Common linked-list mistakes. Then: **for every variable you assigned, where is it read?**
11. **Trace the degenerate cases, not the happy path:** `None` · one node · **two nodes** · the head · the tail. Redraw the arrows; don't tabulate values.
12. **Say the complexity in the template, unprompted**: time and space, each with the reason. If you recursed, say it's O(n) space.

---

## Common linked-list mistakes

Ordered by how often each happens.

| Mistake | What you see | Entry |
|---|---|---|
| `cur.next.next` or `fast.next.next` with no guard on the link it crosses | `AttributeError: 'NoneType' object has no attribute 'next'` | [bug-checklist.md](../reference/bug-checklist.md#the-guard-asymmetry), §The guard asymmetry |
| Node vs value vs `.next`: `seen.add(cur.val)` when the question was about nodes, `tail = cur.val` | a cycle reported on `[1,1]`, or `int` has no attribute `next` | [bug-checklist.md](../reference/bug-checklist.md#node-vs-value-vs-next), §Node vs value vs `.next` |
| Rewired before saving | the rest of the list vanishes; a reversal returns one node | §0.5, primitive 2 |
| `return head` after the front moved | a silent wrong answer: a list starting at a deleted node, or at the new tail | [bug-checklist.md](../reference/bug-checklist.md#stale-names-after-a-structural-edit), §Stale names after a structural edit |
| A dummy named after its role in the loop (`slow = ListNode(0, head)`) | no name in scope means "the front", so the return points somewhere wrong | [bug-checklist.md](../reference/bug-checklist.md#names-that-describe-arrival-order-not-role), §Names that describe arrival order, not role |
| `prev = head` before a reversal | the invariant is false before iteration 1; the old head never ends up pointing at `None` | [bug-checklist.md](../reference/bug-checklist.md#bounds-or-state-that-cant-express-the-answer), §Bounds or state that can't express the answer |
| A reversal written without saying the invariant | works on three nodes, wrong on two | §In-place reversal |
| A stale `.next` on the last node of a rebuilt list | **a cycle, so an infinite loop.** The first few values look right | §Two builders, one join |
| The equality test before the moves | every list of two or more nodes reports a cycle, or an implicit-list loop exits before it starts | §The question and the two answers |
| `prev` advanced unconditionally during a deletion | consecutive matches survive; `[1,1,2]` catches it | §The code, and the invariant |
| An off-by-one in the gap | the k-th from the end is one node out | [bug-checklist.md](../reference/bug-checklist.md#off-by-ones-derive-never-freehand), §Off-by-ones: derive, never freehand |
| The gap opened and never slid | the n-th node **from the start** is deleted | §The fixed gap |
| The wrong middle | an even-length list splits one node off | §Which middle? Trace both parities |
| `fast = head.next` inside the loop, where `fast = fast.next` was meant | `fast` never moves on | [bug-checklist.md](../reference/bug-checklist.md#typos-that-silently-change-meaning), §Typos that silently change meaning |
| `x in seen` with `seen` a Python list | correct output, O(n²) time | §0.4 |
| Phase 2 of Floyd at speed 2 | an arbitrary node inside the cycle | §Phase 2: where does the cycle *start*? |
| Phase 2 on an implicit list without proving the start is outside the cycle | it returns the start state, not a collision; no crash, and small tests may pass | §The implicit list |
| Recursion on a long list | `RecursionError` at about 1,000 frames | §0.7 |
| Copied into a Python list and solved as an array | correct, O(n) space, and it discards the point of the problem | §0.7. Fine as a *stated* first pass; then do it with pointers |
| Dead code: a `length` computed and never read, a `prev` carried and never used | nothing visible; the reader stops trusting the rest | [bug-checklist.md](../reference/bug-checklist.md#dead-code), §Dead code |
| Both arms of an `if/else` assign the same node | four lines that choose nothing | [bug-checklist.md](../reference/bug-checklist.md#dead-branching-both-arms-assign-the-same-value), §Dead branching: both arms assign the same value |
| The same loop copied for each of two input lists | a fix that must be applied twice, and gets applied once | [bug-checklist.md](../reference/bug-checklist.md#copy-paste-replicates-the-defect), §Copy-paste replicates the defect |
| A guard from the last problem: `if not head: return None` in front of a loop that already handles it | dead code, or a wrong answer | [bug-checklist.md](../reference/bug-checklist.md#guards-copied-from-another-problem), §Guards copied from another problem |
| Complexity not stated, or space undersold | "only a few variables" | §0.7: *"O(1) space: nothing I allocate grows with n"* |

---

## Not covered in this module

**Doubly linked lists**: a `.prev` field as well as `.next`. It makes deletion O(1) *given the node*, with no predecessor hunt, which is exactly why a least-recently-used cache needs one. The cost is two links to maintain per edit instead of one, so every rewiring is four assignments rather than two. The LRU Cache row of the drill set is where you'll meet it. It's a **design** problem, and the pairing to know is **a doubly linked list for O(1) reordering plus a hash map for O(1) lookup**.

**Sorting a linked list** ([LC 148 Sort List](https://leetcode.com/problems/sort-list/)): merge sort, using the lower middle (§Which middle?) to split and the merge (§Merging two sorted lists) to combine. O(n log n) time, O(log n) stack when written recursively.

**Also unwritten:** skip lists · circular lists as a deliberate structure · XOR linked lists (trivia) · flattening a multilevel list (LC 430) · the intersection of two lists (LC 160, a neat two-pointer trick) · reversing between two positions (LC 92, which is §Reversing part of a list written out).

---

## Drill set — cold, no IDE, no running

**Solutions are not in this file.** Every shape you need is in §0 and the sections above, taught on other problems.

The NeetCode 150 linked-list problems (11), reordered so each one adds one new thing to the one before.

| # | Problem | Focus |
|---|---|---|
| 1 | [Reverse Linked List](https://leetcode.com/problems/reverse-linked-list/) (LC 206) | §In-place reversal. **The canonical one.** Say the invariant before the body, then read the return off it. ⚑ **Checkpoint** |
| 2 | [Merge Two Sorted Lists](https://leetcode.com/problems/merge-two-sorted-lists/) (LC 21) | §Merging two sorted lists. Dummy and tail, and the O(1) leftover splice |
| 3 | [Linked List Cycle](https://leetcode.com/problems/linked-list-cycle/) (LC 141) | §Floyd's cycle detection, phase 1. Give the hash-set version and its complexity **first**, then the O(1) one |
| 4 | [Remove Nth Node From End of List](https://leetcode.com/problems/remove-nth-node-from-end-of-list/) (LC 19) | §The dummy head and §The fixed gap. **The gap and the dummy together**: deleting needs the predecessor. ⚑ **Checkpoint** |
| 5 | [Add Two Numbers](https://leetcode.com/problems/add-two-numbers/) (LC 2) | §The append skeleton, with a carry. The trap is the **final carry** after both lists end |
| 6 | [Reorder List](https://leetcode.com/problems/reorder-list/) (LC 143) | **The composite.** Find the middle, sever it, reverse the second half, interleave. Three techniques, one problem |
| 7 | [Copy List with Random Pointer](https://leetcode.com/problems/copy-list-with-random-pointer/) (LC 138) | §0.6. **A dict from old node to new node is also the visited set.** A second structure for the same job is a bug |
| 8 | [Find the Duplicate Number](https://leetcode.com/problems/find-the-duplicate-number/) (LC 287) | §Phase 2 and §The implicit list. Floyd on an implicit list, both phases. Check all four conditions against the constraints, and say what "two arrows into `v`" means for this array |
| 9 | [LRU Cache](https://leetcode.com/problems/lru-cache/) (LC 146) | §Not covered in this module. **Design.** A doubly linked list plus a dict. The hard part is the bookkeeping, not the idea |
| 10 | [Merge k Sorted Lists](https://leetcode.com/problems/merge-k-sorted-lists/) (LC 23) | §Merging two sorted lists plus `heapq` ([python-toolkit.md](../reference/python-toolkit.md#4-heapq-the-min-heap), §4. `heapq`: the min-heap; you'll see heaps in full later, in module 10). A heap of the k current heads, or merge in pairs. **Say both complexities** |
| 11 | [Reverse Nodes in k-Group](https://leetcode.com/problems/reverse-nodes-in-k-group/) (LC 25) | §Reversing part of a list. **The hardest in the set.** Reversal of a part plus reattaching four boundary nodes, over and over |

**The order.** Reverse and merge come first. The cycle check sits at row 3 so Floyd is in your hands before row 8 needs both of its phases, and Reorder List sits at row 6 because it is the middle, a reversal and an interleave you already have: the payoff, not a new technique. LRU Cache and Merge K sit late because they're a design problem and a heap problem that happen to contain lists.

**⚑ Checkpoint at row 1.** Every other problem in the set is built out of it. If it doesn't come out clean, stop there and reread §In-place reversal and §0.5, primitive 2, rather than pushing on.

**⚑ Checkpoint at row 4.** The dummy and the gap together is where two primitives meet. If it doesn't come out clean, do row 5 before moving on, and reread §The dummy head and §The fixed gap.

**Spares, if a shape needs a second rep:** [LC 234 Palindrome Linked List](https://leetcode.com/problems/palindrome-linked-list/) (middle plus reversal: the cleanest second rep of row 6's machinery) · [LC 160 Intersection of Two Linked Lists](https://leetcode.com/problems/intersection-of-two-linked-lists/) (a two-pointer trick worth seeing) · [LC 142 Linked List Cycle II](https://leetcode.com/problems/linked-list-cycle-ii/) (Floyd phase 2, undisguised) · [LC 92 Reverse Linked List II](https://leetcode.com/problems/reverse-linked-list-ii/) (§Reversing part of a list, as a warm-up for row 11) · [LC 148 Sort List](https://leetcode.com/problems/sort-list/) (§Not covered in this module) · [LC 328 Odd Even Linked List](https://leetcode.com/problems/odd-even-linked-list/) (two builders, like §Two builders, one join).

*Solved in the sections above, so from memory only:* [LC 203](https://leetcode.com/problems/remove-linked-list-elements/) · [LC 876](https://leetcode.com/problems/middle-of-the-linked-list/) · [LC 1721](https://leetcode.com/problems/swapping-nodes-in-a-linked-list/) · [LC 86](https://leetcode.com/problems/partition-list/) · [LC 202](https://leetcode.com/problems/happy-number/).

## Before you submit anything

Run [bug-checklist.md](../reference/bug-checklist.md#the-30-second-pass), §The 30-second pass, over your code. Thirty seconds. Then the table in §Common linked-list mistakes, and then, for every variable you assigned: where is it read?

---

## Self-check answers

1. **An array gives you O(1) random access and no pointers; a linked list gives you pointers and no random access.** The **same-direction** shape survives (a fixed gap, or two speeds), because it only ever moves forward. Converging pointers die because you can't walk backwards. Binary search dies because reaching the midpoint is an O(n) walk, so each probe costs O(n) and the log buys nothing.
2. `cur = cur.next` **rebinds your name**: it walks, and the list is unchanged. `cur.next = other` **rewrites a field of the list**: it edits, and the list is now a different list. Only the second changes the list.
3. `cur.next = new` destroys the only link to the rest of the list, so nothing points at it any more. Then `new.next = cur.next` reads the field you just overwrote, which is `new` itself: **`new` points at itself, a cycle**, and the rest of the list is lost. Save first, `new.next = cur.next`, then rewire, `cur.next = new`.
4. `while cur:` ends with **`cur = None`**; `while cur.next:` ends with **`cur` on the last node**. `while cur:` survives `head = None` (the loop doesn't run); `while cur.next:` raises `AttributeError` on its first test. **To unlink a node you must stand on its predecessor**, and a singly linked list gives you no way back. So deletion code either uses the look-ahead form (`cur.next.val`, `cur.next = cur.next.next`, under `while cur.next`) or carries a `prev` one node behind a `while cur:` walk.
5. Every node has a predecessor except the head, so without a dummy, deleting the head is a separate case, and it can happen repeatedly. **The dummy is an invented predecessor**, so the head becomes an ordinary node. Return `dummy.next` because deleting the first node doesn't update the name `head`: it still points at the removed node. `dummy.next` is always whatever is currently first.
6. `and` stops at the first falsy operand. In `fast and fast.next`, **`fast.next` is only read once `fast` is known not to be `None`**. In the reversed order, `fast.next` is read first, so when `fast` is `None` it raises `AttributeError`. Write guards left to right, in the order the attributes are dereferenced.
7. **O(n) space**: one stack frame per node, so about 5·10⁴ frames. Python's default recursion limit is about 1,000 frames, so it raises **`RecursionError`** on the real input. Write it iteratively, or at least say the space is O(n).
8. Both are **`False`**: `ListNode` doesn't override `__eq__` or `__hash__`, so `==` falls back to identity, and `a` and `b` are two different objects. A set of the two nodes has **two members**; a set of their values has **one**, because both values are `1`. Write `is` because you mean identity, and on a class that *does* define `__eq__`, `==` and `is` give different answers silently.
