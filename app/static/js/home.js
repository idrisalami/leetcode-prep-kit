// Home (spec §7.2): greeting, today's warm-up, four KPI tiles, progress by module, the matrix
// mini-grid, mistakes to watch, and the setup card while problem statements are missing.

import { get, post } from "./api.js";
import { h, clear, fmtDuration, attachTooltip, emptyState, inlineCode, toast } from "./ui.js";
import { navigate, refreshNav } from "./main.js";

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

function lede(o) {
  const m = o.current_module || { id: "01", title: "Arrays and hashing" };
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
      h("a", { class: "btn btn-sm", href: "#/review" }, "Open Review")));
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
    h("p", { class: "small" }, "One square per row of your matrix. Click to open it in Review."));
  return card;
}

// ---- mistakes ------------------------------------------------------------------------

function mistakesCard(o) {
  const items = o.mistakes || [];
  const card = h("section", { class: "card" }, h("h2", null, "Mistakes to watch"));
  if (!items.length) {
    card.append(emptyState("No mistakes logged yet. Bugs you record in your bug log show up here."));
    return card;
  }
  card.append(h("ul", { class: "plain" }, items.map((m) => h("li", null,
    inlineCode(m.bug),
    m.check ? h("span", { class: "mistake-check" }, "Check: ", inlineCode(m.check)) : null))));
  return card;
}

// ---- setup card ------------------------------------------------------------------------

function failedSlugs(failed) {
  return (failed || []).map((f) => (f && typeof f === "object" ? f.slug : String(f))).filter(Boolean);
}

function setupCard(o, state) {
  const s = o.setup || {};
  const missing = (s.statements_have || 0) < (s.statements_total || 0);
  if (!missing && s.claude !== false) return null;
  const card = h("section", { class: "card setup-card", "aria-label": "Setup" });
  const body = h("div");
  card.append(h("h2", null, "Finish setting up"), body);

  const claudeNote = s.claude === false ? h("p", { class: "notice" },
    "The coach needs the claude command-line tool, which is not on this computer; everything else works without it.")
    : null;

  const drawStatus = (st) => {
    clear(body);
    // Element.append would print "null" for a missing note; only add real nodes.
    const append = body.append.bind(body);
    body.append = (...nodes) => append(...nodes.filter(Boolean));
    const have = st.have || 0;
    const total = st.total || 0;
    const failed = failedSlugs(st.failed);
    if (total && have >= total) {
      body.append(h("p", null, "All " + total + " problem statements are downloaded."), claudeNote);
      return;
    }
    body.append(h("p", null, "Problem statements: " + have + " of " + total + " downloaded. "
      + "The practice page shows each statement next to the editor. Without it, the page links to LeetCode."));
    if (st.running) {
      const pct = total ? Math.round((have / total) * 100) : 0;
      body.append(h("div", { class: "setup-progress", role: "status" },
        h("span", { class: "bar", "aria-hidden": "true" }, h("i", { style: { width: pct + "%" } })),
        h("span", null, "Downloading… " + have + " of " + total)));
    } else {
      const btn = h("button", { class: "btn btn-primary", type: "button" },
        failed.length ? "Try the download again" : "Download problem statements");
      btn.addEventListener("click", () => start(btn));
      body.append(h("div", { class: "btn-row" }, btn));
      if (failed.length) {
        body.append(h("p", { class: "notice notice-warn" },
          plural(failed.length, "statement", "statements") + " could not be downloaded: "
          + failed.slice(0, 6).join(", ") + (failed.length > 6 ? " and " + (failed.length - 6) + " more" : "")
          + ". Those problems still work; their page links to LeetCode."));
      }
    }
    if (st.save_error) body.append(h("p", { class: "notice notice-warn" }, st.save_error));
    body.append(claudeNote);
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
    const st = Object.assign({}, res.statements || {}, { save_error: res.save_error });
    drawStatus(st);
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

  drawStatus({ have: s.statements_have, total: s.statements_total, running: false, failed: [] });
  // A download may already be running (started from another tab or the command line).
  if (missing) poll();
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
  clear(container);
  // Element.append prints "null" for a missing node (no setup card), so only real nodes go in.
  container.append(...[
    h("h1", null, greeting()),
    h("p", { class: "lede" }, lede(o)),
    ...noticeCards(o),
    setupCard(o, state),
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
