// Lays a problem statement out in parts: the question in a callout, one card per example,
// then the constraints and any closing notes. Statements arrive as one flat run of blocks
// (paragraphs, pre blocks, lists) from two sources with slightly different shapes, so the
// grouping works on the text of the top-level blocks alone.

import { h } from "./ui.js";

const EXAMPLE = /^example\s*(\d*)\s*:?$/i;
const CONSTRAINTS = /^constraints?\s*:?$/i;
const FOLLOW_UP = /^follow[\s-]*up\b/i;
const NOTE = /^note\s*:/i;

// Whitespace of every kind collapses, and the invisible zero-width marks some statements carry go.
const squash = (text) => String(text == null ? "" : text)
  .replace(/[​-‍⁠﻿]/g, "").replace(/[\s ]+/g, " ").trim();

/**
 * Sort the top-level blocks of a statement into its parts. Each item is
 * `{ tag, text, solid }`: the element name, its text, and whether it holds something that
 * is not text (an image, a code block, a table). Returns indexes into `items`:
 * `{ question, examples: [{ title, items }], constraints, after }`. Empty spacer blocks and
 * the headings themselves ("Example 1:", "Constraints:") are left out.
 */
export function groupStatement(items) {
  const out = { question: [], examples: [], constraints: [], after: [] };
  let part = "question";
  (items || []).forEach((item, i) => {
    const text = squash(item && item.text);
    const tag = String((item && item.tag) || "").toLowerCase();
    if (!text && !(item && item.solid)) return; // spacer
    const heading = tag === "p" || tag === "div" || /^h[1-6]$/.test(tag);
    const example = heading ? EXAMPLE.exec(text) : null;
    if (example) {
      out.examples.push({ title: example[1] ? "Example " + example[1] : "Example", items: [] });
      part = "example";
      return;
    }
    if (heading && CONSTRAINTS.test(text)) {
      part = "constraints";
      return;
    }
    // After the examples, a follow-up, a note or a fold-out block closes the statement.
    if (part !== "question" && (FOLLOW_UP.test(text) || NOTE.test(text) || tag === "details")) part = "after";
    if (part === "example") out.examples[out.examples.length - 1].items.push(i);
    else out[part].push(i);
  });
  return out;
}

const LABEL = /(^|\n)([ \t]*)(Input|Output|Explanation)[ \t]*:/g;
const GAP = /\n[ \t]*(?:\n[ \t]*)+(?=(?:Input|Output|Explanation)[ \t]*:)/g;

/**
 * Cut the text of an example into plain runs and the labels that start a line ("Input:",
 * "Output:", "Explanation:"), so every statement shows them the same way whether or not its
 * source marked them bold. Blank lines before a label go. Returns `[{ text } | { label }]`.
 */
export function splitLabels(text) {
  const s = String(text == null ? "" : text).replace(GAP, "\n");
  const out = [];
  let last = 0;
  for (const m of s.matchAll(LABEL)) {
    const start = m.index + m[1].length + m[2].length;
    if (start > last) out.push({ text: s.slice(last, start) });
    out.push({ label: m[3] + ":" });
    last = m.index + m[0].length;
  }
  if (last < s.length) out.push({ text: s.slice(last) });
  return out;
}

function markLabels(body) {
  const walker = document.createTreeWalker(body, NodeFilter.SHOW_TEXT);
  const texts = [];
  while (walker.nextNode()) texts.push(walker.currentNode);
  for (const node of texts) {
    if (node.parentElement && node.parentElement.closest("strong, b")) continue;
    const pieces = splitLabels(node.nodeValue);
    if (!pieces.some((piece) => piece.label)) continue;
    node.replaceWith(...pieces.map((piece) => (piece.label
      ? h("strong", null, piece.label) : document.createTextNode(piece.text))));
  }
}

const INLINE = new Set(["a", "b", "strong", "i", "em", "u", "s", "code", "kbd", "samp", "var", "span", "sub", "sup",
  "small", "mark", "font", "br", "img"]);
const SOLID = "img, picture, video, audio, pre, table, ul, ol";

/**
 * Regroup the children of a rendered statement in place. Returns how many example cards it
 * made, so the caller knows whether the statement already shows its examples.
 */
export function layoutStatement(root) {
  // Loose text and inline elements at the top level join into one paragraph per run, so a
  // sentence written without its own block is not broken up word by word.
  const nodes = [];
  let run = null;
  for (const node of Array.from(root.childNodes)) {
    const inline = node.nodeType === 3 || (node.nodeType === 1 && INLINE.has(node.localName));
    if (!inline) {
      run = null;
      if (node.nodeType === 1) nodes.push(node);
    } else if (run || squash(node.textContent) || node.nodeType === 1) {
      if (!run) nodes.push(run = h("p", null));
      run.appendChild(node);
    }
  }
  const groups = groupStatement(nodes.map((n) => ({
    tag: n.localName,
    text: n.textContent,
    solid: n.matches(SOLID) || !!n.querySelector(SOLID),
  })));
  const pick = (indexes) => indexes.map((i) => nodes[i]);
  const parts = [];
  if (groups.question.length) {
    parts.push(h("section", { class: "stmt-q", "aria-label": "Question" },
      h("div", { class: "stmt-label" }, "Question"), pick(groups.question)));
  }
  if (groups.examples.length) {
    parts.push(h("div", { class: "stmt-examples" }, groups.examples.map((ex) =>
      h("section", { class: "stmt-ex", "aria-label": ex.title },
        h("div", { class: "stmt-label" }, ex.title),
        h("div", { class: "stmt-ex-body" }, pick(ex.items))))));
  }
  if (groups.constraints.length) {
    parts.push(h("section", { class: "stmt-cons", "aria-label": "Constraints" },
      h("div", { class: "stmt-label" }, "Constraints"), pick(groups.constraints)));
  }
  if (groups.after.length) parts.push(h("div", { class: "stmt-after" }, pick(groups.after)));
  root.replaceChildren(...parts);
  root.querySelectorAll(".stmt-ex-body").forEach(markLabels);
  return groups.examples.length;
}
