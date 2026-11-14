// The shell: left nav (built from /api/course), the hash router, the heartbeat and anchor
// scrolling. Pages are ES modules exporting render(container, params) that may return a
// teardown function (or a promise of one); it runs before the next page renders.
//
// Every navigation gets a fresh container, attached inside <main> before render() is called.
// When a newer navigation starts, the old container is removed from the document, so a page
// that is still awaiting can only write into a detached node. params.isStale() turns true at
// that moment; pages check it after each await before touching anything outside their
// container (focus, scrolling, toasts, navigate, document.title, the nav, timers).

import { get, post } from "./api.js";
import { h, clear, hideTooltip, emptyState, createBeatCredit } from "./ui.js";

// ---- routes -------------------------------------------------------------------

const ROUTES = [
  { re: /^\/?$/, page: "home", load: () => import("./home.js"), params: () => ({}) },
  { re: /^\/practice\/?$/, page: "problems", load: () => import("./problems.js"), params: () => ({}) },
  { re: /^\/practice\/([a-z0-9-]+)\/?$/, page: "practice", load: () => import("./practice.js"),
    params: (m) => ({ slug: m[1] }) },
  { re: /^\/review\/?$/, page: "review", load: () => import("./matrix.js"), params: () => ({}) },
  { re: /^\/module\/(\d\d)\/?$/, page: "module", load: () => import("./reader.js"),
    params: (m) => ({ kind: "module", id: m[1] }) },
  { re: /^\/doc\/(.+)$/, page: "doc", load: () => import("./reader.js"),
    params: (m) => ({ kind: "doc", path: m[1] }) },
];

/** "#/module/04?at=the-template" -> {path: "/module/04", query: {at: "the-template"}} */
export function parseHash(hash) {
  let raw = String(hash || "").replace(/^#/, "");
  if (!raw.startsWith("/")) raw = "/" + raw;
  const q = raw.indexOf("?");
  const pathPart = q === -1 ? raw : raw.slice(0, q);
  const query = {};
  if (q !== -1) {
    for (const [k, v] of new URLSearchParams(raw.slice(q + 1))) query[k] = v;
  }
  let path = pathPart;
  try { path = decodeURI(pathPart); } catch (e) { /* keep it raw */ }
  return { path, query };
}

function match(path) {
  for (const r of ROUTES) {
    const m = r.re.exec(path);
    if (m) return { route: r, params: r.params(m) };
  }
  return null;
}

// ---- shell ------------------------------------------------------------------------

const app = document.getElementById("app");
const skip = h("a", { class: "skip", href: "#main" }, "Skip to content");
const nav = h("nav", { class: "nav", id: "nav", "aria-label": "Main" });
const main = h("main", { class: "main", id: "main", tabindex: "-1" });
const menuBtn = h("button", { class: "btn btn-quiet topbar-menu", type: "button", "aria-controls": "nav",
  "aria-expanded": "false", onclick: () => setMenu(!document.body.classList.contains("nav-open")) }, "Menu");
const topbar = h("header", { class: "topbar" },
  h("a", { class: "brand", href: "#/" }, "LeetCode Prep"), menuBtn);

clear(app);
app.append(topbar, nav, main);
document.body.prepend(skip);
// Hash routing owns the fragment, so the skip link focuses <main> itself instead of jumping.
skip.addEventListener("click", (e) => {
  e.preventDefault();
  main.focus({ preventScroll: false });
});

function setMenu(open) {
  const wasOpen = document.body.classList.contains("nav-open");
  document.body.classList.toggle("nav-open", open);
  menuBtn.setAttribute("aria-expanded", String(open));
  // Closing the drawer hands focus back to the Menu button (a route change then moves it on
  // to <main>).
  if (wasOpen && !open && getComputedStyle(menuBtn).display !== "none") menuBtn.focus({ preventScroll: true });
}

let course = null;

const DEFAULT_NOTES = {
  bugs: "my-prep/bugs.md", learnings: "my-prep/learnings.md", plan: "my-prep/plan.md",
};
const REFERENCE = [
  ["Python toolkit", "course/reference/python-toolkit.md"],
  ["Decision rules", "course/reference/decision-rules.md"],
  ["Bug checklist", "course/reference/bug-checklist.md"],
];

function navLink(text, href, key, extra) {
  return h("a", { href, class: "nav-link", dataset: { key }, title: text },
    h("span", { class: "nav-text" }, text), extra || null);
}

function moduleMark(m) {
  if (m.id === "00") {
    return m.read ? h("span", { class: "nav-mark nav-mark-done", title: "Read" }, "✓ read")
      : h("span", { class: "nav-mark", title: "Not read yet" }, "unread");
  }
  return h("span", { class: "nav-mark" + (m.total && m.solved === m.total ? " nav-mark-done" : ""),
    title: m.solved + " of " + m.total + " solved" }, m.solved + "/" + m.total);
}

function drawNav() {
  clear(nav);
  const notePath = (key) => {
    const n = course && (course.notes || []).find((x) => x.key === key);
    return n ? n.path : DEFAULT_NOTES[key];
  };
  const modules = course ? course.modules.slice().sort((a, b) => a.id.localeCompare(b.id)) : [];
  nav.append(
    h("a", { class: "brand nav-brand", href: "#/" }, "LeetCode Prep"),
    navLink("Home", "#/", "home"),
    navLink("Practice", "#/practice", "problems"),
    navLink("Review", "#/review", "review"),
    h("div", { class: "nav-sub" }, "The course"),
    h("div", { class: "nav-modules" },
      modules.length ? modules.map((m) => navLink(m.id + " " + m.title, "#/module/" + m.id, "module:" + m.id,
        moduleMark(m)))
        : courseError ? h("div", { class: "nav-note nav-error", role: "status" },
          "The module list could not be loaded. ",
          h("button", { class: "btn btn-sm", type: "button", onclick: () => refreshNav() }, "Retry"))
        : h("span", { class: "nav-note" }, "Modules 00–10")),
    ...REFERENCE.map(([t, p]) => navLink(t, "#/doc/" + p, "doc:" + p)),
    h("div", { class: "nav-sub" }, "Your notes"),
    navLink("Skills matrix", "#/review", "matrix-alias"),
    navLink("My mistakes", "#/doc/" + notePath("bugs"), "doc:" + notePath("bugs")),
    navLink("Learnings", "#/doc/" + notePath("learnings"), "doc:" + notePath("learnings")),
    navLink("Plan", "#/doc/" + notePath("plan"), "doc:" + notePath("plan")),
  );
  markActive();
}

let activeKey = "";

function markActive() {
  for (const a of nav.querySelectorAll(".nav-link")) {
    const on = a.dataset.key === activeKey;
    a.classList.toggle("on", on);
    if (on) a.setAttribute("aria-current", "page");
    else a.removeAttribute("aria-current");
  }
}

let courseError = null;
let coursePending = null;

/**
 * Refetch /api/course and redraw the nav marks (after a solve or "Mark as read"). Calls made
 * while a fetch is in flight share it. Resolves to the payload, or the last good one (null if
 * none) when the fetch fails; courseLoadError() then says why.
 */
export function refreshNav() {
  if (coursePending) return coursePending;
  coursePending = (async () => {
    try {
      course = await get("/course");
      courseError = null;
    } catch (e) {
      courseError = e;
    }
    coursePending = null;
    drawNav();
    return course;
  })();
  return coursePending;
}

/** The last /api/course payload (or null before it has loaded). */
export function courseData() {
  return course;
}

/** The error from the last failed /api/course fetch, or null after a good one. */
export function courseLoadError() {
  return courseError;
}

// ---- router -----------------------------------------------------------------------

let current = { key: null, teardown: null, token: 0, page: "", box: null };
let initialRender = true;

/** Go to a route. Re-renders even when the hash is already the current one. */
export function navigate(hash) {
  const target = hash.startsWith("#") ? hash : "#" + hash;
  if (location.hash === target) render(true);
  else location.hash = target;
}

/** The current route: {page, path, params, query}. */
function currentRoute() {
  const { path, query } = parseHash(location.hash);
  const m = match(path);
  return { page: m ? m.route.page : "", path, params: m ? m.params : {}, query };
}

/** Scroll to the element with this id (opening a collapsed <details> around it). */
export function scrollToAnchor(id) {
  if (!id) return false;
  // Look inside the page only: a heading slug may equal an id of the shell ("main", "nav").
  const box = current.box || main;
  const el = box.querySelector("#" + CSS.escape(id));
  if (!el) return false;
  for (let p = el.parentElement; p && p !== main; p = p.parentElement) {
    if (p.localName === "details") p.open = true;
  }
  el.scrollIntoView({ block: "start" });
  if (!el.hasAttribute("tabindex")) el.setAttribute("tabindex", "-1");
  el.focus({ preventScroll: true });
  main.dispatchEvent(new CustomEvent("prep:anchor", { detail: { id } }));
  return true;
}

function runTeardown() {
  const t = current.teardown;
  current.teardown = null;
  if (typeof t === "function") {
    try { t(); } catch (e) { console.error(e); }
  }
}

async function render(force) {
  const { path, query } = parseHash(location.hash);
  const m = match(path);
  const key = path;
  const first = initialRender;
  initialRender = false;
  setMenu(false);
  hideTooltip();

  // Only the anchor changed: scroll, keep the page. The problem list is the exception: its
  // filters live in the URL, so a bare #/practice (the nav link) must draw the list again and
  // write the restored filters back into the URL.
  if (!force && m && key === current.key && (query.at || m.route.page !== "problems")) {
    if (query.at) scrollToAnchor(query.at);
    else window.scrollTo(0, 0);
    return;
  }

  runTeardown();
  const token = ++current.token;
  const isStale = () => token !== current.token;
  current.key = key;
  current.page = m ? m.route.page : "";
  // A fresh, attached container per navigation; the superseded one leaves the document.
  if (current.box) current.box.remove();
  clear(main);
  const box = h("div", { class: "page" });
  main.append(box);
  current.box = box;
  const settle = () => {
    // Focus follows the route for keyboard and screen-reader users, except on the first load
    // and when an anchor takes the focus instead.
    if (first || query.at) return;
    main.focus({ preventScroll: true });
  };

  document.body.classList.toggle("full", current.page === "practice");
  activeKey = !m ? "" : m.route.page === "module" ? "module:" + m.params.id
    : m.route.page === "doc" ? "doc:" + m.params.path
    : m.route.page === "practice" ? "problems" : m.route.page;
  markActive();

  main.className = "main page-" + (current.page || "missing");
  window.scrollTo(0, 0);
  if (!m) {
    document.title = "Not found · LeetCode Prep";
    box.append(h("h1", null, "Page not found"),
      emptyState("There is no page at this address.", h("a", { class: "btn", href: "#/" }, "Go to Home")));
    settle();
    return;
  }
  try {
    const mod = await m.route.load();
    if (isStale()) return;
    const teardown = await mod.render(box, Object.assign({}, m.params, { query, isStale }));
    if (isStale()) {
      if (typeof teardown === "function") teardown();
      return;
    }
    current.teardown = teardown || null;
    if (query.at) scrollToAnchor(query.at);
    settle();
  } catch (e) {
    if (isStale()) return;
    console.error(e);
    clear(box);
    document.title = "Something went wrong · LeetCode Prep";
    box.append(h("h1", null, "Something went wrong"),
      emptyState(e && e.detail ? e.detail : "This page could not be loaded.",
        h("button", { class: "btn", type: "button", onclick: () => render(true) }, "Retry")));
    settle();
  }
}

window.addEventListener("hashchange", () => render(false));

// A click on a link to the hash we are already on does not fire hashchange; scroll anyway.
document.addEventListener("click", (e) => {
  const a = e.target.closest && e.target.closest("a[href^='#/']");
  if (!a || e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey) return;
  if (a.getAttribute("href") === location.hash) {
    e.preventDefault();
    const { query } = parseHash(location.hash);
    if (query.at) scrollToAnchor(query.at);
    setMenu(false);
  }
});

document.addEventListener("keydown", (e) => {
  if (e.key !== "Escape") return;
  hideTooltip();
  if (document.body.classList.contains("nav-open")) setMenu(false);
});

// ---- heartbeat ----------------------------------------------------------------------
// Every 30 s while the tab is visible and the user typed, clicked or scrolled in the last
// 2 minutes. On the practice workspace the time is credited to that problem.

const BEAT_MS = 30000;
const IDLE_MS = 120000;
let lastActive = Date.now();
const touch = () => { lastActive = Date.now(); };
for (const ev of ["keydown", "pointerdown", "wheel", "touchstart"]) {
  document.addEventListener(ev, touch, { passive: true, capture: true });
}
document.addEventListener("scroll", touch, { passive: true, capture: true });

/** True when a heartbeat would be sent right now. */
export function isActive() {
  return document.visibilityState === "visible" && Date.now() - lastActive < IDLE_MS;
}

// The practice page sends seconds on its own when the learner leaves it or submits. It reports
// them here, so the next beat does not credit the same seconds again.
const beatCredit = createBeatCredit(BEAT_MS / 1000);

/** Seconds a page sent by itself since the last beat; a negative number gives them back. */
export function tookSeconds(n) {
  beatCredit.took(n);
}

setInterval(() => {
  if (!isActive()) { beatCredit.skip(); return; }
  const r = currentRoute();
  const slug = r.page === "practice" ? r.params.slug : null;
  const seconds = beatCredit.next();
  window.dispatchEvent(new CustomEvent("prep:heartbeat", { detail: { slug, seconds } }));
  if (seconds < 1) return;
  post("/heartbeat", { slug, seconds }).then((res) => {
    // The server says when it could not write the state file; the practice page shows it.
    window.dispatchEvent(new CustomEvent("prep:save-state", { detail: { warning: (res && res.save_error) || null } }));
  }).catch(() => { /* time tracking never interrupts */ });
}, BEAT_MS);

// ---- start ------------------------------------------------------------------------------

drawNav();
refreshNav();
render(true);
