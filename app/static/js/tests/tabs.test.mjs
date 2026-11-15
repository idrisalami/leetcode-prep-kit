// The solution tabs and the history list, without the DOM.
// Run with: node --test "app/static/js/tests/*.test.mjs"
import test from "node:test";
import assert from "node:assert/strict";
import { MAIN_TAB, MAX_TAB_NAME, hasTabs, tabsOf, cleanTabName, sameTabs, pickTab, draftText, changedDraft,
  patchDraft, historyRows, historyLabel, fmtWhen, historyMeta } from "../tabs.js";

test("a payload without a tab list is one main tab holding the code", () => {
  assert.equal(hasTabs({ code: "x" }), false);
  assert.equal(hasTabs({ tabs: [] }), false);
  assert.equal(hasTabs(null), false);
  assert.deepEqual(tabsOf({ code: "x = 1", skeleton: "s" }), [{ id: 1, name: "solution.py", code: "x = 1" }]);
  assert.deepEqual(tabsOf({ skeleton: "s" }), [{ id: 1, name: "solution.py", code: "s" }]);
  assert.deepEqual(tabsOf(null), [{ id: 1, name: "solution.py", code: "" }]);
});

test("the tab list is taken as sent, the main tab first", () => {
  const p = { code: "a", tabs: [{ id: 3, name: "heap.py", code: "c" }, { id: 1, name: "solution.py", code: "a" }] };
  assert.equal(hasTabs(p), true);
  assert.deepEqual(tabsOf(p), [{ id: 1, name: "solution.py", code: "a" }, { id: 3, name: "heap.py", code: "c" }]);
});

test("entries that are not tabs, or repeat an id, are dropped; a missing main tab is added", () => {
  const p = { code: "main", tabs: [null, { id: 0, name: "zero" }, { id: "2", name: "text id" },
    { id: 2, name: "", code: "b" }, { id: 2, name: "again", code: "z" }, { id: 4, name: "  two   words ", code: 7 }] };
  assert.deepEqual(tabsOf(p), [
    { id: 1, name: "solution.py", code: "main" },
    { id: 2, name: "solution-2.py", code: "b" },
    { id: 4, name: "two words", code: "" },
  ]);
});

test("a tab name is one tidy line, capped in length", () => {
  assert.equal(cleanTabName("  brute \n force.py "), "brute force.py");
  assert.equal(cleanTabName(""), "");
  assert.equal(cleanTabName(null), "");
  assert.equal(cleanTabName("   "), "");
  assert.equal(cleanTabName("x".repeat(MAX_TAB_NAME + 5)).length, MAX_TAB_NAME);
});

test("tab lists compare by id and name, not by code", () => {
  const a = [{ id: 1, name: "solution.py", code: "a" }, { id: 2, name: "b.py", code: "b" }];
  assert.equal(sameTabs(a, [{ id: 1, name: "solution.py", code: "other" }, { id: 2, name: "b.py" }]), true);
  assert.equal(sameTabs(a, [{ id: 1, name: "solution.py" }]), false);
  assert.equal(sameTabs(a, [{ id: 1, name: "solution.py" }, { id: 2, name: "renamed.py" }]), false);
  assert.equal(sameTabs(a, [{ id: 1, name: "solution.py" }, { id: 3, name: "b.py" }]), false);
  assert.equal(sameTabs(null, []), true);
});

test("the remembered tab is shown only when it still exists", () => {
  const tabs = [{ id: 1 }, { id: 3 }];
  assert.equal(pickTab(tabs, "3"), 3);
  assert.equal(pickTab(tabs, 3), 3);
  assert.equal(pickTab(tabs, "2"), MAIN_TAB);
  assert.equal(pickTab(tabs, null), MAIN_TAB);
  assert.equal(pickTab(tabs, "abc"), MAIN_TAB);
});

test("the draft text holds every tab in id order, so equal content compares equal", () => {
  const notes = { pattern: "p" };
  const a = draftText({ 3: "c", 1: "a" }, notes, true);
  const b = draftText({ 1: "a", 3: "c" }, notes, true);
  assert.equal(a, b);
  assert.deepEqual(JSON.parse(a), { codes: { 1: "a", 3: "c" }, notes });
});

test("for a server from before tabs the draft is the main tab's code alone", () => {
  assert.deepEqual(JSON.parse(draftText({ 1: "a", 2: "b" }, { pattern: "" }, false)), { code: "a", notes: { pattern: "" } });
});

test("the leave-page draft carries only the tabs that changed", () => {
  const saved = draftText({ 1: "a", 2: "b", 3: "c" }, { pattern: "" }, true);
  const now = draftText({ 1: "a", 2: "B", 3: "c" }, { pattern: "new" }, true);
  assert.deepEqual(JSON.parse(changedDraft(now, saved)), { codes: { 2: "B" }, notes: { pattern: "new" } });
  assert.deepEqual(JSON.parse(changedDraft(saved, saved)), { codes: {}, notes: { pattern: "" } });
});

test("the leave-page draft is left alone when it is the older shape or unreadable", () => {
  const old = draftText({ 1: "a" }, {}, false);
  assert.equal(changedDraft(old, old), old);
  assert.equal(changedDraft("not json", old), "not json");
});

test("the saved draft is patched when a tab is added, reset or closed", () => {
  const saved = draftText({ 1: "a", 2: "b" }, { pattern: "p" }, true);
  assert.deepEqual(JSON.parse(patchDraft(saved, 3, "c")), { codes: { 1: "a", 2: "b", 3: "c" }, notes: { pattern: "p" } });
  assert.deepEqual(JSON.parse(patchDraft(saved, 2, "skeleton")).codes, { 1: "a", 2: "skeleton" });
  assert.deepEqual(JSON.parse(patchDraft(saved, 2, null)).codes, { 1: "a" });
  assert.equal(patchDraft(saved, 2, "b"), saved);
  const old = draftText({ 1: "a" }, {}, false);
  assert.deepEqual(JSON.parse(patchDraft(old, 1, "s")), { code: "s", notes: {} });
  assert.equal(patchDraft(old, 2, "x"), old);
});

test("the history shows the newest version first", () => {
  const rows = historyRows([{ id: 1 }, { id: 2 }, null, { id: "3" }, { id: 4 }]);
  assert.deepEqual(rows.map((r) => r.id), [4, 2, 1]);
  assert.deepEqual(historyRows(null), []);
  assert.deepEqual(historyRows([{ id: 0, why: "previous" }]).map((r) => r.id), [0]);
});

test("a history entry is described in the app's own words", () => {
  assert.deepEqual(historyLabel({ why: "submit", ok: true, passed: 9, total: 9 }), { text: "All 9 tests passed", tone: "good" });
  assert.deepEqual(historyLabel({ why: "submit", ok: false, passed: 4, total: 9 }), { text: "4 of 9 tests passed", tone: "bad" });
  assert.deepEqual(historyLabel({ why: "submit", ok: false }), { text: "Tests did not pass", tone: "bad" });
  assert.deepEqual(historyLabel({ why: "submit", ok: true }), { text: "All tests passed", tone: "good" });
  assert.equal(historyLabel({ why: "reset" }).text, "Before a reset");
  assert.equal(historyLabel({ why: "redo" }).text, "Before a redo");
  assert.equal(historyLabel({ why: "closed" }).text, "Closed tab");
  assert.equal(historyLabel({ why: "previous" }).text, "Earlier version");
  assert.equal(historyLabel(null).text, "Earlier version");
});

test("a stored time is shown as written, with no time zone shift", () => {
  assert.equal(fmtWhen("2030-01-05T09:07:41"), "5 Jan 2030, 09:07");
  assert.equal(fmtWhen("2024-03-07T08:05:00"), "7 Mar 2024, 08:05");
  assert.equal(fmtWhen(""), "");
  assert.equal(fmtWhen(null), "");
  assert.equal(fmtWhen("2030-13-01T10:00:00"), "");
  assert.equal(fmtWhen("yesterday"), "");
});

test("the small print of a history row leaves out what is missing", () => {
  assert.equal(historyMeta({ tab: "solution.py", attempt: 2, at: "2030-01-05T09:07:41" }),
    "solution.py · Attempt 2 · 5 Jan 2030, 09:07");
  assert.equal(historyMeta({ tab: "solution.py", attempt: null, at: "" }), "solution.py");
  assert.equal(historyMeta(null), "");
});
