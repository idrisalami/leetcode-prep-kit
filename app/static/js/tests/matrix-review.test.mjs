// Pure helpers of the Review hub (matrix.js). Run with:
// node --test "app/static/js/tests/*.test.mjs"
import test from "node:test";
import assert from "node:assert/strict";
import {
  parseLevel, levelBar, sectionOf, flattenRows, filterSection, sortRows, priorityRank,
  practiseTarget, evidenceAge, allUnknown, normalizeView, viewToQuery, sectionCounts,
} from "../matrix.js";

const row = (id, now, priority = "P0", extra = {}) => ({ id, requirement: id + " skill", module: "01",
  priority, start: "?", now, evidence: "", last_tested: "", practise: null, ...extra });

test("parseLevel reads 0 to 3 and nothing else", () => {
  assert.equal(parseLevel("0"), 0);
  assert.equal(parseLevel(" 3 "), 3);
  assert.equal(parseLevel("**2**"), 2);
  assert.equal(parseLevel("`1`"), 1);
  for (const bad of ["?", "", null, undefined, "4", "2-3", "1 → 2", "two", "-1"]) {
    assert.equal(parseLevel(bad), null, String(bad));
  }
});

test("levelBar fills one segment per level and always carries a text label", () => {
  assert.deepEqual(levelBar("2"), { level: 2, known: true, filled: [true, true, false], text: "2",
    label: "level 2 of 3" });
  assert.deepEqual(levelBar("0"), { level: 0, known: true, filled: [false, false, false], text: "0",
    label: "level 0 of 3" });
  assert.deepEqual(levelBar("?"), { level: null, known: false, filled: [false, false, false], text: "?",
    label: "not tested yet" });
  assert.deepEqual(levelBar("2-3"), { level: null, known: false, filled: [false, false, false], text: "?",
    label: "not a level the app can read: 2-3" });
});

test("sectionOf maps the row letter to a chip", () => {
  assert.equal(sectionOf({ id: "A1" }), "topics");
  assert.equal(sectionOf({ id: "A18" }), "topics");
  assert.equal(sectionOf({ id: "B3" }), "habits");
  assert.equal(sectionOf({ id: "C10" }), "communication");
  assert.equal(sectionOf({ id: "D1" }), "other");
});

const GROUPS = [
  { title: "A. Topics", rows: [row("A1", "3"), row("A2", "?", "P1"), row("A3", "1", "P1"), row("A4", "1")] },
  { title: "B. Craft", rows: [row("B1", "2")] },
  { title: "Problem solving", rows: [row("C1", "0")] },
  { title: "Communication", rows: [row("C6", "?")] },
];

test("flattenRows keeps file order, the group title and an index", () => {
  const rows = flattenRows(GROUPS);
  assert.deepEqual(rows.map((r) => r.id), ["A1", "A2", "A3", "A4", "B1", "C1", "C6"]);
  assert.equal(rows[5].group, "Problem solving");
  assert.deepEqual(rows.map((r) => r.index), [0, 1, 2, 3, 4, 5, 6]);
  assert.deepEqual(flattenRows(null), []);
});

test("filterSection and sectionCounts", () => {
  const rows = flattenRows(GROUPS);
  assert.deepEqual(filterSection(rows, "communication").map((r) => r.id), ["C1", "C6"]);
  assert.deepEqual(sectionCounts(rows), { topics: 4, habits: 1, communication: 2, other: 0 });
});

test("priorityRank: P0 < P1 < P2 < anything else", () => {
  assert.ok(priorityRank("P0") < priorityRank("P1"));
  assert.ok(priorityRank("P1") < priorityRank("P2"));
  assert.ok(priorityRank("P2") < priorityRank("set at discovery"));
  assert.equal(priorityRank(" p1 "), priorityRank("P1"));
});

test("sortRows file order is the input order", () => {
  const rows = flattenRows(GROUPS);
  assert.deepEqual(sortRows(rows, "file").map((r) => r.id), ["A1", "A2", "A3", "A4", "B1", "C1", "C6"]);
});

test("sortRows weakest first: lowest level, then priority, then file order; unknown last", () => {
  const rows = flattenRows(GROUPS);
  const out = sortRows(rows, "weakest").map((r) => r.id);
  // C1 is 0; A4 (P0) before A3 (P1) at level 1; B1 2; A1 3; then the unknown rows, which
  // follow the same priority rule: C6 (P0) before A2 (P1).
  assert.deepEqual(out, ["C1", "A4", "A3", "B1", "A1", "C6", "A2"]);
  // The input is not modified.
  assert.deepEqual(rows.map((r) => r.id), ["A1", "A2", "A3", "A4", "B1", "C1", "C6"]);
});

test("sortRows weakest first is stable for equal keys", () => {
  const rows = flattenRows([{ title: "", rows: [row("A1", "1"), row("A2", "1"), row("A3", "1"), row("A4", "1")] }]);
  assert.deepEqual(sortRows(rows, "weakest").map((r) => r.id), ["A1", "A2", "A3", "A4"]);
});

test("practiseTarget names the problem and what the click does", () => {
  const by = new Map([
    ["two-sum", { slug: "two-sum", title: "Two Sum", status: "new" }],
    ["valid-anagram", { slug: "valid-anagram", title: "Valid Anagram", status: "attempted" }],
    ["contains-duplicate", { slug: "contains-duplicate", title: "Contains Duplicate", status: "solved" }],
  ]);
  assert.deepEqual(practiseTarget({ practise: "two-sum" }, by),
    { slug: "two-sum", title: "Two Sum", status: "new", kind: "next" });
  assert.deepEqual(practiseTarget({ practise: "valid-anagram" }, by),
    { slug: "valid-anagram", title: "Valid Anagram", status: "attempted", kind: "continue" });
  assert.deepEqual(practiseTarget({ practise: "contains-duplicate" }, by),
    { slug: "contains-duplicate", title: "Contains Duplicate", status: "solved", kind: "oldest" });
  assert.deepEqual(practiseTarget({ practise: null }, by), { slug: null, kind: "none" });
  assert.deepEqual(practiseTarget({}, by), { slug: null, kind: "none" });
  // A slug the problem list does not know still goes somewhere, with the slug as its name.
  assert.deepEqual(practiseTarget({ practise: "lost-one" }, by),
    { slug: "lost-one", title: "lost-one", status: "new", kind: "next" });
});

test("evidenceAge says how long ago and flags a revisit after 14 days", () => {
  const today = "2024-03-20";
  assert.deepEqual(evidenceAge("2024-03-20", today), { days: 0, text: "today", due: false });
  assert.deepEqual(evidenceAge("2024-03-19", today), { days: 1, text: "yesterday", due: false });
  assert.deepEqual(evidenceAge("2024-03-07", today), { days: 13, text: "13 days ago", due: false });
  assert.deepEqual(evidenceAge("2024-03-06", today), { days: 14, text: "14 days ago", due: true });
  assert.deepEqual(evidenceAge("2024-02-20", today), { days: 29, text: "29 days ago", due: true });
  assert.equal(evidenceAge("", today), null);
  assert.equal(evidenceAge("<YYYY-MM-DD>", today), null);
  assert.equal(evidenceAge("2024-03-25", today), null);
});

test("allUnknown is true for no rows and for rows that are all ?", () => {
  assert.equal(allUnknown([]), true);
  assert.equal(allUnknown([row("A1", "?"), row("A2", "")]), true);
  assert.equal(allUnknown([row("A1", "?"), row("A2", "0")]), false);
});

test("normalizeView and viewToQuery", () => {
  assert.deepEqual(normalizeView({}), { section: "topics", sort: "file" });
  assert.deepEqual(normalizeView({ view: "habits", sort: "weakest" }), { section: "habits", sort: "weakest" });
  assert.deepEqual(normalizeView({ view: "nope", sort: "random" }), { section: "topics", sort: "file" });
  assert.deepEqual(normalizeView(null), { section: "topics", sort: "file" });
  assert.equal(viewToQuery({ section: "topics", sort: "file" }), "");
  assert.equal(viewToQuery({ section: "communication", sort: "weakest" }), "view=communication&sort=weakest");
});
