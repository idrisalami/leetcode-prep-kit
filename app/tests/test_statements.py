"""Statements: LeetCode GraphQL and NeetCode page parsing, and the downloader (no network)."""
from __future__ import annotations

import json
import os
import unittest
import urllib.error
from unittest import mock

from app.prep import catalog, statements
from app.tests.kit import make_kit, prob

NC_HTML = """<!doctype html><html><head><title>x</title>
<script type="application/json" id="other">{"problem-islands-and-treasure": {"description": "wrong"}}</script>
</head><body><app-root></app-root>
<script id="ng-state" type="application/json">{"problem-islands-and-treasure":{"id":"islands-and-treasure",
"name":"Islands and Treasure","description":"You are given a grid.\\n\\n**Example 1:**\\n\\n```\\nInput: grid = [[0]]\\n```\\n","solutions":{"python":"do not keep"}},"__nghData__":[]}</script>
</body></html>"""

LC_JSON = json.dumps({"data": {"question": {"content": "<p>Given an array of integers.</p>"}}})


def premium(slug, module="08"):
    p = prob(slug, module, "Medium")
    p["premium"] = True
    p["statement_source"] = "neetcode"
    return p


class ParseTests(unittest.TestCase):
    def test_parse_neetcode(self):
        body = statements.parse_neetcode(NC_HTML, "islands-and-treasure")
        self.assertTrue(body.startswith("You are given a grid."))
        self.assertIn("Input: grid = [[0]]", body)

    def test_parse_neetcode_misses(self):
        self.assertIsNone(statements.parse_neetcode(NC_HTML, "valid-tree"))
        self.assertIsNone(statements.parse_neetcode("<html></html>", "islands-and-treasure"))
        broken = NC_HTML.replace('"__nghData__":[]}', '"__nghData__":[')
        self.assertIsNone(statements.parse_neetcode(broken, "islands-and-treasure"))
        empty = NC_HTML.replace('"description":"You are given', '"description":"","x":"')
        self.assertIsNone(statements.parse_neetcode(empty, "islands-and-treasure"))

    def test_parse_neetcode_drops_details_blocks(self):
        def page(desc):
            state = {"problem-islands-and-treasure": {"description": desc}}
            return '<script id="ng-state" type="application/json">%s</script>' % json.dumps(state)
        desc = ('Find the thing.\n\n<details class="hint"><summary>Topics</summary>\n\nGrid\n'
                '<details><summary>inner</summary>x</details>\n</details>\n\n'
                '**Example 1:**\n\n<DETAILS>\n<summary>Hint 1</summary>try BFS</DETAILS>\nEnd.')
        self.assertEqual(statements.parse_neetcode(page(desc), "islands-and-treasure"),
                         "Find the thing.\n\n**Example 1:**\n\nEnd.")
        only = "<details><summary>Topics</summary>x</details>"
        self.assertIsNone(statements.parse_neetcode(page(only), "islands-and-treasure"))

    def test_parse_leetcode(self):
        self.assertEqual(statements.parse_leetcode(LC_JSON.encode()),
                         "<p>Given an array of integers.</p>")
        self.assertIsNone(statements.parse_leetcode(b'{"data": {"question": null}}'))
        self.assertIsNone(statements.parse_leetcode(b'{"errors": [{"message": "x"}]}'))
        self.assertIsNone(statements.parse_leetcode(b"<html>blocked</html>"))
        self.assertIsNone(statements.parse_leetcode(b'{"data": {"question": {"content": null}}}'))

    def test_slug_pairs(self):
        self.assertEqual(statements.NC_SLUGS, {
            "encode-and-decode-strings": "string-encode-and-decode",
            "walls-and-gates": "islands-and-treasure",
            "graph-valid-tree": "valid-tree",
            "number-of-connected-components-in-an-undirected-graph": "count-connected-components",
            "alien-dictionary": "foreign-dictionary"})


class FakeOpener:
    def __init__(self, fail=()):
        self.requests = []
        self.fail = set(fail)

    def __call__(self, req, timeout):
        self.requests.append(req)
        if req.full_url.startswith("https://neetcode.io/"):
            if "islands-and-treasure" in self.fail:
                raise urllib.error.URLError("no route")
            return NC_HTML.encode()
        slug = json.loads(req.data.decode())["variables"]["s"]
        if slug in self.fail:
            raise urllib.error.HTTPError(req.full_url, 403, "Forbidden", {}, None)
        if slug == "empty-one":
            return b'{"data": {"question": null}}'
        return LC_JSON.encode()


class FetchAllTests(unittest.TestCase):
    def setUp(self):
        problems = [prob("two-sum", "01"), prob("group-anagrams", "01"),
                    prob("empty-one", "01"), premium("walls-and-gates")]
        self.paths = make_kit(self, problems=problems, with_course=False)
        self.catalog = catalog.Catalog(self.paths)
        self.sleeps = []
        self.lines = []

    def run_all(self, opener, **kw):
        return statements.fetch_all(self.paths, self.catalog, opener=opener,
                                    sleep=self.sleeps.append,
                                    progress=lambda *a: self.lines.append(a), **kw)

    def test_fetches_everything_missing_and_records_failures(self):
        opener = FakeOpener(fail={"group-anagrams"})
        out = self.run_all(opener)
        self.assertEqual(out, {"have": 2, "total": 4, "failed": ["group-anagrams", "empty-one"]})
        with open(os.path.join(self.paths.statements_dir, "two-sum.json"), encoding="utf-8") as fh:
            saved = json.load(fh)
        self.assertEqual(set(saved), {"slug", "format", "body", "source", "fetched_at"})
        self.assertEqual((saved["slug"], saved["format"], saved["source"]),
                         ("two-sum", "html", "leetcode"))
        nc = self.catalog.statement("walls-and-gates")
        self.assertEqual((nc["format"], nc["source"]), ("markdown", "neetcode"))
        self.assertNotIn("do not keep", json.dumps(nc))
        self.assertEqual([a[0] for a in self.lines],
                         ["two-sum", "group-anagrams", "empty-one", "walls-and-gates"])
        self.assertEqual([a[1] for a in self.lines], ["ok", "failed", "failed", "ok"])
        self.assertTrue(all(s == 0.7 for s in self.sleeps))
        self.assertGreaterEqual(len(self.sleeps), 2)

    def test_requests_carry_only_the_spec_headers(self):
        opener = FakeOpener()
        self.run_all(opener, only=["two-sum", "walls-and-gates"])
        lc, nc = opener.requests
        self.assertEqual(lc.full_url, "https://leetcode.com/graphql")
        self.assertEqual(lc.get_method(), "POST")
        self.assertEqual(dict(lc.header_items()),
                         {"Content-type": "application/json", "User-agent": "Mozilla/5.0",
                          "Referer": "https://leetcode.com/problemset/"})
        self.assertEqual(json.loads(lc.data.decode()),
                         {"query": "query q($s:String!){question(titleSlug:$s){content}}",
                          "variables": {"s": "two-sum"}})
        self.assertEqual(nc.full_url, "https://neetcode.io/problems/islands-and-treasure/question")
        self.assertEqual(nc.get_method(), "GET")
        self.assertEqual(dict(nc.header_items()), {"User-agent": "Mozilla/5.0"})

    def test_only_missing_skips_what_is_there(self):
        self.run_all(FakeOpener())
        opener = FakeOpener()
        self.lines.clear()
        out = self.run_all(opener)
        self.assertEqual([json.loads(r.data.decode())["variables"]["s"] for r in opener.requests],
                         ["empty-one"])
        self.assertEqual(out["have"], 3)
        self.assertEqual(out["failed"], ["empty-one"])
        self.assertIn(("two-sum", "have", ""), self.lines)

    def test_a_failure_of_everything_never_raises(self):
        def broken(req, timeout):
            raise OSError("network down")
        out = self.run_all(broken)
        self.assertEqual(out["have"], 0)
        self.assertEqual(len(out["failed"]), 4)

    def test_unknown_only_slug_is_failed(self):
        out = self.run_all(FakeOpener(), only=["two-sum", "no-such-problem"])
        self.assertEqual(out["failed"], ["no-such-problem"])



class SizeCapTests(unittest.TestCase):
    def test_an_oversized_response_is_refused_before_parsing(self):
        class Resp:
            def __init__(self, size):
                self.size = size
                self.asked = []

            def read(self, n=-1):
                self.asked.append(n)
                return b"x" * (self.size if n is None or n < 0 else min(n, self.size))

            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

        big = Resp(statements.MAX_RESPONSE + 10)
        with mock.patch("urllib.request.urlopen", return_value=big):
            with self.assertRaises(ValueError):
                statements._urlopen(statements._neetcode_request("x"), 1)
        self.assertEqual(big.asked, [statements.MAX_RESPONSE + 1])
        small = Resp(100)
        with mock.patch("urllib.request.urlopen", return_value=small):
            self.assertEqual(len(statements._urlopen(statements._neetcode_request("x"), 1)), 100)


if __name__ == "__main__":
    unittest.main()
