"""The committed catalog: problems.json, the tests files, and the Catalog/Paths views of them."""
from __future__ import annotations

import __future__ as future_flags
import json
import os
import shutil
import tempfile
import unittest

from app.prep import catalog, paths

MODULE_COUNTS = {"01": 9, "02": 6, "03": 11, "04": 7, "05": 11, "06": 15, "07": 10, "08": 19,
                 "09": 23, "10": 7}
BANNED_KEYS = {"content", "description", "statement"}


def fill_bodies(src):
    """Insert `pass` under every block opener whose body is empty, as a stub editor would."""
    lines = src.split("\n")
    out = []
    for i, line in enumerate(lines):
        out.append(line)
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or not stripped.endswith(":"):
            continue
        indent = len(line) - len(line.lstrip())
        following = [l for l in lines[i + 1:] if l.strip() and not l.strip().startswith("#")]
        if not following or len(following[0]) - len(following[0].lstrip()) <= indent:
            out.append(" " * (indent + 4) + "pass")
    return "\n".join(out)


def keys_in(value):
    if isinstance(value, dict):
        for k, v in value.items():
            yield k
            yield from keys_in(v)
    elif isinstance(value, list):
        for v in value:
            yield from keys_in(v)


class CatalogDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.paths = paths.default()
        cls.cat = catalog.Catalog(cls.paths)

    def test_default_root_is_the_kit(self):
        self.assertTrue(os.path.isdir(os.path.join(self.paths.root, "course")))
        self.assertTrue(os.path.isfile(os.path.join(self.paths.data, "problems.json")))

    def test_118_problems_with_unique_slugs(self):
        problems = self.cat.problems()
        self.assertEqual(len(problems), 118)
        self.assertEqual(len({p["slug"] for p in problems}), 118)

    def test_module_counts(self):
        self.assertEqual(self.cat.module_ids(), sorted(MODULE_COUNTS))
        self.assertEqual({m: len(self.cat.by_module(m)) for m in self.cat.module_ids()}, MODULE_COUNTS)

    def test_entries_have_the_spec_keys(self):
        keys = {"slug", "number", "title", "difficulty", "module", "category", "url", "premium",
                "statement_source", "skeleton"}
        for p in self.cat.problems():
            self.assertLessEqual(keys, set(p), p["slug"])
            self.assertEqual(p["premium"], "alt_url" in p, p["slug"])
        self.assertEqual(sum(1 for p in self.cat.problems() if p["premium"]), 5)

    def test_every_problem_has_a_tests_file_with_an_example(self):
        for p in self.cat.problems():
            spec = self.cat.spec(p["slug"])
            self.assertEqual(spec["slug"], p["slug"])
            self.assertTrue(any(c.get("example") for c in spec["cases"]), p["slug"])
            self.assertTrue(self.cat.examples(p["slug"]), p["slug"])

    def test_tests_files_match_problems(self):
        files = {f[:-5] for f in os.listdir(self.paths.tests_dir) if f.endswith(".json")}
        self.assertEqual(files, {p["slug"] for p in self.cat.problems()})

    def test_skeletons_compile(self):
        for p in self.cat.problems():
            src = fill_bodies(p["skeleton"])
            try:
                compile(src, "solution.py", "exec", flags=future_flags.annotations.compiler_flag,
                        dont_inherit=True)
            except SyntaxError as exc:
                self.fail("%s: %s" % (p["slug"], exc))

    def test_class_and_method_appear_in_skeleton(self):
        for p in self.cat.problems():
            spec = self.cat.spec(p["slug"])
            self.assertIn("class %s" % spec["class"], p["skeleton"], p["slug"])
            if spec["driver"] != "design":
                self.assertIn("def %s(" % spec["method"], p["skeleton"], p["slug"])

    def test_drivers_and_compare_modes_are_known(self):
        drivers = {"function", "design", "cycle", "random_list", "clone_graph", "lca",
                   "codec_strings", "codec_tree"}
        modes = {"exact", "unordered", "unordered_nested", "float", "checker:topo_order",
                 "checker:palindrome_substring", "checker:alien_order"}
        for p in self.cat.problems():
            spec = self.cat.spec(p["slug"])
            self.assertIn(spec["driver"], drivers, p["slug"])
            self.assertIn(spec.get("compare", "exact"), modes, p["slug"])

    def test_no_statement_text_keys_in_committed_data(self):
        for folder, _, files in os.walk(self.paths.data):
            if os.path.abspath(folder).startswith(os.path.abspath(self.paths.statements_dir)):
                continue  # git-ignored download folder
            for name in files:
                if not name.endswith(".json"):
                    continue
                with open(os.path.join(folder, name), encoding="utf-8") as fh:
                    found = BANNED_KEYS & set(keys_in(json.load(fh)))
                self.assertEqual(found, set(), name)

    def test_get_unknown_slug_raises(self):
        with self.assertRaises(KeyError):
            self.cat.get("no-such-problem")
        with self.assertRaises(KeyError):
            self.cat.spec("../problems")

    def test_examples_are_display_strings(self):
        first = self.cat.examples("two-sum")[0]
        self.assertEqual(first["name"], "Example 1")
        self.assertEqual(first["input"], "nums = [2,7,11,15], target = 9")
        self.assertEqual(first["expected"], "[0,1]")


class TempRootTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="prep-cat-")
        self.addCleanup(shutil.rmtree, self.root, True)
        real = paths.default()
        shutil.copytree(real.data, os.path.join(self.root, "app", "data"),
                        ignore=shutil.ignore_patterns("statements"))
        self.paths = paths.Paths(self.root)
        self.cat = catalog.Catalog(self.paths)

    def test_paths_layout(self):
        p = self.paths
        self.assertEqual(p.state_file, os.path.join(self.root, "my-prep", "app", "state.json"))
        self.assertEqual(p.solutions_dir, os.path.join(self.root, "my-prep", "solutions"))
        self.assertEqual(p.templates, os.path.join(self.root, "course", "templates"))
        self.assertEqual(p.statements_dir, os.path.join(self.root, "app", "data", "statements"))
        self.assertEqual(p.static, os.path.join(self.root, "app", "static"))

    def test_statement_missing_then_present(self):
        self.assertIsNone(self.cat.statement("two-sum"))
        self.assertEqual(self.cat.statements_have(), 0)
        os.makedirs(self.paths.statements_dir)
        record = {"slug": "two-sum", "format": "html", "body": "<p>x</p>", "source": "leetcode",
                  "fetched_at": "2026-01-01T00:00:00Z"}
        with open(os.path.join(self.paths.statements_dir, "two-sum.json"), "w") as fh:
            json.dump(record, fh)
        with open(os.path.join(self.paths.statements_dir, "3sum.json"), "w") as fh:
            fh.write("{not json")
        self.assertEqual(self.cat.statement("two-sum"), record)
        self.assertIsNone(self.cat.statement("3sum"))
        self.assertEqual(self.cat.statements_have(), 1)


if __name__ == "__main__":
    unittest.main()
