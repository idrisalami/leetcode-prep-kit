// Pure helpers of the practice workspace. Run with: node --test "app/static/js/tests/*.test.mjs"
import test from "node:test";
import assert from "node:assert/strict";
import {
  cleanNeetcode, fmtClock, fmtMs, caseRow, caseFields, errorText, resultSummary,
  historyItems, unreviewedSubmit, scratchKey, reviewFlagText, nextSaveState, createSaver, saveLabel,
} from "../practice.js";

test("cleanNeetcode turns inline $…$ maths into plain text", () => {
  assert.equal(cleanNeetcode("You are given a $m \\times n$ 2D grid."), "You are given a m × n 2D grid.");
  assert.equal(cleanNeetcode("$1 \\le n \\leq 10^5$"), "1 ≤ n ≤ 10<sup>5</sup>");
  assert.equal(cleanNeetcode("$x \\ge 0$, $y \\neq z$"), "x ≥ 0, y ≠ z");
  assert.equal(cleanNeetcode("$2^{31} - 1$"), "2<sup>31</sup> - 1");
  assert.equal(cleanNeetcode("$O(n \\log n)$"), "O(n log n)");
  assert.equal(cleanNeetcode("$\\text{nums}[i]$ and $a_{i}$"), "nums[i] and a<sub>i</sub>");
});

test("cleanNeetcode escapes angle brackets inside the maths so they stay text", () => {
  assert.equal(cleanNeetcode("$a < b$"), "a &lt; b");
  assert.equal(cleanNeetcode("$<img src=x onerror=alert(1)>$"), "&lt;img src=x onerror=alert(1)&gt;");
});

test("cleanNeetcode leaves code spans, fenced blocks and lone dollars alone", () => {
  assert.equal(cleanNeetcode("Use `$a$` here"), "Use `$a$` here");
  assert.equal(cleanNeetcode("```\nx = $a$\n```"), "```\nx = $a$\n```");
  assert.equal(cleanNeetcode("It costs $5 a month"), "It costs $5 a month");
  assert.equal(cleanNeetcode("from $a\nto b$"), "from $a\nto b$");
});

test("cleanNeetcode drops the NeetCode Pro company-tags block and trailing line breaks", () => {
  const md = "Text.\n\n<br>\n<details class=\"hint-accordion\">\n<summary>Hint 1</summary>\n<p>Go.</p>\n</details>\n"
    + "\n<br>\n<details class=\"company-tags-accordion\">\n<summary>Company Tags</summary>\n"
    + "<p>Please upgrade to <a href=\"https://neetcode.io/pro\">NeetCode Pro</a>.</p>\n</details>\n";
  const out = cleanNeetcode(md);
  assert.ok(!out.includes("Company Tags"));
  assert.ok(!out.includes("neetcode.io/pro"));
  assert.ok(out.includes("Hint 1"));
  assert.ok(!/<br>\s*$/.test(out));
});

test("fmtClock shows mm:ss under an hour and h:mm:ss after", () => {
  assert.equal(fmtClock(0), "00:00");
  assert.equal(fmtClock(5), "00:05");
  assert.equal(fmtClock(65), "01:05");
  assert.equal(fmtClock(3599), "59:59");
  assert.equal(fmtClock(3725), "1:02:05");
  assert.equal(fmtClock(-4), "00:00");
  assert.equal(fmtClock("x"), "00:00");
  assert.equal(fmtClock(61.9), "01:01");
});

test("fmtMs rounds to whole milliseconds and switches to seconds at one second", () => {
  assert.equal(fmtMs(null), "");
  assert.equal(fmtMs(undefined), "");
  assert.equal(fmtMs(0.2), "<1 ms");
  assert.equal(fmtMs(3.4), "3 ms");
  assert.equal(fmtMs(999.4), "999 ms");
  assert.equal(fmtMs(1234), "1.2 s");
});

const base = { name: "Example 1", input: "nums = [1], target = 1", expected: "0", got: "0", stdout: "", ms: 2, error: null, message: "" };

test("caseRow gives every status its own icon and words", () => {
  assert.deepEqual(caseRow(Object.assign({}, base, { status: "pass" })),
    { icon: "✓", tone: "pass", name: "Example 1", note: "2 ms", open: false });
  assert.deepEqual(caseRow(Object.assign({}, base, { status: "fail", got: "1" })),
    { icon: "✗", tone: "fail", name: "Example 1", note: "wrong answer · 2 ms", open: true });
  const err = caseRow(Object.assign({}, base, { status: "error", error: { type: "IndexError", message: "list index out of range", line: 4, trace: "" } }));
  assert.equal(err.icon, "✗");
  assert.equal(err.tone, "error");
  assert.equal(err.note, "IndexError on line 4 · 2 ms");
  assert.equal(err.open, true);
  const slow = caseRow(Object.assign({}, base, { status: "timeout", ms: null }));
  assert.equal(slow.icon, "⏱");
  assert.equal(slow.tone, "timeout");
  assert.equal(slow.note, "timed out");
  assert.equal(slow.open, true);
  const skip = caseRow(Object.assign({}, base, { status: "not_run", ms: null }));
  assert.equal(skip.icon, "–");
  assert.equal(skip.tone, "skip");
  assert.equal(skip.note, "not run");
  assert.equal(skip.open, false);
});

test("caseRow names an unnamed case", () => {
  assert.equal(caseRow(Object.assign({}, base, { name: "", status: "pass" })).name, "Case");
});

test("caseFields lists what a failing case needs, and skips empty printed output", () => {
  assert.deepEqual(caseFields(Object.assign({}, base, { status: "fail", got: "1" })), [
    ["Input", "nums = [1], target = 1"], ["Expected", "0"], ["Got", "1"]]);
  assert.deepEqual(caseFields(Object.assign({}, base, { status: "fail", got: "1", stdout: "mid 0\n" })), [
    ["Input", "nums = [1], target = 1"], ["Expected", "0"], ["Got", "1"], ["Printed output", "mid 0\n"]]);
  const e = caseFields(Object.assign({}, base, { status: "error", got: null,
    error: { type: "IndexError", message: "list index out of range", line: 4, trace: "Traceback…" } }));
  assert.deepEqual(e, [["Input", "nums = [1], target = 1"], ["Expected", "0"],
    ["Error", "IndexError on line 4: list index out of range"], ["Traceback", "Traceback…"]]);
  const t = caseFields(Object.assign({}, base, { status: "timeout", got: null, message: "took longer than 2 s" }));
  assert.deepEqual(t, [["Input", "nums = [1], target = 1"], ["Expected", "0"], ["Note", "took longer than 2 s"]]);
});

test("errorText names the type, the line when there is one, and the message", () => {
  assert.equal(errorText({ type: "SyntaxError", message: "invalid syntax", line: 3 }), "SyntaxError on line 3: invalid syntax");
  assert.equal(errorText({ type: "Timeout", message: "too slow", line: null }), "Timeout: too slow");
  assert.equal(errorText({ type: "", message: "odd" }), "Error: odd");
  assert.equal(errorText(null), "");
});

test("resultSummary says how many pass and never claims a LeetCode verdict", () => {
  assert.deepEqual(resultSummary({ passed: 1, total: 2, results: [{}, {}] }, "run"),
    { tone: "bad", text: "1 of 2 examples pass" });
  assert.deepEqual(resultSummary({ passed: 2, total: 2, results: [{}, {}] }, "run"),
    { tone: "good", text: "Both examples pass" });
  assert.deepEqual(resultSummary({ passed: 1, total: 1, results: [{}] }, "run"),
    { tone: "good", text: "The example passes" });
  assert.deepEqual(resultSummary({ passed: 12, total: 12, results: [], solved: true }, "submit"),
    { tone: "good", text: "All 12 of the app's tests pass" });
  assert.deepEqual(resultSummary({ passed: 9, total: 12, results: [] }, "submit"),
    { tone: "bad", text: "9 of 12 of the app's tests pass" });
  assert.deepEqual(resultSummary({ fatal: { type: "SyntaxError" }, passed: 0, total: 12, results: [] }, "submit"),
    { tone: "bad", text: "No test ran" });
  for (const s of [resultSummary({ passed: 3, total: 3 }, "submit").text]) {
    assert.ok(!/leetcode|accepted/i.test(s));
  }
});

test("historyItems merges chat and this attempt's reviews by time", () => {
  const chat = [
    { role: "user", kind: "hint", text: "Give me a hint", at: "T10" },
    { role: "coach", kind: "hint", text: "Look at line 6.", at: "T11" },
  ];
  const submits = [
    { id: "a", at: "T05", attempt: 1, reviewed: true, review: { verdict: "pass" }, passed: 3, total: 3 },
    { id: "b", at: "T12", attempt: 2, reviewed: true, review: { verdict: "needs_work" }, passed: 2, total: 3 },
    { id: "c", at: "T13", attempt: 2, reviewed: false, passed: 3, total: 3 },
  ];
  const items = historyItems(chat, submits, 2);
  assert.deepEqual(items.map((i) => i.type + ":" + i.at), ["chat:T10", "chat:T11", "review:T12"]);
  assert.equal(items[2].submitId, "b");
  assert.deepEqual(items[2].review, { verdict: "needs_work" });
  assert.deepEqual(historyItems(null, null, 1), []);
});

test("historyItems treats a submit without an attempt as attempt 1", () => {
  const items = historyItems([], [{ id: "x", at: "T1", reviewed: true, review: { verdict: "pass" } }], 1);
  assert.equal(items.length, 1);
});

test("unreviewedSubmit finds the latest submit of this attempt still waiting for its review", () => {
  assert.equal(unreviewedSubmit([{ id: "a", attempt: 1, reviewed: false }], 1), "a");
  assert.equal(unreviewedSubmit([{ id: "a", attempt: 1, reviewed: false }, { id: "b", attempt: 1, reviewed: true }], 1), null);
  assert.equal(unreviewedSubmit([{ id: "a", attempt: 1, reviewed: false }], 2), null);
  assert.equal(unreviewedSubmit(undefined, 1), null);
});

test("scratchKey is per problem and per attempt", () => {
  assert.equal(scratchKey("binary-search", 1), "prep:scratch:binary-search:1");
  assert.equal(scratchKey("two-sum", undefined), "prep:scratch:two-sum:1");
});

test("nextSaveState: typing during a save keeps the newer text pending", () => {
  // The snapshot that was sent comes back saved, but the editor moved on: still dirty.
  assert.deepEqual(nextSaveState({ saved: "a", current: "ab", sent: "a" }), { saved: "a", dirty: true });
  assert.deepEqual(nextSaveState({ saved: "", current: "abc", sent: "abc" }), { saved: "abc", dirty: false });
});

// ---- createSaver, with a fake clock and PUTs the test answers by hand ----

function fakeClock() {
  let next = 1;
  const timers = new Map();
  return {
    schedule(fn, ms) { const id = next++; timers.set(id, { fn, ms }); return id; },
    cancel(id) { timers.delete(id); },
    pending() { return [...timers.values()].map((t) => t.ms); },
    fire(ms) {
      for (const [id, t] of timers) if (t.ms === ms) { timers.delete(id); t.fn(); return true; }
      return false;
    },
  };
}
const tick = () => new Promise((r) => setTimeout(r, 0));

function rig(start = "a") {
  const clock = fakeClock();
  const state = { text: start, sends: [], keeps: [], states: [] };
  const saver = createSaver({
    snap: () => state.text,
    saved: start,
    clock,
    send: (text) => new Promise((resolve, reject) => state.sends.push({ text, resolve, reject })),
    keep: (text) => { state.keeps.push(text); return Promise.resolve(); },
    onState: (s) => state.states.push(s),
  });
  return { clock, state, saver };
}

test("createSaver (E6): a failed save is retried once 5 s later; the error stays until a save works", async () => {
  const { clock, state, saver } = rig();
  state.text = "b";
  saver.changed();
  assert.ok(clock.fire(1000));
  await tick();
  state.sends[0].reject(new Error("down"));
  await tick(); await tick();
  assert.ok(state.states.at(-1).error, "Not saved shows");
  assert.deepEqual(clock.pending(), [5000]);
  assert.ok(clock.fire(5000));
  await tick();
  assert.equal(state.sends.length, 2);
  assert.ok(state.states.at(-1).error, "still Not saved while the retry is on its way");
  state.sends[1].reject(new Error("down"));
  await tick(); await tick();
  assert.deepEqual(clock.pending(), [], "only one retry");
  assert.ok(state.states.at(-1).error);
  saver.save();
  await tick();
  state.sends[2].resolve();
  await tick(); await tick();
  assert.equal(state.states.at(-1).error, null);
  assert.equal(saver.saved, "b");
});

test("createSaver (E6): no retry when the text was saved by then", async () => {
  const { clock, state, saver } = rig();
  state.text = "b";
  saver.save();
  await tick();
  state.sends[0].reject(new Error("down"));
  await tick(); await tick();
  state.text = "a"; // typed back to what the server has
  clock.fire(5000);
  await tick();
  assert.equal(state.sends.length, 1);
});

test("createSaver (E7): hold() cancels the timer, waits for the save in flight, and ignores edits", async () => {
  const { clock, state, saver } = rig();
  state.text = "b";
  saver.save();
  await tick();
  state.text = "c";
  saver.changed();
  let held = false;
  const h = saver.hold().then(() => { held = true; });
  assert.deepEqual(clock.pending(), [], "the pending save is cancelled");
  await tick();
  assert.equal(held, false, "still waiting for the PUT of b");
  state.sends[0].resolve();
  await h;
  assert.equal(held, true);
  state.text = "d";
  saver.changed();
  saver.save();
  saver.flush();
  assert.deepEqual(clock.pending(), []);
  await tick();
  assert.equal(state.sends.length, 1, "nothing is sent while held");
  assert.deepEqual(state.keeps, []);
  saver.saved = "d"; // the Reset answer applied
  saver.release();
  assert.deepEqual(clock.pending(), [], "nothing left to save");
});

test("createSaver (E8): flush skips text that is already on its way, and sends newer text", async () => {
  const { state, saver } = rig();
  state.text = "b";
  saver.save();
  await tick();
  saver.flush();
  await tick();
  assert.deepEqual(state.keeps, [], "b is in flight already");
  state.text = "c";
  saver.flush();
  await tick();
  assert.deepEqual(state.keeps, ["c"]);
  saver.flush();
  await tick();
  assert.deepEqual(state.keeps, ["c"], "not twice");
});

test("createSaver: typing during a save sends the newer text after it", async () => {
  const { clock, state, saver } = rig();
  state.text = "b";
  saver.save();
  await tick();
  state.text = "c";
  state.sends[0].resolve();
  await tick(); await tick();
  assert.equal(saver.saved, "b");
  assert.deepEqual(clock.pending(), [1000]);
  assert.equal(state.states.at(-1).dirty, true);
});

// ---- F2, F3: the stale 409 and the save warning ----

const stale409 = () => Object.assign(new Error("stale"), { status: 409, code: "stale", detail: "x" });

test("createSaver (F2): a 409 stale stops saving: no retry, no timers, later edits are ignored", async () => {
  const stalls = [];
  const clock = fakeClock();
  const state = { text: "a", sends: [], keeps: [], states: [] };
  const saver = createSaver({
    snap: () => state.text, saved: "a", clock,
    send: (text) => new Promise((resolve, reject) => state.sends.push({ text, resolve, reject })),
    keep: (text) => { state.keeps.push(text); return Promise.resolve(); },
    onState: (s) => state.states.push(s),
    onStale: (err) => stalls.push(err),
  });
  state.text = "b";
  saver.changed();
  clock.fire(1000);
  await tick();
  state.sends[0].reject(stale409());
  await tick(); await tick();
  assert.equal(stalls.length, 1);
  assert.deepEqual(clock.pending(), [], "no retry timer");
  assert.equal(state.states.at(-1).stale, true);
  state.text = "c";
  saver.changed();
  assert.deepEqual(clock.pending(), [], "edits do not schedule a save");
  assert.equal(saver.save(), null);
  saver.flush();
  assert.equal(state.sends.length, 1);
  assert.equal(state.keeps.length, 0);
});

test("createSaver (F2): reset(text) lifts a stall, and stall(err) stalls from a run or submit", async () => {
  const { clock, state, saver } = rig();
  saver.stall(stale409());
  state.text = "b";
  saver.changed();
  assert.deepEqual(clock.pending(), []);
  saver.reset("b");
  assert.equal(saver.saved, "b");
  state.text = "c";
  saver.changed();
  assert.deepEqual(clock.pending(), [1000]);
});

test("createSaver (F3): a warning from the server shows in the state and clears on the next clean save", async () => {
  const clock = fakeClock();
  const state = { text: "a", sends: [], states: [] };
  const saver = createSaver({
    snap: () => state.text, saved: "a", clock,
    send: (text) => new Promise((resolve, reject) => state.sends.push({ text, resolve, reject })),
    keep: () => Promise.resolve(),
    onState: (s) => state.states.push(s),
  });
  state.text = "b";
  saver.save();
  await tick();
  state.sends[0].resolve({ ok: true, save_error: "Disk is full" });
  await tick(); await tick();
  assert.equal(state.states.at(-1).warning, "Disk is full");
  state.text = "c";
  saver.save();
  await tick();
  state.sends[1].resolve({ ok: true });
  await tick(); await tick();
  assert.equal(state.states.at(-1).warning, null);
});

test("saveLabel: never says Saved while the server could not keep the state", () => {
  const base = { saving: false, error: null, dirty: false, warning: null, stale: false };
  assert.equal(saveLabel(base), "Saved");
  assert.equal(saveLabel({ ...base, dirty: true }), "Not saved yet");
  assert.equal(saveLabel({ ...base, saving: true }), "Saving…");
  assert.equal(saveLabel({ ...base, warning: "Disk is full" }), "Not saved: Disk is full");
  assert.equal(saveLabel({ ...base, saving: true, warning: "Disk is full" }), "Saving…");
  assert.match(saveLabel({ ...base, error: { detail: "boom" } }), /^Not saved: boom/);
  assert.equal(saveLabel({ ...base, error: { status: 413 } }), "Not saved: over 200,000 characters");
  assert.equal(saveLabel({ ...base, stale: true }), "Not saved: changed in another tab");
});

// ---- F15: leaving while held, and the label after a flush that did not leave ----

test("createSaver (F15.4): leaving while a Reset holds the saver sends the typed text once, after the hold", async () => {
  const { state, saver } = rig();
  await saver.hold();
  state.text = "typed during the reset";
  saver.destroy();
  saver.flush();
  assert.equal(state.keeps.length, 0, "nothing goes out while the hold is on");
  saver.release();
  await tick();
  assert.deepEqual(state.keeps, ["typed during the reset"]);
  saver.release();
  await tick();
  assert.equal(state.keeps.length, 1, "only once");
});

test("createSaver (F15.4): nothing is sent after the hold when the text did not change during it", async () => {
  const { state, saver } = rig();
  await saver.hold();
  saver.destroy();
  saver.release();
  await tick();
  assert.equal(state.keeps.length, 0);
});

test("createSaver (F15.5): a keepalive flush that did not leave the page marks the text saved", async () => {
  const { state, saver } = rig();
  state.text = "b";
  saver.flush();
  await tick(); await tick();
  assert.equal(saver.saved, "b");
  assert.equal(state.states.at(-1).dirty, false);
});

test("reviewFlagText names each state of the final review and nothing else", () => {
  assert.match(reviewFlagText("writing"), /in progress.*Stay on this page/);
  assert.match(reviewFlagText("done"), /ready/);
  assert.match(reviewFlagText("failed"), /No final review/);
  assert.match(reviewFlagText("queued"), /starts when/);
  assert.match(reviewFlagText("again"), /Not reviewed/);
  assert.equal(reviewFlagText(null), null);
  assert.equal(reviewFlagText("other"), null);
});
