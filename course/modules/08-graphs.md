# Module 08: Graphs

<!-- toc -->
**Contents**

- [0.1 Prerequisites and the one question](#01-prerequisites-and-the-one-question)
- [0.2 The structure and how it works](#02-the-structure-and-how-it-works)
  - [A tree promises; a graph withdraws the promises](#a-tree-promises-a-graph-withdraws-the-promises)
  - [Four consequences](#four-consequences)
  - [The diamond: why `visited` exists without a cycle](#the-diamond-why-visited-exists-without-a-cycle)
  - [The outer loop](#the-outer-loop)
  - [What transfers unchanged](#what-transfers-unchanged)
- [0.3 Vocabulary](#03-vocabulary)
- [0.4 Operations and their cost](#04-operations-and-their-cost)
- [0.5 The primitives](#05-the-primitives)
- [0.6 Inputs that break it](#06-inputs-that-break-it)
- [0.7 Complexity, out loud](#07-complexity-out-loud)
- [0.8 Signals](#08-signals)
- [0.9 Self-check](#09-self-check)
- [The visited set](#the-visited-set)
  - [Mark on push, or mark on pop?](#mark-on-push-or-mark-on-pop)
  - [Define it by a property, never by the route](#define-it-by-a-property-never-by-the-route)
  - [`visited` is not always a set](#visited-is-not-always-a-set)
- [Representation](#representation)
- [BFS and DFS on a graph](#bfs-and-dfs-on-a-graph)
  - [Why BFS never needs a relaxation test](#why-bfs-never-needs-a-relaxation-test)
  - [`return` inside the neighbour loop](#return-inside-the-neighbour-loop)
  - [Recursion depth is arithmetic](#recursion-depth-is-arithmetic)
  - [Why an explicit stack survives](#why-an-explicit-stack-survives)
  - [Each node once: the O(V + E) argument](#each-node-once-the-ov--e-argument)
- [Grids are graphs](#grids-are-graphs)
  - [The four-part guard, in that order](#the-four-part-guard-in-that-order)
  - [Marking by overwriting](#marking-by-overwriting)
- [Connected components](#connected-components)
  - [Worked: Number of Provinces (LC 547)](#worked-number-of-provinces-lc-547)
- [Flood fill and the guard order](#flood-fill-and-the-guard-order)
  - [Worked: Flood Fill (LC 733)](#worked-flood-fill-lc-733)
- [Shortest path in an unweighted graph](#shortest-path-in-an-unweighted-graph)
  - [Worked: Shortest Path in Binary Matrix (LC 1091)](#worked-shortest-path-in-binary-matrix-lc-1091)
- [Multi-source BFS](#multi-source-bfs)
- [The inversion: start from the special thing](#the-inversion-start-from-the-special-thing)
  - [The two shapes](#the-two-shapes)
  - [Worked: Number of Enclaves (LC 1020)](#worked-number-of-enclaves-lc-1020)
  - [Worked: Number of Closed Islands (LC 1254)](#worked-number-of-closed-islands-lc-1254)
- [Undirected cycles: carry the parent](#undirected-cycles-carry-the-parent)
- [Directed cycles: three colours](#directed-cycles-three-colours)
  - [GREY is the per-path mark, BLACK makes it permanent](#grey-is-the-per-path-mark-black-makes-it-permanent)
  - [The two-set form](#the-two-set-form)
  - [Reading the colours as an answer](#reading-the-colours-as-an-answer)
  - [Worked: Find Eventual Safe States (LC 802)](#worked-find-eventual-safe-states-lc-802)
  - [One start is never enough](#one-start-is-never-enough)
- [Topological sort](#topological-sort)
  - [Kahn's algorithm](#kahns-algorithm)
  - [The DFS form: post-order, reversed](#the-dfs-form-post-order-reversed)
  - [Choosing between the two](#choosing-between-the-two)
  - [Kahn's against BFS](#kahns-against-bfs)
  - [Peeling leaves](#peeling-leaves)
  - [Worked: Minimum Height Trees (LC 310)](#worked-minimum-height-trees-lc-310)
- [Union-find](#union-find)
  - [Worked: Number of Operations to Make Network Connected (LC 1319)](#worked-number-of-operations-to-make-network-connected-lc-1319)
  - [Union-find or DFS?](#union-find-or-dfs)
- [Weighted graphs: Dijkstra and Prim](#weighted-graphs-dijkstra-and-prim)
  - [The claim weights withdraw](#the-claim-weights-withdraw)
  - [Dijkstra](#dijkstra)
  - [`done` is not a cycle guard](#done-is-not-a-cycle-guard)
  - [Prim is Dijkstra with one line changed](#prim-is-dijkstra-with-one-line-changed)
- [Every template, in one place](#every-template-in-one-place)
- [How to attack a graph problem](#how-to-attack-a-graph-problem)
- [In depth](#in-depth)
  - [Four ideas on the way to Dijkstra](#four-ideas-on-the-way-to-dijkstra)
  - [Why the relaxation DFS is exponential](#why-the-relaxation-dfs-is-exponential)
  - [Where the guards go in the two-set form](#where-the-guards-go-in-the-two-set-form)
  - [The lexicographically smallest order](#the-lexicographically-smallest-order)
  - [Proving a traversal optimal](#proving-a-traversal-optimal)
  - [Stacked special cases mean the structure dropped something](#stacked-special-cases-mean-the-structure-dropped-something)
  - [Finish deciding before you act](#finish-deciding-before-you-act)
- [Common graph mistakes](#common-graph-mistakes)
- [Drill set — cold, no IDE, no running](#drill-set--cold-no-ide-no-running)
- [Not covered here](#not-covered-here)
- [Before you submit anything](#before-you-submit-anything)
- [Self-check answers](#self-check-answers)
<!-- /toc -->

This module covers graphs. A graph is a tree with its promises taken away: there can be several paths between two nodes, a node can have several parents, there may be cycles, nobody hands you a root, and the nodes may not even be in one piece. The traversals are the DFS and BFS of module 06, unchanged, plus one structure that every graph solution carries: the **visited set**. You'll learn what `visited` means and at exactly which moment a node enters it, how to build the graph from whatever the input gives you, why a grid is a graph, the two cycle tests and the third colour that directed graphs need, topological sort, union-find, and how weights turn BFS into Dijkstra.

**How to use it.** Read §0, then answer the self-check in §0.9 and re-read the parts of §0 behind any question you miss. Then work through the visited set, representation, the traversals, grids and connected components, and start the drill set cold. Read the later sections in order, as far as the section the next drill needs, before that drill: multi-source BFS before row 3, the inversion before row 5, and undirected cycles through union-find before row 8. §Weighted graphs is for the tier-2 problems.

| Section | What it gives you |
|---|---|
| §0, the foundation | what a graph takes away from a tree, the vocabulary, what each operation costs, the primitives, the inputs that break it, the signals |
| The visited set | when a node is marked, what the mark means, and its disguises |
| Representation | turning an edge list, a matrix or a grid into something you can traverse |
| BFS and DFS on a graph | the two templates, why BFS gives shortest paths, recursion depth, and the O(V + E) argument |
| Grids are graphs | the neighbour loop, the four-part guard, marking by overwriting |
| Connected components, flood fill, shortest paths | the outer loop, the guard order, distance as you push |
| Multi-source BFS | one queue seeded with every source |
| The inversion | start from the special thing instead of from every node |
| Undirected cycles, directed cycles | the parent parameter, then three colours |
| Topological sort | Kahn's algorithm, the DFS form, which to choose, peeling leaves |
| Union-find | connectivity without a traversal |
| Weighted graphs | Dijkstra and Prim, and the claim that weights withdraw |
| Every template, in one place | one algorithm and nine deltas |
| How to attack a graph problem | the steps, in order |
| In depth | the derivations and counterexamples behind the rules |
| Common graph mistakes | the bugs, each linked to its entry |
| Drill set | the problems, with the checkpoints |
| Before you submit anything | the checklist |

---

## 0.1 Prerequisites and the one question

| You need | From | Used here for |
|---|---|---|
| Recursion and the call stack | [00-before-you-start.md](00-before-you-start.md#recursion-and-the-call-stack), §Recursion and the call stack | every recursive DFS here |
| Stack space is the deepest the stack gets, and the default limit is about 1,000 frames | [00-before-you-start.md](00-before-you-start.md#stack-depth), §Stack depth | §Recursion depth is arithmetic |
| Returning a value vs updating an answer on the side | [00-before-you-start.md](00-before-you-start.md#returning-a-value-vs-updating-an-answer-on-the-side), §Returning a value vs updating an answer on the side | a component count kept on the side; a cycle test that returns a bool |
| Reading the constraints | [00-before-you-start.md](00-before-you-start.md#reading-the-constraints), §Reading the constraints | whether recursion fits, and whether O(V²) is allowed |
| Tree DFS: the base case, then recurse into each child | [06-trees.md](06-trees.md#the-shape--memorise-this), §DFS, The shape — memorise this | the DFS template, with one line added |
| Returning a value up the tree: say what a call returns to its parent, then trust the recursion | [06-trees.md](06-trees.md#returning-a-value-up-the-tree), §Returning a value up the tree | a grid traversal that hands a value back up (drill 2) |
| Tree BFS: a queue, one node out, its children in | [06-trees.md](06-trees.md#the-shape--memorise-this-1), §BFS, The shape — memorise this | the BFS template, with one line added |
| Freezing one level with `for _ in range(len(q))` | [06-trees.md](06-trees.md#level-order--the-one-trick-worth-knowing), §Level order — the one trick worth knowing | distance as a level number; Kahn's rounds |
| Discover vs. visit: the frontier is the gap between the two | [06-trees.md](06-trees.md#discover-vs-visit), §Discover vs. visit | mark on push, or mark on pop |
| Going iterative is a control choice, not a space saving | [06-trees.md](06-trees.md#when-to-go-iterative), §When to go iterative | §Why an explicit stack survives |
| In a tree every node except the root has exactly one parent | [06-trees.md](06-trees.md#02-the-structure-and-how-it-works), §0.2 The structure and how it works | the promise a graph withdraws |
| A list used as a stack, and the call stack is a stack | [02-stacks-queues.md](02-stacks-queues.md#a-list-used-as-a-stack), §A list used as a stack | iterative DFS |
| A deque used as a queue: `popleft` is O(1), `pop(0)` is not | [02-stacks-queues.md](02-stacks-queues.md#a-deque-used-as-a-queue), §A deque used as a queue | every BFS |
| The amortised argument: count the work per element, not per iteration | [02-stacks-queues.md](02-stacks-queues.md#the-amortised-argument), §The amortised argument | §Each node once: the O(V + E) argument |
| The per-path mark: on while the item is on the path, off when it leaves | [07-backtracking.md](07-backtracking.md#the-per-path-mark), §The per-path mark | the GREY colour in directed cycle detection |
| Node objects, following a pointer, and a node is hashable by identity | [05-linked-lists.md](05-linked-lists.md#06-inputs-that-break-it), §0.6 Inputs that break it | nodes that are objects, not integers (drill 7) |
| `deque` and `defaultdict` | [python-toolkit.md](../reference/python-toolkit.md#1-deque-the-queue), §1. `deque`: the queue, and [python-toolkit.md](../reference/python-toolkit.md#2-defaultdict-the-dict-that-fills-itself-in), §2. `defaultdict`: the dict that fills itself in | building and walking every graph |
| Tuples are hashable, lists are not | [python-toolkit.md](../reference/python-toolkit.md#dict-keys-must-be-immutable-convert-dont-invent), §Dict keys must be immutable: convert, don't invent | `(r, c)` as a key in `visited` |

**A graph is a tree with the promises taken away.** In module 06 every node had one parent and there was one path from the root to it, so a traversal reached each node exactly once without trying. A graph keeps the nodes and the edges and drops those guarantees. The traversals don't change. What changes is that something now has to remember which nodes have been reached, and that something is the visited set.

**The one question this module answers:**

> *What does `visited` mean, and at exactly which moment does a node enter it?*

Answer that in one sentence before the loop, and most graph bugs never get written. Every section below is a different answer to it: on push for BFS, at the top of the call for recursive DFS, on pop for Dijkstra, three colours for directed cycles, a counter for Kahn's algorithm, a root pointer for union-find.

## 0.2 The structure and how it works

### A tree promises; a graph withdraws the promises

| A tree promised | A graph withdraws it, so you need |
|---|---|
| one path between any two nodes | a visited set, or you reach a node once per path |
| one parent per node | a visited set even when there are no cycles |
| no cycles | a visited set, or the walk never ends |
| a root you are given | an outer loop over every node, with one shared visited set |
| one piece | the same outer loop: one start reaches one component |
| nodes are objects with `.left` and `.right` | a representation you build: usually an adjacency list |
| edges point away from the root | the direction is part of the problem, and you must read it |

| | Tree | Graph |
|---|---|---|
| Paths between two nodes | exactly one | zero, one, or many |
| Parents of a node | one, except the root | any number |
| Cycles | never | possible |
| Where you start | the root | anywhere, often everywhere |
| Pieces | one | any number of components |
| What a node is | an object | an integer, a cell, a string, an object |
| What stops the recursion | `None` | the visited set |
| Direction | parent to child | directed or undirected; the statement says which |

### Four consequences

1. **A visited set is required**, even on a graph with no cycles. The next section shows why.
2. **One start reaches one component.** Anything that must touch every node needs an outer loop.
3. **The representation is your job.** The input is an edge list, a matrix or a grid; the traversal wants "give me the neighbours of u" in O(1).
4. **Direction is information.** In a directed graph, `u → v` does not give you `v → u`. Getting it backwards gives a correct algorithm and a wrong answer.

### The diamond: why `visited` exists without a cycle

```
    A
   / \
  B   C          edges A→B, A→C, B→D, C→D
   \ /
    D
```

There is no cycle here, and a traversal with no visited set still reaches D twice: once through B, once through C. That costs one extra visit here. Chain k diamonds end to end, so that the bottom of each is the top of the next, and the last node is reached once per path: 2ᵏ times. Thirty diamonds, about 90 nodes, and the traversal does a billion visits.

> **`visited` is not a cycle guard. It's a process-each-node-once guard.** It also stops cycles, because a cycle is one more way to reach a node twice. But it is needed on any graph where two paths meet.

### The outer loop

A traversal from one start reaches exactly the component that start is in. To touch every node, wrap the traversal in a loop over every node, and share one visited set across all of it:

```python
visited = set()
for u in range(n):                       # every node, isolated ones included
    if u not in visited:
        traverse(u)                      # marks everything u can reach
```

Each call to `traverse` from this loop is a new component, and the visited set guarantees no node is traversed twice across calls. That is why the whole loop is still O(V + E), not O(V × (V + E)).

### What transfers unchanged

Everything from module 06 except the termination test. The DFS still recurses into each neighbour; the BFS still pops one node and pushes its neighbours; level order still freezes one level with `for _ in range(len(q))`. The base case `if node is None: return` becomes the visited test, and `node.left, node.right` becomes `adj[node]`.

## 0.3 Vocabulary

| Word | Meaning |
|---|---|
| **graph** | a set of nodes and a set of edges between pairs of them |
| **node, vertex** | the same thing. V is how many there are |
| **edge** | a connection between two nodes. E is how many there are |
| **directed, undirected** | whether `u → v` is one-way, or the same as `v → u` |
| **weighted** | each edge carries a number, a cost or a length |
| **neighbour, adjacent** | v is a neighbour of u if there is an edge from u to v |
| **degree, indegree** | how many edges touch a node; in a directed graph, how many point into it |
| **path** | a sequence of nodes, each joined to the next by an edge |
| **cycle** | a path that starts and ends at the same node; in an undirected graph, without reusing an edge |
| **connected component** | a maximal set of nodes that can all reach each other |
| **adjacency list** | for each node, the list of its neighbours: `adj[u]` |
| **adjacency matrix** | a V × V table: `m[u][v]` is 1 if there is an edge |
| **edge list** | the edges as pairs, `[[u, v], ...]`: how most inputs arrive |
| **visited** | the set of nodes already reached. What it means exactly is the question of this module |
| **frontier** | the nodes discovered but not yet processed: the queue or the stack |
| **DAG** | a directed acyclic graph: directed, with no cycle |
| **topological order** | an order of a DAG's nodes in which every edge points forward |
| **Kahn's algorithm** | a topological sort: repeatedly output a node with indegree 0 and lower its neighbours' indegrees. A node on a cycle always keeps an incoming edge from the node before it on the cycle, so it never reaches 0; `len(order) < n`, a count you already keep, is the cycle test for free |
| **source, sink** | a node with no incoming edges; a node with no outgoing edges |
| **implicit graph** | a graph never stored: a node's neighbours are computed from the node |
| **relaxation** | lowering a node's best-known distance when a cheaper route to it is found |
| **union-find** | a structure that tracks which component each node is in, and merges two components |
| **spanning tree, MST** | a tree that uses some edges to connect every node; the minimum spanning tree has the smallest total weight |

## 0.4 Operations and their cost

**V** is the number of nodes, **E** the number of edges, **deg(u)** the number of neighbours of u.

| Operation | Python | Big-O | Trap |
|---|---|---|---|
| Build an adjacency list from an edge list | `adj[u].append(v)` per edge | O(V + E) | an undirected edge needs two lines, `adj[v].append(u)` as well |
| The neighbours of u, from a list | `for v in adj[u]` | O(deg(u)) | `for v in adj` loops over the keys, not the neighbours |
| Is there an edge u to v, from a list | `v in adj[u]` | O(deg(u)) | store neighbour sets if you test this often |
| Is there an edge u to v, from a matrix | `m[u][v] == 1` | O(1) | the neighbours of u cost O(V) to list, however few there are |
| Mark and test | `visited.add(x)`, `x in visited` | O(1) | `visited.add(grid[r][c])` marks a value, not a cell |
| Queue push and pop | `q.append(x)`, `q.popleft()` | O(1) | `list.pop(0)` is O(n) |
| Stack push and pop | `stack.append(x)`, `stack.pop()` | O(1) | `pop()` gives DFS, `popleft()` gives BFS: one word changes the algorithm |
| Heap push and pop | `heapq.heappush(h, (key, x))`, `heapq.heappop(h)` | O(log n) | the tuple is compared from the left, so the key goes first |
| Find and union | `find(x)`, `union(a, b)` | about O(1) amortised | `parent[a] = b` links nodes; you must link roots |
| Every node, isolated ones included | `for u in range(n)` | O(V) | `for u in adj` misses every node that has no edges |
| A full traversal, adjacency list | DFS or BFS | O(V + E) | it's a sum, not a product |
| A full traversal, adjacency matrix | DFS or BFS | O(V²) | every node scans a whole row, whatever E is |

**The row people get wrong is the last.** On a matrix the traversal is O(V²) even when the graph has three edges, because finding the neighbours means scanning the row.

## 0.5 The primitives

Five moves build almost every graph solution. Each has an invariant: the thing that is true every time it runs.

**1. Build the adjacency list first.** Turn the input into `adj` before any traversal, once.

```python
from collections import defaultdict
adj = defaultdict(list)
for u, v in edges:
    adj[u].append(v)
    adj[v].append(u)                     # UNDIRECTED only: delete this line for a directed graph
```

*Invariant:* after the loop, `adj[u]` is exactly the list of u's neighbours, and looking it up is O(1). Never rescan `edges` inside the traversal: that turns every neighbour lookup into O(E).

Because every undirected edge is stored twice, the node you just came from shows up as a visited neighbour, so without skipping the parent a single edge 0 – 1 reads as a cycle. In a directed graph the parent test answers the wrong question: a visited node reached by a second route is not a cycle (the diamond). You need to know whether it is on the current path, which takes a third state, GREY vs BLACK.

**2. Mark on push.** In BFS and iterative DFS, a node is added to `visited` in the same step that puts it in the frontier.

```python
if nei not in visited:
    visited.add(nei)
    q.append(nei)
```

*Invariant:* a node is in `visited` if and only if it is in the frontier now or has been in it before. So each node enters the frontier at most once.

Mark on pop instead and a node is pushed once per unmarked predecessor: on the diamond, D enters the queue twice. Anything written at push time is written twice, and the later, longer route wins: with A: [B, X] and B: [X], `dist[X]` ends at 2 where the true distance is 1.

**3. Mark at the top of the call.** In recursive DFS, the first line of the function marks its own node.

```python
def dfs(u):
    visited.add(u)
    for v in adj[u]:
        if v not in visited:
            dfs(v)
```

*Invariant:* every node that has ever been entered is in `visited`, including the start, whoever called it. The caller tests, the function marks.

**4. The outer loop with one shared set.**

*Invariant:* when the loop reaches u, every node in a component already traversed is in `visited`. So `u not in visited` means "u starts a new component", and each node is traversed once across the whole loop.

**5. The frontier decides the algorithm.** A deque with `popleft` gives BFS: nodes come out in order of distance. A stack, or recursion, gives DFS: the newest node comes out first. A min-heap gives Dijkstra: the cheapest node comes out first.

Dijkstra marks on pop, not push: a node's distance can still drop while it waits in the heap, and each improvement pushes a new entry and leaves the old one stale. The first pop is final, because every other entry is at least as large. The `done` check skips stale copies (lazy deletion); without it the answers stay right but the work grows.

*Invariant (BFS):* the queue holds nodes at distance d, followed by nodes at distance d + 1, and nothing else. That one fact is why BFS finds shortest paths in an unweighted graph.

## 0.6 Inputs that break it

| Input | What breaks | Check |
|---|---|---|
| A disconnected graph | one start reaches one component; the rest is never seen | an outer loop over every node |
| Isolated nodes, with no edges at all | `for u in adj` skips them, because they were never added as keys | loop over `range(n)` |
| n = 1, or no edges | a loop written for at least one edge; an answer that should be the node itself | trace it |
| A self-loop, `u → u` | a directed cycle of length one; an undirected DFS that skips "the parent" may or may not see it | ask whether self-loops are allowed |
| Parallel edges, the same pair twice | in an undirected graph, two copies of an edge form a cycle | the parent test (§Undirected cycles: carry the parent) |
| A cycle where you assumed a DAG | a topological sort returns a partial order, or a DFS never ends | the cycle test is part of the algorithm |
| A chain of 10⁵ nodes, or an all-land 300 × 300 grid | `RecursionError` | §Recursion depth is arithmetic |
| The edge direction read backwards | a correct algorithm, a reversed or empty answer | write the arrow down before building `adj` |
| An empty grid | `len(grid[0])` raises `IndexError` | guard it only if the constraints allow it |
| A grid of one row or one column | neighbour offsets that step outside on every move | the bounds test comes first |
| Weights that are all equal | nothing breaks: BFS is enough | don't reach for Dijkstra when every edge costs the same |
| A negative weight | Dijkstra's "final when popped" stops being true | say it: Dijkstra needs every weight to be non-negative |

## 0.7 Complexity, out loud

Say these as sentences, with the reason:

- **Time:** *"O(V + E), because every node enters the frontier at most once and every edge is examined at most once from each end."* It's a sum: the work per node is paid for by that node's own edges (§Each node once: the O(V + E) argument).
- **Say it in the problem's nouns.** On a grid: *"O(rows × cols), because each cell is visited once and has at most four neighbours."* On a matrix input: *"O(n²), because each node scans its row."* From an edge list: *"O(n + edges)."*
- **Space:** *"O(V) for the visited set and O(V) for the frontier or the recursion stack."* The adjacency list you build is O(V + E); it counts as auxiliary space, so say it.
- **Name the term that isn't there.** If there's no recursion, say so; if the graph is given as a matrix and you build no list, say that too.
- **Dijkstra:** *"O((V + E) log V), because every push and pop on the heap is O(log V), and there are at most E pushes."*
- **A time-space trade:** one BFS from every source at once is O(rows × cols) in time and space; re-scanning the grid round by round needs no queue but costs O((rows × cols)²).
- **Optimality:** *"Any correct algorithm has to look at every node and every edge at least once, so O(V + E) is a lower bound, and this matches it."*

## 0.8 Signals

| In the statement | Reach for | Where |
|---|---|---|
| a grid and "islands", "regions", "area", "connected" | DFS or BFS on the grid, with the outer loop | §Grids are graphs |
| "how many groups", "how many components" | the outer loop with one shared visited set, or union-find | §Connected components |
| "shortest path", "fewest steps", "minimum moves", every step costing the same | BFS: the first arrival is the shortest | §Shortest path in an unweighted graph |
| "distance to the nearest X" for every cell | multi-source BFS: seed the queue with every X | §Multi-source BFS |
| "for every node, can it reach the special set" | start from the special set instead | §The inversion: start from the special thing |
| "prerequisites", "dependencies", "an order in which to do them all", "can it be finished" | topological sort, which is also the cycle test | §Topological sort |
| "does it contain a cycle", undirected | DFS carrying the parent, or union-find | §Undirected cycles: carry the parent |
| "does it contain a cycle", directed | three-colour DFS, or Kahn's algorithm | §Directed cycles: three colours |
| "are u and v connected", asked repeatedly while edges arrive | union-find | §Union-find |
| weighted edges and "cheapest", "shortest", "minimum time" | Dijkstra: a heap instead of a queue | §Dijkstra |
| "connect everything at minimum total cost" | a minimum spanning tree: Prim or Kruskal | §Prim is Dijkstra with one line changed |
| the neighbours are generated, not given: words, states, moves | BFS on an implicit graph: `adj[u]` becomes a function | §Representation |
| a path that may not reuse a cell within one path, "return all paths" | not this module: a per-path mark, which is backtracking | [07-backtracking.md](07-backtracking.md#grids-a-tree-of-moves), §Grids: a tree of moves |

## 0.9 Self-check

Answer each in a sentence or two, without looking back. The answers are at the bottom of the module. Read the part behind any question you miss.

1. On the diamond A→B, A→C, B→D, C→D, a BFS marks nodes when it pops them instead of when it pushes them. How many times does D enter the queue, and what goes wrong if you also record a distance at push time?
2. Why does a graph with no cycles still need a visited set?
3. A recursive flood fill runs on a 300 × 300 grid that is all land. What happens, and what are two fixes?
4. A BFS has a `for` loop over neighbours inside a `while` loop over the queue. Why is it O(V + E) and not O(V × E)?
5. Why does an undirected cycle test need the parent, and why is that not enough in a directed graph?
6. Kahn's algorithm finishes with an order shorter than n. What does that tell you, and why did it cost nothing extra to find out?
7. In Dijkstra, why is a node marked when it is popped, not when it is pushed? And what does the `done` check protect against, if not cycles?
8. You push `(node, distance)` onto a heap instead of `(distance, node)`. What happens, and why might the example in the statement still pass?

---
## The visited set

### Mark on push, or mark on pop?

A container-based traversal has two moments at which it could mark a node: when the node is **discovered** and goes into the frontier, and when it is **processed** and comes out. Module 06 called the gap between them the frontier. In a tree it didn't matter which you picked, because a tree never offers a node twice. In a graph it decides how many times a node enters the queue.

Trace both on the diamond, A→B, A→C, B→D, C→D, starting from A:

```
MARK ON PUSH                              MARK ON POP
push A, visited {A}                       push A
pop A: push B, C   visited {A,B,C}        pop A, mark A: push B, C        q [B, C]
pop B: push D      visited {A,B,C,D}      pop B, mark B: push D           q [C, D]
pop C: D is visited, nothing pushed       pop C, mark C: D not marked yet,
pop D                                            push D again             q [D, D]
                                          pop D, mark D                   q [D]
4 pushes                                  pop D: already marked, continue
                                          5 pushes
```

Mark on pop is still correct here, because the duplicate is skipped when it comes out. But D sat in the queue twice, and on a dense graph a node can be pushed once per incoming edge, so the queue grows to O(E) instead of O(V). Worse, anything you record at push time is recorded more than once. With adjacency A: [B, X], B: [X], setting `dist[nei] = dist[node] + 1` at push and marking on pop gives `dist[X] = 2`: X was pushed from A with distance 1, then pushed again from B and overwritten with 2. The true distance is 1.

| Traversal | Can a node be offered twice? | Mark |
|---|---|---|
| BFS, a queue | yes | **on push**, always |
| Iterative DFS, a stack | yes | on push, by the same reasoning |
| Recursive DFS | the call is the visit | at the top of the function |
| Dijkstra, a min-heap | yes, and its distance can improve while it waits | **on pop**, and only there (§Dijkstra) |

> **Recursive DFS: mark at the top. Anything with a container: mark on push.** Dijkstra is the one exception, and it is an exception for a reason you'll see.

**In recursion the question dissolves.**

> **A queue entry waits. A stack frame doesn't.** Calling a function doesn't park it, it runs it. Discovery and processing are the same instant, so mark-on-push and mark-on-pop are the same line.

The choice that does exist in recursion is **inside the function** or **at the call site**:

```python
# A: inside. The standard.                 # B: at the call site
def dfs(r, c):                             def dfs(r, c):
    visited.add((r, c))      # first line      for dr, dc in DIRS:
    for dr, dc in DIRS:                            if valid and (nr, nc) not in visited:
        if valid and (nr, nc) not in visited:          visited.add((nr, nc))
            dfs(nr, nc)                                dfs(nr, nc)
```

They mark the same cells **except the start**. In B, the cell the outer loop launches from is never marked, because no neighbour called `dfs` on it, so its own neighbour walks straight back into it. On a strip of three land cells, B enters the function four times. A count of regions survives that, because the extra entry is inside the same region. Anything you add up once per entry does not.

> **Mark inside the function, on the first line.** Then the start is marked like every other node, because the outer loop's call is a call like any other.

One caveat for DFS with a container: mark on push gives you no *"I have finished this node"* moment. Topological sort and directed cycle detection both need one, so for those use recursion, where entry and exit are both visible (§Directed cycles: three colours).

### Define it by a property, never by the route

The common way to get `visited` wrong is to define it by how you got to a node:

| Definition | What it leaves out |
|---|---|
| *"reached through an edge"* | the start node of every component |
| *"reached from one of the sources"* | the sources themselves |
| *"has come off the queue"* | everything still in the queue |

Each one has the same hole: **the nodes nobody got to.** Every graph problem has them, the outer loop's start, the seeds of a multi-source BFS, the roots of a forest, and they are the nodes the definition must cover.

> **Define `visited` by a property the node has, not by the route that brought you there.**
>
> ✗ *"reached via an edge"*: leaves out every start
> ✓ *"already assigned to a component"*: the start is assigned to one
> ✓ *"already has a distance"*: a source's distance is 0

**The test, in three seconds:** *does my start node satisfy my own definition?* If it doesn't, the definition is wrong, and the code will process something twice. It's also why multi-source BFS works at all: it starts from nodes nobody reached, and a route-based definition can't describe them.

### `visited` is not always a set

It is whatever structure records "already handled". Recognising the disguises is most of the skill:

| Disguise | Looks like | Note |
|---|---|---|
| a set of ids | `visited = set()` | the default |
| a set of tuples | `visited.add((r, c))` | grids. Tuples are hashable, lists are not |
| the grid itself | `grid[r][c] = 0` | O(1) extra space, but it destroys the input. Say so out loud |
| a distance dict or list | `if nei not in dist` | a distance record is a visited record. Don't keep both |
| a parent list | `if parent[v] == -1` | the same |
| a colour list | `WHITE`, `GREY`, `BLACK` | when two states aren't enough (§Directed cycles: three colours) |
| an indegree counter | `if indeg[v] == 0` | Kahn's algorithm (§Topological sort) |

> **Two structures that must stay in sync will eventually disagree.** If you have a `dist` dict, you don't also need `visited`: `nei not in dist` says everything `nei not in visited` said. It's [bug-checklist.md](../reference/bug-checklist.md#keep-one-source-of-truth), §Keep one source of truth.

Two states, seen or not seen, answer *"have I ever been here?"* Some questions need *"am I here right now, on the path I'm standing on?"* That needs a third state, and it's why undirected and directed cycle detection are different algorithms.

## Representation

The input is almost never the adjacency list you want. It's one of five things, and step one is converting it.

| Given | Looks like | What to do |
|---|---|---|
| an edge list | `edges = [[0, 1], [1, 2]]` and `n` | build an adjacency list, §0.5 primitive 1 |
| an adjacency matrix | `m[i][j] == 1` | usually use it directly; a node's neighbours cost O(V) |
| an adjacency list | `adj = [[1, 2], [0], [0]]` | already done |
| a grid | `grid[r][c]` | implicit: §Grids are graphs |
| implicit, generated | words, puzzle states, lock combinations | neighbours are computed, never stored |

Every traversal has exactly two loops, and they ask different questions:

| Input | Outer loop: every node | Inner loop: the neighbours of `u` |
|---|---|---|
| grid | `for r in range(rows):` then `for c in range(cols):` | `for dr, dc in DIRS:` then `nr, nc = r + dr, c + dc` |
| adjacency list, a list of lists | `for u in range(n):` | `for v in adj[u]:` |
| adjacency list, a dict | `for u in range(n):`, **not** `for u in adj` | `for v in adj[u]:` |
| adjacency matrix | `for i in range(n):` | `for j in range(n):` then `if m[i][j] == 1:` |
| edge list | you can't: build `adj` first | `for u, v in edges:` walks edges, not nodes |
| implicit | usually one start | `for nxt in moves(state):` |

**An edge list is not traversable.** `for u, v in edges` walks edges, so you can neither ask "who are u's neighbours" nor reach a node with no edges. Build the adjacency list first, and take the node count from `n`, never from the edges.

**The second line of the build is the most common setup bug in the topic.** Left out on an undirected graph, you can walk u to v but never back, and components come out split. Left in on a directed graph, you invented edges, and every cycle test says "cycle". Say which it is before you build: *"this is directed, from each item to the items that depend on it, so one direction only."*

> **Edge direction is a reading question.** A pair `[a, b]` might mean a before b, or b before a, and statements use both. Build it backwards and the algorithm is perfect and the answer is reversed. **Write the arrow down before you write the loop.**

**The grid version of index vs value:**

```python
for r in grid:              # ✗ r is a row: a list
    for c in r:             # ✗ c is a cell's value
        ...(r, c)           #   TypeError: unhashable type: 'list'

for r in range(rows):       # ✓ r and c are positions
    for c in range(cols):
        ...grid[r][c]
```

`for r, row in enumerate(grid):` then `for c, val in enumerate(row):` gives you the position and the value together. `enumerate` yields `(index, value)` in that order ([bug-checklist.md](../reference/bug-checklist.md#unpacking-enumerate-in-the-wrong-order), §Unpacking `enumerate` in the wrong order).

| | Adjacency list | Adjacency matrix |
|---|---|---|
| Space | O(V + E) | O(V²), even for three edges |
| Is u–v an edge? | O(deg(u)) | O(1) |
| The neighbours of u | O(deg(u)) | O(V): scan the row |
| A full traversal | O(V + E) | O(V²) |
| Use it when | almost always | the input hands you one, or the graph is dense |

**`defaultdict(list)` or a list of lists.** When the nodes are `0 … n−1`, `adj = [[] for _ in range(n)]` is just as short, and it has an entry for every node, isolated ones included. Use `defaultdict` when the nodes are strings or tuples. One trap with `defaultdict`: reading `adj[u]` for a missing u inserts it, so a lookup inside a `for u in adj` loop raises `RuntimeError: dictionary changed size during iteration`. Loop over `range(n)`, or read with `adj.get(u, [])`. And never write `[[]] * n`: that is n references to one list, and every append lands in all of them.

**An implicit graph** has no adjacency at all. A node's neighbours are a function of the node: the states one move away, the strings one edit away. The traversal is the same; `for v in adj[u]` becomes `for v in neighbours(u)`. The cost to watch is that function. If it is expensive, or generates many candidates per node, it dominates the O(V + E) and is where the work of the problem lives.

## BFS and DFS on a graph

The two templates from module 06, with one line added to each:

```python
from collections import deque

def bfs(start):
    visited = {start}
    q = deque([start])
    while q:
        node = q.popleft()
        for nei in adj[node]:
            if nei not in visited:         # the added line: the tree's None test becomes this
                visited.add(nei)           # mark on push
                q.append(nei)

def dfs(node):
    visited.add(node)                      # mark at the top
    for nei in adj[node]:
        if nei not in visited:
            dfs(nei)
```

When a problem needs neither distances nor levels, both are correct, and you choose on cost: recursion is shorter, BFS or an explicit stack has no depth limit.

### Why BFS never needs a relaxation test

**Every edge costs 1 in BFS, so a node is discovered in order of its distance.** The queue holds nodes at distance d followed by nodes at distance d + 1. The first time a node is discovered, it is discovered from a node at the smallest possible distance, so the first distance it is given is final. Nothing later can beat it, which is why mark on push is safe and `dist[nei] = dist[node] + 1` needs no `if` around it.

Give the edges weights and that breaks:

```
A --1--> B --1--> D          A→B→D costs 2
A --10------------> D        A→D costs 10: fewest edges, not cheapest
```

D is one edge from A, but the cheap route is two edges. A node can be found early along a heavy edge and improved later along a light one, so you have to keep checking, and the first assignment is no longer final. That is the whole difference between BFS and Dijkstra.

### `return` inside the neighbour loop

> **`return` does not mean "recurse". It means "leave this function now."**

```python
for dr, dc in DIRS:
    if valid(nr, nc):
        return dfs(nr, nc)        # the FIRST valid neighbour ends the function
```

The other directions are never tried. The recursion still happens for that one neighbour, which is why it looks as if it works: it walks a single path instead of the whole region. On the T-shaped grid `[[1, 1, 1], [0, 1, 0]]` with `DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]`, a component counter written this way reports two regions, of sizes 3 and 1, where there is one region of 4. A plus-shaped region comes out as three.

> **A `return` inside a loop is a `break` that also ends the function.** If you need every neighbour, you can't return inside the neighbour loop.

**The eye-check:** *does this `dfs` have a return value?* If its job is to fill a shared structure, `visited` or a list or a counter, it returns nothing, so no call to it is ever prefixed with `return`. If it does return a value, the value is built up across the loop and returned after it. Pick one of the two shapes from [00-before-you-start.md](00-before-you-start.md#returning-a-value-vs-updating-an-answer-on-the-side), §Returning a value vs updating an answer on the side, and don't blend them. The checklist entry is [bug-checklist.md](../reference/bug-checklist.md#return-inside-the-neighbour-loop), §`return` inside the neighbour loop.

### Recursion depth is arithmetic

Python's default recursion limit is about 1,000 nested calls. The limit is on **depth**, how many calls are open at once, not on the number of nodes:

```
balanced tree, 1,000,000 nodes    depth about 20     recursion is fine
a chain of 2,000 nodes            depth 2,000        RecursionError
```

> **The question is never "how many nodes?" It is "what is the longest possible chain of nested calls?"**

On a graph, **the depth can reach the size of the largest component**, and it does when the component is shaped like a snake, because DFS walks one node at a time with nothing to unwind. You can't assume a region is compact, so assume the worst.

| Structure | Worst depth | Recursion |
|---|---|---|
| a balanced tree, n = 10⁶ | about 20 | fine |
| a skewed tree, n = 5,000 | 5,000 | ✗ |
| a grid whose largest region has R cells | up to R | ✗ if R can pass about 1,000 |
| a graph whose largest component has C nodes | up to C | ✗ if C can pass about 1,000 |
| a 30 × 30 grid | 900 | fine |
| a 200 × 200 grid | 40,000 | ✗ |
| a 300 × 300 grid | 90,000 | ✗ |

**Read the constraints, work out the maximum depth, compare it with about 1,000.** For a grid: if rows × cols can pass about 1,000, go iterative. A recursive fill on an all-land 30 × 30 grid reaches depth 900 and passes; a chain of 2,000 nodes raises `RecursionError`.

**Say it either way.** *"Depth is bounded by 900 here, under the limit, so I'll recurse"* is as good as switching. What loses points is not having worked it out. Changing the algorithm doesn't help either: any recursive DFS on the same grid has the same depth. It's about the container, not the approach.

### Why an explicit stack survives

| | Recursive DFS | Iterative DFS |
|---|---|---|
| Progress is stored in | the call stack | a Python list, on the heap |
| Its size | small and fixed, a few megabytes | as much memory as the machine has |
| One entry holds | a whole frame: every local, the loop's position, the return address | one tuple `(r, c)` |

> **Recursion stores your progress in a small room you don't control. An explicit stack stores it in a large one you do.**

And the algorithm doesn't change. `stack.pop()` is last-in first-out, which is what the call stack was doing. [02-stacks-queues.md](02-stacks-queues.md#a-list-used-as-a-stack), §A list used as a stack, makes the same point from the other side: writing it iteratively means making the stack explicit.

```python
stack = [start]
visited = {start}
while stack:
    node = stack.pop()                     # pop(), not popleft(): one word is the whole difference
    for nei in adj[node]:
        if nei not in visited:
            visited.add(nei)
            stack.append(nei)
```

A chain of 100,000 nodes runs through this without trouble. It doesn't visit nodes in the same order as the recursive version, because the neighbours are pushed all at once and popped in reverse, but it reaches the same set, which is all a reachability or component question needs.

**`sys.setrecursionlimit` is not the fix.** Raising the limit removes the guard rail, not the cliff: the real stack is still a few megabytes, and recursing past it crashes the interpreter outright instead of raising an exception you can catch. In an interview it also reads as working around the problem rather than solving it.

### Each node once: the O(V + E) argument

A BFS has a `for` loop over neighbours inside a `while` loop over the queue. Multiplying the two bounds gives O(V × E), and it's wrong. Count per node instead, which is [02-stacks-queues.md](02-stacks-queues.md#the-amortised-argument), §The amortised argument, applied to a graph:

- **Each node enters the queue at most once**, because it is marked when it is pushed and never pushed again. So the `while` body runs at most V times.
- **When a node is popped, its own neighbour loop runs deg(u) times.** Summed over every node, that is the total number of adjacency entries: E for a directed graph, 2E for an undirected one.

So the total is V + (sum of degrees) = O(V + E). The inner loop is not "up to E per node"; it is that node's own edges, and each edge is paid for once from each end.

> **Every node enters the frontier at most once. Every edge is examined at most once from each end. So the traversal is O(V + E).** That sentence is the whole derivation.

The same argument covers the outer loop over components: it runs V times, but each traversal it starts only touches unmarked nodes, so all of them together touch each node once. On an adjacency matrix the neighbour loop is a whole row for every node, and the sum becomes V × V = O(V²) instead.

## Grids are graphs

> **A grid is a graph you were handed without being told.** A node is a cell `(r, c)`. An edge means "these two cells are adjacent". Nothing is stored: the neighbours are computed.

```python
DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))          # up, down, left, right
rows, cols = len(grid), len(grid[0])

for dr, dc in DIRS:
    nr, nc = r + dr, c + dc
    if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 1 and (nr, nc) not in visited:
        ...
```

**`DIRS` is the adjacency list of a grid.** There are two worlds:

| | The neighbours are | The loop |
|---|---|---|
| **World A**: an edge list, a matrix, numbered nodes | stored in `adj` | `for nei in adj[node]` |
| **World B**: a grid, or any implicit graph | computed | `for dr, dc in DIRS` |

In World B nobody hands you edges, and you don't need any: the neighbours of `(r, c)` are always `(r ± 1, c)` and `(r, c ± 1)`. Build a `defaultdict` for a grid and iterate `adj[(r, c)]`, and you iterate an empty table: the traversal visits nothing, and every cell comes out as its own component. **An `adj` in a grid problem is dead code.**

### The four-part guard, in that order

1. **In bounds:** `0 <= nr < rows and 0 <= nc < cols`.
2. **The right kind of cell:** land, not water; open, not wall.
3. **Not already visited.**
4. **Sometimes, a condition from the problem:** the same colour as the start, a value the statement says you may step to.

> **Bounds come first, and the failure is silent.** `grid[-1][c]` is not an error in Python. It's the last row. A move off the top edge wraps around to the bottom, and the region grows through the far side of the map. No crash, a wrong answer. It's [bug-checklist.md](../reference/bug-checklist.md#a-negative-index-wraps-instead-of-crashing), §A negative index wraps instead of crashing.

**Guard 2 changes with every problem**: `== 1`, `== 'O'`, `!= '#'`, `== start`. Rewrite it from this problem's statement every time. A guard copied from the last problem is the bug in [bug-checklist.md](../reference/bug-checklist.md#guards-copied-from-another-problem), §Guards copied from another problem.

**Position, not value.** `(r, c)` is a position and `grid[r][c]` is a value. `visited` holds positions; the guard compares values. `visited.add(grid[r][c])` stores the value 1, after which every land cell looks visited. Name them `r` and `c`, never `x` and `y`, and index `grid[r][c]`: row first, because the outer list is the rows.

### Marking by overwriting

| | Extra space | Note |
|---|---|---|
| a set of `(r, c)` | O(rows × cols) | leaves the input alone |
| overwrite, `grid[r][c] = 0` | O(1) | destroys the input |

Overwriting is usually allowed, and it's worth offering: *"I can mark a cell by overwriting it, which is O(1) extra space. Is it OK to change the input?"* Asking scores. Doing it silently doesn't.

> **If you mark by overwriting, the mark has to change the guard's answer.** If the value you write still passes guard 2, the cell is never seen as visited, and the traversal never ends. §Flood fill and the guard order has the case.

**`rows, cols` on an empty grid.** `len(grid[0])` raises `IndexError` when `grid == []`. If the constraints say there is at least one row and one column, don't write the guard: a guard against an input that can't happen is noise.

**Building a grid:** `[[0] * cols] * rows` gives you `rows` references to one row, so writing one cell writes a whole column. Use `[[0] * cols for _ in range(rows)]`.

## Connected components

A component count is the outer loop with a counter:

```python
visited = set()
count = 0
for u in range(n):
    if u not in visited:
        traverse(u)                      # marks u's whole component
        count += 1                       # one new component per launch
```

> **The one shared `visited` is the whole trick.** Create it inside the outer loop and every node becomes its own component: you'd be measuring what each start reaches, not splitting the graph into pieces. If you are accumulating across calls, the accumulator lives outside them.

### Worked: Number of Provinces (LC 547)

[Number of Provinces](https://leetcode.com/problems/number-of-provinces/) (LC 547): `is_connected` is an n × n matrix, with `is_connected[i][j] == 1` when cities i and j are directly connected. Count the groups of cities that are connected directly or through others.

**Pattern:** components. **Delta:** the input is a matrix, so a city's neighbours are a row scan.

```python
def count_provinces(is_connected):
    n = len(is_connected)
    visited = set()

    def dfs(u):
        visited.add(u)
        for v in range(n):
            if is_connected[u][v] == 1 and v not in visited:
                dfs(v)

    count = 0
    for u in range(n):
        if u not in visited:
            dfs(u)
            count += 1
    return count
```

`[[1, 1, 0], [1, 1, 0], [0, 0, 1]]` gives 2; the 3 × 3 identity gives 3; `[[1]]` gives 1.

*Invariant:* when the outer loop reaches u, every city in a province already counted is in `visited`, so `u not in visited` means u starts a province nobody has counted.

**The complexity trap.** The outer loop runs n times and calls a DFS, which looks like n × (the cost of a traversal). It isn't: each city is entered once across all the calls together. Here it is **O(n²) time** because each city scans its row of the matrix, and **O(n) space** for `visited` plus a recursion stack that can be n deep on a chain. With n up to a couple of hundred, the depth is fine.

The same count can be done with union-find, with no traversal at all (§Union-find).

## Flood fill and the guard order

### Worked: Flood Fill (LC 733)

[Flood Fill](https://leetcode.com/problems/flood-fill/) (LC 733): starting from pixel `(sr, sc)`, recolour it and every pixel connected to it through four-directional neighbours of the same original colour.

**Pattern:** a traversal from one start. **Delta:** the image is the visited set: a pixel is visited once its colour is no longer the starting colour.

```python
DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))

def flood_fill(image, sr, sc, color):
    rows, cols = len(image), len(image[0])
    start = image[sr][sc]
    if start == color:
        return image                     # nothing would change, and the fill would never stop

    def fill(r, c):
        if not (0 <= r < rows and 0 <= c < cols):
            return                       # 1. bounds, first
        if image[r][c] != start:
            return                       # 2. the right kind of cell, which is also "not visited"
        image[r][c] = color              # 3. mark, by overwriting
        for dr, dc in DIRS:
            fill(r + dr, c + dc)         # 4. then recurse, unconditionally

    fill(sr, sc)
    return image
```

On `[[1, 1, 1], [1, 1, 0], [1, 0, 1]]` from `(1, 1)` with colour 2, it gives `[[2, 2, 2], [2, 2, 0], [2, 0, 1]]`. The bottom-right 1 is untouched: it touches the region only diagonally.

**Depth.** The worst-case depth of `fill` is the number of cells, and the image can be 50 × 50: an image of one colour is up to 2,500 nested calls, past Python's default limit of about 1,000 ([§Recursion depth is arithmetic](#recursion-depth-is-arithmetic)). Say so, and write the fill with an explicit stack ([§Why an explicit stack survives](#why-an-explicit-stack-survives)). Raising the limit is the other way out, and the same section says why it only moves the cliff.

> **The invariant is "a pixel is visited when its colour is no longer `start`". When `color == start`, no assignment can ever make that true.** The overwrite writes the value the guard is looking for, every cell passes guard 2 forever, and two neighbours call each other until `RecursionError`. The guard on the first line is the mark failing to change the guard's answer, caught before the first call.

The shape: **guards at the top of the function, one per line, cheapest first, then the work.** The recursive calls are unconditional, and the callee defends itself. Checking each neighbour before recursing is also correct, but then the guard is written four times. Guard in the callee, unless you are pushing onto a container, where the check has to happen before the push.

## Shortest path in an unweighted graph

When every step costs the same, **BFS finds the shortest path, and the first time it reaches the target is the answer.** Store the distance in the same structure that marks visited, and set it on push:

```python
dist = {start: 0}                        # dist is the visited set
q = deque([start])
while q:
    node = q.popleft()
    if node == target:
        return dist[node]
    for nei in adj[node]:
        if nei not in dist:
            dist[nei] = dist[node] + 1
            q.append(nei)
return -1
```

If you'd rather not store distances, process the queue a level at a time with `for _ in range(len(q))` from module 06 and count the levels. Both are fine; the dict is harder to get wrong by one.

### Worked: Shortest Path in Binary Matrix (LC 1091)

[Shortest Path in Binary Matrix](https://leetcode.com/problems/shortest-path-in-binary-matrix/) (LC 1091): in an n × n grid of 0s and 1s, find the length of the shortest path of 0-cells from the top-left to the bottom-right, moving in eight directions, counting cells. Return -1 if there is none.

**Pattern:** BFS on a grid. **Deltas:** eight directions instead of four, and the length counts cells, so the start is 1, not 0.

```python
from collections import deque

def shortest_path_binary_matrix(grid):
    n = len(grid)
    if grid[0][0] == 1 or grid[n - 1][n - 1] == 1:
        return -1
    dirs8 = [(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if (dr, dc) != (0, 0)]
    dist = {(0, 0): 1}
    q = deque([(0, 0)])
    while q:
        r, c = q.popleft()
        if (r, c) == (n - 1, n - 1):
            return dist[(r, c)]
        for dr, dc in dirs8:
            nr, nc = r + dr, c + dc
            if 0 <= nr < n and 0 <= nc < n and grid[nr][nc] == 0 and (nr, nc) not in dist:
                dist[(nr, nc)] = dist[(r, c)] + 1
                q.append((nr, nc))
    return -1
```

`[[0, 1], [1, 0]]` gives 2; `[[0, 0, 0], [1, 1, 0], [1, 1, 0]]` gives 4; `[[0]]` gives 1; `[[1]]` gives -1.

*Invariant:* every cell in `dist` holds its true shortest length, because it was set on the first discovery and BFS discovers in order of distance. Testing the target when it is popped, not when it is pushed, also handles `[[0]]`, where the start is the target, with no special case.

## Multi-source BFS

Some problems ask for **the distance from every cell to the nearest special cell**. One BFS per cell is far too slow: a 200 × 200 grid has 40,000 cells, so one walk per cell is about 1.6 × 10⁹ cell visits, against 40,000 for a single walk.

> **Put every source in the queue at distance 0, then run one ordinary BFS.** The queue still holds distance d before distance d + 1, so the first time any cell is discovered, it is discovered from its nearest source.

Think of it as one invisible super-source with an edge of length 0 to every real source. The BFS from that super-source is an ordinary BFS, and its first level is all the real sources.

```python
from collections import deque

def multi_source_bfs(n, adj, sources):
    dist = [-1] * n                      # -1: not reached yet
    q = deque()
    for s in sources:
        dist[s] = 0                      # every source, at distance 0, before the loop
        q.append(s)
    while q:
        u = q.popleft()
        for v in adj[u]:
            if dist[v] == -1:            # the distance list is the visited set
                dist[v] = dist[u] + 1
                q.append(v)
    return dist
```

On a grid, the cells are the nodes (cell `(r, c)` is node `r * cols + c`) and a cell's in-bounds neighbours, up to four, are its `adj`; nothing else in the function changes.

On a 3 × 3 grid with sources at the top-left and bottom-right corners, `sources = [0, 8]`, the distances fill in like this, one BFS level at a time:

```
level 0     level 1     level 2
0 . .       0 1 .       0 1 2
. . .       1 . 1       1 2 1
. . 0       . 1 0       2 1 0
```

The centre and the two remaining corners are all distance 2. Each is reached by whichever source's wave gets there first, and since the waves move in lockstep, that is the nearer one.

**The test is `dist[v] == -1`, never `dist[v] == 0`.** Zero is a real distance here: the sources have it. Testing for 0 to mean "unvisited" sends the BFS back into the sources. It's the property-not-route rule again: a source's distance is 0, so the sources satisfy "already has a distance" without anyone having reached them.

## The inversion: start from the special thing

Some problems ask a question about **every** node, and the answer depends on whether that node can reach some **special** set S: the border of a grid, a set of exits, a sink.

**Why the forward way fails.** Launching one traversal from each node to ask "can I reach the special set?" repeats the same work from every start. That's O(V) traversals, O(V × (V + E)) in total, and each one needs its own visited set, since what node u reached says nothing final about node w.

**The move:** "u can reach S" is the same fact as "S can reach u in the graph with every edge reversed". So reverse the edges and seed one traversal with **all of S** at once: every node it marks is a node that reaches S, and one traversal answers the question for every node. On an undirected graph, or a grid where every move can be made both ways, the reversed graph is the graph itself, and you traverse it as given.

> **A reaches S ⇔ S reaches A in the reversed graph. Seed with all of S.**

| | Traversals | Visited | Time |
|---|---|---|---|
| Forward, one search per node | V | a fresh set for each | O(V × (V + E)) |
| Reversed, one search from S | 1 per seed set | one shared set | O(V + E) |

On a 200 × 200 grid that is about 1.6 × 10⁹ cell visits against 4 × 10⁴.

Reversing the edges is one loop over the adjacency list:

```python
radj = [[] for _ in range(n)]
for u in range(n):
    for v in adj[u]:
        radj[v].append(u)                # u→v becomes v→u

def reached_from(seeds):                 # every node that can reach one of the seeds
    seen = set(seeds)
    stack = list(seeds)
    while stack:
        u = stack.pop()
        for v in radj[u]:
            if v not in seen:
                seen.add(v)
                stack.append(v)
    return seen
```

**What disappears:** the per-start visited sets, the repeated work, and the bookkeeping for "was this region already known to escape?". What remains is one traversal and one pass to read off the answer.

### The two shapes

Once the marks are in, the answer is read off them in one of two ways:

| Shape | Seed sets | Traversals | The answer |
|---|---|---|---|
| **Intersect** | two, S₁ and S₂ | one reversed traversal from each, each with its own visited set | the nodes reached by both, `A & B` for the two reached sets A and B |
| **Complement** | one, S | one reversed traversal | the nodes **not** reached |

Take the directed graph 0→1, 1→2, 1→3, 4→3, 5→4 (a node counts as reaching itself).

- **Intersect:** which nodes can reach both node 2 and node 3? `reached_from([2])` is {0, 1, 2} and `reached_from([3])` is {0, 1, 3, 4, 5}, so `A & B` is {0, 1}. Checked forward: 0 and 1 reach both, and 4 and 5 reach 3 but never 2. Two traversals, not six.
- **Complement:** which nodes can't reach node 2? `reached_from([2])` is {0, 1, 2}, so the answer is the rest, {3, 4, 5}.

The two worked problems below are the complement shape on a grid, where every move goes both ways and nothing needs reversing.

### Worked: Number of Enclaves (LC 1020)

[Number of Enclaves](https://leetcode.com/problems/number-of-enclaves/) (LC 1020): in a grid of 0 (sea) and 1 (land), count the land cells from which you cannot walk off the edge of the grid.

**Pattern:** the inversion, complement shape. **Delta:** the special set is the land on the border, and the answer is a count of what it can't reach.

```python
DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))

def enclaves(grid):
    rows, cols = len(grid), len(grid[0])

    def sink(r, c):
        if not (0 <= r < rows and 0 <= c < cols):
            return
        if grid[r][c] != 1:
            return
        grid[r][c] = 0                   # mark by overwriting: this land can walk off
        for dr, dc in DIRS:
            sink(r + dr, c + dc)

    for r in range(rows):
        for c in range(cols):
            if r in (0, rows - 1) or c in (0, cols - 1):
                sink(r, c)
    return sum(map(sum, grid))           # every 1 left could not reach the edge
```

The first example in the statement gives 3, the second 0.

**Depth.** The worst-case depth of `sink` is the number of cells, and the grid can be 500 × 500: an all-land grid is up to 250,000 nested calls, far past Python's default limit of about 1,000 ([§Recursion depth is arithmetic](#recursion-depth-is-arithmetic)). Say so, and write `sink` with an explicit stack ([§Why an explicit stack survives](#why-an-explicit-stack-survives)). Raising the limit is the other way out, and the same section says why it only moves the cliff.

### Worked: Number of Closed Islands (LC 1254)

[Number of Closed Islands](https://leetcode.com/problems/number-of-closed-islands/) (LC 1254): here 0 is land and 1 is water. A closed island is a group of land cells entirely surrounded by water, so it touches no edge. Count them.

**Pattern:** the inversion, complement shape, then components. **Deltas:** the cell values are swapped, and the answer is a count of regions, not of cells.

```python
def closed_islands(grid):
    rows, cols = len(grid), len(grid[0])

    def fill(r, c):
        if not (0 <= r < rows and 0 <= c < cols):
            return
        if grid[r][c] != 0:
            return
        grid[r][c] = 1                   # land becomes water: marked
        for dr, dc in DIRS:
            fill(r + dr, c + dc)

    for r in range(rows):
        for c in range(cols):
            if r in (0, rows - 1) or c in (0, cols - 1):
                fill(r, c)               # pass 1: remove every island that touches an edge
    count = 0
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == 0:          # pass 2: what's left is closed
                count += 1
                fill(r, c)
    return count
```

The three examples in the statement give 2, 1 and 2.

**Depth.** The worst-case depth of `fill` is the number of cells, and the grid can be 100 × 100: an all-land grid is up to 10,000 nested calls, past Python's default limit of about 1,000 ([§Recursion depth is arithmetic](#recursion-depth-is-arithmetic)). Say so, and write `fill` with an explicit stack ([§Why an explicit stack survives](#why-an-explicit-stack-survives)). Raising the limit is the other way out, and the same section says why it only moves the cliff.

Guard 2 went from `!= 1` to `!= 0` between the two problems, because the cell values swapped meaning: the rule from §Grids are graphs, that guard 2 is rewritten from each statement, in its smallest form.

**The general question to ask:** *is there a small set of nodes that every answer is defined relative to?* If so, start there. Multi-source BFS is the same idea applied to distances: start from the sources, not from every cell.

## Undirected cycles: carry the parent

A plain visited-set DFS can't test an undirected graph for a cycle, because **every undirected edge is stored twice**. Walk 0 to 1, and 1's neighbour list contains 0, which is visited, so the DFS reports a cycle on a single edge.

> **The fix is to remember the one neighbour you are allowed to see again: the node you came from.**

```python
def has_cycle_undirected(n, adj):
    visited = set()

    def dfs(u, parent):
        visited.add(u)
        for v in adj[u]:
            if v == parent:
                continue                 # the edge you arrived on, seen from the other end
            if v in visited:
                return True              # a second way into a visited node: a cycle
            if dfs(v, u):
                return True
        return False

    for u in range(n):
        if u not in visited and dfs(u, -1):
            return True
    return False
```

A single edge `0 – 1` gives False, a triangle gives True. Two parallel copies of the edge `0 – 1` give True, as they should: two edges between the same pair form a cycle of length two. The check fires from the parent's side: when 1 is done, 0's loop reaches the second copy of the edge, sees 1 visited, and 1 is not 0's parent.

`return dfs(...)` would be wrong here for the reason in §`return` inside the neighbour loop. `if dfs(v, u): return True` returns only on success and otherwise lets the loop go on.

**Why this isn't enough in a directed graph.** The parent trick answers "have I seen this node by any route other than the edge I just used?". In a directed graph, being visited by another route is not a cycle at all: the diamond has two routes into D and no cycle. A directed graph needs a different question, and a third state to answer it.

## Directed cycles: three colours

On the diamond, A→B, A→C, B→D, C→D, run a DFS with a plain visited set and report a cycle on any visited neighbour. It goes A, B, D, back up, then C, and C's neighbour D is visited. A two-state test says "cycle". There isn't one: D was finished long ago, in a different branch.

The question a directed cycle test needs is not *"have I ever been here?"* but *"am I on the path to here right now?"* A cycle exists exactly when the DFS meets a node that is still open below it on the current path: an edge back to an ancestor.

```python
WHITE, GREY, BLACK = 0, 1, 2             # unvisited, on the current path, finished

def has_cycle(n, adj):
    color = [WHITE] * n

    def dfs(u):
        color[u] = GREY                  # on entry: u joins the current path
        for v in adj[u]:
            if color[v] == GREY:
                return True              # v is open above u: an edge back into the path
            if color[v] == WHITE and dfs(v):
                return True
        color[u] = BLACK                 # last line: u is finished, and clean
        return False

    for u in range(n):
        if color[u] == WHITE and dfs(u):
            return True
    return False
```

On the diamond it returns False, as it should; with only a visited set, the same graph returns True.

### GREY is the per-path mark, BLACK makes it permanent

**GREY is backtracking's per-path mark from module 07** ([07-backtracking.md, §The per-path mark](07-backtracking.md#the-per-path-mark)): on while the node is on the current path, off when it leaves. **BLACK makes it permanent.** A node that comes off the path doesn't go back to WHITE, because everything below it has been checked and found clean, and that result is still true the next time some other path reaches it. A per-path mark that stays on is the graph's visited set; here it stays on with a different colour, so the two questions get two answers.

**The acid test** for which mark you need: *if a second path reaches this node, should it be explored again?* In backtracking, yes, because a different path is a different answer, so the mark comes off. In a graph, no, because the node's answer doesn't depend on how you reached it, so the mark stays.

| Question | States | Mark |
|---|---|---|
| have I ever been here? | 2: unseen, seen | `visited` |
| am I on the current path? | 2: on, off | GREY, removed when the path leaves |
| both | 3 | WHITE, GREY, BLACK |

**Drop BLACK and it still works, slowly.** Un-mark the node when it finishes, back to WHITE, and every answer is still correct. But each finished node is explored again from every path that reaches it, which is the diamond problem from §0.2. On a chain of 10 diamonds, the `has_cycle` above with that one line changed makes 16,299 calls, against 31 with BLACK: one DFS from the top already makes 4,093, 2^(k+2) − 3 for k diamonds, and the outer loop then starts again from every node, because every node is WHITE again. **BLACK is a memo:** the stored answer for "is there a cycle below this node?". That idea comes back later, in module 09 ([09-dp.md](09-dp.md)), as the memo of a top-down DP.

> **When a question needs one more thing to be true, add a state, don't add a special case.** Two-state DFS gets the diamond wrong; no `if` fixes it, and a third colour does.

**`color[u] = BLACK` goes after the loop, and nowhere else.** Indent it one level, into the `for` loop, and a node goes BLACK after its first neighbour; a node with no out-edges never runs the loop body, so it is never coloured BLACK and stays GREY. The next path to reach it sees GREY and reports a cycle that isn't there: the diamond returns True. It's [bug-checklist.md](../reference/bug-checklist.md#placement-the-right-line-in-the-wrong-scope), §Placement: the right line in the wrong scope.

**Test `== WHITE` before recursing, not `!= GREY`.** BLACK means already proved clean. Recursing into a BLACK node redoes its whole subtree, and on a dense graph that is the exponential blow-up again.

### The two-set form

The same three states can live in two sets instead of a colour list: `path` holds the GREY nodes, and `visited` holds every node that has been entered. A node in `visited` but not in `path` is BLACK. Topological sort is often written this way, with the post-order appended where the node goes BLACK:

```python
def topo_order(n, adj):
    path, visited, order = set(), set(), []

    def dfs(u):
        if u in path:
            return False                 # back into the current path: a cycle
        if u in visited:
            return True                  # finished before, and clean
        path.add(u)
        visited.add(u)
        for v in adj[u]:
            if not dfs(v):
                return False
        path.remove(u)                   # u leaves the path: GREY to BLACK
        order.append(u)                  # post-order: u after everything it points to
        return True

    for u in range(n):
        if not dfs(u):
            return None                  # None: there is a cycle, so no order exists
    return order[::-1]
```

It returns `None`, not a list, when there is no order: an empty list would also be the right answer for a graph with no nodes, and `None` can't be mistaken for an order.

**The order of the two tests is load-bearing.** `path` must be tested first. A GREY node is in both sets, so testing `visited` first returns True for it, and the cycle is never seen: on two nodes with a self-loop on node 0, the swapped version returns `[1, 0]` instead of `None`. The colour list can't have this bug, because a node holds exactly one colour. §Where the guards go in the two-set form has the details.

### Reading the colours as an answer

The colours aren't only a yes-or-no cycle test. When the DFS ends, a BLACK node is one from which no path leads into a cycle, and that set is sometimes the answer itself.

### Worked: Find Eventual Safe States (LC 802)

[Find Eventual Safe States](https://leetcode.com/problems/find-eventual-safe-states/) (LC 802): `graph[i]` lists the nodes i has edges to. A node is safe if every path from it ends at a node with no outgoing edges. Return the safe nodes in increasing order.

**Pattern:** three colours. **Delta:** you want the per-node verdict, not one bool. A node is safe exactly when no path from it reaches a cycle, which is what BLACK records.

```python
WHITE, GREY, BLACK = 0, 1, 2

def eventual_safe_nodes(graph):
    n = len(graph)
    color = [WHITE] * n

    def safe(u):
        if color[u] != WHITE:
            return color[u] == BLACK     # GREY: on the current path, so a cycle
        color[u] = GREY
        for v in graph[u]:
            if not safe(v):
                return False             # u stays GREY: it can reach a cycle
        color[u] = BLACK
        return True

    return [u for u in range(n) if safe(u)]
```

`[[1, 2], [2, 3], [5], [0], [5], [], []]` gives `[2, 4, 5, 6]`; `[[1, 2, 3, 4], [1, 2], [3, 4], [0, 4], []]` gives `[4]`; `[[0]]` gives `[]`; `[[]]` gives `[0]`.

*Invariant:* a node that leaves GREY becomes BLACK only if every neighbour returned True. A node that returns False stays GREY on purpose, and the early `return False` is what keeps it GREY: any later path that reaches it sees GREY and correctly learns "unsafe".

The same answer comes out of Kahn's algorithm, but not on the graph as given. Run on the original edges, Kahn's peels off nodes with no cycle **upstream**. Safety is about what lies **downstream**, so you reverse every edge, as in §The inversion: start from the special thing, start from the nodes with no outgoing edges, and the nodes Kahn's reaches are the safe ones.

### One start is never enough

Like the component count, a cycle test needs the outer loop. With edges 0→1, 2→3 and 3→2, a DFS from node 0 alone returns False. The cycle is in a component node 0 can't reach. The loop `for u in range(n): if color[u] == WHITE and dfs(u)` finds it. Skipping nodes that aren't WHITE is not just a speed-up: it is also what keeps a BLACK node from being restarted as if it were new.

## Topological sort

**A topological order** lists a DAG's nodes so that every edge points forward: for each edge u→v, u comes before v. It exists exactly when the graph has no directed cycle, so every topological sort is also a cycle test.

### Kahn's algorithm

> **Repeatedly take a node with no remaining incoming edges, output it, and delete its outgoing edges.**

```python
from collections import deque

def kahn(n, adj):
    indeg = [0] * n
    for u in range(n):
        for v in adj[u]:
            indeg[v] += 1
    q = deque(u for u in range(n) if indeg[u] == 0)
    order = []
    while q:
        u = q.popleft()
        order.append(u)
        for v in adj[u]:
            indeg[v] -= 1                # delete the edge u→v
            if indeg[v] == 0:
                q.append(v)              # v's last prerequisite is done
    return order if len(order) == n else None   # None: there is a cycle
```

On the diamond, a→b, a→c, b→d, c→d:

| Step | Pop | Effect | Queue after |
|---|---|---|---|
| start | | indegrees a 0, b 1, c 1, d 2 | [a] |
| 1 | a | b and c drop to 0 | [b, c] |
| 2 | b | d drops to 1 | [c] |
| 3 | c | d drops to 0 | [d] |
| 4 | d | | [] |

The order is `[a, b, c, d]`. Add an edge d→a and nothing starts with indegree 0: the queue starts empty, nothing is output, and `kahn` returns `None`.

**The cycle test is free.** A node on a cycle always has an incoming edge from the node before it on the cycle, and that node can't be output until it is free itself, so no node on the cycle ever reaches indegree 0. **If the order is shorter than n, the graph has a cycle**, and the missing nodes are on a cycle or downstream of one. With edges 0→1, 1→2, 2→1, 2→3 and 4→3, Kahn's outputs 0 and 4, then runs out of ready nodes: `order` is `[0, 4]`, 2 nodes out of 5, so `kahn` returns `None`.

*Invariant:* `indeg[v]` is the number of v's incoming edges whose source has not been output yet. A node is pushed exactly when that reaches 0, so each node is pushed at most once, and the indegree is the visited set: there is no other one.

### The DFS form: post-order, reversed

A node's DFS finishes only after everything reachable from it has finished. So in post-order, every node appears **after** everything it points to, and reversing the post-order puts every edge forward. The two-set `topo_order` above is this algorithm: three colours to catch cycles, `order.append(u)` on the line where u goes BLACK, and `order[::-1]` at the end.

### Choosing between the two

Both are O(V + E) and both detect cycles. Pick on what the problem needs from the order:

| If you need | Use | Why |
|---|---|---|
| the order processed in waves, or the number of waves | Kahn's | each round of the queue is one wave |
| the lexicographically smallest order | Kahn's with a heap | §The lexicographically smallest order |
| no recursion, on a deep graph | Kahn's | it is a loop |
| a node "becomes ready" when its prerequisites are done | Kahn's | the indegree counter is that sentence |
| a per-node verdict, like "can this node reach a cycle?" | three colours | the colours are the verdict |
| the DFS is already written | the DFS form | one extra line |
| no indegree pass | the DFS form | it needs only `adj` |

**Two non-reasons.** Neither is faster, and neither is "more correct on cycles": both find every cycle. And neither gives a unique order. Most DAGs have many valid orders, and a checker accepts any of them, so the order your code prints differs from the example's for no fault of yours.

### Kahn's against BFS

Kahn's looks like BFS, a queue and a neighbour loop, and differs in one test:

| | BFS | Kahn's |
|---|---|---|
| A node is pushed when | **any** neighbour reaches it | **all** its incoming edges are used up |
| The frontier starts with | the source | every node of indegree 0 |
| A "level" means | the distance from the source | the earliest wave in which the node can be done |
| The visited set | `visited` or `dist` | `indeg[v] == 0` |

**Levels differ.** On A→B, A→C, B→C, BFS from A gives the levels `[[A], [B, C]]`: C is one edge away. Kahn's gives `[[A], [B], [C]]`: C has to wait for B. If a problem asks for the fewest rounds when everything can run in parallel once its prerequisites are done, the number of Kahn's waves is the answer, and it equals the number of nodes on the longest path, not the shortest.

### Peeling leaves

Kahn's idea, removing nodes that are no longer held in, works on undirected graphs too, with **degree 1** in place of indegree 0. Peeling the leaves of a tree layer by layer works inward from every edge at once, and the last layer standing is the middle.

### Worked: Minimum Height Trees (LC 310)

[Minimum Height Trees](https://leetcode.com/problems/minimum-height-trees/) (LC 310): a tree has n nodes labelled 0 to n − 1. Rooting it at different nodes gives trees of different heights. Return every root that gives the minimum height.

**Pattern:** Kahn's algorithm on an undirected graph. **Deltas:** the degree-1 nodes are the starting queue, and the answer is the last layer, not the order.

```python
def find_min_height_trees(n, edges):
    if n == 1:
        return [0]                       # one node, no edges: no leaves to start from
    adj = [[] for _ in range(n)]
    for u, v in edges:
        adj[u].append(v)
        adj[v].append(u)
    degree = [len(adj[u]) for u in range(n)]
    leaves = [u for u in range(n) if degree[u] == 1]
    remaining = n
    while remaining > 2:
        remaining -= len(leaves)
        new_leaves = []
        for leaf in leaves:
            for v in adj[leaf]:
                degree[v] -= 1
                if degree[v] == 1:
                    new_leaves.append(v)
        leaves = new_leaves
    return leaves
```

A path 0–1–2–3–4 gives `[2]`; a path of four nodes gives `[1, 2]`; a star centred at 0 gives `[0]`; n = 2 gives `[0, 1]`.

*Invariant:* `leaves` holds exactly the current degree-1 nodes of the tree that remains, and `remaining` counts that tree's nodes.

**Why `remaining > 2` and not `while leaves:`.** The middle of a tree is one node or two. With `while leaves:` the loop peels the last layer too, and on the path 0–1–2–3–4 the answer comes out `[]`. Stop while at most two nodes remain, and what's left is the answer.

**Why `n == 1` needs its own line.** A single node has degree 0, so it is never a leaf, the queue starts empty, and without the guard the function returns `[]`. The guard is a genuine case the structure can't express, not a patch.

## Union-find

Union-find, or disjoint-set union, keeps a forest in which every component is one tree, named by its root. Two operations: `find(x)` returns the root of x's component, and `union(a, b)` merges two components by hanging one root under the other.

```python
parent = list(range(n))                  # every node starts as its own root
size = [1] * n

def find(x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]    # path halving: point at the grandparent
        x = parent[x]
    return x

def union(a, b):
    ra, rb = find(a), find(b)
    if ra == rb:
        return False                     # already in one component
    if size[ra] < size[rb]:
        ra, rb = rb, ra
    parent[rb] = ra                      # hang the smaller tree under the larger
    size[ra] += size[rb]
    return True
```

*Invariant:* a and b are in the same component if and only if `find(a) == find(b)`, and `parent[x] == x` exactly for the roots. `union` returns True when it merged two components and False when there was nothing to merge.

**The traps:**

- **Link roots, not nodes.** `parent[a] = b` joins a to b's component but leaves the rest of a's old component behind. Always `find` both first.
- **Compare roots, not parents.** `parent[a] == parent[b]` is True only if both happen to sit one step below the same root.
- **`parent = list(range(n))`, not `[0] * n`.** The zeros list makes every node a child of 0 before a single union.
- **Counting components:** start at n and subtract one on every union that returns True. Counting the roots at the end is also correct, but the running count needs no second pass.

**Complexity.** With path halving and union by size, each operation is O(α(n)) amortised, where α is the inverse Ackermann function: below 5 for any input that fits in the universe, so treat it as O(1). With neither, a tree can become a chain and `find` costs O(n). With only one of the two, it is O(log n). Say the name of the bound and what makes it hold; nobody wants the proof.

### Worked: Number of Operations to Make Network Connected (LC 1319)

[Number of Operations to Make Network Connected](https://leetcode.com/problems/number-of-operations-to-make-network-connected/) (LC 1319): n computers and a list of cables, each joining two computers. You may unplug any cable and plug it between any two computers. Return the fewest moves needed to connect every computer, or -1 if it can't be done.

**Pattern:** union-find, counting components. **Deltas:** a counting fact decides the -1 before any union, and the answer is a count of components, not a bool.

```python
def make_connected(n, connections):
    if len(connections) < n - 1:
        return -1                        # n computers in one piece need at least n − 1 cables
    parent = list(range(n))
    size = [1] * n

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra == rb:
            return False
        if size[ra] < size[rb]:
            ra, rb = rb, ra
        parent[rb] = ra
        size[ra] += size[rb]
        return True

    components = n
    for a, b in connections:
        if union(a, b):
            components -= 1
    return components - 1                # one moved cable joins two components
```

n = 4 with `[[0, 1], [0, 2], [1, 2]]` gives 1. n = 6 with `[[0, 1], [0, 2], [0, 3], [1, 2], [1, 3]]` gives 2. n = 6 with four cables gives -1.

**Why the count is enough.** There are always enough spare cables once the first test passes: k components need k − 1 joining cables, and with at least n − 1 cables in total, the cables that were not needed inside a component number at least k − 1. So the answer is the number of components minus one, and no cable has to be named.

### Union-find or DFS?

Both answer connectivity. They differ in what they're good at:

| Question | Better tool | Why |
|---|---|---|
| how many components, on a fixed graph | either | both are O(V + E) or near it |
| are u and v connected, asked again and again while edges keep arriving | union-find | each query is about O(1); a DFS would rerun |
| does adding this edge close a cycle (undirected) | union-find | `union` returns False |
| the shortest path, or the distance | BFS | union-find knows nothing about paths |
| the edges arrive one at a time, and the graph is never built | union-find | it needs only the pair |
| anything directed: cycles, order, reachability | DFS or Kahn's | union-find has no direction |
| removing edges | DFS | union-find can merge, never split |
| the components themselves, listed | DFS | union-find gives roots; listing needs a pass |

**Union-find is the wrong tool** whenever the edges have a direction, whenever an edge can be deleted, and whenever you need a path rather than a yes or no.

## Weighted graphs: Dijkstra and Prim

### The claim weights withdraw

BFS rests on one claim: *the first time a node is reached is the cheapest.* With every edge costing 1, it's true, because the queue hands out nodes in order of distance. With weights it's false, and §Why BFS never needs a relaxation test showed the counterexample: one edge of cost 10 beats two edges of cost 1 on edge count and loses on cost.

So the marker has to change. BFS marks on push. With weights you can't, because a node's distance may still improve after it is pushed. And you can't drop the marker either: §Four ideas on the way to Dijkstra walks through what happens without one. **You need a different marker, put on at a different moment.**

### Dijkstra

> **Dijkstra is BFS with a min-heap instead of a queue.** The heap hands out the node with the smallest known distance first, and **the first time a node is popped, its distance is final.**

A heap is a structure whose `heappop` returns the smallest item in O(log n), and `heappush` adds one in O(log n). That is all Dijkstra needs from it here; you'll see how a heap works later, in module 10 ([10-heaps.md](10-heaps.md)).

```python
import heapq

def dijkstra(adj, src, n):               # adj[u] = [(v, weight), ...]
    dist = [float('inf')] * n
    dist[src] = 0
    done = [False] * n
    heap = [(0, src)]                    # (distance, node): the key goes first
    while heap:
        d, u = heapq.heappop(heap)
        if done[u]:
            continue                     # a stale copy, pushed before u's distance improved
        done[u] = True                   # mark on pop: d is final now
        for v, w in adj[u]:
            if d + w < dist[v]:
                dist[v] = d + w          # relax: a cheaper route to v
                heapq.heappush(heap, (d + w, v))
    return dist
```

**Why the first pop is final.** When u is popped with distance d, every other entry in the heap is at least d. Any other route to u leaves the finished nodes through some entry still in the heap, which already costs at least d, and the weights are non-negative, so the route can only grow from there. Nothing can beat d. That argument needs non-negative weights; with a negative edge it fails, and Dijkstra's answers can be wrong.

**A trace.** An undirected graph with the edges A–B 4, A–C 1, B–C 2, B–D 1, C–D 5, D–E 3, A–E 6, from A:

| Step | Pop | `done`? | What happens | dist after |
|---|---|---|---|---|
| 1 | (0, A) | new | push (4, B), (1, C), (6, E) | A 0, B 4, C 1, E 6 |
| 2 | (1, C) | new | B improves to 3, push (3, B); push (6, D) | B 3, D 6 |
| 3 | (3, B) | new | D improves to 4, push (4, D) | D 4 |
| 4 | (4, B) | B done | stale: skip | |
| 5 | (4, D) | new | E stays 6: 4 + 3 = 7 is no better | |
| 6 | (6, D) | D done | stale: skip | |
| 7 | (6, E) | new | nothing improves | |

Final: A 0, B 3, C 1, D 4, E 6. B was pushed at 4 and improved to 3 while the first copy sat in the heap. That improvement is exactly what BFS couldn't handle.

**Lazy deletion.** The heap can't update an entry's key, so when a distance improves you push a new entry and leave the old one in. The old one surfaces later as a stale copy, and `if done[u]: continue` throws it away. That's why the heap can hold up to E entries, and why the time is **O((V + E) log V)**: each edge pushes at most once, each push and pop is O(log E), and log E ≤ 2 log V.

### `done` is not a cycle guard

In BFS, `visited` stops a node from being processed twice. In Dijkstra, the relaxation test `d + w < dist[v]` already stops a walk round a cycle, because coming back around a cycle never makes a distance smaller. So what does `done` do?

> **`done` stops a stale heap entry from being processed again.** Without it, a node is popped once per copy, and each pop re-scans its edges.

The distances stay correct without it, because a stale pop relaxes nothing that hasn't already been relaxed. Only the work grows: on the graph above, the version with `done` scans 14 adjacency entries and the version without scans 20. On a graph where nodes are pushed many times, the waste is a factor of the number of copies. Checking `if d > dist[u]: continue` instead of keeping a `done` list does the same job.

**`(distance, node)`, not `(node, distance)`.** Tuples compare from the left, so the heap orders by the first field. Push `(node, distance)` and the heap hands out the lowest-numbered node first, not the closest. On the graph above, that ordering gives D a distance of 5 instead of 4. A small example often passes anyway, when the node numbers happen to rise with distance. It's [bug-checklist.md](../reference/bug-checklist.md#the-heap-tuple-in-the-wrong-order), §The heap tuple in the wrong order.

### Prim is Dijkstra with one line changed

A **minimum spanning tree** connects every node of an undirected weighted graph using the edges of smallest total weight. Prim's algorithm grows it from one node, always adding the cheapest edge that reaches a node not yet in the tree.

```python
import heapq

def prim(adj, n):                        # adj[u] = [(v, weight), ...], undirected
    in_tree = [False] * n
    heap = [(0, 0)]                      # (cost to attach, node)
    total = 0
    while heap:
        c, u = heapq.heappop(heap)
        if in_tree[u]:
            continue                     # a stale entry: u is attached already
        in_tree[u] = True
        total += c
        for v, w in adj[u]:
            if not in_tree[v]:
                heapq.heappush(heap, (w, v))   # the one line that differs: w, not d + w
    return total
```

**The one delta:** Dijkstra pushes `d + w`, the cost of the whole path from the source; Prim pushes `w`, the cost of the one edge that attaches v. Everything else, the heap, the mark on pop, the stale-entry skip, is the same.

**The tuple order is a statement of what you minimise and what you need back.** The first field is the thing the heap must order by, a path length or an edge cost. The second is what you need when it comes out, the node.

On the graph above, Prim from A pops (0, A), (1, C), (2, B), (1, D), (3, E), then three stale entries, (4, B), (5, D), (6, E). The total is 7. Without the `in_tree` skip, the stale entries are added too and the total comes out 22. With the tuple reversed, it comes out 9.

**Dijkstra's tree is not the MST.** The tree of cheapest paths from A uses the edge A–E 6, because 6 is the cheapest way to reach E from A, and its total weight is 10. The MST reaches E with D–E 3 instead, for a total of 7. One minimises each node's distance from the source; the other minimises the sum of the edges, and the two disagree.

**Kruskal's algorithm** finds the same tree from the other end: sort every edge by weight, and take each edge that joins two different components. That last test is union-find.

```python
def kruskal(n, edges):                   # edges = [(weight, u, v), ...]
    total, components = 0, n
    for w, u, v in sorted(edges):
        if union(u, v):                  # joins two components: keep it
            total += w
            components -= 1
    return total if components == 1 else -1
```

On the graph above it picks A–C 1, B–D 1, B–C 2 and D–E 3, for the same total of 7. If more than one component is left when the edges run out, the graph wasn't connected and there is no spanning tree.

**On a dense graph, skip the heap.** When every pair of nodes has an edge, E is about V², and the heap versions cost O(V² log V) time and O(V²) heap space. The array version of Prim keeps one best-cost entry per node and scans for the minimum each round, O(V²) time and O(V) space, with no heap at all:

```python
def prim_dense(n, w):                    # w[u][v] is the weight of u–v, inf if there is no edge
    best = [float('inf')] * n
    best[0] = 0
    in_tree = [False] * n
    total = 0
    for _ in range(n):
        u = min((x for x in range(n) if not in_tree[x]), key=lambda x: best[x])
        in_tree[u] = True
        total += best[u]
        for v in range(n):
            if not in_tree[v]:
                best[v] = min(best[v], w[u][v])
    return total
```

On the five-node graph above, as a matrix with `inf` for the missing edges, it also gives 7.

> **The heap is a win only when E ≪ V².** On a sparse graph, the heap's log factor beats scanning every node. On a complete graph there is nothing to skip, and the scan is cheaper.

---

## Every template, in one place

Ten templates, in this order, because each is a row above it with a single change. The skeleton is §BFS and DFS on a graph.

| Row | Template | The delta from the row above | Invariant | Time · space |
|---|---|---|---|---|
| 1 | recursive DFS | (§BFS and DFS on a graph): mark at the top of the call | every node in `visited` has been entered exactly once | O(V + E) · O(V), and the stack can be V deep |
| 2 | iterative DFS | the call stack becomes a list; mark on push | every node in `visited` has been pushed exactly once | O(V + E) · O(V) |
| 3 | BFS | `pop()` becomes `popleft()` on a deque | the queue holds nodes at distance d, then nodes at d + 1, and nothing else | O(V + E) · O(V) |
| 4 | BFS with distances | `visited` becomes `dist`, set on push | `dist[v]` is final the moment it is set | O(V + E) · O(V) |
| 5 | multi-source BFS | every source goes in at distance 0 before the loop | `dist[v]` is the distance to the nearest source | O(V + E) · O(V) |
| 6 | DFS carrying the parent | row 1 with `dfs(u, parent)`; skip the parent once | a visited neighbour other than the parent means a second way in: a cycle | O(V + E) · O(V) |
| 7 | three-colour DFS | row 1 with GREY on entry and BLACK after the loop; reverse the post-order for a topological order | GREY is exactly the current path; a BLACK node has no cycle below it | O(V + E) · O(V), the stack up to the longest chain |
| 8 | Kahn's algorithm | row 3 seeded with every indegree-0 node; push when the indegree hits 0 | `indeg[v]` counts v's incoming edges from nodes not yet output | O(V + E) · O(V) |
| 9 | Dijkstra | row 4 with a min-heap on distance; relax, and mark on pop | every `done` node holds its final distance; the heap holds candidates, some stale | O((V + E) log V) · O(V + E) |
| 10 | Prim | push `w` instead of `d + w`; add the cost on pop | the nodes `in_tree` are joined by the cheapest edges that attached them | O((V + E) log V) · O(V + E) |

> **Read it as one algorithm and nine deltas.**

Notes on the rows:

- **The outer loop wraps any row.** Rows 1 to 7 see only what their start reaches. Wrap them in `for u in range(n): if u not in visited:` for components, and for any cycle test (§Connected components, §One start is never enough). Row 8 doesn't need it: it seeds every indegree-0 node itself.
- **Union-find is not on the ladder** because it isn't a traversal. It never walks an edge twice, never needs `adj`, and answers only "same component?" (§Union-find). Kruskal is union-find over the edges in weight order.
- **Rows 9 and 10 are the only ones that mark on pop.** Everything else marks on push or at the top of the call, and that line position is the whole difference between them and BFS.

---

## How to attack a graph problem

1. **Are the edges weighted?** Unweighted, or every edge the same cost: BFS for distances. Non-negative weights: Dijkstra, marked on pop. "Connect everything as cheaply as possible": a minimum spanning tree, Prim or Kruskal.
2. **What is the output?** Connectivity, a shortest path, an order, a cycle, a per-node verdict, a spanning tree. If the statement says "minimum", ask *minimum what: steps, or total weight?*
3. **What is a node, and what is an edge?** One sentence each. On a grid: *"a node is a cell `(r, c)`, an edge is a shared side."* Then: are the neighbours stored or computed (§Grids are graphs)?
4. **Directed or undirected, and which way do the edges point?** Write the arrow down from the statement, then count the `append` lines in the build (§Representation).
5. **What does `visited` mean, and at which moment does a node enter it?** By a property, never by the route (§Define it by a property, never by the route). The moment is a line position: on push, at the top of the call, or on pop for Dijkstra.
6. **How many sources?** One, every node in turn (the outer loop), or a whole set at once (§Multi-source BFS). If the question is about every node reaching a special set, start from the set (§The inversion: start from the special thing).
7. **Recursion or not?** Work out the longest possible chain from the constraints and compare it with about 1,000 (§Recursion depth is arithmetic).
8. Write it.
9. **Run [bug-checklist.md](../reference/bug-checklist.md#the-30-second-pass), §The 30-second pass**, then §Common graph mistakes below. Then, specific to here: *is there a `return` in front of a call that returns nothing?* · *does my start node satisfy my own definition of visited?* · *for every variable I assigned, where is it read?*
10. **Trace the miss and the degenerate cases**, not the happy path: a node reachable by two routes, a node with no edges, a 1 × 1 grid, a grid that is all one region, and the start being the target.
11. **Say the complexity unprompted, time and space**, in the problem's nouns: *"O(rows × cols)"* on a grid, *"O(V²)"* on a matrix. Count the adjacency list you built and the call stack you didn't see. Then: *is it optimal?* (§Proving a traversal optimal).

---

## In depth

The derivations and counterexamples behind the rules above. Read them once, then come back when a rule stops making sense.

### Four ideas on the way to Dijkstra

The question: the cheapest distance from one node to every other, with non-negative weights. Four attempts, each fixing the one before:

| # | The idea | Correct? | Cost |
|---|---|---|---|
| 1 | a DFS that marks **edges** as used | no: overestimates | recursion depth up to E, not V |
| 2 | a DFS with **no marker**, which continues only while the distance improves | yes | exponential in the worst case |
| 3 | idea 2 with the adjacency list built once, instead of rescanning the edge list on every call | yes | the same calls, each O(deg) instead of O(E) |
| 4 | a min-heap, and mark on pop: **Dijkstra** | yes | O((V + E) log V) |

**Idea 1 is the route-based definition again.** Marking an edge as used says nothing about whether the node at its far end already has its best distance, and it lets a node be re-entered by every unused edge into it. On the five-node graph from §Dijkstra, with each neighbour list in the order the edges are listed, it gives B 4, C 9, D 19, E 16 against the true B 3, C 1, D 4, E 6, and its recursion reaches depth 15 on a graph of five nodes. The depth bound is now the number of directed edges, which is the arithmetic of §Recursion depth is arithmetic in a new place.

**Idea 2 is correct and still not good enough.** It has no marker at all, and it terminates because `dist[node]` only ever decreases, which is a monotone quantity, not a flag. That buys correctness and nothing else (§Why the relaxation DFS is exponential).

**Idea 3 changes no algorithm.** Scanning the whole edge list inside the recursion to find a node's neighbours turns every lookup into O(E). Building the adjacency list first removes that factor, and the speed-up can be an order of magnitude on its own. **Build the adjacency list before you traverse, always.**

**Idea 4 puts the marker back.** The ladder is: *a marker, then no marker, then a different marker.* Take the boolean away because "first arrival is best" is false with weights; put it back as `done` once the heap's pop order has made it true again.

### Why the relaxation DFS is exponential

```python
def relax_dfs(u, d):
    if d >= dist[u]:
        return                           # no improvement: stop
    dist[u] = d
    for v, w in adj[u]:
        relax_dfs(v, d + w)
```

It is easy to call this O(V · E), and that bound has to be earned by a mechanism, such as running a fixed number of rounds over every edge. This code has no rounds, so the bound doesn't apply. **A complexity bound is earned by a mechanism. Remove the mechanism and the bound goes with it.**

**The counterexample is a chain of diamonds.** Diamond i runs from `s_i` to `s_(i+1)` through two middle nodes: an expensive route of weight 2^(m − i), listed first, and a free route of weight 0. Every edge out of a middle node costs 0. The DFS takes the expensive route first everywhere, so it reaches the end of the chain with a distance that is too high, then improves it by a smaller amount at each level on the way back, and every improvement re-walks everything downstream:

| Diamonds m | Nodes | Calls |
|---|---|---|
| 3 | 10 | 29 |
| 5 | 16 | 125 |
| 10 | 31 | 4,093 |
| 15 | 46 | 131,069 |

That is exactly 2^(m+2) − 3 calls: exponential on 46 nodes. Make the expensive routes **grow** down the chain instead of shrinking, and m = 15 takes only 481 calls, because the late improvements are then too small to matter downstream and the search prunes. Building the counterexample is itself the proof that the pruning is doing real work, and that it doesn't always.

**On bounded weights it is pseudo-polynomial:** the number of calls grows with the size of the weights, not just with V and E. A bound that mentions the magnitude of the weights is a warning, not a bound. Say "pseudo-polynomial" out loud when you see one.

### Where the guards go in the two-set form

The colour version has two guards, and they do different jobs:

| Guard | What it saves | Kind |
|---|---|---|
| `if color[v] == WHITE` before recursing | re-exploring a subtree already proved clean | **asymptotic.** Without it, a dense DAG goes exponential. This is BLACK acting as a memo |
| `if color[u] != WHITE: continue` in the outer loop | restarting finished nodes | **a constant factor.** On a chain of 60 nodes, 119 calls without it and 60 with it |

> **BLACK is what keeps the algorithm linear. The outer guard is hygiene on top of it.** It also stops `color[u] = GREY` from un-finishing a BLACK node. In the code in §Directed cycles: three colours that is harmless, because every neighbour of a BLACK node is BLACK and nothing can observe the change, but code that is correct only because of a fact about the code around it is [bug-checklist.md](../reference/bug-checklist.md#the-right-line-kept-for-the-wrong-reason), §The right line kept for the wrong reason. State the rule instead.

In the two-set form the same two jobs are done by the order of the two tests at the top of `dfs`:

- **`if u in path: return False` comes first.** A GREY node is in both sets, so it has to be caught by the more specific test before the general one sees it.
- **`if u in visited: return True` comes second**, and it is the memo: a node in `visited` but not in `path` is BLACK, already proved clean.

Swap them, and a GREY node is answered by the `visited` test as "finished and clean". The back edge is never reported. With a self-loop on node 0, the swapped version returns the order `[1, 0]` for a graph that has no topological order.

### The lexicographically smallest order

When several nodes are ready at once, the order says nothing about which goes first. If a problem asks for the lexicographically smallest topological order, **use Kahn's algorithm with a min-heap in place of the queue**: at every step, output the smallest node that is ready.

On the DAG 0→1, 0→4, 1→3, 1→4, 2→4:

| Version | Order |
|---|---|
| Kahn's with a deque | `[0, 2, 1, 3, 4]` |
| Kahn's with a min-heap | `[0, 1, 2, 3, 4]` |
| DFS, nodes and neighbours visited in increasing order, post-order reversed | `[2, 0, 1, 4, 3]` |

The DFS form can't be fixed by sorting. Reversing a post-order puts the **last** node to finish first, and the last to finish is the root of the last DFS tree, here node 2, which the outer loop reached last precisely because it was the largest. Kahn's decides each position at the moment it is filled, so choosing the smallest ready node at each step is enough. The heap makes it O((V + E) log V).

### Proving a traversal optimal

> **Ask: what must any correct algorithm at minimum do?** That's a lower bound. If your solution matches it, it is optimal, and you have argued it rather than asserted it.

On a grid question whose answer can depend on any cell: *"To answer at all I have to look at every cell, so Ω(rows × cols) is a lower bound for any algorithm, and mine is O(rows × cols). It matches."* The same argument covers most traversal problems: **if the answer depends on every node and edge, you can't beat O(V + E)**, and you should say so instead of trailing off.

**A time lower bound says nothing about space.** Space is argued separately, and it usually has a trade rather than an optimum. For the distance from every cell to its nearest special cell:

| | Time | Extra space |
|---|---|---|
| multi-source BFS | **O(rows × cols)**, optimal | O(rows × cols) for the queue and `dist` |
| repeated full sweeps, each setting a cell to one more than its smallest neighbour, until nothing changes | O((rows × cols)²) | **O(1)**, if you may write into the grid |

**Neither dominates, and that table is the answer to "can you do it in constant space?"** Offering the trade unprompted is worth more than having picked the right row. **And name the term that isn't there:** BFS is iterative, so there is no call stack, unlike a recursive DFS, where the stack was a hidden O(rows × cols).

### Stacked special cases mean the structure dropped something

[As Far from Land as Possible](https://leetcode.com/problems/as-far-from-land-as-possible/) (LC 1162): in an n × n grid of 0 (water) and 1 (land), find the water cell farthest from its nearest land cell and return that distance. Return -1 if there is no land, or no water.

It is §Multi-source BFS with the land cells as the sources. The question is where to read the answer from. Count BFS rounds, and the count can't tell the cases apart: an all-land grid has one round of sources and no water to reach, so the counter gives 0 where the answer is -1, and the code grows a branch for it. Then another for the grid with no land. Each branch patches information the counter threw away. Read it off `dist` instead, which recorded every cell's distance with the sources included:

```python
return max((d for d in dist if d > 0), default=-1)
```

| | `[[1, 0, 1], [0, 0, 0], [1, 0, 1]]` | all land | no land |
|---|---|---|---|
| a round counter, read directly | 2 | **0, needs a branch** | -1, by the arithmetic of a counter that never ran |
| `dist`, read with the line above | 2 | -1 | -1 |

> **When you stack special cases at the end of a function, suspect the structure you're reading from.** Each branch is patching information the structure dropped. It's [bug-checklist.md](../reference/bug-checklist.md#a-structure-that-cant-express-the-answer), §A structure that can't express the answer, and the right structure usually already exists: here `dist` was correct all along, and the counter was a lossy copy of it. Keep one source of truth.

### Finish deciding before you act

A common grid task is to collect a group of cells, decide whether the whole group passes some test, and only then change every cell in it. The bug is acting inside the loop that decides:

```python
ok = True
for cell in group:
    if fails(cell):
        ok = False
    if ok:                               # ✗ inside the deciding loop
        change_all(group)
```

The loop does two jobs, deciding and acting, and the action fires before the disqualifying evidence arrives:

| Iteration | `fails(cell)`? | `ok` after | Action |
|---|---|---|---|
| 1 | no | still True | **changes the whole group** ✗ |
| 2 | yes | False | too late |

> **A flag computed by a loop is not trustworthy until that loop ends.** Reading it inside the loop reads a half-computed value.

Move the `if ok:` out by one level, after the loop. Better still, **delete the flag**, so there is nothing half-computed to read: `if not any(fails(cell) for cell in group): change_all(group)`. The line was right and its scope was wrong, which is [bug-checklist.md](../reference/bug-checklist.md#placement-the-right-line-in-the-wrong-scope), §Placement: the right line in the wrong scope.

---

## Common graph mistakes

| Mistake | What you see | Entry |
|---|---|---|
| BFS marking on pop | a node queued once per incoming edge; a distance set at push time overwritten | §Mark on push, or mark on pop? |
| `visited` created inside the outer loop | every node counted as its own component | §Connected components |
| `visited` defined by the route | the start node processed twice; a per-cell total too high | §Define it by a property, never by the route |
| Two structures recording "seen" | they disagree after the first edge case | [bug-checklist.md](../reference/bug-checklist.md#keep-one-source-of-truth), §Keep one source of truth |
| The second `append` missing on an undirected graph | components split in two; a node unreachable from its own neighbour | §Representation |
| The second `append` present on a directed graph | every cycle test says "cycle" | §Representation |
| An edge's direction read backwards | a perfect algorithm and a reversed answer | §Representation |
| `for u in adj` over a dict | isolated nodes never visited; `RuntimeError` when a lookup inserts a key | §Representation |
| `return dfs(...)` inside the neighbour loop | one path explored instead of the whole region | §`return` inside the neighbour loop |
| A recursive DFS on a large grid | `RecursionError` on the biggest input only | §Recursion depth is arithmetic |
| `sys.setrecursionlimit` as the fix | a crash with no exception instead of an exception | §Why an explicit stack survives |
| The cell read before the bounds test | a region that wraps round to the other side of the grid | [bug-checklist.md](../reference/bug-checklist.md#a-negative-index-wraps-instead-of-crashing), §A negative index wraps instead of crashing |
| Guard 2 copied from the last problem | water counted as land, or nothing counted | [bug-checklist.md](../reference/bug-checklist.md#guards-copied-from-another-problem), §Guards copied from another problem |
| `visited.add(grid[r][c])` | every land cell looks visited after the first | §Grids are graphs |
| An overwrite mark that still passes guard 2 | a fill that never stops, then `RecursionError` | §Flood fill and the guard order |
| `[[0] * cols] * rows` | one write lands in every row | §Marking by overwriting |
| An `adj` built for a grid | nothing visited; every cell its own component | §Grids are graphs |
| `dist[...] == 0` as "unvisited" in multi-source BFS | the BFS walks back into its sources | §Multi-source BFS |
| An undirected cycle test without the parent | a single edge reported as a cycle | §Undirected cycles: carry the parent |
| Two states for a directed cycle test | the diamond reported as a cycle | §Directed cycles: three colours |
| `color[u] = BLACK` inside the loop | sinks stay GREY; cycles that aren't there | [bug-checklist.md](../reference/bug-checklist.md#placement-the-right-line-in-the-wrong-scope), §Placement: the right line in the wrong scope |
| The `visited` test before the `path` test | real cycles missed; an order returned for a cyclic graph | §The two-set form |
| A cycle test from one start | a cycle in another component missed | §One start is never enough |
| Kahn's without the `len(order) == n` check | a partial order returned as if it were complete | §Kahn's algorithm |
| `while leaves:` when peeling | `[]` instead of the middle of the tree | §Peeling leaves |
| `parent[a] = b` in union-find | components half-merged | §Union-find |
| `parent = [0] * n` | every node in one component before any union | §Union-find |
| Dijkstra marked on push | the first, possibly worse, distance frozen | §Dijkstra |
| `(node, distance)` in the heap | wrong distances; the example in the statement still passes | [bug-checklist.md](../reference/bug-checklist.md#the-heap-tuple-in-the-wrong-order), §The heap tuple in the wrong order |
| Dijkstra on negative weights | a distance that is too high, with no error | §Dijkstra |
| "O(V × E)" for BFS | the two loops multiplied | §Each node once: the O(V + E) argument |
| "O(V + E)" on an adjacency matrix | the answer should be O(V²) | §Each node once: the O(V + E) argument |

---

## Drill set — cold, no IDE, no running

Each problem is ordered so that it adds exactly one new thing to the one before. The patterns are taught above on problems outside this table (Number of Provinces, Flood Fill, Shortest Path in Binary Matrix, the two inversion problems, Find Eventual Safe States, Minimum Height Trees, the network-cables example), except the rows that apply a template almost unchanged, which say so.

| # | Problem | Focus |
|---|---|---|
| 1 | [Number of Islands](https://leetcode.com/problems/number-of-islands/) (LC 200) | **The outer loop on a grid.** One shared `visited`, the four-part guard, and the depth arithmetic before you choose recursion. ⚑ **Checkpoint** |
| 2 | [Max Area of Island](https://leetcode.com/problems/max-area-of-island/) (LC 695) | **+ the traversal returns a value up.** The tree shape from [06-trees.md](06-trees.md#returning-a-value-up-the-tree), §Returning a value up the tree, on a grid |
| 3 | [Rotting Oranges](https://leetcode.com/problems/rotting-oranges/) (LC 994) | **Multi-source BFS.** |
| 4 | [Walls and Gates](https://leetcode.com/problems/walls-and-gates/) (LC 286) 🔒 | Premium — skip if locked, row 3 covers it |
| 5 | [Surrounded Regions](https://leetcode.com/problems/surrounded-regions/) (LC 130) | **The inversion.** This is the shape from §The inversion: start from the special thing |
| 6 | [Pacific Atlantic Water Flow](https://leetcode.com/problems/pacific-atlantic-water-flow/) (LC 417) | **The inversion again.** The hardest grid problem here |
| 7 | [Clone Graph](https://leetcode.com/problems/clone-graph/) (LC 133) | **Nodes are objects again.** There is no `range(n)` to index a list by, so decide what records "already handled" before you write the loop |
| 8 | [Number of Connected Components in an Undirected Graph](https://leetcode.com/problems/number-of-connected-components-in-an-undirected-graph/) (LC 323) 🔒 | **An edge list, counted both ways:** a traversal, then union-find. Premium: the free stand-in is [Count the Number of Complete Components](https://leetcode.com/problems/count-the-number-of-complete-components/) (LC 2685) |
| 9 | [Graph Valid Tree](https://leetcode.com/problems/graph-valid-tree/) (LC 261) 🔒 | **A definition with two halves.** Checking only one of them is the trap. Premium: if it's locked, do the network-cables example in §Union-find from memory instead |
| 10 | [Course Schedule](https://leetcode.com/problems/course-schedule/) (LC 207) | **Directed cycles.** Apply the template; the work is reading the input direction and the return value. ⚑ **Checkpoint** |
| 11 | [Course Schedule II](https://leetcode.com/problems/course-schedule-ii/) (LC 210) | **+ the order.** Apply the template; the work is reading the input direction and the return value |
| 12 | [Redundant Connection](https://leetcode.com/problems/redundant-connection/) (LC 684) | **Union-find, undisguised.** |
| 13 | [Word Ladder](https://leetcode.com/problems/word-ladder/) (LC 127) | **An implicit graph.** The neighbours are generated, and the obvious way to generate them is too slow |

**Why this order:** the grid problems come first, rows 1 to 6, because a grid is where BFS and DFS from module 06 are already strongest, and the only new idea is the visited set. Row 2 changes what the traversal hands back, row 3 changes how many starts it has, and rows 5 and 6 change where it starts from. Row 7 goes back to nodes as objects, which lands better once the plain set is automatic. Rows 8 and 9 move to edge lists, and to the first problem where union-find is an option. Rows 10 and 11 are directed graphs, the new content of this module. Row 12 is union-find on its own, and row 13 is last because it needs everything: BFS distances, an implicit graph, and a neighbour function you have to make fast.

**⚑ Checkpoint:** if row 1 doesn't come out clean without notes, stop there. Every grid row after it is this template with one thing changed, so reread §0.5, §Grids are graphs and §Connected components, and don't move on to row 2 until it does.

**⚑ Checkpoint:** row 10 is the first problem where two states are not enough. Everything before it is a tree with a visited set. If it doesn't come out clean, do row 11 anyway, then reread §Directed cycles: three colours and §Topological sort before row 12.

🔒 = LeetCode Premium. A 🔒 problem with a **Code it** button in the app can be solved there without Premium: the app brings its own statement and tests.

**Spares, if a shape needs a second rep:** [Flood Fill](https://leetcode.com/problems/flood-fill/) (LC 733, written out in §Flood fill and the guard order; a from-memory rep) · [Number of Provinces](https://leetcode.com/problems/number-of-provinces/) (LC 547, written out in §Connected components; a from-memory rep) · [01 Matrix](https://leetcode.com/problems/01-matrix/) (LC 542, the multi-source template almost unchanged; a from-memory rep) · [Find if Path Exists in Graph](https://leetcode.com/problems/find-if-path-exists-in-graph/) (LC 1971, the simplest edge-list traversal) · [Is Graph Bipartite?](https://leetcode.com/problems/is-graph-bipartite/) (LC 785, a third use for a colour array) · [Find Eventual Safe States](https://leetcode.com/problems/find-eventual-safe-states/) (LC 802, written out in §Directed cycles: three colours; a from-memory rep) · [Minimum Height Trees](https://leetcode.com/problems/minimum-height-trees/) (LC 310, written out in §Topological sort; a from-memory rep) · [Shortest Path in Binary Matrix](https://leetcode.com/problems/shortest-path-in-binary-matrix/) (LC 1091, written out in §Shortest path in an unweighted graph; a from-memory rep) · [Number of Operations to Make Network Connected](https://leetcode.com/problems/number-of-operations-to-make-network-connected/) (LC 1319, written out in §Union-find; a from-memory rep) · [Number of Enclaves](https://leetcode.com/problems/number-of-enclaves/) (LC 1020, written out in §The inversion: start from the special thing; a from-memory rep) · [Number of Closed Islands](https://leetcode.com/problems/number-of-closed-islands/) (LC 1254, written out in §The inversion: start from the special thing; a from-memory rep) · [As Far from Land as Possible](https://leetcode.com/problems/as-far-from-land-as-possible/) (LC 1162, discussed in §Stacked special cases mean the structure dropped something) · [Parallel Courses](https://leetcode.com/problems/parallel-courses/) (LC 1136) 🔒 · [Find All Possible Recipes from Given Supplies](https://leetcode.com/problems/find-all-possible-recipes-from-given-supplies/) (LC 2115).

**Tier 2, once the core lands:** [Reconstruct Itinerary](https://leetcode.com/problems/reconstruct-itinerary/) (LC 332) · [Min Cost to Connect All Points](https://leetcode.com/problems/min-cost-to-connect-all-points/) (LC 1584) · [Network Delay Time](https://leetcode.com/problems/network-delay-time/) (LC 743) · [Swim in Rising Water](https://leetcode.com/problems/swim-in-rising-water/) (LC 778) · [Alien Dictionary](https://leetcode.com/problems/alien-dictionary/) (LC 269) 🔒 · [Cheapest Flights Within K Stops](https://leetcode.com/problems/cheapest-flights-within-k-stops/) (LC 787). §Weighted graphs: Dijkstra and Prim has what the weighted ones need.

## Not covered here

- **Negative edge weights.** Dijkstra's argument needs every weight to be non-negative; graphs with negative edges need a different family of algorithms.
- **A\* search:** Dijkstra with an estimate of the remaining distance added to the heap key.
- **Strongly connected components**, the maximal groups of a directed graph in which every node reaches every other.
- **Bridges and articulation points:** the edges and nodes whose removal disconnects the graph.
- **All-pairs shortest paths**, the distance between every pair of nodes at once.
- **Heaps themselves.** Dijkstra and Prim use `heapq` as a black box here; you'll see how a heap works later, in module 10 ([10-heaps.md](10-heaps.md)).

If one of these comes up, one sentence is enough: *"I know the name and roughly what it does; I'd build it from BFS, DFS or Dijkstra, and I'd have to look up the details."*

## Before you submit anything

Run [bug-checklist.md](../reference/bug-checklist.md#the-30-second-pass), §The 30-second pass, over your code. Thirty seconds.

---

## Self-check answers

1. **D enters the queue twice**: once from B and once from C, because neither push marks it, so the traversal makes 5 pushes instead of 4. The duplicate is skipped when it comes out, so the visit order survives, but anything recorded at push time is recorded twice. With A: [B, X] and B: [X], X is pushed from A with distance 1 and again from B with distance 2, and the second write wins: **`dist[X] = 2` where the true distance is 1.**
2. Because **two routes into one node are not a cycle and still reach it twice.** On the diamond, D is reached from B and from C. Chain k diamonds and the number of routes to the end doubles each time, 2ᵏ, so without `visited` the last node is processed 2ᵏ times. `visited` is a process-each-node-once guard, not a cycle guard.
3. **`RecursionError`.** An all-land region is one component of 90,000 cells, and a DFS can open a call for most of them at once, far past Python's limit of about 1,000. The fixes: **BFS**, or **DFS with an explicit stack**. Both keep their progress in a list on the heap. Raising the recursion limit is not a fix.
4. Because **the two bounds don't multiply.** Each node enters the queue at most once, so the `while` body runs at most V times. Each time a node is popped, its loop runs over its own edges only, so across the whole run each edge is examined at most once from each end. The total is V plus the sum of the degrees, a **sum, O(V + E)**, not a product.
5. Every undirected edge is stored twice, so without the parent **a single edge 0 – 1 reads as a cycle**: from 1, the visited neighbour 0 is just the edge you arrived on. Skipping the parent fixes that. In a directed graph the parent test answers the wrong question: being reached by a second route isn't a cycle there, as the diamond shows. **You need to know whether the node is on the current path, which takes a third state: GREY versus BLACK.**
6. **The graph has a cycle.** A node on a cycle always has an incoming edge from the node before it on the cycle, which can't be output until it is free itself, so no node on the cycle, and nothing downstream of one, ever reaches indegree 0. The check was free because **`len(order) < n` reads a count you were already keeping.**
7. Because **a node's distance can improve while it waits in the heap**, so the distance at push time may not be final. The first time a node is popped, every other heap entry is at least as large, so that distance is final, and that is the moment to mark. **`done` protects against stale duplicate entries**, the old copies left behind when a distance improved (lazy deletion). Without it the answers stay correct and the work grows: on the module's example, 20 adjacency scans instead of 14.
8. **The heap orders by node id instead of distance**, so it hands out the lowest-numbered node first, not the closest, and nodes are finalised before their distances are right. On the module's five-node example, D comes out as 5 instead of 4. The example in a statement can still pass when **the node numbers happen to rise with distance**, so the wrong order and the right one coincide.
