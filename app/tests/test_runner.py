"""Runner robustness: hostile or broken user code still yields a truthful per-case result."""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock

from app.prep import harness, runner


def spec_for(cases, limit=2.0, method="f", params=None):
    return {"slug": "t", "driver": "function", "class": "Solution", "method": method,
            "params": params if params is not None else [{"name": "n", "type": "int"}],
            "returns": "int", "compare": "exact", "time_limit_s": limit, "cases": cases}


def case(n, expected, name, example=True):
    return {"name": name, "example": example, "args": [n], "expected": expected}


def statuses(result):
    return [r["status"] for r in result["results"]]


THREE = [case(1, 1, "a"), case(2, 2, "b"), case(3, 3, "c")]


def run_bounded(spec, code, bound_s, **kwargs):
    """runner.run in a helper thread: a hung kill path fails the test after bound_s instead of
    hanging the suite. Returns (result, elapsed seconds)."""
    box = {}

    def target():
        box["res"] = runner.run(spec, code, **kwargs)

    started = time.monotonic()
    worker = threading.Thread(target=target, daemon=True)
    worker.start()
    worker.join(bound_s)
    elapsed = time.monotonic() - started
    if worker.is_alive():
        raise AssertionError("runner.run did not return within %.1f s (hung kill path?)" % bound_s)
    return box["res"], elapsed


def alive(pid):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True


def wait_dead(pid, seconds=5.0):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        if not alive(pid):
            return True
        time.sleep(0.05)
    return not alive(pid)


GRANDCHILD = ("import subprocess, sys\n"
              "class Solution:\n"
              "    def f(self, n):\n"
              "        p = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])\n"
              "        with open(%r, 'w') as fh:\n"
              "            fh.write(str(p.pid))\n"
              "        %s\n")


class TimeoutTests(unittest.TestCase):
    def test_infinite_loop_times_out_and_later_cases_not_run(self):
        code = """
class Solution:
    def f(self, n):
        while n == 2:
            pass
        return n
"""
        res, elapsed = run_bounded(spec_for(THREE, limit=0.5), code, 0.5 + 6)
        self.assertEqual(statuses(res), ["pass", "timeout", "not_run"])
        self.assertLess(elapsed, 0.5 + 6)
        self.assertEqual(res["passed"], 1)
        self.assertEqual(res["total"], 3)

    def test_timeout_keeps_printed_output(self):
        code = "class Solution:\n    def f(self, n):\n        print('looping')\n        while True:\n            pass\n"
        res = runner.run(spec_for(THREE[:1], limit=0.5), code)
        self.assertEqual(statuses(res), ["timeout"])
        self.assertEqual(res["results"][0]["stdout"], "looping\n")

    def test_lone_surrogate_in_output(self):
        code = "class Solution:\n    def f(self, n):\n        print('\\ud800')\n        return '\\ud800'\n"
        res = runner.run(spec_for(THREE[:1]), code)
        self.assertEqual(statuses(res), ["fail"])

    def test_sleep_in_first_case(self):
        code = "import time\nclass Solution:\n    def f(self, n):\n        time.sleep(30)\n"
        res, elapsed = run_bounded(spec_for(THREE[:2], limit=0.5), code, 0.5 + 6)
        self.assertEqual(statuses(res), ["timeout", "not_run"])
        self.assertLess(elapsed, 0.5 + 6)


class ParentKillTests(unittest.TestCase):
    """The child cannot enforce its own limits while one C call holds the GIL (10**10**9), so only
    the parent's whole-run limit ends it. The parent's constants are patched so the tests take ~2 s."""

    HOLD_GIL = "10**10**9"

    def setUp(self):
        for obj, name in ((runner, "EXTRA_S"), (harness, "LOAD_LIMIT_S")):
            patcher = mock.patch.object(obj, name, 0.5)  # only the parent reads these; the child keeps its own
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_a_child_that_ignores_its_case_limit_is_killed_and_reported_as_a_timeout(self):
        code = "class Solution:\n    def f(self, n):\n        return %s\n" % self.HOLD_GIL
        res, elapsed = run_bounded(spec_for(THREE[:2], limit=0.5), code, 15)
        self.assertIsNone(res["fatal"])
        self.assertEqual(statuses(res), ["timeout", "not_run"])
        self.assertLess(elapsed, 0.5 + 0.5 + 0.5 + 6)  # case limit + load limit + extra + a startup margin

    def test_a_child_that_never_finishes_loading_is_a_fatal_timeout(self):
        code = "x = %s\nclass Solution:\n    def f(self, n):\n        return n\n" % self.HOLD_GIL
        res, elapsed = run_bounded(spec_for(THREE, limit=0.5), code, 15)
        self.assertEqual(res["fatal"]["type"], "Timeout")
        self.assertEqual(res["fatal"]["message"], "your code did not finish loading in time")
        self.assertEqual(res["results"], [])
        self.assertEqual(res["total"], 3)
        self.assertLess(elapsed, 0.5 * 3 + 0.5 + 0.5 + 6)

    def spawn_and_get_pid(self, tail):
        pid_dir = tempfile.TemporaryDirectory()
        self.addCleanup(pid_dir.cleanup)
        pid_file = os.path.join(pid_dir.name, "pid")
        res, _ = run_bounded(spec_for(THREE[:1], limit=0.5), GRANDCHILD % (pid_file, tail), 15)
        self.assertEqual(statuses(res), ["timeout"])
        with open(pid_file) as fh:
            pid = int(fh.read())
        self.addCleanup(lambda: alive(pid) and os.kill(pid, 9))
        return pid

    def test_a_process_spawned_by_the_solution_dies_with_a_parent_kill(self):
        pid = self.spawn_and_get_pid(self.HOLD_GIL)
        self.assertTrue(wait_dead(pid), "the grandchild %d outlived the run" % pid)

    def test_a_process_spawned_by_the_solution_dies_with_a_case_timeout(self):
        pid = self.spawn_and_get_pid("while True:\n            pass")  # the child reports the timeout itself and exits
        self.assertTrue(wait_dead(pid), "the grandchild %d outlived the run" % pid)

    def test_killing_an_already_gone_group_is_not_an_error(self):
        with mock.patch.object(runner.os, "killpg", side_effect=ProcessLookupError):
            res = runner.run(spec_for(THREE[:1]), "class Solution:\n    def f(self, n):\n        return n\n")
        self.assertEqual(statuses(res), ["pass"])


class StderrTailTests(unittest.TestCase):
    def write(self, data):
        fd, path = tempfile.mkstemp(prefix="stderr-test-")
        os.close(fd)
        self.addCleanup(os.remove, path)
        with open(path, "wb") as fh:
            fh.write(data)
        return path

    def test_only_the_last_64_kb_are_read(self):
        path = self.write(b"A" * 5_000_000 + "end \u00e9\n".encode("utf-8"))
        real_open, read = open, []

        class Spy:
            def __init__(self, fh):
                self.fh = fh

            def __getattr__(self, name):
                return getattr(self.fh, name)

            def __enter__(self):
                return self

            def __exit__(self, *exc):
                self.fh.close()

            def read(self, *args):
                data = self.fh.read(*args)
                read.append(len(data))
                return data

        def spy_open(file, mode="r", *args, **kwargs):
            return Spy(real_open(file, "rb"))

        with mock.patch.object(runner, "open", spy_open, create=True):
            tail = runner._stderr_tail(path)
        self.assertLessEqual(sum(read), 64 * 1024)
        self.assertIsInstance(tail, str)
        self.assertTrue(tail.endswith("end \u00e9"))
        self.assertEqual(len(tail), runner.STDERR_TAIL)

    def test_a_cut_multibyte_character_at_the_seek_point_is_replaced_not_raised(self):
        path = self.write("\u00e9".encode("utf-8") * 100_000)
        tail = runner._stderr_tail(path)
        self.assertEqual(len(tail), runner.STDERR_TAIL)

    def test_a_missing_file_gives_an_empty_tail(self):
        self.assertEqual(runner._stderr_tail("/nonexistent/stderr.txt"), "")

    def test_a_flood_of_stderr_still_runs_and_reports(self):
        code = ("import sys\nclass Solution:\n    def f(self, n):\n"
                "        sys.stderr.write('e' * 3_000_000)\n        return n\n")
        self.assertEqual(statuses(runner.run(spec_for(THREE[:1]), code)), ["pass"])


class OutputAndExitTests(unittest.TestCase):
    def test_print_is_captured_per_case(self):
        code = "class Solution:\n    def f(self, n):\n        print('seen', n)\n        return n\n"
        res = runner.run(spec_for(THREE[:2]), code)
        self.assertEqual(statuses(res), ["pass", "pass"])
        self.assertEqual(res["results"][0]["stdout"], "seen 1\n")
        self.assertEqual(res["results"][1]["stdout"], "seen 2\n")

    def test_print_is_cut_to_2000_characters(self):
        code = "class Solution:\n    def f(self, n):\n        print('x' * 5000)\n        return n\n"
        res = runner.run(spec_for(THREE[:1]), code)
        self.assertEqual(len(res["results"][0]["stdout"]), 2000)

    def test_sys_exit_is_an_error_and_later_cases_still_run(self):
        code = ("import sys\nclass Solution:\n    def f(self, n):\n"
                "        if n == 1:\n            sys.exit(3)\n        return n\n")
        res = runner.run(spec_for(THREE[:2]), code)
        self.assertEqual(statuses(res), ["error", "pass"])
        err = res["results"][0]["error"]
        self.assertEqual(err["type"], "SystemExit")
        self.assertEqual(err["message"], "sys.exit() was called (code 3)")
        self.assertEqual(err["line"], 5)

    def test_os_exit_is_an_error_and_later_cases_are_not_run(self):
        code = "import os\nclass Solution:\n    def f(self, n):\n        if n == 2:\n            os._exit(7)\n        return n\n"
        res = runner.run(spec_for(THREE), code)
        self.assertEqual(statuses(res), ["pass", "error", "not_run"])
        err = res["results"][1]["error"]
        self.assertEqual(err["type"], "ProcessExit")
        self.assertEqual(err["message"], "the process ended during this case (exit code 7)")


class RecursionTests(unittest.TestCase):
    RECURSE = """
class Solution:
    def f(self, n):
        return 0 if n == 0 else 1 + self.f(n - 1)
"""

    def test_depth_15000_succeeds(self):
        res = runner.run(spec_for([case(15000, 15000, "deep")]), self.RECURSE)
        self.assertEqual(statuses(res), ["pass"])

    def test_depth_50000_is_a_recursion_error_and_the_next_case_still_runs(self):
        res = runner.run(spec_for([case(50000, 50000, "deep"), case(2, 2, "next")]), self.RECURSE)
        self.assertEqual(statuses(res), ["error", "pass"])
        err = res["results"][0]["error"]
        self.assertEqual(err["type"], "RecursionError")
        self.assertEqual(err["message"], "maximum recursion depth exceeded in comparison")

    def test_unbounded_recursion_is_an_error(self):
        code = "class Solution:\n    def f(self, n):\n        return self.f(n + 1)\n"
        res = runner.run(spec_for([case(1, 1, "inf"), case(2, 2, "next")]), code)
        self.assertEqual(statuses(res)[0], "error")
        self.assertEqual(res["results"][0]["error"]["type"], "RecursionError")


class FatalAndErrorTests(unittest.TestCase):
    def test_syntax_error_is_fatal_with_line(self):
        code = "class Solution:\n    def f(self, n):\n        return n +\n"
        res = runner.run(spec_for(THREE), code)
        self.assertEqual(res["fatal"]["type"], "SyntaxError")
        self.assertEqual(res["fatal"]["line"], 3)
        self.assertEqual(res["results"], [])
        self.assertEqual(res["passed"], 0)
        self.assertEqual(res["total"], 3)

    def test_import_time_exception_is_fatal(self):
        res = runner.run(spec_for(THREE), "x = 1\nraise ValueError('boom')\n")
        self.assertEqual(res["fatal"]["type"], "ValueError")
        self.assertEqual(res["fatal"]["line"], 2)

    def test_missing_method_is_fatal_and_named(self):
        code = "class Solution:\n    def g(self, n):\n        return n\n"
        res = runner.run(spec_for(THREE, method="twoSum"), code)
        self.assertIsNotNone(res["fatal"])
        self.assertIn("twoSum", res["fatal"]["message"])

    def test_missing_class_is_fatal(self):
        res = runner.run(spec_for(THREE), "def f(n):\n    return n\n")
        self.assertIn("Solution", res["fatal"]["message"])

    def test_exception_reports_user_line_and_trace(self):
        code = "class Solution:\n    def f(self, n):\n        x = [1]\n        return x[n]\n"
        res = runner.run(spec_for([case(0, 1, "ok"), case(5, 0, "bad")]), code)
        self.assertEqual(statuses(res), ["pass", "error"])
        err = res["results"][1]["error"]
        self.assertEqual(err["type"], "IndexError")
        self.assertEqual(err["line"], 4)
        self.assertIn("solution.py", err["trace"])
        self.assertNotIn("harness.py", err["trace"])

    def test_empty_code_is_fatal(self):
        res = runner.run(spec_for(THREE), "")
        self.assertIsNotNone(res["fatal"])


class InputAndResultTests(unittest.TestCase):
    def test_mutation_does_not_corrupt_displayed_input(self):
        code = "class Solution:\n    def f(self, nums):\n        nums.clear()\n        return 0\n"
        spec = spec_for([{"name": "m", "example": True, "args": [[1, 2, 3]], "expected": 0}],
                        params=[{"name": "nums", "type": "int[]"}])
        res = runner.run(spec, code)
        self.assertEqual(res["results"][0]["input"], "nums = [1,2,3]")

    def test_mutation_does_not_leak_between_runs_of_shared_args(self):
        code = "class Solution:\n    def f(self, nums):\n        nums.append(9)\n        return len(nums)\n"
        spec = spec_for([{"name": "a", "example": True, "args": [[1]], "expected": 2},
                         {"name": "b", "example": True, "args": [[1]], "expected": 2}],
                        params=[{"name": "nums", "type": "int[]"}])
        self.assertEqual(statuses(runner.run(spec, code)), ["pass", "pass"])

    def test_union_annotation_runs_on_39(self):
        code = """
class Solution:
    def f(self, head: ListNode | None, k: int | None = None) -> ListNode | None:
        return head
"""
        spec = spec_for([{"name": "u", "example": True, "args": [[1, 2]], "expected": [1, 2]}],
                        params=[{"name": "head", "type": "ListNode"}])
        spec["returns"] = "ListNode"
        self.assertEqual(statuses(runner.run(spec, code)), ["pass"])

    def test_typing_names_without_imports(self):
        code = """
class Solution:
    def f(self, nums: List[int], root: Optional[TreeNode]) -> Dict[str, int]:
        c = Counter(nums)
        q = deque([1])
        heappush(nums, 0)
        return {"n": len(c) + len(q) + int(inf > 0) + len(nums)}
"""
        spec = spec_for([{"name": "t", "example": True, "args": [[1, 1, 2], []], "expected": {"n": 8}}],
                        params=[{"name": "nums", "type": "int[]"}, {"name": "root", "type": "TreeNode"}])
        self.assertEqual(statuses(runner.run(spec, code)), ["pass"])

    def test_counter_is_collections_counter_not_typing(self):
        code = "class Solution:\n    def f(self, n):\n        return Counter('aab')['a']\n"
        self.assertEqual(statuses(runner.run(spec_for([case(0, 2, "c")]), code)), ["pass"])

    def test_examples_only(self):
        cases = [case(1, 1, "a"), case(2, 2, "hidden", example=False), case(3, 3, "b")]
        code = "class Solution:\n    def f(self, n):\n        return n\n"
        res = runner.run(spec_for(cases), code, examples_only=True)
        self.assertEqual([r["name"] for r in res["results"]], ["a", "b"])
        self.assertEqual(res["total"], 2)
        self.assertEqual(runner.run(spec_for(cases), code)["total"], 3)

    def test_result_shape(self):
        code = "class Solution:\n    def f(self, n):\n        return n + 1\n"
        res = runner.run(spec_for([case(1, 1, "a")]), code)
        self.assertIsNone(res["fatal"])
        row = res["results"][0]
        for key in ("name", "example", "status", "input", "expected", "got", "stdout", "ms", "error"):
            self.assertIn(key, row)
        self.assertEqual(row["status"], "fail")
        self.assertEqual(row["input"], "n = 1")
        self.assertEqual(row["expected"], "1")
        self.assertEqual(row["got"], "2")
        self.assertIsNone(row["error"])
        self.assertIsInstance(row["ms"], (int, float))

    def test_run_never_raises_on_bad_spec(self):
        res = runner.run({"slug": "broken"}, "class Solution:\n    pass\n")
        self.assertIsNotNone(res["fatal"])


if __name__ == "__main__":
    unittest.main()
