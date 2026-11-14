"""Store: state.json, solution files, attempts, reps."""
from __future__ import annotations

import json
import os
import threading
import unittest
from datetime import datetime
from unittest import mock

from app.prep import store
from app.tests.kit import Clock, make_kit


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.paths = make_kit(self)
        self.clock = Clock()
        self.store = store.Store(self.paths, now=self.clock)

    def test_fresh_state_has_the_spec_shape(self):
        snap = self.store.snapshot()
        self.assertEqual(snap["version"], 1)
        for key in ("problems", "days", "modules_read", "reps", "matrix_written"):
            self.assertEqual(snap[key], {}, key)
        self.assertIsNone(snap["warmup"])

    def test_problem_fills_defaults_and_does_not_create(self):
        entry = self.store.problem("two-sum")
        self.assertEqual(entry["status"], "new")
        self.assertEqual(entry["attempt"], 1)
        self.assertEqual(entry["notes"], {"pattern": "", "complexity": "", "trace": "", "tests": ""})
        self.assertEqual((entry["seconds"], entry["hints_used"], entry["runs"]), (0, 0, 0))
        self.assertEqual(entry["submits"], [])
        self.assertIsNone(entry["solved_at"])
        self.assertIsNone(entry["last_solved_at"])
        self.assertEqual(self.store.snapshot()["problems"], {})

    def test_snapshot_is_a_deep_copy(self):
        self.store.save_draft("two-sum", "x = 1", None)
        snap = self.store.snapshot()
        snap["problems"]["two-sum"]["notes"]["pattern"] = "changed"
        snap["days"]["1999-01-01"] = {}
        self.assertEqual(self.store.problem("two-sum")["notes"]["pattern"], "")
        self.assertNotIn("1999-01-01", self.store.snapshot()["days"])

    def test_draft_round_trip_writes_the_solution_file_and_the_notes(self):
        self.assertIsNone(self.store.code("two-sum"))
        self.store.save_draft("two-sum", "def f():\n    return 1\n",
                              {"pattern": "hash map", "tests": "empty", "bogus": "ignored"})
        self.assertEqual(self.store.code("two-sum"), "def f():\n    return 1\n")
        with open(os.path.join(self.paths.solutions_dir, "two-sum.py"), encoding="utf-8") as fh:
            self.assertEqual(fh.read(), "def f():\n    return 1\n")
        entry = self.store.problem("two-sum")
        self.assertEqual(entry["notes"]["pattern"], "hash map")
        self.assertEqual(entry["notes"]["tests"], "empty")
        self.assertNotIn("bogus", entry["notes"])
        self.assertEqual(entry["status"], "attempted")
        self.assertEqual(entry["first_opened"], "2026-11-12T09:00:00")
        # notes alone, and code alone, keep what the other call saved
        self.store.save_draft("two-sum", "y = 2", None)
        self.assertEqual(self.store.problem("two-sum")["notes"]["pattern"], "hash map")
        self.store.save_draft("two-sum", None, {"complexity": "O(n)"})
        self.assertEqual(self.store.code("two-sum"), "y = 2")

    def test_state_survives_a_restart(self):
        self.store.save_draft("two-sum", "x", {"pattern": "p"})
        again = store.Store(self.paths, now=self.clock)
        self.assertEqual(again.problem("two-sum")["notes"]["pattern"], "p")

    def test_unsafe_slugs_are_refused(self):
        for bad in ("../x", "a/b", "", "UP", "a.b"):
            with self.assertRaises(ValueError, msg=bad):
                self.store.save_draft(bad, "x", None)

    def test_run_counts_on_the_problem_and_the_day(self):
        self.store.record_run("two-sum")
        self.store.record_run("two-sum")
        entry = self.store.problem("two-sum")
        self.assertEqual((entry["runs"], entry["status"]), (2, "attempted"))
        self.assertEqual(self.store.snapshot()["days"]["2026-11-12"]["runs"], 2)

    def test_submit_fail_then_pass_is_not_first_try(self):
        self.store.add_seconds("two-sum", 40)
        failed = self.store.record_submit("two-sum", 3, 5)
        self.assertFalse(failed["ok"])
        self.assertEqual((failed["passed"], failed["total"], failed["attempt"]), (3, 5, 1))
        self.assertEqual(failed["seconds"], 40)
        self.assertFalse(failed["reviewed"])
        entry = self.store.problem("two-sum")
        self.assertEqual(entry["status"], "attempted")
        self.assertIs(entry["first_try"], False)
        self.assertIsNone(entry["solved_at"])
        self.clock.advance(minutes=5)
        passed = self.store.record_submit("two-sum", 5, 5)
        self.assertTrue(passed["ok"])
        self.assertNotEqual(passed["id"], failed["id"])
        entry = self.store.problem("two-sum")
        self.assertEqual(entry["status"], "solved")
        self.assertIs(entry["first_try"], False)
        self.assertEqual(entry["solved_at"], "2026-11-12T09:05:00")
        self.assertEqual(entry["last_solved_at"], "2026-11-12T09:05:00")
        self.assertEqual(len(entry["submits"]), 2)
        day = self.store.snapshot()["days"]["2026-11-12"]
        self.assertEqual((day["submits"], day["solved"]), (2, ["two-sum"]))

    def test_submit_pass_first_is_first_try(self):
        rec = self.store.record_submit("two-sum", 5, 5)
        entry = self.store.problem("two-sum")
        self.assertIs(entry["first_try"], True)
        self.assertEqual(entry["status"], "solved")
        self.assertEqual(self.store.submit("two-sum", rec["id"])["id"], rec["id"])
        self.assertIsNone(self.store.submit("two-sum", "nope"))
        self.assertIsNone(self.store.submit("unknown", rec["id"]))

    def test_later_failing_submit_keeps_solved_and_first_solve_fields(self):
        self.store.record_submit("two-sum", 5, 5)
        solved_at = self.store.problem("two-sum")["solved_at"]
        self.clock.advance(days=1)
        self.store.record_submit("two-sum", 1, 5)
        entry = self.store.problem("two-sum")
        self.assertEqual(entry["status"], "solved")
        self.assertEqual(entry["solved_at"], solved_at)
        self.assertIs(entry["first_try"], True)
        self.assertEqual(entry["last_solved_at"], solved_at)
        self.clock.advance(days=1)
        self.store.record_submit("two-sum", 5, 5)
        self.assertEqual(self.store.problem("two-sum")["last_solved_at"], "2026-11-14T09:00:00")
        self.assertEqual(self.store.problem("two-sum")["solved_at"], solved_at)

    def test_zero_total_is_not_a_pass(self):
        self.assertFalse(self.store.record_submit("two-sum", 0, 0)["ok"])

    def test_mark_reviewed(self):
        rec = self.store.record_submit("two-sum", 1, 5)
        self.store.mark_reviewed("two-sum", rec["id"], {"verdict": "close"})
        got = self.store.submit("two-sum", rec["id"])
        self.assertTrue(got["reviewed"])
        self.assertEqual(got["review"], {"verdict": "close"})

    def test_chat_and_hints(self):
        self.store.add_chat("two-sum", "user", "hint", "stuck")
        self.store.add_chat("two-sum", "coach", "hint", "think about a map")
        self.store.add_hint("two-sum")
        entry = self.store.problem("two-sum")
        self.assertEqual([c["role"] for c in entry["chat"]], ["user", "coach"])
        self.assertEqual(entry["chat"][0]["kind"], "hint")
        self.assertEqual(entry["chat"][0]["at"], "2026-11-12T09:00:00")
        self.assertEqual((entry["hints_used"], entry["attempt_hints"]), (1, 1))

    def test_seconds_are_clamped_and_land_on_day_and_problem(self):
        self.store.add_seconds("two-sum", 500)
        self.store.add_seconds("two-sum", -5)
        self.store.add_seconds(None, 10)
        self.store.add_seconds("two-sum", 20)
        entry = self.store.problem("two-sum")
        self.assertEqual((entry["seconds"], entry["attempt_seconds"]), (80, 80))
        self.assertEqual(self.store.snapshot()["days"]["2026-11-12"]["seconds"], 90)

    def test_two_threads_lose_no_seconds(self):
        def work():
            for _ in range(200):
                self.store.add_seconds("two-sum", 1)
        threads = [threading.Thread(target=work) for _ in range(2)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(self.store.problem("two-sum")["seconds"], 400)
        self.assertEqual(self.store.snapshot()["days"]["2026-11-12"]["seconds"], 400)
        again = store.Store(self.paths, now=self.clock)
        self.assertEqual(again.problem("two-sum")["seconds"], 400)

    def test_writes_are_atomic_and_leave_valid_json(self):
        self.store.save_draft("two-sum", "x", None)
        self.store.add_seconds("two-sum", 5)
        folder = os.path.dirname(self.paths.state_file)
        self.assertEqual(os.listdir(folder), ["state.json"])
        with open(self.paths.state_file, encoding="utf-8") as fh:
            self.assertEqual(json.load(fh)["problems"]["two-sum"]["seconds"], 5)
        self.assertEqual(os.listdir(self.paths.solutions_dir), ["two-sum.py"])

    def test_corrupt_state_is_set_aside_and_a_fresh_one_started(self):
        os.makedirs(os.path.dirname(self.paths.state_file), exist_ok=True)
        with open(self.paths.state_file, "w", encoding="utf-8") as fh:
            fh.write("{not json")
        fresh = store.Store(self.paths, now=self.clock)
        self.assertEqual(fresh.snapshot()["problems"], {})
        folder = os.path.dirname(self.paths.state_file)
        broken = [f for f in os.listdir(folder) if f.startswith("state.json.broken-")]
        self.assertEqual(len(broken), 1)
        self.assertEqual(fresh.recovered, os.path.join(folder, broken[0]))
        with open(os.path.join(folder, broken[0]), encoding="utf-8") as fh:
            self.assertEqual(fh.read(), "{not json")
        self.assertIsNone(self.store.recovered)

    def test_reset_code_deletes_the_file_and_keeps_history(self):
        self.store.save_draft("two-sum", "x", {"pattern": "p"})
        self.store.record_submit("two-sum", 1, 5)
        self.store.reset_code("two-sum")
        self.assertIsNone(self.store.code("two-sum"))
        self.assertEqual(len(self.store.problem("two-sum")["submits"]), 1)
        self.assertEqual(self.store.problem("two-sum")["attempt"], 1)
        self.store.reset_code("two-sum")  # already gone: no error
        self.store.reset_code("never-seen")
        self.assertNotIn("never-seen", self.store.snapshot()["problems"])
        self.assertEqual(self.store.rev("never-seen"), 0)

    def test_reset_keeps_changed_code_as_prev(self):
        prev = os.path.join(self.paths.solutions_dir, "two-sum.prev.py")
        self.store.save_draft("two-sum", "my code", None)
        self.store.reset_code("two-sum", "skeleton")
        self.assertIsNone(self.store.code("two-sum"))
        with open(prev, encoding="utf-8") as fh:
            self.assertEqual(fh.read(), "my code")
        # code equal to the skeleton is dropped and leaves the older .prev.py alone
        self.store.save_draft("two-sum", "skeleton", None)
        self.store.reset_code("two-sum", "skeleton")
        self.assertIsNone(self.store.code("two-sum"))
        with open(prev, encoding="utf-8") as fh:
            self.assertEqual(fh.read(), "my code")

    def test_rev_and_touched_at(self):
        self.assertEqual(self.store.rev("two-sum"), 0)
        self.store.save_draft("two-sum", "x", None)
        self.assertEqual(self.store.rev("two-sum"), 1)
        self.store.record_run("two-sum")
        self.assertEqual(self.store.rev("two-sum"), 1)
        self.clock.advance(minutes=2)
        self.store.record_submit("two-sum", 1, 5)
        self.assertEqual(self.store.problem("two-sum")["touched_at"], "2026-11-12T09:02:00")
        self.store.reset_code("two-sum")
        self.assertEqual(self.store.rev("two-sum"), 2)
        self.store.reset_code("two-sum")  # an entry exists, so the page must reload either way
        self.assertEqual(self.store.rev("two-sum"), 3)

    def test_redo_starts_a_new_attempt(self):
        self.store.save_draft("two-sum", "first code", {"pattern": "p"})
        self.store.add_chat("two-sum", "user", "hint", "help")
        self.store.add_seconds("two-sum", 60)
        self.store.add_hint("two-sum")
        self.store.record_run("two-sum")
        first = self.store.record_submit("two-sum", 5, 5)
        before = self.store.problem("two-sum")
        self.assertEqual((first["seconds"], first["hints_used"]), (60, 1))
        self.clock.advance(days=3)
        self.assertEqual(self.store.redo("two-sum"), 2)
        after = self.store.problem("two-sum")
        self.assertEqual(after["attempt"], 2)
        self.assertEqual((after["attempt_seconds"], after["attempt_hints"]), (0, 0))
        self.assertEqual(after["chat"], [])
        self.assertEqual(after["notes"], {"pattern": "", "complexity": "", "trace": "", "tests": ""})
        self.assertEqual((after["solved_at"], after["first_try"]), (before["solved_at"], True))
        self.assertEqual(after["status"], "solved")
        self.assertEqual((after["seconds"], after["hints_used"], after["runs"]), (60, 1, 1))
        self.assertEqual(len(after["submits"]), 1)
        self.assertIsNone(self.store.code("two-sum"))
        prev = os.path.join(self.paths.solutions_dir, "two-sum.prev.py")
        with open(prev, encoding="utf-8") as fh:
            self.assertEqual(fh.read(), "first code")
        self.store.save_draft("two-sum", "second code", None)
        self.store.add_seconds("two-sum", 30)
        self.store.add_hint("two-sum")
        self.store.add_hint("two-sum")
        second = self.store.record_submit("two-sum", 2, 5)
        self.assertEqual((second["attempt"], second["seconds"], second["hints_used"]), (2, 30, 2))
        self.assertEqual(self.store.problem("two-sum")["hints_used"], 3)
        # a second redo overwrites the older .prev.py
        self.store.redo("two-sum")
        with open(prev, encoding="utf-8") as fh:
            self.assertEqual(fh.read(), "second code")

    def test_add_rep_replaces_the_same_slug_and_attempt(self):
        self.assertEqual(self.store.add_rep("A6", "a", 1, 1), [1])
        self.clock.advance(minutes=1)
        self.assertEqual(self.store.add_rep("A6", "b", 1, 0), [1, 0])
        self.clock.advance(minutes=1)
        self.assertEqual(self.store.add_rep("A6", "a", 1, 2), [0, 2])
        self.clock.advance(minutes=1)
        self.assertEqual(self.store.add_rep("A6", "a", 2, 3), [0, 2, 3])
        self.clock.advance(minutes=1)
        self.assertEqual(self.store.add_rep("A6", "c", 1, 1), [2, 3, 1])
        rows = self.store.snapshot()["reps"]["A6"]
        self.assertEqual(sorted(r["slug"] + str(r["attempt"]) for r in rows), ["a1", "a2", "b1", "c1"])
        self.assertEqual(set(rows[0]), {"slug", "attempt", "level", "at"})
        self.assertEqual(self.store.add_rep("A7", "z", 1, 3), [3])

    def test_matrix_written_module_read_and_warmup(self):
        self.assertIsNone(self.store.matrix_written("A6"))
        self.store.set_matrix_written("A6", "2")
        self.assertEqual(self.store.matrix_written("A6"), "2")
        self.store.set_module_read("00", True)
        self.assertEqual(self.store.snapshot()["modules_read"], {"00": True})
        self.store.set_module_read("00", False)
        self.assertEqual(self.store.snapshot()["modules_read"], {"00": False})
        self.assertIsNone(self.store.warmup())
        self.store.set_warmup("2026-11-12", "two-sum", ["a"])
        self.assertEqual(self.store.warmup(), {"date": "2026-11-12", "slug": "two-sum", "skipped": ["a"]})


class WrongShapeTests(unittest.TestCase):
    def setUp(self):
        self.paths = make_kit(self)
        self.clock = Clock()

    def put(self, data):
        os.makedirs(os.path.dirname(self.paths.state_file), exist_ok=True)
        with open(self.paths.state_file, "w", encoding="utf-8") as fh:
            json.dump(data, fh)

    def broken_files(self):
        folder = os.path.dirname(self.paths.state_file)
        return [f for f in os.listdir(folder) if ".broken-" in f]

    def open_store(self):
        return store.Store(self.paths, now=self.clock)

    def test_wrong_shaped_state_is_set_aside_and_the_app_starts_fresh(self):
        cases = [{"days": None}, {"days": []}, {"reps": []}, {"reps": None}, {"warmup": 5},
                 {"problems": []}, {"modules_read": []}, {"matrix_written": []},
                 {"matrix_written": None}, {"version": "one"}, [], "x", 3, None]
        for data in cases:
            with self.subTest(data=data):
                self.put(data)
                before = len(self.broken_files())
                st = self.open_store()
                self.assertIsInstance(st.recovered, str)
                self.assertEqual(len(self.broken_files()), before + 1)
                self.assertFalse(os.path.exists(self.paths.state_file))
                self.assertEqual(st.snapshot()["days"], {})
                st.record_run("two-sum")  # the next write works
                st.add_rep("A6", "two-sum", 1, 2)
                st.warmup()
                self.clock.advance(seconds=1)
                os.remove(self.paths.state_file)
                for name in self.broken_files():
                    os.remove(os.path.join(os.path.dirname(self.paths.state_file), name))

    def test_a_valid_state_is_not_set_aside(self):
        self.put({"version": 1, "problems": {}, "days": {}, "modules_read": {}, "reps": {},
                  "matrix_written": {}, "warmup": None, "future_key": [1]})
        st = self.open_store()
        self.assertIsNone(st.recovered)
        self.assertEqual(self.broken_files(), [])
        self.assertEqual(st.snapshot()["future_key"], [1])

    def test_an_empty_day_record_survives_record_run(self):
        self.put({"days": {"2026-11-12": {}}})
        st = self.open_store()
        self.assertIsNone(st.recovered)
        st.record_run("two-sum")
        st.record_submit("two-sum", 1, 1)
        st.add_seconds("two-sum", 10)
        day = st.snapshot()["days"]["2026-11-12"]
        self.assertEqual((day["runs"], day["submits"], day["seconds"], day["solved"]),
                         (1, 1, 10, ["two-sum"]))

    def test_a_day_with_null_values_is_normalised(self):
        self.put({"days": {"2026-11-12": {"runs": None, "submits": "x", "seconds": None,
                                           "solved": None}, "2026-11-11": 4, "2026-11-10": []}})
        st = self.open_store()
        self.assertEqual(list(st.snapshot()["days"]), ["2026-11-12"])
        st.record_run("two-sum")
        self.assertEqual(st.snapshot()["days"]["2026-11-12"]["runs"], 1)

    def test_a_rep_row_without_attempt_survives_add_rep(self):
        self.put({"reps": {"A6": [{"slug": "a", "level": 1, "at": "2026-11-01T09:00:00"},
                                   "junk", {"attempt": 1, "level": 2},
                                   {"slug": "b", "attempt": 1}], "A7": "nope"}})
        st = self.open_store()
        self.assertIsNone(st.recovered)
        levels = st.add_rep("A6", "c", 1, 3)
        self.assertEqual(levels[-1], 3)
        self.assertEqual(st.add_rep("A7", "c", 1, 1), [1])

    def test_malformed_problem_records_are_normalised(self):
        self.put({"problems": {"good": {"status": "solved", "runs": 2}, "junk": 5, "nulls": {
            "runs": None, "notes": None, "submits": {}, "attempt": None, "chat": 3}}})
        st = self.open_store()
        self.assertIsNone(st.recovered)
        self.assertEqual(sorted(st.snapshot()["problems"]), ["good", "nulls"])
        st.record_run("nulls")
        st.add_hint("nulls")
        st.save_draft("nulls", None, {"pattern": "p"})
        st.record_submit("nulls", 1, 1)
        st.add_chat("nulls", "user", "hint", "t")
        self.assertEqual(st.redo("nulls"), 2)
        self.assertEqual(st.problem("good")["runs"], 2)
        st.record_run("junk")

    def test_unknown_keys_in_sub_dicts_survive_a_load_and_save(self):
        self.put({"problems": {"two-sum": {"status": "solved", "notes": {"pattern": "p", "future": "keep"},
                                           "newer_field": {"a": 1}}},
                  "days": {"2026-11-12": {"runs": 2, "streak": 5}},
                  "warmup": {"date": "2026-11-12", "slug": "a", "skipped": [], "mood": "ok"}})
        st = self.open_store()
        st.record_run("two-sum")  # forces a save
        with open(self.paths.state_file, encoding="utf-8") as fh:
            saved = json.load(fh)
        problem = saved["problems"]["two-sum"]
        self.assertEqual(problem["notes"], {"pattern": "p", "complexity": "", "trace": "",
                                            "tests": "", "future": "keep"})
        self.assertEqual(problem["newer_field"], {"a": 1})
        self.assertEqual(saved["days"]["2026-11-12"]["streak"], 5)
        self.assertEqual(saved["warmup"]["mood"], "ok")

    def test_known_keys_in_sub_dicts_are_still_repaired(self):
        self.put({"problems": {"two-sum": {"notes": {"pattern": 7, "future": "keep"}}},
                  "days": {"2026-11-12": {"runs": "x", "streak": 5}}})
        snap = self.open_store().snapshot()
        self.assertEqual(snap["problems"]["two-sum"]["notes"]["pattern"], "")
        self.assertEqual(snap["problems"]["two-sum"]["notes"]["future"], "keep")
        self.assertEqual(snap["days"]["2026-11-12"]["runs"], 0)
        self.assertEqual(snap["days"]["2026-11-12"]["streak"], 5)

    def test_a_failed_solution_write_raises_write_failed_with_the_relative_path(self):
        st = self.open_store()
        with mock.patch("app.prep.store.os.replace", side_effect=OSError(28, "No space left on device")):
            with self.assertRaises(store.WriteFailed) as ctx:
                st.save_draft("two-sum", "code", None)
        self.assertEqual(ctx.exception.rel_path, "my-prep/solutions/two-sum.py")
        self.assertIn("No space left", ctx.exception.reason)
        leftovers = os.listdir(self.paths.solutions_dir)
        self.assertEqual(leftovers, [], "the temp file is removed")
        self.assertNotIn("two-sum", st.snapshot()["problems"], "a failed write leaves no state")
        self.assertEqual(st.rev("two-sum"), 0)

    def test_draft_saved_at_is_the_solution_files_mtime(self):
        st = self.open_store()
        self.assertIsNone(st.draft_saved_at("two-sum"))
        st.save_draft("two-sum", "code", None)
        os.utime(os.path.join(self.paths.solutions_dir, "two-sum.py"),
                 (1767225600, 1767225600))
        stamp = st.draft_saved_at("two-sum")
        self.assertEqual(stamp, datetime.fromtimestamp(1767225600).isoformat(timespec="seconds"))

    def test_a_malformed_warmup_is_normalised(self):
        self.put({"warmup": {"date": "2026-11-12", "slug": "a", "skipped": 7}})
        self.assertEqual(self.open_store().warmup()["skipped"], [])

    def test_failing_set_aside_still_gives_a_fresh_store(self):
        self.put([])
        with mock.patch("app.prep.store.os.replace", side_effect=OSError("denied")):
            st = self.open_store()
        self.assertIsInstance(st.recovered, str)
        self.assertIn("denied", st.recovered)
        self.assertEqual(st.snapshot()["days"], {})
        st.record_run("two-sum")  # and it keeps working, saving over the unreadable file
        self.assertIsNone(st.save_error)

    def test_a_failed_save_keeps_memory_and_reports_the_error(self):
        st = self.open_store()
        self.assertIsNone(st.save_error)
        with mock.patch("app.prep.store.os.replace", side_effect=OSError("disk full")):
            st.record_run("two-sum")
            st.set_module_read("00", True)
            st.add_rep("A6", "two-sum", 1, 1)
        self.assertIn("disk full", st.save_error)
        self.assertEqual(st.problem("two-sum")["runs"], 1)
        self.assertEqual(st.snapshot()["modules_read"], {"00": True})
        folder = os.path.dirname(self.paths.state_file)
        self.assertEqual([f for f in os.listdir(folder) if f.endswith(".tmp")], [])
        st.record_run("two-sum")
        self.assertIsNone(st.save_error)
        self.assertEqual(self.open_store().problem("two-sum")["runs"], 2)

    def test_mark_reviewed_does_not_create_an_unknown_problem(self):
        st = self.open_store()
        st.mark_reviewed("never-seen", "abc", {"verdict": "close"})
        self.assertEqual(st.snapshot()["problems"], {})


if __name__ == "__main__":
    unittest.main()
