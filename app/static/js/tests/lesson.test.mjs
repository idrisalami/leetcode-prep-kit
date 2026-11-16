// Pure classifiers for the lesson pages. Run with: node --test "app/static/js/tests/*.test.mjs"
import test from "node:test";
import assert from "node:assert/strict";
import {
  classifyCallout, bigOClass, countWords, readingMinutes, pairSelfCheck, tallyText,
  progressLine, countsAsSection, newlyRead, parseStored, load, store,
  splitTokenLines, lineMark, eyebrowText, splitH2Number, cellBadge,
} from "../lesson.js";

test("classifyCallout follows the spec table", () => {
  const c = (o) => classifyCallout({ first: "text", text: "", bold: "", h2: "", ...o });
  assert.deepEqual(c({ text: "⚠️ You'll see this again in module 07.", bold: "You'll see this again in module 07." }),
    { kind: "pointer", label: "Comes back later in module 07" });
  assert.deepEqual(c({ text: "⚠ You’ll see it again.", bold: "You’ll see it again." }),
    { kind: "pointer", label: "Comes back later" });
  assert.deepEqual(c({ first: "strong", text: "⚠ The bug: advancing prev", bold: "The bug:" }),
    { kind: "trap", label: "Heads up" });
  assert.equal(c({ first: "em", text: "What is the invariant?", h2: "0.1 The one question" }).kind, "question");
  assert.equal(c({ first: "em", text: "What is the invariant?", h2: "0.1 The one question" }).label, "The one question");
  assert.equal(c({ first: "em", text: "“I'll use two pointers…”", h2: "0.4 Patterns" }).kind, "say");
  assert.equal(c({ first: "em", text: "“I'll use two pointers…”", h2: "0.4 Patterns" }).label, "Say it like this");
  assert.equal(c({ first: "em", text: "just a note", h2: "0.4 Patterns" }).kind, "plain");
  assert.deepEqual(c({ first: "strong", text: "Once P becomes true…", bold: "Once P becomes true" }),
    { kind: "rule", label: "Key idea" });
  assert.deepEqual(c({ text: "plain words" }), { kind: "plain", label: "" });
});

test("bigOClass tiers", () => {
  const cases = { "O(1)": "fast", "O(log n)": "fast", "O(log(n))": "fast", "O(log R)": "fast",
    "O(n)": "mid", "O(n + m)": "mid", "O(n log n)": "mid", "O(k log n)": "mid", "O(min(n, m))": "mid",
    "O(V + E)": "mid", "O(n) amortised": "mid", "O(n^2)": "steep", "O(n²)": "steep", "O(2^n)": "steep",
    "O(n!)": "steep", "O(n*m)": "steep", "O(nm)": "steep", "O(n·m)": "steep", "O(m × n)": "steep" };
  for (const [s, want] of Object.entries(cases)) assert.equal(bigOClass(s), want, s);
  for (const s of ["n log n", "O", "lo(1)", "O(n) time and O(1) space"]) assert.equal(bigOClass(s), null, s);
});

test("countWords", () => {
  assert.equal(countWords(""), 0);
  assert.equal(countWords("  one two\nthree  "), 3);
});

test("readingMinutes", () => {
  assert.equal(readingMinutes(0, 0), 1);
  assert.equal(readingMinutes(200, 0), 1);
  assert.equal(readingMinutes(201, 0), 2);
  assert.equal(readingMinutes(300, 200), 2);
  assert.equal(readingMinutes(400, 1), 3);
});

test("pairSelfCheck", () => {
  assert.deepEqual(pairSelfCheck(["q1", "q2"], ["a1", "a2"]), [["q1", "a1"], ["q2", "a2"]]);
  assert.equal(pairSelfCheck([], []), null);
  assert.equal(pairSelfCheck(["q1"], []), null);
  assert.equal(pairSelfCheck(["q1", "q2"], ["a1"]), null);
});

test("tallyText", () => {
  assert.equal(tallyText({ 0: "got", 1: "got", 2: "missed" }, 8), "2 of 8 got · 1 missed");
  assert.equal(tallyText({}, 8), "0 of 8 got");
  assert.equal(tallyText({ 3: "got" }, 8), "1 of 8 got");
});

test("progressLine", () => {
  assert.equal(progressLine({ read: 3, total: 11, drills: { solved: 4, count: 9 } }), "3 of 11 sections read · 4/9 drills");
  assert.equal(progressLine({ read: 3, total: 11, drills: null }), "3 of 11 sections read");
});

test("countsAsSection", () => {
  assert.equal(countsAsSection("Self-check answers"), false);
  assert.equal(countsAsSection("self-check answers"), false);
  assert.equal(countsAsSection("Drill set"), true);
  assert.equal(countsAsSection("0.9 Self-check"), true);
});

test("newlyRead", () => {
  const ends = [{ id: "a", top: 100 }, { id: "b", top: 900 }, { id: "c", top: 50 }];
  assert.deepEqual(newlyRead(ends, 800, new Set(["c"])), ["a"]);
});

test("parseStored and load survive bad storage", () => {
  assert.deepEqual(parseStored("{bad", {}), {});
  assert.deepEqual(parseStored(null, []), []);
  assert.deepEqual(parseStored('["a"]', []), ["a"]);
  const saved = globalThis.localStorage;
  globalThis.localStorage = { getItem() { throw new Error("denied"); }, setItem() { throw new Error("denied"); } };
  assert.deepEqual(load("prep:read:x", []), []);
  assert.doesNotThrow(() => store("prep:read:x", ["a"]));
  delete globalThis.localStorage;
  assert.deepEqual(load("prep:read:x", ["fb"]), ["fb"]);
  assert.doesNotThrow(() => store("prep:read:x", ["a"]));
  globalThis.localStorage = saved;
});

test("load and store round-trip through a working storage", () => {
  const saved = globalThis.localStorage;
  const mem = new Map();
  globalThis.localStorage = { getItem: (k) => (mem.has(k) ? mem.get(k) : null), setItem: (k, v) => mem.set(k, String(v)) };
  store("prep:selfcheck:x", { 0: "got" });
  assert.deepEqual(load("prep:selfcheck:x", {}), { 0: "got" });
  globalThis.localStorage = saved;
});

test("splitTokenLines splits at newlines and keeps a token's class on both sides", () => {
  const lines = splitTokenLines([
    { cls: "cm-keyword", text: "def" }, { cls: null, text: " f():\n    " },
    { cls: "cm-string", text: '"""a\nb"""' }, { cls: null, text: "\n" }, { cls: "cm-comment", text: "# ✗ x" },
  ]);
  assert.deepEqual(lines, [
    [{ cls: "cm-keyword", text: "def" }, { cls: null, text: " f():" }],
    [{ cls: null, text: "    " }, { cls: "cm-string", text: '"""a' }],
    [{ cls: "cm-string", text: 'b"""' }],
    [{ cls: "cm-comment", text: "# ✗ x" }],
  ]);
  assert.deepEqual(splitTokenLines([{ cls: null, text: "a\n\nb" }]),
    [[{ cls: null, text: "a" }], [], [{ cls: null, text: "b" }]]);
});

test("lineMark reads only the comment", () => {
  assert.equal(lineMark("hi = mid - 1   # ✗ drops the answer"), "bad");
  assert.equal(lineMark("hi = mid       # ✓ keeps it"), "good");
  assert.equal(lineMark("print('✗')"), "");
  assert.equal(lineMark("x = 1  # fine"), "");
  assert.equal(lineMark(""), "");
});

test("eyebrowText", () => {
  assert.equal(eyebrowText("0.5", 9), "§0.5 · about 9 min");
  assert.equal(eyebrowText(null, 1), "about 1 min");
});

test("splitH2Number", () => {
  assert.deepEqual(splitH2Number("0.5 The primitives"), { num: "0.5", lead: "0.5 ", rest: "The primitives" });
  assert.deepEqual(splitH2Number("0.10 Ten"), { num: "0.10", lead: "0.10 ", rest: "Ten" });
  assert.equal(splitH2Number("Exact match: the canonical template"), null);
  assert.equal(splitH2Number("0.5"), null);
});

test("cellBadge pills plain and bold Big-O cells, nothing else", () => {
  assert.equal(cellBadge("O(1)", []), "fast");
  assert.equal(cellBadge(" O(log n) ", []), "fast");
  assert.equal(cellBadge("O(n)", ["strong"]), "mid");
  assert.equal(cellBadge("O(hi – lo)", []), "mid");
  assert.equal(cellBadge("the cost of the check, often O(n)", []), null);
  assert.equal(cellBadge("O(R) time and space", []), null);
  assert.equal(cellBadge("O(n)", ["code"]), null); // code cells take the code path
  assert.equal(cellBadge("O(n)", ["strong", "em"]), null);
  assert.equal(cellBadge("O(n)", ["a"]), null);
});
