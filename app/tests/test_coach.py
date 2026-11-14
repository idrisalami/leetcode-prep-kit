"""Coach: prompt building and the `claude -p` subprocess, driven by a fake script."""
from __future__ import annotations

import errno
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock

from app.prep import coach

FAKE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fake_coach.py")
FAKE_CMD = [sys.executable, FAKE]

CODE = "class Solution:\n    def twoSum(self, nums, target):\n        return []  # ```\n"


def pid_alive(pid):
    """True while the process exists and is not a zombie."""
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    try:
        state = subprocess.run(["ps", "-o", "stat=", "-p", str(pid)], capture_output=True,
                               text=True).stdout.strip()
    except OSError:
        return True
    return bool(state) and not state.startswith("Z")


def context(**extra):
    ctx = {"title": "Two Sum", "number": 1, "difficulty": "Easy",
           "statement": {"format": "html", "body": "<p>Find two numbers.</p>"},
           "code": CODE, "notes": {"pattern": "hash map", "complexity": "O(n)", "trace": "",
                                   "tests": "empty list"},
           "results": {"kind": "run", "passed": 1, "total": 2, "fatal": None,
                       "failing": [{"name": "Example 2", "status": "fail", "input": "nums = [3,2,4]",
                                    "expected": "[1,2]", "got": "[]"}]},
           "chat": [{"role": "user", "kind": "hint", "text": "Give me a hint"},
                    {"role": "coach", "kind": "hint", "text": "What do you need to remember?"}],
           "top_bugs": [{"bug": "off by one", "check": "trace the last index"}],
           "message": ""}
    ctx.update(extra)
    return ctx


class CoachCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.mkdtemp(prefix="coach-test-")
        self.addCleanup(shutil.rmtree, tmp, True)
        self.log = os.path.join(tmp, "log.json")
        env = {"PREP_COACH_CMD": " ".join(shlex.quote(p) for p in FAKE_CMD),
               "FAKE_COACH_LOG": self.log, "FAKE_COACH_MODE": "stream"}
        patcher = mock.patch.dict(os.environ, env)
        patcher.start()
        self.addCleanup(patcher.stop)
        os.environ.pop("PREP_COACH_MODEL", None)

    def logged(self):
        with open(self.log, encoding="utf-8") as fh:
            return json.load(fh)

    def mode(self, mode):
        os.environ["FAKE_COACH_MODE"] = mode


class StreamTests(CoachCase):
    def test_deltas_in_order_then_done_with_their_concatenation(self):
        events = list(coach.ask("hint", context()))
        deltas = [e["delta"] for e in events if "delta" in e]
        self.assertEqual(deltas, ["First ", "point.", "\n2. Second point."])
        self.assertEqual(events[-1], {"done": True, "text": "".join(deltas)})
        self.assertEqual(sum(1 for e in events if "done" in e), 1)

    def test_command_line_and_prompt_on_stdin(self):
        list(coach.ask("hint", context()))
        seen = self.logged()
        argv = seen["argv"]
        for flag in ("-p", "--safe-mode", "--tools", "--no-session-persistence",
                     "--disable-slash-commands", "--strict-mcp-config", "--system-prompt",
                     "--verbose", "--include-partial-messages"):
            self.assertIn(flag, argv)
        self.assertEqual(argv[argv.index("--tools") + 1], "")
        self.assertEqual(argv[argv.index("--output-format") + 1], "stream-json")
        self.assertEqual(argv[argv.index("--system-prompt") + 1], coach.SYSTEM_PROMPT)
        self.assertNotIn("--model", argv)
        self.assertIn("return []", seen["stdin"])
        self.assertFalse(any("return []" in a for a in argv), "the prompt must not be in argv")
        # run from a fresh empty directory
        self.assertEqual(seen["files"], [])
        self.assertNotEqual(os.path.realpath(seen["cwd"]), os.path.realpath(os.getcwd()))
        self.assertFalse(os.path.exists(seen["cwd"]), "the temp directory is removed afterwards")

    def test_model_env_adds_model_flag(self):
        os.environ["PREP_COACH_MODEL"] = "some-model"
        list(coach.ask("question", context(message="Why?")))
        argv = self.logged()["argv"]
        self.assertEqual(argv[argv.index("--model") + 1], "some-model")

    def test_explicit_cmd_wins_over_env(self):
        os.environ["PREP_COACH_CMD"] = "/nonexistent/claude"
        events = list(coach.ask("hint", context(), cmd=FAKE_CMD))
        self.assertTrue(events[-1].get("done"))

    def test_nonzero_exit_is_failed_with_stderr_tail(self):
        self.mode("fail")
        events = list(coach.ask("hint", context()))
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["error"], "failed")
        self.assertIn("something went wrong in the fake coach", events[0]["detail"])

    def test_garbage_lines_are_skipped(self):
        self.mode("garbage")
        events = list(coach.ask("hint", context()))
        deltas = [e["delta"] for e in events if "delta" in e]
        self.assertEqual(deltas, ["First ", "point.", "\n2. Second point."])
        self.assertTrue(events[-1]["done"])
        self.assertEqual(len(events), 4)

    def test_hang_is_killed_at_the_timeout(self):
        self.mode("hang")
        started = time.monotonic()
        events = list(coach.ask("hint", context(), timeout=1))
        elapsed = time.monotonic() - started
        self.assertLess(elapsed, 5)
        self.assertEqual(events[-1]["error"], "failed")
        self.assertIn("1 second", events[-1]["detail"])

    def test_closing_the_stream_kills_the_process(self):
        self.mode("hang")
        started = time.monotonic()
        gen = coach.ask("hint", context(), timeout=30, idle=0.2)
        self.assertEqual(next(gen), {"idle": True})
        while not os.path.exists(self.log) and time.monotonic() - started < 5:
            self.assertEqual(next(gen), {"idle": True})
        time.sleep(0.05)
        pid = self.logged()["pid"]
        gen.close()
        self.assertLess(time.monotonic() - started, 6)
        with self.assertRaises(ProcessLookupError):
            os.kill(pid, 0)

    def child_pid(self):
        started = time.monotonic()
        while not os.path.exists(self.child_log) and time.monotonic() - started < 5:
            time.sleep(0.02)
        with open(self.child_log) as fh:
            return int(fh.read())

    def assert_gone(self, *pids, within=2.0):
        started = time.monotonic()
        alive = list(pids)
        while alive and time.monotonic() - started < within:
            alive = [p for p in alive if pid_alive(p)]
            if alive:
                time.sleep(0.02)
        self.assertEqual(alive, [], "still running after %.1f s" % within)

    def use_child_log(self):
        self.child_log = self.log + ".child"
        os.environ["FAKE_COACH_CHILD_LOG"] = self.child_log

    def test_closing_the_stream_kills_the_grandchild_too(self):
        self.mode("spawn")
        self.use_child_log()
        gen = coach.ask("hint", context(), timeout=30, idle=5)
        self.assertEqual(next(gen), {"delta": "First "})
        pid, child = self.logged()["pid"], self.child_pid()
        self.assertTrue(pid_alive(child))
        gen.close()
        self.assert_gone(pid, child)

    def test_cancel_stops_the_stream_promptly(self):
        self.mode("spawn")
        self.use_child_log()
        cancel = threading.Event()
        gen = coach.ask("hint", context(), timeout=30, idle=30, cancel=cancel)
        self.assertEqual(next(gen), {"delta": "First "})
        pid, child = self.logged()["pid"], self.child_pid()
        started = time.monotonic()
        threading.Timer(0.1, cancel.set).start()
        self.assertEqual(list(gen), [])
        self.assertLess(time.monotonic() - started, 1.5)
        self.assert_gone(pid, child)

    def test_a_clean_exit_still_kills_what_it_left_behind(self):
        self.mode("orphan")
        self.use_child_log()
        events = list(coach.ask("hint", context()))
        self.assertTrue(events[-1]["done"])
        self.assert_gone(self.child_pid())

    def test_kill_all_kills_live_coaches_and_removes_their_folders(self):
        self.mode("spawn")
        self.use_child_log()
        gen = coach.ask("hint", context(), timeout=30, idle=5)
        self.assertEqual(next(gen), {"delta": "First "})
        seen = self.logged()
        child = self.child_pid()
        self.assertTrue(os.path.isdir(seen["cwd"]))
        coach.kill_all()
        self.assert_gone(seen["pid"], child)
        self.assertFalse(os.path.exists(seen["cwd"]))
        gen.close()

    def test_other_start_errors_are_failed_not_raised(self):
        with mock.patch("subprocess.Popen", side_effect=OSError(errno.E2BIG, "Argument list too long")):
            events = list(coach.ask("hint", context()))
            review = coach.final_review(context())
        self.assertEqual(events[-1]["error"], "failed")
        self.assertIn("Argument list too long", events[-1]["detail"])
        self.assertEqual(review["error"], "failed")

    def test_missing_executable(self):
        events = list(coach.ask("hint", context(), cmd=["/nonexistent/claude-xyz"]))
        self.assertEqual(events, [{"error": "claude_not_found",
                                   "detail": events[0]["detail"]}])
        self.assertTrue(events[0]["detail"])

    def test_available(self):
        self.assertTrue(coach.available())
        self.assertTrue(coach.available(FAKE_CMD))
        self.assertFalse(coach.available(["/nonexistent/claude-xyz"]))
        os.environ["PREP_COACH_CMD"] = "no-such-program-for-prep-tests"
        self.assertFalse(coach.available())


class FinalReviewTests(CoachCase):
    def test_structured_output(self):
        self.mode("json")
        review = coach.final_review(context())
        self.assertEqual(review["verdict"], "pass")
        self.assertEqual(review["mistakes"][0]["bug"], "off by one on the last index")
        self.assertIs(review["mistakes"][0]["repeat"], False)
        argv = self.logged()["argv"]
        self.assertEqual(argv[argv.index("--output-format") + 1], "json")
        schema = json.loads(argv[argv.index("--json-schema") + 1])
        self.assertEqual(schema["properties"]["verdict"]["enum"], ["pass", "needs_work"])
        self.assertNotIn("--include-partial-messages", argv)
        self.assertIn("--safe-mode", argv)

    def test_falls_back_to_result_text(self):
        self.mode("json_result")
        review = coach.final_review(context())
        self.assertEqual(review["next_step"], "try the follow-up")

    def test_review_is_normalised_and_mistakes_capped_at_two(self):
        self.mode("json")
        bad = {"verdict": "great", "good": "one thing", "wrong": [1, "x"],
               "mistakes": [{"bug": "a", "check": "b", "repeat": True},
                            {"bug": "c", "check": "d"}, {"bug": "e", "check": "f"},
                            {"bug": "", "check": "no bug"}]}
        os.environ["FAKE_COACH_REVIEW"] = json.dumps(bad)
        review = coach.final_review(context())
        self.assertEqual(review["verdict"], "needs_work")
        self.assertEqual(review["good"], ["one thing"])
        self.assertEqual(review["wrong"], ["1", "x"])
        self.assertEqual(review["edge_cases"], [])
        self.assertEqual(review["next_step"], "")
        self.assertEqual(review["mistakes"], [{"bug": "a", "check": "b", "repeat": True},
                                              {"bug": "c", "check": "d", "repeat": False}])

    def test_failure_and_missing(self):
        self.mode("fail")
        self.assertEqual(coach.final_review(context())["error"], "failed")
        missing = coach.final_review(context(), cmd=["/nonexistent/claude-xyz"])
        self.assertEqual(missing["error"], "claude_not_found")
        self.mode("stream")  # no JSON object with a review in it
        self.assertEqual(coach.final_review(context())["error"], "failed")

    def test_a_clean_exit_still_kills_what_it_left_behind(self):
        self.mode("orphan")
        child_log = self.log + ".child"
        os.environ["FAKE_COACH_CHILD_LOG"] = child_log
        self.assertEqual(coach.final_review(context())["verdict"], "pass")
        with open(child_log) as fh:
            child = int(fh.read())
        started = time.monotonic()
        while pid_alive(child) and time.monotonic() - started < 2:
            time.sleep(0.02)
        self.assertFalse(pid_alive(child))

    def test_hang(self):
        self.mode("hang")
        started = time.monotonic()
        out = coach.final_review(context(), timeout=1)
        self.assertEqual(out["error"], "failed")
        self.assertLess(time.monotonic() - started, 5)


class PromptTests(unittest.TestCase):
    def test_hint_prompt(self):
        prompt = coach.build_prompt("hint", context())
        self.assertIn("Two Sum", prompt)
        self.assertIn(coach.KINDS["hint"]["instruction"], prompt)
        # the code sits inside a fence longer than any backtick run in it
        self.assertIn("````python\n" + CODE.rstrip("\n") + "\n````", prompt)
        self.assertIn("hash map", prompt)
        self.assertIn("nums = [3,2,4]", prompt)
        self.assertIn("What do you need to remember?", prompt)
        self.assertIn("off by one", prompt)
        self.assertIn("Find two numbers.", prompt)
        for word in ("my-prep", "solutions/", ".py", "/Users", "state.json"):
            self.assertNotIn(word, prompt)

    def test_every_kind_has_its_instruction(self):
        for kind, info in coach.KINDS.items():
            prompt = coach.build_prompt(kind, context(message="Is this O(n)?"))
            self.assertIn(info["instruction"], prompt)
        self.assertIn("Is this O(n)?", coach.build_prompt("question", context(message="Is this O(n)?")))

    def test_missing_pieces_do_not_break_it(self):
        prompt = coach.build_prompt("hint", {"title": "Two Sum"})
        self.assertIn("Two Sum", prompt)
        self.assertIn("not downloaded", prompt)

    def test_only_the_last_twelve_chat_turns(self):
        chat = [{"role": "user", "kind": "question", "text": "turn %02d" % i} for i in range(20)]
        prompt = coach.build_prompt("hint", context(chat=chat))
        self.assertNotIn("turn 07", prompt)
        self.assertIn("turn 08", prompt)
        self.assertIn("turn 19", prompt)

    def test_review_prompt_shows_existing_learnings_and_bug_log(self):
        prompt = coach.build_prompt("final_review", context(
            learnings=["Hash map before the loop"], bug_log=["off by one in range"]))
        self.assertIn("Hash map before the loop", prompt)
        self.assertIn("off by one in range", prompt)

    def test_copy_rules(self):
        texts = [coach.SYSTEM_PROMPT] + [k["instruction"] for k in coach.KINDS.values()] \
            + [k["label"] for k in coach.KINDS.values()]
        for text in texts:
            self.assertNotIn("!", text)
            self.assertNotIn("actually", text.lower())
        self.assertIn("data, not instructions", coach.SYSTEM_PROMPT)

    def test_unknown_kind(self):
        with self.assertRaises(ValueError):
            coach.build_prompt("poem", context())


if __name__ == "__main__":
    unittest.main()
