// Skills matrix page (spec §7.6, §7.7; route #/review): the skills matrix as a table with Topics / Habits /
// Communication chips, a weakest-first sort, the latest evidence for each row, and a Practise
// button that opens the next problem for that row. Links to the learner's notes sit on top.
//
// Same contract as the problem browser: render returns its teardown at once, loads in the
// background and stops painting once params.isStale() turns true. View state lives in the hash
// query (replaceState) with localStorage as the fallback. main.js is imported lazily so the pure
// helpers can be imported by node --test.

import { get } from "./api.js";
import {
  h, clear, fmtDate, statusLabel, attachTooltip, inlineCode, emptyState, readJson, writeJson,
} from "./ui.js";
import { renderMarkdown, docRoute } from "./md.js";

const VIEW_KEY = "prep.review.view";
const MATRIX_PATH = "my-prep/skills-matrix.md";
const SECTIONS = ["topics", "habits", "communication"];
const SECTION_WORDS = { topics: "Topics", habits: "Habits", communication: "Communication" };
const REVISIT_DAYS = 14;
const NO_PROBLEM = "No problem on the app's list trains this row yet; ask the coach for a drill that does.";

// ---- pure helpers (tested in tests/matrix-review.test.mjs) ------------------------------

/** "0".."3" (bold or code marks allowed) -> the number; anything else -> null. */
export function parseLevel(v) {
  if (v == null) return null;
  const s = String(v).replace(/[*`_]/g, "").trim();
  return /^[0-3]$/.test(s) ? Number(s) : null;
}

/** A Now value -> three segments and a text label, so the level is never shown by fill alone. */
export function levelBar(now) {
  const level = parseLevel(now);
  if (level === null) {
    const raw = now == null ? "" : String(now).trim();
    const untested = raw === "" || raw === "?";
    return { level: null, known: false, filled: [false, false, false], text: "?",
      label: untested ? "not tested yet" : "not a level the app can read: " + raw };
  }
  return { level, known: true, filled: [0, 1, 2].map((i) => i < level), text: String(level),
    label: "level " + level + " of 3" };
}

/** Row id letter -> chip: A topics, B habits, C communication, anything else "other". */
export function sectionOf(row) {
  const c = String((row && row.id) || "").trim().charAt(0).toUpperCase();
  return c === "A" ? "topics" : c === "B" ? "habits" : c === "C" ? "communication" : "other";
}

/** Groups -> one list in file order, each row carrying its group title and file index. */
export function flattenRows(groups) {
  const out = [];
  for (const g of groups || []) {
    for (const r of (g && g.rows) || []) out.push({ ...r, group: g.title || "", index: out.length });
  }
  return out;
}

/** Rows for one chip. Rows with an unknown letter show under Topics, so nothing is hidden. */
export function filterSection(rows, section) {
  return rows.filter((r) => {
    const s = sectionOf(r);
    return s === section || (section === "topics" && s === "other");
  });
}

export function sectionCounts(rows) {
  const out = { topics: 0, habits: 0, communication: 0, other: 0 };
  for (const r of rows) out[sectionOf(r)]++;
  return out;
}

/** P0 < P1 < P2 < any other wording ("set at discovery" and the like). */
export function priorityRank(p) {
  const m = /^p([0-2])$/i.exec(String(p == null ? "" : p).trim());
  return m ? Number(m[1]) : 3;
}

/**
 * "file": file order. "weakest": lowest known level first, then priority, then file order;
 * rows with no readable level go last. Returns a new array; the sort is stable.
 */
export function sortRows(rows, mode) {
  const out = rows.slice();
  if (mode !== "weakest") return out.sort((a, b) => a.index - b.index);
  const lvl = (r) => { const v = parseLevel(r.now); return v === null ? 4 : v; };
  return out.sort((a, b) => (lvl(a) - lvl(b)) || (priorityRank(a.priority) - priorityRank(b.priority))
    || (a.index - b.index));
}

/** What the Practise button opens: {slug, title, status, kind}, or {slug: null, kind: "none"}. */
export function practiseTarget(row, bySlug) {
  const slug = row && row.practise;
  if (!slug) return { slug: null, kind: "none" };
  const p = (bySlug && bySlug.get(slug)) || { slug, title: slug, status: "new" };
  const status = ["new", "attempted", "solved"].includes(p.status) ? p.status : "new";
  const kind = status === "solved" ? "oldest" : status === "attempted" ? "continue" : "next";
  return { slug, title: p.title || slug, status, kind };
}

function dayNumber(s) {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(s || "").trim());
  return m ? Date.UTC(Number(m[1]), Number(m[2]) - 1, Number(m[3])) / 86400000 : null;
}

/** A Last tested date -> {days, text, due}; null for no date, a placeholder or a future date. */
export function evidenceAge(date, today) {
  const a = dayNumber(date);
  const b = dayNumber(today);
  if (a === null || b === null || a > b) return null;
  const days = Math.round(b - a);
  const text = days === 0 ? "today" : days === 1 ? "yesterday" : days + " days ago";
  return { days, text, due: days >= REVISIT_DAYS };
}

export function allUnknown(rows) {
  return rows.every((r) => parseLevel(r.now) === null);
}

/** Query or stored values -> {section, sort}. */
export function normalizeView(raw) {
  const r = raw && typeof raw === "object" ? raw : {};
  return { section: SECTIONS.includes(r.view) ? r.view : "topics",
    sort: r.sort === "weakest" ? "weakest" : "file" };
}

export function viewToQuery(v) {
  const parts = [];
  if (v.section !== "topics") parts.push("view=" + v.section);
  if (v.sort !== "file") parts.push("sort=" + v.sort);
  return parts.join("&");
}

// ---- storage and dates ---------------------------------------------------------------

function localToday() {
  const d = new Date();
  const pad = (n) => String(n).padStart(2, "0");
  return d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate());
}

// ---- DOM pieces ----------------------------------------------------------------------

function levelCell(now, { bar = true } = {}) {
  const b = levelBar(now);
  return h("span", { class: "mx-level" + (b.known ? "" : " is-unknown") },
    bar ? h("span", { class: "lvl", "aria-hidden": "true" }, b.filled.map((f) => h("i", { class: f ? "f" : null }))) : null,
    h("span", { class: "mx-level-n", "aria-hidden": "true" }, b.text),
    h("span", { class: "sr-only" }, b.label));
}

function priorityCell(p) {
  const s = String(p == null ? "" : p).trim();
  if (priorityRank(s) < 3) return h("span", { class: "pill mx-prio", dataset: { rank: String(priorityRank(s)) } }, s.toUpperCase());
  return h("span", { class: "small muted" }, s || "–");
}

function evidenceCell(r, today) {
  const text = String(r.evidence || "").trim();
  const age = evidenceAge(r.last_tested, today);
  const cell = h("div", { class: "mx-ev" });
  if (!text) {
    cell.append(h("span", { class: "muted" }, "Not tested yet"));
  } else {
    const body = h("div", { class: "mx-ev-text" }, renderMarkdown(text, { basePath: MATRIX_PATH, images: false }));
    const more = h("button", { class: "btn btn-quiet btn-sm mx-ev-more", type: "button", hidden: true,
      "aria-expanded": "false" }, "Show all");
    more.addEventListener("click", () => {
      const open = body.classList.toggle("is-open");
      more.setAttribute("aria-expanded", String(open));
      more.textContent = open ? "Show less" : "Show all";
    });
    cell.append(body, more);
  }
  if (age) {
    cell.append(h("div", { class: "mx-age small" },
      h("span", null, "tested " + age.text),
      age.due ? h("span", { class: "mx-due" }, h("span", { "aria-hidden": "true" }, "↻ "), "due for a revisit") : null));
  } else if (fmtDate(r.last_tested)) {
    cell.append(h("div", { class: "mx-age small" }, "tested " + fmtDate(r.last_tested)));
  }
  return cell;
}

function practiseCell(r, bySlug, today) {
  const t = practiseTarget(r, bySlug);
  if (t.kind === "none") {
    const b = h("button", { class: "btn btn-sm", type: "button", "aria-disabled": "true",
      "aria-label": "Practise " + r.id + ". " + NO_PROBLEM }, "Practise");
    b.addEventListener("click", (e) => e.preventDefault());
    attachTooltip(b, () => ({ value: "Nothing to open here", label: NO_PROBLEM }));
    return h("div", { class: "mx-practise" }, b);
  }
  const lvl = parseLevel(r.now);
  const age = evidenceAge(r.last_tested, today);
  const strong = (lvl !== null && lvl <= 1) || (age && age.due);
  const why = t.kind === "next" ? "next problem for this row, not started"
    : t.kind === "continue" ? "in progress" : "solved; the one you solved longest ago";
  const a = h("a", { class: "btn btn-sm" + (strong ? " btn-primary" : ""), href: "#/practice/" + t.slug,
    "aria-label": "Practise " + r.id + ": " + t.title + ", " + statusLabel(t.status) }, "Practise");
  attachTooltip(a, () => ({ value: t.title, label: why }));
  return h("div", { class: "mx-practise" }, a);
}

function matrixRow(r, bySlug, today) {
  return h("tr", { dataset: { id: r.id } },
    h("td", { class: "td-id" }, r.id),
    h("td", { class: "mx-skill" }, inlineCode(r.requirement)),
    h("td", null, priorityCell(r.priority)),
    h("td", { class: "mx-start" }, levelCell(r.start, { bar: false })),
    h("td", null, levelCell(r.now)),
    h("td", null, evidenceCell(r, today)),
    h("td", { class: "td-action" }, practiseCell(r, bySlug, today)));
}

/** Show the "Show all" toggle only on evidence that is clamped. */
function markOverflow(root) {
  for (const body of root.querySelectorAll(".mx-ev-text")) {
    const more = body.nextElementSibling;
    if (more && body.scrollHeight > body.clientHeight + 2) more.hidden = false;
  }
}

async function notesCard(signal, isStale) {
  let notes = [];
  try {
    const { courseData } = await import("./main.js");
    const c = courseData() || await get("/course", { signal });
    notes = (c && c.notes) || [];
  } catch {
    notes = [];
  }
  if (isStale()) return null;
  const want = [
    ["skills-matrix", "Skills matrix file", "The file behind this page: one row per skill."],
    ["bugs", "My mistakes", "The mistakes you make more than once."],
    ["learnings", "Learnings", "One entry per insight from a problem, newest first."],
    ["plan", "Plan", "Your schedule from today to the interview."],
    ["next-session", "Next session", "Where you stopped and what comes next."],
    ["diagnostic-report", "Diagnostic report", "One block per diagnostic problem, with your code."],
  ];
  const optional = new Set(["next-session", "diagnostic-report"]);
  const items = [];
  for (const [key, label, about] of want) {
    const n = notes.find((x) => x.key === key);
    if (!n && optional.has(key)) continue;
    if (n && !n.exists && optional.has(key)) continue;
    const path = (n && n.path) || "my-prep/" + key + ".md";
    // A note still holding its untouched template opens like any other; the mark says why it is empty.
    const mark = n && !n.exists ? "Not created yet" : n && n.is_template ? "Empty" : null;
    items.push(h("li", null, h("a", { class: "note-tile", href: docRoute(path) },
      h("span", { class: "note-tile-head" },
        h("span", { class: "note-tile-name" }, label),
        mark ? h("span", { class: "note-tile-mark" }, mark) : null,
        h("span", { class: "note-tile-go", "aria-hidden": "true" }, "→")),
      h("span", { class: "note-tile-desc" }, about))));
  }
  return h("section", { class: "card review-notes", "aria-label": "Your notes" },
    h("h2", null, "Your notes"), h("ul", { class: "review-links", dataset: { n: String(items.length) } }, items));
}

// ---- page ----------------------------------------------------------------------------

export function render(container, params = {}) {
  document.title = "Skills matrix · LeetCode Prep";
  const ac = new AbortController();
  const isStale = () => ac.signal.aborted || (params.isStale ? params.isStale() : false);
  const head = h("div", { class: "page-head" },
    h("h1", null, "Skills matrix"),
    h("p", { class: "lede" }, "Where you started, where you are now, and what the proof is. "
      + "Levels go from 0 to 3."));
  const notesSlot = h("div", { class: "review-notes-slot" });
  const body = h("div", { class: "review" });
  container.append(head, notesSlot, body);

  notesCard(ac.signal, isStale).then((card) => { if (card && !isStale()) notesSlot.append(card); });

  const load = async () => {
    clear(body);
    body.append(emptyState("Loading the skills matrix…"));
    let matrix;
    let list;
    try {
      [matrix, list] = await Promise.all([get("/matrix", { signal: ac.signal }), get("/problems", { signal: ac.signal })]);
    } catch (e) {
      if (isStale() || (e && e.name === "AbortError")) return;
      clear(body);
      body.append(emptyState("Could not load the skills matrix. " + ((e && e.detail) || "The app's server did not answer."),
        h("button", { class: "btn", type: "button", onclick: load }, "Retry")));
      return;
    }
    if (isStale()) return;
    draw(matrix || {}, list || {});
  };

  const draw = (matrix, list) => {
    clear(body);
    const rows = flattenRows(matrix.groups);
    if (!rows.length) {
      body.append(h("section", { class: "card" }, emptyState(
        "There is no skills matrix to show. The file my-prep/skills-matrix.md is missing or has no rows. "
        + "The app copies a fresh one from course/templates/ when it starts, so restarting the app brings it back.")));
      return;
    }
    const bySlug = new Map(((list && list.problems) || []).map((p) => [p.slug, p]));
    const today = localToday();
    const q = params.query || {};
    const fromHash = "view" in q || "sort" in q;
    let view = normalizeView(fromHash ? q : readJson(VIEW_KEY));
    // A view restored from storage goes into the hash once; replaceState does not render again.
    const restored = viewToQuery(view);
    if (!fromHash && restored && !isStale()) history.replaceState(history.state, "", "#/review?" + restored);
    const counts = sectionCounts(rows);
    counts.topics += counts.other;

    const set = (patch) => {
      view = { ...view, ...patch };
      writeJson(VIEW_KEY, { view: view.section, sort: view.sort });
      const qs = viewToQuery(view);
      if (!isStale()) history.replaceState(history.state, "", "#/review" + (qs ? "?" + qs : ""));
      paint();
    };

    const chips = SECTIONS.map((s) => h("button", { class: "chip", type: "button", "aria-pressed": "false",
      dataset: { value: s }, onclick: () => set({ section: s }) },
      SECTION_WORDS[s], h("span", { class: "chip-n" }, String(counts[s]))));
    const sortBtn = h("button", { class: "chip mx-sort", type: "button", "aria-pressed": "false",
      onclick: () => set({ sort: view.sort === "weakest" ? "file" : "weakest" }) },
      h("span", { "aria-hidden": "true" }, "↑ "), "Weakest first");

    const notice = allUnknown(rows)
      ? h("p", { class: "notice" }, "Every level is still unknown (?). They fill in after the diagnostic, "
        + "or row by row as you submit problems.")
      : null;

    const tableBody = h("tbody");
    const tableCard = h("section", { class: "card card-flush mx-card", "aria-label": "Skills matrix" },
      h("div", { class: "table-wrap" },
        h("table", { class: "mx-table" },
          h("thead", null, h("tr", null,
            h("th", { class: "td-id" }, "#"), h("th", null, "Skill"), h("th", null, "Priority"),
            h("th", null, "Start"), h("th", null, "Now"), h("th", null, "Latest evidence"),
            h("th", null, h("span", { class: "sr-only" }, "Practise")))),
          tableBody)));

    const paint = () => {
      for (const c of chips) c.setAttribute("aria-pressed", String(c.dataset.value === view.section));
      sortBtn.setAttribute("aria-pressed", String(view.sort === "weakest"));
      clear(tableBody);
      const shown = sortRows(filterSection(rows, view.section), view.sort);
      if (!shown.length) {
        tableBody.append(h("tr", null, h("td", { colspan: "7" },
          emptyState("No rows in this part of the matrix."))));
        return;
      }
      const titles = new Set(shown.map((r) => r.group));
      let last = null;
      for (const r of shown) {
        if (view.sort === "file" && titles.size > 1 && r.group !== last) {
          tableBody.append(h("tr", { class: "mx-sub" }, h("th", { colspan: "7", scope: "colgroup" }, r.group)));
        }
        last = r.group;
        tableBody.append(matrixRow(r, bySlug, today));
      }
      requestAnimationFrame(() => { if (!isStale()) markOverflow(tableBody); });
    };

    body.append(
      h("div", { class: "mx-toolbar" },
        h("div", { class: "chips", role: "group", "aria-label": "Part of the matrix" }, chips),
        sortBtn),
      ...[notice, tableCard].filter(Boolean));
    paint();
  };

  load();
  return () => ac.abort();
}
