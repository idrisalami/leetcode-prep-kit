"""Notes: bootstrap from the templates and surgical edits of the skills matrix, learnings, bugs."""
from __future__ import annotations

import difflib
import os
import re
import stat
import threading
import unittest
from unittest import mock

from app.prep import notes
from app.tests.kit import make_kit


def read(path):
    with open(path, encoding="utf-8", newline="") as fh:
        return fh.read()


def raw(path):
    with open(path, "rb") as fh:
        return fh.read()


def write(path, text):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


class NotesCase(unittest.TestCase):
    def setUp(self):
        self.paths = make_kit(self)
        self.created = notes.bootstrap(self.paths)

    def mine(self, name):
        return os.path.join(self.paths.my_prep, name)


class BootstrapTests(NotesCase):
    def test_creates_every_template_except_the_lesson_plus_lessons_dir(self):
        templates = sorted(f for f in os.listdir(self.paths.templates) if f != "lesson.md")
        self.assertEqual(sorted(self.created), templates)
        self.assertEqual(sorted(f for f in os.listdir(self.paths.my_prep) if f != "lessons"), templates)
        self.assertNotIn("lesson.md", os.listdir(self.paths.my_prep))
        self.assertEqual(os.listdir(self.mine("lessons")), [])
        for name in templates:
            self.assertEqual(read(self.mine(name)), read(os.path.join(self.paths.templates, name)))

    def test_second_call_creates_nothing_and_keeps_edits(self):
        write(self.mine("plan.md"), "my own plan\n")
        self.assertEqual(notes.bootstrap(self.paths), [])
        self.assertEqual(read(self.mine("plan.md")), "my own plan\n")

    def test_a_missing_template_is_copied_alone(self):
        os.remove(self.mine("bugs.md"))
        write(self.mine("plan.md"), "edited\n")
        self.assertEqual(notes.bootstrap(self.paths), ["bugs.md"])
        self.assertEqual(read(self.mine("plan.md")), "edited\n")


class MatrixReadTests(NotesCase):
    def test_missing_file_gives_an_empty_list(self):
        os.remove(self.mine("skills-matrix.md"))
        self.assertEqual(notes.read_matrix(self.paths), [])

    def test_groups_and_rows_of_the_template(self):
        groups = notes.read_matrix(self.paths)
        rows = [r for g in groups for r in g["rows"]]
        ids = [r["id"] for r in rows]
        self.assertEqual(ids[:18], ["A%d" % i for i in range(1, 19)])
        self.assertIn("B1", ids)
        self.assertIn("C11", ids)
        self.assertEqual(groups[0]["title"], "A. Topics, in module order")
        self.assertEqual(len(groups[0]["rows"]), 18)  # the "outside the kit" table joins group A
        a6 = next(r for r in rows if r["id"] == "A6")
        self.assertEqual(a6, {"id": "A6", "requirement": "Binary search, including rotated arrays and searching the answer space",
                              "module": "04", "priority": "P0", "start": "?", "now": "?",
                              "evidence": "", "last_tested": ""})
        self.assertEqual(next(r for r in rows if r["id"] == "A13")["priority"], "set at discovery")

    def test_the_level_table_and_column_table_are_not_rows(self):
        ids = [r["id"] for g in notes.read_matrix(self.paths) for r in g["rows"]]
        self.assertTrue(all(i[0] in "ABC" and i[1:].isdigit() for i in ids), ids)


class UpdateMatrixRowTests(NotesCase):
    def diff(self, before, after):
        return [l for l in difflib.unified_diff(before.splitlines(), after.splitlines(), lineterm="", n=0)
                if l[:1] in "+-" and l[:3] not in ("+++", "---")]

    def test_changes_exactly_one_line_and_only_its_cells(self):
        before = read(self.mine("skills-matrix.md"))
        self.assertTrue(notes.update_matrix_row(self.paths, "A6", 2, "LC 704 Binary Search: passed first try in 12 min, no hints (app)", "2026-11-12"))
        after = read(self.mine("skills-matrix.md"))
        changes = self.diff(before, after)
        self.assertEqual(len(changes), 2, changes)  # one line out, one line in
        self.assertTrue(changes[0].startswith("-| A6 |"))
        row = next(r for g in notes.read_matrix(self.paths) for r in g["rows"] if r["id"] == "A6")
        self.assertEqual((row["start"], row["now"]), ("2", "2"))
        self.assertEqual(row["evidence"], "LC 704 Binary Search: passed first try in 12 min, no hints (app)")
        self.assertEqual(row["last_tested"], "2026-11-12")
        self.assertEqual((row["requirement"][:13], row["module"], row["priority"]), ("Binary search", "04", "P0"))
        self.assertEqual(before.count("\n"), after.count("\n"))

    def test_start_is_only_written_while_it_is_a_question_mark(self):
        notes.update_matrix_row(self.paths, "A6", 1, "first (app)", "2026-11-12")
        notes.update_matrix_row(self.paths, "A6", 3, "second (app)", "2026-11-13")
        row = next(r for g in notes.read_matrix(self.paths) for r in g["rows"] if r["id"] == "A6")
        self.assertEqual((row["start"], row["now"], row["evidence"], row["last_tested"]),
                         ("1", "3", "second (app)", "2026-11-13"))

    def test_hand_written_evidence_is_kept_before_the_app_segment(self):
        notes.update_matrix_row(self.paths, "A6", 1, "on paper | twice", "2026-11-12")
        notes.update_matrix_row(self.paths, "A6", 2, "LC 704 (app)", "2026-11-13")
        notes.update_matrix_row(self.paths, "A6", 2, "LC 35 (app)", "2026-11-14")
        row = next(r for g in notes.read_matrix(self.paths) for r in g["rows"] if r["id"] == "A6")
        self.assertEqual(row["evidence"], "on paper | twice; LC 35 (app)")

    def test_now_none_leaves_now_and_start_alone(self):
        self.assertTrue(notes.update_matrix_row(self.paths, "A7", None, "kept it", "2026-11-12"))
        row = next(r for g in notes.read_matrix(self.paths) for r in g["rows"] if r["id"] == "A7")
        self.assertEqual((row["start"], row["now"]), ("?", "?"))
        self.assertEqual((row["evidence"], row["last_tested"]), ("kept it", "2026-11-12"))

    def test_pipes_and_newlines_in_evidence_cannot_break_the_table(self):
        notes.update_matrix_row(self.paths, "A1", 1, "a | b\nc", "2026-11-12")
        row = next(r for g in notes.read_matrix(self.paths) for r in g["rows"] if r["id"] == "A1")
        self.assertEqual(row["evidence"], "a | b c")  # read back as one cell, pipe intact
        self.assertEqual(row["last_tested"], "2026-11-12")
        line = next(l for l in read(self.mine("skills-matrix.md")).splitlines() if l.startswith("| A1 |"))
        self.assertIn(r"| a \| b c |", line)

    def test_a_row_with_an_escaped_pipe_keeps_its_columns_on_the_next_update(self):
        notes.update_matrix_row(self.paths, "A1", 1, "a | b (app)", "2026-11-12")
        self.assertTrue(notes.update_matrix_row(self.paths, "A1", 2, "c | d (app)", "2026-11-13"))
        row = next(r for g in notes.read_matrix(self.paths) for r in g["rows"] if r["id"] == "A1")
        self.assertEqual((row["now"], row["evidence"], row["last_tested"]),
                         ("2", "c | d (app)", "2026-11-13"))

    def test_a_matrix_with_an_extra_column_keeps_the_extra_cell(self):
        path = self.mine("skills-matrix.md")
        text = read(path)
        lines = text.split("\n")
        for i, l in enumerate(lines):
            if l.startswith("| A6 |"):
                lines[i] = l + " extra |"
        write(path, "\n".join(lines))
        before = read(path)
        self.assertTrue(notes.update_matrix_row(self.paths, "A6", 2, "ev", "2026-11-12"))
        after = read(path)
        changes = self.diff(before, after)
        self.assertEqual(len(changes), 2, changes)
        self.assertTrue(changes[1].endswith("| extra |"), changes[1])
        row = next(r for g in notes.read_matrix(self.paths) for r in g["rows"] if r["id"] == "A6")
        self.assertEqual((row["now"], row["evidence"], row["last_tested"]), ("2", "ev", "2026-11-12"))

    def test_a_row_without_a_trailing_pipe_is_updated_in_place(self):
        path = self.mine("skills-matrix.md")
        notes.update_matrix_row(self.paths, "A6", 1, "first (app)", "2026-11-10")  # last cell filled
        lines = read(path).split("\n")
        for i, l in enumerate(lines):
            if l.startswith("| A6 |"):
                lines[i] = l.rstrip().rstrip("|").rstrip()
        write(path, "\n".join(lines))
        before = read(path)
        self.assertTrue(notes.update_matrix_row(self.paths, "A6", 2, "ev", "2026-11-12"))
        changes = self.diff(before, read(path))
        self.assertEqual(len(changes), 2, changes)
        row = next(r for g in notes.read_matrix(self.paths) for r in g["rows"] if r["id"] == "A6")
        self.assertEqual((row["now"], row["evidence"], row["last_tested"]), ("2", "ev", "2026-11-12"))

    def test_read_matrix_on_a_crlf_file_matches_the_lf_file(self):
        path = self.mine("skills-matrix.md")
        lf = notes.read_matrix(self.paths)
        write(path, read(path).replace("\n", "\r\n"))
        self.assertEqual(notes.read_matrix(self.paths), lf)

    def test_crlf_file_keeps_crlf(self):
        path = self.mine("skills-matrix.md")
        text = read(path).replace("\n", "\r\n")
        write(path, text)
        self.assertTrue(notes.update_matrix_row(self.paths, "A6", 2, "ev", "2026-11-12"))
        after = read(path)
        self.assertEqual(after.count("\n"), after.count("\r\n"))
        self.assertEqual(len(self.diff(text, after)), 2)

    def test_unknown_row_or_missing_table_or_file_returns_false_and_touches_nothing(self):
        path = self.mine("skills-matrix.md")
        before = read(path)
        self.assertFalse(notes.update_matrix_row(self.paths, "A99", 1, "x", "2026-11-12"))
        self.assertEqual(read(path), before)
        write(path, "# Skills matrix\n\nno tables here\n")
        self.assertFalse(notes.update_matrix_row(self.paths, "A6", 1, "x", "2026-11-12"))
        self.assertEqual(read(path), "# Skills matrix\n\nno tables here\n")
        os.remove(path)
        self.assertFalse(notes.update_matrix_row(self.paths, "A6", 1, "x", "2026-11-12"))
        self.assertFalse(os.path.exists(path))


class BugsTests(NotesCase):
    def test_top_bugs_on_the_untouched_template_is_empty(self):
        self.assertEqual(notes.top_bugs(self.paths), [])
        self.assertEqual(notes.bug_log(self.paths), [])

    def test_missing_files(self):
        os.remove(self.mine("bugs.md"))
        self.assertEqual(notes.top_bugs(self.paths), [])
        self.assertEqual(notes.bug_log(self.paths), [])
        self.assertFalse(notes.append_bug_log(self.paths, "b", "c", "w"))

    def test_top_bugs_returns_only_filled_rows(self):
        path = self.mine("bugs.md")
        text = read(path)
        text = text.replace("| 1 | | |", "| 1 | Off by one in the loop bound | Trace the empty input |")
        text = text.replace("| 3 | | |", "| 3 | Forgot to return | Read the last line |")
        write(path, text)
        self.assertEqual(notes.top_bugs(self.paths), [
            {"bug": "Off by one in the loop bound", "check": "Trace the empty input"},
            {"bug": "Forgot to return", "check": "Read the last line"}])

    def test_append_bug_log_adds_one_row_under_log(self):
        path = self.mine("bugs.md")
        before = read(path)
        self.assertTrue(notes.append_bug_log(self.paths, "Mutated while iterating", "Copy first",
                                             "two-sum, 2026-11-12"))
        after = read(path)
        added = [l for l in after.splitlines() if "Mutated while iterating" in l]
        self.assertEqual(added, ["| Mutated while iterating | Copy first | two-sum, 2026-11-12 |"])
        log = after.split("## Log")[1]
        self.assertIn(added[0], log)
        self.assertNotIn(added[0], before.split("## Log")[0])
        self.assertEqual(notes.bug_log(self.paths), ["Mutated while iterating"])
        self.assertEqual(notes.top_bugs(self.paths), [])
        # the first real row takes the template's empty placeholder row, nothing else changes
        self.assertEqual(after.count("\n"), before.count("\n"))
        self.assertTrue(notes.append_bug_log(self.paths, "Second bug", "Check two", "x"))
        self.assertEqual(notes.bug_log(self.paths), ["Second bug", "Mutated while iterating"])

    def test_append_bug_log_without_a_log_table_returns_false_and_touches_nothing(self):
        path = self.mine("bugs.md")
        write(path, "# Bugs\n\n## Log\n\nnothing\n")
        self.assertFalse(notes.append_bug_log(self.paths, "b", "c", "w"))
        self.assertEqual(read(path), "# Bugs\n\n## Log\n\nnothing\n")

    def test_append_bug_log_on_a_crlf_file_keeps_crlf_and_changes_one_line(self):
        path = self.mine("bugs.md")
        text = read(path).replace("\n", "\r\n")
        write(path, text)
        self.assertTrue(notes.append_bug_log(self.paths, "Bug one", "Check one", "where"))
        after = read(path)
        self.assertEqual(after.count("\n"), after.count("\r\n"))
        changes = [l for l in difflib.unified_diff(text.split("\r\n"), after.split("\r\n"), lineterm="", n=0)
                   if l[:1] in "+-" and l[:3] not in ("+++", "---")]
        self.assertEqual(len(changes), 2, changes)
        self.assertEqual(changes[1], "+| Bug one | Check one | where |")
        self.assertTrue(notes.append_bug_log(self.paths, "Bug two", "Check two", "where"))
        after = read(path)
        self.assertEqual(after.count("\n"), after.count("\r\n"))
        self.assertEqual(notes.bug_log(self.paths), ["Bug two", "Bug one"])

    def test_bug_cells_keep_a_literal_pipe(self):
        self.assertTrue(notes.append_bug_log(self.paths, "a | b", "c", "w"))
        self.assertEqual(notes.bug_log(self.paths), ["a | b"])


def marked_cells(line):
    """How a parity-aware GFM renderer (marked, as the app's page uses) splits a table row."""
    body = line.strip()[1:]
    cells, cur, run = [], "", 0
    for ch in body:
        if ch == "|" and run % 2 == 0:
            cells.append(cur)
            cur, run = "", 0
            continue
        cur += ch
        run = run + 1 if ch == "\\" else 0
    if cur.strip():
        cells.append(cur)
    out = []
    for c in cells:
        c = c.strip().replace("\\|", "|")
        out.append(re.sub(r"\\([\\|])", r"\1", c))  # then Markdown's own backslash escapes
    return out


class BackslashPipeTests(NotesCase):
    def test_a_renderer_sees_three_cells_and_the_original_text(self):
        for text in ("a\\|b", "a\\\\|b", "trailing\\", "\\|"):
            os.remove(self.mine("bugs.md"))
            notes.bootstrap(self.paths)
            self.assertTrue(notes.append_bug_log(self.paths, text, "check", "where"))
            row = [l for l in read(self.mine("bugs.md")).split("\n") if l.startswith("| ") and "check" in l][-1]
            self.assertEqual(marked_cells(row), [text, "check", "where"], row)

    def test_bug_cells_round_trip_backslashes_around_pipes(self):
        for text in ("a\\|b", "a\\\\|b", "trailing\\", "\\|", "plain \\ slash", "a | b | c"):
            self.assertTrue(notes.append_bug_log(self.paths, text, "check", "where"), text)
            self.assertEqual(notes.bug_log(self.paths)[0], text)
        self.assertEqual(len(notes.bug_log(self.paths)), 6)

    def test_all_three_cells_survive_a_backslash_before_a_pipe(self):
        self.assertTrue(notes.append_bug_log(self.paths, "x\\|y", "c\\", "w\\\\|z"))
        lines = read(self.mine("bugs.md")).split("\n")
        row = [l for l in lines if l.startswith("| x")][0]
        cells = notes._cells(row)
        self.assertEqual(cells, ["x\\|y", "c\\", "w\\\\|z"])

    def test_matrix_evidence_round_trips_too(self):
        row = notes.read_matrix(self.paths)[0]["rows"][0]["id"]
        self.assertTrue(notes.update_matrix_row(self.paths, row, None, "a\\|b", "2026-11-12"))
        got = [r for g in notes.read_matrix(self.paths) for r in g["rows"] if r["id"] == row][0]
        self.assertEqual(got["evidence"], "a\\|b")
        self.assertEqual(got["last_tested"], "2026-11-12")


class BugLogShapeTests(NotesCase):
    def test_a_table_with_other_columns_gets_nothing_and_a_reason(self):
        path = self.mine("bugs.md")
        text = "# Bugs\n\n## Log\n\n| When | What |\n|---|---|\n| today | thing |\n"
        write(path, text)
        ok, reason = notes.append_bug_log_result(self.paths, "b", "c", "w")
        self.assertFalse(ok)
        self.assertIn("columns", reason)
        self.assertEqual(read(path), text)
        self.assertFalse(notes.append_bug_log(self.paths, "b", "c", "w"))

    def test_the_template_header_and_a_reworded_one_are_accepted(self):
        ok, reason = notes.append_bug_log_result(self.paths, "b", "c", "w")
        self.assertEqual((ok, reason), (True, None))
        path = self.mine("bugs.md")
        write(path, "## Log\n\n| bug | The check that catches it | Where it appeared |\n|---|---|---|\n")
        self.assertTrue(notes.append_bug_log_result(self.paths, "b", "c", "w")[0])

    def test_a_missing_file_is_a_failure_with_a_reason(self):
        os.remove(self.mine("bugs.md"))
        ok, reason = notes.append_bug_log_result(self.paths, "b", "c", "w")
        self.assertFalse(ok)
        self.assertTrue(reason)


class LearningsTests(NotesCase):
    def test_recent_learnings_on_the_template_is_empty(self):
        self.assertEqual(notes.recent_learnings(self.paths), [])

    def test_append_learning_goes_under_entries_newest_first(self):
        path = self.mine("learnings.md")
        before = read(path)
        self.assertTrue(notes.append_learning(self.paths, "2026-11-12", "Slices copy",
                                              "Sliced inside a loop in two-sum.", "A slice is a copy."))
        self.assertTrue(notes.append_learning(self.paths, "2026-11-13", "Mid is floor",
                                              "Binary search looped forever.", "Use lo + (hi - lo) // 2."))
        text = read(path)
        self.assertTrue(text.startswith(before.split("## Entries")[0]))  # everything above is untouched
        self.assertLess(text.index("2026-11-13"), text.index("2026-11-12"))
        self.assertEqual(notes.recent_learnings(self.paths), [
            {"date": "2026-11-13", "title": "Mid is floor", "rule": "Use lo + (hi - lo) // 2."},
            {"date": "2026-11-12", "title": "Slices copy", "rule": "A slice is a copy."}])

    def test_appended_entry_has_the_template_format_exactly(self):
        notes.append_learning(self.paths, "2026-11-12", "Slices copy", "Sliced in a loop.", "A slice is a copy.")
        text = read(self.mine("learnings.md"))
        self.assertTrue(text.endswith(
            "## Entries\n\n### 2026-11-12 — Slices copy\n\n**What happened:** Sliced in a loop.\n\n"
            "**The rule:** A slice is a copy.\n\n"), repr(text[-200:]))

    def test_older_entries_stay_byte_identical_below_the_new_one(self):
        path = self.mine("learnings.md")
        old = "\n### 2026-11-01 [python] — Old fact\n\n**What happened:** x\n\n**The rule:** y\nsecond line of the rule\n"
        write(path, read(path).rstrip("\n") + "\n" + old)
        notes.append_learning(self.paths, "2026-11-12", "New", "w", "r")
        self.assertTrue(read(path).endswith(old))
        got = notes.recent_learnings(self.paths, n=5)
        self.assertEqual([g["title"] for g in got], ["New", "Old fact"])
        self.assertEqual(got[1], {"date": "2026-11-01", "title": "Old fact", "rule": "y second line of the rule"})
        self.assertEqual(len(notes.recent_learnings(self.paths, n=1)), 1)

    def test_default_n_is_three(self):
        for i in range(5):
            notes.append_learning(self.paths, "2026-11-0%d" % (i + 1), "t%d" % i, "w", "r")
        got = notes.recent_learnings(self.paths)
        self.assertEqual([g["title"] for g in got], ["t4", "t3", "t2"])

    def test_the_template_example_blocks_are_not_entries(self):
        self.assertEqual(notes.recent_learnings(self.paths, n=10), [])

    def test_text_cannot_inject_a_heading(self):
        notes.append_learning(self.paths, "2026-11-12", "a\n### 2020-01-01 — fake", "w\n\n## Entries", "r")
        got = notes.recent_learnings(self.paths, n=5)
        self.assertEqual(len(got), 1)

    def test_crlf_is_kept(self):
        path = self.mine("learnings.md")
        write(path, read(path).replace("\n", "\r\n"))
        self.assertTrue(notes.append_learning(self.paths, "2026-11-12", "t", "w", "r"))
        text = read(path)
        self.assertEqual(text.count("\n"), text.count("\r\n"))
        self.assertEqual(notes.recent_learnings(self.paths)[0]["rule"], "r")

    def test_no_entries_heading_or_no_file_returns_false(self):
        path = self.mine("learnings.md")
        write(path, "# Learnings\n")
        self.assertFalse(notes.append_learning(self.paths, "2026-11-12", "t", "w", "r"))
        self.assertEqual(read(path), "# Learnings\n")
        os.remove(path)
        self.assertFalse(notes.append_learning(self.paths, "2026-11-12", "t", "w", "r"))
        self.assertEqual(notes.recent_learnings(self.paths), [])


class UnreadablePathTests(NotesCase):
    def make_dirs(self):
        for name in ("skills-matrix.md", "bugs.md", "learnings.md"):
            os.remove(self.mine(name))
            os.mkdir(self.mine(name))

    def test_a_directory_in_place_of_a_file_is_a_missing_file(self):
        self.make_dirs()
        self.assertEqual(notes.read_matrix(self.paths), [])
        self.assertEqual(notes.top_bugs(self.paths), [])
        self.assertEqual(notes.bug_log(self.paths), [])
        self.assertEqual(notes.recent_learnings(self.paths), [])
        self.assertFalse(notes.update_matrix_row(self.paths, "A6", 1, "x", "2026-11-12"))
        self.assertFalse(notes.append_bug_log(self.paths, "b", "c", "w"))
        self.assertFalse(notes.append_learning(self.paths, "2026-11-12", "f", "w", "r"))

    def test_any_oserror_on_read_is_a_missing_file(self):
        with mock.patch("builtins.open", side_effect=PermissionError("no")):
            self.assertEqual(notes.read_matrix(self.paths), [])
            self.assertFalse(notes.append_learning(self.paths, "2026-11-12", "f", "w", "r"))


class AtomicWriteTests(NotesCase):
    def listing(self):
        return sorted(os.listdir(self.paths.my_prep))

    def test_a_failed_replace_leaves_the_file_untouched_and_returns_false(self):
        calls = [
            lambda: notes.update_matrix_row(self.paths, "A6", 2, "ev", "2026-11-12"),
            lambda: notes.append_bug_log(self.paths, "b", "c", "w"),
            lambda: notes.append_learning(self.paths, "2026-11-12", "f", "w", "r"),
        ]
        names = ("skills-matrix.md", "bugs.md", "learnings.md")
        before = {n: raw(self.mine(n)) for n in names}
        listing = self.listing()
        for name, call in zip(names, calls):
            with self.subTest(name=name):
                with mock.patch("app.prep.notes.os.replace", side_effect=OSError("boom")):
                    self.assertIs(call(), False)
                self.assertEqual(raw(self.mine(name)), before[name])
                self.assertEqual(self.listing(), listing)

    def test_a_failed_write_removes_the_temp_file(self):
        listing = self.listing()
        with mock.patch("app.prep.notes.os.fsync", side_effect=OSError("io")):
            self.assertFalse(notes.append_learning(self.paths, "2026-11-12", "f", "w", "r"))
        self.assertEqual(self.listing(), listing)

    def test_permission_bits_are_preserved(self):
        path = self.mine("learnings.md")
        os.chmod(path, 0o640)
        self.assertTrue(notes.append_learning(self.paths, "2026-11-12", "f", "w", "r"))
        self.assertEqual(stat.S_IMODE(os.stat(path).st_mode), 0o640)
        self.assertFalse([f for f in self.listing() if f.endswith(".tmp")])

    def test_concurrent_appends_lose_nothing(self):
        n = 8
        barrier = threading.Barrier(n)
        results = []

        def work(i):
            barrier.wait()
            results.append(notes.append_learning(self.paths, "2026-11-12", "finding %d" % i,
                                                 "what %d" % i, "rule %d" % i))

        threads = [threading.Thread(target=work, args=(i,)) for i in range(n)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(results, [True] * n)
        titles = sorted(e["title"] for e in notes.recent_learnings(self.paths, n=20))
        self.assertEqual(titles, sorted("finding %d" % i for i in range(n)))
        self.assertFalse([f for f in self.listing() if f.endswith(".tmp")])



class EvidenceMergeTests(unittest.TestCase):
    NEW = "LC 1 Two Sum: passes the app's tests, first try, in 3 min, no hints (app)"

    def test_app_segments_are_replaced_and_hand_text_kept_in_order(self):
        old = "did it on paper; LC 217 Contains Duplicate: 3/9 of the app's tests pass, in 1 min, " \
              "no hints (app); explained it to a friend"
        self.assertEqual(notes.merge_evidence(old, self.NEW),
                         "did it on paper; explained it to a friend; " + self.NEW)

    def test_empty_and_placeholder_cells_become_the_app_segment(self):
        for old in ("", "  ", "?", "-", "\u2014", None):
            self.assertEqual(notes.merge_evidence(old, self.NEW), self.NEW, old)

    def test_hand_text_alone_is_kept(self):
        self.assertEqual(notes.merge_evidence("whiteboard, 20 min", self.NEW),
                         "whiteboard, 20 min; " + self.NEW)


if __name__ == "__main__":
    unittest.main()
