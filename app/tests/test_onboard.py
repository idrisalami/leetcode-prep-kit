"""The first steps in the app: discovery chat, the module 00 self-check, the diagnostic."""
from __future__ import annotations

import os
import unittest

from app.prep import notes, onboard, paths
from app.tests.test_api import DUP_RIGHT, DUP_WRONG, ApiCase, read, sse

REAL = paths.default()


class ParserTests(unittest.TestCase):
    def test_self_check_has_eight_questions_with_answers(self):
        items = onboard.self_check(REAL)
        self.assertEqual([it["n"] for it in items], list(range(1, 9)))
        self.assertTrue(all(it["question"] and it["answer"] for it in items))

    def test_diagnostic_has_seven_problems_in_the_kit(self):
        d = onboard.diagnostic(REAL)
        self.assertEqual(len(d["problems"]), 7)
        self.assertEqual(d["problems"][0]["slug"], "contains-duplicate")
        self.assertEqual(d["problems"][0]["rows"], ["A1"])
        self.assertEqual(sum(p["minutes"] for p in d["problems"]), 140)
        self.assertTrue(d["rules"])

    def test_result_line(self):
        self.assertEqual(onboard.result_line({"fatal": {"type": "SyntaxError", "line": 3}}),
                         ("did not run: SyntaxError on line 3", "-"))
        self.assertEqual(onboard.result_line({"passed": 2, "total": 2, "results": []}),
                         ("2/2 passed", "-"))
        line, first = onboard.result_line({"passed": 1, "total": 2, "results": [
            {"status": "pass"}, {"status": "fail", "input": "[1, 1]", "expected": True,
                                 "got": False}]})
        self.assertEqual(line, "1/2 passed")
        self.assertEqual(first, "[1, 1]; expected True, got False")

    def test_bad_answers_are_refused(self):
        self.assertIsNone(onboard.normalise_discovery({"profile": "x"}, REAL))
        self.assertIsNone(onboard.normalise_selfcheck({}, []))
        self.assertIsNone(onboard.normalise_diagnostic([], REAL, []))


class OnboardCase(ApiCase):
    def mine(self, name):
        return os.path.join(self.kit.my_prep, name)

    def steps(self):
        return self.call("GET", "/api/overview")["onboarding"]


class DiscoveryTests(OnboardCase):
    def test_greeting_then_answers_then_finish(self):
        self.assertEqual(self.call("GET", "/api/setup/discovery"),
                         {"messages": [], "done": False, "started": False})
        resp = self.raw("POST", "/api/setup/chat", {"message": ""})
        self.assertEqual(resp.status, 200)
        self.assertEqual(sse(resp)[-1]["done"], True)
        msgs = self.call("GET", "/api/setup/discovery")["messages"]
        self.assertEqual([m["role"] for m in msgs], ["coach"])
        self.call("POST", "/api/setup/chat", {"message": ""}, status=400)
        sse(self.raw("POST", "/api/setup/chat", {"message": "A backend role in a month."}))
        out = self.call("GET", "/api/setup/discovery")
        self.assertEqual([(m["role"], m["text"][:9]) for m in out["messages"]],
                         [("coach", "First poi"), ("user", "A backend"), ("coach", "First poi")])
        self.assertTrue(out["started"])
        self.assertTrue(self.steps()["discovery_started"])

        done = self.call("POST", "/api/setup/discovery/finish", {})
        self.assertIn("profile.md", done["saved"]["written"])
        self.assertEqual(done["saved"]["skipped"], [])
        self.assertTrue(done["onboarding"]["discovery"])
        self.assertIn("said: target", read(self.mine("profile.md")))
        self.assertTrue(notes.profile_started(self.kit))
        plan = read(self.mine("plan.md"))
        self.assertIn("- [x] Discovery", plan)
        self.assertIn("2026-12-15", plan)
        self.assertIn("## Next up: Module 00 self-check", read(self.mine("next-session.md")))
        self.assertEqual([p["id"] for p in done["answer"]["priorities"]], ["C9"])

    def test_finish_needs_an_answer_and_reset_clears(self):
        self.call("POST", "/api/setup/discovery/finish", {}, status=400)
        sse(self.raw("POST", "/api/setup/chat", {"message": ""}))
        self.call("POST", "/api/setup/discovery/finish", {}, status=400)
        self.call("POST", "/api/setup/discovery/reset", {})
        self.assertEqual(self.call("GET", "/api/setup/discovery")["messages"], [])

    def test_a_failing_coach_writes_nothing(self):
        sse(self.raw("POST", "/api/setup/chat", {"message": "hello"}))
        before = read(self.mine("profile.md"))
        os.environ["FAKE_COACH_MODE"] = "fail"
        self.call("POST", "/api/setup/discovery/finish", {}, status=502)
        self.assertEqual(read(self.mine("profile.md")), before)
        self.assertFalse(self.steps()["discovery"])

    def test_busy_coach(self):
        self.app.coach_slot.acquire()
        try:
            self.call("POST", "/api/setup/chat", {"message": "hi"}, status=409)
            self.call("POST", "/api/setup/selfcheck/mark", {"answers": {"1": "x"}}, status=409)
        finally:
            self.app.coach_slot.release()


class SelfCheckTests(OnboardCase):
    def test_answers_hidden_until_marked(self):
        out = self.call("GET", "/api/setup/selfcheck")
        self.assertEqual(len(out["items"]), 8)
        self.assertNotIn("answer", out["items"][0])
        self.assertIsNone(out["result"])
        self.call("PUT", "/api/setup/selfcheck", {"answers": {"1": "quadratic", "99": "x"}})
        self.assertEqual(self.call("GET", "/api/setup/selfcheck")["answers"], {"1": "quadratic"})

    def test_mark_writes_the_score_and_ticks_module_00(self):
        self.call("POST", "/api/setup/selfcheck/mark", {"answers": {"1": " "}}, status=400)
        answers = {str(n): "an answer" for n in range(1, 9)}
        out = self.call("POST", "/api/setup/selfcheck/mark", {"answers": answers})
        self.assertEqual(out["result"]["summary"], {"score": 6, "total": 8, "missed": ["3", "7"]})
        self.assertTrue(out["items"][0]["answer"])
        self.assertTrue(out["onboarding"]["self_check"])
        plan = read(self.mine("plan.md"))
        line = next(l for l in plan.splitlines() if "Module 00" in l)
        self.assertTrue(line.startswith("- [x] Module 00"))
        self.assertTrue(line.endswith("Self-check: `6/8`, missed `3, 7`"), line)
        self.assertIn("## Next up: The diagnostic", read(self.mine("next-session.md")))
        self.assertTrue(self.app.store.module_read("00") if hasattr(self.app.store, "module_read")
                        else True)


class DiagnosticTests(OnboardCase):
    def test_view(self):
        out = self.call("GET", "/api/setup/diagnostic")
        self.assertEqual(len(out["problems"]), 7)
        first = out["problems"][0]
        self.assertEqual(first["slug"], "contains-duplicate")
        self.assertTrue(first["in_kit"])
        self.assertIn("containsDuplicate", first["skeleton"])
        self.assertEqual(first["code"], first["skeleton"])
        self.assertEqual([q["key"] for q in out["overall_questions"]], ["worst", "idea", "aloud"])
        self.assertIsNone(out["review"])
        self.assertFalse(out["done"])

    def test_answers_are_checked(self):
        self.call("PUT", "/api/setup/diagnostic/answer",
                  {"slug": "two-sum", "code": "", "seconds": 0}, status=400)
        self.call("PUT", "/api/setup/diagnostic/answer",
                  {"slug": "contains-duplicate", "code": "", "seconds": -1}, status=400)
        self.call("PUT", "/api/setup/diagnostic/answer",
                  {"slug": "contains-duplicate", "code": "x", "seconds": True}, status=400)
        self.call("POST", "/api/setup/diagnostic/finish", {}, status=400)

    def test_finish_runs_scores_and_plans(self):
        self.call("PUT", "/api/setup/diagnostic/answer",
                  {"slug": "contains-duplicate", "code": DUP_RIGHT, "seconds": 400,
                   "notes": "a set", "finished": True})
        self.call("PUT", "/api/setup/diagnostic/answer",
                  {"slug": "contains-duplicate", "code": DUP_RIGHT, "seconds": 300})
        self.call("PUT", "/api/setup/diagnostic/answer",
                  {"slug": "best-time-to-buy-and-sell-stock", "code": "def broken(:\n",
                   "seconds": 60})
        self.call("PUT", "/api/setup/diagnostic/answer",
                  {"overall": {"worst": "the trie", "idea": "islands", "nope": "x"}})
        view = self.call("GET", "/api/setup/diagnostic")
        self.assertEqual(view["overall"], {"worst": "the trie", "idea": "islands"})
        saved = view["problems"][0]
        self.assertEqual((saved["seconds"], saved["finished"]), (400, True))

        out = self.call("POST", "/api/setup/diagnostic/finish", {})
        review = out["review"]
        self.assertEqual(len(review["problems"]), 7)
        self.assertRegex(review["problems"][0]["result"], r"^(\d+)/\1 passed$")
        self.assertTrue(review["problems"][1]["result"].startswith("did not run"))
        self.assertTrue(out["onboarding"]["diagnostic"] and out["onboarding"]["scored"])
        self.assertEqual(out["saved"]["skipped"], [])

        report = read(self.mine("diagnostic-report.md"))
        self.assertIn("Time used:            7 min / 10 min", report)
        self.assertIn("the trie", report)
        plan = read(self.mine("plan.md"))
        self.assertIn("- [x] Diagnostic", plan)
        self.assertIn("- [x] Scoring and plan", plan)
        self.assertIn("Planned: `2026-11-13` to `2026-11-15`, `6` hours", plan)
        self.assertEqual(self.matrix_cell(review["matrix"][0]["id"], "now"), "1")
        self.assertIn("(diagnostic)", self.matrix_cell(review["matrix"][0]["id"], "evidence"))
        self.assertIn("A1 hashing: slow", read(self.mine("skills-matrix.md")))
        self.assertIn("## Next up: Block 01", read(self.mine("next-session.md")))
        self.call("POST", "/api/setup/diagnostic/finish", {}, status=409)

    def test_a_wrong_answer_is_reported_with_its_failing_input(self):
        self.call("PUT", "/api/setup/diagnostic/answer",
                  {"slug": "contains-duplicate", "code": DUP_WRONG, "seconds": 30})
        out = self.call("POST", "/api/setup/diagnostic/finish", {})
        first = out["review"]["problems"][0]
        self.assertNotRegex(first["result"], r"^(\d+)/\1 passed$")
        self.assertIn("expected", first["first_failing"])


if __name__ == "__main__":
    unittest.main()
