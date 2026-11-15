// The practice workspace at #/practice/<slug>: the problem, the four "Before you code" boxes, the
// editor with autosave, Run and Submit with their results, and the coach. The pure helpers at the
// top never touch the DOM, so node can import this file for the unit tests. main.js is loaded
// lazily inside render() for the same reason (it builds the shell when it is imported).
import { get, post, put, ApiError } from "./api.js";
import { h, clear, sanitizeHtml, confirmDialog, difficultyPill, statusMark, toast } from "./ui.js";
import { renderMarkdown, highlightPython } from "./md.js";
import { createEditor, keyLabels, isMacPlatform } from "./editor.js";
import { createCoach } from "./coach.js";
import { redoQuestion } from "./redo.js";
import {
  MAIN_TAB, MAIN_NAME, MAX_TAB_NAME, MAX_TABS, hasTabs, tabsOf, cleanTabName, sameTabs, pickTab,
  draftText, changedDraft, patchDraft, historyRows, historyLabel, historyMeta,
} from "./tabs.js";
import { starButton } from "./star.js";
import { layoutStatement } from "./statement.js";

// ---- pure helpers ---------------------------------------------------------------

const TEX = [
  [/\\(?:text|textbf|textit|texttt|mathrm|mathbf|mathit|operatorname)\{([^{}]*)\}/g, "$1"],
  [/\\times(?![a-zA-Z])/g, "×"], [/\\cdot(?![a-zA-Z])/g, "·"],
  [/\\leq?(?![a-zA-Z])/g, "≤"], [/\\geq?(?![a-zA-Z])/g, "≥"], [/\\neq?(?![a-zA-Z])/g, "≠"],
  [/\\approx(?![a-zA-Z])/g, "≈"], [/\\pm(?![a-zA-Z])/g, "±"], [/\\infty(?![a-zA-Z])/g, "∞"],
  [/\\(?:ldots|dots|cdots)(?![a-zA-Z])/g, "…"], [/\\(?:to|rightarrow)(?![a-zA-Z])/g, "→"],
  [/\\in(?![a-zA-Z])/g, "∈"], [/\\sqrt(?![a-zA-Z])/g, "√"], [/\\sum(?![a-zA-Z])/g, "∑"],
  [/\\lfloor(?![a-zA-Z])/g, "⌊"], [/\\rfloor(?![a-zA-Z])/g, "⌋"],
  [/\\lceil(?![a-zA-Z])/g, "⌈"], [/\\rceil(?![a-zA-Z])/g, "⌉"],
  [/\\([{}%#&$_])/g, "\u0000$1"], // escaped literals survive the brace and underscore passes
  [/\\[,;!: ]/g, " "],
  [/\^\{([^{}]*)\}/g, "<sup>$1</sup>"], [/\^(-?\d+|[A-Za-z])/g, "<sup>$1</sup>"],
  [/_\{([^{}]*)\}/g, "<sub>$1</sub>"], [/_(\d+|[a-z])(?![A-Za-z0-9])/g, "<sub>$1</sub>"],
  [/\\([a-zA-Z]+)/g, "$1"], // \log, \min, \max and anything unknown: the bare word
  [/[{}]/g, ""],
];

function plainMaths(tex) {
  let s = tex.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  for (const [re, to] of TEX) s = s.replace(re, to);
  // Left-over * and _ would turn into emphasis in the Markdown around it.
  s = s.replace(/(^|[^\u0000])([*_])/g, "$1\\$2");
  return s.replace(/\u0000/g, "");
}

/**
 * Tidy a NeetCode statement for the Markdown renderer: inline $…$ maths becomes plain text with
 * <sup>/<sub> (angle brackets escaped, so the maths can never become HTML), and the trailing
 * "Company Tags" NeetCode Pro upsell goes. Code spans and fenced blocks are left as they are.
 */
export function cleanNeetcode(md) {
  let s = String(md == null ? "" : md);
  s = s.replace(/(?:\s*<br\s*\/?>)*\s*<details class="company-tags-accordion">[\s\S]*?<\/details>/g, "");
  s = s.replace(/(?:\s*<br\s*\/?>)+\s*$/, "");
  return s.split(/(```[\s\S]*?(?:```|$)|`[^`\n]*`)/).map((part, i) => (i % 2 ? part
    : part.replace(/\$(?![\s$])([^$\n]+?)(?<!\s)\$/g, (_m, tex) => plainMaths(tex)))).join("");
}

const pad2 = (n) => String(n).padStart(2, "0");

/** Seconds -> "mm:ss", or "h:mm:ss" from one hour. */
export function fmtClock(seconds) {
  let n = Number(seconds);
  if (!Number.isFinite(n) || n < 0) n = 0;
  n = Math.floor(n);
  const hrs = Math.floor(n / 3600);
  const min = Math.floor((n % 3600) / 60);
  const sec = n % 60;
  return hrs ? hrs + ":" + pad2(min) + ":" + pad2(sec) : pad2(min) + ":" + pad2(sec);
}

/** A case's run time in words: "<1 ms", "3 ms", "1.2 s"; "" when there is none. */
export function fmtMs(ms) {
  if (ms === null || ms === undefined || !Number.isFinite(Number(ms))) return "";
  const n = Number(ms);
  if (n < 1) return "<1 ms";
  if (Math.round(n) < 1000) return Math.round(n) + " ms";
  return (n / 1000).toFixed(1) + " s";
}

const lineOf = (e) => (e && Number.isInteger(e.line) && e.line > 0 ? e.line : null);

/** "IndexError on line 4: list index out of range" (no line, no " on line"). */
export function errorText(err) {
  if (!err) return "";
  const line = lineOf(err);
  return (err.type || "Error") + (line ? " on line " + line : "") + (err.message ? ": " + err.message : "");
}

const withTime = (words, r) => {
  const t = fmtMs(r.ms);
  return t ? words + " · " + t : words;
};

/** One line of the output strip: {icon, tone, name, note, open}. */
export function caseRow(r) {
  const name = r.name || "Case";
  switch (r.status) {
    case "pass":
      return { icon: "✓", tone: "pass", name, note: fmtMs(r.ms), open: false };
    case "fail":
      return { icon: "✗", tone: "fail", name, note: withTime("wrong answer", r), open: true };
    case "timeout":
      return { icon: "⏱", tone: "timeout", name, note: "timed out", open: true };
    case "not_run":
      return { icon: "–", tone: "skip", name, note: "not run", open: false };
    default: {
      const e = r.error;
      const line = lineOf(e);
      const head = ((e && e.type) || "Error") + (line ? " on line " + line : "");
      return { icon: "✗", tone: "error", name, note: withTime(head, r), open: true };
    }
  }
}

/** The [label, value] pairs a failing case shows when it is expanded. */
export function caseFields(r) {
  const rows = [["Input", r.input], ["Expected", r.expected]];
  if (r.status === "fail") rows.push(["Got", r.got]);
  if (r.status === "error") {
    rows.push(["Error", r.error ? errorText(r.error) : r.message || "Error"]);
    if (r.error && r.error.trace) rows.push(["Traceback", r.error.trace]);
  }
  if (r.status === "timeout" && r.message) rows.push(["Note", r.message]);
  if (r.stdout) rows.push(["Printed output", r.stdout]);
  return rows.filter(([, v]) => v !== null && v !== undefined);
}

/** The headline of a run or a submit. Never a LeetCode verdict: these are the app's tests. */
export function resultSummary(result, kind) {
  const results = result.results || [];
  const ran = results.some((r) => r.status && r.status !== "not_run");
  const total = Number(result.total) || 0;
  const passed = Number(result.passed) || 0;
  if ((result.fatal && !ran) || !total) return { tone: "bad", text: "No test ran" };
  const all = passed === total;
  if (kind === "submit") {
    return all ? { tone: "good", text: "All " + total + " of the app's tests pass" }
      : { tone: "bad", text: passed + " of " + total + " of the app's tests pass" };
  }
  if (all) {
    return { tone: "good", text: total === 1 ? "The example passes" : total === 2 ? "Both examples pass"
      : "All " + total + " examples pass" };
  }
  return { tone: "bad", text: total === 1 ? "The example does not pass" : passed + " of " + total + " examples pass" };
}

const attemptOf = (s) => s.attempt || 1;

/** Chat turns and this attempt's written reviews, in time order, for the coach pane. */
export function historyItems(chat, submits, attempt) {
  const a = attempt || 1;
  const items = (chat || []).map((c) => Object.assign({ type: "chat" }, c));
  for (const s of submits || []) {
    if (attemptOf(s) !== a || !s.reviewed || !s.review) continue;
    items.push({ type: "review", at: s.at, submitId: s.id, review: s.review, passed: s.passed, total: s.total });
  }
  return items.sort((x, y) => (x.at < y.at ? -1 : x.at > y.at ? 1 : 0));
}

/** The id of this attempt's latest submit when it still has no review, else null. */
export function unreviewedSubmit(submits, attempt) {
  const mine = (submits || []).filter((s) => attemptOf(s) === (attempt || 1));
  const last = mine[mine.length - 1];
  return last && !last.reviewed ? last.id : null;
}

const normCode = (s) => String(s == null ? "" : s).replace(/\r\n?/g, "\n").trim();

/** True when the editor holds the starting skeleton (or nothing): there is no solution to run yet. */
export function isUntouchedSkeleton(code, skeleton) {
  const c = normCode(code);
  return c === "" || c === normCode(skeleton);
}

/**
 * "Solved before · new attempt" while a Redo'd problem has no passing submit in its new attempt;
 * null otherwise (the plain solved mark is right then, or the problem is not solved).
 */
export function attemptNote(p) {
  if (!p || p.status !== "solved" || (p.attempt || 1) <= 1) return null;
  const passed = (p.submits || []).some((s) => (s.attempt || 1) === p.attempt && s.ok);
  return passed ? null : "Solved before · new attempt";
}

/** What the submit result says about the final review, by the state the coach pane reports. */
export function reviewFlagText(state) {
  if (state === "queued") return "The final review starts when the coach finishes its answer.";
  if (state === "writing") return "Final review in progress in the coach pane. Stay on this page.";
  if (state === "done") return "The final review is ready in the coach pane.";
  if (state === "failed") return "No final review was written. See the coach pane.";
  if (state === "again") return "Not reviewed: another final review is still being written.";
  return null;
}

/** Where the free-text notes tab lives in localStorage. */
export function scratchKey(slug, attempt) {
  return "prep:scratch:" + slug + ":" + (attempt || 1);
}

/** After a save of `sent` came back: what is saved now, and is the editor still ahead of it? */
export function nextSaveState({ current, sent }) {
  return { saved: sent, dirty: current !== sent };
}

const realClock = {
  schedule: (fn, ms) => setTimeout(fn, ms),
  cancel: (t) => clearTimeout(t),
};

/**
 * The words next to the editor. A failure or a stale tab always wins; a warning from the server
 * ("the state could not be written") never reads as "Saved".
 */
export function saveLabel({ saving, error, dirty, warning, stale }) {
  if (stale) return "Not saved: changed in another tab";
  if (error) {
    return error.status === 413 ? "Not saved: over 200,000 characters"
      : "Not saved: " + (error.detail || "the server did not answer");
  }
  if (saving) return "Saving…";
  if (warning) return "Not saved: " + warning;
  return dirty ? "Not saved yet" : "Saved";
}

const isStaleError = (e) => !!e && e.status === 409 && e.code === "stale";

/**
 * The draft autosave, without the DOM. One PUT at a time; the editor is never written back to.
 *   snap()            the text to save now (a JSON string of code and the four boxes)
 *   saved             the text the server already has
 *   send(text)        the PUT, a promise; keep(text) the keepalive PUT used on leaving
 *   onState({saving, error, dirty, warning, stale})  after every change of state
 *   onStale(err)      once, when the server says another tab changed the problem (409 stale);
 *                     saving stops until reset(text) is called. stall(err) does the same for a
 *                     Run or Submit that got the 409.
 * `warning` is the server's save_error from the last answer.
 * A failed save is retried once, `retryMs` later, if the text is still unsaved; the error stays
 * until a save succeeds. hold() stops all saving (Reset and Redo call it before their POST) and
 * resolves once no save is in flight; edits while held are ignored, release() looks again.
 */
export function createSaver({ snap, saved, send, keep, onState = () => {}, onStale = () => {},
  clock = realClock, delay = 1000, retryMs = 5000 }) {
  let timer = null;
  let retryTimer = null;
  let inflight = null; // {text, promise}
  let error = null;
  let retried = false;
  let held = false;
  let dead = false;
  let lastFlush = null;
  let warning = null;
  let stalled = false;
  let heldText = null; // the text when the hold began
  let leaveText = null; // the text when the page was left during a hold
  const stopTimers = () => {
    if (timer !== null) { clock.cancel(timer); timer = null; }
    if (retryTimer !== null) { clock.cancel(retryTimer); retryTimer = null; }
  };
  const report = () => {
    if (!dead) onState({ saving: !!inflight, error, dirty: snap() !== saved, warning, stale: stalled });
  };
  const stall = (err) => {
    if (stalled || dead) return;
    stalled = true;
    stopTimers();
    onStale(err);
    report();
  };

  function changed() {
    if (dead || held || stalled) return;
    stopTimers();
    retried = false;
    timer = clock.schedule(save, delay);
    report();
  }

  function save() {
    stopTimers();
    if (dead || held || stalled) return inflight ? inflight.promise : null;
    if (inflight) return inflight.promise;
    const text = snap();
    if (text === saved) { error = null; report(); return null; }
    const mine = { text };
    mine.promise = Promise.resolve().then(() => send(text)).then((res) => {
      saved = text;
      error = null;
      warning = (res && res.save_error) || null;
      retried = false;
      return nextSaveState({ current: dead ? text : snap(), sent: text }).dirty;
    }, (err) => {
      if (isStaleError(err)) { stall(err); return false; }
      error = err || new Error("save failed");
      if (!retried && !held && !dead && !stalled) {
        retried = true;
        retryTimer = clock.schedule(() => { retryTimer = null; if (snap() !== saved) save(); }, retryMs);
      }
      return false;
    }).then((dirty) => {
      if (inflight === mine) inflight = null;
      report();
      if (dirty) changed();
    });
    inflight = mine;
    report();
    return mine.promise;
  }

  /** Leaving the page: send what is not saved yet, unless that exact text is already on its way. */
  function flush() {
    stopTimers();
    if (held || dead || stalled) return; // a Reset or Redo owns the draft until its answer is applied
    const text = snap();
    if (text === saved || text === lastFlush) return;
    if (inflight && inflight.text === text) return;
    lastFlush = text;
    Promise.resolve().then(() => keep(text)).then((res) => {
      // The page did not go away (a cancelled unload, the back-forward cache): the server has
      // this text now, so the label must not keep saying "Not saved yet".
      if (dead || inflight || held || stalled) return;
      saved = text;
      warning = (res && res.save_error) || null;
      report();
    }).catch(() => {});
  }

  async function hold() {
    held = true;
    heldText = snap();
    stopTimers();
    if (inflight) await inflight.promise;
  }

  function release() {
    held = false;
    if (dead) {
      // The page was left during the hold. Text typed since the hold began goes out now, once.
      const text = leaveText;
      leaveText = null;
      if (text !== null && text !== heldText && text !== saved) {
        Promise.resolve().then(() => keep(text)).catch(() => {});
      }
      return;
    }
    if (snap() !== saved) changed(); else report();
  }

  /** A newer copy was loaded in place: what the server has is now `text`; saving may go on. */
  function reset(text) {
    saved = text;
    stalled = false;
    error = null;
    warning = null;
    lastFlush = null;
    report();
  }

  return {
    changed, save, flush, hold, release, stall, reset,
    /** The server's save_error from a Reset, a Redo or the heartbeat. */
    setWarning(text) { warning = text || null; report(); },
    get stalled() { return stalled; },
    get saved() { return saved; },
    set saved(text) { saved = text; },
    get busy() { return !!inflight; },
    destroy() {
      if (held && !dead) leaveText = snap();
      dead = true;
      stopTimers();
    },
  };
}

// ---- the page -----------------------------------------------------------------------

const COACH_KEY = "prep:coachHidden";
const SAVE_MS = 1000;
const STALE_TEXT = "This problem changed in another tab. Reload to see the newer code.";
const MAX_BEAT = 30; // longest stretch the leave-page heartbeat and a submit may carry
const KEEPALIVE_MAX = 60000; // browsers refuse keepalive bodies over 64 KB
const BOXES = [
  ["pattern", "Pattern and signal", "Which pattern, and what in the statement points to it?"],
  ["complexity", "Complexity and why", "Time and space, and the reason for each."],
  ["tests", "Edge cases to test", "Inputs that could break it: empty, one item, duplicates…"],
  ["trace", "Hand trace on the smallest input", "Walk the smallest example through your plan, step by step."],
];

// Saves still in flight per problem (a flush on leaving). Opening the same problem again waits
// for them, so it never loads the text from before the last keystrokes.
const pendingSaves = new Map();

const lsGet = (k) => { try { return localStorage.getItem(k); } catch (e) { return null; } };
const lsSet = (k, v) => {
  try { if (v === null) localStorage.removeItem(k); else localStorage.setItem(k, v); } catch (e) { /* private mode */ }
};

function track(slug, promise) {
  const p = promise.catch(() => {}).finally(() => { if (pendingSaves.get(slug) === p) pendingSaves.delete(slug); });
  pendingSaves.set(slug, p);
  return promise;
}

export async function render(container, params) {
  const { slug, isStale } = params;
  document.title = "Practice · LeetCode Prep";
  container.classList.add("pr-page");
  container.append(h("p", { class: "pr-loading", role: "status" }, "Loading the problem…"));
  const shell = await import("./main.js");
  if (isStale()) return null;
  let view = null;
  let gone = false;
  const stale = () => gone || isStale();

  async function load() {
    if (pendingSaves.has(slug)) await pendingSaves.get(slug);
    if (stale()) return;
    let p;
    let setup = null;
    try {
      [p, setup] = await Promise.all([get("/problem/" + encodeURIComponent(slug)),
        get("/setup/status").catch(() => null)]);
    } catch (e) {
      if (stale()) return;
      clear(container);
      container.append(failPage(e, slug));
      return;
    }
    if (stale()) return;
    clear(container);
    view = build(container, p, { setup, shell, stale, reload: async () => {
      if (view) view.destroy({ save: false });
      view = null;
      clear(container);
      container.append(h("p", { class: "pr-loading", role: "status" }, "Loading the problem…"));
      await load();
    } });
  }
  await load();
  if (isStale()) return null;
  return () => {
    gone = true;
    if (view) view.destroy({ save: true });
    view = null;
  };
}

function failPage(e, slug) {
  const missing = e instanceof ApiError && e.status === 404;
  document.title = (missing ? "Problem not found" : "Something went wrong") + " · LeetCode Prep";
  return h("div", { class: "pr-fail" },
    h("h1", null, missing ? "Problem not found" : "The problem could not be loaded"),
    h("p", null, missing ? "There is no problem called “" + slug + "” in the app."
      : (e && e.detail) || (e && e.message) || "The server did not answer."),
    h("p", { class: "pr-fail-actions" },
      h("a", { class: "btn", href: "#/" }, "← Home"),
      h("a", { class: "btn", href: "#/practice" }, "All problems"),
      missing ? null : h("button", { class: "btn btn-primary", type: "button", onclick: () => location.reload() }, "Retry")));
}

/** Build the workspace for problem `p` inside `root`. Returns {destroy({save})}. */
function build(root, p, { setup, shell, stale, reload }) {
  const slug = p.slug;
  const path = "/problem/" + encodeURIComponent(slug);
  const mac = isMacPlatform(navigator);
  const keys = keyLabels(mac);
  const cleanups = [];
  const listen = (target, ev, fn, opts) => {
    target.addEventListener(ev, fn, opts);
    cleanups.push(() => target.removeEventListener(ev, fn, opts));
  };
  let dead = false;
  const isDead = () => dead || stale();
  // One thing at a time changes the stored problem from this page: a run, a submit, a reset, a
  // redo or a tab change. `idle` resolves when the current one is over.
  let running = null;
  let runCtrl = null;
  let idle = Promise.resolve();
  let idleDone = null;
  const busy = (what) => {
    running = what;
    idle = new Promise((r) => { idleDone = r; });
    syncButtons();
  };
  const free = () => {
    running = null;
    if (idleDone) idleDone();
    idleDone = null;
    syncButtons();
  };
  document.title = p.title + " · Practice · LeetCode Prep";

  // ---- top bar ----
  let seconds = Number(p.seconds) || 0;
  const clock = h("span", { class: "pr-clock" }, fmtClock(seconds));
  const timer = h("span", { class: "pr-timer", title: "Active time on this problem, all attempts" },
    h("span", { class: "sr-only" }, "Time on this problem: "), clock);
  const statusBox = h("span", { class: "pr-status" });
  const drawStatus = () => {
    clear(statusBox);
    const note = attemptNote(p);
    if (note) statusBox.append(h("span", { class: "status status-solved" },
      h("span", { class: "status-icon", "aria-hidden": "true" }, "✓"), " " + note));
    else if (p.status === "solved") statusBox.append(statusMark("solved"));
    else if (p.status === "attempted") statusBox.append(statusMark("attempted"));
  };
  drawStatus();
  const toggle = h("button", { class: "btn btn-sm pr-coach-toggle", type: "button", "aria-controls": "pr-coach" });
  const meta = h("span", { class: "pr-meta" },
    "Module " + p.module + (p.module_title ? " · " + p.module_title : "") + " · ", difficultyPill(p.difficulty));
  const top = h("header", { class: "pr-top" },
    h("a", { class: "btn btn-quiet btn-sm pr-home", href: "#/" }, "← Home"),
    h("h1", { class: "pr-title" }, (p.number ? p.number + ". " : "") + p.title),
    starButton(p, { isStale: stale, cls: "pr-star" }), meta, statusBox, h("span", { class: "pr-spacer" }), timer, toggle);

  // ---- problem pane ----
  const noteBoxes = {};
  const boxes = BOXES.map(([key, label, hint]) => {
    const id = "pr-note-" + key;
    const ta = h("textarea", { class: "pr-box-input", id, rows: "2", placeholder: hint, spellcheck: "true" });
    ta.value = (p.notes && p.notes[key]) || "";
    noteBoxes[key] = ta;
    return h("div", { class: "pr-box" }, h("label", { for: id }, label), ta);
  });
  const notesNow = () => {
    const n = {};
    for (const [key] of BOXES) n[key] = noteBoxes[key].value;
    return n;
  };
  const problem = h("section", { class: "pr-pane pr-problem", "aria-label": "Problem" },
    statementBlock(p),
    h("div", { class: "pr-before" },
      h("h2", { class: "pr-h" }, "Before you code"),
      h("p", { class: "pr-sub" }, "Saved with your draft. The coach and the final review read them."),
      boxes));

  // ---- editor and tabs ----
  // `multi` is false with a server from before tabs: one tab, no history, the older draft shape.
  const multi = hasTabs(p);
  const initial = tabsOf(p);
  let tabList = initial.map(({ id, name }) => ({ id, name }));
  const TAB_KEY = "prep:tab:" + slug;
  let cur = pickTab(tabList, lsGet(TAB_KEY)); // the solution tab the editor shows
  let panel = "code"; // which panel is on screen: "code" | "notes" | "history"
  const nameOf = (id) => (tabList.find((t) => t.id === id) || { name: MAIN_NAME }).name;
  const editorHost = h("div", { class: "pr-editor", id: "pr-panel-code", role: "tabpanel",
    "aria-labelledby": "pr-tab-code-" + cur });
  const scratch = h("textarea", { class: "pr-scratch", "aria-label": "Free notes",
    placeholder: "Anything else: ideas, a plan, things to look up." });
  const sKey = scratchKey(slug, p.attempt);
  scratch.value = lsGet(sKey) || "";
  const scratchPanel = h("div", { class: "pr-scratch-panel", id: "pr-panel-notes", role: "tabpanel",
    "aria-labelledby": "pr-tab-notes", hidden: true },
  h("p", { class: "pr-sub" }, "These notes stay in this browser only. The coach reads the four boxes on the left, not this."),
  scratch);
  const codeTabs = h("span", { class: "pr-codetabs", role: "presentation" });
  const addBtn = h("button", { class: "pr-tab-add pr-lock", type: "button", "aria-label": "New solution tab",
    title: "New solution tab", hidden: !multi }, "+");
  const tabNotes = h("button", { class: "pr-tab", id: "pr-tab-notes", role: "tab", type: "button",
    "aria-selected": "false", "aria-controls": "pr-panel-notes", tabindex: "-1" }, "notes");
  const histCount = h("span", { class: "pr-tab-count", hidden: true });
  const tabHist = h("button", { class: "pr-tab", id: "pr-tab-history", role: "tab", type: "button",
    "aria-selected": "false", "aria-controls": "pr-panel-history", tabindex: "-1" }, "history", histCount);
  const saveState = h("span", { class: "pr-save" }, "Saved");
  const tablist = h("div", { role: "tablist", "aria-label": "Files", class: "pr-tablist" },
    codeTabs, addBtn, h("span", { class: "pr-tab-gap", role: "presentation" }), tabNotes, tabHist);
  const tabs = h("div", { class: "pr-tabs" }, tablist, saveState);

  // The history panel: every earlier version of the code, and the way back into a solved problem.
  const redoBtn2 = h("button", { class: "btn btn-sm pr-lock", type: "button" }, "↻ Redo from scratch");
  const histRetry = h("div", { class: "pr-hist-retry", hidden: p.status !== "solved" },
    h("p", null, "You solved this one. To practise it again, start from a blank skeleton. The versions below stay here."),
    redoBtn2);
  const histList = h("div", { class: "pr-hist-list" });
  const histPanel = h("div", { class: "pr-hist", id: "pr-panel-history", role: "tabpanel",
    "aria-labelledby": "pr-tab-history", hidden: true },
  h("p", { class: "pr-sub" }, "Every submit is kept here, with the code from before a reset, a redo or a closed tab. "
    + "Open one to read it" + (multi ? " or to bring it back in a new tab." : ".")),
  multi ? null : h("p", { class: "notice notice-warn" }, "Tabs and the history need the newer version of the app. "
    + "Stop it (Ctrl+C in its terminal window) and start it again."),
  histRetry, histList);

  const runBtn = h("button", { class: "btn btn-primary pr-run", type: "button",
    title: "Run the examples (" + keys.run + ")" }, "▶ Run examples");
  const submitBtn = h("button", { class: "btn pr-submit", type: "button" }, "Submit for final review");
  const resetBtn = h("button", { class: "btn btn-quiet btn-sm", type: "button" }, "Reset to skeleton");
  const redoBtn = h("button", { class: "btn btn-sm pr-redo", type: "button", hidden: p.status !== "solved",
    title: "Solve this problem again from a blank skeleton" }, "↻ Redo from scratch");
  const syncSolved = () => { redoBtn.hidden = histRetry.hidden = p.status !== "solved"; };
  const actions = h("div", { class: "pr-actions" }, runBtn, submitBtn,
    h("span", { class: "pr-keys" }, keys.run + " runs · " + keys.save + " saves · " + keys.comment
      + " comments · Esc then Tab leaves the editor"),
    h("span", { class: "pr-spacer" }), resetBtn, redoBtn);
  const outLive = h("div", { class: "sr-only", role: "status", "aria-live": "polite" });
  const out = h("div", { class: "pr-out", tabindex: "0", "aria-label": "Results" },
    h("p", { class: "pr-out-empty" }, "Run the examples to see each case here."));
  // Shown when the server says another tab changed this problem (409 stale). It stays until the
  // newer copy is loaded: nothing is saved or run from here before that.
  const staleReload = h("button", { class: "btn btn-sm", type: "button" }, "Reload");
  const staleNote = h("div", { class: "notice notice-warn pr-stale", role: "alert", hidden: true },
    h("p", null, STALE_TEXT), staleReload);
  const work = h("section", { class: "pr-pane pr-work", "aria-label": "Code" },
    staleNote, tabs, editorHost, scratchPanel, histPanel, actions, out, outLive);

  // ---- coach ----
  const pendingId = unreviewedSubmit(p.submits, p.attempt);
  const pendingRec = pendingId ? (p.submits || []).find((x) => x.id === pendingId) : null;
  // The note beside the last submit's result; the coach pane reports the review's progress to it.
  let reviewFlag = null;
  function setReviewFlag(state) {
    const text = reviewFlagText(state);
    if (!reviewFlag || !text || (setup && setup.claude === false)) return;
    clear(reviewFlag);
    reviewFlag.className = "pr-review-flag pr-review-flag-" + state;
    if (state === "writing") reviewFlag.append(h("span", { class: "pr-spin pr-spin-sm", "aria-hidden": "true" }));
    if (state === "done") reviewFlag.append(h("span", { "aria-hidden": "true" }, "✓"));
    reviewFlag.append(h("span", null, text));
    if (state === "again") reviewFlag = null; // the running review belongs to an earlier submit
  }

  const coach = createCoach({
    slug, isStale: isDead,
    // An ask waits for a run or a tab change to end, and for the autosave: the coach route stores
    // the code it is sent, and that must not cross one of the page's own saves.
    context: async () => {
      while (running && !isDead()) await idle;
      await saveAll();
      return { code: editor.getValue(cur), notes: notesNow(), tab: multi ? cur : undefined };
    },
    claude: setup ? setup.claude !== false : true,
    setup,
    history: historyItems(p.chat, p.submits, p.attempt),
    pendingSubmit: pendingId,
    reviewing: !!(pendingRec && pendingRec.review_in_progress),
    onOpen: () => setCoach(true),
    onReview: setReviewFlag,
  });

  const grid = h("div", { class: "pr-grid" }, problem, work, coach.el);
  root.append(top, grid);

  // ---- editor ----
  const editor = createEditor(editorHost, {
    value: initial[0].code,
    docId: MAIN_TAB,
    label: nameOf(cur) + ", Python code editor",
    onChange: () => changed(),
    onRun: () => runCode("run"),
    onSave: () => saveNow(),
  });
  for (const t of initial.slice(1)) editor.openDoc(t.id, t.code);
  editor.showDoc(cur);

  // ---- coach toggle ----
  function setCoach(show, remember = true) {
    grid.classList.toggle("pr-no-coach", !show);
    coach.el.hidden = !show;
    toggle.textContent = show ? "Hide coach ⟩" : "⟨ Show coach";
    toggle.setAttribute("aria-expanded", String(show));
    if (remember) lsSet(COACH_KEY, show ? null : "1");
    editor.refresh();
  }
  setCoach(lsGet(COACH_KEY) !== "1", false);
  toggle.addEventListener("click", () => {
    const show = coach.el.hidden;
    setCoach(show);
    if (show) coach.focusInput();
  });

  // ---- tabs ----
  // The bar holds one tab per solution file, then "notes" and "history".
  const tabBtns = new Map(); // tab id -> its button
  function syncTabs() {
    for (const [id, btn] of tabBtns) {
      const on = panel === "code" && id === cur;
      btn.setAttribute("aria-selected", String(on));
      btn.tabIndex = on ? 0 : -1;
      if (btn.parentNode) btn.parentNode.classList.toggle("pr-tab-current", id === cur);
    }
    for (const [btn, which] of [[tabNotes, "notes"], [tabHist, "history"]]) {
      btn.setAttribute("aria-selected", String(panel === which));
      btn.tabIndex = panel === which ? 0 : -1;
    }
    editorHost.setAttribute("aria-labelledby", "pr-tab-code-" + cur);
    editor.setLabel(nameOf(cur) + ", Python code editor");
  }
  function showPanel(which) {
    panel = which;
    editorHost.hidden = which !== "code";
    scratchPanel.hidden = which !== "notes";
    histPanel.hidden = which !== "history";
    syncTabs();
    if (which === "code") editor.refresh();
  }
  function showCode(id) {
    if (!editor.showDoc(id)) return;
    cur = id;
    lsSet(TAB_KEY, id === MAIN_TAB ? null : String(id));
    showPanel("code");
    const btn = tabBtns.get(id);
    if (btn && btn.parentNode) btn.parentNode.scrollIntoView({ block: "nearest", inline: "nearest" });
  }
  function drawTabs() {
    clear(codeTabs);
    tabBtns.clear();
    for (const t of tabList) {
      const btn = h("button", { class: "pr-tab pr-tab-code", id: "pr-tab-code-" + t.id, role: "tab", type: "button",
        "aria-selected": "false", "aria-controls": "pr-panel-code", tabindex: "-1", dataset: { tab: String(t.id) },
        title: multi ? "Double-click to rename" : null }, t.name);
      const close = t.id === MAIN_TAB ? null : h("button", { class: "pr-tab-x pr-lock", type: "button",
        tabindex: "-1", dataset: { close: String(t.id) }, "aria-label": "Close " + t.name, title: "Close this tab" }, "×");
      tabBtns.set(t.id, btn);
      codeTabs.append(h("span", { class: "pr-tabwrap", role: "presentation" }, btn, close));
    }
    syncTabs();
    syncButtons();
  }
  tablist.addEventListener("click", (e) => {
    const x = e.target.closest("[data-close]");
    if (x) { closeTab(Number(x.dataset.close)); return; }
    const tab = e.target.closest('[role="tab"]');
    if (!tab) return;
    if (tab === tabNotes) showPanel("notes");
    else if (tab === tabHist) showPanel("history");
    else {
      showCode(Number(tab.dataset.tab));
      if (e.detail > 0) editor.focus(); // a mouse click goes on to the code; the keyboard stays on the tab
    }
  });
  tablist.addEventListener("dblclick", (e) => {
    const tab = e.target.closest(".pr-tab-code");
    if (tab) renameTab(Number(tab.dataset.tab));
  });
  tablist.addEventListener("keydown", (e) => {
    const tab = e.target;
    if (!tab.getAttribute || tab.getAttribute("role") !== "tab") return;
    const all = Array.from(tablist.querySelectorAll('[role="tab"]'));
    const at = all.indexOf(tab);
    const id = Number(tab.dataset.tab);
    let next = null;
    if (e.key === "ArrowRight") next = all[(at + 1) % all.length];
    else if (e.key === "ArrowLeft") next = all[(at - 1 + all.length) % all.length];
    else if (e.key === "Home") next = all[0];
    else if (e.key === "End") next = all[all.length - 1];
    else if (e.key === "F2" && id) { e.preventDefault(); renameTab(id); return; }
    else if (e.key === "Delete" && id && id !== MAIN_TAB) { e.preventDefault(); closeTab(id, true); return; }
    if (!next) return;
    e.preventDefault();
    next.click();
    next.focus();
  });
  addBtn.addEventListener("click", () => addTab());

  // Double-click (or F2) turns a tab into a text box for its name.
  function renameTab(id) {
    const t = tabList.find((x) => x.id === id);
    const btn = tabBtns.get(id);
    if (!multi || !t || !btn || !btn.parentNode || running || saver.stalled) return;
    const input = h("input", { class: "pr-tab-edit", type: "text", maxlength: String(MAX_TAB_NAME),
      "aria-label": "Name of this tab", spellcheck: "false", autocomplete: "off" });
    input.value = t.name;
    const fit = () => { input.size = Math.max(6, input.value.length + 1); };
    fit();
    let done = false;
    const finish = (commit, refocus) => {
      if (done) return;
      done = true;
      const name = cleanTabName(input.value);
      input.replaceWith(btn);
      if (refocus) btn.focus();
      if (!commit || !name || name === t.name) return;
      tabOp("rename", async () => {
        const res = noteRev(await post(path + "/tab/rename", withRev({ tab: id, name })));
        if (isDead()) return;
        t.name = (res.tab && res.tab.name) || name;
        const had = document.activeElement === btn;
        drawTabs();
        if (had && tabBtns.get(id)) tabBtns.get(id).focus();
      }, "The tab could not be renamed");
    };
    input.addEventListener("input", fit);
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter") { e.preventDefault(); finish(true, true); }
      else if (e.key === "Escape") { e.preventDefault(); finish(false, true); }
    });
    input.addEventListener("blur", () => finish(true, false));
    btn.replaceWith(input);
    input.focus();
    input.select();
  }

  // Everything typed reaches the server before something else changes the stored problem.
  async function saveAll() {
    for (let i = 0; i < 2 && !isDead() && !saver.stalled && snap() !== saver.saved; i++) await saver.save();
  }
  // A change to the tabs on the server. The autosave goes first and then stays quiet, so two
  // requests from this page never carry the same version number.
  async function tabOp(what, fn, failText) {
    if (running || isDead() || behind()) return false;
    busy(what);
    let ok = false;
    await saveAll();
    await saver.hold();
    try {
      if (!isDead() && !saver.stalled) {
        await fn();
        ok = true;
      }
    } catch (e) {
      if (!isDead()) {
        if (e instanceof ApiError && e.status === 409 && e.code === "stale") saver.stall(e);
        else toast(failText + ": " + (e.detail || e.message), { kind: "error" });
      }
    } finally {
      saver.release();
      if (!isDead()) free();
    }
    return ok;
  }
  /** A new tab: the skeleton, or the code of history entry `fromHistory`. */
  function addTab(fromHistory) {
    if (!multi) return Promise.resolve(false);
    if (tabList.length >= MAX_TABS) {
      toast("A problem can have " + MAX_TABS + " tabs at most. Close one first.");
      return Promise.resolve(false);
    }
    return tabOp("tab", async () => {
      const res = noteRev(await post(path + "/tab",
        withRev(fromHistory === undefined ? {} : { from_history: fromHistory })));
      if (isDead()) return;
      const t = res.tab;
      const code = typeof t.code === "string" ? t.code : (p.skeleton ?? "");
      tabList.push({ id: t.id, name: t.name });
      editor.openDoc(t.id, code);
      saver.saved = patchDraft(saver.saved, t.id, code);
      drawTabs();
      showCode(t.id);
      editor.focus();
    }, "A new tab could not be opened");
  }
  async function closeTab(id, byKey = false) {
    const t = tabList.find((x) => x.id === id);
    if (!t || id === MAIN_TAB || running || behind()) return;
    if (!isUntouchedSkeleton(editor.getValue(id), p.skeleton)) {
      const ok = await confirmDialog("Close " + t.name + "? Its code stays in the history, where you can open it again.",
        { confirm: "Close the tab", focus: "cancel" });
      if (!ok || isDead() || running) return;
    }
    await tabOp("close", async () => {
      const res = noteRev(await post(path + "/tab/close", withRev({ tab: id })));
      if (isDead()) return;
      const at = tabList.findIndex((x) => x.id === id);
      tabList = tabList.filter((x) => x.id !== id);
      if (cur === id) {
        cur = tabList[Math.max(0, at - 1)].id;
        editor.showDoc(cur);
        lsSet(TAB_KEY, cur === MAIN_TAB ? null : String(cur));
      }
      editor.closeDoc(id);
      saver.saved = patchDraft(saver.saved, id, null);
      setHistory(res.history);
      drawTabs();
      if (panel === "code") editor.refresh();
      if (byKey && tabBtns.get(cur)) tabBtns.get(cur).focus();
    }, "The tab could not be closed");
  }

  // ---- history ----
  const histOpen = new Set(); // the rows left open, so a redraw keeps them open
  const histCode = new Map(); // the code of the entries already fetched
  const histKey = (rec) => rec.id + ":" + (rec.sha || "");
  function setHistory(list) {
    if (!Array.isArray(list)) return;
    p.history = list;
    drawHistory();
  }
  function drawHistory() {
    const rows = historyRows(p.history);
    histCount.textContent = String(rows.length);
    histCount.hidden = rows.length === 0;
    clear(histList);
    if (!rows.length) {
      if (multi) histList.append(h("p", { class: "pr-hist-note" }, "Nothing here yet. Your first submit will show up here."));
      return;
    }
    for (const rec of rows) histList.append(historyRow(rec));
  }
  function historyRow(rec) {
    const key = histKey(rec);
    const label = historyLabel(rec);
    const body = h("div", { class: "pr-hist-body" });
    const det = h("details", { class: "pr-hist-row" },
      h("summary", null, h("span", { class: "pr-hist-chip pr-hist-" + label.tone }, label.text),
        h("span", { class: "pr-hist-meta" }, historyMeta(rec))),
      body);
    let state = "idle"; // "idle" | "loading" | "shown"
    const show = (code) => {
      state = "shown";
      clear(body);
      const pre = h("pre", { class: "pr-hist-code", tabindex: "0", "aria-label": "The code of this version" });
      highlightPython(code, pre);
      const open = multi ? h("button", { class: "btn btn-sm pr-lock", type: "button" }, "Open in a new tab") : null;
      if (open) {
        open.disabled = running !== null;
        open.addEventListener("click", () => addTab(rec.id));
      }
      const copy = h("button", { class: "btn btn-sm", type: "button" }, "Copy");
      copy.addEventListener("click", async () => {
        try {
          await navigator.clipboard.writeText(code);
          toast("Copied.");
        } catch (e) {
          toast("The code could not be copied.", { kind: "error" });
        }
      });
      body.append(pre, h("div", { class: "pr-hist-actions" }, open, copy));
    };
    const fill = async () => {
      if (state !== "idle") return;
      if (histCode.has(key)) { show(histCode.get(key)); return; }
      state = "loading";
      clear(body);
      body.append(h("p", { class: "pr-hist-note" }, "Loading…"));
      try {
        const res = await get(path + "/history/" + rec.id);
        if (isDead()) return;
        histCode.set(key, typeof res.code === "string" ? res.code : "");
        show(histCode.get(key));
      } catch (e) {
        if (isDead()) return;
        state = "idle";
        clear(body);
        body.append(h("p", { class: "pr-hist-note" }, "This version could not be loaded: " + (e.detail || e.message)));
      }
    };
    det.addEventListener("toggle", () => {
      if (det.open) {
        histOpen.add(key);
        fill();
      } else {
        histOpen.delete(key);
      }
    });
    if (histOpen.has(key)) {
      det.open = true;
      fill();
    }
    return det;
  }
  drawTabs();
  drawHistory();

  let scratchTimer = null;
  let scratchDropped = false; // Redo cleared the key: nothing may write the old notes back
  const saveScratch = () => {
    clearTimeout(scratchTimer);
    scratchTimer = null;
    if (!scratchDropped) lsSet(sKey, scratch.value || null);
  };
  scratch.addEventListener("input", () => { clearTimeout(scratchTimer); scratchTimer = setTimeout(saveScratch, 300); });

  // ---- autosave ----
  // createSaver (above) does the timing; this part only shows its state.
  const codesNow = () => Object.fromEntries(tabList.map((t) => [t.id, editor.getValue(t.id)]));
  const snap = () => draftText(codesNow(), notesNow(), multi);
  const fromServer = (n) => {
    const out = {};
    for (const [key] of BOXES) out[key] = (n && n[key]) || "";
    return out;
  };
  // The problem's version number: sent with every save, run and submit, so the server can tell
  // that another tab changed the problem since this page loaded it.
  let rev = Number.isInteger(p.rev) ? p.rev : null;
  const withRev = (body) => (rev === null ? body : Object.assign({}, body, { base_rev: rev }));
  const noteRev = (res) => { if (res && Number.isInteger(res.rev)) rev = res.rev; return res; };
  const saver = createSaver({
    snap,
    saved: draftText(Object.fromEntries(initial.map((t) => [t.id, t.code])), fromServer(p.notes), multi),
    send: (text) => track(slug, put(path + "/draft", withRev(JSON.parse(text)))).then(noteRev),
    // Leaving the page: the browser limits the size of this request, so a long draft goes down
    // to the tabs that changed since the last save.
    keep: (text) => {
      const body = text.length < KEEPALIVE_MAX ? text : changedDraft(text, saver.saved);
      return track(slug, put(path + "/draft", withRev(JSON.parse(body)),
        { keepalive: body.length < KEEPALIVE_MAX })).then(noteRev);
    },
    delay: SAVE_MS,
    onStale: () => { staleNote.hidden = false; },
    onState: (st) => {
      // A failure stays on screen through the retry, until a save goes through.
      saveState.textContent = saveLabel(st);
      saveState.classList.toggle("pr-save-bad", !!st.error || !!st.warning || !!st.stale);
    },
  });
  listen(window, "prep:save-state", (e) => saver.setWarning(e.detail && e.detail.warning));
  const changed = () => { if (!dead) saver.changed(); };
  const saveNow = () => { saver.save(); };
  const flush = () => saver.flush();
  for (const ta of Object.values(noteBoxes)) ta.addEventListener("input", changed);
  listen(window, "pagehide", () => { flush(); saveScratch(); });
  listen(window, "beforeunload", () => { flush(); saveScratch(); });

  // ---- time ----
  // `sinceBeat` is the active time the 30 s heartbeat has not carried yet. Leaving the page sends
  // it (at most 30 s), and a submit sends it as `elapsed`, so a short visit is not lost.
  let sinceBeat = 0;
  const tick = setInterval(() => {
    if (!shell.isActive()) return;
    seconds += 1;
    sinceBeat += 1;
    clock.textContent = fmtClock(seconds);
  }, 1000);
  cleanups.push(() => clearInterval(tick));
  listen(window, "prep:heartbeat", (e) => {
    if (e.detail && e.detail.slug === slug) sinceBeat = 0;
  });
  // Taking the seconds also tells the shell, so its next beat does not credit them again.
  const takeElapsed = () => {
    const n = Math.min(MAX_BEAT, Math.floor(sinceBeat));
    sinceBeat = 0;
    shell.tookSeconds(n);
    return n;
  };
  // A submit that failed credited nothing: the seconds go back to both counters.
  const giveBack = (n) => {
    if (!(n >= 1)) return;
    sinceBeat += n;
    shell.tookSeconds(-n);
  };
  const sendRest = () => {
    const n = takeElapsed();
    if (n >= 1) post("/heartbeat", { slug, seconds: n }, { keepalive: true }).catch(() => {});
  };
  listen(window, "pagehide", sendRest);

  // ---- a newer copy from another tab ----
  // Put the server's copy of the problem into this page, in place: code, the four boxes, status.
  function applyFresh(fresh) {
    if (isDead()) return;
    // Another attempt, or other tabs than the ones on screen: build the page again.
    const freshTabs = tabsOf(fresh);
    if ((fresh.attempt || 1) !== (p.attempt || 1) || hasTabs(fresh) !== multi || !sameTabs(freshTabs, tabList)) {
      reload();
      return;
    }
    for (const t of freshTabs) editor.setValue(t.code, t.id);
    for (const [key] of BOXES) noteBoxes[key].value = (fresh.notes && fresh.notes[key]) || "";
    saver.reset(draftText(Object.fromEntries(freshTabs.map((t) => [t.id, t.code])), fromServer(fresh.notes), multi));
    noteRev(fresh);
    setHistory(fresh.history);
    if (fresh.status !== p.status) {
      p.status = fresh.status;
      p.submits = fresh.submits || p.submits;
      drawStatus();
      syncSolved();
    }
    staleNote.hidden = true;
    clear(out);
    out.append(h("p", { class: "pr-out-empty" }, "Run the examples to see each case here."));
  }
  staleReload.addEventListener("click", async () => {
    staleReload.disabled = true;
    try {
      const fresh = await get(path);
      if (!isDead()) applyFresh(fresh);
    } catch (e) {
      if (!isDead()) toast("The problem could not be reloaded: " + (e.detail || e.message), { kind: "error" });
    } finally {
      staleReload.disabled = false;
    }
  });
  // Coming back to the tab: if another tab changed the problem and nothing here is unsaved,
  // take the newer copy quietly. Unsaved work is never overwritten; the server's 409 guards it.
  listen(document, "visibilitychange", async () => {
    if (document.visibilityState !== "visible" || isDead() || running || saver.busy || saver.stalled) return;
    if (snap() !== saver.saved) return;
    let fresh;
    try { fresh = await get(path); } catch (e) { return; }
    if (isDead() || running || saver.busy || saver.stalled || snap() !== saver.saved) return;
    if (Number.isInteger(fresh.rev) && fresh.rev !== rev) applyFresh(fresh);
  });

  // ---- run and submit ----
  function syncButtons() {
    const on = running !== null;
    runBtn.disabled = submitBtn.disabled = resetBtn.disabled = redoBtn.disabled = on;
    for (const b of work.querySelectorAll(".pr-lock")) b.disabled = on;
  }
  async function runCode(kind) {
    if (running || dead) return;
    const tab = cur;
    if (panel !== "code") showPanel("code");
    if (isUntouchedSkeleton(editor.getValue(tab), p.skeleton)) {
      clear(out);
      out.append(h("p", { class: "notice notice-warn", role: "alert" }, "Write your solution first."));
      outLive.textContent = "Write your solution first.";
      editor.clearError();
      editor.focus();
      return;
    }
    busy(kind);
    runCtrl = new AbortController();
    const mine = runCtrl;
    clear(out);
    out.append(h("p", { class: "pr-out-wait" }, kind === "run" ? "Running the examples…" : "Running the app's tests…"));
    outLive.textContent = kind === "run" ? "Running the examples." : "Running the app's tests.";
    // The autosave goes first and then stays quiet until the answer is back. A save sent during
    // the run would carry the version number the run has just replaced, and the server would
    // take it for a change made in another tab.
    await saveAll();
    await saver.hold();
    let body = {};
    let res = null;
    let failure = null;
    try {
      if (!isDead() && !mine.signal.aborted && !saver.stalled) {
        const code = editor.getValue(tab);
        const at = multi ? { code, tab } : { code };
        body = withRev(kind === "run" ? at : Object.assign(at, { notes: notesNow(), elapsed: takeElapsed() }));
        res = await post(path + (kind === "run" ? "/run" : "/submit"), body, { signal: mine.signal });
        noteRev(res);
      }
    } catch (e) {
      failure = e;
    } finally {
      saver.release();
    }
    if (runCtrl === mine) runCtrl = null;
    if (isDead() || mine.signal.aborted) return;
    free();
    clear(out);
    if (!res && !failure) {
      out.append(h("p", { class: "notice notice-warn", role: "alert" },
        "Not run: this problem changed in another tab. Reload first."));
      outLive.textContent = "";
      return;
    }
    if (failure) {
      giveBack(body.elapsed);
      editor.clearError();
      if (failure instanceof ApiError && failure.status === 409 && failure.code === "stale") saver.stall(failure);
      const text = failure instanceof ApiError && failure.status === 413
        ? "The code is over 200,000 characters, so it was not run."
        : (failure.detail || failure.message || "The run failed.");
      out.append(h("p", { class: "notice notice-warn", role: "alert" }, text));
      outLive.textContent = "";
      return;
    }
    saver.setWarning(res.save_error);
    drawResult(res, kind, tab);
    if (kind === "submit") afterSubmit(res);
  }

  function drawResult(res, kind, tab) {
    const several = tabList.length > 1;
    const sum = resultSummary(res, kind);
    const solved = kind === "submit" && res.solved;
    reviewFlag = kind === "submit" ? h("span", { class: "pr-sum-note" },
      setup && setup.claude === false ? "The final review needs a coach; see the coach pane."
        : "The final review is in the coach pane.") : null;
    out.append(h("div", { class: "pr-sum pr-sum-" + sum.tone + (solved ? " pr-solved" : "") },
      h("span", { class: "pr-sum-icon", "aria-hidden": "true" }, sum.tone === "good" ? "✓" : "✗"),
      h("strong", null, sum.text),
      several ? h("span", { class: "pr-sum-note pr-sum-tab" }, nameOf(tab)) : null,
      solved && res.first_try ? h("span", { class: "pr-sum-note" }, "First try.") : null,
      reviewFlag));
    outLive.textContent = sum.text + ".";
    let markLine = null;
    if (res.fatal) {
      out.append(h("div", { class: "pr-fatal", role: "alert" },
        h("strong", null, errorText(res.fatal)),
        res.fatal.type === "SyntaxError" ? h("p", null, "Nothing ran. Fix the line and run again.") : null));
      markLine = lineOf(res.fatal);
    }
    const rows = h("ul", { class: "pr-cases" });
    let opened = false;
    for (const r of res.results || []) {
      const row = caseRow(r);
      const head = [h("span", { class: "pr-case-icon", "aria-hidden": "true" }, row.icon),
        h("span", { class: "pr-case-name" }, row.name),
        h("span", { class: "pr-case-note" }, row.note)];
      const sr = h("span", { class: "sr-only" }, row.tone === "pass" ? "passes: " : row.tone === "skip" ? "" : "fails: ");
      if (row.open) {
        const det = h("details", { class: "pr-case-box" },
          h("summary", { class: "pr-case pr-case-" + row.tone }, sr, ...head),
          h("dl", { class: "pr-fields" }, caseFields(r).map(([k, v]) => [h("dt", null, k),
            h("dd", null, h("pre", null, String(v)))])));
        // Only the first failing case starts open; a full submit can fail many at once.
        if (!opened) { det.open = true; opened = true; }
        rows.append(h("li", null, det));
      } else {
        rows.append(h("li", { class: "pr-case pr-case-" + row.tone }, sr, ...head));
      }
      if (markLine === null && r.status === "error") markLine = lineOf(r.error);
    }
    if ((res.results || []).length) out.append(rows);
    if (markLine !== null && editor.markError(markLine, tab)) {
      out.append(h("p", { class: "pr-sub" }, "Line " + markLine + " is marked in "
        + (several ? nameOf(tab) : "the editor") + "."));
    } else {
      editor.clearError();
    }
    out.scrollTop = 0;
  }

  function afterSubmit(res) {
    p.submits = (p.submits || []).concat([{ id: res.submit_id, attempt: p.attempt || 1, ok: !!res.solved }]);
    if (res.solved) p.status = "solved";
    else if (p.status === "new") p.status = "attempted";
    syncSolved();
    setHistory(res.history);
    drawStatus();
    shell.refreshNav();
    setCoach(true);
    coach.review(res.submit_id);
  }

  runBtn.addEventListener("click", () => runCode("run"));
  submitBtn.addEventListener("click", () => runCode("submit"));

  // In a tab that is behind another tab, Reset and Redo would act on the other tab's code and
  // drop what is typed here, so they wait for the Reload.
  const behind = () => {
    if (!saver.stalled) return false;
    toast("This problem changed in another tab. Reload first.", { kind: "error" });
    return true;
  };

  resetBtn.addEventListener("click", async () => {
    if (running || behind()) return;
    const tab = cur;
    const kept = !isUntouchedSkeleton(editor.getValue(tab), p.skeleton);
    const ok = await confirmDialog("Replace " + (tabList.length > 1 ? "the code in " + nameOf(tab) : "your code")
      + " with the starting skeleton? The four boxes keep their text."
      + (!kept ? "" : multi ? " Your current code is kept in the history."
        : " Your current code is kept as " + slug + ".prev.py."),
    { confirm: "Reset the code", focus: "cancel" });
    if (!ok || isDead() || running || !tabList.some((t) => t.id === tab)) return;
    busy("reset");
    await saveAll(); // the last keystrokes reach the server before it moves the code aside
    // No autosave may land during the POST and write the old code over the skeleton.
    await saver.hold();
    if (isDead()) { saver.release(); return; }
    try {
      if (saver.stalled) return;
      const res = await post(path + "/reset", multi ? { tab } : {});
      noteRev(res);
      if (isDead()) return;
      saver.setWarning(res.save_error);
      editor.setValue(res.code, tab);
      saver.saved = patchDraft(saver.saved, tab, res.code);
      setHistory(res.history);
      if (tab === cur && panel !== "code") showPanel("code");
      clear(out);
      out.append(h("p", { class: "pr-out-empty" }, "The code is back to the skeleton."));
    } catch (e) {
      if (!isDead()) toast("The code could not be reset: " + (e.detail || e.message), { kind: "error" });
    } finally {
      saver.release(); // after a page change this sends text typed during the hold, once
      if (!isDead()) free();
    }
  });

  // Start a solved problem again. The server moves every tab's code to the history first.
  async function redo() {
    if (running || behind()) return;
    const ok = await confirmDialog(redoQuestion("this problem"), { confirm: "Start again", focus: "cancel" });
    if (!ok || isDead() || running) return;
    busy("redo");
    await saveAll(); // the last keystrokes are part of what the history keeps
    await saver.hold();
    if (isDead()) { saver.release(); return; }
    if (saver.stalled) { saver.release(); free(); return; }
    try {
      await post(path + "/redo", {});
      if (isDead()) return;
      scratchDropped = true;
      lsSet(sKey, null);
      lsSet(TAB_KEY, null);
      await reload();
    } catch (e) {
      if (isDead()) return;
      saver.release();
      free();
      toast("The problem could not be restarted: " + (e.detail || e.message), { kind: "error" });
    }
  }
  redoBtn.addEventListener("click", redo);
  redoBtn2.addEventListener("click", redo);

  // Cmd/Ctrl-S anywhere on the page saves; Cmd/Ctrl-Enter outside the coach runs the examples.
  // The editor handles both itself and marks the event as handled.
  listen(window, "keydown", (e) => {
    if (e.defaultPrevented || !(mac ? e.metaKey : e.ctrlKey) || e.altKey) return;
    if (e.key === "s" || e.key === "S") {
      e.preventDefault();
      saveNow();
    } else if (e.key === "Enter" && !coach.el.contains(e.target)) {
      e.preventDefault();
      runCode("run");
    }
  });

  return {
    destroy({ save: keep = true } = {}) {
      if (keep) flush();
      saveScratch();
      sendRest();
      dead = true;
      if (idleDone) idleDone();
      saver.destroy();
      if (runCtrl) runCtrl.abort();
      coach.destroy();
      for (const c of cleanups) c();
      editor.destroy();
    },
  };
}

function statementBlock(p) {
  const link = h("a", { class: "pr-out-link", href: p.url, target: "_blank", rel: "noopener noreferrer" },
    "Open on LeetCode ↗");
  const st = p.statement;
  if (st && st.body) {
    let body;
    if (st.format === "html") {
      body = h("div", { class: "md pr-stmt" }, sanitizeHtml(st.body));
    } else {
      body = renderMarkdown(cleanNeetcode(st.body));
      body.classList.add("pr-stmt");
    }
    // The statement carries its own examples; the app's list would only repeat them.
    const shown = layoutStatement(body);
    return h("div", { class: "pr-statement" }, body, shown ? null : examplesBlock(p),
      h("p", { class: "pr-linkline" }, link));
  }
  return h("div", { class: "pr-statement" },
    h("div", { class: "notice pr-nostmt" },
      h("p", null, "The statement is not downloaded yet. Read it on LeetCode; the examples below are the ones Run checks."),
      h("p", null, link),
      h("p", { class: "pr-sub" }, "To see statements here, use “Download” under Get started on ",
        h("a", { href: "#/" }, "Home"), ".")),
    examplesBlock(p));
}

function examplesBlock(p) {
  const ex = p.examples || [];
  return h("div", { class: "pr-examples" },
    h("p", { class: "pr-sub" }, "These are what “Run examples” checks."),
    ex.length ? h("div", { class: "stmt-examples" }, ex.map((e) => h("section", { class: "stmt-ex" },
      h("div", { class: "stmt-label" }, e.name || "Example"),
      h("div", { class: "stmt-ex-body" },
        h("pre", null, h("strong", null, "Input:"), " " + e.input + "\n", h("strong", null, "Output:"), " " + e.expected)))))
      : h("p", { class: "pr-sub" }, "This problem has no examples in the app."));
}
