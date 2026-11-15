// Pure helpers of the problem browser (problems.js). Run with:
// node --test "app/static/js/tests/*.test.mjs"
import test from "node:test";
import assert from "node:assert/strict";
import {
  normalizeFilters, filtersToQuery, filterProblems, facetCounts, groupByModule,
  pickContinue, touchTimes, actionFor, nextUpModule,
} from "../problems.js";
import { redoFailure } from "../redo.js";
import { starFailure } from "../star.js";

const MODULES = [{ id: "01", title: "Arrays and hashing" }, { id: "02", title: "Stacks" },
  { id: "03", title: "Two pointers" }];

const P = (slug, module, difficulty, status, seconds = 0) => ({ slug, number: slug.length,
  title: slug, module, difficulty, status, seconds });

const LIST = [
  P("a1", "01", "Easy", "solved", 600),
  P("a2", "01", "Medium", "attempted", 300),
  P("a3", "01", "Hard", "new"),
  P("b1", "02", "Easy", "new"),
  P("b2", "02", "Medium", "solved", 900),
  P("c1", "03", "Medium", "attempted", 1200),
];

test("normalizeFilters keeps known values and falls back to all", () => {
  assert.deepEqual(normalizeFilters({}, ["01", "02"]),
    { status: "all", difficulty: "all", module: "all", starred: "all" });
  assert.deepEqual(normalizeFilters({ status: "solved", difficulty: "Hard", module: "02" }, ["01", "02"]),
    { status: "solved", difficulty: "Hard", module: "02", starred: "all" });
  assert.deepEqual(normalizeFilters({ status: "done", difficulty: "hard", module: "99" }, ["01"]),
    { status: "all", difficulty: "Hard", module: "all", starred: "all" });
  assert.deepEqual(normalizeFilters(null, ["01"]),
    { status: "all", difficulty: "all", module: "all", starred: "all" });
  assert.equal(normalizeFilters({ starred: "yes" }).starred, "yes");
  for (const odd of ["no", "true", true, 1, "", null]) {
    assert.equal(normalizeFilters({ starred: odd }).starred, "all");
  }
});

test("filtersToQuery leaves out defaults and keeps a fixed order", () => {
  assert.equal(filtersToQuery({ status: "all", difficulty: "all", module: "all" }), "");
  assert.equal(filtersToQuery({ module: "04", status: "attempted", difficulty: "all" }), "status=attempted&module=04");
  assert.equal(filtersToQuery({ status: "new", difficulty: "Easy", module: "all" }), "status=new&difficulty=Easy");
  assert.equal(filtersToQuery({ status: "all", difficulty: "all", module: "all", starred: "all" }), "");
  assert.equal(filtersToQuery({ starred: "yes", module: "04", status: "all", difficulty: "all" }),
    "module=04&starred=yes");
  assert.deepEqual(normalizeFilters(Object.fromEntries(new URLSearchParams("module=04&starred=yes")), ["04"]),
    { status: "all", difficulty: "all", module: "04", starred: "yes" });
});

test("filterProblems applies all three filters and keeps the list order", () => {
  const all = { status: "all", difficulty: "all", module: "all" };
  assert.deepEqual(filterProblems(LIST, all).map((p) => p.slug), ["a1", "a2", "a3", "b1", "b2", "c1"]);
  assert.deepEqual(filterProblems(LIST, { ...all, status: "attempted" }).map((p) => p.slug), ["a2", "c1"]);
  assert.deepEqual(filterProblems(LIST, { ...all, difficulty: "Medium", module: "01" }).map((p) => p.slug), ["a2"]);
  assert.deepEqual(filterProblems(LIST, { status: "solved", difficulty: "Hard", module: "all" }), []);
});

test("the star filter keeps the starred problems and combines with the others", () => {
  const all = { status: "all", difficulty: "all", module: "all", starred: "all" };
  const list = LIST.map((p) => ({ ...p, starred: ["a2", "b1", "c1"].includes(p.slug) }));
  assert.equal(filterProblems(list, all).length, 6);
  assert.deepEqual(filterProblems(list, { ...all, starred: "yes" }).map((p) => p.slug), ["a2", "b1", "c1"]);
  assert.deepEqual(filterProblems(list, { ...all, starred: "yes", difficulty: "Medium" }).map((p) => p.slug),
    ["a2", "c1"]);
  assert.deepEqual(filterProblems(LIST, { ...all, starred: "yes" }), []); // no starred field: not starred
  const c = facetCounts(list, { ...all, starred: "yes" }, ["01", "02", "03"]);
  assert.deepEqual(c.starred, { all: 6, yes: 3 });
  assert.deepEqual(c.status, { all: 3, new: 1, attempted: 2, solved: 0 });
  assert.deepEqual(c.difficulty, { all: 3, Easy: 1, Medium: 2, Hard: 0 });
  assert.deepEqual(facetCounts(list, { ...all, module: "01" }, ["01"]).starred, { all: 3, yes: 1 });
  const g = groupByModule(list, MODULES, { ...all, starred: "yes" });
  assert.deepEqual(g.map((x) => [x.id, x.total, x.rows.length]), [["01", 3, 1], ["02", 2, 1], ["03", 1, 1]]);
});

test("starFailure says to restart when the server has no star route yet", () => {
  assert.match(starFailure({ status: 404, detail: "No API route." }), /python3 app\/server\.py/);
  assert.equal(starFailure({ status: 500, detail: "Disk full." }), "Could not save the star. Disk full.");
  assert.equal(starFailure(new Error("network")), "Could not save the star. The app's server did not answer.");
});

test("an unknown status counts as new", () => {
  const odd = [{ slug: "x", module: "01", difficulty: "Easy" }];
  assert.equal(filterProblems(odd, { status: "new", difficulty: "all", module: "all" }).length, 1);
});

test("facetCounts counts each option with the other two filters applied", () => {
  const c = facetCounts(LIST, { status: "all", difficulty: "Medium", module: "all" }, ["01", "02", "03"]);
  assert.deepEqual(c.status, { all: 3, new: 0, attempted: 2, solved: 1 });
  assert.deepEqual(c.difficulty, { all: 6, Easy: 2, Medium: 3, Hard: 1 });
  assert.deepEqual(c.module, { all: 3, "01": 1, "02": 1, "03": 1 });
});

test("groupByModule keeps module order, module totals and only matching rows", () => {
  const g = groupByModule(LIST, MODULES, { status: "new", difficulty: "all", module: "all" });
  assert.deepEqual(g.map((x) => x.id), ["01", "02"]);
  assert.deepEqual(g[0], { id: "01", title: "Arrays and hashing", solved: 1, total: 3,
    rows: [LIST[2]] });
  assert.equal(g[1].solved, 1);
  assert.equal(g[1].total, 2);
});

test("groupByModule keeps a problem whose module is not in the module list", () => {
  const g = groupByModule([P("z", "11", "Easy", "new")], MODULES, { status: "all", difficulty: "all", module: "all" });
  assert.equal(g.length, 1);
  assert.equal(g[0].id, "11");
  assert.equal(g[0].title, "Module 11");
});

test("nextUpModule is the first module that is not fully solved", () => {
  assert.equal(nextUpModule(LIST, MODULES), "01");
  const done = LIST.map((p) => (p.module === "01" ? { ...p, status: "solved" } : p));
  assert.equal(nextUpModule(done, MODULES), "02");
  assert.equal(nextUpModule(LIST.map((p) => ({ ...p, status: "solved" })), MODULES), null);
});

test("touchTimes uses the list's last_at and the opened time, whichever is later", () => {
  const list = [
    { ...P("a2", "01", "Medium", "attempted"), last_at: "2024-03-02T09:00:00" },
    { ...P("c1", "03", "Medium", "attempted"), last_at: "2024-03-01T09:00:00" },
    { ...P("d1", "03", "Easy", "attempted"), last_at: null },
    { ...P("e1", "03", "Easy", "attempted"), last_at: "not a time" },
    { ...P("a1", "01", "Easy", "solved"), last_at: "2024-05-01T00:00:00" },
    null,
  ];
  const opened = { c1: "2024-03-05T10:00:00.000Z", a2: "2024-01-01T00:00:00.000Z", e1: "2024-02-01T00:00:00.000Z",
    a1: "2024-06-01T00:00:00.000Z" };
  assert.deepEqual(touchTimes(list, opened), {
    a2: "2024-03-02T09:00:00",          // last_at is later than the opened time
    c1: "2024-03-05T10:00:00.000Z",     // opened in this browser after the last save
    e1: "2024-02-01T00:00:00.000Z",     // a bad last_at falls back to the opened time
  }, "d1 has neither, a1 is solved");
  assert.deepEqual(touchTimes(list), { a2: "2024-03-02T09:00:00", c1: "2024-03-01T09:00:00" });
  assert.deepEqual(touchTimes(list, null), touchTimes(list));
});

test("redoFailure opens the workspace on not_solved and stays put on anything else", () => {
  assert.deepEqual(redoFailure({ code: "not_solved", detail: "x" }, "Two Sum"), { open: true, kind: "info",
    text: "Two Sum is not solved yet, so there is nothing to redo. Opening it as it is." });
  assert.deepEqual(redoFailure({ code: "io", detail: "Disk full." }, "Two Sum"),
    { open: false, kind: "error", text: "Disk full." });
  assert.deepEqual(redoFailure(new Error("network"), "Two Sum"),
    { open: false, kind: "error", text: "Could not start it again." });
});

test("pickContinue returns null when nothing is in progress", () => {
  assert.equal(pickContinue(LIST.filter((p) => p.status !== "attempted"), {}), null);
  assert.equal(pickContinue([], {}), null);
});

test("pickContinue picks the most recently touched attempted problem", () => {
  const touches = { a2: "2024-03-02T09:00:00", c1: "2024-03-01T09:00:00", a1: "2024-04-01T00:00:00" };
  assert.equal(pickContinue(LIST, touches).slug, "a2");
  assert.equal(pickContinue(LIST, { c1: "2024-03-05T00:00:00", a2: "2024-03-02T09:00:00" }).slug, "c1");
});

test("pickContinue prefers a touched problem over one without a time, then more time spent", () => {
  assert.equal(pickContinue(LIST, { a2: "2024-01-01T00:00:00" }).slug, "a2");
  // No times at all: the one with more time on it (c1 1200 s over a2 300 s).
  assert.equal(pickContinue(LIST, {}).slug, "c1");
  // Equal time: list order.
  const even = [P("x", "01", "Easy", "attempted", 60), P("y", "01", "Easy", "attempted", 60)];
  assert.equal(pickContinue(even, {}).slug, "x");
});

test("actionFor maps status to the one button", () => {
  assert.deepEqual(actionFor({ status: "new" }), { kind: "start", label: "Start coding" });
  assert.deepEqual(actionFor({ status: "attempted" }), { kind: "continue", label: "Continue" });
  assert.deepEqual(actionFor({ status: "solved" }), { kind: "redo", label: "Redo" });
  assert.deepEqual(actionFor({}), { kind: "start", label: "Start coding" });
});
