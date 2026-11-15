// The setup pages' pure helpers, without the DOM.
// Run with: node --test "app/static/js/tests/*.test.mjs"
import test from "node:test";
import assert from "node:assert/strict";
import { fmtClock, clockText, nextOpen, scoreLine, chatTurns, blockRows } from "../setup.js";

test("the clock reads minutes and seconds, and hours past an hour", () => {
  assert.equal(fmtClock(0), "0:00");
  assert.equal(fmtClock(125), "2:05");
  assert.equal(fmtClock(3725), "1:02:05");
  assert.equal(fmtClock(-4), "0:00");
  assert.equal(fmtClock(59.9), "0:59");
});

test("the countdown says what is left, then how far over", () => {
  assert.deepEqual(clockText(20, 0), { text: "20:00 left", over: false });
  assert.deepEqual(clockText(20, 1199), { text: "0:01 left", over: false });
  assert.deepEqual(clockText(20, 1200), { text: "0:00 left", over: false });
  assert.deepEqual(clockText(20, 1265), { text: "1:05 over", over: true });
});

test("the next problem is the first unfinished one after the current, then from the top", () => {
  const ps = (...f) => f.map((finished) => ({ finished }));
  assert.equal(nextOpen(ps(false, false, false)), 0);
  assert.equal(nextOpen(ps(true, false, false), 0), 1);
  assert.equal(nextOpen(ps(false, true, true), 2), 0);
  assert.equal(nextOpen(ps(false, true, false), 0), 2);
  assert.equal(nextOpen(ps(true, true, true), 1), -1);
  assert.equal(nextOpen([]), -1);
});

test("the score line names what was missed", () => {
  assert.equal(scoreLine({ score: 8, total: 8, missed: [] }), "8/8, nothing missed");
  assert.equal(scoreLine({ score: 7, total: 8, missed: ["3"] }), "7/8, missed question 3");
  assert.equal(scoreLine({ score: 5, total: 8, missed: ["1", "4", "6"] }), "5/8, missed questions 1, 4 and 6");
  assert.equal(scoreLine(null), "");
});

test("chat turns keep only well-formed user and coach messages", () => {
  const turns = chatTurns([{ role: "coach", text: "Hi" }, { role: "user", text: "Hello" },
    { role: "system", text: "x" }, null, { role: "user" }]);
  assert.deepEqual(turns.map((t) => t.role), ["coach", "user"]);
  assert.deepEqual(chatTurns(undefined), []);
});

test("the dated blocks come out as rows in module order", () => {
  const rows = blockRows({ "02": { start: "2026-12-01", end: "2026-12-08", hours: 9 },
    "01": { start: "2026-11-20", end: "2026-11-30", hours: 12 } });
  assert.deepEqual(rows.map((r) => r.module), ["01", "02"]);
  assert.equal(rows[0].hours, 12);
  assert.deepEqual(blockRows(null), []);
  assert.deepEqual(blockRows([{ module: "03" }]), [{ module: "03" }]);
});
