// Pure parsers for the lesson widgets. Run with: node --test "app/static/js/tests/*.test.mjs"
import test from "node:test";
import assert from "node:assert/strict";
import { BlockError, parseSteps, parseCompare, stepCells } from "../lesson-widgets.js";

const LOWER_BOUND = `title: lower_bound(nums, 7)
array: 1 3 5 7 7 9 11
- lo=0 hi=7 | Start: the boundary is somewhere in [0, 7).
- lo=0 hi=7 mid=3 | nums[3] = 7 >= 7, so mid is T. Keep it: hi = mid.
- lo=0 hi=3 mid=1 | nums[1] = 3 < 7, so mid is F. lo = mid + 1.
- lo=2 hi=3 mid=2 | nums[2] = 5 < 7. lo = mid + 1.
- lo=3 hi=3 ans=3 | lo == hi: the boundary is index 3.
`;

const COMPARE = `title: Two ways to write the range
option: Closed [lo, hi]
  Means: every index from lo to hi, both ends included
  Start: lo, hi = 0, len(nums) - 1
  Loop: while lo <= hi
  Discard right: hi = mid - 1
  Ends when: lo > hi, the range is empty
  Use for: exact match
option: Half-open [lo, hi)
  Means: lo included, hi excluded
  Start: lo, hi = 0, len(nums)
  Loop: while lo < hi
  Discard right: hi = mid
  Ends when: lo == hi, lo is the answer
  Use for: boundaries, lower_bound
`;

test("parseSteps reads the spec example", () => {
  const d = parseSteps(LOWER_BOUND);
  assert.equal(d.title, "lower_bound(nums, 7)");
  assert.deepEqual(d.array, ["1", "3", "5", "7", "7", "9", "11"]);
  assert.equal(d.range, "closed");
  assert.equal(d.steps.length, 5);
  assert.deepEqual(d.steps[1].ptrs, { lo: 0, hi: 7, mid: 3 });
  assert.equal(d.steps[1].text, "nums[3] = 7 >= 7, so mid is T. Keep it: hi = mid.");
});

test("range: half-open is read", () => {
  const d = parseSteps("range: half-open\n" + LOWER_BOUND);
  assert.equal(d.range, "half-open");
});

test("stepCells: half-open greys outside [lo, hi), ghost at len", () => {
  const d = { ...parseSteps(LOWER_BOUND), range: "half-open" };
  const c = stepCells(d, 0); // lo=0 hi=7
  assert.equal(c.length, 8);
  assert.equal(c[7].ghost, true);
  assert.deepEqual(c[7].labels, ["hi"]);
  assert.ok(c.slice(0, 7).every((x) => x.state === "in"));
  const c2 = stepCells(d, 2); // lo=0 hi=3 mid=1
  assert.equal(c2.length, 7); // no ghost: no pointer equals 7
  assert.equal(c2[1].state, "mid");
  assert.equal(c2[3].state, "out");
  assert.equal(c2[0].state, "in");
  assert.deepEqual(c2[1].labels, ["mid"]);
  assert.deepEqual(c2[0].labels, ["lo"]);
  assert.equal(stepCells(d, 4)[3].state, "ans");
  assert.deepEqual(stepCells(d, 4)[3].labels, ["lo", "hi"]); // ans is not a label
});

test("stepCells: closed range keeps hi inside", () => {
  const d = parseSteps("array: a b c d e f\n- lo=1 hi=4 | x");
  const c = stepCells(d, 0);
  assert.equal(c.length, 6);
  assert.equal(c[0].state, "out");
  assert.equal(c[4].state, "in");
  assert.equal(c[5].state, "out");
  assert.equal(c[2].value, "c");
  assert.equal(c[2].index, 2);
  assert.equal(c[2].ghost, false);
});

test("stepCells: no pair means nothing is out", () => {
  const d = parseSteps("array: a b c d\n- i=2 | x");
  const c = stepCells(d, 0);
  assert.ok(c.every((x) => x.state === "in"));
  assert.deepEqual(c[2].labels, ["i"]);
});

test("parseSteps errors", () => {
  for (const [src, msg] of [
    ["- lo=0 | x", /array/], // no array:
    ["array: 1 2\n", /no steps/],
    ["array: 1 2\n- lo=0 hi=3 | x", /past the end/], // 3 > len 2
    ["array: 1 2\n- lo=x | x", /lo/], // not an integer
    ["array: 1 2\n- low=0 | x", /unknown pointer "low"/],
    ["array: 1 2\n- lo=0", /\|/], // no narration separator
  ]) assert.throws(() => parseSteps(src), (e) => e instanceof BlockError && msg.test(e.message), src);
});

test("parseCompare reads the spec example", () => {
  const d = parseCompare(COMPARE);
  assert.equal(d.title, "Two ways to write the range");
  assert.equal(d.options.length, 2);
  assert.equal(d.options[1].name, "Half-open [lo, hi)");
  assert.deepEqual(d.options[0].rows[2], { label: "Loop", value: "while lo <= hi" });
  assert.equal(d.options[0].rows.length, 6);
});

test("parseCompare errors", () => {
  const opt = (n) => `option: O${n}\n  A: b\n`;
  assert.throws(() => parseCompare(opt(1)), (e) => e instanceof BlockError && /two/.test(e.message));
  assert.throws(() => parseCompare([1, 2, 3, 4, 5].map(opt).join("")),
    (e) => e instanceof BlockError && /four/.test(e.message));
  assert.throws(() => parseCompare("  A: b\n" + opt(1) + opt(2)), (e) => e instanceof BlockError);
});

import { stepView, nextStep, inlineSegments } from "../lesson-widgets.js";

test("stepView: counter, button states and narration at each end", () => {
  const d = parseSteps(LOWER_BOUND);
  const first = stepView(d, 0);
  assert.equal(first.counter, "Step 1 of 5");
  assert.equal(first.backDisabled, true);
  assert.equal(first.nextDisabled, false);
  assert.equal(first.narration, "Start: the boundary is somewhere in [0, 7).");
  assert.equal(first.cells.length, 8); // 7 cells plus the ghost for hi=7
  const last = stepView(d, 4);
  assert.equal(last.counter, "Step 5 of 5");
  assert.equal(last.backDisabled, false);
  assert.equal(last.nextDisabled, true);
});

test("nextStep clamps to the first and last step", () => {
  assert.equal(nextStep(0, -1, 5), 0);
  assert.equal(nextStep(0, 1, 5), 1);
  assert.equal(nextStep(4, 1, 5), 4);
  assert.equal(nextStep(3, -1, 5), 2);
});

test("inlineSegments splits backticked code out of a value", () => {
  assert.deepEqual(inlineSegments("plain"), [{ code: false, text: "plain" }]);
  assert.deepEqual(inlineSegments("use `hi = mid` here"), [
    { code: false, text: "use " }, { code: true, text: "hi = mid" }, { code: false, text: " here" },
  ]);
  assert.deepEqual(inlineSegments("`a` and `b`"), [
    { code: true, text: "a" }, { code: false, text: " and " }, { code: true, text: "b" },
  ]);
  assert.deepEqual(inlineSegments("a lone ` tick"), [{ code: false, text: "a lone ` tick" }]);
});
