// Lesson widgets: parsers for ```steps and ```compare blocks (pure, no DOM).
// A block that cannot be read throws BlockError; the caller shows the message
// and leaves the original block on the page.

export class BlockError extends Error {
  constructor(message) {
    super(message);
    this.name = "BlockError";
  }
}

export const POINTER_KEYS = ["lo", "hi", "l", "r", "i", "j", "left", "right", "mid", "ans"];
const PAIRS = [["lo", "hi"], ["l", "r"], ["left", "right"]];
const RANGES = ["closed", "half-open"];

function header(line) {
  const m = /^(title|array|range):\s*(.*)$/.exec(line);
  return m ? { key: m[1], value: m[2].trim() } : null;
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
  if (!array || !array.length) throw new BlockError("the block needs an array: line with at least one value");
  if (!raw.length) throw new BlockError("the block has no steps (lines starting with \"- \")");
  const steps = raw.map(({ body }, s) => {
    const where = `step ${s + 1}`;
    const bar = body.indexOf("|");
    if (bar < 0) throw new BlockError(`${where}: put " | " between the pointers and the narration`);
    const ptrs = {};
    for (const pair of body.slice(0, bar).trim().split(/\s+/).filter(Boolean)) {
      const m = /^([^=]+)=(.*)$/.exec(pair);
      if (!m) throw new BlockError(`${where}: "${pair}" is not key=value`);
      const [, key, val] = m;
      if (!POINTER_KEYS.includes(key)) throw new BlockError(`${where}: unknown pointer "${key}" (use ${POINTER_KEYS.join(" ")})`);
      if (!/^\d+$/.test(val)) throw new BlockError(`${where}: ${key}=${val} is not a cell index`);
      const idx = Number(val);
      if (idx > array.length) throw new BlockError(`${where}: ${key}=${idx} is past the end of the array (length ${array.length})`);
      ptrs[key] = idx;
    }
    return { ptrs, text: body.slice(bar + 1).trim() };
  });
  return { title, array, range, steps };
}

export function stepCells(data, k) {
  const { array, range } = data;
  const ptrs = data.steps[k].ptrs;
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
    cells.push({
      value: idx < n ? array[idx] : "",
      index: idx,
      ghost: idx === n,
      state,
      labels: POINTER_KEYS.filter((key) => key !== "ans" && ptrs[key] === idx),
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
