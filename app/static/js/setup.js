// The setup steps, all in the app: #/setup/plan (the discovery chat that writes the profile and
// the plan), #/setup/selfcheck (module 00's self-check, marked by the coach) and
// #/setup/diagnostic (the timed problems, run on the app's tests and scored by the coach).
// The coach only answers; the server writes every file under my-prep/.

import { get, post, put, stream } from "./api.js";
import { h, clear, toast, confirmDialog, sanitizeHtml } from "./ui.js";
import { renderMarkdown } from "./md.js";
import { createEditor } from "./editor.js";
import { coachError } from "./coach.js";
import { cleanNeetcode } from "./practice.js";
import { layoutStatement } from "./statement.js";

// ---- pure helpers (tested) ------------------------------------------------------------

const pad2 = (n) => String(n).padStart(2, "0");

/** 125 -> "2:05"; 3725 -> "1:02:05". */
export function fmtClock(seconds) {
  const s = Math.max(0, Math.floor(seconds));
  const hh = Math.floor(s / 3600);
  const mm = Math.floor((s % 3600) / 60);
  return (hh ? hh + ":" + pad2(mm) : String(mm)) + ":" + pad2(s % 60);
}

/** The clock for a problem with `minutes` allowed after `used` seconds: {text, over}. */
export function clockText(minutes, used) {
  const left = minutes * 60 - used;
  return left >= 0 ? { text: fmtClock(left) + " left", over: false }
    : { text: fmtClock(-left) + " over", over: true };
}

/** The index of the problem to open: the first unfinished one after `from`, else the first unfinished. */
export function nextOpen(problems, from = -1) {
  for (let i = from + 1; i < problems.length; i++) if (!problems[i].finished) return i;
  for (let i = 0; i < problems.length; i++) if (!problems[i].finished) return i;
  return -1;
}

/** "6/8, missed questions 3 and 7" from {score, total, missed}. */
export function scoreLine(summary) {
  if (!summary) return "";
  const missed = summary.missed || [];
  const tail = !missed.length ? ", nothing missed"
    : missed.length === 1 ? ", missed question " + missed[0]
      : ", missed questions " + missed.slice(0, -1).join(", ") + " and " + missed[missed.length - 1];
  return summary.score + "/" + summary.total + tail;
}

/** The review's dated blocks, {"01": {start, end, hours}}, as rows sorted by module. */
export function blockRows(blocks) {
  if (Array.isArray(blocks)) return blocks;
  return Object.entries(blocks || {}).sort(([a], [b]) => a.localeCompare(b))
    .map(([module, b]) => ({ module, ...(b || {}) }));
}

/** The plan chat's turns as {role, text}; drops anything malformed. */
export function chatTurns(messages) {
  return (Array.isArray(messages) ? messages : [])
    .filter((m) => m && (m.role === "user" || m.role === "coach") && typeof m.text === "string");
}

// ---- shared pieces ----------------------------------------------------------------------

const STEPS = [
  { key: "plan", label: "Plan chat" },
  { key: "selfcheck", label: "Self-check" },
  { key: "diagnostic", label: "Diagnostic" },
];

function stepper(active) {
  return h("ol", { class: "su-steps", "aria-label": "Setup steps" },
    ...STEPS.map((s, i) => h("li", { class: s.key === active ? "su-step su-step-on" : "su-step" },
      h("a", { href: "#/setup/" + s.key, "aria-current": s.key === active ? "step" : null },
        h("span", { class: "su-step-n" }, String(i + 1)), s.label))));
}

function head(active, title, lede) {
  return [
    h("p", { class: "su-back" }, h("a", { href: "#/" }, "← Home")),
    stepper(active),
    h("h1", null, title),
    h("p", { class: "lede" }, lede),
  ];
}

/** A notice for a coach failure, with "Choose a coach" when the coach is missing. */
function errorNotice(err) {
  const e = coachError(err);
  return h("div", { class: "notice notice-warn su-error", role: "alert" },
    h("p", null, e.text),
    e.setup ? h("p", null, h("a", { class: "btn btn-sm btn-primary", href: "#/welcome" }, "Choose a coach")) : null);
}

function working(text) {
  return h("div", { class: "su-working", role: "status" },
    h("span", { class: "pr-spin", "aria-hidden": "true" }), h("span", null, text));
}

function savedList(saved) {
  if (!saved) return null;
  const written = saved.written || [];
  const skipped = saved.skipped || [];
  return h("div", { class: "su-saved" },
    written.length ? h("p", null, "Written: ",
      ...written.flatMap((name, i) => [i ? ", " : "",
        h("a", { href: "#/doc/my-prep/" + name }, name)])) : null,
    ...skipped.map((s) => h("p", { class: "notice notice-warn" }, "Not written: " + s)));
}

const md = (text) => {
  const el = renderMarkdown(text || "", { images: false, breaks: true });
  el.classList.add("pr-md");
  return el;
};

function debounce(fn, ms) {
  let t = null;
  const wrapped = (...a) => { clearTimeout(t); t = setTimeout(() => { t = null; fn(...a); }, ms); };
  wrapped.flush = (...a) => { if (t) { clearTimeout(t); t = null; fn(...a); } };
  wrapped.cancel = () => { clearTimeout(t); t = null; };
  return wrapped;
}

// ---- page ------------------------------------------------------------------------------

export async function render(container, params) {
  const view = { plan: planView, selfcheck: selfcheckView, diagnostic: diagnosticView }[params.step];
  container.classList.add("su-page", "su-" + params.step);
  return view(container, params);
}

// ---- 1. the plan chat -------------------------------------------------------------------

async function planView(root, { isStale }) {
  const data = await get("/setup/discovery");
  if (isStale()) return undefined;
  document.title = "Plan chat · LeetCode Prep";
  let ctrl = null;
  let turns = chatTurns(data.messages);
  let done = !!data.done;

  root.append(...head("plan", "Set up your plan",
    "A short chat with the coach about your target, your timeline and the hours you have. "
    + "When it looks right, press Finish: the app writes your profile and your plan."));

  const log = h("div", { class: "su-log", "aria-live": "polite" });
  const input = h("textarea", { class: "su-input", rows: "3", "aria-label": "Your answer",
    placeholder: "Type your answer. Enter sends, Shift+Enter adds a line." });
  const send = h("button", { class: "btn btn-primary btn-sm", type: "button" }, "Send");
  const finish = h("button", { class: "btn btn-sm", type: "button" });
  const reset = h("button", { class: "btn btn-quiet btn-sm", type: "button" }, "Start over");
  const status = h("div", { class: "su-status" });
  const chat = h("div", { class: "card su-chat" }, log,
    h("div", { class: "su-compose" }, input, h("div", { class: "btn-row" }, send, finish, reset)));
  root.append(chat, status);

  const addTurn = (role, text) => {
    const node = h("div", { class: "pr-msg " + (role === "user" ? "pr-msg-user" : "pr-msg-coach") },
      h("div", { class: "pr-who" }, role === "user" ? "You" : "Coach"),
      role === "user" ? h("div", { class: "pr-msg-text" }, text) : md(text));
    log.append(node);
    log.scrollTop = log.scrollHeight;
    return node;
  };
  const sync = (busy) => {
    input.disabled = send.disabled = busy;
    finish.disabled = reset.disabled = busy;
    finish.hidden = !turns.some((t) => t.role === "user");
    finish.textContent = done ? "Update my plan" : "Finish discovery";
    reset.hidden = !turns.length;
  };
  for (const t of turns) addTurn(t.role, t.text);
  if (done) status.append(doneCard(null));

  async function ask(message) {
    clear(status);
    sync(true);
    const mine = new AbortController();
    ctrl = mine;
    const you = message ? addTurn("user", message) : null;
    const reply = h("div", { class: "pr-msg pr-msg-coach pr-streaming" }, h("div", { class: "pr-who" }, "Coach"));
    let body = h("div", { class: "pr-wait" }, "Thinking…");
    reply.append(body);
    log.append(reply);
    log.scrollTop = log.scrollHeight;
    let text = "";
    let failed = null;
    await stream("/setup/chat", { message }, {
      signal: mine.signal,
      onDelta: (d) => {
        text += d;
        const next = md(text);
        body.replaceWith(next);
        body = next;
        log.scrollTop = log.scrollHeight;
      },
      onDone: (full) => { if (full) text = full; },
      onError: (err) => { failed = err; },
    });
    if (isStale() || mine.signal.aborted) return;
    ctrl = null;
    if (failed) {
      reply.remove();
      if (you) you.remove();
      input.value = message;
      status.append(errorNotice(failed));
    } else {
      reply.classList.remove("pr-streaming");
      const final = md(text);
      body.replaceWith(final);
      if (message) turns.push({ role: "user", text: message });
      turns.push({ role: "coach", text });
    }
    sync(false);
    input.focus();
  }

  function doneCard(res) {
    const answer = res && res.answer;
    return h("div", { class: "card su-done" },
      h("h2", { class: "card-title" }, "Your profile and plan are written"),
      res ? savedList(res.saved) : null,
      answer && answer.what_next ? md(answer.what_next) : null,
      h("div", { class: "btn-row" },
        h("a", { class: "btn btn-primary btn-sm", href: "#/setup/selfcheck" }, "Next: the self-check"),
        h("a", { class: "btn btn-sm", href: "#/doc/my-prep/plan.md" }, "Open my plan")));
  }

  send.addEventListener("click", () => {
    const text = input.value.trim();
    if (!text) { input.focus(); return; }
    input.value = "";
    ask(text);
  });
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey && !e.isComposing) { e.preventDefault(); send.click(); }
  });
  finish.addEventListener("click", async () => {
    clear(status);
    sync(true);
    status.append(working("The coach is writing your profile and your plan. This takes a minute."));
    let res = null;
    try { res = await post("/setup/discovery/finish"); } catch (err) {
      if (isStale()) return;
      clear(status);
      status.append(errorNotice(err));
      sync(false);
      return;
    }
    if (isStale()) return;
    done = true;
    clear(status);
    status.append(doneCard(res));
    sync(false);
    status.scrollIntoView({ behavior: "smooth", block: "start" });
  });
  reset.addEventListener("click", async () => {
    const ok = await confirmDialog("Clear this chat and start again? Files already written stay as they are.",
      { confirm: "Start over" });
    if (!ok || isStale()) return;
    try { await post("/setup/discovery/reset"); } catch (err) { toast(err.message, { kind: "error" }); return; }
    if (isStale()) return;
    turns = [];
    clear(log);
    clear(status);
    ask("");
  });

  sync(false);
  if (!turns.length) ask("");
  else input.focus();
  return () => { if (ctrl) ctrl.abort(); };
}

// ---- 2. the self-check ------------------------------------------------------------------

async function selfcheckView(root, { isStale }) {
  let data = await get("/setup/selfcheck");
  if (isStale()) return undefined;
  document.title = "Self-check · LeetCode Prep";
  root.append(...head("selfcheck", "Module 00's self-check",
    "Short answers in your own words; a line or two each is enough. The coach marks them and "
    + "the score goes into your plan. Your answers save as you type."));
  if (!data.items.length) {
    root.append(h("div", { class: "notice" }, "Module 00 has no self-check section."));
    return undefined;
  }

  const answers = { ...(data.answers || {}) };
  const save = debounce(() => {
    put("/setup/selfcheck", { answers }).catch(() => toast("Your answers did not save.", { kind: "error" }));
  }, 700);
  const list = h("ol", { class: "su-qs" });
  const status = h("div", { class: "su-status" });
  const mark = h("button", { class: "btn btn-primary", type: "button" });
  root.append(list, h("div", { class: "btn-row su-actions" }, mark), status);

  function paint() {
    clear(list);
    for (const it of data.items) {
      const key = String(it.n);
      const box = h("textarea", { class: "su-answer", rows: "3", "aria-label": "Answer to question " + it.n });
      box.value = answers[key] || "";
      box.addEventListener("input", () => { answers[key] = box.value; save(); });
      const m = it.mark;
      list.append(h("li", { class: "card su-q" + (m ? (m.correct ? " su-q-ok" : " su-q-miss") : "") },
        h("div", { class: "su-q-text" }, md(it.question)), box,
        m ? h("div", { class: "su-mark" },
          h("p", { class: "su-verdict" }, m.correct ? "✓ Right" : "✗ Not yet",
            m.note ? h("span", { class: "muted" }, " · " + m.note) : null),
          it.answer ? h("details", null, h("summary", null, "The module's answer"), md(it.answer)) : null)
          : null));
    }
    mark.textContent = data.result ? "Mark my answers again" : "Mark my answers";
    clear(status);
    if (data.result && data.result.summary) {
      status.append(h("div", { class: "card su-done" },
        h("h2", { class: "card-title" }, "Score: " + scoreLine(data.result.summary)),
        h("p", null, "It is saved on the Module 00 line of your plan."),
        data.saved ? savedList(data.saved) : null,
        h("div", { class: "btn-row" },
          h("a", { class: "btn btn-primary btn-sm", href: "#/setup/diagnostic" }, "Next: the diagnostic"),
          h("a", { class: "btn btn-sm", href: "#/module/00" }, "Reread module 00"))));
    }
  }

  mark.addEventListener("click", async () => {
    save.cancel();
    mark.disabled = true;
    clear(status);
    status.append(working("The coach is marking your answers."));
    try {
      data = await post("/setup/selfcheck/mark", { answers });
    } catch (err) {
      if (isStale()) return;
      mark.disabled = false;
      clear(status);
      status.append(errorNotice(err));
      return;
    }
    if (isStale()) return;
    mark.disabled = false;
    paint();
    status.scrollIntoView({ behavior: "smooth", block: "start" });
  });

  paint();
  return () => save.flush();
}

// ---- 3. the diagnostic ------------------------------------------------------------------

const SAVE_EVERY_S = 15;

async function diagnosticView(root, { isStale }) {
  const data = await get("/setup/diagnostic");
  if (isStale()) return undefined;
  document.title = "Diagnostic · LeetCode Prep";
  root.append(...head("diagnostic", "The diagnostic",
    "Seven problems in one sitting, about 2h50 with breaks. Write each answer in the editor: "
    + "there is no Run button, as in an interview. When you finish, the app runs your answers "
    + "on its tests and the coach scores them and dates your plan."));
  if (data.review) {
    root.append(reviewBlock(data.review, null));
    return undefined;
  }
  const problems = data.problems;
  if (!problems.length) {
    root.append(h("div", { class: "notice" }, "course/diagnostic.md lists no problems."));
    return undefined;
  }

  const rules = h("details", { class: "card su-rules" },
    h("summary", null, "The rules"),
    md(data.rules.map((r, i) => (i + 1) + ". " + r).join("\n")));
  const started = problems.some((p) => p.seconds > 0 || p.finished);
  rules.open = !started;
  root.append(rules);

  const startBtn = h("button", { class: "btn btn-primary", type: "button" }, "Start problem 1");
  const intro = h("div", { class: "btn-row su-actions" }, startBtn,
    h("span", { class: "muted" }, "The clock starts when you press it."));
  const work = h("div", { class: "su-work", hidden: !started });
  if (!started) root.append(intro);
  root.append(work);

  // tabs: one per problem, then the wrap-up
  const tabs = h("div", { class: "su-tabs", role: "tablist", "aria-label": "Diagnostic problems" });
  const pane = h("div", { class: "su-pane" });
  work.append(tabs, pane);

  const stmtBox = h("div", { class: "su-stmt" });
  const clock = h("span", { class: "su-clock", role: "timer", "aria-live": "off" });
  const editorHost = h("div", { class: "pr-editor su-editor" });
  const notesBox = h("textarea", { class: "su-notes", rows: "2",
    "aria-label": "Notes for the coach", placeholder: "Notes for the coach: your approach, where you got stuck (optional)" });
  const next = h("button", { class: "btn btn-primary btn-sm", type: "button" });
  const probTitle = h("h2", { class: "su-ptitle" });
  const codeCol = h("div", { class: "su-code" },
    h("div", { class: "su-codebar" }, probTitle, clock), editorHost, notesBox,
    h("div", { class: "btn-row" }, next,
      h("span", { class: "muted su-nolink" }, "No Run: the tests run when you finish.")));
  const probView = h("div", { class: "su-prob" }, stmtBox, codeCol);
  const wrapView = h("div", { class: "su-wrap", hidden: true });
  pane.append(probView, wrapView);

  let cur = -1;
  let tick = null;
  const editor = createEditor(editorHost, { value: problems[0].code || "", docId: 0,
    label: "Diagnostic answer, Python code editor", onChange: () => saveSoon(), onSave: () => saveNow() });
  problems.forEach((p, i) => { if (i) editor.openDoc(i, p.code || ""); });

  const payload = (i, extra = {}) => ({ slug: problems[i].slug, code: editor.getValue(i),
    notes: problems[i].notes || "", seconds: problems[i].seconds, ...extra });
  function saveNow(i = cur, extra = {}, opts = {}) {
    if (i < 0) return Promise.resolve();
    return put("/setup/diagnostic/answer", payload(i, extra), opts)
      .catch(() => { if (!isStale()) toast("Your answer did not save.", { kind: "error" }); });
  }
  const saveSoon = debounce(() => saveNow(), 1500);
  notesBox.addEventListener("input", () => { if (cur >= 0) { problems[cur].notes = notesBox.value; saveSoon(); } });

  function paintTabs(active) {
    clear(tabs);
    problems.forEach((p, i) => tabs.append(h("button", {
      class: "su-tab" + (i === active ? " su-tab-on" : "") + (p.finished ? " su-tab-done" : ""),
      type: "button", role: "tab", "aria-selected": String(i === active),
      onclick: () => open(i) }, (p.finished ? "✓ " : "") + p.n + ". " + p.title)));
    tabs.append(h("button", { class: "su-tab su-tab-wrap" + (active === -1 ? " su-tab-on" : ""),
      type: "button", role: "tab", "aria-selected": String(active === -1), onclick: () => openWrap() },
    "Finish"));
  }

  function paintClock() {
    const p = problems[cur];
    const c = clockText(p.minutes, p.seconds);
    clock.textContent = c.text + " · " + p.minutes + " min";
    clock.classList.toggle("su-over", c.over);
  }

  function statement(p) {
    const link = h("a", { href: p.url, target: "_blank", rel: "noopener noreferrer" }, "Open on LeetCode ↗");
    const st = p.statement;
    if (st && st.body) {
      const body = st.format === "html" ? h("div", { class: "md pr-stmt" }, sanitizeHtml(st.body))
        : renderMarkdown(cleanNeetcode(st.body));
      body.classList.add("pr-stmt");
      layoutStatement(body);
      return [h("h2", { class: "su-stitle" }, p.title), body, h("p", { class: "pr-linkline" }, link)];
    }
    return [h("h2", { class: "su-stitle" }, p.title),
      h("div", { class: "notice" }, h("p", null, "The statement is not downloaded. Read it on LeetCode, "
        + "then write your answer here."), h("p", null, link))];
  }

  function leave() {
    if (cur >= 0) { saveSoon.cancel(); saveNow(); }
  }

  function open(i) {
    if (i === cur && !probView.hidden) return;
    leave();
    cur = i;
    const p = problems[i];
    probView.hidden = false;
    wrapView.hidden = true;
    clear(stmtBox);
    stmtBox.append(...statement(p));
    probTitle.textContent = p.n + ". " + p.title;
    notesBox.value = p.notes || "";
    editor.showDoc(i);
    editor.refresh();
    next.textContent = i === problems.length - 1 ? "Done, go to Finish" : "Done, next problem";
    paintTabs(i);
    paintClock();
    editor.focus();
  }

  function openWrap() {
    leave();
    cur = -1;
    probView.hidden = true;
    wrapView.hidden = false;
    paintTabs(-1);
    paintWrap();
  }

  next.addEventListener("click", async () => {
    const i = cur;
    problems[i].finished = true;
    saveSoon.cancel();
    await saveNow(i, { finished: true });
    if (isStale()) return;
    const n = nextOpen(problems, i);
    if (n === -1 || n <= i && i === problems.length - 1) openWrap();
    else open(n);
  });

  // the wrap-up: the overall questions and Finish
  const overall = { ...(data.overall || {}) };
  const saveOverall = debounce(() => {
    put("/setup/diagnostic/answer", { overall }).catch(() => toast("Your answers did not save.", { kind: "error" }));
  }, 700);
  function paintWrap() {
    clear(wrapView);
    const left = problems.filter((p) => !p.finished).length;
    const finishBtn = h("button", { class: "btn btn-primary", type: "button" }, "Finish and score");
    const status = h("div", { class: "su-status" });
    wrapView.append(h("h2", null, "Three questions, then Finish"),
      ...data.overall_questions.map((q) => {
        const box = h("textarea", { class: "su-answer", rows: "3", "aria-label": q.question });
        box.value = overall[q.key] || "";
        box.addEventListener("input", () => { overall[q.key] = box.value; saveOverall(); });
        return h("label", { class: "card su-q" }, h("span", { class: "su-q-text" }, q.question), box);
      }),
      ...(left ? [h("p", { class: "notice" }, left === 1 ? "One problem is not marked done yet."
        : left + " problems are not marked done yet.")] : []),
      h("div", { class: "btn-row su-actions" }, finishBtn), status);
    finishBtn.addEventListener("click", async () => {
      if (left) {
        const ok = await confirmDialog("Finish anyway? What you wrote so far is what gets scored.",
          { confirm: "Finish and score" });
        if (!ok || isStale()) return;
      }
      saveOverall.flush();
      finishBtn.disabled = true;
      clear(status);
      status.append(working("Running your answers on the tests, then the coach scores them. "
        + "This takes a minute or two."));
      let res;
      try { res = await post("/setup/diagnostic/finish"); } catch (err) {
        if (isStale()) return;
        finishBtn.disabled = false;
        clear(status);
        status.append(errorNotice(err));
        return;
      }
      if (isStale()) return;
      stop();
      rules.remove();
      work.remove();
      root.append(reviewBlock(res.review, res.saved));
      root.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  }

  function start(at) {
    intro.remove();
    rules.open = false;
    work.hidden = false;
    open(at);
    let since = 0;
    tick = setInterval(() => {
      if (isStale() || cur < 0 || document.hidden || problems[cur].finished) return;
      problems[cur].seconds += 1;
      paintClock();
      if (++since >= SAVE_EVERY_S) { since = 0; saveNow(); }
    }, 1000);
  }
  const stop = () => { if (tick) { clearInterval(tick); tick = null; } };
  startBtn.addEventListener("click", () => start(0));
  if (started) {
    const at = nextOpen(problems);
    if (at === -1) { start(0); openWrap(); } else start(at);
  }

  const onHide = () => { if (document.hidden && cur >= 0) saveNow(cur, {}, { keepalive: true }); };
  document.addEventListener("visibilitychange", onHide);
  return () => {
    stop();
    document.removeEventListener("visibilitychange", onHide);
    if (cur >= 0) { saveSoon.cancel(); saveNow(cur, {}, { keepalive: true }); }
    saveOverall.flush();
  };
}

const OUTCOME_CLASS = { "solved clean": "su-oc-ok", "solved with bugs": "su-oc-mid",
  partial: "su-oc-mid", stuck: "su-oc-bad" };

function reviewBlock(review, saved) {
  const rows = review.problems || [];
  const blocks = blockRows(review.blocks);
  return h("div", { class: "su-review" },
    h("div", { class: "card" },
      h("h2", { class: "card-title" }, "Your diagnostic, scored"),
      h("table", { class: "su-table" },
        h("thead", null, h("tr", null, h("th", null, "Problem"), h("th", null, "Tests"),
          h("th", null, "Outcome"), h("th", null, "The coach's note"))),
        h("tbody", null, ...rows.map((p) => h("tr", null,
          h("td", null, p.title),
          h("td", null, p.result || "—"),
          h("td", null, p.outcome ? h("span", { class: "tag " + (OUTCOME_CLASS[p.outcome] || "") }, p.outcome) : "—"),
          h("td", null, p.comment || "")))))),
    blocks.length ? h("div", { class: "card" },
      h("h2", { class: "card-title" }, "Your plan, dated"),
      h("table", { class: "su-table" },
        h("thead", null, h("tr", null, h("th", null, "Module"), h("th", null, "From"),
          h("th", null, "To"), h("th", null, "Hours"))),
        h("tbody", null, ...blocks.map((b) => h("tr", null,
          h("td", null, "Module " + b.module + (b.title ? " · " + b.title : "")), h("td", null, b.start || "—"),
          h("td", null, b.end || "—"), h("td", null, b.hours == null ? "—" : String(b.hours))))))) : null,
    (review.matrix || []).length ? h("div", { class: "card" },
      h("h2", { class: "card-title" }, "Skills matrix, updated"),
      h("ul", { class: "su-matrix" }, ...review.matrix.map((m) => h("li", null,
        h("strong", null, m.id), " → level " + m.level + (m.evidence ? ": " + m.evidence : ""))))) : null,
    (review.known_gaps || []).length ? h("div", { class: "card" },
      h("h2", { class: "card-title" }, "Known gaps"),
      h("ul", null, ...review.known_gaps.map((g) => h("li", null, g)))) : null,
    review.what_next ? h("div", { class: "card su-done" },
      h("h2", { class: "card-title" }, "What's next"), md(review.what_next),
      savedList(saved),
      h("div", { class: "btn-row" },
        h("a", { class: "btn btn-primary btn-sm", href: "#/" }, "Back to Home"),
        h("a", { class: "btn btn-sm", href: "#/doc/my-prep/plan.md" }, "Open my plan"),
        h("a", { class: "btn btn-sm", href: "#/review" }, "Skills matrix"))) : null);
}

