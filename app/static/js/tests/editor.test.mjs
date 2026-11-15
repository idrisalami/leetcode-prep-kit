// Pure helpers of the editor module. Run with: node --test "app/static/js/tests/*.test.mjs"
import test from "node:test";
import assert from "node:assert/strict";
import { keyLabels, isMacPlatform, clampLine, indentBackspace } from "../editor.js";

test("keyLabels uses the Command sign on a Mac and Ctrl elsewhere", () => {
  assert.deepEqual(keyLabels(true), { run: "⌘↩", save: "⌘S", comment: "⌘/" });
  assert.deepEqual(keyLabels(false), { run: "Ctrl+Enter", save: "Ctrl+S", comment: "Ctrl+/" });
});

test("isMacPlatform reads the platform string", () => {
  assert.equal(isMacPlatform({ platform: "MacIntel" }), true);
  assert.equal(isMacPlatform({ platform: "iPhone" }), true);
  assert.equal(isMacPlatform({ platform: "Win32" }), false);
  assert.equal(isMacPlatform({ platform: "Linux x86_64" }), false);
  assert.equal(isMacPlatform({ userAgentData: { platform: "macOS" } }), true);
  assert.equal(isMacPlatform(undefined), false);
});

test("clampLine turns a 1-based user line into a 0-based editor line, or null", () => {
  assert.equal(clampLine(1, 10), 0);
  assert.equal(clampLine(10, 10), 9);
  assert.equal(clampLine(11, 10), null);
  assert.equal(clampLine(0, 10), null);
  assert.equal(clampLine(null, 10), null);
  assert.equal(clampLine("3", 10), 2);
  assert.equal(clampLine(2.5, 10), null);
});

test("indentBackspace removes a whole indent step inside the indentation", () => {
  assert.equal(indentBackspace("    "), 4);
  assert.equal(indentBackspace("        "), 4);
  assert.equal(indentBackspace("            ", 4), 4);
});

test("indentBackspace goes back to the previous indent stop from an uneven column", () => {
  assert.equal(indentBackspace(" "), 1);
  assert.equal(indentBackspace("  "), 2);
  assert.equal(indentBackspace("     "), 1);
  assert.equal(indentBackspace("       "), 3);
  assert.equal(indentBackspace("   ", 2), 1);
});

test("indentBackspace leaves everything else to the editor", () => {
  assert.equal(indentBackspace(""), 0);
  assert.equal(indentBackspace("    x"), 0);
  assert.equal(indentBackspace("x = 1    "), 0);
  assert.equal(indentBackspace("\t"), 0);
  assert.equal(indentBackspace(undefined), 0);
  assert.equal(indentBackspace("    ", 0), 0);
});
