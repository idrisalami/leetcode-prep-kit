// The solution tabs and the history of earlier versions on the Practice page: the parts with no
// DOM in them, so node can test them. Tab 1 is always the main solution (solution.py); the
// server names and numbers the others.

export const MAIN_TAB = 1;
export const MAIN_NAME = "solution.py";
export const MAX_TAB_NAME = 40;
/** The most tabs one problem can have. The server enforces the same limit (store.MAX_TABS). */
export const MAX_TABS = 8;

const isId = (n) => Number.isInteger(n) && n >= 1;

/** True when the server's answer carries the tab list (a server from before tabs does not). */
export function hasTabs(p) {
  return !!p && Array.isArray(p.tabs) && p.tabs.length > 0;
}

/**
 * The tabs of problem payload `p` as [{id, name, code}], the main tab first. Entries that are
 * not a tab, or repeat an id, are dropped. Without a tab list there is one tab, the main one,
 * holding `p.code` (or the skeleton).
 */
export function tabsOf(p) {
  const start = (p && (p.code ?? p.skeleton)) ?? "";
  const out = [];
  const seen = new Set();
  for (const t of (p && Array.isArray(p.tabs) ? p.tabs : [])) {
    if (!t || !isId(t.id) || seen.has(t.id)) continue;
    seen.add(t.id);
    out.push({
      id: t.id,
      name: cleanTabName(t.name) || (t.id === MAIN_TAB ? MAIN_NAME : "solution-" + t.id + ".py"),
      code: typeof t.code === "string" ? t.code : (t.id === MAIN_TAB ? start : ""),
    });
  }
  const main = out.find((t) => t.id === MAIN_TAB) || { id: MAIN_TAB, name: MAIN_NAME, code: start };
  return [main, ...out.filter((t) => t.id !== MAIN_TAB)];
}

/** A tab name as typed, tidied: one line, single spaces, no longer than the limit. "" if empty. */
export function cleanTabName(text) {
  return String(text == null ? "" : text).replace(/\s+/g, " ").trim().slice(0, MAX_TAB_NAME).trim();
}

/** Do two tab lists show the same tabs (ids and names, in order)? The code is not compared. */
export function sameTabs(a, b) {
  const x = a || [];
  const y = b || [];
  return x.length === y.length && x.every((t, i) => t.id === y[i].id && t.name === y[i].name);
}

/** The id to show: `wanted` when that tab exists, the main tab otherwise. */
export function pickTab(tabs, wanted) {
  const id = Number(wanted);
  return (tabs || []).some((t) => t.id === id) ? id : MAIN_TAB;
}

/**
 * The text the autosave compares and sends: every tab's code and the four boxes. `codes` is
 * {id: code}. With `multi` false (a server from before tabs) it is the older shape, the main
 * tab's code alone. Keys are written in id order, so equal content gives an equal string.
 */
export function draftText(codes, notes, multi) {
  if (!multi) return JSON.stringify({ code: codes[MAIN_TAB] ?? "", notes });
  const sorted = {};
  for (const id of Object.keys(codes).map(Number).sort((a, b) => a - b)) sorted[id] = codes[id];
  return JSON.stringify({ codes: sorted, notes });
}

/**
 * The same draft with only the tabs whose code differs from the saved draft: the short body for
 * the save on leaving the page, which has a size limit. Both arguments are draftText strings.
 */
export function changedDraft(text, saved) {
  let now;
  let before;
  try { now = JSON.parse(text); before = JSON.parse(saved); } catch (e) { return text; }
  if (!now || !now.codes || !before || !before.codes) return text;
  const codes = {};
  for (const [id, code] of Object.entries(now.codes)) {
    if (before.codes[id] !== code) codes[id] = code;
  }
  return JSON.stringify({ codes, notes: now.notes });
}

/** `saved` (a draftText string) with tab `id` set to `code`, or taken out when `code` is null. */
export function patchDraft(saved, id, code) {
  const s = JSON.parse(saved);
  if (!s.codes) {
    if (id === MAIN_TAB && code !== null) s.code = code;
    return JSON.stringify(s);
  }
  const codes = Object.assign({}, s.codes);
  if (code === null) delete codes[id]; else codes[id] = code;
  return draftText(codes, s.notes, true);
}

/** The history list as the panel shows it: newest first, entries without an id dropped. */
export function historyRows(history) {
  return (Array.isArray(history) ? history : [])
    .filter((r) => r && Number.isInteger(r.id) && r.id >= 0)
    .slice().reverse();
}

/**
 * What one history entry is, in the app's words: {text, tone}. A submit shows the result of the
 * app's tests; the others say what moved the code aside.
 */
export function historyLabel(rec) {
  const why = rec && rec.why;
  if (why === "submit") {
    const total = Number(rec.total) || 0;
    const passed = Number(rec.passed) || 0;
    if (rec.ok) return { text: total ? "All " + total + " tests passed" : "All tests passed", tone: "good" };
    return { text: total ? passed + " of " + total + " tests passed" : "Tests did not pass", tone: "bad" };
  }
  if (why === "reset") return { text: "Before a reset", tone: "plain" };
  if (why === "redo") return { text: "Before a redo", tone: "plain" };
  if (why === "closed") return { text: "Closed tab", tone: "plain" };
  return { text: "Earlier version", tone: "plain" };
}

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

/** "2030-01-05T09:07:41" as "5 Jan 2030, 09:07", the clock as it was stored. "" if unreadable. */
export function fmtWhen(iso) {
  const m = /^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2})/.exec(String(iso == null ? "" : iso));
  if (!m) return "";
  const month = MONTHS[Number(m[2]) - 1];
  if (!month) return "";
  return Number(m[3]) + " " + month + " " + m[1] + ", " + m[4] + ":" + m[5];
}

/** The small print of a history row: which tab, which attempt, when. Parts that are missing go. */
export function historyMeta(rec) {
  const parts = [];
  if (rec && rec.tab) parts.push(String(rec.tab));
  if (rec && Number.isInteger(rec.attempt)) parts.push("Attempt " + rec.attempt);
  const when = fmtWhen(rec && rec.at);
  if (when) parts.push(when);
  return parts.join(" · ");
}
