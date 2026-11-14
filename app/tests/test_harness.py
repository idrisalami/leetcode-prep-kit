"""Harness behaviour through runner.run: conversions, drivers, compare modes, generators, display."""
from __future__ import annotations

import sys
import threading
import unittest
from unittest import mock

from app.prep import harness, runner


def fn_spec(method, params, returns, cases, **extra):
    spec = {"slug": "t", "driver": "function", "class": "Solution", "method": method,
            "params": params, "returns": returns, "compare": "exact", "time_limit_s": 2.0,
            "cases": cases}
    spec.update(extra)
    return spec


def case(args, expected, name="c"):
    return {"name": name, "example": True, "args": args, "expected": expected}


def statuses(result):
    return [r["status"] for r in result["results"]]


IDENTITY_LIST = """
class Solution:
    def f(self, head: ListNode | None) -> ListNode | None:
        return head
"""


class ConversionTests(unittest.TestCase):
    def test_listnode_round_trip_and_empty(self):
        spec = fn_spec("f", [{"name": "head", "type": "ListNode"}], "ListNode",
                       [case([[1, 2, 3]], [1, 2, 3]), case([[]], [])])
        res = runner.run(spec, IDENTITY_LIST)
        self.assertEqual(statuses(res), ["pass", "pass"])

    def test_listnode_values_are_real_nodes(self):
        code = """
class Solution:
    def f(self, head):
        out = []
        while head:
            out.append(head.val * 10)
            head = head.next
        return out
"""
        spec = fn_spec("f", [{"name": "head", "type": "ListNode"}], "int[]",
                       [case([[1, 2]], [10, 20]), case([[]], [])])
        self.assertEqual(statuses(runner.run(spec, code)), ["pass", "pass"])

    def test_listnode_array(self):
        code = """
class Solution:
    def f(self, lists):
        assert lists[1] is None
        return [l.val for l in lists if l]
"""
        spec = fn_spec("f", [{"name": "lists", "type": "ListNode[]"}], "int[]",
                       [case([[[1, 4], [], [2]]], [1, 2])])
        self.assertEqual(statuses(runner.run(spec, code)), ["pass"])

    def test_listnode_array_return(self):
        code = """
class Solution:
    def f(self, lists):
        return lists
"""
        spec = fn_spec("f", [{"name": "lists", "type": "ListNode[]"}], "ListNode[]",
                       [case([[[1, 4], [], [2]]], [[1, 4], [], [2]])])
        self.assertEqual(statuses(runner.run(spec, code)), ["pass"])

    def test_treenode_round_trip_with_gaps_and_empty(self):
        code = """
class Solution:
    def f(self, root: Optional[TreeNode]) -> Optional[TreeNode]:
        return root
"""
        spec = fn_spec("f", [{"name": "root", "type": "TreeNode"}], "TreeNode",
                       [case([[1, None, 2, 3]], [1, None, 2, 3]), case([[]], []),
                        case([[3, 9, 20, None, None, 15, 7]], [3, 9, 20, None, None, 15, 7])])
        self.assertEqual(statuses(runner.run(spec, code)), ["pass", "pass", "pass"])

    def test_treenode_shape_is_built_level_order(self):
        code = """
class Solution:
    def f(self, root):
        return [root.val, root.left, root.right.val, root.right.left.val, root.right.right]
"""
        spec = fn_spec("f", [{"name": "root", "type": "TreeNode"}], "int[]",
                       [case([[1, None, 2, 3]], [1, None, 2, 3, None])])
        self.assertEqual(statuses(runner.run(spec, code)), ["pass"])

    def test_serialised_tree_trims_trailing_nulls(self):
        code = """
class Solution:
    def f(self, root):
        root.right = None
        return root
"""
        spec = fn_spec("f", [{"name": "root", "type": "TreeNode"}], "TreeNode",
                       [case([[1, 2, 3]], [1, 2])])
        res = runner.run(spec, code)
        self.assertEqual(statuses(res), ["pass"])
        self.assertEqual(res["results"][0]["got"], "[1,2]")

    def test_cyclic_returned_list_is_reported(self):
        code = """
class Solution:
    def f(self, head):
        head.next = head
        return head
"""
        spec = fn_spec("f", [{"name": "head", "type": "ListNode"}], "ListNode",
                       [case([[1, 2]], [1, 2])])
        res = runner.run(spec, code)
        self.assertEqual(statuses(res), ["error"])
        self.assertIn("cycle", res["results"][0]["error"]["message"])

    def test_wrong_return_type_fails_without_crashing(self):
        code = """
class Solution:
    def f(self, nums):
        return {1, 2}
"""
        spec = fn_spec("f", [{"name": "nums", "type": "int[]"}], "int[]", [case([[1, 2]], [1, 2])])
        res = runner.run(spec, code)
        self.assertEqual(statuses(res), ["fail"])
        self.assertEqual(res["results"][0]["got"], "{1, 2}")


class DriverTests(unittest.TestCase):
    def test_function_driver(self):
        spec = fn_spec("add", [{"name": "a", "type": "int"}, {"name": "b", "type": "int"}], "int",
                       [case([1, 2], 3)])
        good = "class Solution:\n    def add(self, a, b):\n        return a + b\n"
        bad = "class Solution:\n    def add(self, a, b):\n        return a - b\n"
        self.assertEqual(statuses(runner.run(spec, good)), ["pass"])
        res = runner.run(spec, bad)
        self.assertEqual(statuses(res), ["fail"])
        self.assertEqual(res["passed"], 0)
        self.assertEqual(res["total"], 1)

    def test_function_inplace_compares_argument(self):
        spec = fn_spec("solve", [{"name": "board", "type": "int[][]"}], "void",
                       [case([[[1, 2], [3, 4]]], [[0, 2], [3, 4]])], inplace=0)
        good = "class Solution:\n    def solve(self, board):\n        board[0][0] = 0\n"
        bad = "class Solution:\n    def solve(self, board):\n        return [[0, 2], [3, 4]]\n"
        self.assertEqual(statuses(runner.run(spec, good)), ["pass"])
        self.assertEqual(statuses(runner.run(spec, bad)), ["fail"])

    def test_function_inplace_linked_list(self):
        spec = fn_spec("reorderList", [{"name": "head", "type": "ListNode"}], "void",
                       [case([[1, 2, 3]], [1, 3, 2])], inplace=0)
        good = """
class Solution:
    def reorderList(self, head):
        second, third = head.next, head.next.next
        head.next, third.next, second.next = third, second, None
"""
        bad = "class Solution:\n    def reorderList(self, head):\n        pass\n"
        self.assertEqual(statuses(runner.run(spec, good)), ["pass"])
        self.assertEqual(statuses(runner.run(spec, bad)), ["fail"])

    def test_design_driver(self):
        spec = {"slug": "t", "driver": "design", "class": "Counter2", "method": None, "params": [],
                "returns": None, "compare": "exact", "time_limit_s": 2.0,
                "cases": [{"name": "Example 1", "example": True, "ops": ["Counter2", "add", "get"],
                           "args": [[10], [5], []], "expected": [None, None, 15]}]}
        good = """
class Counter2:
    def __init__(self, start):
        self.n = start
    def add(self, k) -> None:
        self.n += k
    def get(self):
        return self.n
"""
        bad = good.replace("self.n += k", "self.n = k")
        res = runner.run(spec, good)
        self.assertEqual(statuses(res), ["pass"])
        self.assertIn("Counter2", res["results"][0]["input"])
        self.assertEqual(statuses(runner.run(spec, bad)), ["fail"])

    def test_design_missing_method_is_fatal(self):
        spec = {"slug": "t", "driver": "design", "class": "C", "method": None, "params": [],
                "returns": None, "compare": "exact", "time_limit_s": 2.0,
                "cases": [{"name": "e", "ops": ["C", "push"], "args": [[], [1]], "expected": [None, None]}]}
        res = runner.run(spec, "class C:\n    pass\n")
        self.assertIsNotNone(res["fatal"])
        self.assertIn("push", res["fatal"]["message"])

    def test_cycle_driver(self):
        spec = fn_spec("hasCycle", [{"name": "head", "type": "ListNode"}, {"name": "pos", "type": "int"}],
                       "bool", [case([[3, 2, 0, -4], 1], True), case([[1], -1], False)], driver="cycle")
        good = """
class Solution:
    def hasCycle(self, head):
        slow = fast = head
        while fast and fast.next:
            slow, fast = slow.next, fast.next.next
            if slow is fast:
                return True
        return False
"""
        bad = "class Solution:\n    def hasCycle(self, head):\n        return False\n"
        self.assertEqual(statuses(runner.run(spec, good)), ["pass", "pass"])
        self.assertEqual(statuses(runner.run(spec, bad)), ["fail", "pass"])

    def test_random_list_driver(self):
        spec = fn_spec("copyRandomList", [{"name": "head", "type": "Node"}], "Node",
                       [case([[[7, None], [13, 0], [11, 4], [10, 2], [1, 0]]],
                             [[7, None], [13, 0], [11, 4], [10, 2], [1, 0]]),
                        case([[]], [])], driver="random_list")
        good = """
class Solution:
    def copyRandomList(self, head: 'Optional[Node]') -> 'Optional[Node]':
        copies = {None: None}
        node = head
        while node:
            copies[node] = Node(node.val)
            node = node.next
        node = head
        while node:
            copies[node].next = copies[node.next]
            copies[node].random = copies[node.random]
            node = node.next
        return copies[head]
"""
        bad = "class Solution:\n    def copyRandomList(self, head):\n        return head\n"
        self.assertEqual(statuses(runner.run(spec, good)), ["pass", "pass"])
        res = runner.run(spec, bad)
        self.assertEqual(statuses(res)[0], "fail")
        self.assertIn("original", res["results"][0]["message"])

    def test_clone_graph_driver(self):
        spec = fn_spec("cloneGraph", [{"name": "adjList", "type": "int[][]"}], "int[][]",
                       [case([[[2, 4], [1, 3], [2, 4], [1, 3]]], [[2, 4], [1, 3], [2, 4], [1, 3]]),
                        case([[[]]], [[]]), case([[]], [])], driver="clone_graph")
        good = """
class Solution:
    def cloneGraph(self, node: Optional['Node']) -> Optional['Node']:
        if node is None:
            return None
        copies = {}
        def dfs(n):
            if n in copies:
                return copies[n]
            c = copies[n] = Node(n.val)
            c.neighbors = [dfs(m) for m in n.neighbors]
            return c
        return dfs(node)
"""
        bad = "class Solution:\n    def cloneGraph(self, node):\n        return node\n"
        self.assertEqual(statuses(runner.run(spec, good)), ["pass", "pass", "pass"])
        res = runner.run(spec, bad)
        self.assertEqual(statuses(res)[:2], ["fail", "fail"])
        self.assertIn("original", res["results"][0]["message"])

    def test_lca_driver(self):
        spec = fn_spec("lowestCommonAncestor",
                       [{"name": "root", "type": "TreeNode"}, {"name": "p", "type": "int"},
                        {"name": "q", "type": "int"}], "int",
                       [case([[6, 2, 8, 0, 4, 7, 9, None, None, 3, 5], 2, 8], 6),
                        case([[6, 2, 8, 0, 4, 7, 9, None, None, 3, 5], 2, 4], 2)], driver="lca")
        good = """
class Solution:
    def lowestCommonAncestor(self, root: 'TreeNode', p: 'TreeNode', q: 'TreeNode') -> 'TreeNode':
        while True:
            if p.val < root.val and q.val < root.val:
                root = root.left
            elif p.val > root.val and q.val > root.val:
                root = root.right
            else:
                return root
"""
        bad = "class Solution:\n    def lowestCommonAncestor(self, root, p, q):\n        return p\n"
        self.assertEqual(statuses(runner.run(spec, good)), ["pass", "pass"])
        self.assertEqual(statuses(runner.run(spec, bad)), ["fail", "pass"])

    def test_codec_strings_driver(self):
        spec = fn_spec("encode", [{"name": "strs", "type": "str[]"}], "str[]",
                       [case([["Hello", "World"]], ["Hello", "World"]), case([[""]], [""])],
                       driver="codec_strings")
        good = """
class Solution:
    def encode(self, strs: List[str]) -> str:
        return "".join("%d#%s" % (len(s), s) for s in strs)
    def decode(self, s: str) -> List[str]:
        out, i = [], 0
        while i < len(s):
            j = s.index("#", i)
            n = int(s[i:j])
            out.append(s[j + 1:j + 1 + n])
            i = j + 1 + n
        return out
"""
        # Keeps state on the instance, which two separate instances defeat.
        stateful = """
class Solution:
    def encode(self, strs):
        self.saved = strs
        return ""
    def decode(self, s):
        return self.saved
"""
        not_str = """
class Solution:
    def encode(self, strs):
        return list(strs)
    def decode(self, s):
        return list(s)
"""
        self.assertEqual(statuses(runner.run(spec, good)), ["pass", "pass"])
        self.assertEqual(statuses(runner.run(spec, stateful)), ["error", "error"])
        res = runner.run(spec, not_str)
        self.assertEqual(statuses(res), ["fail", "fail"])
        self.assertIn("str", res["results"][0]["message"])

    def test_codec_strings_missing_decode_is_fatal(self):
        spec = fn_spec("encode", [{"name": "strs", "type": "str[]"}], "str[]",
                       [case([["a"]], ["a"])], driver="codec_strings")
        res = runner.run(spec, "class Solution:\n    def encode(self, strs):\n        return ''\n")
        self.assertIn("decode", res["fatal"]["message"])

    def test_codec_tree_driver(self):
        spec = {"slug": "t", "driver": "codec_tree", "class": "Codec", "method": "serialize",
                "params": [{"name": "root", "type": "TreeNode"}], "returns": "TreeNode",
                "compare": "exact", "time_limit_s": 2.0,
                "cases": [case([[1, 2, 3, None, None, 4, 5]], [1, 2, 3, None, None, 4, 5]),
                          case([[]], [])]}
        good = """
class Codec:
    def serialize(self, root):
        out = []
        def go(n):
            if n is None:
                out.append("#")
                return
            out.append(str(n.val))
            go(n.left)
            go(n.right)
        go(root)
        return ",".join(out)
    def deserialize(self, data):
        it = iter(data.split(","))
        def go():
            v = next(it)
            if v == "#":
                return None
            n = TreeNode(int(v))
            n.left = go()
            n.right = go()
            return n
        return go()
"""
        bad = good.replace("n.left = go()\n            n.right = go()", "n.right = go()\n            n.left = go()")
        self.assertEqual(statuses(runner.run(spec, good)), ["pass", "pass"])
        self.assertEqual(statuses(runner.run(spec, bad)), ["fail", "pass"])


class CompareTests(unittest.TestCase):
    RETURN_GOT = "class Solution:\n    def f(self, got):\n        return got\n"

    def check(self, compare, pairs, returns="any"):
        cases = [case([got], expected, name="c%d" % i) for i, (got, expected) in enumerate(pairs)]
        spec = fn_spec("f", [{"name": "got", "type": "any"}], returns, cases, compare=compare)
        return statuses(runner.run(spec, self.RETURN_GOT))

    def check_fixed(self, compare, params, rows):
        """rows: (args, got, expected). Each row runs a solution that returns `got` as given."""
        out = []
        for args, got, expected in rows:
            names = ", ".join(p["name"] for p in params)
            code = "class Solution:\n    def f(self, %s):\n        return %r\n" % (names, got)
            spec = fn_spec("f", params, "any", [case(args, expected)], compare=compare)
            out.append(statuses(runner.run(spec, code))[0])
        return out

    def test_exact(self):
        self.assertEqual(self.check("exact", [([1, [2]], [1, [2]]), ([1, 2], [2, 1]), (1, True)]),
                         ["pass", "fail", "fail"])

    def test_exact_normalises_tuples(self):
        code = "class Solution:\n    def f(self):\n        return (1, (2, 3))\n"
        spec = fn_spec("f", [], "any", [case([], [1, [2, 3]])])
        self.assertEqual(statuses(runner.run(spec, code)), ["pass"])

    def test_unordered(self):
        self.assertEqual(self.check("unordered", [([[1, 2], [3]], [[3], [1, 2]]),
                                                  ([[2, 1], [3]], [[3], [1, 2]]),
                                                  ([1, 1, 2], [1, 2, 2]), (3, [3])]),
                         ["pass", "fail", "fail", "fail"])

    def test_unordered_nested(self):
        self.assertEqual(self.check("unordered_nested", [([[2, 1], [3]], [[3], [1, 2]]),
                                                         ([[1, 2]], [[1, 2], [1, 2]]),
                                                         ([[1, 3]], [[1, 2]])]),
                         ["pass", "fail", "fail"])

    def test_float(self):
        self.assertEqual(self.check("float", [(2.000001, 2.0), ([None, 1.500004], [None, 1.5]),
                                              (2.001, 2.0), ([1.0], [1.0, 2.0])]),
                         ["pass", "pass", "fail", "fail"])

    TOPO = [{"name": "numCourses", "type": "int"}, {"name": "prerequisites", "type": "int[][]"}]

    def test_checker_topo_order(self):
        graph = [4, [[1, 0], [2, 0], [3, 1], [3, 2]]]
        cyclic = [2, [[1, 0], [0, 1]]]
        res = self.check_fixed("checker:topo_order", self.TOPO, [
            (graph, [0, 2, 1, 3], [0, 1, 2, 3]),   # valid, different from expected
            (graph, [0, 3, 1, 2], [0, 1, 2, 3]),   # 3 before its prerequisites
            (graph, [0, 1, 2], [0, 1, 2, 3]),      # missing a course
            (graph, [0, 1, 1, 3], [0, 1, 2, 3]),   # repeated course
            (cyclic, [], []),                      # impossible, empty expected
            ([2, [[1, 0]]], [], [0, 1]),           # empty when an order exists
            (cyclic, [0, 1], []),                  # an order when none exists
        ])
        self.assertEqual(res, ["pass", "fail", "fail", "fail", "pass", "fail", "fail"])

    def test_checker_palindrome_substring(self):
        params = [{"name": "s", "type": "str"}]
        res = self.check_fixed("checker:palindrome_substring", params, [
            (["babad"], "aba", "bab"),   # valid, different from expected
            (["babad"], "bab", "bab"),
            (["babad"], "bad", "bab"),   # same length, not a palindrome
            (["babad"], "b", "bab"),     # palindrome, too short
            (["babad"], "cdc", "bab"),   # palindrome, not a substring
        ])
        self.assertEqual(res, ["pass", "pass", "fail", "fail", "fail"])

    def test_checker_alien_order(self):
        params = [{"name": "words", "type": "str[]"}]
        words = ["hrn", "hrf", "er", "enn", "rfnn"]
        free = ["ab", "ac", "d"]   # b < c and a < d; several orders are valid
        bad = ["abc", "ab"]        # a prefix after its extension: no order
        res = self.check_fixed("checker:alien_order", params, [
            ([words], "hernf", "hernf"),
            ([words], "fhern", "hernf"),   # breaks n < f
            ([words], "hern", "hernf"),    # missing a letter
            ([free], "bacd", "abcd"),      # valid, different from expected
            ([free], "cbad", "abcd"),      # breaks b < c
            ([free], "abcdd", "abcd"),     # repeated letter
            ([bad], "", ""),
            ([bad], "abc", ""),
        ])
        self.assertEqual(res, ["pass", "fail", "fail", "pass", "fail", "fail", "pass", "fail"])


class GeneratorTests(unittest.TestCase):
    def test_range(self):
        self.assertEqual(harness.expand({"$range": [0, 10, 3]}), [0, 3, 6, 9])

    def test_repeat_expands_value_first_and_copies(self):
        out = harness.expand({"$repeat": [{"$range": [0, 2, 1]}, 3]})
        self.assertEqual(out, [[0, 1], [0, 1], [0, 1]])
        out[0].append(9)
        self.assertEqual(out[1], [0, 1])

    def test_lcg_is_pinned(self):
        spec = {"$lcg": {"n": 5, "lo": 0, "hi": 9, "seed": 1}}
        self.assertEqual(harness.expand(spec), [0, 5, 4, 1, 4])
        self.assertEqual(harness.expand(spec), [0, 5, 4, 1, 4])

    def test_lcg_respects_bounds(self):
        out = harness.expand({"$lcg": {"n": 200, "lo": -3, "hi": 3, "seed": 42}})
        self.assertEqual(len(out), 200)
        self.assertTrue(all(-3 <= v <= 3 for v in out))

    def test_str(self):
        self.assertEqual(harness.expand({"$str": {"chars": "ab", "n": 6, "seed": 7}}), "ababab")
        out = harness.expand({"$str": {"chars": "xyz", "n": 50, "seed": 3}})
        self.assertEqual(len(out), 50)
        self.assertEqual(set(out) - set("xyz"), set())

    def test_nested_generators_inside_args(self):
        self.assertEqual(harness.expand([1, {"a": {"$range": [0, 2, 1]}}]), [1, {"a": [0, 1]}])

    def test_generators_through_runner_and_display(self):
        code = "class Solution:\n    def f(self, nums, s):\n        return [len(nums), len(s)]\n"
        spec = fn_spec("f", [{"name": "nums", "type": "int[]"}, {"name": "s", "type": "str"}], "int[]",
                       [case([{"$lcg": {"n": 20000, "lo": 0, "hi": 9, "seed": 1}},
                              {"$str": {"chars": "ab", "n": 300, "seed": 2}}],
                             [20000, 300])])
        res = runner.run(spec, code)
        self.assertEqual(statuses(res), ["pass"])
        self.assertEqual(res["results"][0]["input"], "nums = <20000 integers>, s = <300 characters>")


class GeneratedExpectedTests(unittest.TestCase):
    CODE = "class Solution:\n    def f(self, n):\n        return list(range(n))\n"

    def spec(self, expected, **extra):
        return fn_spec("f", [{"name": "n", "type": "int"}], "int[]", [case([5], expected)], **extra)

    def test_a_generated_expected_list_is_expanded_before_comparing(self):
        res = runner.run(self.spec({"$range": [0, 5, 1]}), self.CODE)
        self.assertEqual(statuses(res), ["pass"])
        self.assertEqual(res["results"][0]["expected"], "<5 integers>")  # the display stays short

    def test_a_wrong_generated_expected_still_fails(self):
        self.assertEqual(statuses(runner.run(self.spec({"$range": [1, 6, 1]}), self.CODE)), ["fail"])

    def test_generators_nested_inside_expected_are_expanded(self):
        code = "class Solution:\n    def f(self, n):\n        return [[7, 7], [0, 1, 2]]\n"
        spec = self.spec([{"$repeat": [7, 2]}, {"$range": [0, 3, 1]}])
        self.assertEqual(statuses(runner.run(spec, code)), ["pass"])


class StackFallbackTests(unittest.TestCase):
    MB = 1024 * 1024

    def setUp(self):
        # threading.stack_size() with no argument also resets the size to 0 on 3.9, so the test
        # records the sizes the harness sets instead of reading them back.
        real_stack_size, real_start = threading.stack_size, threading.Thread.start
        self.addCleanup(real_stack_size, 0)
        self.addCleanup(sys.setrecursionlimit, sys.getrecursionlimit())
        self.size = 0
        self.fail_above = 10 ** 12

        def stack_size(new=0):
            self.size = new
            return real_stack_size(new)

        def start(thread):
            if self.size > self.fail_above:  # the size was accepted, but the thread cannot start
                raise RuntimeError("can't start new thread")
            return real_start(thread)

        for target, name, repl in ((threading, "stack_size", stack_size), (threading.Thread, "start", start)):
            patcher = mock.patch.object(target, name, repl)
            patcher.start()
            self.addCleanup(patcher.stop)

    def run_user_code_in_thread(self):
        names = []
        finished, value, exc = harness._in_thread(lambda: names.append(threading.current_thread().name) or 41, 5)
        self.assertTrue(finished)
        self.assertIsNone(exc)
        self.assertEqual(value, 41)
        self.assertNotEqual(names, ["MainThread"])

    def test_when_512_and_256_mb_threads_cannot_start_it_falls_back_to_64(self):
        self.fail_above = 64 * self.MB
        harness._set_limits()
        self.assertEqual(self.size, 64 * self.MB)
        self.run_user_code_in_thread()

    def test_when_no_big_thread_can_start_user_code_still_runs_in_a_default_thread(self):
        self.fail_above = 0
        harness._set_limits()
        self.assertEqual(self.size, 0)
        self.run_user_code_in_thread()

    def test_the_largest_size_is_kept_when_it_works(self):
        harness._set_limits()
        self.assertEqual(self.size, 512 * self.MB)


class DisplayTests(unittest.TestCase):
    def test_display_value(self):
        self.assertEqual(harness.display_value([1, [2, None], "a", True]), '[1,[2,null],"a",true]')
        self.assertEqual(harness.display_value({"$range": [0, 100, 1]}), "<100 integers>")

    def test_display_cut_to_400(self):
        text = harness.display_value(list(range(1000)))
        self.assertEqual(len(text), 400)
        self.assertTrue(text.endswith("…"))

    def test_display_input_function(self):
        spec = fn_spec("f", [{"name": "nums", "type": "int[]"}, {"name": "target", "type": "int"}], "int[]", [])
        self.assertEqual(harness.display_input(spec, case([[2, 7, 11, 15], 9], [0, 1])),
                         "nums = [2,7,11,15], target = 9")

    def test_display_input_design(self):
        spec = {"driver": "design", "params": []}
        text = harness.display_input(spec, {"ops": ["A", "b"], "args": [[], [1]]})
        self.assertEqual(text, '["A","b"]\n[[],[1]]')


if __name__ == "__main__":
    unittest.main()
