"""API: every route through App.handle, on a temporary kit with the real problem data."""
from __future__ import annotations

import io
import json
import os
import shutil
import sys
import threading
import time
import unittest
from datetime import datetime
from unittest import mock

from app.prep import api, paths
from app.tests.kit import Clock, make_kit

FAKE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fake_coach.py")
FAKE_CMD = [sys.executable, FAKE]
REAL = paths.default()
PORT = 8765

TWO_SUM = """class Solution:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        seen = {}
        for i, x in enumerate(nums):
            if target - x in seen:
                return [seen[target - x], i]
            seen[x] = i
"""
DUP_WRONG = """class Solution:
    def containsDuplicate(self, nums: List[int]) -> bool:
        return False
"""
DUP_RIGHT = """class Solution:
    def containsDuplicate(self, nums: List[int]) -> bool:
        return len(set(nums)) != len(nums)
"""


def full_kit(case):
    kit = make_kit(case)
    shutil.copyfile(os.path.join(REAL.data, "problems.json"), os.path.join(kit.data, "problems.json"))
    shutil.copytree(REAL.tests_dir, kit.tests_dir)
    return kit


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


MISSING_CODEX = ["/nonexistent/codex-for-prep-tests"]
PROVIDERS = [{"key": "claude", "label": "Claude Code", "command": "claude", "found": True,
              "install_url": "https://claude.com/claude-code"},
             {"key": "codex", "label": "OpenAI Codex", "command": "codex", "found": False,
              "install_url": "https://github.com/openai/codex"}]
COACH = {"choice": None, "active": "claude", "providers": PROVIDERS}


class ApiCase(unittest.TestCase):
    coach_cmd = FAKE_CMD
    codex_cmd = MISSING_CODEX  # never the machine's own codex

    def setUp(self):
        self.kit = full_kit(self)
        self.clock = Clock()
        self.errlog = io.StringIO()
        self.app = api.App(self.kit, PORT, coach_cmd=self.coach_cmd, now=self.clock,
                           log=self.errlog, codex_cmd=self.codex_cmd)
        patcher = mock.patch.dict(os.environ, {"FAKE_COACH_MODE": "auto"})
        patcher.start()
        self.addCleanup(patcher.stop)
        for key in ("FAKE_COACH_LOG", "FAKE_COACH_REVIEW", "PREP_COACH_MODEL"):
            os.environ.pop(key, None)

    def raw(self, method, path, body=None, headers=None, query=None):
        h = {"Host": "127.0.0.1:%d" % PORT}
        if method != "GET":
            h["Content-Type"] = "application/json"
        if headers:
            h.update(headers)
        h = {k: v for k, v in h.items() if v is not None}
        if body is None:
            data = b"" if method == "GET" else b"{}"
        elif isinstance(body, bytes):
            data = body
        else:
            data = json.dumps(body).encode()
        return self.app.handle(method, path, query or {}, h, data)

    def call(self, method, path, body=None, headers=None, query=None, status=200):
        resp = self.raw(method, path, body, headers, query)
        self.assertIsNone(resp.stream)
        self.assertEqual(resp.headers.get("Content-Type"), "application/json; charset=utf-8")
        out = json.loads(resp.body.decode("utf-8"))
        self.assertEqual(resp.status, status, out)
        if status >= 400:
            self.assertEqual(set(out), {"error", "detail"} | set(out) & {"save_error"})
            self.assertTrue(out["detail"])
        return out

    def submit(self, slug, code, notes=None):
        return self.call("POST", "/api/problem/%s/submit" % slug, {"code": code, "notes": notes or {}})

    def matrix_cell(self, row_id, column):
        for group in self.call("GET", "/api/matrix")["groups"]:
            for row in group["rows"]:
                if row["id"] == row_id:
                    return row[column]
        return None

    def set_matrix_cell(self, row_id, now):
        path = os.path.join(self.kit.my_prep, "skills-matrix.md")
        lines = read(path).split("\n")
        for i, line in enumerate(lines):
            if line.startswith("| %s |" % row_id):
                cells = line.split("|")
                cells[6] = " %s " % now
                lines[i] = "|".join(cells)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines))


class OverviewTests(ApiCase):
    def test_fresh_overview(self):
        out = self.call("GET", "/api/overview")
        self.assertEqual(set(out), {"day", "current_module", "warmup", "kpis", "modules", "matrix",
                                    "mistakes", "setup", "onboarding", "notices"})
        self.assertEqual(out["onboarding"], {"discovery": False, "discovery_started": False,
                                             "self_check": False, "diagnostic": False,
                                             "diagnostic_started": False, "scored": False})
        self.assertEqual(out["notices"], [])
        self.assertEqual(out["day"], 1)
        self.assertEqual(out["current_module"], {"id": "01", "title": "Arrays and hashing"})
        problems = json.loads(read(os.path.join(REAL.data, "problems.json")))
        first_easy = next(p for p in problems if p["module"] == "01" and p["difficulty"] == "Easy")
        self.assertEqual(out["warmup"], {"slug": first_easy["slug"], "title": first_easy["title"],
                                         "difficulty": "Easy", "module": "01",
                                         "module_title": "Arrays and hashing", "done": False})
        self.assertEqual(out["kpis"], {"solved": 0, "total": 119, "solved_week": 0, "seconds": 0,
                                       "seconds_week": 0, "streak": 0, "best_streak": 0,
                                       "first_try_pct": 0, "first_try_n": 0, "submitted_n": 0})
        ids = [m["id"] for m in out["modules"]]
        self.assertEqual(ids, ["%02d" % i for i in range(1, 11)] + ["00"])
        self.assertEqual(out["modules"][0], {"id": "01", "title": "Arrays and hashing", "solved": 0,
                                             "total": 9, "pct": 0, "read": None})
        self.assertEqual(out["modules"][-1], {"id": "00", "title": "Before you start", "read": False})
        self.assertEqual([r["id"] for r in out["matrix"]], ["A%d" % i for i in range(1, 19)])
        self.assertEqual(out["matrix"][0], {"id": "A1", "now": "?", "priority": "P0",
                                            "requirement": out["matrix"][0]["requirement"]})
        self.assertEqual(out["mistakes"], [])
        self.assertEqual(out["setup"], {"statements_have": 0, "statements_total": 119,
                                        "claude": True, "coach": COACH})
        # opening Home does not count as activity
        self.assertEqual(self.app.store.snapshot()["problems"], {})

    def test_overview_after_progress(self):
        self.call("POST", "/api/heartbeat", {"slug": "two-sum", "seconds": 45})
        self.submit("contains-duplicate", DUP_RIGHT)
        self.submit("two-sum", TWO_SUM)
        self.call("POST", "/api/module/00/read", {"read": True})
        self.clock.advance(days=2)
        out = self.call("GET", "/api/overview")
        self.assertEqual(out["day"], 3)
        k = out["kpis"]
        self.assertEqual((k["solved"], k["solved_week"], k["seconds"], k["submitted_n"],
                          k["first_try_n"], k["first_try_pct"], k["best_streak"]),
                         (2, 2, 45, 2, 2, 100, 1))
        self.assertEqual(out["modules"][0]["solved"], 2)
        self.assertEqual(out["modules"][0]["pct"], 22)
        self.assertIs(out["modules"][-1]["read"], True)
        self.assertEqual(out["matrix"][0]["now"], "2")

    def test_mistakes_come_from_learnings_when_top5_is_empty(self):
        sub = self.submit("two-sum", TWO_SUM)
        self.call("POST", "/api/problem/two-sum/review", {"submit_id": sub["submit_id"]})
        out = self.call("GET", "/api/overview")
        self.assertEqual(out["mistakes"], [{"bug": "off by one on the last index",
                                            "check": "trace the last element by hand",
                                            "source": "learnings"}])

    def test_onboarding_follows_the_notes(self):
        plan = os.path.join(self.kit.my_prep, "plan.md")
        profile = os.path.join(self.kit.my_prep, "profile.md")
        with open(profile, encoding="utf-8") as fh:
            text = fh.read()
        with open(profile, "w", encoding="utf-8") as fh:
            fh.write(text.replace("## Target\n", "## Target\n\nA backend role, first round in a month.\n", 1))
        self.assertEqual(self.call("GET", "/api/overview")["onboarding"],
                         {"discovery": False, "discovery_started": True, "self_check": False,
                          "diagnostic": False, "diagnostic_started": False, "scored": False})
        with open(plan, encoding="utf-8") as fh:
            text = fh.read()
        with open(plan, "w", encoding="utf-8") as fh:
            fh.write(text.replace("- [ ] Discovery", "- [x] Discovery").replace("- [ ] Diagnostic", "- [x] Diagnostic"))
        self.assertEqual(self.call("GET", "/api/overview")["onboarding"],
                         {"discovery": True, "discovery_started": True, "self_check": False,
                          "diagnostic": True, "diagnostic_started": True, "scored": False})

    def test_warmup_another(self):
        first = self.call("GET", "/api/overview")["warmup"]["slug"]
        other = self.call("POST", "/api/warmup/another", {})["warmup"]
        self.assertNotEqual(other["slug"], first)
        self.assertEqual(set(other), {"slug", "title", "difficulty", "module", "module_title", "done"})
        self.assertEqual(self.call("GET", "/api/overview")["warmup"]["slug"], other["slug"])


class ProblemTests(ApiCase):
    def test_problems_list(self):
        out = self.call("GET", "/api/problems")
        self.assertEqual(len(out["problems"]), 119)
        self.assertEqual(set(out["problems"][0]),
                         {"slug", "number", "title", "difficulty", "module", "category", "url",
                          "premium", "status", "seconds", "solved_at", "last_at", "starred"})
        self.assertEqual({p["status"] for p in out["problems"]}, {"new"})
        self.assertEqual(out["modules"][0], {"id": "01", "title": "Arrays and hashing"})
        self.assertEqual(len(out["modules"]), 10)
        self.submit("two-sum", TWO_SUM)
        self.submit("contains-duplicate", DUP_WRONG)
        by = {p["slug"]: p for p in self.call("GET", "/api/problems")["problems"]}
        self.assertEqual(by["two-sum"]["status"], "solved")
        self.assertTrue(by["two-sum"]["solved_at"])
        self.assertEqual(by["contains-duplicate"]["status"], "attempted")

    def test_problems_carry_last_at(self):
        out = self.call("GET", "/api/problems")
        self.assertTrue(all("last_at" in p and p["last_at"] is None for p in out["problems"]))
        self.clock.advance(minutes=5)
        self.submit("two-sum", TWO_SUM)  # saves the draft (file mtime is real time) and submits
        sol = os.path.join(self.kit.solutions_dir, "two-sum.py")
        os.utime(sol, (1767225600, 1767225600))  # an old draft save: the submit is the latest
        by = {p["slug"]: p for p in self.call("GET", "/api/problems")["problems"]}
        self.assertEqual(by["two-sum"]["last_at"], "2026-11-12T09:05:00")
        self.assertIsNone(by["contains-duplicate"]["last_at"])
        self.clock.advance(minutes=10)
        self.app.store.add_chat("two-sum", "user", "hint", "t")
        by = {p["slug"]: p for p in self.call("GET", "/api/problems")["problems"]}
        self.assertEqual(by["two-sum"]["last_at"], "2026-11-12T09:15:00")
        future = 4102488000  # noon UTC on 2100-01-01: a draft save later than everything else
        os.utime(sol, (future, future))
        by = {p["slug"]: p for p in self.call("GET", "/api/problems")["problems"]}
        self.assertEqual(by["two-sum"]["last_at"],
                         datetime.fromtimestamp(future).isoformat(timespec="seconds"))

    def test_star_a_problem(self):
        path = "/api/problem/two-sum/star"
        self.assertIs(self.call("GET", "/api/problem/two-sum")["starred"], False)
        self.assertEqual({p["starred"] for p in self.call("GET", "/api/problems")["problems"]}, {False})
        self.assertEqual(self.call("POST", path, {"starred": True}), {"ok": True, "starred": True})
        self.assertEqual(self.call("POST", path, {"starred": True}), {"ok": True, "starred": True})
        by = {p["slug"]: p for p in self.call("GET", "/api/problems")["problems"]}
        self.assertIs(by["two-sum"]["starred"], True)
        self.assertEqual(by["two-sum"]["status"], "new")  # a star is not an attempt
        self.assertEqual(sum(p["starred"] for p in by.values()), 1)
        self.assertIs(self.call("GET", "/api/problem/two-sum")["starred"], True)
        self.assertEqual(self.app.store.snapshot()["problems"], {})
        again = api.App(self.kit, PORT, coach_cmd=self.coach_cmd, now=self.clock, log=self.errlog)
        self.assertIs(json.loads(again.handle("GET", "/api/problem/two-sum", {},
                                              {"Host": "127.0.0.1:%d" % PORT}, b"").body)["starred"], True)
        self.assertEqual(self.call("POST", path, {"starred": False}), {"ok": True, "starred": False})
        self.assertIs(self.call("GET", "/api/problem/two-sum")["starred"], False)

    def test_star_refuses_bad_requests(self):
        self.call("POST", "/api/problem/no-such-problem/star", {"starred": True}, status=404)
        for body in ({"starred": "yes"}, {"starred": 1}, {}, {"starred": None}):
            with self.subTest(body=body):
                self.call("POST", "/api/problem/two-sum/star", body, status=400)
        self.call("GET", "/api/problem/two-sum/star", status=405)
        self.assertEqual(self.app.store.starred(), set())

    def test_problem_detail_does_not_create_state(self):
        out = self.call("GET", "/api/problem/two-sum")
        for key in ("slug", "number", "title", "difficulty", "module", "category", "url",
                    "premium", "skeleton", "module_title", "status", "seconds", "hints_used",
                    "submits", "code", "notes", "chat", "examples", "statement", "attempt"):
            self.assertIn(key, out)
        self.assertEqual(out["status"], "new")
        self.assertEqual(out["code"], out["skeleton"])
        self.assertEqual(out["notes"], {"pattern": "", "complexity": "", "trace": "", "tests": ""})
        self.assertEqual(out["examples"][0], {"name": "Example 1",
                                              "input": "nums = [2,7,11,15], target = 9",
                                              "expected": "[0,1]"})
        self.assertIsNone(out["statement"])
        self.assertEqual(out["module_title"], "Arrays and hashing")
        self.assertEqual(self.app.store.snapshot()["problems"], {})
        self.assertFalse(os.path.exists(self.kit.state_file))

    def test_statement_is_returned_as_data(self):
        os.makedirs(self.kit.statements_dir)
        with open(os.path.join(self.kit.statements_dir, "two-sum.json"), "w") as fh:
            json.dump({"slug": "two-sum", "format": "html", "body": "<p>x</p>", "source": "leetcode",
                       "fetched_at": "2026-11-12T09:00:00"}, fh)
        with open(os.path.join(self.kit.statements_dir, "lru-cache.json"), "w") as fh:
            fh.write("{not json")
        with open(os.path.join(self.kit.statements_dir, "valid-anagram.json"), "w") as fh:
            json.dump({"format": "exe", "body": "x"}, fh)
        self.assertEqual(self.call("GET", "/api/problem/two-sum")["statement"],
                         {"format": "html", "body": "<p>x</p>"})
        self.assertIsNone(self.call("GET", "/api/problem/lru-cache")["statement"])
        self.assertIsNone(self.call("GET", "/api/problem/valid-anagram")["statement"])
        self.assertEqual(self.call("GET", "/api/overview")["setup"]["statements_have"], 1)

    def test_draft_round_trip(self):
        self.assertEqual(self.call("PUT", "/api/problem/two-sum/draft",
                                   {"code": "x = 1\n", "notes": {"pattern": "hash map"}}),
                         {"ok": True, "rev": 1})
        out = self.call("GET", "/api/problem/two-sum")
        self.assertEqual(out["code"], "x = 1\n")
        self.assertEqual(out["notes"]["pattern"], "hash map")
        self.assertEqual(out["status"], "attempted")
        self.assertEqual(read(os.path.join(self.kit.solutions_dir, "two-sum.py")), "x = 1\n")

    def test_unchanged_skeleton_draft_stays_new(self):
        skeleton = self.call("GET", "/api/problem/two-sum")["skeleton"]
        self.call("PUT", "/api/problem/two-sum/draft",
                  {"code": skeleton, "notes": {"pattern": "", "complexity": "", "trace": "", "tests": ""}})
        self.assertEqual(self.call("GET", "/api/problem/two-sum")["status"], "new")
        self.assertEqual(self.app.store.snapshot()["problems"], {})
        self.call("PUT", "/api/problem/two-sum/draft", {"code": skeleton, "notes": {"trace": "i=0"}})
        self.assertEqual(self.call("GET", "/api/problem/two-sum")["status"], "attempted")

    def test_draft_validation(self):
        self.call("PUT", "/api/problem/two-sum/draft", {"code": 5}, status=400)
        self.call("PUT", "/api/problem/two-sum/draft", {"code": "x", "notes": "text"}, status=400)
        self.call("PUT", "/api/problem/two-sum/draft", {"code": "x", "notes": {"pattern": 3}},
                  status=400)

    def test_run_examples_only(self):
        out = self.call("POST", "/api/problem/two-sum/run", {"code": TWO_SUM})
        self.assertEqual(set(out), {"fatal", "results", "passed", "total", "rev"})
        self.assertIsNone(out["fatal"])
        self.assertEqual(out["passed"], out["total"])
        self.assertEqual(out["total"], 3)
        self.assertTrue(all(r["example"] for r in out["results"]))
        self.assertIn("message", out["results"][0])
        entry = self.app.store.problem("two-sum")
        self.assertEqual(entry["runs"], 1)
        self.assertEqual(entry["status"], "attempted")
        self.assertEqual(self.app.store.code("two-sum"), TWO_SUM)

    def test_run_with_syntax_error_is_fatal(self):
        out = self.call("POST", "/api/problem/two-sum/run", {"code": "class Solution:\n  def ("})
        self.assertEqual(out["fatal"]["type"], "SyntaxError")
        self.assertEqual(out["results"], [])

    def test_submit_solves_and_writes_the_matrix(self):
        out = self.submit("two-sum", TWO_SUM)
        for key in ("fatal", "results", "passed", "total", "solved", "first_try", "submit_id",
                    "matrix"):
            self.assertIn(key, out)
        self.assertGreater(out["total"], 3)
        self.assertEqual(out["passed"], out["total"])
        self.assertIs(out["solved"], True)
        self.assertIs(out["first_try"], True)
        self.assertEqual(out["matrix"], {"row": "A1", "now": 2, "written": True})
        self.assertEqual(self.matrix_cell("A1", "now"), "2")
        self.assertEqual(self.matrix_cell("A1", "start"), "2")
        self.assertEqual(self.matrix_cell("A1", "last_tested"), "2026-11-12")
        self.assertEqual(self.matrix_cell("A1", "evidence"),
                         "LC 1 Two Sum: passes the app's tests, first try, in under 1 min, no hints (app)")
        self.assertEqual(self.app.store.matrix_written("A1"), "2")
        entry = self.app.store.problem("two-sum")
        self.assertEqual(entry["status"], "solved")
        self.assertEqual(entry["submits"][0]["id"], out["submit_id"])

    def test_wrong_submit_does_not_solve(self):
        out = self.submit("contains-duplicate", DUP_WRONG)
        self.assertIs(out["solved"], False)
        self.assertIs(out["first_try"], False)
        self.assertLess(out["passed"], out["total"])
        self.assertEqual(out["matrix"]["row"], "A1")
        self.assertIn(out["matrix"]["now"], (0, 1))
        self.assertEqual(self.app.store.problem("contains-duplicate")["status"], "attempted")
        second = self.submit("contains-duplicate", DUP_RIGHT)
        self.assertIs(second["solved"], True)
        self.assertIs(second["first_try"], False)

    def test_submit_never_lowers_a_hand_set_level(self):
        self.set_matrix_cell("A1", "3")
        out = self.submit("contains-duplicate", DUP_WRONG)
        self.assertIs(out["matrix"]["written"], False)
        self.assertEqual(self.matrix_cell("A1", "now"), "3")
        self.assertIn("Contains Duplicate", self.matrix_cell("A1", "evidence"))
        self.assertIsNone(self.app.store.matrix_written("A1"))

    def test_submit_may_lower_what_the_app_wrote(self):
        self.submit("two-sum", TWO_SUM)  # writes 2
        self.clock.advance(minutes=1)
        out = self.submit("contains-duplicate", DUP_WRONG)
        self.assertTrue(out["matrix"]["written"])
        self.assertEqual(self.matrix_cell("A1", "now"), str(out["matrix"]["now"]))
        self.assertEqual(self.matrix_cell("A1", "start"), "2")

    def test_submit_for_a_row_the_app_does_not_write(self):
        os.remove(os.path.join(self.kit.my_prep, "skills-matrix.md"))
        out = self.submit("two-sum", TWO_SUM)
        self.assertIsNone(out["matrix"])
        self.assertIs(out["solved"], True)

    def test_reset_and_redo(self):
        skeleton = self.call("GET", "/api/problem/two-sum")["skeleton"]
        self.call("PUT", "/api/problem/two-sum/draft", {"code": "x = 1\n", "notes": {}})
        out = self.call("POST", "/api/problem/two-sum/reset", {})
        self.assertEqual((out["code"], out["rev"]), (skeleton, 2))
        self.assertEqual([(r["why"], r["tab"]) for r in out["history"]], [("reset", "solution.py")])
        self.assertEqual(self.call("GET", "/api/problem/two-sum")["code"], skeleton)
        out = self.call("POST", "/api/problem/two-sum/redo", {}, status=409)
        self.assertEqual(out["error"], "not_solved")
        self.submit("two-sum", TWO_SUM, {"pattern": "hash map"})
        self.assertEqual(self.call("POST", "/api/problem/two-sum/redo", {}),
                         {"code": skeleton, "attempt": 2, "rev": 4})
        detail = self.call("GET", "/api/problem/two-sum")
        self.assertEqual(detail["code"], skeleton)
        self.assertEqual(detail["attempt"], 2)
        self.assertEqual(detail["status"], "solved")
        self.assertEqual(detail["notes"]["pattern"], "")
        self.assertEqual(read(os.path.join(self.kit.solutions_dir, "two-sum.prev.py")), TWO_SUM)

    def test_reset_keeps_the_changed_code_as_prev(self):
        self.call("PUT", "/api/problem/two-sum/draft", {"code": "x = 1\n", "notes": {}})
        self.call("POST", "/api/problem/two-sum/reset", {})
        self.assertEqual(read(os.path.join(self.kit.solutions_dir, "two-sum.prev.py")), "x = 1\n")

    def test_a_failed_submit_write_leaves_the_state_as_it_was(self):
        with mock.patch("app.prep.store.os.replace", side_effect=OSError(28, "No space left on device")):
            out = self.call("POST", "/api/problem/two-sum/submit",
                            {"code": "x = 1\n", "elapsed": 30}, status=500)
        self.assertEqual(out["error"], "write_failed")
        self.assertNotIn("two-sum", self.app.store.snapshot()["problems"])
        self.assertEqual(self.app.store.rev("two-sum"), 0)

    def test_a_failed_draft_write_is_500_write_failed_naming_the_file(self):
        with mock.patch("app.prep.store.os.replace", side_effect=OSError(28, "No space left on device")):
            out = self.call("PUT", "/api/problem/two-sum/draft", {"code": "x = 1\n"}, status=500)
        self.assertEqual(out["error"], "write_failed")
        self.assertIn("my-prep/solutions/two-sum.py", out["detail"])
        self.assertNotIn(self.kit.root, out["detail"])
        self.assertIn("No space left", out["detail"])

    def test_a_read_only_solutions_folder_is_write_failed_not_internal(self):
        os.makedirs(self.kit.solutions_dir)
        os.chmod(self.kit.solutions_dir, 0o500)
        self.addCleanup(os.chmod, self.kit.solutions_dir, 0o700)
        if os.access(self.kit.solutions_dir, os.W_OK):
            self.skipTest("the folder stays writable for this user")
        out = self.call("POST", "/api/problem/two-sum/run", {"code": "x = 1\n"}, status=500)
        self.assertEqual(out["error"], "write_failed")

    def test_heartbeat(self):
        self.assertEqual(self.call("POST", "/api/heartbeat", {"slug": "two-sum", "seconds": 30}),
                         {"ok": True})
        self.call("POST", "/api/heartbeat", {"slug": "two-sum", "seconds": 1000})
        self.call("POST", "/api/heartbeat", {"slug": None, "seconds": 10})
        self.call("POST", "/api/heartbeat", {"slug": None, "seconds": -5})
        self.assertEqual(self.app.store.problem("two-sum")["seconds"], 90)
        self.assertEqual(self.call("GET", "/api/overview")["kpis"]["seconds"], 100)
        self.call("POST", "/api/heartbeat", {"slug": None, "seconds": "ten"}, status=400)
        self.call("POST", "/api/heartbeat", {"slug": None, "seconds": True}, status=400)
        self.call("POST", "/api/heartbeat", {"slug": "no-such-problem", "seconds": 5}, status=404)


    def test_a_short_heartbeat_counts_its_seconds(self):
        self.call("POST", "/api/heartbeat", {"slug": "two-sum", "seconds": 1})
        self.call("POST", "/api/heartbeat", {"slug": "two-sum", "seconds": 7})
        self.assertEqual(self.app.store.problem("two-sum")["seconds"], 8)

    def test_submit_adds_elapsed_before_it_records(self):
        out = self.call("POST", "/api/problem/two-sum/submit", {"code": TWO_SUM, "elapsed": 45})
        self.assertEqual(self.app.store.problem("two-sum")["seconds"], 45)
        self.assertEqual(self.app.store.submit("two-sum", out["submit_id"])["seconds"], 45)
        self.assertEqual(self.call("GET", "/api/overview")["kpis"]["seconds"], 45)
        self.assertIn("in under 1 min", self.matrix_cell("A1", "evidence"))
        for _ in range(3):
            self.call("POST", "/api/heartbeat", {"slug": "two-sum", "seconds": 60})
        self.call("POST", "/api/problem/two-sum/submit", {"code": TWO_SUM, "elapsed": 1000})
        self.assertEqual(self.app.store.problem("two-sum")["seconds"], 45 + 180 + 60)
        self.assertIn("after 2 submits, in 4 min, no hints (app)", self.matrix_cell("A1", "evidence"))
        self.call("POST", "/api/problem/two-sum/submit", {"code": TWO_SUM, "elapsed": 0})
        for bad_elapsed in ("5", True, -1.5, [3]):
            self.call("POST", "/api/problem/two-sum/submit",
                      {"code": TWO_SUM, "elapsed": bad_elapsed}, status=400)
        self.assertEqual(len(self.app.store.problem("two-sum")["submits"]), 3)

    def test_review_in_progress_is_marked_on_its_submit(self):
        first = self.submit("two-sum", TWO_SUM)["submit_id"]
        second = self.submit("two-sum", TWO_SUM)["submit_id"]
        self.app.reviewing.add(("two-sum", second))
        marks = {s["id"]: s["review_in_progress"]
                 for s in self.call("GET", "/api/problem/two-sum")["submits"]}
        self.assertEqual(marks, {first: False, second: True})
        self.app.reviewing.clear()
        marks = [s["review_in_progress"] for s in self.call("GET", "/api/problem/two-sum")["submits"]]
        self.assertEqual(marks, [False, False])
        self.assertNotIn("review_in_progress", self.app.store.problem("two-sum")["submits"][0])


class TabRouteTests(ApiCase):
    """Editor tabs and the history of a problem's code."""

    def detail(self):
        return self.call("GET", "/api/problem/two-sum")

    def add(self, **body):
        return self.call("POST", "/api/problem/two-sum/tab", body)

    def test_a_problem_starts_with_the_main_tab_and_no_history(self):
        detail = self.detail()
        self.assertEqual(detail["tabs"], [{"id": 1, "name": "solution.py", "code": detail["skeleton"]}])
        self.assertEqual(detail["history"], [])
        self.assertEqual(detail["code"], detail["skeleton"])

    def test_a_new_tab_starts_from_the_skeleton_and_saves_on_its_own(self):
        skeleton = self.detail()["skeleton"]
        out = self.add()
        self.assertEqual(out["tab"], {"id": 2, "name": "solution-2.py", "code": skeleton})
        self.assertEqual(out["rev"], self.app.store.rev("two-sum"))
        self.call("PUT", "/api/problem/two-sum/draft",
                  {"codes": {"1": "a = 1\n", "2": "b = 2\n"}, "notes": {}})
        detail = self.detail()
        self.assertEqual([(t["id"], t["code"]) for t in detail["tabs"]], [(1, "a = 1\n"), (2, "b = 2\n")])
        self.assertEqual(detail["code"], "a = 1\n")
        self.assertEqual(read(os.path.join(self.kit.solutions_dir, "two-sum.py")), "a = 1\n")
        self.assertEqual(read(os.path.join(self.kit.solutions_dir, "two-sum.2.py")), "b = 2\n")

    def test_an_unchanged_draft_of_every_tab_does_not_move_the_rev(self):
        self.add()
        self.call("PUT", "/api/problem/two-sum/draft", {"codes": {"1": "a = 1\n", "2": "b = 2\n"}})
        rev = self.app.store.rev("two-sum")
        out = self.call("PUT", "/api/problem/two-sum/draft", {"codes": {"1": "a = 1\n", "2": "b = 2\n"}})
        self.assertEqual(out["rev"], rev)

    def test_a_draft_for_a_tab_that_is_not_there_writes_nothing(self):
        out = self.call("PUT", "/api/problem/two-sum/draft",
                        {"codes": {"1": "a = 1\n", "7": "b = 2\n"}}, status=400)
        self.assertEqual(out["error"], "bad_tab")
        self.assertIsNone(self.app.store.code("two-sum"))
        for codes in ([], {"x": "a"}, {"0": "a"}, {"1": 3}, {"-1": "a"}, {"1.5": "a"}):
            self.call("PUT", "/api/problem/two-sum/draft", {"codes": codes}, status=400)
        self.call("PUT", "/api/problem/two-sum/draft",
                  {"codes": {"1": "x" * (api.MAX_CODE + 1)}}, status=413)

    def test_a_tab_can_be_named_and_renamed(self):
        self.assertEqual(self.add(name="  brute force \n")["tab"]["name"], "brute force")
        out = self.call("POST", "/api/problem/two-sum/tab/rename", {"tab": 2, "name": "one pass"})
        self.assertEqual(out["tab"], {"id": 2, "name": "one pass"})
        self.assertEqual([t["name"] for t in self.detail()["tabs"]], ["solution.py", "one pass"])
        self.call("POST", "/api/problem/two-sum/tab/rename", {"tab": 2, "name": "  "}, status=400)
        self.call("POST", "/api/problem/two-sum/tab/rename", {"tab": 2}, status=400)
        for tab in (9, "2", True, 2.0, -1):
            out = self.call("POST", "/api/problem/two-sum/tab/rename", {"tab": tab, "name": "x"},
                            status=400)
            self.assertEqual(out["error"], "bad_tab")
        self.call("POST", "/api/problem/two-sum/tab", {"name": 3}, status=400)

    def test_closing_a_tab_keeps_its_code_in_the_history(self):
        self.add()
        self.call("PUT", "/api/problem/two-sum/draft", {"codes": {"2": "b = 2\n"}})
        out = self.call("POST", "/api/problem/two-sum/tab/close", {"tab": 2})
        self.assertTrue(out["ok"])
        self.assertEqual([(r["why"], r["tab"]) for r in out["history"]], [("closed", "solution-2.py")])
        self.assertEqual([t["id"] for t in self.detail()["tabs"]], [1])
        self.assertFalse(os.path.exists(os.path.join(self.kit.solutions_dir, "two-sum.2.py")))
        hid = out["history"][0]["id"]
        self.assertEqual(self.call("GET", "/api/problem/two-sum/history/%d" % hid),
                         {"id": hid, "code": "b = 2\n"})
        self.assertEqual(self.call("POST", "/api/problem/two-sum/tab/close", {"tab": 1},
                                   status=400)["error"], "bad_tab")
        self.assertEqual(self.call("POST", "/api/problem/two-sum/tab/close", {"tab": 2},
                                   status=400)["error"], "bad_tab")

    def test_a_history_entry_that_is_not_there_is_404(self):
        self.call("GET", "/api/problem/two-sum/history/1", status=404)
        self.call("GET", "/api/problem/two-sum/history/0", status=404)
        self.call("GET", "/api/problem/no-such-problem/history/1", status=404)
        self.call("POST", "/api/problem/two-sum/tab", {"from_history": 4}, status=404)
        self.call("POST", "/api/problem/two-sum/tab", {"from_history": "1"}, status=400)
        self.assertEqual([t["id"] for t in self.detail()["tabs"]], [1])

    def test_an_earlier_version_opens_in_a_new_tab(self):
        self.call("PUT", "/api/problem/two-sum/draft", {"code": "old = 1\n"})
        history = self.call("POST", "/api/problem/two-sum/reset", {})["history"]
        out = self.add(from_history=history[0]["id"], name="earlier")
        self.assertEqual(out["tab"], {"id": 2, "name": "earlier", "code": "old = 1\n"})
        self.assertEqual(self.detail()["tabs"][1]["code"], "old = 1\n")
        # the copy left by a reset before there was a history opens the same way
        self.assertEqual(self.call("GET", "/api/problem/two-sum/history/%d" % history[0]["id"])["code"],
                         "old = 1\n")

    def test_there_is_a_limit_to_the_tabs(self):
        from app.prep import store
        for _ in range(store.MAX_TABS - 1):
            self.add()
        out = self.call("POST", "/api/problem/two-sum/tab", {}, status=409)
        self.assertEqual(out["error"], "tab_limit")
        self.assertEqual(len(self.detail()["tabs"]), store.MAX_TABS)

    def test_a_stale_page_cannot_change_the_tabs(self):
        self.add()
        rev = self.app.store.rev("two-sum")
        self.call("PUT", "/api/problem/two-sum/draft", {"code": "a = 1\n"})
        for path, body in (("/tab", {}), ("/tab/rename", {"tab": 2, "name": "x"}),
                           ("/tab/close", {"tab": 2})):
            resp = self.raw("POST", "/api/problem/two-sum" + path, dict(body, base_rev=rev))
            self.assertEqual(resp.status, 409, path)
            self.assertEqual(json.loads(resp.body.decode("utf-8"))["error"], "stale")
        self.assertEqual([t["name"] for t in self.detail()["tabs"]], ["solution.py", "solution-2.py"])

    def test_a_submit_from_a_tab_is_kept_with_its_result(self):
        self.add(name="one pass")
        out = self.call("POST", "/api/problem/two-sum/submit", {"code": TWO_SUM, "tab": 2})
        self.assertTrue(out["solved"])
        record = out["history"][-1]
        self.assertEqual((record["why"], record["tab"], record["ok"], record["submit_id"]),
                         ("submit", "one pass", True, out["submit_id"]))
        self.assertEqual(self.call("GET", "/api/problem/two-sum/history/%d" % record["id"])["code"], TWO_SUM)
        self.assertEqual(read(os.path.join(self.kit.solutions_dir, "two-sum.2.py")), TWO_SUM)
        self.assertIsNone(self.app.store.code("two-sum"))  # the main tab was not touched
        self.assertEqual(self.detail()["history"], out["history"])
        bad = self.call("POST", "/api/problem/two-sum/submit", {"code": TWO_SUM, "tab": 5}, status=400)
        self.assertEqual(bad["error"], "bad_tab")
        self.call("POST", "/api/problem/two-sum/run", {"code": TWO_SUM, "tab": 5}, status=400)

    def test_reset_of_one_tab_leaves_the_others(self):
        skeleton = self.detail()["skeleton"]
        self.add()
        self.call("PUT", "/api/problem/two-sum/draft", {"codes": {"1": "a = 1\n", "2": "b = 2\n"}})
        out = self.call("POST", "/api/problem/two-sum/reset", {"tab": 2})
        self.assertEqual(out["code"], skeleton)
        self.assertEqual([(t["id"], t["code"]) for t in self.detail()["tabs"]],
                         [(1, "a = 1\n"), (2, skeleton)])
        self.assertEqual([(r["why"], r["tab"]) for r in out["history"]], [("reset", "solution-2.py")])

    def test_redo_keeps_every_tab_in_the_history_and_starts_with_one(self):
        self.add()
        self.call("PUT", "/api/problem/two-sum/draft", {"codes": {"2": "b = 2\n"}})
        self.submit("two-sum", TWO_SUM)
        self.call("POST", "/api/problem/two-sum/redo", {})
        detail = self.detail()
        self.assertEqual([t["id"] for t in detail["tabs"]], [1])
        self.assertEqual(detail["code"], detail["skeleton"])
        self.assertEqual(sorted((r["why"], r["tab"]) for r in detail["history"]),
                         [("redo", "solution-2.py"), ("submit", "solution.py")])
        accepted = [r for r in detail["history"] if r["why"] == "submit"][0]
        self.assertEqual(self.call("GET", "/api/problem/two-sum/history/%d" % accepted["id"])["code"], TWO_SUM)

    def test_the_coach_reads_the_tab_it_is_asked_about(self):
        log = os.path.join(self.kit.root, "coach-log.json")
        os.environ["FAKE_COACH_LOG"] = log
        self.add()
        self.call("POST", "/api/problem/two-sum/run",
                  {"code": "class Solution:\n    def twoSum(self, nums, target):\n        return [9, 9]\n"})
        sse(self.raw("POST", "/api/problem/two-sum/coach",
                     {"kind": "review", "tab": 2, "code": "second_tab = True\n"}))
        with open(log, encoding="utf-8") as fh:
            prompt = json.load(fh)["stdin"]
        self.assertIn("second_tab = True", prompt)
        self.assertNotIn("return [9, 9]", prompt)
        self.assertNotIn("[9,9]", prompt)  # the run was of the other tab
        self.assertEqual(self.app.store.code("two-sum", 2), "second_tab = True\n")
        sse(self.raw("POST", "/api/problem/two-sum/coach", {"kind": "review", "tab": 1}))
        with open(log, encoding="utf-8") as fh:
            prompt = json.load(fh)["stdin"]
        self.assertIn("return [9, 9]", prompt)
        self.assertIn("[9,9]", prompt)
        resp = self.raw("POST", "/api/problem/two-sum/coach", {"kind": "review", "tab": 6})
        self.assertEqual(resp.status, 400)

    def test_the_final_review_is_of_the_code_that_was_submitted(self):
        log = os.path.join(self.kit.root, "coach-log.json")
        os.environ["FAKE_COACH_LOG"] = log
        self.add()
        sub = self.call("POST", "/api/problem/two-sum/submit", {"code": TWO_SUM, "tab": 2})
        self.call("PUT", "/api/problem/two-sum/draft",
                  {"codes": {"1": "main_tab = 1\n", "2": "edited_later = 2\n"}})
        self.call("POST", "/api/problem/two-sum/run", {"code": "main_tab = 1\n"})
        self.call("POST", "/api/problem/two-sum/review", {"submit_id": sub["submit_id"]})
        with open(log, encoding="utf-8") as fh:
            prompt = json.load(fh)["stdin"]
        self.assertIn("seen[x] = i", prompt)
        self.assertNotIn("edited_later", prompt)
        self.assertNotIn("main_tab", prompt)


class SaveErrorTests(ApiCase):
    TEXT = "Could not write my-prep/app/state.json: No space left on device."

    def failing(self):
        return mock.patch("app.prep.store.json.dump", side_effect=OSError(28, "No space left on device"))

    def test_writing_routes_carry_the_save_error_until_saving_works(self):
        self.submit("two-sum", TWO_SUM)
        with self.failing():
            out = self.call("POST", "/api/heartbeat", {"slug": "two-sum", "seconds": 5})
            self.assertEqual(out, {"ok": True, "save_error": self.TEXT})
            for method, path, body in (
                    ("PUT", "/api/problem/two-sum/draft", {"code": "x\n"}),
                    ("POST", "/api/problem/two-sum/run", {"code": "x\n"}),
                    ("POST", "/api/problem/two-sum/submit", {"code": TWO_SUM}),
                    ("POST", "/api/problem/two-sum/redo", {}),
                    ("POST", "/api/problem/two-sum/reset", {}),
                    ("POST", "/api/module/01/read", {"read": True}),
                    ("POST", "/api/warmup/another", {})):
                self.assertEqual(self.call(method, path, body)["save_error"], self.TEXT, path)
            err = self.call("PUT", "/api/problem/no-such-problem/draft", {"code": "x"}, status=404)
            self.assertEqual(err["save_error"], self.TEXT)
            overview = self.call("GET", "/api/overview")
            self.assertEqual(overview["notices"], [{"kind": "save_error", "text": self.TEXT}])
            self.assertNotIn("save_error", self.call("GET", "/api/problem/two-sum"))
        self.assertEqual(self.errlog.getvalue().count(self.TEXT), 1)
        out = self.call("POST", "/api/heartbeat", {"slug": "two-sum", "seconds": 5})
        self.assertEqual(out, {"ok": True})
        self.assertEqual(self.call("GET", "/api/overview")["notices"], [])
        self.assertEqual(self.errlog.getvalue().count("Saving progress works again."), 1)
        self.call("POST", "/api/heartbeat", {"slug": "two-sum", "seconds": 5})
        self.assertEqual(self.errlog.getvalue().count("Saving progress works again."), 1)

    def test_a_set_aside_state_is_a_notice_for_the_whole_run(self):
        os.makedirs(os.path.dirname(self.kit.state_file), exist_ok=True)
        with open(self.kit.state_file, "w") as fh:
            fh.write("[]")
        app = api.App(self.kit, PORT, coach_cmd=self.coach_cmd, now=self.clock, log=self.errlog)
        name = os.path.basename(app.store.recovered)
        self.assertTrue(name.startswith("state.json.broken-"), name)
        self.app = app
        text = ("Your saved progress could not be read and was set aside as %s. The app started "
                "with empty progress." % name)
        self.assertEqual(self.call("GET", "/api/overview")["notices"],
                         [{"kind": "state_recovered", "text": text}])
        self.call("POST", "/api/heartbeat", {"slug": None, "seconds": 5})
        self.assertEqual(self.call("GET", "/api/overview")["notices"],
                         [{"kind": "state_recovered", "text": text}])


STALE_DETAIL = "This problem changed in another tab. Reload to see the newer code."


class RevTests(ApiCase):
    def rev(self, slug="two-sum"):
        return self.call("GET", "/api/problem/%s" % slug)["rev"]

    def test_rev_rises_on_every_change_to_code_or_notes(self):
        self.assertEqual(self.rev(), 0)
        skeleton = self.call("GET", "/api/problem/two-sum")["skeleton"]
        self.assertEqual(self.call("PUT", "/api/problem/two-sum/draft", {"code": skeleton}),
                         {"ok": True, "rev": 0})  # nothing changed
        self.assertEqual(self.call("PUT", "/api/problem/two-sum/draft", {"code": "x = 1\n"}),
                         {"ok": True, "rev": 1})
        self.assertEqual(self.call("PUT", "/api/problem/two-sum/draft",
                                   {"notes": {"pattern": "hash map"}})["rev"], 2)
        self.assertEqual(self.call("POST", "/api/problem/two-sum/run", {"code": "x = 1\n"})["rev"], 2)
        self.assertEqual(self.call("POST", "/api/problem/two-sum/run", {"code": "x = 2\n"})["rev"], 3)
        self.assertEqual(self.submit("two-sum", TWO_SUM)["rev"], 4)
        self.assertEqual(self.submit("two-sum", TWO_SUM)["rev"], 4)
        self.assertEqual(self.call("POST", "/api/problem/two-sum/redo", {})["rev"], 5)
        self.call("PUT", "/api/problem/two-sum/draft", {"code": "y = 1\n"})
        self.assertEqual(self.call("POST", "/api/problem/two-sum/reset", {})["rev"], 7)
        self.assertEqual(self.rev(), 7)
        self.assertEqual(self.rev("valid-anagram"), 0)

    def test_a_stale_base_rev_is_409_and_writes_nothing(self):
        self.call("PUT", "/api/problem/two-sum/draft", {"code": "new work\n", "base_rev": 0})
        before = self.app.store.snapshot()
        for method, route, body in (
                ("PUT", "draft", {"code": "old\n", "base_rev": 0}),
                ("PUT", "draft", {"notes": {"pattern": "p"}, "base_rev": 0}),
                ("POST", "run", {"code": "old\n", "base_rev": 0}),
                ("POST", "submit", {"code": TWO_SUM, "base_rev": 0, "elapsed": 20})):
            resp = self.raw(method, "/api/problem/two-sum/%s" % route, body)
            self.assertEqual(resp.status, 409, route)
            self.assertEqual(json.loads(resp.body), {"error": "stale", "detail": STALE_DETAIL,
                                                     "rev": 1})
        self.assertEqual(self.app.store.snapshot(), before)
        self.assertEqual(read(os.path.join(self.kit.solutions_dir, "two-sum.py")), "new work\n")
        self.assertNotIn("two-sum", self.app.last_results)
        # the current rev is accepted, and no base_rev behaves as before
        self.assertEqual(self.call("PUT", "/api/problem/two-sum/draft",
                                   {"code": "newer\n", "base_rev": 1})["rev"], 2)
        self.assertEqual(self.call("PUT", "/api/problem/two-sum/draft", {"code": "x\n"})["rev"], 3)

    def test_base_rev_must_be_a_whole_number(self):
        for bad_rev in ("1", 1.5, True, [1]):
            self.call("PUT", "/api/problem/two-sum/draft", {"code": "x\n", "base_rev": bad_rev},
                      status=400)
        self.assertEqual(self.rev(), 0)

    def test_touched_at_counts_a_notes_only_save_and_a_run(self):
        self.call("PUT", "/api/problem/two-sum/draft", {"code": "x = 1\n"})
        sol = os.path.join(self.kit.solutions_dir, "two-sum.py")
        os.utime(sol, (1767225600, 1767225600))  # an old file write
        self.clock.advance(minutes=7)
        self.call("PUT", "/api/problem/two-sum/draft", {"notes": {"trace": "i=0"}})
        self.assertEqual(self.app.store.problem("two-sum")["touched_at"], "2026-11-12T09:07:00")
        by = {p["slug"]: p for p in self.call("GET", "/api/problems")["problems"]}
        self.assertEqual(by["two-sum"]["last_at"], "2026-11-12T09:07:00")
        self.clock.advance(minutes=3)
        self.call("POST", "/api/problem/two-sum/run", {"code": "x = 1\n"})
        self.assertEqual(self.app.store.problem("two-sum")["touched_at"], "2026-11-12T09:10:00")


class ReviewTests(ApiCase):
    def test_review_writes_one_learning(self):
        sub = self.submit("two-sum", TWO_SUM)
        out = self.call("POST", "/api/problem/two-sum/review", {"submit_id": sub["submit_id"]})
        self.assertEqual(set(out["review"]), {"verdict", "good", "wrong", "edge_cases",
                                              "next_step", "mistakes"})
        self.assertEqual(out["saved"], {"learnings": 1, "bugs": 0, "skipped": []})
        text = read(os.path.join(self.kit.my_prep, "learnings.md"))
        self.assertEqual(text.count("off by one on the last index"), 2)  # heading and what happened
        self.assertIn("### 2026-11-12 — off by one on the last index", text)
        self.assertIn("**The rule:** trace the last element by hand", text)
        self.assertIn("https://leetcode.com/problems/two-sum/", text)
        self.assertTrue(self.app.store.submit("two-sum", sub["submit_id"])["reviewed"])
        again = self.call("POST", "/api/problem/two-sum/review", {"submit_id": sub["submit_id"]},
                          status=409)
        self.assertEqual(again["error"], "already_reviewed")
        self.assertEqual(read(os.path.join(self.kit.my_prep, "learnings.md")), text)

    def test_repeat_mistakes_also_go_to_the_bug_log(self):
        os.environ["FAKE_COACH_MODE"] = "json"
        os.environ["FAKE_COACH_REVIEW"] = json.dumps({
            "verdict": "needs_work", "good": [], "wrong": ["slow"], "edge_cases": [],
            "next_step": "x", "mistakes": [{"bug": "mutating while iterating",
                                           "check": "copy first", "repeat": True}]})
        sub = self.submit("contains-duplicate", DUP_WRONG)
        out = self.call("POST", "/api/problem/contains-duplicate/review",
                        {"submit_id": sub["submit_id"]})
        self.assertEqual(out["saved"], {"learnings": 1, "bugs": 1, "skipped": []})
        bugs = read(os.path.join(self.kit.my_prep, "bugs.md"))
        self.assertIn("| mutating while iterating | copy first | Contains Duplicate, 2026-11-12 |", bugs)

    def test_skipped_writes_are_reported(self):
        os.remove(os.path.join(self.kit.my_prep, "learnings.md"))
        sub = self.submit("two-sum", TWO_SUM)
        out = self.call("POST", "/api/problem/two-sum/review", {"submit_id": sub["submit_id"]})
        self.assertEqual(out["saved"]["learnings"], 0)
        self.assertEqual(len(out["saved"]["skipped"]), 1)
        self.assertIn("learnings.md", out["saved"]["skipped"][0])

    def test_a_bug_log_with_other_columns_is_skipped_with_a_reason(self):
        os.environ["FAKE_COACH_MODE"] = "json"
        os.environ["FAKE_COACH_REVIEW"] = json.dumps({
            "verdict": "needs_work", "good": [], "wrong": ["slow"], "edge_cases": [],
            "next_step": "x", "mistakes": [{"bug": "mutating while iterating",
                                           "check": "copy first", "repeat": True}]})
        path = os.path.join(self.kit.my_prep, "bugs.md")
        text = "# Bugs\n\n## Log\n\n| When | What |\n|---|---|\n| today | thing |\n"
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        sub = self.submit("contains-duplicate", DUP_WRONG)
        out = self.call("POST", "/api/problem/contains-duplicate/review",
                        {"submit_id": sub["submit_id"]})
        self.assertEqual(out["saved"]["bugs"], 0)
        self.assertEqual(out["saved"]["learnings"], 1)
        self.assertEqual(len(out["saved"]["skipped"]), 1)
        self.assertIn("bugs.md", out["saved"]["skipped"][0])
        self.assertIn("columns", out["saved"]["skipped"][0])
        self.assertEqual(read(path), text)

    def test_review_unknown_submit(self):
        self.submit("two-sum", TWO_SUM)
        self.call("POST", "/api/problem/two-sum/review", {"submit_id": "nope"}, status=404)
        self.call("POST", "/api/problem/two-sum/review", {}, status=400)
        sub = self.submit("contains-duplicate", DUP_WRONG)
        self.call("POST", "/api/problem/two-sum/review", {"submit_id": sub["submit_id"]}, status=404)

    def test_coach_failure_leaves_the_submit_unreviewed(self):
        os.environ["FAKE_COACH_MODE"] = "fail"
        sub = self.submit("two-sum", TWO_SUM)
        out = self.call("POST", "/api/problem/two-sum/review", {"submit_id": sub["submit_id"]},
                        status=502)
        self.assertEqual(out["error"], "failed")
        self.assertFalse(self.app.store.submit("two-sum", sub["submit_id"])["reviewed"])


class MissingCoachTests(ApiCase):
    coach_cmd = ["/nonexistent/claude-for-prep-tests"]

    def test_review_without_claude(self):
        sub = self.submit("two-sum", TWO_SUM)
        self.assertIs(sub["solved"], True)
        out = self.call("POST", "/api/problem/two-sum/review", {"submit_id": sub["submit_id"]},
                        status=503)
        self.assertEqual(out["error"], "claude_not_found")
        record = self.app.store.submit("two-sum", sub["submit_id"])
        self.assertFalse(record["reviewed"])
        self.assertTrue(record["ok"])
        self.assertEqual(self.app.store.problem("two-sum")["status"], "solved")
        self.assertIs(self.call("GET", "/api/setup/status")["claude"], False)
        self.assertIs(self.call("GET", "/api/overview")["setup"]["claude"], False)

    def test_nothing_chosen_and_nothing_found_means_no_coach(self):
        out = self.call("GET", "/api/setup/coach")
        self.assertIsNone(out["choice"])
        self.assertIsNone(out["active"])
        self.assertEqual([p["found"] for p in out["providers"]], [False, False])
        self.call("POST", "/api/setup/coach", {"provider": "claude"}, status=409)
        self.assertFalse(os.path.exists(self.kit.settings_file))

    def test_coach_stream_without_claude(self):
        resp = self.raw("POST", "/api/problem/two-sum/coach", {"kind": "hint", "message": "",
                                                               "code": None, "notes": None})
        events = sse(resp)
        self.assertEqual(events[-1]["error"], "claude_not_found")
        chat = self.app.store.problem("two-sum")["chat"]
        self.assertEqual(chat, [])
        self.assertEqual(self.app.store.problem("two-sum")["hints_used"], 0)


def sse(resp):
    events = []
    for chunk in resp.stream:
        for line in chunk.decode("utf-8").split("\n"):
            if line.startswith("data: "):
                events.append(json.loads(line[6:]))
    return events


class CoachRouteTests(ApiCase):
    def test_hint_streams_and_is_stored(self):
        resp = self.raw("POST", "/api/problem/two-sum/coach",
                        {"kind": "hint", "message": "", "code": TWO_SUM, "notes": {"pattern": "map"}})
        self.assertEqual(resp.status, 200)
        self.assertEqual(resp.headers["Content-Type"], "text/event-stream; charset=utf-8")
        self.assertIsNone(resp.body)
        events = sse(resp)
        self.assertEqual(events[-1], {"done": True, "text": "First point.\n2. Second point."})
        self.assertEqual(len([e for e in events if "delta" in e]), 3)
        entry = self.app.store.problem("two-sum")
        self.assertEqual([(c["role"], c["kind"], c["text"]) for c in entry["chat"]],
                         [("user", "hint", "Give me a hint"),
                          ("coach", "hint", "First point.\n2. Second point.")])
        self.assertEqual(entry["hints_used"], 1)
        self.assertEqual(entry["notes"]["pattern"], "map")
        self.assertEqual(self.app.store.code("two-sum"), TWO_SUM)

    def test_question_stores_the_typed_message(self):
        sse(self.raw("POST", "/api/problem/two-sum/coach",
                     {"kind": "question", "message": "Why a map?", "code": None, "notes": None}))
        entry = self.app.store.problem("two-sum")
        self.assertEqual(entry["chat"][0]["text"], "Why a map?")
        self.assertEqual(entry["hints_used"], 0)
        self.call("POST", "/api/problem/two-sum/coach",
                  {"kind": "question", "message": "  ", "code": None, "notes": None}, status=400)
        self.call("POST", "/api/problem/two-sum/coach", {"kind": "poem"}, status=400)

    def test_failed_reply_is_not_stored(self):
        os.environ["FAKE_COACH_MODE"] = "fail"
        events = sse(self.raw("POST", "/api/problem/two-sum/coach", {"kind": "hint"}))
        self.assertEqual(events[-1]["error"], "failed")
        entry = self.app.store.problem("two-sum")
        self.assertEqual(entry["chat"], [])
        self.assertEqual(entry["hints_used"], 0)

    def test_disconnect_stores_nothing_for_the_reply(self):
        os.environ["FAKE_COACH_MODE"] = "hang"
        self.app.coach_idle = 0.1
        resp = self.raw("POST", "/api/problem/two-sum/coach", {"kind": "hint"})
        started = time.monotonic()
        first = next(iter(resp.stream))
        self.assertTrue(first.startswith(b":"))
        resp.stream.close()
        self.assertLess(time.monotonic() - started, 5)
        entry = self.app.store.problem("two-sum")
        self.assertEqual(entry["chat"], [])
        self.assertEqual(entry["hints_used"], 0)

    def test_prompt_carries_the_last_run(self):
        log = os.path.join(self.kit.root, "coach-log.json")
        os.environ["FAKE_COACH_LOG"] = log
        self.call("POST", "/api/problem/two-sum/run",
                  {"code": "class Solution:\n    def twoSum(self, nums, target):\n        return [9, 9]\n"})
        sse(self.raw("POST", "/api/problem/two-sum/coach", {"kind": "review"}))
        with open(log, encoding="utf-8") as fh:
            prompt = json.load(fh)["stdin"]
        self.assertIn("return [9, 9]", prompt)
        self.assertIn("nums = [2,7,11,15], target = 9", prompt)
        self.assertIn("[9,9]", prompt)


    def test_idle_events_become_pings(self):
        os.environ["FAKE_COACH_MODE"] = "hang"
        self.app.coach_idle = 0.1
        resp = self.raw("POST", "/api/problem/two-sum/coach", {"kind": "hint"})
        stream = iter(resp.stream)
        self.assertEqual(next(stream), b": open\n\n")
        self.assertEqual(next(stream), b": ping\n\n")
        resp.stream.close()

    def test_one_coach_call_at_a_time(self):
        os.environ["FAKE_COACH_MODE"] = "hang"
        self.app.coach_idle = 0.1
        first = self.raw("POST", "/api/problem/two-sum/coach", {"kind": "hint"})
        next(iter(first.stream))
        out = self.call("POST", "/api/problem/contains-duplicate/coach", {"kind": "hint"},
                        status=409)
        self.assertEqual(out["error"], "busy")
        sub = self.submit("two-sum", TWO_SUM)
        out = self.call("POST", "/api/problem/two-sum/review", {"submit_id": sub["submit_id"]},
                        status=409)
        self.assertEqual(out["error"], "busy")
        first.stream.close()
        os.environ["FAKE_COACH_MODE"] = "auto"
        self.assertTrue(sse(self.raw("POST", "/api/problem/two-sum/coach",
                                     {"kind": "hint"}))[-1]["done"])

    def test_a_stream_never_started_frees_the_slot(self):
        resp = self.raw("POST", "/api/problem/two-sum/coach", {"kind": "hint"})
        resp.stream.close()
        self.assertTrue(sse(self.raw("POST", "/api/problem/two-sum/coach",
                                     {"kind": "hint"}))[-1]["done"])

    def test_an_error_inside_the_stream_is_an_event(self):
        with mock.patch.object(self.app.store, "add_chat", side_effect=OSError(28, "No space left")):
            events = sse(self.raw("POST", "/api/problem/two-sum/coach", {"kind": "hint"}))
        self.assertEqual(events[-1]["error"], "internal")
        self.assertIn("No space left", events[-1]["detail"])
        self.assertIn("Traceback", self.errlog.getvalue())
        self.assertTrue(sse(self.raw("POST", "/api/problem/two-sum/coach",
                                     {"kind": "hint"}))[-1]["done"])

    def test_other_start_errors_are_failed(self):
        sub = self.submit("two-sum", TWO_SUM)
        with mock.patch("subprocess.Popen", side_effect=OSError(7, "Argument list too long")):
            events = sse(self.raw("POST", "/api/problem/two-sum/coach", {"kind": "hint"}))
            out = self.call("POST", "/api/problem/two-sum/review",
                            {"submit_id": sub["submit_id"]}, status=502)
        self.assertEqual(events[-1]["error"], "failed")
        self.assertEqual(out["error"], "failed")


class ConcurrentReviewTests(ApiCase):
    def test_a_second_review_of_the_same_submit_while_one_runs(self):
        sub = self.submit("two-sum", TWO_SUM)
        entered, release = threading.Event(), threading.Event()
        real = api.coach.final_review

        def slow_review(context, cmd=None, provider="claude"):
            entered.set()
            release.wait(5)
            return real(context, cmd=cmd, provider=provider)

        results = []
        with mock.patch.object(api.coach, "final_review", side_effect=slow_review):
            worker = threading.Thread(target=lambda: results.append(self.raw(
                "POST", "/api/problem/two-sum/review", {"submit_id": sub["submit_id"]})))
            worker.start()
            self.assertTrue(entered.wait(5))
            out = self.call("POST", "/api/problem/two-sum/review",
                            {"submit_id": sub["submit_id"]}, status=409)
            self.assertEqual(out["error"], "already_reviewed")
            release.set()
            worker.join(10)
        self.assertEqual(results[0].status, 200)
        self.call("POST", "/api/problem/two-sum/review", {"submit_id": sub["submit_id"]},
                  status=409)


class CourseTests(ApiCase):
    def test_course_listing_and_module_read(self):
        out = self.call("GET", "/api/course")
        self.assertEqual(set(out), {"modules", "reference", "notes"})
        first = out["modules"][0]
        self.assertEqual(set(first), {"id", "title", "path", "solved", "total", "read"})
        self.assertEqual(first["id"], "00")
        self.assertIs(first["read"], False)
        self.assertEqual(self.call("POST", "/api/module/03/read", {"read": True}), {"ok": True})
        mods = {m["id"]: m for m in self.call("GET", "/api/course")["modules"]}
        self.assertIs(mods["03"]["read"], True)
        self.assertEqual(mods["03"]["total"], 11)
        self.assertTrue(out["reference"])
        self.assertEqual(set(out["notes"][0]), {"key", "title", "path", "exists", "is_template"})
        self.assertTrue(out["notes"][0]["exists"])
        self.call("POST", "/api/module/99/read", {"read": True}, status=404)
        self.call("POST", "/api/module/03/read", {"read": "yes"}, status=400)

    def test_a_doc_over_two_megabytes_is_413_too_large(self):
        with open(os.path.join(self.kit.my_prep, "big.md"), "wb") as fh:
            fh.write(b"x" * (2 * 1024 * 1024 + 1))
        out = self.call("GET", "/api/doc", query={"path": "my-prep/big.md"}, status=413)
        self.assertEqual(out["error"], "too_large")

    def test_course_notes_carry_is_template(self):
        notes_list = self.call("GET", "/api/course")["notes"]
        self.assertTrue(all(n["is_template"] is True for n in notes_list))
        with open(os.path.join(self.kit.my_prep, "plan.md"), "a", encoding="utf-8") as fh:
            fh.write("mine\n")
        by = {n["key"]: n for n in self.call("GET", "/api/course")["notes"]}
        self.assertIs(by["plan"]["is_template"], False)
        self.assertIs(by["bugs"]["is_template"], True)

    def test_doc(self):
        out = self.call("GET", "/api/doc", query={"path": "course/modules/01-arrays-hashing.md"})
        self.assertEqual(set(out), {"path", "title", "markdown"})
        self.assertTrue(out["markdown"].startswith("# "))
        self.call("GET", "/api/doc", query={"path": "my-prep/skills-matrix.md"})
        self.call("GET", "/api/doc", query={"path": "course/modules/nope.md"}, status=404)
        for bad in ("course/../app/server.py", "../etc/passwd", "/etc/passwd", "app/data/problems.json",
                    "course/modules/..%2f..%2fapp.md", "my-prep/app/state.json",
                    "course/a..b/../x.md", "course\\x.md", ""):
            self.call("GET", "/api/doc", query={"path": bad}, status=403)
        self.call("GET", "/api/doc", status=403)

    def test_matrix(self):
        out = self.call("GET", "/api/matrix")
        rows = [r for g in out["groups"] for r in g["rows"]]
        self.assertEqual(set(rows[0]), {"id", "requirement", "module", "priority", "start", "now",
                                        "evidence", "last_tested", "practise"})
        by = {r["id"]: r for r in rows}
        self.assertEqual(by["A1"]["practise"], "contains-duplicate")
        self.assertIsNone(by["A3"]["practise"])
        self.assertTrue(out["groups"][0]["title"])


class CoachChoiceTests(ApiCase):
    codex_cmd = FAKE_CMD

    def hint(self):
        return sse(self.raw("POST", "/api/problem/two-sum/coach",
                            {"kind": "hint", "message": "", "code": TWO_SUM, "notes": None}))

    def logged(self):
        with open(os.environ["FAKE_COACH_LOG"], encoding="utf-8") as fh:
            return json.load(fh)

    def test_default_is_claude_until_a_choice_is_made(self):
        out = self.call("GET", "/api/setup/coach")
        self.assertIsNone(out["choice"])
        self.assertEqual(out["active"], "claude")
        self.assertEqual([(p["key"], p["found"]) for p in out["providers"]],
                         [("claude", True), ("codex", True)])
        self.assertFalse(os.path.exists(self.kit.settings_file))

    def test_choosing_codex_routes_hints_and_reviews_through_it(self):
        os.environ["FAKE_COACH_LOG"] = os.path.join(self.kit.root, "coach-log.json")
        out = self.call("POST", "/api/setup/coach", {"provider": "codex"})
        self.assertEqual((out["choice"], out["active"]), ("codex", "codex"))
        self.assertEqual(json.loads(read(self.kit.settings_file)), {"coach": "codex"})
        events = self.hint()
        self.assertEqual(events[-1], {"done": True, "text": "First point.\n2. Second point."})
        self.assertEqual(self.logged()["argv"][0], "exec")
        sub = self.submit("two-sum", TWO_SUM)
        review = self.call("POST", "/api/problem/two-sum/review", {"submit_id": sub["submit_id"]})
        self.assertEqual(review["review"]["verdict"], "pass")
        self.assertIn("--output-schema", self.logged()["argv"])
        # the choice is read from the file, so it holds after a restart
        again = api.App(self.kit, PORT, coach_cmd=self.coach_cmd, now=self.clock, log=self.errlog,
                        codex_cmd=self.codex_cmd)
        self.assertEqual(json.loads(again.handle(
            "GET", "/api/setup/coach", {}, {"Host": "127.0.0.1:%d" % PORT}, b"").body)["active"], "codex")

    def test_choosing_claude_back(self):
        os.environ["FAKE_COACH_LOG"] = os.path.join(self.kit.root, "coach-log.json")
        self.call("POST", "/api/setup/coach", {"provider": "codex"})
        out = self.call("POST", "/api/setup/coach", {"provider": "claude"})
        self.assertEqual((out["choice"], out["active"]), ("claude", "claude"))
        self.hint()
        self.assertIn("-p", self.logged()["argv"])

    def test_no_coach(self):
        out = self.call("POST", "/api/setup/coach", {"provider": "none"})
        self.assertEqual((out["choice"], out["active"]), ("none", None))
        self.assertIs(self.call("GET", "/api/setup/status")["claude"], False)
        setup = self.call("GET", "/api/overview")["setup"]
        self.assertIs(setup["claude"], False)
        self.assertEqual(setup["coach"]["choice"], "none")

    def test_bad_requests_change_nothing(self):
        for body in ({"provider": "gemini"}, {"provider": None}, {}, {"provider": ["codex"]}):
            self.call("POST", "/api/setup/coach", body, status=400)
        self.assertFalse(os.path.exists(self.kit.settings_file))

    def test_a_broken_settings_file_means_no_choice(self):
        os.makedirs(os.path.dirname(self.kit.settings_file), exist_ok=True)
        for text in ("{not json", "[1, 2]", '{"coach": "gemini"}', '{"coach": 3}'):
            with open(self.kit.settings_file, "w", encoding="utf-8") as fh:
                fh.write(text)
            out = self.call("GET", "/api/setup/coach")
            self.assertIsNone(out["choice"], text)
            self.assertEqual(out["active"], "claude", text)
        # and the next choice still saves over it
        self.call("POST", "/api/setup/coach", {"provider": "codex"})
        self.assertEqual(json.loads(read(self.kit.settings_file))["coach"], "codex")

    def test_a_chosen_tool_that_went_missing(self):
        self.call("POST", "/api/setup/coach", {"provider": "codex"})
        self.app.codex_cmd = MISSING_CODEX
        out = self.call("GET", "/api/setup/coach")
        self.assertEqual((out["choice"], out["active"]), ("codex", "codex"))
        self.assertIs(self.call("GET", "/api/setup/status")["claude"], False)
        self.assertEqual(self.hint()[-1]["error"], "claude_not_found")

    def test_choosing_a_tool_that_is_not_there(self):
        self.app.codex_cmd = MISSING_CODEX
        out = self.call("POST", "/api/setup/coach", {"provider": "codex"}, status=409)
        self.assertEqual(out["error"], "coach_not_found")
        self.assertFalse(os.path.exists(self.kit.settings_file))

    def test_the_post_is_guarded_like_every_write(self):
        resp = self.raw("POST", "/api/setup/coach", {"provider": "codex"},
                        headers={"Origin": "http://evil.example"})
        self.assertEqual(resp.status, 403)
        self.assertFalse(os.path.exists(self.kit.settings_file))


class SetupTests(ApiCase):
    def test_status_and_download(self):
        out = self.call("GET", "/api/setup/status")
        self.assertEqual(out, {"statements": {"have": 0, "total": 119, "running": False, "failed": []},
                               "claude": True, "coach": COACH})

        def opener(req, timeout):
            if req.full_url.startswith("https://neetcode.io/"):
                raise OSError("offline")
            return json.dumps({"data": {"question": {"content": "<p>s</p>"}}}).encode()

        self.app.statements_opener = opener
        self.app.statements_sleep = lambda s: None
        self.assertEqual(self.call("POST", "/api/setup/statements", {}), {"started": True})
        deadline = time.monotonic() + 10
        while self.call("GET", "/api/setup/status")["statements"]["running"]:
            self.assertLess(time.monotonic(), deadline)
            time.sleep(0.02)
        st = self.call("GET", "/api/setup/status")["statements"]
        self.assertEqual((st["have"], st["total"]), (114, 119))
        self.assertEqual(len(st["failed"]), 5)
        self.assertIn("walls-and-gates", st["failed"])

    def test_a_download_that_raises_is_reported(self):
        with mock.patch.object(api.statements, "fetch_all", side_effect=RuntimeError("disk gone")):
            self.call("POST", "/api/setup/statements")
            started = time.monotonic()
            while self.app.statements_running and time.monotonic() - started < 5:
                time.sleep(0.01)
        out = self.call("GET", "/api/setup/status")["statements"]
        self.assertFalse(out["running"])
        self.assertIn("disk gone", out["error"])
        self.assertIn("Traceback", self.errlog.getvalue())

    def test_save_error_is_reported(self):
        self.app.store.save_error = "OSError: disk full"
        self.assertEqual(self.call("GET", "/api/setup/status")["save_error"], "OSError: disk full")


class GuardTests(ApiCase):
    def test_host_header(self):
        for host in ("evil.example:8765", "127.0.0.1:9999", "127.0.0.1", "localhost", None,
                     "127.0.0.1:8765.evil.example"):
            out = self.call("GET", "/api/overview", headers={"Host": host}, status=403)
            self.assertEqual(out["error"], "forbidden")
        self.call("GET", "/api/overview", headers={"Host": "localhost:8765"})
        self.call("GET", "/api/overview", headers={"host": "LOCALHOST:8765", "Host": None})

    def test_origin(self):
        for origin in ("http://evil.example", "http://127.0.0.1:9999", "null",
                       "https://127.0.0.1:8765", "http://localhost:8765.evil"):
            self.call("POST", "/api/heartbeat", {"slug": None, "seconds": 5},
                      headers={"Origin": origin}, status=403)
        self.call("POST", "/api/heartbeat", {"slug": None, "seconds": 5},
                  headers={"Origin": "http://localhost:8765"})
        self.call("POST", "/api/heartbeat", {"slug": None, "seconds": 5},
                  headers={"Origin": "http://127.0.0.1:8765"})
        self.assertEqual(self.app.store.snapshot()["days"]["2026-11-12"]["seconds"], 10)

    def test_content_type(self):
        for ctype in (None, "text/plain", "application/x-www-form-urlencoded",
                      "multipart/form-data", "application/jsonp"):
            self.call("POST", "/api/heartbeat", {"slug": None, "seconds": 5},
                      headers={"Content-Type": ctype}, status=403)
        self.call("PUT", "/api/problem/two-sum/draft", {"code": "x"},
                  headers={"Content-Type": "text/plain"}, status=403)
        self.call("POST", "/api/heartbeat", {"slug": None, "seconds": 5},
                  headers={"Content-Type": "application/json; charset=utf-8"})
        self.assertEqual(self.app.store.snapshot()["days"]["2026-11-12"]["seconds"], 5)

    def test_unknown_things(self):
        out = self.call("GET", "/api/problem/no-such-problem", status=404)
        self.assertEqual(out["error"], "not_found")
        self.call("POST", "/api/problem/no-such-problem/run", {"code": "x"}, status=404)
        self.call("GET", "/api/problem/..%2Fstate", status=404)
        self.assertEqual(self.call("GET", "/api/nothing-here", status=404)["error"], "not_found")
        self.call("GET", "/api/problem/two-sum/frobnicate", status=404)
        resp = self.raw("DELETE", "/api/overview")
        self.assertEqual(resp.status, 405)
        self.assertEqual(json.loads(resp.body)["error"], "method_not_allowed")
        self.assertEqual(resp.headers["Allow"], "GET")
        self.call("GET", "/api/problem/two-sum/run", status=405)

    def test_bad_bodies(self):
        for body in (b"{not json", b"[1, 2]", b'"text"', b"\xff\xfe", b""):
            out = self.call("POST", "/api/problem/two-sum/run", body, status=400)
            self.assertEqual(out["error"], "bad_request")
        out = self.call("POST", "/api/problem/two-sum/run", {"code": "x" * 200001}, status=413)
        self.assertEqual(out["error"], "too_large")
        self.call("POST", "/api/problem/two-sum/run", {}, status=400)

    def test_deeply_nested_json_is_a_400(self):
        out = self.call("POST", "/api/heartbeat", b"[" * 100000, status=400)
        self.assertEqual(out["error"], "bad_request")
        self.assertEqual(self.errlog.getvalue(), "")

    def test_unexpected_exception_is_a_500_and_the_app_goes_on(self):
        with mock.patch.object(self.app.store, "snapshot", side_effect=RuntimeError("boom")):
            out = self.call("GET", "/api/overview", status=500)
        self.assertEqual(out, {"error": "internal", "detail": "RuntimeError: boom"})
        self.assertIn("Traceback", self.errlog.getvalue())
        self.assertIn("RuntimeError: boom", self.errlog.getvalue())
        self.call("GET", "/api/overview")

    def test_value_error_from_the_store_is_a_400(self):
        with mock.patch.object(self.app.store, "add_seconds", side_effect=ValueError("bad slug")):
            out = self.call("POST", "/api/heartbeat", {"slug": None, "seconds": 5}, status=400)
        self.assertEqual(out["error"], "bad_request")

    def test_every_response_has_the_safety_headers(self):
        for resp in (self.raw("GET", "/api/overview"), self.raw("GET", "/api/nope"),
                     self.raw("GET", "/api/overview", headers={"Host": "x"})):
            self.assertEqual(resp.headers["X-Content-Type-Options"], "nosniff")
            self.assertEqual(resp.headers["Cache-Control"], "no-store")


class StartupTests(unittest.TestCase):
    def test_bootstrap_and_broken_state(self):
        kit = full_kit(self)
        os.makedirs(os.path.dirname(kit.state_file))
        with open(kit.state_file, "w") as fh:
            fh.write("{broken")
        app = api.App(kit, PORT, coach_cmd=FAKE_CMD)
        self.assertIn("skills-matrix.md", app.created)
        self.assertTrue(os.path.isfile(os.path.join(kit.my_prep, "bugs.md")))
        lines = app.startup_lines()
        self.assertTrue(any("state.json" in line and "broken" in line for line in lines), lines)
        self.assertTrue(any("skills-matrix.md" in line for line in lines), lines)
        for line in lines:
            self.assertNotIn("!", line)
        again = api.App(kit, PORT, coach_cmd=FAKE_CMD)
        self.assertEqual(again.created, [])
        self.assertEqual(again.startup_lines(), [])


if __name__ == "__main__":
    unittest.main()
