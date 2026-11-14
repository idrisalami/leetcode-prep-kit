// Pure helpers from md.js. Run with: node --test app/static/js/tests/
import test from "node:test";
import assert from "node:assert/strict";
import { slugify, resolveDocLink, stripToc, leetcodeSlug } from "../md.js";

test("slugify follows GitHub's heading-id rule", () => {
  const seen = new Map();
  assert.equal(slugify("0.1 Prerequisites and the one question", seen), "01-prerequisites-and-the-one-question");
  assert.equal(slugify("Primitive 2: the range convention, [lo, hi] or [lo, hi)", seen),
    "primitive-2-the-range-convention-lo-hi-or-lo-hi");
  assert.equal(slugify("Exit condition vs termination: lo < hi or lo <= hi", seen),
    "exit-condition-vs-termination-lo--hi-or-lo--hi");
  assert.equal(slugify("hi = len(nums) or len(nums) - 1?", seen), "hi--lennums-or-lennums---1");
  assert.equal(slugify("Drill set — cold, no IDE, no running", seen), "drill-set--cold-no-ide-no-running");
  assert.equal(slugify("Boundary search: lower_bound and upper_bound", seen),
    "boundary-search-lower_bound-and-upper_bound");
  assert.equal(slugify("Café déjà vu", seen), "café-déjà-vu");
});

test("slugify numbers duplicates -1, -2 and does not reuse a taken slug", () => {
  const seen = new Map();
  assert.equal(slugify("The structure", seen), "the-structure");
  assert.equal(slugify("The structure", seen), "the-structure-1");
  assert.equal(slugify("The structure", seen), "the-structure-2");
  assert.equal(slugify("the-structure-1", seen), "the-structure-1-1");
});

test("slugify without a seen map does not count duplicates", () => {
  assert.equal(slugify("Same"), "same");
  assert.equal(slugify("Same"), "same");
});

test("resolveDocLink routes relative .md links inside the app", () => {
  const base = "course/modules/04-binary-search.md";
  assert.equal(resolveDocLink("00-before-you-start.md#counting-loops", base), "#/module/00?at=counting-loops");
  assert.equal(resolveDocLink("05-linked-lists.md", base), "#/module/05");
  assert.equal(resolveDocLink("../reference/bug-checklist.md#b3", base), "#/doc/course/reference/bug-checklist.md?at=b3");
  assert.equal(resolveDocLink("./../../my-prep/learnings.md", base), "#/doc/my-prep/learnings.md");
  assert.equal(resolveDocLink("#the-three-conditions", base), "#/module/04?at=the-three-conditions");
  assert.equal(resolveDocLink("#x", "course/reference/python-toolkit.md"), "#/doc/course/reference/python-toolkit.md?at=x");
});

test("resolveDocLink leaves absolute and non-Markdown links alone", () => {
  const base = "course/modules/04-binary-search.md";
  assert.equal(resolveDocLink("https://leetcode.com/problems/binary-search/", base), null);
  assert.equal(resolveDocLink("mailto:a@b.c", base), null);
  assert.equal(resolveDocLink("../../app/server.py", base), null);
  assert.equal(resolveDocLink("../../../outside.md", base), null);
});

test("stripToc drops the toc block and keeps everything else", () => {
  const md = "# T\n\n<!-- toc -->\n- [a](#a)\n<!-- /toc -->\n\nBody\n";
  assert.equal(stripToc(md), "# T\n\n\n\nBody\n");
  assert.equal(stripToc("no toc"), "no toc");
});

test("leetcodeSlug reads the problem slug out of a LeetCode URL", () => {
  assert.equal(leetcodeSlug("https://leetcode.com/problems/binary-search/"), "binary-search");
  assert.equal(leetcodeSlug("https://leetcode.com/problems/two-sum/description/"), "two-sum");
  assert.equal(leetcodeSlug("http://www.leetcode.com/problems/sqrtx"), "sqrtx");
  assert.equal(leetcodeSlug("https://example.com/problems/two-sum/"), null);
  assert.equal(leetcodeSlug("05-linked-lists.md"), null);
});
