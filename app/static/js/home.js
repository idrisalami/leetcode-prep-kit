// Home (spec §7.2): greeting, today's warm-up, four KPI tiles, progress by module, the matrix
// mini-grid, mistakes to watch, and the get started checklist until its steps are ticked.

import { get, post } from "./api.js";
import { h, clear, fmtDuration, attachTooltip, emptyState, inlineCode, toast, readJson, writeJson }
  from "./ui.js";
import { navigate, refreshNav } from "./main.js";
import { HIDE_KEY, stepStates, canHide, showStart, countLabel } from "./start.js";
import { isCoachPayload, coachStatus, unavailableText } from "./coachpick.js";

const POLL_MS = 1500;

function greeting(now = new Date()) {
  const hour = now.getHours();
  if (hour < 5) return "Good evening";
  if (hour < 12) return "Good morning";
  if (hour < 18) return "Good afternoon";
  return "Good evening";
}

function plural(n, one, many) {
  return n + " " + (n === 1 ? one : many);
}

function hasActivity(o) {
  const k = o.kpis || {};
  return (k.solved || 0) > 0 || (k.seconds || 0) > 0 || (k.submitted_n || 0) > 0;
}

function lede(o, starting) {
  const m = o.current_module || { id: "01", title: "Arrays and hashing" };
  if (starting && !hasActivity(o)) {
    return "Welcome. The steps below get you set up, and you can start coding at any point.";
  }
  if (!hasActivity(o)) return "Day 1. Start with module " + m.id + " — " + m.title + ".";
  return "Day " + (o.day || 1) + ". You're in module " + m.id + " — " + m.title + ".";
}

// ---- warm-up ---------------------------------------------------------------------

function warmupCard(o, isStale) {
  const card = h("section", { class: "card warm", "aria-label": "Today's warm-up" });
  const draw = (w) => {
    clear(card);
    if (!w) {
      card.append(h("div", { class: "warm-body" }, h("h2", null, "Today's warm-up"),
        h("div", { class: "warm-meta" }, "No warm-up today. Every Easy problem is already solved.")));
      return;
    }
    const another = h("button", { class: "btn", type: "button" }, "Pick another");
    another.addEventListener("click", async () => {
      another.disabled = true;
      try {
        const res = await post("/warmup/another", {});
        draw(res && res.warmup);
      } catch (e) {
        if (!isStale()) toast(e.detail || "Could not pick another warm-up.", { kind: "error" });
        another.disabled = false;
      }
    });
    const meta = [w.difficulty || "Easy", "about 10 minutes",
      "from module " + w.module + (w.module_title ? ", " + w.module_title : "")].join(" · ");
    card.append(
      h("div", { class: "warm-body" },
        h("h2", null, "Today's warm-up"),
        h("div", { class: "warm-title" }, w.title),
        h("div", { class: "warm-meta" }, meta,
          w.done ? h("span", { class: "warm-done" }, " · ✓ done today") : null)),
      another,
      h("button", { class: "btn btn-primary", type: "button",
        onclick: () => navigate("#/practice/" + w.slug) }, w.done ? "Open it again" : "Start coding"));
  };
  draw(o.warmup);
  return card;
}

// ---- KPI tiles -------------------------------------------------------------------

function tile(value, label, detail) {
  return h("div", { class: "card kpi" },
    h("div", { class: "kpi-v" }, value),
    h("div", { class: "kpi-l" }, label),
    h("div", { class: "kpi-d" }, detail));
}

function kpiTiles(o) {
  const k = o.kpis || {};
  const solved = k.solved || 0;
  const total = k.total || 0;
  const firstTry = (k.submitted_n || 0) > 0;
  return h("div", { class: "kpis" },
    tile([String(solved), h("small", null, " of " + total)], "Problems solved",
      solved ? (k.solved_week || 0) + " this week" : "Your first solve shows up here"),
    tile(fmtDuration(k.seconds || 0), "Time on the platform",
      (k.seconds || 0) ? fmtDuration(k.seconds_week || 0) + " this week"
        : "Counted while you work in the app"),
    tile(plural(k.streak || 0, "day", "days"), "Current streak",
      (k.best_streak || 0) ? "Best: " + plural(k.best_streak, "day", "days")
        : "A day counts when you practise"),
    tile(firstTry ? Math.round(k.first_try_pct || 0) + "%" : "–", "Solved on first try",
      firstTry ? (k.first_try_n || 0) + " of " + plural(k.submitted_n, "problem", "problems")
        + " passed the app's tests on the first submit"
        : "Shows after your first solve"));
}

// ---- progress by module --------------------------------------------------------------

function progressCard(o) {
  const card = h("section", { class: "card" }, h("h2", null, "Progress by module"));
  const mods = o.modules || [];
  const current = o.current_module && o.current_module.id;
  for (const m of mods.filter((x) => x.id !== "00")) {
    const pct = Math.max(0, Math.min(100, Math.round(m.pct || 0)));
    const row = h("a", { class: "prog-row" + (m.id === current ? " is-next" : ""),
      href: "#/module/" + m.id, "aria-label": m.id + " " + m.title + ", " + m.solved + " of "
        + m.total + " solved" },
      h("span", { class: "prog-n" }, m.id),
      h("span", { class: "prog-name" }, h("span", null, m.title),
        m.id === current ? h("span", { class: "tag tag-next" }, "next up") : null),
      h("span", { class: "bar", "aria-hidden": "true" }, h("i", { style: { width: pct + "%" } })),
      h("span", { class: "prog-p" }, pct + "%"));
    attachTooltip(row, () => ({ value: m.solved + " of " + m.total + " solved", label: m.title }));
    card.append(row);
  }
  const zero = mods.find((x) => x.id === "00");
  if (zero) {
    card.append(h("hr", { class: "prog-sep" }),
      h("a", { class: "prog-row", href: "#/module/00" },
        h("span", { class: "prog-n" }, "00"),
        h("span", { class: "prog-name" }, h("span", null, zero.title)),
        h("span", { class: "prog-read" + (zero.read ? " is-read" : "") },
          zero.read ? "✓ read" : "not read yet")));
  }
  return card;
}

// ---- matrix mini-grid ----------------------------------------------------------------

function step(now) {
  if (now === "3") return "3";
  if (now === "1" || now === "2") return "2";
  if (now === "0") return "1";
  return "unknown";
}

function matrixCard(o) {
  const rows = o.matrix || [];
  const card = h("section", { class: "card" }, h("h2", null, "Skills matrix"));
  if (!rows.length) {
    card.append(emptyState("Your skills matrix is empty. It fills in after the diagnostic.",
      h("a", { class: "btn btn-sm", href: "#/review" }, "Open the skills matrix")));
    return card;
  }
  const grid = h("div", { class: "mx" });
  for (const r of rows) {
    const known = r.now !== "?" && r.now !== undefined && r.now !== null && r.now !== "";
    const score = known ? r.now + " of 3" : "not tested yet";
    const cell = h("a", { class: "mx-cell", href: "#/review", dataset: { step: step(String(r.now)) },
      "aria-label": r.id + ": " + score + ". " + (r.requirement || "") }, known ? r.now : "?");
    attachTooltip(cell, () => ({ value: r.id + " · " + score, label: r.requirement || "" }));
    grid.append(cell);
  }
  card.append(grid,
    h("div", { class: "legend" },
      h("span", null, h("i", { dataset: { step: "3" } }), "Solid = 3"),
      h("span", null, h("i", { dataset: { step: "2" } }), "Getting there = 1–2"),
      h("span", null, h("i", { dataset: { step: "1" } }), "Not yet = 0"),
      h("span", null, h("i", { class: "unknown" }), "Not tested = ?")),
    h("p", { class: "small" }, "One square per row of your matrix. Click to open the skills matrix."));
  return card;
}

// ---- mistakes ------------------------------------------------------------------------

function mistakesCard(o) {
  const items = o.mistakes || [];
  const card = h("section", { class: "card" }, h("h2", null, "Mistakes to watch"));
  if (!items.length) {
    card.append(emptyState("Nothing yet. The mistakes named in your final reviews show up here."));
    return card;
  }
  card.append(h("ul", { class: "plain" }, items.map((m) => h("li", null,
    inlineCode(m.bug),
    m.check ? h("span", { class: "mistake-check" }, "Check: ", inlineCode(m.check)) : null))));
  // Say which note the list comes from, so an empty "My mistakes" page is not a surprise.
  card.append(h("p", { class: "small muted mistake-source" }, items[0].source === "learnings"
    ? ["From your latest ", h("a", { href: "#/doc/my-prep/learnings.md" }, "Learnings"),
      ". A mistake moves to My mistakes the second time you make it."]
    : ["Your top 5 from ", h("a", { href: "#/doc/my-prep/bugs.md" }, "My mistakes"), "."]));
  return card;
}

// ---- get started ---------------------------------------------------------------------

function failedSlugs(failed) {
  return (failed || []).map((f) => (f && typeof f === "object" ? f.slug : String(f))).filter(Boolean);
}

const START_TITLES = {
  statements: "Download the problem statements",
  plan: "Set up your plan with the coach",
  selfcheck: "Answer module 00's self-check",
  diagnostic: "Take the diagnostic",
  solve: "Solve your first problem",
};

/**
 * The checklist a newcomer follows, in the order the work is done: statements, the plan chat
 * with the coach, module 00's self-check, the diagnostic, a first solve. Every step happens in
 * the app. Which steps there are and which are ticked comes from start.js, so every tick
 * follows the real files. Returns null when there is nothing left to show.
 */
function startCard(o, state) {
  const s = o.setup || {};
  const isHidden = () => readJson(HIDE_KEY) === true;
  if (!showStart(stepStates(o, null), isHidden())) return null;

  let st = null;      // the newest /setup/status answer, once one has arrived
  let drawn = "";     // what the list shows now, to skip redraws that would change nothing
  let progress = null;

  const card = h("section", { class: "card start-card", "aria-label": "Get started" });
  const count = h("span", { class: "start-count" });
  const hide = h("button", { class: "btn btn-quiet btn-sm", type: "button",
    "aria-label": "Hide the get started steps" }, "Hide");
  const list = h("ol", { class: "start-list" });
  card.append(h("div", { class: "start-head" }, h("h2", null, "Get started"), count, hide), list);
  hide.addEventListener("click", () => {
    writeJson(HIDE_KEY, true);
    card.remove();
  });

  const text = (...parts) => h("p", { class: "start-text" }, ...parts);
  const btnClass = (step) => "btn btn-sm" + (step.next ? " btn-primary" : "");
  const numbers = () => {
    const have = Number(st ? st.have : s.statements_have) || 0;
    const total = Number(st ? st.total : s.statements_total) || 0;
    return { have, total, pct: total ? Math.round((have / total) * 100) : 0 };
  };

  // What each open step shows: {body: [nodes], action: node or null}.
  const parts = {
    statements(step) {
      const { have, total, pct } = numbers();
      const failed = failedSlugs(st && st.failed);
      const body = [text("Each problem then shows its statement next to the editor. "
        + "Until then, its page links to LeetCode."
        + (have && !(st && st.running) ? " " + have + " of " + total + " are here so far." : ""))];
      let action = null;
      if (st && st.running) {
        progress = { bar: h("i", { style: { width: pct + "%" } }),
          label: h("span", null, "Downloading… " + have + " of " + total) };
        body.push(h("div", { class: "start-progress", role: "status" },
          h("span", { class: "bar", "aria-hidden": "true" }, progress.bar), progress.label));
      } else {
        action = h("button", { class: btnClass(step), type: "button",
          "aria-label": failed.length ? "Try the download again" : "Download the problem statements" },
        failed.length ? "Try again" : "Download");
        action.addEventListener("click", () => start(action));
        if (failed.length) {
          body.push(h("p", { class: "notice notice-warn" },
            plural(failed.length, "statement", "statements") + " could not be downloaded: "
            + failed.slice(0, 6).join(", ") + (failed.length > 6 ? " and " + (failed.length - 6) + " more" : "")
            + ". Those problems still work; their page links to LeetCode."));
        }
      }
      if (st && st.save_error) body.push(h("p", { class: "notice notice-warn" }, st.save_error));
      return { body, action };
    },
    solve(step) {
      const w = o.warmup;
      return {
        body: [text("Write your solution in the editor and press Submit; the app runs its tests. "
          + (w && w.title ? "Today's warm-up is " + w.title + "." : "Any problem counts."))],
        // Never the primary button: the warm-up card right below carries the same action in blue.
        action: h("button", { class: "btn btn-sm", type: "button",
          onclick: () => navigate(w && w.slug ? "#/practice/" + w.slug : "#/practice") }, "Start coding"),
      };
    },
    plan(step) {
      const c = coachStatus(s);
      const body = [step.state === "doing"
        ? text("Your first answers are saved. Open the chat again and carry on where you stopped.")
        : text("A short chat, right here: your target, your timeline, the hours you have. "
          + "The app then writes your profile and your plan.")];
      return { body, action: needsCoach(step, c, body)
        || h("a", { class: btnClass(step), href: "#/setup/plan" },
          step.state === "doing" ? "Continue the chat" : "Start the chat") };
    },
    selfcheck(step) {
      const c = coachStatus(s);
      const body = [text("Eight short questions on the basics module 00 covers. The coach marks "
        + "them and the score goes into your plan.")];
      return { body, action: needsCoach(step, c, body)
        || h("a", { class: btnClass(step), href: "#/setup/selfcheck" }, "Open the self-check") };
    },
    diagnostic(step) {
      const c = coachStatus(s);
      const body = [text("Seven timed problems in the app's editor, with no Run button: about "
        + "2h50 in one sitting, breaks included. The app runs your answers on its tests, and the "
        + "coach scores them and dates your plan.")];
      return { body, action: needsCoach(step, c, body)
        || h("a", { class: btnClass(step), href: "#/setup/diagnostic" },
          step.state === "doing" ? "Continue the diagnostic" : "Open the diagnostic") };
    },
  };

  // The coach steps need a connected coach. Without one, say so and offer the welcome page;
  // returns that button, or null when the coach is ready.
  function needsCoach(step, c, body) {
    if (c.kind === "ready") return null;
    body.push(text(unavailableText(c) + " This step needs a coach; the rest of the app works "
      + "without one."));
    return isCoachPayload(s.coach)
      ? h("a", { class: btnClass(step), href: "#/welcome" },
        c.kind === "none" ? "Connect a coach" : "Choose a coach")
      : h("a", { class: btnClass(step), href: "https://claude.com/claude-code",
        target: "_blank", rel: "noopener noreferrer" }, "Get Claude Code");
  }

  const row = (step, n) => {
    const done = step.state === "done";
    const p = done ? { body: [], action: null } : parts[step.key](step);
    const data = { state: step.state };
    if (step.next) data.next = "1";
    return h("li", { class: "start-step", dataset: data },
      h("span", { class: "start-mark", "aria-hidden": "true" }, done ? "✓" : String(n)),
      h("div", { class: "start-body" },
        h("div", { class: "start-title" }, START_TITLES[step.key],
          done ? h("span", { class: "visually-hidden" }, " (done)") : null,
          step.state === "doing" && step.key !== "statements"
            ? h("span", { class: "tag tag-next" }, "in progress") : null),
        ...p.body),
      p.action ? h("div", { class: "start-act" }, p.action) : null);
  };

  const draw = () => {
    const steps = stepStates(o, st);
    if (!showStart(steps, isHidden())) {
      card.remove();
      return;
    }
    // While a download runs, only its bar moves: rebuilding the list on every poll would
    // take the keyboard focus off whatever the reader is on.
    const key = JSON.stringify([steps, failedSlugs(st && st.failed), st && st.save_error]);
    if (key === drawn && st && st.running && progress) {
      const { have, total, pct } = numbers();
      progress.bar.style.width = pct + "%";
      progress.label.textContent = "Downloading… " + have + " of " + total;
      return;
    }
    drawn = key;
    progress = null;
    count.textContent = countLabel(steps);
    hide.hidden = !canHide(steps);
    clear(list);
    steps.forEach((step, i) => list.append(row(step, i + 1)));
  };

  const poll = async () => {
    state.timer = null;
    let res;
    try {
      res = await get("/setup/status");
    } catch (e) {
      if (state.dead || state.isStale()) return;
      state.timer = setTimeout(poll, POLL_MS * 2);
      return;
    }
    if (state.dead || state.isStale()) return;
    st = Object.assign({}, res.statements || {}, { save_error: res.save_error });
    draw();
    if (st.running) state.timer = setTimeout(poll, POLL_MS);
    else if (state.wasRunning) {
      state.wasRunning = false;
      toast(failedSlugs(st.failed).length ? "The download finished with some failures."
        : "Problem statements are downloaded.");
      refreshNav();
    }
    if (st.running) state.wasRunning = true;
  };

  const start = async (btn) => {
    btn.disabled = true;
    try {
      await post("/setup/statements", {});
      if (state.dead || state.isStale()) return;
      state.wasRunning = true;
      poll();
    } catch (e) {
      btn.disabled = false;
      if (!state.isStale()) toast(e.detail || "The download could not start.", { kind: "error" });
    }
  };

  draw();
  // A download may already be running (started from another tab or the command line).
  if ((s.statements_have || 0) < (s.statements_total || 0)) poll();
  return card;
}

// ---- server notices ------------------------------------------------------------------

/** The server's notices (state could not be saved, state was recovered) as cards at the top. */
function noticeCards(o) {
  return (o.notices || []).filter((n) => n && n.text).map((n) =>
    h("p", { class: "notice notice-warn", role: n.kind === "save_error" ? "alert" : "status" }, n.text));
}

// ---- page ------------------------------------------------------------------------------

export async function render(container, params = {}) {
  const isStale = params.isStale || (() => false);
  const o = await get("/overview");
  if (isStale()) return null;
  document.title = "Home · LeetCode Prep";
  const state = { timer: null, dead: false, wasRunning: false, isStale };
  const starting = startCard(o, state);
  clear(container);
  // Element.append prints "null" for a missing node (no checklist), so only real nodes go in.
  container.append(...[
    h("h1", null, greeting()),
    h("p", { class: "lede" }, lede(o, !!starting)),
    ...noticeCards(o),
    starting,
    warmupCard(o, isStale),
    kpiTiles(o),
    h("div", { class: "two" },
      progressCard(o),
      h("div", { class: "stack" }, matrixCard(o), mistakesCard(o))),
  ].filter(Boolean));
  return () => {
    state.dead = true;
    if (state.timer) clearTimeout(state.timer);
  };
}
