// DOM helpers, the one HTML sanitiser, formatters and small shared widgets.
// The pure functions (isSafeUrl, fmtDuration, fmtDate, statusLabel) never touch the DOM,
// so node can import this file for the unit tests.

// ---- pure helpers ---------------------------------------------------------

const SAFE_SCHEMES = new Set(["http", "https", "mailto"]);

/** True for http(s)/mailto URLs and for relative or "#" references; false for anything else. */
export function isSafeUrl(url) {
  if (typeof url !== "string") return false;
  // Browsers drop ASCII whitespace and control characters inside a scheme ("java\tscript:"),
  // so the check looks at the URL the way the browser will.
  const squashed = url.replace(/[\u0000- \u007f-\u009f]/g, "");
  const scheme = /^([a-zA-Z][a-zA-Z0-9+.-]*):/.exec(squashed);
  if (!scheme) return true;
  return SAFE_SCHEMES.has(scheme[1].toLowerCase());
}

/** 0 -> "0 min", 20 -> "under 1 min", 540 -> "9 min", 77400 -> "21.5 h". */
export function fmtDuration(seconds) {
  const s = Number(seconds);
  if (!isFinite(s) || s <= 0) return "0 min";
  if (s < 60) return "under 1 min";
  if (s < 3600) return Math.floor(s / 60) + " min";
  const h = Math.round((s / 3600) * 10) / 10;
  return (Number.isInteger(h) ? String(h) : h.toFixed(1)) + " h";
}

/**
 * Keeps the 30 s heartbeat from crediting seconds twice. A page that sends active seconds on its
 * own (the practice page, when the learner leaves it or submits) reports them with took(n); the
 * next beat is shortened by that much. took(-n) gives seconds back when the request that carried
 * them failed. next() returns the seconds the beat should send, 0 to 60 (the server's cap), and
 * carries over what did not fit. skip() is for a beat that is not sent at all.
 */
export function createBeatCredit(windowSeconds) {
  let taken = 0;
  return {
    took(n) {
      if (Number.isInteger(n)) taken += n;
    },
    /** A beat that was not sent (tab hidden or idle): its window is dropped, a debt is kept. */
    skip() {
      if (taken > 0) taken = 0;
    },
    next() {
      const owed = windowSeconds - taken;
      const send = Math.max(0, Math.min(60, owed));
      taken = send - owed;
      return send;
    },
  };
}

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

/** "2024-03-07" or an ISO timestamp -> "7 Mar 2024"; anything unreadable -> "". */
export function fmtDate(iso) {
  if (typeof iso !== "string") return "";
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso);
  if (!m) return "";
  const month = Number(m[2]);
  const day = Number(m[3]);
  if (month < 1 || month > 12 || day < 1 || day > 31) return "";
  return day + " " + MONTHS[month - 1] + " " + m[1];
}

/** JSON from localStorage, or null when it is missing, unreadable or storage is blocked. */
export function readJson(key) {
  try { return JSON.parse(localStorage.getItem(key) || "null"); } catch { return null; }
}

/** JSON into localStorage; does nothing when storage is blocked or full (private mode). */
export function writeJson(key, value) {
  try { localStorage.setItem(key, JSON.stringify(value)); } catch { /* no memory */ }
}

/** API status -> the words the page shows. */
export function statusLabel(status) {
  if (status === "solved") return "solved";
  if (status === "attempted") return "in progress";
  return "not started";
}

// ---- DOM building -----------------------------------------------------------

/**
 * h("a", {href: "#/", class: "x", onclick: fn, dataset: {k: "v"}}, "text", node, [more])
 * Strings become text nodes (never HTML). null/false children are skipped.
 */
export function h(tag, attrs, ...children) {
  const el = document.createElement(tag);
  if (attrs) {
    for (const [key, value] of Object.entries(attrs)) {
      if (value === null || value === undefined || value === false) continue;
      if (key.startsWith("on") && typeof value === "function") {
        el.addEventListener(key.slice(2).toLowerCase(), value);
      } else if (key === "class") {
        el.className = value;
      } else if (key === "dataset") {
        Object.assign(el.dataset, value);
      } else if (key === "style" && typeof value === "object") {
        Object.assign(el.style, value);
      } else if (key === "href" || key === "src") {
        if (isSafeUrl(String(value))) el.setAttribute(key, value);
      } else if (value === true) {
        el.setAttribute(key, "");
      } else {
        el.setAttribute(key, String(value));
      }
    }
  }
  appendChildren(el, children);
  return el;
}

function appendChildren(el, children) {
  for (const child of children) {
    if (child === null || child === undefined || child === false) continue;
    if (Array.isArray(child)) appendChildren(el, child);
    else if (child instanceof Node) el.appendChild(child);
    else el.appendChild(document.createTextNode(String(child)));
  }
}

/** Remove every child of el. */
export function clear(el) {
  while (el.firstChild) el.removeChild(el.firstChild);
  return el;
}

// ---- the sanitiser ------------------------------------------------------------

// Removed together with everything inside them.
const DROP = new Set(["script", "style", "iframe", "object", "embed", "link", "meta", "form",
  "input", "button", "textarea", "select", "option", "frame", "frameset", "noscript", "template",
  "base", "svg", "math", "applet", "audio", "video", "source", "track", "canvas", "dialog",
  "portal", "noembed", "noframes", "xmp", "plaintext", "title", "head"]);

// Kept as they are (attributes still filtered). Anything not listed and not dropped is unwrapped:
// the element goes, its children stay.
const KEEP = new Set(["a", "abbr", "b", "blockquote", "br", "caption", "cite", "code", "col",
  "colgroup", "dd", "del", "details", "dfn", "div", "dl", "dt", "em", "figcaption", "figure",
  "h1", "h2", "h3", "h4", "h5", "h6", "hr", "i", "img", "ins", "kbd", "li", "mark", "ol", "p",
  "pre", "q", "s", "samp", "small", "span", "strike", "strong", "sub", "summary", "sup", "table",
  "tbody", "td", "tfoot", "th", "thead", "tr", "u", "ul", "var", "font"]);

// No id, name or class from the author: id and name clobber document and window properties
// (`<img name="body">` shadows document.body), and class would let a note dress up as app UI.
// Heading ids are added by md.js after sanitising; class survives only as a code language.
const ATTRS = new Set(["href", "src", "alt", "title", "colspan", "rowspan", "align", "start",
  "width", "height", "open", "lang", "dir"]);
const URL_ATTRS = new Set(["href", "src"]);
const LANG_TOKEN = /^language-[a-z0-9+-]+$/;

/**
 * The attribute policy, as a pure function: the value to keep for attribute `name` on element
 * `tag`, or null to drop it. `class` on code and pre keeps only its language-* tokens
 * (lower-cased); everywhere else it goes.
 */
export function allowAttr(tag, name, value) {
  const n = String(name).toLowerCase();
  const v = String(value == null ? "" : value);
  if (n === "class") {
    if (tag !== "code" && tag !== "pre") return null;
    const keep = v.toLowerCase().split(/\s+/).filter((t) => LANG_TOKEN.test(t));
    return keep.length ? keep.join(" ") : null;
  }
  if (!ATTRS.has(n) || n.startsWith("on")) return null;
  if (URL_ATTRS.has(n) && !isSafeUrl(v)) return null;
  return v;
}

/**
 * Parse untrusted HTML into an inert document, keep only safe elements and attributes, and
 * return the result as a DocumentFragment of the live document. Nothing in the input can run:
 * DOMParser never executes scripts or loads resources, and every script-capable element,
 * every on* attribute and every href/src with a scheme other than http, https or mailto is
 * removed before the nodes are adopted.
 *
 * With `{ images: false }` (coach output, matrix evidence) no media element survives either:
 * each img becomes a text node of its alt (nothing without one), and picture, source, video and
 * audio go. This happens in the inert document, because an img adopted into the page fetches
 * its URL at once, and that URL can carry the user's code to a third party.
 */
export function sanitizeHtml(html, { images = true } = {}) {
  const doc = new DOMParser().parseFromString(
    "<!doctype html><html><body>" + String(html == null ? "" : html) + "</body></html>", "text/html");
  cleanChildren(doc.body, { images });
  const frag = document.createDocumentFragment();
  for (const node of Array.from(doc.body.childNodes)) frag.appendChild(document.adoptNode(node));
  return frag;
}

const MEDIA = new Set(["img", "picture", "source", "video", "audio"]);

function cleanChildren(parent, opts) {
  for (const node of Array.from(parent.childNodes)) {
    if (node.nodeType === 3) continue; // text
    if (node.nodeType !== 1) { node.remove(); continue; } // comments, processing instructions
    const tag = node.localName;
    if (!opts.images && MEDIA.has(tag)) {
      if (tag === "picture") {
        // Its img turns into alt text; its source elements go.
        cleanChildren(node, opts);
        node.replaceWith(...Array.from(node.childNodes));
      } else {
        const alt = tag === "img" ? (node.getAttribute("alt") || "") : "";
        if (alt) node.replaceWith(node.ownerDocument.createTextNode(alt));
        else node.remove();
      }
      continue;
    }
    if (DROP.has(tag) || node.namespaceURI !== "http://www.w3.org/1999/xhtml") {
      node.remove();
      continue;
    }
    cleanChildren(node, opts);
    if (!KEEP.has(tag)) {
      node.replaceWith(...Array.from(node.childNodes));
      continue;
    }
    cleanAttributes(node);
  }
}

function cleanAttributes(el) {
  for (const attr of Array.from(el.attributes)) {
    const keep = allowAttr(el.localName, attr.name, attr.value);
    if (keep === null) el.removeAttribute(attr.name);
    else if (keep !== attr.value) el.setAttribute(attr.name, keep);
  }
  if (el.localName === "a" && el.hasAttribute("href")) {
    const href = el.getAttribute("href");
    if (/^(https?:)?\/\//i.test(href.trim())) {
      el.setAttribute("target", "_blank");
      el.setAttribute("rel", "noopener noreferrer");
    }
  }
  if (el.localName === "img") {
    el.setAttribute("loading", "lazy");
    el.setAttribute("referrerpolicy", "no-referrer");
  }
}

// ---- formatters that build DOM ------------------------------------------------

/** A small neutral pill naming the difficulty, with a level mark so it is not colour-coded. */
export function difficultyPill(level) {
  const text = level || "?";
  return h("span", { class: "pill pill-diff", dataset: { level: String(text).toLowerCase() } }, text);
}

/** A status mark: icon plus words, so state is never colour alone. */
export function statusMark(status, extra) {
  const icon = status === "solved" ? "✓" : status === "attempted" ? "◐" : "○";
  return h("span", { class: "status status-" + (status || "new") },
    h("span", { class: "status-icon", "aria-hidden": "true" }, icon),
    " " + statusLabel(status) + (extra ? ", " + extra : ""));
}

// ---- toast, confirm, tooltip ---------------------------------------------------

let toastBox = null;

/** A short message at the bottom of the window that goes away by itself. */
export function toast(text, { kind = "info", ms = 3800 } = {}) {
  if (!toastBox) {
    toastBox = h("div", { class: "toasts", role: "status", "aria-live": "polite" });
    document.body.appendChild(toastBox);
  }
  const item = h("div", { class: "toast toast-" + kind }, text);
  toastBox.appendChild(item);
  setTimeout(() => {
    item.classList.add("toast-out");
    setTimeout(() => item.remove(), 250);
  }, ms);
}

/** A modal yes/no question. Resolves true on the confirm button, false on Cancel or Escape. */
export function confirmDialog(text, { confirm = "Continue", cancel = "Cancel", focus = "confirm" } = {}) {
  return new Promise((resolve) => {
    const dlg = h("dialog", { class: "dialog card" });
    const done = (value) => {
      dlg.close();
      dlg.remove();
      resolve(value);
    };
    const cancelBtn = h("button", { class: "btn", type: "button", onclick: () => done(false) }, cancel);
    const confirmBtn = h("button", { class: "btn btn-primary", type: "button", onclick: () => done(true) }, confirm);
    dlg.append(h("p", { class: "dialog-text" }, text), h("div", { class: "dialog-actions" }, cancelBtn, confirmBtn));
    dlg.addEventListener("cancel", (e) => { e.preventDefault(); done(false); });
    document.body.appendChild(dlg);
    dlg.showModal();
    // `focus: "cancel"` is for dialogs that throw work away: Enter then does the safe thing.
    (focus === "cancel" ? cancelBtn : confirmBtn).focus();
  });
}

let tipEl = null;

function tipBox() {
  if (!tipEl) {
    tipEl = h("div", { class: "tooltip", role: "tooltip", id: "app-tooltip", hidden: true });
    document.body.appendChild(tipEl);
  }
  return tipEl;
}

/**
 * Give `target` a hover and keyboard-focus tooltip. `content()` returns {value, label}:
 * the value is the strong line, the label the quieter one. Text only (textContent).
 */
export function attachTooltip(target, content) {
  const show = () => {
    const { value, label } = content();
    const tip = tipBox();
    clear(tip);
    tip.append(h("strong", null, value));
    if (label) tip.append(h("span", null, label));
    tip.hidden = false;
    const r = target.getBoundingClientRect();
    const t = tip.getBoundingClientRect();
    let left = r.left + r.width / 2 - t.width / 2;
    left = Math.max(8, Math.min(left, window.innerWidth - t.width - 8));
    let top = r.top - t.height - 8;
    if (top < 8) top = r.bottom + 8;
    tip.style.left = Math.round(left + window.scrollX) + "px";
    tip.style.top = Math.round(top + window.scrollY) + "px";
    target.setAttribute("aria-describedby", "app-tooltip");
  };
  const hide = () => {
    if (tipEl) tipEl.hidden = true;
    target.removeAttribute("aria-describedby");
  };
  target.addEventListener("mouseenter", show);
  target.addEventListener("mouseleave", hide);
  target.addEventListener("focus", show);
  target.addEventListener("blur", hide);
}

/** Hide any open tooltip (used on route change). */
export function hideTooltip() {
  if (tipEl) tipEl.hidden = true;
}

/** Text with `backtick` spans turned into <code> elements; everything stays text. */
export function inlineCode(text) {
  return String(text == null ? "" : text).split(/(`[^`\n]+`)/).filter(Boolean)
    .map((part) => /^`[^`]+`$/.test(part) ? h("code", null, part.slice(1, -1)) : part);
}

/** A centred one-line message for empty, loading and error states. */
export function emptyState(text, ...extra) {
  return h("div", { class: "empty" }, h("p", null, text), ...extra);
}

