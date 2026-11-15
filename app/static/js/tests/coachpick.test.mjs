// The coach choice (welcome page, menu line, Home's plan step), without the DOM.
// Run with: node --test "app/static/js/tests/*.test.mjs"
import test from "node:test";
import assert from "node:assert/strict";
import { isCoachPayload, needsWelcome, cards, coachStatus, unavailableText, navLabel, backHash }
  from "../coachpick.js";

const payload = (over = {}, found = { claude: true, codex: true }) => Object.assign({
  choice: null,
  active: found.claude ? "claude" : null,
  providers: [
    { key: "claude", label: "Claude Code", command: "claude", found: found.claude,
      install_url: "https://claude.com/claude-code" },
    { key: "codex", label: "OpenAI Codex", command: "codex", found: found.codex,
      install_url: "https://github.com/openai/codex" },
  ],
}, over);

test("only a real payload with nothing picked opens the welcome page", () => {
  assert.equal(needsWelcome(payload()), true);
  assert.equal(needsWelcome(payload({ choice: "claude" })), false);
  assert.equal(needsWelcome(payload({ choice: "none", active: null })), false);
  // An older server, an error body, a broken answer: never a redirect.
  for (const bad of [null, undefined, "", 404, {}, { choice: null }, { choice: null, providers: [] },
    { error: "not_found" }, { providers: [{ key: "claude" }] }]) {
    assert.equal(isCoachPayload(bad), false);
    assert.equal(needsWelcome(bad), false);
  }
});

test("one card per tool, in the server's order", () => {
  const list = cards(payload({ choice: "codex", active: "codex" }, { claude: false, codex: true }));
  assert.deepEqual(list.map((c) => [c.key, c.found, c.recommended, c.connected]),
    [["claude", false, true, false], ["codex", true, false, true]]);
  assert.equal(list[0].installUrl, "https://claude.com/claude-code");
  assert.equal(list[1].command, "codex");
  assert.deepEqual(cards(null), []);
});

test("a card survives missing fields", () => {
  const list = cards({ choice: null, active: null, providers: [{ key: "codex" }, null, {}] });
  assert.deepEqual(list, [{ key: "codex", label: "codex", command: "codex", found: false,
    installUrl: "", recommended: false, connected: false }]);
});

test("the status names the tool in use", () => {
  assert.deepEqual(coachStatus({ claude: true, coach: payload({ choice: "claude" }) }),
    { kind: "ready", label: "Claude Code", command: "claude" });
  assert.deepEqual(coachStatus({ claude: true, coach: payload({ choice: "codex", active: "codex" }) }),
    { kind: "ready", label: "OpenAI Codex", command: "codex" });
  // Nothing picked yet: Claude Code when it is there.
  assert.deepEqual(coachStatus({ claude: true, coach: payload() }),
    { kind: "ready", label: "Claude Code", command: "claude" });
});

test("the status says why there is no coach", () => {
  const gone = coachStatus({ claude: false,
    coach: payload({ choice: "codex", active: "codex" }, { claude: true, codex: false }) });
  assert.deepEqual(gone, { kind: "missing", label: "OpenAI Codex", command: "codex" });
  assert.equal(unavailableText(gone), "OpenAI Codex was not found on this computer.");

  const none = coachStatus({ claude: false, coach: payload({ choice: "none", active: null }) });
  assert.deepEqual(none, { kind: "none", label: null, command: null });
  assert.equal(unavailableText(none), "No coach is connected.");

  const nothing = coachStatus({ claude: false, coach: payload({}, { claude: false, codex: false }) });
  assert.deepEqual(nothing, { kind: "missing", label: null, command: null });
  assert.equal(unavailableText(nothing), "No coach tool was found on this computer.");

  assert.equal(unavailableText(coachStatus({ claude: true, coach: payload() })), "");
  assert.equal(unavailableText(null), "");
});

test("an older server means Claude Code, found or not", () => {
  assert.deepEqual(coachStatus({ claude: true }), { kind: "ready", label: "Claude Code", command: "claude" });
  assert.deepEqual(coachStatus({ claude: false }), { kind: "missing", label: "Claude Code", command: "claude" });
  assert.deepEqual(coachStatus(null), { kind: "ready", label: "Claude Code", command: "claude" });
  assert.deepEqual(coachStatus({ claude: false, coach: { error: "x" } }).kind, "missing");
});

test("the menu line", () => {
  assert.equal(navLabel(payload({ choice: "claude" })), "Claude Code");
  assert.equal(navLabel(payload({ choice: "codex", active: "codex" })), "OpenAI Codex");
  assert.equal(navLabel(payload({ choice: "none", active: null })), "Not connected");
  assert.equal(navLabel(payload({ choice: "codex", active: "codex" }, { claude: true, codex: false })), "Not connected");
  assert.equal(navLabel(payload({}, { claude: false, codex: false })), "Not connected");
  assert.equal(navLabel(null), "Not connected");
});

test("the way back is an in-app route or Home", () => {
  assert.equal(backHash("/practice/two-sum"), "#/practice/two-sum");
  assert.equal(backHash("/module/04?at=the-template"), "#/module/04?at=the-template");
  assert.equal(backHash("/doc/course/diagnostic.md"), "#/doc/course/diagnostic.md");
  for (const bad of [undefined, "", "practice", "//evil.example", "/welcome", "/welcome?back=/welcome",
    "javascript:alert(1)", "/a b", "/x#y", "https://example.com"]) {
    assert.equal(backHash(bad), "#/");
  }
});
