// The coach pane of the practice workspace: chips, a question box, streamed replies rendered as
// sanitised Markdown, Stop, the saved history and the final review blocks. The pure helpers at
// the top never touch the DOM, so node can import this file for the unit tests.
import { ApiError, stream, post, get } from "./api.js";
import { h, clear, inlineCode } from "./ui.js";
import { renderMarkdown } from "./md.js";
import { isCoachPayload, coachStatus, unavailableText } from "./coachpick.js";

// ---- pure helpers ---------------------------------------------------------------

/** The four asks of spec §7.3, in order. */
export const CHIPS = [
  { kind: "hint", label: "Give me a hint" },
  { kind: "review", label: "Review my solution" },
  { kind: "approach", label: "Is my approach right?" },
  { kind: "complexity", label: "Check my complexity" },
];

/** One line icon per ask, as SVG shapes on a 24 by 24 grid: [tag, attributes]. */
export const ASK_ICONS = {
  // a light bulb
  hint: [["path", { d: "M12 3a6 6 0 0 0-3.6 10.8c.7.5 1.1 1.3 1.1 2.2h5c0-.9.4-1.7 1.1-2.2A6 6 0 0 0 12 3z" }],
    ["path", { d: "M9.5 19h5" }], ["path", { d: "M10.5 21.5h3" }]],
  // a clipboard with a tick
  review: [["rect", { x: "5", y: "4.5", width: "14", height: "16.5", rx: "2" }],
    ["path", { d: "M9 4.5V3h6v1.5" }], ["path", { d: "m9 13 2.2 2.2L15.2 11" }]],
  // a compass
  approach: [["circle", { cx: "12", cy: "12", r: "9" }], ["path", { d: "m15.6 8.4-2.1 5.1-5.1 2.1 2.1-5.1z" }]],
  // a growth curve on two axes
  complexity: [["path", { d: "M4 4v16h16" }], ["path", { d: "M7.5 16.5c5 0 8.5-3.5 9.5-10" }]],
};

/** The small "who" line above a user turn. */
export function userLabel(kind) {
  const chip = CHIPS.find((c) => c.kind === kind);
  return chip ? "You · pressed “" + chip.label + "”" : "You";
}

const SVG_NS = "http://www.w3.org/2000/svg";

/** The icon of one ask button. Decoration only: the label next to it says the same thing. */
function askIcon(kind) {
  const svg = document.createElementNS(SVG_NS, "svg");
  const set = (node, attrs) => { for (const k of Object.keys(attrs)) node.setAttribute(k, attrs[k]); };
  set(svg, { class: "ask-icon", viewBox: "0 0 24 24", width: "18", height: "18", fill: "none",
    stroke: "currentColor", "stroke-width": "1.7", "stroke-linecap": "round", "stroke-linejoin": "round",
    "aria-hidden": "true", focusable: "false" });
  for (const [tag, attrs] of ASK_ICONS[kind] || []) {
    const shape = document.createElementNS(SVG_NS, tag);
    set(shape, attrs);
    svg.appendChild(shape);
  }
  return svg;
}

const realClock = {
  now: () => Date.now(),
  schedule: (fn, ms) => setTimeout(fn, ms),
  cancel: (t) => clearTimeout(t),
};

/**
 * Rate-limit fn: the first call runs at once, later calls inside `ms` collapse into one call at
 * the end of the interval. Returns {call, flush, cancel}.
 */
export function throttle(fn, ms, clock = realClock) {
  let last = -Infinity;
  let timer = null;
  const fire = () => { timer = null; last = clock.now(); fn(); };
  return {
    call() {
      if (timer !== null) return;
      const wait = last + ms - clock.now();
      if (wait <= 0) fire();
      else timer = clock.schedule(fire, wait);
    },
    flush() {
      if (timer === null) return;
      clock.cancel(timer);
      fire();
    },
    cancel() {
      if (timer === null) return;
      clock.cancel(timer);
      timer = null;
    },
  };
}

const list = (v) => (Array.isArray(v) ? v.filter((x) => typeof x === "string" && x.trim()) : []);

/** The final review as the five blocks of spec §7.3. */
export function reviewBlocks(review) {
  const r = review && typeof review === "object" ? review : {};
  const pass = r.verdict === "pass";
  return [
    { title: "Verdict", text: pass ? "Ready to move on" : "Needs more work", tone: pass ? "good" : "warn" },
    { title: "What's good", items: list(r.good), empty: "Nothing noted." },
    { title: "What's wrong", items: list(r.wrong), empty: "Nothing found." },
    { title: "Edge cases you didn't mention", items: list(r.edge_cases), empty: "None missing." },
    { title: "Next step", text: typeof r.next_step === "string" ? r.next_step : "" },
  ];
}

const plural = (n, one, many) => n + " " + (n === 1 ? one : many);

/** The line under a review saying what went to learnings.md and bugs.md. */
/**
 * What a poll of the problem says about one submit's review: {action: "wait"} while the server
 * writes it, {action: "done", review, record} once it is stored, {action: "offer"} when nobody is
 * writing it any more (show the button again).
 */
export function reviewPoll(submits, id) {
  const rec = (submits || []).find((s) => s && s.id === id);
  if (rec && rec.reviewed && rec.review) return { action: "done", review: rec.review, record: rec };
  if (rec && rec.review_in_progress) return { action: "wait" };
  return { action: "offer" };
}

export function savedLine(saved, review) {
  // Restored from history: the counts were not kept, so say only that the save happened then.
  if (!saved) return "Notes from this review were saved when it was written.";
  const parts = [];
  if (saved.learnings > 0) parts.push(plural(saved.learnings, "entry", "entries") + " in learnings.md");
  if (saved.bugs > 0) parts.push(plural(saved.bugs, "row", "rows") + " in bugs.md");
  if (parts.length) return "Saved to your notes: " + parts.join(" and ") + ".";
  if (saved.skipped && saved.skipped.length) return "Nothing could be saved to your notes.";
  return "No mistakes to save to your notes this time.";
}

const REST_WORKS = "Everything else on this page works without it.";
const NOT_FOUND = "The coach is not available on this computer. " + REST_WORKS;

/**
 * The lines of the "no coach" note for a setup answer (/api/setup/status):
 * {text, choose, install}. `choose`: the welcome page can connect a tool; `install`: an older
 * server, where the coach is Claude Code and nothing else.
 */
export function setupLines(setup) {
  const why = unavailableText(coachStatus(setup)) || "The coach is not available on this computer.";
  const choose = isCoachPayload(setup && setup.coach);
  return { text: why + " " + REST_WORKS, choose, install: !choose };
}
const noDot = (s) => String(s || "").trim().replace(/[.\s]+$/, "");

/** How long after the user's own Stop a `busy` answer is taken to be that stopped answer. */
export const STOP_GRACE_MS = 10000;
/** The wait before asking again when that happens (the server frees the slot about 0.2 s after). */
const STOP_RETRY_MS = 1500;
const REVIEW_POLL_MS = 3000;

/** Is `err` the server still finishing the answer the user stopped at `stoppedAt`? */
export function busyFromStop(err, stoppedAt, now) {
  return err instanceof ApiError && err.code === "busy" && stoppedAt !== null
    && now - stoppedAt >= 0 && now - stoppedAt < STOP_GRACE_MS;
}

/**
 * A coach failure -> {text, setup, retry}: what to show and whether trying again can help.
 * `afterStop`: the user stopped an answer a moment ago and the retry was busy too.
 */
export function coachError(err, { afterStop = false } = {}) {
  if (!(err instanceof ApiError)) {
    return { text: (err && err.message) || "Something went wrong.", setup: false, retry: true };
  }
  switch (err.code) {
    case "claude_not_found":
      return { text: NOT_FOUND, setup: true, retry: false };
    case "busy":
      if (afterStop) return { text: "Still stopping the last answer. Try again in a moment.", setup: false, retry: true };
      return { text: "The coach is busy with another answer, maybe in another tab. Try again when it is done.",
        setup: false, retry: true };
    case "failed":
      return { text: "The coach failed: " + noDot(err.detail) + ". Try again in a moment.", setup: false, retry: true };
    case "timeout":
      return { text: "The coach took too long to answer and was stopped. Try again.", setup: false, retry: true };
    case "offline":
      return { text: err.detail, setup: false, retry: true };
    case "stream":
      return { text: err.detail || "The coach's answer was cut off.", setup: false, retry: true };
    case "internal":
      return { text: "Something went wrong in the app: " + noDot(err.detail) + ".", setup: false, retry: true };
    default:
      if (err.status >= 400 && err.status < 500) return { text: err.detail, setup: false, retry: false };
      return { text: err.detail || "The coach failed.", setup: false, retry: true };
  }
}

// ---- the pane -------------------------------------------------------------------------

const PAINT_MS = 120;

/** Milliseconds waited -> "0:07", "2:15": the clock on the final review's wait card. */
export function waitClock(ms) {
  let n = Math.floor(Number(ms) / 1000);
  if (!Number.isFinite(n) || n < 0) n = 0;
  return Math.floor(n / 60) + ":" + String(n % 60).padStart(2, "0");
}

/**
 * Build the coach pane. Options:
 *   slug, isStale()          the problem and the page's staleness check
 *   context() -> {code, notes, tab?}  what the coach reads with every ask; may be a promise
 *   claude                    false when /api/setup/status said the coach's tool is missing
 *   setup                     that /api/setup/status answer, to say which tool and why
 *   history                  items from historyItems() (chat turns and reviews, by time)
 *   pendingSubmit             a submit id of this attempt still waiting for its final review
 *   reviewing                 true when the server is writing that review right now (another tab)
 *   onOpen()                  show the pane (a final review opens it)
 *   onReview(state)           the final review moved on: "queued" | "writing" | "done" | "failed" | "again"
 * Returns {el, review(submitId), focusInput(), destroy()}.
 */
export function createCoach({ slug, isStale, context, claude = true, setup = null, history = [],
  pendingSubmit = null, reviewing = false, onOpen, onReview }) {
  let info = setup || { claude };
  const path = "/problem/" + encodeURIComponent(slug);
  let busy = null; // null | "chat" | "review"
  let ctrl = null;
  let stoppedAt = null; // when the user last pressed Stop (E3)
  let reviewCtrl = null;
  let queuedReview = null;
  let missing = claude === false;
  let paint = null;
  const stale = () => (isStale ? isStale() : false);

  const log = h("div", { class: "pr-log", role: "log", "aria-live": "off", tabindex: "0",
    "aria-label": "Conversation with the coach" });
  const live = h("div", { class: "sr-only", role: "status", "aria-live": "polite" });
  const empty = h("p", { class: "pr-coach-empty" },
    "Empty until you ask. The coach reads your code and the four boxes, and answers only the question you pick.");
  const setupNote = h("div", { class: "notice notice-warn pr-setup", hidden: !missing });
  const chips = CHIPS.map((c) => h("button", { class: "ask-btn", type: "button", dataset: { kind: c.kind },
    onclick: () => ask(c.kind, "") }, askIcon(c.kind), h("span", { class: "ask-label" }, c.label)));
  const input = h("textarea", { class: "pr-ask-input", rows: "2", placeholder: "Ask the coach…",
    "aria-label": "Question for the coach", maxlength: "200000" });
  const send = h("button", { class: "btn btn-primary btn-sm", type: "submit" }, "Send");
  const stop = h("button", { class: "btn btn-sm pr-stop", type: "button", hidden: true, onclick: () => stopAsk() }, "Stop");
  const form = h("form", { class: "pr-ask" }, input, h("div", { class: "pr-ask-btns" }, send, stop));
  form.addEventListener("submit", (e) => { e.preventDefault(); sendQuestion(); });
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey && !e.isComposing && !e.metaKey && !e.ctrlKey) {
      e.preventDefault();
      sendQuestion();
    }
  });

  const el = h("aside", { class: "pr-coach", id: "pr-coach", "aria-label": "Coach" },
    h("h2", { class: "pr-coach-title" }, "Coach · answers only when you ask"),
    log, setupNote,
    h("div", { class: "pr-chips", role: "group", "aria-label": "Ask the coach" }, chips),
    form, live);

  const drawSetup = () => {
    clear(setupNote);
    setupNote.hidden = !missing;
    if (!missing) return;
    const again = h("button", { class: "btn btn-sm", type: "button" }, "Check again");
    again.addEventListener("click", async () => {
      again.disabled = true;
      try {
        const s = await get("/setup/status");
        if (stale()) return;
        missing = s && s.claude === false;
        if (s) info = s;
      } catch (e) { /* keep the note */ }
      if (stale()) return;
      again.disabled = false;
      drawSetup();
      syncControls();
      live.textContent = missing ? "The coach is still not available." : "The coach is ready.";
    });
    const lines = setupLines(info);
    setupNote.append(h("p", null, lines.text));
    if (lines.install) {
      setupNote.append(h("p", null, "Install Claude Code and sign in, then press Check again. "
        + "The README's “What you need” section has the link."));
    }
    setupNote.append(
      h("div", { class: "pr-setup-btns" },
        lines.choose ? h("a", { class: "btn btn-sm btn-primary", href: "#/welcome?back="
          + encodeURIComponent("/practice/" + slug) }, "Choose a coach") : null,
        again));
  };

  const syncControls = () => {
    const off = busy !== null || missing;
    for (const c of chips) c.disabled = off;
    send.disabled = off;
    stop.hidden = busy !== "chat";
  };

  const atBottom = () => log.scrollHeight - log.scrollTop - log.clientHeight < 40;
  const toBottom = () => { log.scrollTop = log.scrollHeight; };
  // A new turn always scrolls into view; streamed text only follows when the reader is at the end.
  const add = (node) => {
    empty.remove();
    log.append(node);
    toBottom();
    return node;
  };

  const userTurn = (kind, text) => h("div", { class: "pr-msg pr-msg-user" },
    h("div", { class: "pr-who" }, userLabel(kind)), h("div", { class: "pr-msg-text" }, text));
  const coachBody = (text) => {
    // No images from the coach: a Markdown or raw <img> would be fetched from anywhere it names.
    const body = renderMarkdown(text || "", { images: false });
    body.classList.add("pr-md");
    return body;
  };
  const coachTurn = (text) => h("div", { class: "pr-msg pr-msg-coach" },
    h("div", { class: "pr-who" }, "Coach"), coachBody(text));

  const reviewNode = (review, saved, record) => {
    const node = h("div", { class: "pr-msg pr-msg-coach pr-review" },
      h("div", { class: "pr-who" }, "Coach · final review"
        + (record && record.total ? ", " + record.passed + " of " + record.total + " of the app's tests passed" : "")));
    for (const b of reviewBlocks(review)) {
      const blk = h("div", { class: "pr-blk" }, h("b", null, b.title));
      if (b.items) {
        blk.append(b.items.length ? h("ul", null, b.items.map((t) => h("li", null, inlineCode(t))))
          : h("p", { class: "pr-blk-none" }, b.empty));
      } else if (b.tone) {
        blk.append(h("span", { class: "pr-verdict pr-verdict-" + b.tone }, b.text));
      } else {
        blk.append(h("p", null, b.text ? inlineCode(b.text) : "No next step given."));
      }
      node.append(blk);
    }
    node.append(h("p", { class: "pr-saved" }, savedLine(saved, review)));
    if (saved && saved.skipped && saved.skipped.length) {
      node.append(h("ul", { class: "pr-skipped notice notice-warn" }, saved.skipped.map((s) => h("li", null, s))));
    }
    return node;
  };

  // ---- history ----
  if (history.length) {
    for (const item of history) {
      if (item.type === "review") log.append(reviewNode(item.review, null, item));
      else if (item.role === "user") log.append(userTurn(item.kind, item.text));
      else log.append(coachTurn(item.text));
    }
  } else {
    log.append(empty);
  }
  drawSetup();
  syncControls();
  requestAnimationFrame(toBottom);

  // ---- asking ----
  const errorNote = (err, where, opts) => {
    const info = coachError(err, opts);
    if (info.setup) {
      missing = true;
      drawSetup();
    }
    // The setup note above the log already says the tool is missing; say it once.
    if (info.setup) return info;
    where.append(h("p", { class: "notice pr-error", role: "alert" }, info.text));
    return info;
  };

  async function ask(kind, message, raw) {
    if (busy || missing || stale()) return;
    const hadFocus = el.contains(document.activeElement) && document.activeElement !== input;
    busy = "chat";
    ctrl = new AbortController();
    const mine = ctrl;
    syncControls();
    if (hadFocus) stop.focus();
    live.textContent = "The coach is answering.";

    const label = (CHIPS.find((c) => c.kind === kind) || {}).label;
    const turn = h("div", { class: "pr-pair" }, userTurn(kind, message || label));
    const reply = h("div", { class: "pr-msg pr-msg-coach pr-streaming" }, h("div", { class: "pr-who" }, "Coach"));
    let body = h("div", { class: "pr-wait" }, "Thinking…");
    reply.append(body);
    turn.append(reply);
    add(turn);

    let text = "";
    let outcome = null;
    paint = throttle(() => {
      if (stale()) return;
      const stick = atBottom();
      const next = coachBody(text);
      body.replaceWith(next);
      body = next;
      if (stick) toBottom();
    }, PAINT_MS);
    // The page may first finish a run or a save, so the coach reads the code as it is stored.
    let ctx = null;
    try { ctx = await context(); } catch (e) { outcome = e; }
    const ask = ctx ? { kind, message, code: ctx.code, notes: ctx.notes } : null;
    if (ask && ctx.tab !== undefined) ask.tab = ctx.tab;
    const send = () => (!ask || mine.signal.aborted || stale() ? Promise.resolve() : stream(path + "/coach", ask, {
      signal: mine.signal,
      onDelta: (d) => { if (!mine.signal.aborted) { text += d; paint.call(); } },
      onDone: (full) => { outcome = "done"; if (full) text = full; },
      onError: (err) => { outcome = err; },
    }));
    await send();
    // Asked again right after a Stop: the server may still be ending the stopped answer. Wait a
    // moment and ask once more, without showing the busy message in between.
    let afterStop = false;
    if (!mine.signal.aborted && !stale() && busyFromStop(outcome, stoppedAt, Date.now())) {
      afterStop = true;
      await new Promise((resolve) => {
        const t = setTimeout(resolve, STOP_RETRY_MS);
        mine.signal.addEventListener("abort", () => { clearTimeout(t); resolve(); }, { once: true });
      });
      if (!mine.signal.aborted && !stale()) {
        text = "";
        outcome = null;
        await send();
      }
    }
    paint.cancel();
    paint = null;
    if (ctrl === mine) ctrl = null;
    if (stale()) return;
    reply.classList.remove("pr-streaming");
    let focusReply = false;
    if (outcome === "done") {
      const next = coachBody(text);
      body.replaceWith(next);
      if (raw !== undefined && input.value === raw) input.value = "";
      // Focus goes to the answer only from inside the coach pane, and never out of a question box
      // that holds new typing; the editor and the rest of the page keep their focus.
      reply.tabIndex = -1;
      const at = document.activeElement;
      focusReply = el.contains(at) && !(at === input && input.value.trim());
      live.textContent = "The coach answered.";
    } else {
      // Nothing was stored: the turn stays on screen marked as not kept, the question stays in the box.
      if (text) {
        const next = coachBody(text);
        body.replaceWith(next);
      } else {
        body.remove();
      }
      turn.classList.add("pr-pair-lost");
      if (mine.signal.aborted) {
        reply.append(h("p", { class: "pr-lost" }, "Stopped. This answer is not kept."));
        live.textContent = "Stopped.";
      } else {
        const info = errorNote(outcome, reply, { afterStop });
        reply.append(h("p", { class: "pr-lost" }, "Not kept." + (raw ? " Your question is still in the box." : "")));
        live.textContent = info.text;
      }
    }
    toBottom();
    busy = null;
    syncControls();
    if (focusReply) reply.focus();
    else if (document.activeElement === stop || document.activeElement === document.body) input.focus();
    if (queuedReview) {
      const id = queuedReview;
      queuedReview = null;
      review(id);
    }
  }

  function sendQuestion() {
    const raw = input.value;
    const message = raw.trim();
    if (!message) { input.focus(); return; }
    ask("question", message, raw);
  }

  function stopAsk() {
    if (!ctrl) return;
    stoppedAt = Date.now();
    ctrl.abort();
  }

  // ---- the final review ----
  const waitTimers = new Set();
  const tell = (state) => { if (onReview) onReview(state); };

  // The card shown while a review is being written: it has to be seen, so that nobody leaves
  // the page thinking nothing is happening. The clock shows that the wait is alive.
  function waitCard(title, ...lines) {
    const clock = h("span", { class: "pr-rw-clock", "aria-hidden": "true" }, "0:00");
    const card = h("div", { class: "pr-review-wait" },
      h("div", { class: "pr-rw-head" },
        h("span", { class: "pr-spin", "aria-hidden": "true" }),
        h("strong", { class: "pr-rw-title" }, title),
        clock),
      lines.map((line) => h("p", { class: "pr-rw-text" }, line)));
    const started = Date.now();
    const timer = setInterval(() => {
      if (!card.isConnected) { clearInterval(timer); waitTimers.delete(timer); return; }
      clock.textContent = waitClock(Date.now() - started);
    }, 1000);
    waitTimers.add(timer);
    return card;
  }

  async function review(submitId) {
    if (stale() || !submitId) return;
    if (onOpen) onOpen();
    if (busy === "chat") {
      // One coach at a time: the review starts when the current answer ends.
      queuedReview = submitId;
      if (!log.querySelector(".pr-review-queued")) {
        add(h("p", { class: "pr-coach-note pr-review-queued" }, "The final review starts when this answer is done."));
      }
      tell("queued");
      return;
    }
    if (busy === "review" || awaited) {
      // One review at a time: this submit's code is not reviewed now.
      if (!log.querySelector(".pr-review-again")) {
        add(h("p", { class: "pr-coach-note pr-review-again", role: "status" },
          "A final review is already being written. Submit again when it is done to review the new code."));
      }
      tell("again");
      return;
    }
    for (const n of log.querySelectorAll(".pr-review-queued, .pr-review-offer, .pr-review-again")) n.remove();
    busy = "review";
    syncControls();
    reviewCtrl = new AbortController();
    const mine = reviewCtrl;
    const wait = add(waitCard("Your final review is being written",
      h("span", null, "It can take up to three minutes. ", h("b", null, "Stay on this page"),
        " and it will show right here."),
      "You can keep reading and editing while you wait. If you leave, it is still saved: you will find it here the next time you open this problem."));
    live.textContent = "Your final review is being written. It can take up to three minutes. Stay on this page to read it.";
    tell("writing");
    let res = null;
    let failure = null;
    try {
      res = await post(path + "/review", { submit_id: submitId }, { signal: mine.signal });
    } catch (e) {
      if (e && e.name === "AbortError") return;
      failure = e;
    }
    if (reviewCtrl === mine) reviewCtrl = null;
    if (stale()) return;
    busy = null;
    syncControls();
    if (res) {
      wait.replaceWith(reviewNode(res.review, res.saved, null));
      live.textContent = "The final review is written.";
      tell("done");
      toBottom();
      return;
    }
    const box = h("div", { class: "pr-msg pr-msg-coach" }, h("div", { class: "pr-who" }, "Coach · final review"));
    wait.replaceWith(box);
    tell("failed");
    if (failure instanceof ApiError && failure.code === "already_reviewed") {
      box.append(h("p", { class: "pr-coach-note" }, "This submit's final review is already written, or is being written now. Reload the page in a minute to see it."));
      return;
    }
    const info = errorNote(failure, box);
    if (info.setup) box.append(h("p", { class: "pr-coach-note" }, "No final review was written."));
    live.textContent = info.text;
    if (info.retry) {
      box.append(h("button", { class: "btn btn-sm", type: "button", onclick: () => { box.remove(); review(submitId); } },
        "Try the final review again"));
    }
    toBottom();
  }

  let pollTimer = null;
  let awaited = false; // a review started before this page opened is still being written
  const offerNode = (id) => h("div", { class: "pr-coach-note pr-review-offer" },
    h("p", null, "Your last submit has no final review yet."),
    h("button", { class: "btn btn-sm", type: "button", onclick: () => review(id) }, "Write the final review"));

  // The server is already writing this review (started in another tab or before a reload): say
  // so, and look again every few seconds instead of offering a button that would only fail.
  function waitForReview(id) {
    const note = add(waitCard("Your final review is being written",
      "It was started before this page opened and can take up to three minutes. It shows right here when it is done."));
    live.textContent = "Your final review is being written. It shows here when it is done.";
    awaited = true;
    tell("writing");
    const look = async () => {
      pollTimer = null;
      let p = null;
      try { p = await get(path); } catch (e) { /* try again below */ }
      if (stale()) return;
      const next = p ? reviewPoll(p.submits, id) : { action: "wait" };
      if (next.action === "wait") { pollTimer = setTimeout(look, REVIEW_POLL_MS); return; }
      awaited = false;
      if (next.action === "done") {
        note.replaceWith(reviewNode(next.review, null, next.record));
        live.textContent = "The final review is written.";
        tell("done");
        toBottom();
      } else {
        note.replaceWith(offerNode(id));
        tell(null);
      }
    };
    pollTimer = setTimeout(look, REVIEW_POLL_MS);
  }

  if (pendingSubmit) {
    if (reviewing) waitForReview(pendingSubmit);
    else add(offerNode(pendingSubmit));
  }

  return {
    el,
    review,
    focusInput: () => input.focus(),
    destroy() {
      if (paint) paint.cancel();
      if (ctrl) ctrl.abort();
      if (reviewCtrl) reviewCtrl.abort();
      if (pollTimer) clearTimeout(pollTimer);
      for (const t of waitTimers) clearInterval(t);
      waitTimers.clear();
      queuedReview = null;
    },
  };
}
