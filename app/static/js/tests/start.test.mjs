// The "Get started" checklist on Home, without the DOM.
// Run with: node --test "app/static/js/tests/*.test.mjs"
import test from "node:test";
import assert from "node:assert/strict";
import { stepStates, canHide, showStart, countLabel } from "../start.js";

const overview = (over = {}) => Object.assign({
  setup: { statements_have: 0, statements_total: 118, claude: true },
  kpis: { solved: 0 },
  onboarding: { discovery: false, discovery_started: false, self_check: false, diagnostic: false,
    diagnostic_started: false },
}, over);
const states = (steps) => steps.map((s) => s.key + ":" + s.state + (s.next ? "*" : ""));
const ob = (over = {}) => Object.assign({ discovery: false, discovery_started: false, self_check: false,
  diagnostic: false, diagnostic_started: false }, over);

test("a first start has five steps in work order, the first solve last", () => {
  const steps = stepStates(overview(), null);
  assert.deepEqual(states(steps),
    ["statements:todo*", "plan:todo", "selfcheck:todo", "diagnostic:todo", "solve:todo"]);
  assert.equal(countLabel(steps), "0 of 5 done");
  assert.equal(showStart(steps, false), true);
  assert.equal(canHide(steps), false);
});

test("each tick comes from its own part of the payload", () => {
  const o = overview({ setup: { statements_have: 118, statements_total: 118 } });
  assert.deepEqual(states(stepStates(o, null)).slice(0, 2), ["statements:done", "plan:todo*"]);
  o.onboarding = ob({ discovery_started: true });
  assert.equal(states(stepStates(o, null))[1], "plan:doing*");
  o.onboarding = ob({ discovery: true, discovery_started: true });
  assert.deepEqual(states(stepStates(o, null)).slice(1, 3), ["plan:done", "selfcheck:todo*"]);
  o.onboarding = ob({ discovery: true, self_check: true });
  assert.equal(states(stepStates(o, null))[3], "diagnostic:todo*");
  o.onboarding = ob({ discovery: true, self_check: true, diagnostic_started: true });
  assert.equal(states(stepStates(o, null))[3], "diagnostic:doing*");
  o.onboarding = ob({ discovery: true, self_check: true, diagnostic: true });
  assert.deepEqual(states(stepStates(o, null)).slice(3), ["diagnostic:done", "solve:todo*"]);
  o.kpis = { solved: 1 };
  assert.equal(states(stepStates(o, null))[4], "solve:done");
});

test("steps can be ticked out of order; next is the first one still open", () => {
  const o = overview({ kpis: { solved: 3 }, onboarding: ob({ discovery: true, diagnostic: true }) });
  assert.deepEqual(states(stepStates(o, null)),
    ["statements:todo*", "plan:done", "selfcheck:todo", "diagnostic:done", "solve:done"]);
});

test("a polled download status wins over the page's first numbers", () => {
  const o = overview();
  assert.equal(states(stepStates(o, { have: 40, total: 118, running: true }))[0], "statements:doing*");
  assert.equal(states(stepStates(o, { have: 118, total: 118, running: false }))[0], "statements:done");
  assert.equal(states(stepStates(o, { have: 110, total: 118, running: false }))[0], "statements:todo*");
});

test("the card goes once every step is ticked", () => {
  const o = overview({ setup: { statements_have: 118, statements_total: 118 }, kpis: { solved: 2 },
    onboarding: ob({ discovery: true, self_check: true, diagnostic: true }) });
  const steps = stepStates(o, null);
  assert.equal(countLabel(steps), "5 of 5 done");
  assert.equal(showStart(steps, false), false);
});

test("Hide works only after the two steps done in the app, and stops working if one reopens", () => {
  const done = overview({ setup: { statements_have: 118, statements_total: 118 }, kpis: { solved: 1 } });
  assert.equal(canHide(stepStates(done, null)), true);
  assert.equal(showStart(stepStates(done, null), true), false);
  assert.equal(showStart(stepStates(done, null), false), true);
  const reopened = overview({ setup: { statements_have: 100, statements_total: 118 }, kpis: { solved: 1 } });
  assert.equal(showStart(stepStates(reopened, null), true), true);
});

test("a server from before the checklist gives the two app steps only", () => {
  const o = overview();
  delete o.onboarding;
  const steps = stepStates(o, null);
  assert.deepEqual(states(steps), ["statements:todo*", "solve:todo"]);
  o.setup.statements_have = 118;
  o.kpis.solved = 5;
  assert.equal(showStart(stepStates(o, null), false), false);
});

test("a payload with nothing in it does not throw", () => {
  assert.deepEqual(states(stepStates(null, null)), ["statements:done", "solve:todo*"]);
  assert.deepEqual(states(stepStates({}, null)), ["statements:done", "solve:todo*"]);
});
