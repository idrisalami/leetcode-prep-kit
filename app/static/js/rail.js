// Progress rail: the reader's contents list, plus a dot per section and a local
// "N of M sections read" line. A section counts as read once its last element has
// entered the viewport after a real scroll. Read ids live in prep:read:<path>.
import { h } from "./ui.js";
import { docRoute } from "./md.js";
import { progressLine, countsAsSection, newlySeen, cleanRead, parentSection, railStats, load, store } from "./lesson.js";

const WIDE = 1100;

/** The last element of the section that starts at `h2`: just before the next h2 (and its eyebrow or rule). */
function sectionEnd(h2, next, root) {
  let end = next ? next.previousElementSibling : root.lastElementChild;
  while (end && end !== h2 && (end.classList.contains("eyebrow") || end.localName === "hr")) {
    end = end.previousElementSibling;
  }
  return end || h2;
}

export function buildRail(root, { path, title, drills }) {
  const heads = Array.from(root.querySelectorAll("h2, h3"));
  if (heads.length < 2) return null;
  const key = "prep:read:" + path;
  const kinds = heads.map((hd) => hd.localName);
  const h2s = heads.filter((hd) => hd.localName === "h2");
  const sections = h2s.map((hd, i) => ({
    id: hd.id, counted: countsAsSection(hd.textContent), head: hd,
    end: sectionEnd(hd, h2s[i + 1] || null, root),
  }));
  const read = new Set(cleanRead(load(key, []), sections.map((s) => s.id)));

  const dots = new Map();
  const links = heads.map((hd) => {
    const isH2 = hd.localName === "h2";
    const dot = isH2 ? h("span", { class: "rail-dot", "aria-hidden": "true" }) : null;
    if (dot) dots.set(hd.id, dot);
    return h("a", { href: docRoute(path, hd.id), class: isH2 ? null : "toc-3", dataset: { id: hd.id } },
      dot, hd.textContent.trim());
  });
  const line = h("p", { class: "rail-progress" });
  const fill = h("span");
  // The line and bar live in the summary so they stay pinned while a long contents list scrolls.
  const toc = h("details", { class: "toc rail" },
    h("summary", null, h("span", { class: "toc-title" }, title || "Contents"),
      line, h("div", { class: "rail-bar", "aria-hidden": "true" }, fill)),
    h("nav", { "aria-label": "Contents" }, links));
  toc.open = window.innerWidth >= WIDE;
  toc.firstChild.addEventListener("click", (e) => { if (window.innerWidth >= WIDE) e.preventDefault(); });

  function draw() {
    const on = parentSection(kinds, links.findIndex((a) => a.classList.contains("on")));
    for (const s of sections) {
      const dot = dots.get(s.id);
      dot.classList.toggle("read", s.counted && read.has(s.id));
      dot.classList.toggle("on", on >= 0 && heads[on] === s.head);
    }
    const st = railStats(sections, read);
    line.textContent = progressLine({ read: st.read, total: st.total, drills });
    fill.style.width = st.pct + "%";
  }

  // Nothing counts until the reader has scrolled: a page that loads with its end on screen is not
  // read. A jump to an anchor (`jumped`) only moves the baseline, so the sections it skipped stay unread.
  const y0 = window.scrollY;
  let moved = false;
  let prev = {};
  function onUpdate(jumped = false) {
    const ends = sections.filter((s) => s.counted).map((s) => ({ id: s.id, top: s.end.getBoundingClientRect().top }));
    if (!jumped && !moved && window.scrollY !== y0) moved = true;
    if (moved && !jumped) {
      const fresh = newlySeen(ends, prev, window.innerHeight, read);
      if (fresh.length) {
        fresh.forEach((id) => read.add(id));
        store(key, [...read]);
      }
    }
    prev = Object.fromEntries(ends.map((e) => [e.id, e.top]));
    draw();
  }

  draw();
  return { toc, heads, links, onUpdate };
}
