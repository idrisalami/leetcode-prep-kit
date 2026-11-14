// Problem browser (spec §7.4): every problem on the list, grouped by module, with status,
// difficulty and module filters, a "pick up where you left off" card, and one action per row.
//
// Contract: render(container, params) returns its teardown at once and loads in the background,
// so leaving the page aborts the fetches. Nothing outside the container is touched once
// params.isStale() turns true. Filter state lives in the hash query (written with replaceState,
// so it never re-renders) with localStorage as the fallback.
//
// main.js is imported lazily (it touches `document` on import), so the pure helpers below can
// be imported by node --test.

import { get } from "./api.js";
import {
  h, clear, fmtDuration, fmtDate, difficultyPill, statusMark, attachTooltip, emptyState,
  readJson, writeJson,
} from "./ui.js";
import { redoButton } from "./redo.js";

const STATUSES = ["new", "attempted", "solved"];
const DIFFICULTIES = ["Easy", "Medium", "Hard"];
const STATUS_WORDS = { all: "All", new: "Not started", attempted: "In progress", solved: "Solved" };
const FILTER_KEY = "prep.browse.filters";
const OPENED_KEY = "prep.browse.opened";

// ---- pure helpers (tested in tests/browse-problems.test.mjs) ----------------------------

const statusOf = (p) => (STATUSES.includes(p && p.status) ? p.status : "new");

/** Raw query or stored values -> {status, difficulty, module}; anything unknown is "all". */
export function normalizeFilters(raw, moduleIds = []) {
  const r = raw && typeof raw === "object" ? raw : {};
  const status = STATUSES.includes(r.status) ? r.status : "all";
  const d = typeof r.difficulty === "string" ? r.difficulty.trim().toLowerCase() : "";
  const difficulty = DIFFICULTIES.find((x) => x.toLowerCase() === d) || "all";
  const module = typeof r.module === "string" && moduleIds.includes(r.module) ? r.module : "all";
  return { status, difficulty, module };
}

/** Filters -> "status=…&difficulty=…&module=…" without the defaults; "" when all are "all". */
export function filtersToQuery(f) {
  const parts = [];
  for (const k of ["status", "difficulty", "module"]) {
    if (f[k] && f[k] !== "all") parts.push(k + "=" + encodeURIComponent(f[k]));
  }
  return parts.join("&");
}

function matches(p, f, skip) {
  if (skip !== "status" && f.status !== "all" && statusOf(p) !== f.status) return false;
  if (skip !== "difficulty" && f.difficulty !== "all" && p.difficulty !== f.difficulty) return false;
  if (skip !== "module" && f.module !== "all" && p.module !== f.module) return false;
  return true;
}

/** The problems that pass all three filters, in list order. */
export function filterProblems(problems, f) {
  return (problems || []).filter((p) => matches(p, f));
}

/** For each filter, how many problems each option would show with the other two applied. */
export function facetCounts(problems, f, moduleIds = []) {
  const out = {
    status: { all: 0, new: 0, attempted: 0, solved: 0 },
    difficulty: { all: 0, Easy: 0, Medium: 0, Hard: 0 },
    module: { all: 0 },
  };
  for (const id of moduleIds) out.module[id] = 0;
  for (const p of problems || []) {
    if (matches(p, f, "status")) { out.status.all++; out.status[statusOf(p)]++; }
    if (matches(p, f, "difficulty")) {
      out.difficulty.all++;
      if (p.difficulty in out.difficulty) out.difficulty[p.difficulty]++;
    }
    if (matches(p, f, "module")) {
      out.module.all++;
      out.module[p.module] = (out.module[p.module] || 0) + 1;
    }
  }
  return out;
}

/**
 * Module groups in module order, each with its whole-module progress and only the rows that pass
 * the filters. Groups with no matching row are left out. A problem whose module is not in the
 * module list still shows, under "Module NN", after the known ones.
 */
export function groupByModule(problems, modules, f) {
  const order = [];
  const byId = new Map();
  for (const m of modules || []) {
    byId.set(m.id, { id: m.id, title: m.title, solved: 0, total: 0, rows: [] });
    order.push(m.id);
  }
  for (const p of problems || []) {
    if (!byId.has(p.module)) {
      byId.set(p.module, { id: p.module, title: "Module " + p.module, solved: 0, total: 0, rows: [] });
      order.push(p.module);
    }
    const g = byId.get(p.module);
    g.total++;
    if (statusOf(p) === "solved") g.solved++;
    if (matches(p, f)) g.rows.push(p);
  }
  return order.map((id) => byId.get(id)).filter((g) => g.rows.length > 0);
}

/** The first module (in module order) with a problem not yet solved, or null. */
export function nextUpModule(problems, modules) {
  for (const m of modules || []) {
    const mine = (problems || []).filter((p) => p.module === m.id);
    if (mine.length && mine.some((p) => statusOf(p) !== "solved")) return m.id;
  }
  return null;
}

const stamp = (s) => (typeof s === "string" && s ? Date.parse(s) : NaN);

function latest(a, b) {
  if (Number.isNaN(stamp(a))) return Number.isNaN(stamp(b)) ? null : b;
  if (Number.isNaN(stamp(b))) return a;
  return stamp(b) > stamp(a) ? b : a;
}

/**
 * {slug: last touch} for the attempted problems: the later of the server's `last_at` (draft
 * save, run, submit or chat turn; local time without a zone) and the time this browser last
 * opened it from the list (`opened`, from localStorage). Problems with neither are left out.
 */
export function touchTimes(problems, opened = {}) {
  const out = {};
  const seen = opened && typeof opened === "object" ? opened : {};
  for (const p of problems || []) {
    if (!p || !p.slug || statusOf(p) !== "attempted") continue;
    const t = latest(p.last_at, seen[p.slug]);
    if (t) out[p.slug] = t;
  }
  return out;
}

/**
 * The attempted problem to offer first: the latest touch time, then more time spent, then list
 * order. Null when nothing is in progress.
 */
export function pickContinue(problems, touches = {}) {
  const open = (problems || []).map((p, i) => ({ p, i })).filter((x) => statusOf(x.p) === "attempted");
  if (!open.length) return null;
  const t = (p) => { const v = stamp(touches[p.slug]); return Number.isNaN(v) ? -Infinity : v; };
  open.sort((a, b) => (t(b.p) - t(a.p)) || ((b.p.seconds || 0) - (a.p.seconds || 0)) || (a.i - b.i));
  return open[0].p;
}

/** The one action a row offers. */
export function actionFor(p) {
  const s = statusOf(p);
  if (s === "solved") return { kind: "redo", label: "Redo" };
  if (s === "attempted") return { kind: "continue", label: "Continue" };
  return { kind: "start", label: "Start coding" };
}

// ---- storage -------------------------------------------------------------------------

/** Remember that a problem was opened from this page, as one more "last touched" signal. */
function noteOpened(slug) {
  const seen = readJson(OPENED_KEY) || {};
  seen[slug] = new Date().toISOString();
  const recent = Object.entries(seen).sort((a, b) => (a[1] < b[1] ? 1 : -1)).slice(0, 40);
  writeJson(OPENED_KEY, Object.fromEntries(recent));
}

// ---- DOM pieces ----------------------------------------------------------------------

function actionButton(p, isStale) {
  const a = actionFor(p);
  const label = a.label + ": " + p.title;
  if (a.kind === "redo") {
    return redoButton(p, { attrs: { "aria-label": label }, label: a.label, isStale,
      onOpen: () => noteOpened(p.slug) });
  }
  return h("a", { class: "btn btn-sm" + (a.kind === "continue" ? " btn-primary" : ""),
    href: "#/practice/" + p.slug, "aria-label": label, onclick: () => noteOpened(p.slug) }, a.label);
}

function problemRow(p, isStale) {
  const premium = p.premium
    ? h("span", { class: "tag tag-premium", title: "Premium on LeetCode. You can still solve it here." },
      "premium", h("span", { class: "sr-only" }, ". Premium on LeetCode. You can still solve it here."))
    : null;
  return h("tr", { dataset: { slug: p.slug } },
    h("td", { class: "td-id" }, p.number != null ? String(p.number) : ""),
    h("td", { class: "td-title" },
      h("a", { href: "#/practice/" + p.slug, onclick: () => noteOpened(p.slug) }, p.title), premium),
    h("td", null, difficultyPill(p.difficulty)),
    h("td", null, statusMark(statusOf(p), p.seconds > 0 ? fmtDuration(p.seconds) : "")),
    h("td", { class: "td-action" }, actionButton(p, isStale)));
}

function moduleCard(g, nextUp, isStale) {
  const pct = g.total ? Math.round((g.solved / g.total) * 100) : 0;
  const head = h("div", { class: "browse-head" },
    h("h2", { class: "browse-title" },
      h("a", { href: "#/module/" + g.id }, h("span", { class: "browse-n" }, g.id), " · " + g.title)),
    g.id === nextUp ? h("span", { class: "tag tag-next" }, "next up") : null,
    h("span", { class: "browse-progress" },
      h("span", { class: "bar", "aria-hidden": "true" }, h("i", { style: { width: pct + "%" } })),
      h("span", { class: "browse-count" }, g.solved + " of " + g.total + " solved")));
  return h("section", { class: "card card-flush browse-card", "aria-label": "Module " + g.id + ", " + g.title },
    head,
    h("div", { class: "table-wrap" },
      h("table", { class: "table-hover browse-table" },
        h("thead", null, h("tr", null,
          h("th", { class: "td-id" }, "#"), h("th", null, "Problem"), h("th", null, "Level"),
          h("th", null, "Status"), h("th", null, h("span", { class: "sr-only" }, "Action")))),
        h("tbody", null, g.rows.map((p) => problemRow(p, isStale))))));
}

function continueCard(p, others, onShowAll) {
  const bits = [p.difficulty, "module " + p.module];
  if (p.seconds > 0) bits.push(fmtDuration(p.seconds) + " so far");
  if (p.touched && fmtDate(p.touched)) bits.push("last active " + fmtDate(p.touched));
  const more = others > 0
    ? h("button", { class: "btn btn-quiet btn-sm", type: "button", onclick: onShowAll },
      others === 1 ? "1 other in progress" : others + " others in progress")
    : null;
  return h("section", { class: "card continue-card", "aria-label": "Pick up where you left off" },
    h("div", { class: "continue-body" },
      h("h2", null, "Pick up where you left off"),
      h("div", { class: "continue-title" }, p.title),
      h("div", { class: "continue-meta" }, statusMark("attempted"), " · " + bits.join(" · "))),
    h("div", { class: "btn-row continue-actions" },
      more,
      h("a", { class: "btn btn-primary", href: "#/practice/" + p.slug,
        onclick: () => noteOpened(p.slug) }, "Continue")));
}

/** A row of single-select chip buttons. Returns {el, update(selected, counts)}. */
function chipGroup(label, options, onPick) {
  const buttons = options.map((o) => {
    const n = h("span", { class: "chip-n" });
    const b = h("button", { class: "chip", type: "button", "aria-pressed": "false",
      dataset: { value: o.value }, onclick: () => onPick(o.value) }, o.text, n);
    if (o.tip) attachTooltip(b, () => ({ value: o.tip, label: n.textContent + " shown with the other filters" }));
    return { b, n, o };
  });
  const el = h("div", { class: "filter-row", role: "group", "aria-label": label },
    h("span", { class: "filter-label", "aria-hidden": "true" }, label),
    h("div", { class: "chips" }, buttons.map((x) => x.b)));
  const update = (selected, counts) => {
    for (const { b, n, o } of buttons) {
      b.setAttribute("aria-pressed", String(o.value === selected));
      const c = counts[o.value] || 0;
      n.textContent = String(c);
      b.classList.toggle("chip-zero", c === 0 && o.value !== selected);
    }
  };
  return { el, update };
}

// ---- page ----------------------------------------------------------------------------

export function render(container, params = {}) {
  document.title = "Practice · LeetCode Prep";
  const ac = new AbortController();
  const isStale = () => ac.signal.aborted || (params.isStale ? params.isStale() : false);
  const head = h("div", { class: "page-head" },
    h("h1", null, "Practice"),
    h("p", { class: "lede" }, "Every problem on the list, by module. Pick one, code it here, and "
      + "submit when it passes the app's tests."));
  const body = h("div", { class: "browse" });
  container.append(head, body);

  const load = async () => {
    clear(body);
    body.append(emptyState("Loading the problem list…"));
    let data;
    try {
      data = await get("/problems", { signal: ac.signal });
    } catch (e) {
      if (isStale() || (e && e.name === "AbortError")) return;
      clear(body);
      body.append(emptyState("Could not load the problem list. " + ((e && e.detail) || "The app's server did not answer."),
        h("button", { class: "btn", type: "button", onclick: load }, "Retry")));
      return;
    }
    if (isStale()) return;
    draw(data || {});
  };

  const draw = (data) => {
    const problems = Array.isArray(data.problems) ? data.problems : [];
    const modules = Array.isArray(data.modules) ? data.modules.filter((m) => m.id !== "00") : [];
    const moduleIds = modules.map((m) => m.id);
    clear(body);
    if (!problems.length) {
      body.append(emptyState("The problem list is empty. It comes from app/data/problems.json; "
        + "check that the file is there and restart the app."));
      return;
    }

    const q = params.query || {};
    const fromHash = ["status", "difficulty", "module"].some((k) => k in q);
    let filters = normalizeFilters(fromHash ? q : readJson(FILTER_KEY), moduleIds);
    // Filters restored from storage go into the hash once, so the URL describes the view.
    // replaceState fires no hashchange, so this does not render the page again.
    const restored = filtersToQuery(filters);
    if (!fromHash && restored && !isStale()) {
      history.replaceState(history.state, "", "#/practice?" + restored);
    }
    const nextUp = nextUpModule(problems, modules);

    const continueSlot = h("div", { class: "continue-slot" });
    const count = h("p", { class: "browse-showing small muted", "aria-live": "polite" });
    const clearBtn = h("button", { class: "btn btn-quiet btn-sm", type: "button" }, "Clear filters");
    const list = h("div", { class: "browse-list" });

    const set = (patch) => {
      filters = { ...filters, ...patch };
      writeJson(FILTER_KEY, filters);
      const qs = filtersToQuery(filters);
      if (!isStale()) history.replaceState(history.state, "", "#/practice" + (qs ? "?" + qs : ""));
      paint();
    };
    clearBtn.addEventListener("click", () => set({ status: "all", difficulty: "all", module: "all" }));

    const statusChips = chipGroup("Status", ["all", ...STATUSES].map((v) => ({ value: v, text: STATUS_WORDS[v] })),
      (v) => set({ status: v }));
    const diffChips = chipGroup("Level", [{ value: "all", text: "All" },
      ...DIFFICULTIES.map((d) => ({ value: d, text: d }))], (v) => set({ difficulty: v }));
    const modChips = chipGroup("Module", [{ value: "all", text: "All" },
      ...modules.map((m) => ({ value: m.id, text: m.id, tip: m.id + " · " + m.title }))], (v) => set({ module: v }));

    const paint = () => {
      const c = facetCounts(problems, filters, moduleIds);
      statusChips.update(filters.status, c.status);
      diffChips.update(filters.difficulty, c.difficulty);
      modChips.update(filters.module, c.module);
      const shown = filterProblems(problems, filters).length;
      count.textContent = "Showing " + shown + " of " + problems.length + " problems";
      clearBtn.hidden = filtersToQuery(filters) === "";
      clear(list);
      const groups = groupByModule(problems, modules, filters);
      if (!groups.length) {
        list.append(h("section", { class: "card" }, emptyState("No problem matches these filters.",
          h("button", { class: "btn", type: "button", onclick: () => set({ status: "all", difficulty: "all", module: "all" }) },
            "Clear filters"))));
        return;
      }
      for (const g of groups) list.append(moduleCard(g, nextUp, isStale));
    };

    body.append(continueSlot,
      h("section", { class: "card browse-filters", "aria-label": "Filters" },
        statusChips.el, diffChips.el, modChips.el,
        h("div", { class: "browse-foot" }, count, clearBtn)),
      list);
    paint();
    fillContinue(problems, continueSlot, () => set({ status: "attempted", difficulty: "all", module: "all" }));
  };

  /** The most recently touched attempted problem, from the list's own last_at: no extra requests. */
  const fillContinue = (problems, slot, onShowAll) => {
    const open = problems.filter((p) => statusOf(p) === "attempted");
    if (!open.length) return;
    const merged = touchTimes(problems, readJson(OPENED_KEY) || {});
    const pick = pickContinue(problems, merged);
    if (!pick || isStale()) return;
    clear(slot);
    slot.append(continueCard({ ...pick, touched: merged[pick.slug] }, open.length - 1, onShowAll));
  };

  load();
  return () => ac.abort();
}
