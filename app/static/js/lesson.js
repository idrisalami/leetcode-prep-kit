import { widgetFor } from "./lesson-widgets.js";

// Lesson pages: pure classifiers (callouts, Big-O, reading time, self-check,
// progress) and safe localStorage helpers. The DOM pass builds on these.

const WARN = /^⚠️?/;

export function classifyCallout({ first, text, bold, h2 }) {
  if (WARN.test(text)) {
    if (/^You['’]ll see/.test(bold) && /again/.test(bold)) {
      const mod = /\b(\d{2})\b/.exec(bold);
      return { kind: "pointer", label: "Comes back later" + (mod ? ` in module ${mod[1]}` : "") };
    }
    return { kind: "trap", label: "Heads up" };
  }
  if (first === "em" && /^0\.1\b/.test(h2)) return { kind: "question", label: "The one question" };
  if (first === "em" && /^["“'‘]/.test(text)) return { kind: "say", label: "Say it like this" };
  if (first === "strong") return { kind: "rule", label: "Key idea" };
  return { kind: "plain", label: "" };
}

// The text inside the O( ... ) that opens `s`, or null when `s` is not one
// Big-O expression optionally followed by plain words ("amortised").
function bigOInner(s) {
  const t = String(s).trim();
  if (!t.startsWith("O(")) return null;
  let depth = 0;
  for (let i = 1; i < t.length; i++) {
    if (t[i] === "(") depth++;
    else if (t[i] === ")" && --depth === 0) {
      const rest = t.slice(i + 1);
      return /^(\s+[A-Za-z-]+)*$/.test(rest) ? t.slice(2, i) : null;
    }
  }
  return null;
}

export function bigOClass(code) {
  const inner = bigOInner(code);
  if (inner === null) return null;
  const x = inner.replace(/\s+/g, "");
  if (!x) return null;
  if (x === "1" || /^log(\([A-Za-z]\)|[A-Za-z])$/.test(x)) return "fast";
  if (/[\^²!]/.test(x) || /^[A-Za-z][*·×]?[A-Za-z]$/.test(x)) return "steep";
  return "mid";
}

export function countWords(s) {
  return String(s).split(/\s+/).filter(Boolean).length;
}

export function readingMinutes(proseWords, codeWords) {
  return Math.max(1, Math.ceil((proseWords + codeWords / 2) / 200));
}

export function pairSelfCheck(questions, answers) {
  if (!questions.length || !answers.length || questions.length !== answers.length) return null;
  return questions.map((q, i) => [q, answers[i]]);
}

export function tallyText(results, total) {
  const vals = Object.values(results);
  const got = vals.filter((v) => v === "got").length;
  const missed = vals.filter((v) => v === "missed").length;
  return `${got} of ${total} got` + (missed ? ` · ${missed} missed` : "");
}

/** The questions h2: "0.9 Self-check" on numbered modules, plain "Self-check" on module 00. */
export function isSelfCheckHeading(text) {
  return /^(0\.\d+\s+)?self-check$/i.test(String(text).trim());
}

export function markText(result) {
  return result === "got" ? "✓ got" : result === "missed" ? "✗ missed" : "";
}

/** Stored results, keeping only "got"/"missed" for cards that exist (the list may have shrunk). */
export function cleanResults(raw, count) {
  const out = {};
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) return out;
  for (const [k, v] of Object.entries(raw)) {
    const i = Number(k);
    if (Number.isInteger(i) && i >= 0 && i < count && (v === "got" || v === "missed")) out[i] = v;
  }
  return out;
}

export function recordResult(results, index, value) {
  return { ...results, [index]: value };
}

export function progressLine({ read, total, drills }) {
  return `${read} of ${total} sections read` + (drills ? ` · ${drills.solved}/${drills.count} drills` : "");
}

export function countsAsSection(h2Text) {
  return !/^self-check answers$/i.test(String(h2Text).trim());
}

export function newlyRead(ends, viewportH, read) {
  return ends.filter((e) => !read.has(e.id) && e.top < viewportH).map((e) => e.id);
}

/**
 * newlyRead, minus ends that only got above the viewport by a jump: an end counts when it is on
 * screen now, or was below the fold at the last look (`prev`: id -> top) and the reader scrolled past it.
 */
export function newlySeen(ends, prev, viewportH, read) {
  const top = new Map(ends.map((e) => [e.id, e.top]));
  return newlyRead(ends, viewportH, read).filter((id) => top.get(id) >= 0 || !(id in prev) || prev[id] >= viewportH);
}

/** Stored read ids, minus anything that is not a heading id on the page now. */
export function cleanRead(raw, ids) {
  if (!Array.isArray(raw)) return [];
  const live = new Set(ids);
  return [...new Set(raw.filter((id) => typeof id === "string" && live.has(id)))];
}

/** Index of the h2 at or before link `i` (kinds are "h2"/"h3"), or -1. */
export function parentSection(kinds, i) {
  for (let k = Math.min(i, kinds.length - 1); k >= 0; k--) if (kinds[k] === "h2") return k;
  return -1;
}

/** Read and total over counted sections, and the bar width as a whole percent. */
export function railStats(sections, read) {
  const counted = sections.filter((s) => s.counted);
  const n = counted.filter((s) => read.has(s.id)).length;
  return { read: n, total: counted.length, pct: counted.length ? Math.round((100 * n) / counted.length) : 0 };
}

export function parseStored(raw, fallback) {
  if (raw == null) return fallback;
  try {
    return JSON.parse(raw);
  } catch {
    return fallback;
  }
}

export function load(key, fallback) {
  try {
    return parseStored(globalThis.localStorage.getItem(key), fallback);
  } catch {
    return fallback;
  }
}

export function store(key, value) {
  try {
    globalThis.localStorage.setItem(key, JSON.stringify(value));
  } catch {
    /* storage missing, full or denied: the page still works, it just forgets */
  }
}

// ---- static enrichment helpers (pure) ------------------------------------------------------

/** Split highlighted tokens into lines at "\n"; a token spanning a newline lands on both lines. */
export function splitTokenLines(tokens) {
  const lines = [[]];
  for (const { cls, text } of tokens) {
    text.split("\n").forEach((part, k) => {
      if (k > 0) lines.push([]);
      if (part) lines[lines.length - 1].push({ cls, text: part });
    });
  }
  return lines;
}

/** "bad" or "good" when the line's comment (after "#") carries ✗ or ✓. */
export function lineMark(line) {
  const at = String(line).indexOf("#");
  if (at < 0) return "";
  const comment = line.slice(at);
  return comment.includes("✗") ? "bad" : comment.includes("✓") ? "good" : "";
}

export function eyebrowText(num, minutes) {
  return (num ? `§${num} · ` : "") + `about ${minutes} min`;
}

/** The leading "0.N " of a numbered h2, or null. */
export function splitH2Number(text) {
  const m = /^(0\.\d+)(\s+)(\S[\s\S]*)$/.exec(String(text));
  return m ? { num: m[1], lead: m[1] + m[2], rest: m[3] } : null;
}

/** Tier for a table cell written as plain or bold text: one Big-O, at most one word after it. */
export function cellBadge(text, tags) {
  if (tags.length > 1 || (tags.length === 1 && tags[0] !== "strong")) return null;
  const t = String(text).trim();
  const tier = bigOClass(t);
  if (!tier) return null;
  return countWords(t.slice(t.lastIndexOf(")") + 1)) <= 1 ? tier : null;
}

// ---- the DOM pass ----------------------------------------------------------------------------

const HOW_TO_PLAY = /^How to play this in an interview:?$/;

function el(doc, tag, cls, text) {
  const e = doc.createElement(tag);
  if (cls) e.className = cls;
  if (text != null) e.textContent = text;
  return e;
}

function meaningful(node) {
  return Array.from(node.childNodes).filter((n) => !(n.nodeType === 3 && !n.data.trim()));
}

function label(doc, text) {
  return el(doc, "span", "call-lbl", text);
}

function enrichCallouts(root, doc) {
  let h2 = "";
  for (const node of root.querySelectorAll("h2, blockquote")) {
    if (node.localName === "h2") { h2 = node.textContent.trim(); continue; }
    const p = node.firstElementChild;
    const kids = p ? meaningful(p) : [];
    const lead = kids[0];
    const tag = lead && lead.nodeType === 1 ? lead.localName : "text";
    const first = tag === "em" ? (kids.length === 1 ? "em" : "text") : tag === "strong" ? "strong" : "text";
    const strong = p && p.querySelector("strong");
    const { kind, label: lbl } = classifyCallout({
      first, text: node.textContent.trim(), bold: strong ? strong.textContent.trim() : "", h2,
    });
    node.classList.add("call", `call-${kind}`);
    if (kind === "rule" && tag === "strong") lead.classList.add("big");
    if (lbl) node.prepend(label(doc, lbl));
  }
}

function enrichHowToPlay(root, doc) {
  for (const p of root.querySelectorAll("p")) {
    const lead = meaningful(p)[0];
    if (!lead || lead.nodeType !== 1 || lead.localName !== "strong" || !HOW_TO_PLAY.test(lead.textContent.trim())) continue;
    const box = el(doc, "div", "call call-say");
    p.before(box);
    box.append(label(doc, "Say it like this"), p);
  }
}

function enrichLead(root) {
  for (const h2 of root.querySelectorAll("h2")) {
    const next = h2.nextElementSibling;
    if (next && next.localName === "p") next.classList.add("lead");
  }
}

function sectionMinutes(h2) {
  let prose = 0;
  let code = 0;
  for (let n = h2; n && !(n !== h2 && n.localName === "h2"); n = n.nextElementSibling) {
    const pres = n.localName === "pre" ? [n] : Array.from(n.querySelectorAll("pre"));
    const c = pres.reduce((sum, pre) => sum + countWords(pre.textContent), 0);
    code += c;
    prose += countWords(n.textContent) - c;
  }
  return readingMinutes(prose, code);
}

function enrichEyebrows(root, doc) {
  for (const h2 of root.querySelectorAll("h2")) {
    if (!countsAsSection(h2.textContent)) continue;
    const parts = splitH2Number(h2.textContent);
    const minutes = sectionMinutes(h2);
    const brow = el(doc, "div", "eyebrow");
    if (parts) {
      const t = h2.firstChild;
      if (t && t.nodeType === 3 && t.data.startsWith(parts.lead)) {
        t.data = t.data.slice(parts.lead.length);
        h2.insertBefore(el(doc, "span", "sr-num", parts.lead), t);
      }
      brow.append(el(doc, "span", "eyebrow-num", `§${parts.num}`));
    }
    brow.append(el(doc, "span", "eyebrow-time", eyebrowText(null, minutes)));
    brow.setAttribute("aria-hidden", "true");
    h2.before(brow);
  }
}

function markCodeLines(root, doc) {
  for (const code of root.querySelectorAll("pre > code")) {
    const before = code.textContent;
    if (!/[✗✓]/.test(before)) continue;
    const original = Array.from(code.childNodes);
    if (original.some((n) => n.nodeType === 1 && n.children.length)) continue; // nested markup: leave it
    const tokens = original.map((n) => ({ cls: n.nodeType === 1 ? n.className : null, text: n.textContent }));
    const lines = splitTokenLines(tokens);
    const rebuilt = lines.map((line, i) => {
      const mark = lineMark(line.map((t) => t.text).join(""));
      const span = el(doc, "span", "code-line" + (mark ? ` ${mark}` : ""));
      for (const t of line) span.append(t.cls ? el(doc, "span", t.cls, t.text) : doc.createTextNode(t.text));
      if (i < lines.length - 1) span.append(doc.createTextNode("\n"));
      return span;
    });
    code.replaceChildren(...rebuilt);
    if (code.textContent !== before) {
      code.replaceChildren(...original);
      console.warn("lesson: code-line split changed the text; left the block as it was");
    }
  }
}

function enrichBadges(root) {
  for (const code of root.querySelectorAll("td code")) {
    const c = bigOClass(code.textContent);
    if (c) code.classList.add("bigo", `bigo-${c}`);
  }
  for (const td of root.querySelectorAll("td")) {
    const tags = Array.from(td.children).map((n) => n.localName);
    const tier = cellBadge(td.textContent, tags);
    if (!tier) continue;
    const pill = el(td.ownerDocument, "span", `bigo bigo-${tier}`);
    pill.append(...td.childNodes);
    td.replaceChildren(pill);
  }
}

const ANSWERS_H2 = /^self-check answers$/i;

/** The first <ol> directly under the h2 whose text passes `test`, before the next h2. */
function sectionList(root, test) {
  for (const h2 of root.querySelectorAll("h2")) {
    if (!test(h2.textContent)) continue;
    for (let n = h2.nextElementSibling; n && n.localName !== "h2"; n = n.nextElementSibling) {
      if (n.localName === "ol") return { found: true, ol: n };
    }
    return { found: true, ol: null };
  }
  return { found: false, ol: null };
}

function items(ol) {
  return ol ? Array.from(ol.children).filter((n) => n.localName === "li") : [];
}

function cloneKids(doc, from, into) {
  for (const n of Array.from(from.childNodes)) into.append(n.cloneNode(true));
  return into;
}

/**
 * One self-check card, closed. Event wiring stays with the caller.
 * The card is plain content, so a screen reader reads both the question and the answer; each face
 * carries a real toggle button, which keeps "Got it" / "Missed it" out of any other button.
 */
export function buildFlipCard(doc, question, answer, n) {
  const card = el(doc, "div", "flip");
  const toggle = (text) => {
    const b = el(doc, "button", "link flip-toggle", text);
    b.type = "button";
    b.setAttribute("aria-expanded", "false");
    return b;
  };
  const show = toggle("Show answer");
  const hide = toggle("Show question");
  const inner = el(doc, "div", "flip-in");
  const front = el(doc, "div", "flip-f");
  const head = el(doc, "div", "flip-head");
  const mark = el(doc, "span", "flip-mark");
  head.append(el(doc, "span", "flip-num", `Q${n}`), mark);
  front.append(head, cloneKids(doc, question, el(doc, "div", "flip-body")), show);
  const back = el(doc, "div", "flip-b");
  const acts = el(doc, "div", "flip-acts");
  const got = el(doc, "button", "btn btn-sm flip-got", "Got it");
  const missed = el(doc, "button", "btn btn-sm flip-missed", "Missed it");
  got.type = missed.type = "button";
  acts.append(got, missed, hide);
  const answerBody = cloneKids(doc, answer, el(doc, "div", "flip-body"));
  back.append(el(doc, "div", "flip-head", `Answer ${n}`), answerBody, acts);
  back.setAttribute("aria-hidden", "true");
  back.inert = true;
  inner.append(front, back);
  card.append(inner);
  return { card, front, back, toggles: [show, hide], mark, got, missed, answerText: answerBody.textContent };
}

/** What the live region says when a card flips: the answer itself when it opens. */
export function flipAnnouncement(open, n, answerText = "") {
  return open ? `Answer ${n}: ${String(answerText).replace(/\s+/g, " ").trim()}` : `Question ${n}`;
}

function enrichSelfCheck(root, doc, path) {
  const q = sectionList(root, isSelfCheckHeading);
  const a = sectionList(root, (t) => ANSWERS_H2.test(String(t).trim()));
  if (!q.found && !a.found) return; // no self-check on this page at all
  const qs = items(q.ol);
  const as = items(a.ol);
  const pairs = pairSelfCheck(qs, as);
  if (!pairs) {
    console.warn(`self-check: ${qs.length} questions, ${as.length} answers`);
    return;
  }
  const key = "prep:selfcheck:" + path;
  let results = cleanResults(load(key, {}), pairs.length);
  const start = Number(q.ol.getAttribute("start")) || 1;

  const grid = el(doc, "div", "flip-grid");
  const tally = el(doc, "div", "flip-tally");
  const tallyLine = el(doc, "span", "flip-tally-text");
  const reset = el(doc, "button", "link", "Reset");
  reset.type = "button";
  tally.append(tallyLine, reset);
  const live = el(doc, "div", "sr-only");
  live.setAttribute("aria-live", "polite");
  grid.append(tally);

  const cards = pairs.map(([qi, ai], i) => {
    const { card, front, back, toggles, mark, got, missed, answerText } = buildFlipCard(doc, qi, ai, start + i);

    // `focus` moves focus to the toggle on the face now showing, so a keyboard user never sits on a hidden face.
    const setOpen = (open, focus = false) => {
      card.classList.toggle("open", open);
      back.setAttribute("aria-hidden", String(!open));
      back.inert = !open;
      front.setAttribute("aria-hidden", String(open));
      front.inert = open;
      toggles.forEach((b) => b.setAttribute("aria-expanded", String(open)));
      live.textContent = flipAnnouncement(open, start + i, answerText);
      if (focus) toggles[open ? 1 : 0].focus();
    };
    card.addEventListener("click", (e) => {
      if (e.target.closest("a, button")) return;
      setOpen(!card.classList.contains("open"));
    });
    toggles.forEach((b) => b.addEventListener("click", () => setOpen(!card.classList.contains("open"), true)));
    const record = (value) => (e) => {
      e.stopPropagation();
      results = recordResult(results, i, value);
      store(key, results);
      draw();
      setOpen(false, true);
    };
    got.addEventListener("click", record("got"));
    missed.addEventListener("click", record("missed"));
    grid.append(card);
    return { card, mark, got, missed };
  });

  function draw() {
    tallyLine.textContent = tallyText(results, pairs.length);
    reset.hidden = !Object.keys(results).length;
    cards.forEach(({ card, mark, got, missed }, i) => {
      const r = results[i];
      mark.textContent = markText(r);
      mark.className = "flip-mark" + (r ? ` ${r}` : "");
      card.dataset.result = r || "";
      got.setAttribute("aria-pressed", String(r === "got"));
      missed.setAttribute("aria-pressed", String(r === "missed"));
    });
  }
  reset.addEventListener("click", () => {
    results = {};
    store(key, results);
    draw();
  });
  grid.append(live);
  draw();
  q.ol.replaceWith(grid);
}

/** Post-process a rendered lesson in place. Each rule is isolated: a failure warns and the page keeps going. */
export function enrichLesson(root, { path = "", isModule = false } = {}) {
  const doc = root.ownerDocument;
  const rules = [
    ["widgets", () => {
      for (const code of root.querySelectorAll("pre > code.language-steps, pre > code.language-compare")) widgetFor(code);
    }],
    ["self-check", () => { if (isModule) enrichSelfCheck(root, doc, path); }],
    ["callouts", () => enrichCallouts(root, doc)],
    ["how to play", () => enrichHowToPlay(root, doc)],
    ["lead", () => enrichLead(root)],
    ["eyebrows", () => enrichEyebrows(root, doc)],
    ["code lines", () => markCodeLines(root, doc)],
    ["badges", () => enrichBadges(root)],
  ];
  for (const [name, run] of rules) {
    try {
      run();
    } catch (e) {
      console.warn(`lesson: ${name} skipped for ${path || "this page"} (module: ${isModule})`, e);
    }
  }
}
