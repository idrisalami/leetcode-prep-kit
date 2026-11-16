// Pure classifiers for the lesson pages. Run with: node --test "app/static/js/tests/*.test.mjs"
import test from "node:test";
import assert from "node:assert/strict";
import {
  classifyCallout, bigOClass, countWords, readingMinutes, pairSelfCheck, tallyText,
  progressLine, countsAsSection, newlyRead, parseStored, load, store,
  splitTokenLines, lineMark, eyebrowText, splitH2Number, cellBadge, buildFlipCard, flipAnnouncement,
} from "../lesson.js";
import { installFakeDom, findAll } from "./fake-dom.mjs";

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

import { isSelfCheckHeading, markText, cleanResults, recordResult } from "../lesson.js";

test("isSelfCheckHeading: the questions h2, numbered or not, never the answers h2", () => {
  assert.equal(isSelfCheckHeading("0.9 Self-check"), true);
  assert.equal(isSelfCheckHeading("  Self-check "), true);
  assert.equal(isSelfCheckHeading("Self-check answers"), false);
  assert.equal(isSelfCheckHeading("0.8 Complexity"), false);
});

test("markText: the small mark on a card's front", () => {
  assert.equal(markText("got"), "✓ got");
  assert.equal(markText("missed"), "✗ missed");
  assert.equal(markText(undefined), "");
});

test("cleanResults keeps only known values for cards that exist", () => {
  assert.deepEqual(cleanResults({ 0: "got", 1: "missed", 2: "maybe", 9: "got" }, 3), { 0: "got", 1: "missed" });
  assert.deepEqual(cleanResults(null, 3), {});
  assert.deepEqual(cleanResults(["got"], 3), {});
  assert.deepEqual(cleanResults("got", 3), {});
});

test("recordResult overwrites one card and leaves the input alone", () => {
  const before = { 0: "got" };
  const after = recordResult(before, 0, "missed");
  assert.deepEqual(after, { 0: "missed" });
  assert.deepEqual(before, { 0: "got" });
  assert.deepEqual(recordResult(after, 2, "got"), { 0: "missed", 2: "got" });
});

import { cleanRead, parentSection, railStats } from "../lesson.js";

test("cleanRead keeps only string ids still on the page, once each", () => {
  const ids = ["a", "b", "c"];
  assert.deepEqual(cleanRead(["a", "gone", "c", "a", 3, null], ids), ["a", "c"]);
  assert.deepEqual(cleanRead({ a: 1 }, ids), []);
  assert.deepEqual(cleanRead(null, ids), []);
});

test("parentSection finds the h2 that holds the current link", () => {
  const kinds = ["h2", "h3", "h3", "h2", "h3"];
  assert.equal(parentSection(kinds, 2), 0);
  assert.equal(parentSection(kinds, 3), 3);
  assert.equal(parentSection(kinds, 4), 3);
  assert.equal(parentSection(["h3", "h2"], 0), -1); // an h3 before any h2
  assert.equal(parentSection(kinds, -1), -1);
});

test("railStats counts only counted sections and gives the bar width", () => {
  const sections = [{ id: "a", counted: true }, { id: "b", counted: true }, { id: "x", counted: false },
    { id: "c", counted: true }];
  assert.deepEqual(railStats(sections, new Set(["a", "x"])), { read: 1, total: 3, pct: 33 });
  assert.deepEqual(railStats(sections, new Set(["a", "b", "c"])), { read: 3, total: 3, pct: 100 });
  assert.deepEqual(railStats([], new Set()), { read: 0, total: 0, pct: 0 });
});

import { newlySeen } from "../lesson.js";

test("newlySeen: a scroll past counts, a jump past does not", () => {
  const vh = 800;
  // Scrolled from the top to far down: both ends crossed the bottom edge since the last look.
  const prev = { a: 900, b: 2000 };
  assert.deepEqual(newlySeen([{ id: "a", top: -500 }, { id: "b", top: 300 }], prev, vh, new Set()), ["a", "b"]);
  // After an anchor jump the baseline is the landing position: a skipped end stays above the
  // viewport and never crossed, so it is not read; one on screen is.
  const landed = { a: -1500, b: 100 };
  assert.deepEqual(newlySeen([{ id: "a", top: -1600 }, { id: "b", top: 0 }], landed, vh, new Set()), ["b"]);
  // Scrolling back up brings the skipped end into view: now it counts.
  assert.deepEqual(newlySeen([{ id: "a", top: 200 }], { a: -1600 }, vh, new Set()), ["a"]);
  // Already read, or still below the fold: nothing.
  assert.deepEqual(newlySeen([{ id: "a", top: 100 }, { id: "c", top: 900 }], {}, vh, new Set(["a"])), []);
});

test("flip card exposes question and answer as content, with a real toggle button on each face", () => {
  const doc = installFakeDom();
  const li = (text) => { const e = doc.createElement("li"); e.append(text); return e; };
  const { card, front, back, toggles, got, missed } = buildFlipCard(doc, li("Why a min-heap?"), li("It keeps the k largest."), 3);
  for (const a of ["role", "tabindex", "aria-label"]) assert.equal(card.getAttribute(a), null, `card has no ${a}`);
  assert.ok(front.textContent.includes("Why a min-heap?"));
  assert.ok(back.textContent.includes("It keeps the k largest."));
  const [show, hide] = toggles;
  assert.equal(show.localName, "button");
  assert.equal(show.type, "button");
  assert.equal(show.textContent, "Show answer");
  assert.equal(show.getAttribute("aria-expanded"), "false");
  assert.ok(findAll(front, "button").includes(show));
  assert.equal(hide.textContent, "Show question");
  assert.ok(findAll(back, "button").includes(hide));
  assert.equal(back.getAttribute("aria-hidden"), "true");
  assert.equal(back.inert, true);
  assert.deepEqual([got.textContent, missed.textContent], ["Got it", "Missed it"]);
});

test("flipAnnouncement reads the answer out on flip, not just that it flipped", () => {
  assert.equal(flipAnnouncement(true, 3, "  It keeps\n the k largest. "), "Answer 3: It keeps the k largest.");
  assert.equal(flipAnnouncement(false, 3, "ignored"), "Question 3");
});
