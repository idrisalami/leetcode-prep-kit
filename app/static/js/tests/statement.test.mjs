// Grouping of a problem statement into question, examples, constraints and closing notes.
// Run with: node --test "app/static/js/tests/*.test.mjs"
import test from "node:test";
import assert from "node:assert/strict";
import { groupStatement, splitLabels } from "../statement.js";

const p = (text) => ({ tag: "p", text });
const pre = (text) => ({ tag: "pre", text, solid: true });
const ul = (text) => ({ tag: "ul", text, solid: true });

test("the usual shape: question, one card per example, constraints", () => {
  const groups = groupStatement([
    p("Given an array, return the answer."),
    p("You may assume one answer exists."),
    p("Example 1:"),
    pre("Input: nums = [1]\nOutput: 1"),
    p("Example 2:"),
    pre("Input: nums = [2]\nOutput: 2"),
    p("Constraints:"),
    ul("nums is not empty"),
  ]);
  assert.deepEqual(groups, {
    question: [0, 1],
    examples: [{ title: "Example 1", items: [3] }, { title: "Example 2", items: [5] }],
    constraints: [7],
    after: [],
  });
});

test("headings themselves and empty spacer blocks are left out", () => {
  const groups = groupStatement([
    p("Question."),
    p(" "),
    p(" "),
    p("Example 1:"),
    pre("Input: x"),
    p(""),
    p("Constraints:"),
    ul("x"),
  ]);
  assert.deepEqual(groups.question, [0]);
  assert.deepEqual(groups.examples, [{ title: "Example 1", items: [4] }]);
  assert.deepEqual(groups.constraints, [7]);
});

test("a block with no text but an image is kept, not treated as a spacer", () => {
  const groups = groupStatement([
    p("Question."),
    p("Example 1:"),
    { tag: "img", text: "", solid: true },
    pre("Input: x"),
  ]);
  assert.deepEqual(groups.examples[0].items, [2, 3]);
});

test("examples written as several blocks stay in one card", () => {
  const groups = groupStatement([
    p("Question."),
    { tag: "div", text: "Example 1:" },
    { tag: "div", text: "Input: s = \"a\"" },
    { tag: "div", text: "Output: true" },
    p("Explanation: it matches."),
    { tag: "h3", text: "Example 2" },
    p("Input: s = \"b\""),
  ]);
  assert.deepEqual(groups.examples, [
    { title: "Example 1", items: [2, 3, 4] },
    { title: "Example 2", items: [6] },
  ]);
});

test("an example heading with no number, odd spacing or invisible marks is still a heading", () => {
  const groups = groupStatement([
    p("Question."),
    p("Example:"),
    pre("Input: x"),
    p("​ Example  2 :﻿"),
    pre("Input: y"),
    p("constraints"),
    ul("y"),
  ]);
  assert.deepEqual(groups.examples.map((ex) => ex.title), ["Example", "Example 2"]);
  assert.deepEqual(groups.constraints, [6]);
});

test("only a block of its own counts as a heading", () => {
  const groups = groupStatement([
    p("Example 1: this sentence only starts like a heading."),
    pre("Example 1:"),
    ul("Constraints:"),
  ]);
  assert.deepEqual(groups, { question: [0, 1, 2], examples: [], constraints: [], after: [] });
});

test("a follow-up after the constraints goes to the closing notes", () => {
  const groups = groupStatement([
    p("Question."),
    p("Example 1:"),
    pre("Input: x"),
    p("Constraints:"),
    ul("x"),
    p("Follow-up: can you do it in one pass?"),
    p("More about the follow-up."),
    { tag: "details", text: "Hint" },
  ]);
  assert.deepEqual(groups.constraints, [4]);
  assert.deepEqual(groups.after, [5, 6, 7]);
});

test("a note between the examples and the constraints does not swallow the constraints", () => {
  const groups = groupStatement([
    p("Question."),
    p("Example 1:"),
    pre("Input: x"),
    p("Note: the edges are undirected."),
    p("Constraints:"),
    ul("x"),
  ]);
  assert.deepEqual(groups.examples[0].items, [2]);
  assert.deepEqual(groups.after, [3]);
  assert.deepEqual(groups.constraints, [5]);
});

test("a note or follow-up inside the question stays in the question", () => {
  const groups = groupStatement([
    p("Question."),
    p("Note: the answer fits in an integer."),
    p("Follow up: think about the sorted case."),
    p("Example 1:"),
    pre("Input: x"),
  ]);
  assert.deepEqual(groups.question, [0, 1, 2]);
  assert.deepEqual(groups.after, []);
});

test("a statement with no examples is all question, then constraints", () => {
  const groups = groupStatement([p("Design a class."), pre("class X"), p("Constraints:"), ul("x")]);
  assert.deepEqual(groups, { question: [0, 1], examples: [], constraints: [3], after: [] });
});

test("nothing in gives empty parts out", () => {
  const empty = { question: [], examples: [], constraints: [], after: [] };
  assert.deepEqual(groupStatement([]), empty);
  assert.deepEqual(groupStatement(null), empty);
  assert.deepEqual(groupStatement([null, {}, { tag: "p" }]), empty);
});

test("labels at the start of a line are cut out of example text", () => {
  assert.deepEqual(splitLabels("Input: s = \"a\"\nOutput: true\n"), [
    { label: "Input:" }, { text: " s = \"a\"\n" },
    { label: "Output:" }, { text: " true\n" },
  ]);
  assert.deepEqual(splitLabels("  Explanation : because"), [
    { text: "  " }, { label: "Explanation:" }, { text: " because" },
  ]);
});

test("blank lines before a label go, others stay", () => {
  assert.deepEqual(splitLabels("Input: x\n\n  \nOutput: y\n\nrest"), [
    { label: "Input:" }, { text: " x\n" },
    { label: "Output:" }, { text: " y\n\nrest" },
  ]);
});

test("text with no label at the start of a line is left whole", () => {
  assert.deepEqual(splitLabels(" nums = [1], the Output: is later"), [{ text: " nums = [1], the Output: is later" }]);
  assert.deepEqual(splitLabels(""), []);
  assert.deepEqual(splitLabels(null), []);
});
