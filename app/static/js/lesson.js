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

export function progressLine({ read, total, drills }) {
  return `${read} of ${total} sections read` + (drills ? ` · ${drills.solved}/${drills.count} drills` : "");
}

export function countsAsSection(h2Text) {
  return !/^self-check answers$/i.test(String(h2Text).trim());
}

export function newlyRead(ends, viewportH, read) {
  return ends.filter((e) => !read.has(e.id) && e.top < viewportH).map((e) => e.id);
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
