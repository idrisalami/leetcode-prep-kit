// Lesson widgets: parsers for ```steps and ```compare blocks (pure, no DOM).
// A block that cannot be read throws BlockError; the caller shows the message
// and leaves the original block on the page.

export class BlockError extends Error {
  constructor(message) {
    super(message);
    this.name = "BlockError";
  }
}

// Pointers: any name with a cell index (lo=0, prev=2). mid and ans also colour their cell;
// ans draws no label. A pair from PAIRS greys the cells outside it.
// Rows: name=[a, b] sets a row of items shown under the array, kept until a later step sets it again.
// array=[...] replaces the array's values from that step on. A "_" value is a blank cell.
const PAIRS = [["lo", "hi"], ["l", "r"], ["left", "right"]];
const RANGES = ["closed", "half-open"];
const NAME = /^[A-Za-z_][A-Za-z0-9_]*$/;
const TOKEN = /([^\s=]+)=(\[[^\]]*\]?|\S*)/g;

function header(line) {
  const m = /^(title|array|range):\s*(.*)$/.exec(line);
  return m ? { key: m[1], value: m[2].trim() } : null;
}

function items(where, key, val) {
  if (!val.endsWith("]")) throw new BlockError(`${where}: ${key}=${val} is missing its closing ]`);
  return val.slice(1, -1).split(",").map((x) => x.trim()).filter(Boolean);
}

export function parseSteps(text) {
  let title = "";
  let array = null;
  let range = "closed";
  const raw = [];
  String(text).split("\n").forEach((line, n) => {
    const t = line.trim();
    if (!t) return;
    if (t.startsWith("- ")) { raw.push({ body: t.slice(2), line: n + 1 }); return; }
    const h = header(t);
    if (!h) throw new BlockError(`line ${n + 1}: expected title:, array:, range: or a "- " step, got "${t}"`);
    if (h.key === "title") title = h.value;
    else if (h.key === "array") array = h.value.split(/\s+/).filter(Boolean);
    else if (!RANGES.includes(h.value)) throw new BlockError(`range must be closed or half-open, got "${h.value}"`);
    else range = h.value;
  });
  if (!raw.length) throw new BlockError("the block has no steps (lines starting with \"- \")");
  const rowNames = [];
  let cur = array;
  const held = {};
  const steps = raw.map(({ body }, s) => {
    const where = `step ${s + 1}`;
    const bar = body.indexOf("|");
    if (bar < 0) throw new BlockError(`${where}: put " | " between the pointers and the narration`);
    const head = body.slice(0, bar).trim();
    const ptrs = {};
    let rest = head;
    for (const m of head.matchAll(TOKEN)) {
      rest = rest.replace(m[0], "");
      const [, key, val] = m;
      if (!NAME.test(key)) throw new BlockError(`${where}: "${key}" is not a name (letters, digits, _)`);
      if (val.startsWith("[")) {
        const list = items(where, key, val);
        if (key === "array") { cur = list; continue; }
        if (!rowNames.includes(key)) rowNames.push(key);
        held[key] = list;
        continue;
      }
      if (!/^\d+$/.test(val)) throw new BlockError(`${where}: ${key}=${val} is not a cell index`);
      ptrs[key] = Number(val);
    }
    if (rest.trim()) throw new BlockError(`${where}: "${rest.trim()}" is not key=value`);
    for (const [key, idx] of Object.entries(ptrs)) {
      if (!cur) throw new BlockError(`${where}: ${key}=${idx} needs an array: line to point into`);
      if (idx > cur.length) throw new BlockError(`${where}: ${key}=${idx} is past the end of the array (length ${cur.length})`);
    }
    return { ptrs, text: body.slice(bar + 1).trim(), array: cur, rows: { ...held } };
  });
  if (!(array && array.length) && !rowNames.length && !steps.some((st) => st.array)) {
    throw new BlockError("the block needs an array: line with at least one value, or a row like stack=[...]");
  }
  return { title, array, range, rowNames, steps };
}

export function stepCells(data, k) {
  const { range } = data;
  const step = data.steps[k];
  const array = step.array || data.array || [];
  const ptrs = step.ptrs;
  const n = array.length;
  const ghost = Object.values(ptrs).some((v) => v === n);
  const pair = PAIRS.find(([a, b]) => a in ptrs && b in ptrs);
  const outside = (idx) => {
    if (!pair) return false;
    const lo = ptrs[pair[0]];
    const hi = ptrs[pair[1]];
    return range === "half-open" ? idx < lo || idx >= hi : idx < lo || idx > hi;
  };
  const cells = [];
  for (let idx = 0; idx < n + (ghost ? 1 : 0); idx++) {
    const state = ptrs.ans === idx ? "ans" : ptrs.mid === idx ? "mid" : outside(idx) ? "out" : "in";
    const raw = idx < n ? array[idx] : "";
    cells.push({
      value: raw === "_" ? "" : raw,
      index: idx,
      ghost: idx === n,
      blank: raw === "_",
      state,
      labels: Object.keys(ptrs).filter((key) => key !== "ans" && ptrs[key] === idx),
    });
  }
  return cells;
}

export function parseCompare(text) {
  let title = "";
  const options = [];
  String(text).split("\n").forEach((line, n) => {
    if (!line.trim()) return;
    const t = line.trim();
    if (/^\s/.test(line)) {
      const cur = options[options.length - 1];
      if (!cur) throw new BlockError(`line ${n + 1}: row "${t}" comes before any option:`);
      const sep = t.indexOf(": ");
      if (sep < 0) throw new BlockError(`line ${n + 1}: row "${t}" needs "Label: value"`);
      cur.rows.push({ label: t.slice(0, sep).trim(), value: t.slice(sep + 2).trim() });
      return;
    }
    const m = /^(title|option):\s*(.*)$/.exec(t);
    if (!m) throw new BlockError(`line ${n + 1}: expected title: or option:, got "${t}"`);
    if (m[1] === "title") title = m[2].trim();
    else options.push({ name: m[2].trim(), rows: [] });
  });
  if (options.length < 2) throw new BlockError(`a compare block needs two to four options, found ${options.length}`);
  if (options.length > 4) throw new BlockError(`a compare block takes at most four options, found ${options.length}`);
  const empty = options.find((o) => !o.rows.length);
  if (empty) throw new BlockError(`option "${empty.name}" has no rows`);
  return { title, options };
}

// ---- view helpers (pure) -----------------------------------------------------------------

export function stepView(data, k) {
  const n = data.steps.length;
  return {
    counter: `Step ${k + 1} of ${n}`,
    backDisabled: k <= 0,
    nextDisabled: k >= n - 1,
    narration: data.steps[k].text,
    cells: stepCells(data, k),
    rows: (data.rowNames || []).map((name) => ({ name, items: data.steps[k].rows?.[name] || [] })),
  };
}

export function nextStep(k, delta, n) {
  return Math.min(n - 1, Math.max(0, k + delta));
}

/** Split `code` spans out of a value; an unpaired backtick stays plain text. */
export function inlineSegments(text) {
  const s = String(text);
  const out = [];
  const re = /`([^`]+)`/g;
  let at = 0;
  let m;
  while ((m = re.exec(s))) {
    if (m.index > at) out.push({ code: false, text: s.slice(at, m.index) });
    out.push({ code: true, text: m[1] });
    at = re.lastIndex;
  }
  if (at < s.length || !out.length) out.push({ code: false, text: s.slice(at) });
  return out;
}

// ---- DOM builders ------------------------------------------------------------------------

function el(doc, tag, cls, text) {
  const e = doc.createElement(tag);
  if (cls) e.className = cls;
  if (text != null) e.textContent = text;
  return e;
}

function inline(doc, parent, text) {
  for (const seg of inlineSegments(text)) {
    parent.append(seg.code ? el(doc, "code", null, seg.text) : doc.createTextNode(seg.text));
  }
  return parent;
}

export function buildStepper(data, doc = globalThis.document) {
  const box = el(doc, "div", "widget stepper");
  box.setAttribute("tabindex", "0");
  box.setAttribute("role", "group");
  box.setAttribute("aria-label", data.title ? `Step-through: ${data.title}` : "Step-through");
  if (data.title) box.append(inline(doc, el(doc, "div", "wtitle"), data.title));
  const arr = el(doc, "div", "arr");
  const rows = el(doc, "div", "rows");
  const narr = el(doc, "p", "narr");
  narr.setAttribute("aria-live", "polite");
  const bar = el(doc, "div", "wbar");
  const back = el(doc, "button", "btn btn-sm", "← Back");
  const next = el(doc, "button", "btn btn-primary btn-sm", "Next →");
  back.type = next.type = "button";
  const counter = el(doc, "span", "wcount");
  bar.append(back, next, counter);
  box.append(arr, rows, narr, bar);

  let k = 0;
  const render = () => {
    const v = stepView(data, k);
    arr.replaceChildren(...v.cells.map((c) => {
      const cell = el(doc, "div", `cell ${c.state}` + (c.ghost ? " ghost" : "") + (c.blank ? " blank" : ""));
      cell.append(el(doc, "div", "v", c.value), el(doc, "div", "i", c.ghost ? "" : String(c.index)),
        el(doc, "div", "p", c.labels.join(" ")));
      return cell;
    }));
    arr.hidden = !v.cells.length;
    rows.replaceChildren(...v.rows.map((r) => {
      const row = el(doc, "div", "row");
      const list = el(doc, "div", "items");
      if (r.items.length) list.append(...r.items.map((x) => el(doc, "span", "item", x)));
      else list.append(el(doc, "span", "empty", "empty"));
      row.append(el(doc, "span", "rname", r.name), list);
      return row;
    }));
    rows.hidden = !v.rows.length;
    narr.replaceChildren();
    inline(doc, narr, v.narration);
    counter.textContent = v.counter;
    back.disabled = v.backDisabled;
    next.disabled = v.nextDisabled;
  };
  const go = (delta) => { k = nextStep(k, delta, data.steps.length); render(); };
  back.addEventListener("click", () => go(-1));
  next.addEventListener("click", () => go(1));
  box.addEventListener("keydown", (e) => {
    if (e.key === "ArrowLeft") { e.preventDefault(); go(-1); }
    else if (e.key === "ArrowRight") { e.preventDefault(); go(1); }
  });
  render();
  return box;
}

export function buildCompare(data, doc = globalThis.document) {
  const box = el(doc, "div", "widget compare");
  if (data.title) box.append(inline(doc, el(doc, "div", "wtitle"), data.title));
  const seg = el(doc, "div", "seg");
  seg.setAttribute("role", "group");
  const dl = el(doc, "dl");
  box.append(seg, dl);
  // Rows keep their place across options: the label order comes from the first option,
  // and labels only another option has are appended in the order they first appear.
  const labels = [];
  for (const o of data.options) for (const r of o.rows) if (!labels.includes(r.label)) labels.push(r.label);
  const dds = labels.map((lbl) => {
    const dd = el(doc, "dd");
    dl.append(el(doc, "dt", null, lbl), dd);
    return dd;
  });
  const buttons = data.options.map((o, i) => {
    const b = el(doc, "button", null, o.name);
    b.type = "button";
    b.addEventListener("click", () => show(i));
    seg.append(b);
    return b;
  });
  function show(i) {
    buttons.forEach((b, j) => {
      b.setAttribute("aria-pressed", String(i === j));
      b.className = i === j ? "on" : "";
    });
    const rows = new Map(data.options[i].rows.map((r) => [r.label, r.value]));
    dds.forEach((dd, j) => {
      dd.replaceChildren();
      inline(doc, dd, rows.has(labels[j]) ? rows.get(labels[j]) : "—");
    });
  }
  show(0);
  return box;
}

/** Replace a ```steps / ```compare block with its widget; on a bad block keep it and say so. */
export function widgetFor(code) {
  const pre = code.parentElement;
  const doc = code.ownerDocument;
  const kind = /\blanguage-(steps|compare)\b/.exec(code.className || "");
  if (!pre || !kind) return null;
  try {
    const text = code.textContent;
    const w = kind[1] === "steps" ? buildStepper(parseSteps(text), doc) : buildCompare(parseCompare(text), doc);
    pre.replaceWith(w);
    return w;
  } catch (e) {
    if (!(e instanceof BlockError)) throw e;
    console.warn(`lesson: ${kind[1]} block: ${e.message}`);
    const note = el(doc, "p", "widget-note", "demo could not be read");
    note.title = e.message;
    pre.after(note);
    return null;
  }
}
