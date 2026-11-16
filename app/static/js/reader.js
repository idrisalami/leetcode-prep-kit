// The document reader: course modules (#/module/NN) and any other course or my-prep Markdown
// file (#/doc/<path>). Sticky contents list from the headings, self-check answers collapsed,
// "Code it" next to drill-table problems, a "Solve in the app" table, and "Mark as read" on
// module 00.

import { get, post, ApiError } from "./api.js";
import { h, clear, difficultyPill, statusMark, emptyState, toast, fmtDuration } from "./ui.js";
import { redoButton } from "./redo.js";
import { renderMarkdown, leetcodeSlug, docRoute } from "./md.js";
import { refreshNav, courseData, courseLoadError } from "./main.js";
import { enrichLesson } from "./lesson.js";

const WIDE = 1100;

// ---- problem actions ------------------------------------------------------------------

/** The one button for a problem: Start coding, Continue, or Redo (after a confirm). */
function problemButton(p, { small = true, isStale = () => false } = {}) {
  const cls = "btn" + (small ? " btn-sm" : "");
  if (p.status === "solved") return redoButton(p, { attrs: { class: cls }, isStale });
  if (p.status === "attempted") {
    return h("a", { class: cls + " btn-primary", href: "#/practice/" + p.slug }, "Continue");
  }
  return h("a", { class: cls, href: "#/practice/" + p.slug }, "Start coding");
}

/** Status mark and "Code it" after every LeetCode link in a table that the app knows. */
function addDrillTools(root, bySlug) {
  for (const a of root.querySelectorAll("td a[href]")) {
    const p = bySlug.get(leetcodeSlug(a.getAttribute("href")));
    if (!p || a.dataset.tools) continue;
    a.dataset.tools = "1";
    a.closest("td").append(h("div", { class: "drill-tools" },
      statusMark(p.status),
      h("a", { class: "btn btn-sm", href: "#/practice/" + p.slug,
        "aria-label": "Code " + p.title + " in the app" }, "Code it")));
  }
}

/** Problems of this module, in the order the drill tables list them. */
function moduleProblems(root, problems, id) {
  const mine = problems.filter((p) => p.module === id);
  const order = new Map();
  for (const a of root.querySelectorAll("a[href]")) {
    const slug = leetcodeSlug(a.getAttribute("href"));
    if (slug && !order.has(slug)) order.set(slug, order.size);
  }
  const rank = (p) => (order.has(p.slug) ? order.get(p.slug) : 1000 + mine.indexOf(p));
  return mine.slice().sort((a, b) => rank(a) - rank(b));
}

function solveCard(list, isStale) {
  const rows = list.map((p, i) => h("tr", null,
    h("td", { class: "td-id" }, String(i + 1)),
    h("td", null, h("a", { href: "#/practice/" + p.slug }, p.title),
      p.premium ? h("span", { class: "tag" }, "premium") : null),
    h("td", null, difficultyPill(p.difficulty)),
    h("td", null, statusMark(p.status, p.seconds ? fmtDuration(p.seconds) : "")),
    h("td", { class: "td-action" }, problemButton(p, { isStale }))));
  return h("section", { class: "card card-flush solve-card", "aria-label": "Solve in the app" },
    h("div", { class: "card-title" }, "Solve in the app"),
    h("div", { class: "table-wrap" },
      h("table", { class: "table-hover" },
        h("thead", null, h("tr", null, h("th", null, "#"), h("th", null, "Problem"),
          h("th", null, "Level"), h("th", null, "Status"), h("th", null, h("span", { class: "sr-only" }, "Action")))),
        h("tbody", null, rows))));
}

// ---- document shaping ---------------------------------------------------------------------

/** Put everything under "## Self-check answers" (up to the next h1/h2) behind "Show answers". */
function collapseAnswers(root) {
  for (const hd of root.querySelectorAll("h2")) {
    if (!/^self-check answers$/i.test(hd.textContent.trim())) continue;
    const details = h("details", { class: "answers" }, h("summary", null, "Show answers"));
    let n = hd.nextSibling;
    // Stop at the next h1/h2, or at the eyebrow that the lesson pass puts above an h2.
    while (n && !(n.nodeType === 1 && (/^h[12]$/.test(n.localName) || n.classList.contains("eyebrow")))) {
      const next = n.nextSibling;
      details.appendChild(n);
      n = next;
    }
    details.addEventListener("toggle", () => {
      details.firstChild.textContent = details.open ? "Hide answers" : "Show answers";
    });
    hd.after(details);
  }
}

/** The first heading when it is the page title; it moves into the page header. */
function takeTitle(root) {
  const first = root.firstElementChild;
  if (first && first.localName === "h1") {
    first.remove();
    return first.textContent.trim();
  }
  return "";
}

function buildToc(root, path) {
  const heads = Array.from(root.querySelectorAll("h2, h3"));
  if (heads.length < 2) return null;
  const links = heads.map((hd) => h("a", { href: docRoute(path, hd.id),
    class: hd.localName === "h3" ? "toc-3" : null, dataset: { id: hd.id } }, hd.textContent.trim()));
  const toc = h("details", { class: "toc" },
    h("summary", null, h("span", { class: "toc-title" }, "Contents")),
    h("nav", { "aria-label": "Contents" }, links));
  toc.open = window.innerWidth >= WIDE;
  // On wide screens the list is a fixed sidebar, not a collapsible block.
  toc.firstChild.addEventListener("click", (e) => { if (window.innerWidth >= WIDE) e.preventDefault(); });
  return { toc, heads, links };
}

function trackActive({ toc, heads, links }, container) {
  let current = "";
  const set = (id) => {
    if (id === current) return;
    current = id;
    for (const a of links) a.classList.toggle("on", a.dataset.id === id);
    const on = links.find((a) => a.dataset.id === id);
    if (on && window.innerWidth >= WIDE) {
      const tr = toc.getBoundingClientRect();
      const ar = on.getBoundingClientRect();
      if (ar.top < tr.top || ar.bottom > tr.bottom) on.scrollIntoView({ block: "nearest" });
    }
  };
  let queued = false;
  let pinned = null; // the anchor just jumped to wins until the page scrolls on
  const update = () => {
    queued = false;
    if (pinned && Math.abs(window.scrollY - pinned.y) < 4) { set(pinned.id); return; }
    pinned = null;
    let id = heads.length ? heads[0].id : "";
    // At the bottom of the page the last headings can never reach the top: take the last
    // one on screen instead.
    const atBottom = window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 4;
    const line = atBottom ? window.innerHeight - 40 : 90;
    for (const hd of heads) {
      if (hd.getBoundingClientRect().top <= line) id = hd.id;
      else break;
    }
    set(id);
  };
  const onScroll = () => {
    if (!queued) { queued = true; requestAnimationFrame(update); }
  };
  let wasWide = window.innerWidth >= WIDE;
  const onResize = () => {
    const wide = window.innerWidth >= WIDE;
    if (wide !== wasWide) toc.open = wide;
    wasWide = wide;
    onScroll();
  };
  // The shell's <main>, found from the page's own container (never by a global id lookup).
  const main = container.closest("main") || container;
  const onAnchor = (e) => { pinned = { id: e.detail.id, y: window.scrollY }; set(e.detail.id); };
  window.addEventListener("scroll", onScroll, { passive: true });
  window.addEventListener("resize", onResize);
  main.addEventListener("prep:anchor", onAnchor);
  update();
  return () => {
    window.removeEventListener("scroll", onScroll);
    window.removeEventListener("resize", onResize);
    main.removeEventListener("prep:anchor", onAnchor);
  };
}

// ---- pages ----------------------------------------------------------------------------------

/** The course payload, loading it if the shell has not yet. Throws the real error on failure. */
async function loadCourse() {
  let course = courseData();
  if (!course) course = await refreshNav();
  if (!course) {
    const e = courseLoadError();
    throw new ApiError(e ? e.status : 0, e ? e.code : "course",
      "The course list could not be loaded" + (e && e.detail ? ": " + e.detail : "."));
  }
  return course;
}

async function moduleInfo(id) {
  const course = await loadCourse();
  const m = course.modules.find((x) => x.id === id);
  if (!m) throw new ApiError(404, "not_found", "There is no module " + id + ".");
  return m;
}

function readToggle(m, onChange, isStale) {
  const btn = h("button", { class: "btn" + (m.read ? "" : " btn-primary"), type: "button",
    "aria-pressed": String(!!m.read) }, m.read ? "Mark as unread" : "Mark as read");
  btn.addEventListener("click", async () => {
    btn.disabled = true;
    try {
      await post("/module/" + m.id + "/read", { read: !m.read });
      m.read = !m.read;
      if (isStale()) return;
      await refreshNav();
      if (isStale()) return;
      onChange();
    } catch (e) {
      btn.disabled = false;
      if (!isStale()) toast(e.detail || "Could not save that.", { kind: "error" });
    }
  });
  return btn;
}

function findNote(path) {
  return ((courseData() && courseData().notes) || []).find((n) => n.path === path) || null;
}

function missingDoc(container, path, err) {
  clear(container);
  const note = findNote(path);
  if (err && err.status === 403) {
    document.title = "Not available · LeetCode Prep";
    container.append(h("h1", null, "This file is not available"),
      emptyState("The app only opens Markdown files in the course and my-prep folders.",
        h("a", { class: "btn", href: "#/" }, "Go to Home")));
    return;
  }
  const name = note ? note.title : path.split("/").pop();
  document.title = name + " · LeetCode Prep";
  container.append(h("h1", null, name),
    emptyState(path.startsWith("my-prep/")
      ? "This note does not exist yet. It is created in the my-prep folder as you work: "
        + "the diagnostic, the coach and your own edits write it."
      : "There is no file at " + path + ".",
    h("a", { class: "btn", href: "#/" }, "Go to Home")));
}

export async function render(container, params) {
  const isStale = params.isStale || (() => false);
  const isModule = params.kind === "module";
  let mod = null;
  let path = params.path;
  let staleNote = false;
  if (isModule) {
    mod = await moduleInfo(params.id);
    if (isStale()) return null;
    path = mod.path;
  } else if (path.startsWith("my-prep/")) {
    // The course may say a note does not exist yet, but it can have been written since the
    // course loaded (the coach, the diagnostic). Ask for it anyway: a 404 shows the empty state.
    if (!courseData()) await refreshNav();
    if (isStale()) return null;
    const note = findNote(path);
    staleNote = !!(note && note.exists === false);
  }

  let doc;
  let problems;
  try {
    [doc, problems] = await Promise.all([
      get("/doc?path=" + encodeURIComponent(path)),
      get("/problems").then((r) => r.problems || []).catch(() => []),
    ]);
  } catch (e) {
    if (isStale()) return null;
    if (!isModule && e instanceof ApiError && (e.status === 403 || e.status === 404)) {
      missingDoc(container, path, e);
      return null;
    }
    throw e;
  }
  if (isStale()) return null;
  // The note exists after all: refresh the course so the nav and the review notes card agree.
  if (staleNote) refreshNav();

  const bySlug = new Map(problems.map((p) => [p.slug, p]));
  const md = renderMarkdown(doc.markdown || "", { basePath: path });
  const fileTitle = takeTitle(md);
  enrichLesson(md, { path, isModule });
  collapseAnswers(md);
  addDrillTools(md, bySlug);

  const head = h("header", { class: "reader-head" });
  if (isModule) {
    const list = moduleProblems(md, problems, mod.id);
    if (list.length) {
      const card = solveCard(list, isStale);
      const drill = Array.from(md.querySelectorAll("h2")).find((x) => /^drill set/i.test(x.textContent.trim()));
      // The eyebrow above the drill heading, and the divider above that, belong below the table.
      let anchor = drill;
      if (anchor && anchor.previousElementSibling && anchor.previousElementSibling.classList.contains("eyebrow")) {
        anchor = anchor.previousElementSibling;
      }
      if (anchor && anchor.previousElementSibling && anchor.previousElementSibling.localName === "hr") {
        anchor = anchor.previousElementSibling;
      }
      if (anchor) anchor.before(card);
      else md.append(card);
    }
    document.title = mod.id + " " + mod.title + " · LeetCode Prep";
    const drawHead = () => {
      clear(head);
      const solved = list.filter((p) => p.status === "solved").length;
      head.append(h("h1", null, mod.id + " · " + mod.title));
      if (mod.id === "00") {
        head.append(h("p", { class: "lede" }, mod.read ? "✓ Read." : "Read this before module 01."),
          h("div", { class: "btn-row read-toggle" }, readToggle(mod, drawHead, isStale)));
      } else {
        head.append(h("p", { class: "lede" }, solved + " of " + list.length + " solved"));
      }
    };
    drawHead();
  } else {
    const title = fileTitle || doc.title || path;
    document.title = title + " · LeetCode Prep";
    head.append(h("h1", null, title), h("p", { class: "lede small" }, path));
  }

  const article = h("article", { class: "card doc lesson" }, md);
  const toc = buildToc(md, path);
  clear(container);
  container.append(head, toc ? h("div", { class: "reader" }, toc.toc, article) : article);
  return toc ? trackActive(toc, container) : null;
}
