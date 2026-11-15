// The "Get started" checklist on Home: which steps there are and where each one stands. No DOM
// in here, so node can test it. Every tick comes from the overview payload, which the server
// builds from the real files; nothing is marked by hand.

/** The browser's memory of "Hide" on the checklist. */
export const HIDE_KEY = "prep.start.hidden";

/**
 * The steps as [{key, state, next}], in order. `state` is "done", "doing" or "todo"; `next` is
 * true on the first step that is not done. `o` is the overview payload; `st` is a newer
 * statements status ({have, total, running}) when a download has been polled, else null.
 *
 * The order is the order the work is done in: statements, the plan chat, module 00's self-check,
 * the diagnostic, then a first solve. A server from before the checklist sends no `onboarding`:
 * the three coach steps are then left out, since nothing could ever tick them.
 */
export function stepStates(o, st) {
  const setup = (o && o.setup) || {};
  const have = Number(st ? st.have : setup.statements_have) || 0;
  const total = Number(st ? st.total : setup.statements_total) || 0;
  const solved = Number(o && o.kpis && o.kpis.solved) || 0;
  const ob = o && o.onboarding;
  const steps = [{ key: "statements", done: have >= total, doing: !!(st && st.running) }];
  if (ob && typeof ob === "object") {
    steps.push({ key: "plan", done: !!ob.discovery, doing: !!ob.discovery_started });
    steps.push({ key: "selfcheck", done: !!ob.self_check, doing: false });
    steps.push({ key: "diagnostic", done: !!ob.diagnostic, doing: !!ob.diagnostic_started });
  }
  steps.push({ key: "solve", done: solved > 0, doing: false });
  const next = steps.find((s) => !s.done);
  return steps.map((s) => ({
    key: s.key,
    state: s.done ? "done" : (s.doing ? "doing" : "todo"),
    next: s === next,
  }));
}

const isDone = (steps, key) => steps.some((s) => s.key === key && s.state === "done");

/** Can the card be hidden yet? Once the statements are here and a first problem is solved. */
export function canHide(steps) {
  return isDone(steps, "statements") && isDone(steps, "solve");
}

/** Does the card show? Not when every step is ticked, and not when it was hidden. */
export function showStart(steps, hidden) {
  if (!steps.some((s) => s.state !== "done")) return false;
  return !(hidden && canHide(steps));
}

/** "1 of 5 done". */
export function countLabel(steps) {
  return steps.filter((s) => s.state === "done").length + " of " + steps.length + " done";
}
