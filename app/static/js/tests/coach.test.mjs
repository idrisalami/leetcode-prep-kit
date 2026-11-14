// Pure helpers of the coach pane. Run with: node --test "app/static/js/tests/*.test.mjs"
import test from "node:test";
import assert from "node:assert/strict";
import { throttle, reviewBlocks, savedLine, coachError, CHIPS, userLabel, busyFromStop, STOP_GRACE_MS, reviewPoll } from "../coach.js";
import { ApiError } from "../api.js";

function fakeClock() {
  let now = 0;
  let timers = [];
  return {
    now: () => now,
    schedule: (fn, ms) => { const t = { fn, at: now + ms }; timers.push(t); return t; },
    cancel: (t) => { timers = timers.filter((x) => x !== t); },
    advance(ms) {
      now += ms;
      const due = timers.filter((t) => t.at <= now);
      timers = timers.filter((t) => t.at > now);
      for (const t of due) t.fn();
    },
    pending: () => timers.length,
  };
}

test("throttle runs the first call at once, then at most once per interval", () => {
  const c = fakeClock();
  let runs = 0;
  const t = throttle(() => { runs++; }, 100, c);
  t.call();
  assert.equal(runs, 1);
  t.call(); t.call(); t.call();
  assert.equal(runs, 1);
  c.advance(50);
  assert.equal(runs, 1);
  c.advance(50);
  assert.equal(runs, 2, "the trailing call runs once at the end of the interval");
  c.advance(500);
  assert.equal(runs, 2, "nothing more without new calls");
});

test("throttle.flush runs a pending call now; cancel drops it", () => {
  const c = fakeClock();
  let runs = 0;
  const t = throttle(() => { runs++; }, 100, c);
  t.call(); t.call();
  t.flush();
  assert.equal(runs, 2);
  assert.equal(c.pending(), 0);
  t.flush();
  assert.equal(runs, 2, "flush without a pending call does nothing");
  c.advance(200);
  t.call(); t.call();
  t.cancel();
  c.advance(200);
  assert.equal(runs, 3, "the leading call ran, the trailing one was cancelled");
});

test("reviewBlocks lays out the five blocks in order", () => {
  const blocks = reviewBlocks({ verdict: "pass", good: ["clear names"], wrong: [], edge_cases: ["empty input"],
    next_step: "try the follow-up", mistakes: [] });
  assert.deepEqual(blocks.map((b) => b.title),
    ["Verdict", "What's good", "What's wrong", "Edge cases you didn't mention", "Next step"]);
  assert.equal(blocks[0].text, "Ready to move on");
  assert.equal(blocks[0].tone, "good");
  assert.deepEqual(blocks[1].items, ["clear names"]);
  assert.deepEqual(blocks[2].items, []);
  assert.equal(blocks[2].empty, "Nothing found.");
  assert.equal(blocks[4].text, "try the follow-up");
});

test("reviewBlocks reads needs_work and survives missing fields", () => {
  const blocks = reviewBlocks({ verdict: "needs_work" });
  assert.equal(blocks[0].text, "Needs more work");
  assert.equal(blocks[0].tone, "warn");
  assert.deepEqual(blocks[1].items, []);
  assert.equal(blocks[4].text, "");
  assert.equal(reviewBlocks(null).length, 5);
});

test("savedLine says what went to the notes", () => {
  assert.equal(savedLine({ learnings: 1, bugs: 0, skipped: [] }, { mistakes: [{}] }),
    "Saved to your notes: 1 entry in learnings.md.");
  assert.equal(savedLine({ learnings: 2, bugs: 1, skipped: [] }, { mistakes: [{}, {}] }),
    "Saved to your notes: 2 entries in learnings.md and 1 row in bugs.md.");
  assert.equal(savedLine({ learnings: 0, bugs: 0, skipped: [] }, { mistakes: [] }),
    "No mistakes to save to your notes this time.");
  assert.equal(savedLine({ learnings: 0, bugs: 0, skipped: ["x"] }, { mistakes: [{}] }),
    "Nothing could be saved to your notes.");
  // Restored from history: the counts are gone, the mistakes are not.
  // Restored from history: the counts are gone, so one sentence whatever the mistakes.
  for (const review of [{ mistakes: [{}, {}] }, { mistakes: [{}] }, { mistakes: [] }, null]) {
    assert.equal(savedLine(null, review), "Notes from this review were saved when it was written.");
  }
});

test("coachError explains each failure and whether a retry makes sense", () => {
  const nf = coachError(new ApiError(503, "claude_not_found", "claude is not on PATH"));
  assert.equal(nf.setup, true);
  assert.match(nf.text, /claude/);
  const nf2 = coachError(new ApiError(0, "claude_not_found", "x"));
  assert.equal(nf2.setup, true);
  const busy = coachError(new ApiError(409, "busy", "The coach is already answering."));
  assert.equal(busy.retry, true);
  assert.match(busy.text, /busy|already/i);
  const failed = coachError(new ApiError(0, "failed", "claude exited with code 1"));
  assert.match(failed.text, /claude exited with code 1/);
  assert.equal(failed.retry, true);
  const slow = coachError(new ApiError(0, "timeout", "no answer in 180 s"));
  assert.match(slow.text, /too long/i);
  const off = coachError(new ApiError(0, "offline", "The app's server is not answering. Is it still running?"));
  assert.match(off.text, /server/);
  const bad = coachError(new ApiError(400, "bad_request", "Type a question first."));
  assert.equal(bad.text, "Type a question first.");
  assert.equal(bad.retry, false);
  assert.equal(coachError(new Error("boom")).text, "boom");
  for (const e of [nf, busy, failed, slow, off, bad]) {
    assert.ok(!/actually|!/.test(e.text), e.text);
  }
});

test("the four chips are the spec's, and a user turn names the chip pressed", () => {
  assert.deepEqual(CHIPS.map((c) => c.label),
    ["Give me a hint", "Review my solution", "Is my approach right?", "Check my complexity"]);
  assert.deepEqual(CHIPS.map((c) => c.kind), ["hint", "review", "approach", "complexity"]);
  assert.equal(userLabel("hint"), "You · pressed “Give me a hint”");
  assert.equal(userLabel("question"), "You");
  assert.equal(userLabel(undefined), "You");
});

test("busyFromStop (E3): only a busy answer within 10 s of the user's own Stop", () => {
  const busy = new ApiError(409, "busy", "busy");
  assert.equal(busyFromStop(busy, 1000, 1000 + 300), true);
  assert.equal(busyFromStop(busy, 1000, 1000 + STOP_GRACE_MS - 1), true);
  assert.equal(busyFromStop(busy, 1000, 1000 + STOP_GRACE_MS), false, "too long ago");
  assert.equal(busyFromStop(busy, null, 5000), false, "never stopped: another tab is busy");
  assert.equal(busyFromStop(new ApiError(502, "failed", "x"), 1000, 1100), false);
  assert.equal(busyFromStop(null, 1000, 1100), false);
});

test("coachError (E3): busy after a Stop and one retry says it is still stopping; other busy cases keep the old text", () => {
  const busy = new ApiError(409, "busy", "busy");
  assert.equal(coachError(busy, { afterStop: true }).text, "Still stopping the last answer. Try again in a moment.");
  assert.match(coachError(busy).text, /busy with another answer/);
  assert.match(coachError(new ApiError(502, "failed", "boom"), { afterStop: true }).text, /^The coach failed: boom/);
});

test("reviewPoll (F6): wait while the server writes the review, show it when done, offer it again if it stopped", () => {
  const mk = (extra) => [{ id: "s1", attempt: 1, reviewed: false, review_in_progress: false }, Object.assign({ id: "s2", attempt: 1 }, extra)];
  assert.deepEqual(reviewPoll(mk({ reviewed: false, review_in_progress: true }), "s2"), { action: "wait" });
  const done = reviewPoll(mk({ reviewed: true, review: { verdict: "ok" }, review_in_progress: false }), "s2");
  assert.equal(done.action, "done");
  assert.deepEqual(done.review, { verdict: "ok" });
  assert.deepEqual(reviewPoll(mk({ reviewed: false, review_in_progress: false }), "s2"), { action: "offer" });
  assert.deepEqual(reviewPoll([], "s2"), { action: "offer" });
  assert.deepEqual(reviewPoll(null, "s2"), { action: "offer" });
});
