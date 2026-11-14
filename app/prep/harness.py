"""Runs inside the child process: builds inputs, calls the user's code, compares, writes results.

Child entry point (started by runner.py with `python3 -I`, so this file must not import its
siblings):

    python3 -I app/prep/harness.py <spec.json> <solution.py> <results.jsonl> [--examples-only]

Every line written to the results file is one JSON object:
    {"start": k}                     case k (position among the selected cases) is about to run
    {"case": k, ...result...}        case k finished
    {"fatal": {type, message, line}} the code could not be loaded; nothing else follows
    {"done": true}                   every selected case has a result

The parent (runner.py) turns a missing result after a start marker into `timeout` or `error`.

The display helpers (display_value, display_input, expand) are also imported by the parent.
"""
from __future__ import annotations

import __future__ as future_flags
import builtins
import collections
import copy
import json
import linecache
import math
import os
import sys
import threading
import time
import traceback

NODE_LIMIT = 100000
DISPLAY_MAX = 400
STDOUT_MAX = 2000
TRACE_FRAMES = 20
TRACE_MAX = 4000
LOAD_LIMIT_S = 5.0
RECURSION_LIMIT = 20000
SOLUTION_FILE = "solution.py"


# ---------------------------------------------------------------------------
# Node classes (the same shapes LeetCode provides)

class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

    def __repr__(self):
        return "ListNode(%r)" % (self.val,)


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

    def __repr__(self):
        return "TreeNode(%r)" % (self.val,)


class RandomNode:
    """`Node` for copy-list-with-random-pointer."""

    def __init__(self, x=0, next=None, random=None):
        self.val = int(x)
        self.next = next
        self.random = random

    def __repr__(self):
        return "Node(%r)" % (self.val,)


class GraphNode:
    """`Node` for clone-graph."""

    def __init__(self, val=0, neighbors=None):
        self.val = val
        self.neighbors = neighbors if neighbors is not None else []

    def __repr__(self):
        return "Node(%r)" % (self.val,)


RandomNode.__name__ = RandomNode.__qualname__ = "Node"
GraphNode.__name__ = GraphNode.__qualname__ = "Node"


class OutputError(Exception):
    """The returned structure cannot be read back (a cycle, or too many nodes)."""


class CaseTimeout(BaseException):
    pass


# ---------------------------------------------------------------------------
# Generators

def _lcg(seed):
    x = seed
    while True:
        x = (1103515245 * x + 12345) % 2147483648
        yield x


def _generator_key(value):
    if isinstance(value, dict) and len(value) == 1:
        key = next(iter(value))
        if key in ("$range", "$repeat", "$lcg", "$str"):
            return key
    return None


def expand(value):
    """Expand every `$` generator object inside a JSON value. Always returns fresh objects."""
    key = _generator_key(value)
    if key == "$range":
        return list(range(*value[key]))
    if key == "$repeat":
        item, n = value[key]
        first = expand(item)
        if isinstance(first, (list, dict)):
            return [first] + [copy.deepcopy(first) for _ in range(int(n) - 1)] if n > 0 else []
        return [first] * int(n)
    if key == "$lcg":
        p = value[key]
        gen = _lcg(p["seed"])
        lo, span = p["lo"], p["hi"] - p["lo"] + 1
        return [lo + next(gen) % span for _ in range(p["n"])]
    if key == "$str":
        p = value[key]
        gen = _lcg(p["seed"])
        chars = p["chars"]
        return "".join(chars[next(gen) % len(chars)] for _ in range(p["n"]))
    if isinstance(value, list):
        return [expand(v) for v in value]
    if isinstance(value, dict):
        return {k: expand(v) for k, v in value.items()}
    return value


def _plural(sample, n):
    if isinstance(sample, bool):
        word = "booleans"
    elif isinstance(sample, int):
        word = "integers"
    elif isinstance(sample, float):
        word = "numbers"
    elif isinstance(sample, str):
        word = "strings"
    elif isinstance(sample, list):
        word = "lists"
    else:
        word = "items"
    return "<%d %s>" % (n, word)


def _describe_generator(value):
    key = _generator_key(value)
    p = value[key]
    if key == "$range":
        return "<%d integers>" % len(range(*p))
    if key == "$repeat":
        item, n = p
        sample = item if _generator_key(item) is None else expand(item)
        return _plural(sample, int(n))
    if key == "$lcg":
        return "<%d integers>" % p["n"]
    return "<%d characters>" % p["n"]


# ---------------------------------------------------------------------------
# Display

def _cut(text):
    if len(text) > DISPLAY_MAX:
        return text[:DISPLAY_MAX - 1] + "…"
    return text


def _compact(value):
    if _generator_key(value) is not None:
        return _describe_generator(value)
    if isinstance(value, list):
        return "[" + ",".join(_compact(v) for v in value) + "]"
    if isinstance(value, dict):
        return "{" + ",".join(json.dumps(k, ensure_ascii=False) + ":" + _compact(v)
                              for k, v in value.items()) + "}"
    return json.dumps(value, ensure_ascii=False)


def display_value(value):
    """Compact JSON for a spec or result value, generators shown as short descriptions,
    falling back to repr for values JSON cannot hold. Cut to 400 characters."""
    try:
        text = _compact(_normalise(value))
    except Exception:
        try:
            text = repr(value)
        except Exception:
            text = "<value that cannot be shown>"
    return _cut(text)


def display_input(spec, case):
    if spec.get("driver") == "design":
        return _cut(display_value(case.get("ops")) + "\n" + display_value(case.get("args")))
    params = spec.get("params") or []
    args = case.get("args") or []
    parts = []
    for i, arg in enumerate(args):
        name = params[i]["name"] if i < len(params) else "arg%d" % (i + 1)
        parts.append("%s = %s" % (name, display_value(arg)))
    return _cut(", ".join(parts))


# ---------------------------------------------------------------------------
# Conversions

def _to_list(values):
    head = None
    for v in reversed(values):
        head = ListNode(v, head)
    return head


def _from_list(node):
    if node is None:
        return []
    if not (hasattr(node, "val") and hasattr(node, "next")):
        return node
    out = []
    while node is not None:
        if len(out) >= NODE_LIMIT:
            raise OutputError("returned list has a cycle or is too long")
        out.append(node.val)
        node = node.next
    return out


def _to_tree(values):
    if not values or values[0] is None:
        return None
    root = TreeNode(values[0])
    queue = collections.deque([root])
    i = 1
    while queue and i < len(values):
        node = queue.popleft()
        if i < len(values) and values[i] is not None:
            node.left = TreeNode(values[i])
            queue.append(node.left)
        i += 1
        if i < len(values) and values[i] is not None:
            node.right = TreeNode(values[i])
            queue.append(node.right)
        i += 1
    return root


def _from_tree(root):
    if root is None:
        return []
    if not (hasattr(root, "val") and hasattr(root, "left") and hasattr(root, "right")):
        return root
    out = []
    queue = collections.deque([root])
    count = 0
    while queue:
        node = queue.popleft()
        if node is None:
            out.append(None)
            continue
        count += 1
        if count > NODE_LIMIT:
            raise OutputError("returned tree has a cycle or is too large")
        out.append(node.val)
        queue.append(node.left)
        queue.append(node.right)
    while out and out[-1] is None:
        out.pop()
    return out


def convert_in(type_name, value):
    if type_name == "ListNode":
        return _to_list(value)
    if type_name == "ListNode[]":
        return [_to_list(v) for v in value]
    if type_name == "TreeNode":
        return _to_tree(value)
    return value


def convert_out(type_name, value):
    if type_name == "ListNode":
        return _from_list(value)
    if type_name == "ListNode[]":
        if isinstance(value, (list, tuple)):
            return [_from_list(v) for v in value]
        return value
    if type_name == "TreeNode":
        return _from_tree(value)
    return value


def _normalise(value):
    if isinstance(value, (list, tuple)):
        return [_normalise(v) for v in value]
    if isinstance(value, dict):
        return {k: _normalise(v) for k, v in value.items()}
    return value


# ---------------------------------------------------------------------------
# Compare

def _strict_eq(a, b):
    if isinstance(a, bool) or isinstance(b, bool):
        return type(a) is type(b) and a == b
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(_strict_eq(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(_strict_eq(a[k], b[k]) for k in a)
    if isinstance(a, (list, dict)) or isinstance(b, (list, dict)):
        return False
    try:
        return bool(a == b)
    except Exception:
        return False


def _key(item):
    try:
        return json.dumps(item, sort_keys=True)
    except Exception:
        return "repr:" + repr(item)


def _multiset_eq(got, expected):
    if not isinstance(got, list) or not isinstance(expected, list) or len(got) != len(expected):
        return False
    return collections.Counter(_key(x) for x in got) == collections.Counter(_key(x) for x in expected)


def _sorted_inner(items):
    out = []
    for item in items:
        if not isinstance(item, list):
            return None
        out.append(sorted(item, key=_key))
    return out


def _float_eq(a, b):
    num = (int, float)
    if isinstance(a, num) and isinstance(b, num) and not isinstance(a, bool) and not isinstance(b, bool):
        return abs(a - b) <= 1e-5
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(_float_eq(x, y) for x, y in zip(a, b))
    return _strict_eq(a, b)


def _check_topo_order(args, expected, got):
    n, prerequisites = args[0], args[1]
    if expected == []:
        if got == []:
            return None
        return "the prerequisites contain a cycle, so the answer is []"
    if not isinstance(got, list) or not all(isinstance(c, int) and not isinstance(c, bool) for c in got):
        return "expected a list of course numbers"
    if sorted(got) != list(range(n)):
        return "the order must list every course from 0 to %d exactly once" % (n - 1)
    pos = {c: i for i, c in enumerate(got)}
    for course, before in prerequisites:
        if pos[before] > pos[course]:
            return "course %d comes before its prerequisite %d" % (course, before)
    return None


def _check_palindrome_substring(args, expected, got):
    s = args[0]
    if not isinstance(got, str):
        return "expected a string"
    if got != got[::-1]:
        return "%s is not a palindrome" % json.dumps(got)
    if got not in s:
        return "%s does not occur in the input" % json.dumps(got)
    if len(got) != len(expected):
        return "length %d, but the longest palindrome has length %d" % (len(got), len(expected))
    return None


def _check_alien_order(args, expected, got):
    words = args[0]
    if expected == "":
        if got == "":
            return None
        return "no order fits these words, so the answer is \"\""
    if not isinstance(got, str):
        return "expected a string"
    letters = set("".join(words))
    if len(got) != len(set(got)) or set(got) != letters:
        return "the order must contain each letter of the words exactly once"
    pos = {c: i for i, c in enumerate(got)}
    for first, second in zip(words, words[1:]):
        for a, b in zip(first, second):
            if a != b:
                if pos[a] > pos[b]:
                    return "%s must come before %s (from %s, %s)" % (
                        json.dumps(a), json.dumps(b), json.dumps(first), json.dumps(second))
                break
    return None


CHECKERS = {
    "topo_order": _check_topo_order,
    "palindrome_substring": _check_palindrome_substring,
    "alien_order": _check_alien_order,
}


def compare(mode, got, expected, args):
    """Returns (passed, reason_or_None)."""
    got = _normalise(got)
    mode = mode or "exact"
    if mode == "exact":
        return _strict_eq(got, expected), None
    if mode == "unordered":
        return _multiset_eq(got, expected), None
    if mode == "unordered_nested":
        if not isinstance(got, list) or not isinstance(expected, list):
            return False, None
        g, e = _sorted_inner(got), _sorted_inner(expected)
        return g is not None and e is not None and _multiset_eq(g, e), None
    if mode == "float":
        return _float_eq(got, expected), None
    if mode.startswith("checker:"):
        checker = CHECKERS[mode[len("checker:"):]]
        reason = checker(args, expected, got)
        return reason is None, reason
    raise ValueError("unknown compare mode %r" % mode)


# ---------------------------------------------------------------------------
# Drivers. Each returns (got_value, reason_or_None); a reason means the case fails.

def _required_methods(spec, cases):
    driver = spec.get("driver", "function")
    if driver == "design":
        names = []
        for case in cases:
            for op in case.get("ops", [])[1:]:
                if op not in names:
                    names.append(op)
        return names
    if driver == "codec_strings":
        return ["encode", "decode"]
    if driver == "codec_tree":
        return ["serialize", "deserialize"]
    return [spec["method"]]


def _drive_function(spec, cls, args):
    params = spec.get("params") or []
    types = [p.get("type") for p in params]
    converted = [convert_in(types[i] if i < len(types) else None, a) for i, a in enumerate(args)]
    returned = getattr(cls(), spec["method"])(*converted)
    inplace = spec.get("inplace")
    if inplace is not None:
        return convert_out(types[inplace], converted[inplace]), None
    return convert_out(spec.get("returns"), returned), None


def _drive_design(spec, cls, case):
    ops, args = case["ops"], case["args"]
    obj = cls(*args[0])
    out = [None]
    for op, op_args in zip(ops[1:], args[1:]):
        out.append(getattr(obj, op)(*op_args))
    return out, None


def _drive_cycle(spec, cls, args):
    values, pos = args[0], args[1]
    nodes = [ListNode(v) for v in values]
    for a, b in zip(nodes, nodes[1:]):
        a.next = b
    if nodes and pos is not None and pos >= 0:
        nodes[-1].next = nodes[pos]
    head = nodes[0] if nodes else None
    return getattr(cls(), spec["method"])(head), None


def _drive_random_list(spec, cls, args):
    rows = args[0]
    nodes = [RandomNode(val) for val, _ in rows]
    for a, b in zip(nodes, nodes[1:]):
        a.next = b
    for node, (_, rand) in zip(nodes, rows):
        node.random = nodes[rand] if rand is not None else None
    inputs = set(id(n) for n in nodes)
    returned = getattr(cls(), spec["method"])(nodes[0] if nodes else None)
    if returned is None:
        return [], None
    if not hasattr(returned, "next"):
        return returned, None
    walked, index = [], {}
    node = returned
    while node is not None:
        if len(walked) >= NODE_LIMIT:
            raise OutputError("returned list has a cycle or is too long")
        index[id(node)] = len(walked)
        walked.append(node)
        node = node.next
    reason = None
    if any(id(n) in inputs or id(getattr(n, "random", None)) in inputs for n in walked):
        reason = "returned a node from the original list"
    out = []
    for n in walked:
        rand = getattr(n, "random", None)
        if rand is None:
            out.append([n.val, None])
        elif id(rand) in index:
            out.append([n.val, index[id(rand)]])
        else:
            out.append([n.val, "outside"])
            reason = reason or "a random pointer leads outside the returned list"
    return out, reason


def _drive_clone_graph(spec, cls, args):
    adjacency = args[0]
    nodes = [GraphNode(i + 1) for i in range(len(adjacency))]
    for node, neighbours in zip(nodes, adjacency):
        node.neighbors = [nodes[j - 1] for j in neighbours]
    inputs = set(id(n) for n in nodes)
    returned = getattr(cls(), spec["method"])(nodes[0] if nodes else None)
    if returned is None:
        return [], None
    if not hasattr(returned, "neighbors"):
        return returned, None
    seen = {id(returned): returned}
    queue = collections.deque([returned])
    while queue:
        node = queue.popleft()
        for nb in node.neighbors:
            if id(nb) not in seen:
                if len(seen) >= NODE_LIMIT:
                    raise OutputError("returned graph is too large")
                seen[id(nb)] = nb
                queue.append(nb)
    reason = None
    if any(i in inputs for i in seen):
        reason = "returned a node from the original graph"
    ordered = sorted(seen.values(), key=lambda n: n.val)
    return [[nb.val for nb in n.neighbors] for n in ordered], reason


def _drive_lca(spec, cls, args):
    root = _to_tree(args[0])
    wanted = {args[1]: None, args[2]: None}
    queue = collections.deque([root] if root else [])
    while queue:
        node = queue.popleft()
        if node.val in wanted and wanted[node.val] is None:
            wanted[node.val] = node
        queue.extend(c for c in (node.left, node.right) if c is not None)
    returned = getattr(cls(), spec["method"])(root, wanted[args[1]], wanted[args[2]])
    if hasattr(returned, "val"):
        return returned.val, None
    return returned, None


def _drive_codec_strings(spec, cls, args):
    encoded = cls().encode(args[0])
    if not isinstance(encoded, str):
        return encoded, "encode returned %s, not a str" % type(encoded).__name__
    return cls().decode(encoded), None


def _drive_codec_tree(spec, cls, args):
    root = _to_tree(args[0])
    data = cls().serialize(root)
    return _from_tree(cls().deserialize(data)), None


DRIVERS = {
    "function": _drive_function,
    "cycle": _drive_cycle,
    "random_list": _drive_random_list,
    "clone_graph": _drive_clone_graph,
    "lca": _drive_lca,
    "codec_strings": _drive_codec_strings,
    "codec_tree": _drive_codec_tree,
}


# ---------------------------------------------------------------------------
# Child process

class _Capture:
    """Stand-in for sys.stdout that keeps the first STDOUT_MAX characters."""

    def __init__(self):
        self.parts = []
        self.size = 0

    def write(self, text):
        text = str(text)
        if self.size < STDOUT_MAX:
            piece = text[:STDOUT_MAX - self.size]
            self.parts.append(piece)
            self.size += len(piece)
        return len(text)

    def flush(self):
        pass

    def isatty(self):
        return False

    def value(self):
        return "".join(self.parts)


def _user_frames(tb):
    return [f for f in traceback.extract_tb(tb) if f.filename == SOLUTION_FILE]


def _error_info(exc):
    frames = _user_frames(exc.__traceback__)
    line = frames[-1].lineno if frames else None
    if isinstance(exc, SyntaxError) and exc.filename == SOLUTION_FILE:
        line = exc.lineno
    if isinstance(exc, SystemExit):
        message = "sys.exit() was called (code %r)" % (exc.code,)
    else:
        message = str(exc)
    shown = frames[-TRACE_FRAMES:]
    trace = ""
    if len(frames) > len(shown):
        trace = "... %d earlier calls in solution.py ...\n" % (len(frames) - len(shown))
    trace += "".join(traceback.format_list(shown))
    trace += "".join(traceback.format_exception_only(type(exc), exc))
    if len(trace) > TRACE_MAX:
        trace = "…" + trace[-(TRACE_MAX - 1):]
    return {"type": type(exc).__name__, "message": message, "line": line, "trace": trace}


def _in_thread(fn, limit):
    """Run fn in a big-stack worker thread. Returns (finished, value, exception)."""
    box = {}

    def target():
        try:
            box["value"] = fn()
        except BaseException as exc:  # SystemExit and friends belong to the user's case
            box["exc"] = exc

    worker = threading.Thread(target=target, daemon=True)
    worker.start()
    worker.join(limit)
    if worker.is_alive():
        return False, None, None
    return True, box.get("value"), box.get("exc")


def _namespace(driver):
    import bisect
    import functools
    import heapq
    import itertools
    import operator
    import random
    import re
    import string

    ns = {"__name__": "solution", "__builtins__": builtins}
    exec("from typing import *", ns)
    ns.update({
        "collections": collections, "heapq": heapq, "bisect": bisect, "math": math,
        "itertools": itertools, "functools": functools, "string": string, "re": re,
        "random": random, "operator": operator,
        "deque": collections.deque, "defaultdict": collections.defaultdict,
        "Counter": collections.Counter, "OrderedDict": collections.OrderedDict,
        "heappush": heapq.heappush, "heappop": heapq.heappop, "heapify": heapq.heapify,
        "heapreplace": heapq.heapreplace, "heappushpop": heapq.heappushpop,
        "nlargest": heapq.nlargest, "nsmallest": heapq.nsmallest,
        "bisect_left": bisect.bisect_left, "bisect_right": bisect.bisect_right,
        "insort": bisect.insort, "inf": math.inf,
        "lru_cache": functools.lru_cache, "cache": functools.cache, "reduce": functools.reduce,
        "accumulate": itertools.accumulate, "permutations": itertools.permutations,
        "combinations": itertools.combinations, "product": itertools.product,
        "ListNode": ListNode, "TreeNode": TreeNode,
    })
    if driver == "random_list":
        ns["Node"] = RandomNode
    elif driver == "clone_graph":
        ns["Node"] = GraphNode
    return ns


def _load(spec, src, cases):
    """Compile and execute the user's code. Returns (class, None) or (None, fatal)."""
    linecache.cache[SOLUTION_FILE] = (len(src), None, src.splitlines(True), SOLUTION_FILE)
    try:
        code = compile(src, SOLUTION_FILE, "exec",
                       flags=future_flags.annotations.compiler_flag, dont_inherit=True)
    except SyntaxError as exc:
        return None, {"type": type(exc).__name__, "message": exc.msg, "line": exc.lineno}
    except (ValueError, TypeError) as exc:
        return None, {"type": type(exc).__name__, "message": str(exc), "line": None}
    ns = _namespace(spec.get("driver", "function"))
    capture = _Capture()
    saved = sys.stdout
    sys.stdout = capture
    try:
        finished, _, exc = _in_thread(lambda: exec(code, ns), LOAD_LIMIT_S)
    finally:
        sys.stdout = saved
    if not finished:
        return None, {"type": "Timeout", "message": "your code did not finish loading within %g s"
                      % LOAD_LIMIT_S, "line": None}
    if exc is not None:
        info = _error_info(exc)
        return None, {"type": info["type"], "message": info["message"], "line": info["line"]}
    class_name = spec["class"]
    cls = ns.get(class_name)
    if not isinstance(cls, type):
        return None, {"type": "MissingDefinition",
                      "message": "no class named %s was found in your code" % class_name, "line": None}
    for name in _required_methods(spec, cases):
        if not callable(getattr(cls, name, None)):
            return None, {"type": "MissingDefinition",
                          "message": "%s has no method named %s" % (class_name, name), "line": None}
    return cls, None


def _run_case(spec, cls, case):
    driver = spec.get("driver", "function")
    if driver == "design":
        work = {"ops": case["ops"], "args": expand(case["args"])}
        got, reason = _drive_design(spec, cls, work)
    else:
        got, reason = DRIVERS[driver](spec, cls, expand(case["args"]))
    return got, reason


def selected_cases(spec, examples_only):
    cases = spec.get("cases") or []
    return [c for c in cases if not examples_only or c.get("example")]


def case_limit(spec, case):
    return float(case.get("time_limit_s", spec.get("time_limit_s", 2.0)))


def blank_result(spec, case, status):
    return {"name": case.get("name", ""), "example": bool(case.get("example")), "status": status,
            "input": display_input(spec, case), "expected": display_value(case.get("expected")),
            "got": None, "stdout": "", "ms": 0, "error": None, "message": None}


def _evaluate(spec, cls, case):
    """Runs one case in a worker thread and returns its result dict."""
    result = blank_result(spec, case, "error")
    capture = _Capture()
    outcome = {}

    def work():
        started = time.perf_counter()
        try:
            outcome["got"], outcome["reason"] = _run_case(spec, cls, case)
        finally:
            outcome["ms"] = round((time.perf_counter() - started) * 1000, 1)

    saved = sys.stdout
    sys.stdout = capture
    try:
        finished, _, exc = _in_thread(work, case_limit(spec, case))
    finally:
        sys.stdout = saved
    result["stdout"] = capture.value()
    if not finished:
        result["status"] = "timeout"
        result["ms"] = round(case_limit(spec, case) * 1000, 1)
        return result
    result["ms"] = outcome.get("ms", 0)
    if exc is not None:
        result["error"] = _error_info(exc)
        return result
    got, reason = outcome["got"], outcome["reason"]
    result["got"] = display_value(got)
    if reason is None:
        compare_args = expand(case["args"]) if (spec.get("compare") or "").startswith("checker:") else None
        try:
            passed, reason = compare(spec.get("compare"), got, expand(case.get("expected")), compare_args)
        except Exception as exc:
            result["error"] = {"type": type(exc).__name__, "message": "could not compare: %s" % exc,
                               "line": None, "trace": ""}
            return result
    else:
        passed = False
    result["status"] = "pass" if passed else "fail"
    result["message"] = reason
    return result


def _can_start_thread():
    try:
        probe = threading.Thread(target=lambda: None, daemon=True)
        probe.start()
        probe.join()
        return True
    except RuntimeError:  # "can't start new thread": the size was accepted but there is no memory for it
        return False


def _set_limits():
    sys.setrecursionlimit(RECURSION_LIMIT + 60)
    for size in (512, 256, 64):
        try:
            threading.stack_size(size * 1024 * 1024)
        except (ValueError, RuntimeError):
            continue
        if _can_start_thread():
            return
    threading.stack_size(0)  # the platform default; user code still runs in a thread


def main(argv):
    spec_path, solution_path, results_path = argv[1], argv[2], argv[3]
    examples_only = "--examples-only" in argv[4:]
    out = open(results_path, "w", encoding="utf-8")

    def emit(obj):
        out.write(json.dumps(obj) + "\n")  # ASCII escapes: lone surrogates cannot break the write
        out.flush()

    try:
        with open(spec_path, encoding="utf-8") as fh:
            spec = json.load(fh)
        with open(solution_path, encoding="utf-8") as fh:
            src = fh.read()
        cases = selected_cases(spec, examples_only)
        _set_limits()
        cls, fatal = _load(spec, src, cases)
    except Exception as exc:
        emit({"fatal": {"type": "HarnessError", "message": "%s: %s" % (type(exc).__name__, exc),
                        "line": None}})
        out.close()
        os._exit(0)
    if fatal is not None:
        emit({"fatal": fatal})
        out.close()
        os._exit(0)
    for k, case in enumerate(cases):
        emit({"start": k})
        try:
            result = _evaluate(spec, cls, case)
        except Exception as exc:
            result = blank_result(spec, case, "error")
            result["error"] = {"type": "HarnessError", "message": "%s: %s" % (type(exc).__name__, exc),
                               "line": None, "trace": ""}
        result["case"] = k
        emit(result)
        if result["status"] == "timeout":
            out.close()
            os._exit(0)  # the worker thread cannot be stopped; later cases stay not_run
    emit({"done": True})
    out.close()
    os._exit(0)


if __name__ == "__main__":
    main(sys.argv)
