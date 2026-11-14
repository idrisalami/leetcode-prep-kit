// Markdown -> sanitised DOM: GitHub heading ids, Python highlighting with CodeMirror's runMode,
// and relative .md links routed inside the app. slugify, resolveDocLink, stripToc and
// leetcodeSlug are pure (node imports this file for the tests); the rest needs the browser
// globals `marked` and `CodeMirror` loaded by index.html.

import { sanitizeHtml } from "./ui.js";

// ---- pure helpers ---------------------------------------------------------

/**
 * GitHub's heading-id rule: lowercase; drop everything except letters, digits, marks, spaces,
 * hyphens and underscores; each space becomes a hyphen. With a `seen` Map, a repeat gets
 * -1, -2, ... and never reuses a slug already handed out.
 */
export function slugify(text, seen) {
  const base = String(text == null ? "" : text)
    .toLowerCase()
    .replace(/[^\p{L}\p{M}\p{N}\p{Pc} -]/gu, "")
    .replace(/ /g, "-");
  if (!seen) return base;
  let slug = base;
  while (seen.has(slug)) {
    const n = seen.get(base) + 1;
    seen.set(base, n);
    slug = base + "-" + n;
  }
  seen.set(slug, 0);
  return slug;
}

const MODULE_PATH = /^course\/modules\/(\d\d)-[^/]*\.md$/;
const ROOTS = ["course", "my-prep"];

/** The in-app route for a document path, with an optional heading anchor. */
export function docRoute(path, anchor) {
  const m = MODULE_PATH.exec(path);
  const base = m ? "#/module/" + m[1] : "#/doc/" + path;
  return anchor ? base + "?at=" + encodeURIComponent(anchor) : base;
}

/**
 * Turn a link found in the document at `basePath` into an in-app route, or null when the link
 * is absolute, not Markdown, or would leave course/ and my-prep/.
 */
export function resolveDocLink(href, basePath) {
  if (typeof href !== "string" || !href) return null;
  if (/^[a-zA-Z][a-zA-Z0-9+.-]*:/.test(href) || href.startsWith("//")) return null;
  const hashAt = href.indexOf("#");
  const pathPart = hashAt === -1 ? href : href.slice(0, hashAt);
  let anchor = hashAt === -1 ? "" : href.slice(hashAt + 1);
  try { anchor = decodeURIComponent(anchor); } catch (e) { /* keep it raw */ }
  if (!pathPart) return docRoute(basePath, anchor);
  if (pathPart.includes("?")) return null;
  let target = pathPart;
  try { target = decodeURIComponent(pathPart); } catch (e) { /* keep it raw */ }
  if (!target.toLowerCase().endsWith(".md")) return null;
  const parts = target.startsWith("/") ? [] : basePath.split("/").slice(0, -1);
  for (const seg of target.split("/")) {
    if (seg === "" || seg === ".") continue;
    if (seg === "..") {
      if (!parts.length) return null;
      parts.pop();
    } else {
      parts.push(seg);
    }
  }
  if (parts.length < 2 || !ROOTS.includes(parts[0])) return null;
  return docRoute(parts.join("/"), anchor);
}

/** Remove the file's own `<!-- toc --> ... <!-- /toc -->` block. */
export function stripToc(markdown) {
  return String(markdown).replace(/<!--\s*toc\s*-->[\s\S]*?<!--\s*\/toc\s*-->/i, "");
}

/** "https://leetcode.com/problems/two-sum/..." -> "two-sum"; anything else -> null. */
export function leetcodeSlug(href) {
  const m = /^https?:\/\/(?:www\.)?leetcode\.com\/problems\/([a-z0-9-]+)(?:[/?#]|$)/i.exec(String(href || ""));
  return m ? m[1].toLowerCase() : null;
}

// ---- browser side -------------------------------------------------------------

/** Highlight Python source into `el` with CodeMirror's runMode (plain text if it is missing). */
function highlightPython(code, el) {
  el.textContent = "";
  const CM = window.CodeMirror;
  if (CM && typeof CM.runMode === "function") {
    CM.runMode(code, "python", el);
  } else {
    el.textContent = code;
  }
  el.classList.add("cm-s-prep");
}

/**
 * Render Markdown into a sanitised <div class="md">. Headings get GitHub ids; Python code
 * blocks are highlighted; relative .md links become in-app routes (basePath is the file's own
 * path, e.g. "course/modules/04-binary-search.md"); external links open in a new tab.
 * `images: false` replaces every image with its alt text before it reaches the page (see
 * sanitizeHtml); coach output and matrix evidence use it, documents and statements do not.
 */
export function renderMarkdown(markdown, { basePath = "", images = true } = {}) {
  const html = window.marked.parse(stripToc(markdown), { gfm: true, async: false });
  const root = document.createElement("div");
  root.className = "md";
  root.appendChild(sanitizeHtml(html, { images }));

  // The sanitiser drops every author id, so the slugs below are the only ids in the document.
  const seen = new Map();
  for (const hd of root.querySelectorAll("h1, h2, h3, h4, h5, h6")) {
    hd.id = slugify(hd.textContent.trim(), seen);
  }

  for (const code of root.querySelectorAll("pre > code")) {
    const pre = code.parentElement;
    pre.classList.add("code-block");
    const lang = (/language-([\w-]+)/.exec(code.className) || [])[1] || "";
    if (lang === "python" || lang === "py") highlightPython(code.textContent.replace(/\n$/, ""), code);
  }

  for (const a of root.querySelectorAll("a[href]")) {
    const href = a.getAttribute("href");
    const route = basePath ? resolveDocLink(href, basePath) : null;
    if (route) {
      a.setAttribute("href", route);
      a.removeAttribute("target");
      a.classList.add("doc-link");
    } else if (/^[a-z][a-z0-9+.-]*:|^\/\//i.test(href)) {
      if (!href.toLowerCase().startsWith("mailto:")) {
        a.setAttribute("target", "_blank");
        a.setAttribute("rel", "noopener noreferrer");
      }
    } else {
      // A relative link to something the app cannot show (a .py file, a folder): keep the text.
      const span = document.createElement("span");
      span.className = "dead-link";
      span.title = href;
      while (a.firstChild) span.appendChild(a.firstChild);
      a.replaceWith(span);
    }
  }

  for (const table of root.querySelectorAll("table")) {
    const wrap = document.createElement("div");
    wrap.className = "table-wrap";
    table.replaceWith(wrap);
    wrap.appendChild(table);
  }
  return root;
}
