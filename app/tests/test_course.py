"""Course: module list, reference list, notes docs and the read-only document whitelist."""
from __future__ import annotations

import os
import tempfile
import unittest

from app.prep import course, notes
from app.tests.kit import make_kit


class CourseTests(unittest.TestCase):
    def setUp(self):
        self.paths = make_kit(self)

    def test_eleven_modules_with_titles_minus_the_prefix(self):
        mods = course.modules(self.paths)
        self.assertEqual([m["id"] for m in mods], ["%02d" % i for i in range(11)])
        titles = {m["id"]: m["title"] for m in mods}
        self.assertEqual(titles["00"], "Before you start")
        self.assertEqual(titles["01"], "Arrays and hashing")
        self.assertEqual(titles["04"], "Binary search")
        self.assertEqual(titles["10"], "Heaps, top-K and selection")
        self.assertEqual(mods[4]["path"], "course/modules/04-binary-search.md")

    def test_prefix_with_an_em_dash_is_also_removed(self):
        path = os.path.join(self.paths.course, "modules", "04-binary-search.md")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("# Module 4 — Binary search\n")
        self.assertEqual(course.modules(self.paths)[4]["title"], "Binary search")

    def test_reference_lists_the_reference_files(self):
        ref = course.reference(self.paths)
        self.assertEqual([r["path"] for r in ref], ["course/reference/bug-checklist.md",
                                                    "course/reference/decision-rules.md",
                                                    "course/reference/python-toolkit.md"])
        self.assertEqual(ref[2]["title"], "The Python toolkit")

    def test_notes_docs_in_order_with_exists(self):
        docs = course.notes_docs(self.paths)
        self.assertEqual([d["key"] for d in docs], ["skills-matrix", "bugs", "learnings", "plan",
                                                    "next-session", "profile", "diagnostic-report"])
        self.assertTrue(all(not d["exists"] for d in docs))
        notes.bootstrap(self.paths)
        docs = course.notes_docs(self.paths)
        self.assertTrue(all(d["exists"] for d in docs))
        self.assertEqual(docs[0], {"key": "skills-matrix", "title": "Skills matrix",
                                   "path": "my-prep/skills-matrix.md", "exists": True,
                                   "is_template": True})

    def test_is_template_is_true_only_for_a_byte_identical_copy(self):
        docs = {d["key"]: d for d in course.notes_docs(self.paths)}
        self.assertTrue(all(d["is_template"] is False for d in docs.values()), "no files yet")
        notes.bootstrap(self.paths)
        docs = {d["key"]: d for d in course.notes_docs(self.paths)}
        self.assertTrue(all(d["is_template"] is True for d in docs.values()))
        with open(os.path.join(self.paths.my_prep, "plan.md"), "ab") as fh:
            fh.write(b"one more line\n")
        docs = {d["key"]: d for d in course.notes_docs(self.paths)}
        self.assertIs(docs["plan"]["is_template"], False)
        self.assertIs(docs["bugs"]["is_template"], True)
        self.assertEqual(set(docs["plan"]), {"key", "title", "path", "exists", "is_template"})

    def test_a_file_over_two_megabytes_is_too_large(self):
        os.makedirs(self.paths.my_prep)
        path = os.path.join(self.paths.my_prep, "big.md")
        with open(path, "wb") as fh:
            fh.write(b"# Big\n" + b"x" * (course.MAX_DOC - 6))
        self.assertEqual(len(course.read_doc(self.paths, "my-prep/big.md")["markdown"]), course.MAX_DOC)
        with open(path, "ab") as fh:
            fh.write(b"x")
        with self.assertRaises(course.TooLarge):
            course.read_doc(self.paths, "my-prep/big.md")

    def test_read_doc(self):
        doc = course.read_doc(self.paths, "course/modules/04-binary-search.md")
        self.assertEqual(doc["path"], "course/modules/04-binary-search.md")
        self.assertEqual(doc["title"], "Module 04: Binary search")
        self.assertTrue(doc["markdown"].startswith("# Module 04"))
        self.assertEqual(course.read_doc(self.paths, "course/README.md")["title"], "The course")

    def test_read_doc_in_my_prep_and_title_fallback(self):
        notes.bootstrap(self.paths)
        self.assertEqual(course.read_doc(self.paths, "my-prep/plan.md")["title"], "Plan")
        with open(os.path.join(self.paths.my_prep, "lessons", "x.md"), "w", encoding="utf-8") as fh:
            fh.write("no heading here\n")
        self.assertEqual(course.read_doc(self.paths, "my-prep/lessons/x.md")["title"], "x")

    def test_missing_files_are_not_found(self):
        for rel in ("course/modules/99-nothing.md", "my-prep/plan.md"):
            with self.assertRaises(course.NotFound, msg=rel):
                course.read_doc(self.paths, rel)

    def test_outside_the_whitelist_is_forbidden(self):
        os.makedirs(os.path.join(self.paths.my_prep, "app"))
        with open(self.paths.state_file, "w", encoding="utf-8") as fh:
            fh.write("{}")
        for rel in ("../README.md", "/etc/passwd", "course/../app/server.py", "my-prep/app/state.json",
                    "app/prep/store.py", "README.md", "CLAUDE.md", "course/modules/../../README.md",
                    "course\\..\\README.md", "course/modules/04-binary-search.md\x00.png",
                    "course/README.txt", "", "my-prep", "course", "my-prep/../course/README.md"):
            with self.assertRaises(course.Forbidden, msg=repr(rel)):
                course.read_doc(self.paths, rel)

    def test_a_symlink_escaping_the_root_is_forbidden(self):
        # a second temp dir, outside the kit root altogether: a root escape, not only a whitelist miss
        outside_tmp = tempfile.TemporaryDirectory()
        self.addCleanup(outside_tmp.cleanup)
        outside_dir = outside_tmp.name
        self.assertFalse(os.path.realpath(outside_dir).startswith(os.path.realpath(self.paths.root) + os.sep))
        outside = os.path.join(outside_dir, "secret.md")
        with open(outside, "w", encoding="utf-8") as fh:
            fh.write("secret\n")
        os.makedirs(self.paths.my_prep)
        os.symlink(outside, os.path.join(self.paths.my_prep, "leak.md"))
        os.symlink(outside_dir, os.path.join(self.paths.course, "linked-dir"))
        for rel in ("my-prep/leak.md", "course/linked-dir/secret.md"):
            with self.assertRaises(course.Forbidden, msg=rel):
                course.read_doc(self.paths, rel)

    def test_a_symlink_to_a_kit_file_outside_the_whitelist_is_forbidden(self):
        os.makedirs(self.paths.my_prep)
        os.symlink(os.path.join(self.paths.data, "problems.json"), os.path.join(self.paths.my_prep, "p.md"))
        with self.assertRaises(course.Forbidden):
            course.read_doc(self.paths, "my-prep/p.md")


if __name__ == "__main__":
    unittest.main()
