// Pure helpers from ui.js. Run with: node --test app/static/js/tests/
import test from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { isSafeUrl, fmtDuration, fmtDate, statusLabel, allowAttr, sanitizeHtml, readJson, writeJson, createBeatCredit } from "../ui.js";
import { installFakeDom, findAll } from "./fake-dom.mjs";

const { marked } = createRequire(import.meta.url)("../../vendor/marked/marked.min.js");

function sanitized(html, opts) {
  const live = installFakeDom();
  const frag = sanitizeHtml(html, opts);
  return { frag, live, imgs: findAll(frag, "img"), adoptedImgs: live.adopted.flatMap((n) => findAll(n, "img")) };
}

test("sanitizeHtml with images:false leaves no img from a raw <img onerror>, before adoption", () => {
  const r = sanitized('<p>see <img src=x onerror="alert(1)" alt="the tree"> here</p>', { images: false });
  assert.equal(r.imgs.length, 0);
  assert.equal(r.adoptedImgs.length, 0, "no img node ever reaches the live document");
  assert.equal(r.frag.textContent, "see the tree here", "the image becomes its alt text");
});

test("sanitizeHtml with images:false strips a Markdown image rendered by marked", () => {
  const html = marked.parse("look ![a](http://127.0.0.1:8793/probe.png) now", { gfm: true, async: false });
  assert.match(html, /<img/, "marked does make an img, so the test means something");
  const r = sanitized(html, { images: false });
  assert.equal(r.imgs.length, 0);
  assert.equal(r.adoptedImgs.length, 0);
  assert.equal(r.frag.textContent.trim(), "look a now");
});

test("sanitizeHtml with images:false drops picture, source, video and audio; no alt means no text", () => {
  const r = sanitized('<p>a<img src="http://x/1.png">b</p><picture><source srcset="http://x/2.png"><img src="http://x/3.png" alt="pic"></picture>' +
    '<video src="http://x/v.mp4" poster="http://x/p.png">v</video><audio src="http://x/a.mp3">au</audio>', { images: false });
  assert.equal(r.imgs.length, 0);
  for (const tag of ["picture", "source", "video", "audio"]) assert.equal(findAll(r.frag, tag).length, 0, tag);
  assert.equal(r.frag.textContent, "abpic");
});

test("sanitizeHtml keeps images by default (statements and course documents)", () => {
  const r = sanitized('<p><img src="https://assets.leetcode.com/t.png" alt="tree" onerror="x()"></p>');
  assert.equal(r.imgs.length, 1);
  assert.equal(r.imgs[0].getAttribute("alt"), "tree");
  assert.equal(r.imgs[0].getAttribute("onerror"), null);
  assert.equal(r.imgs[0].getAttribute("referrerpolicy"), "no-referrer");
});

test("readJson and writeJson round-trip through localStorage and survive bad data", () => {
  const store = new Map();
  globalThis.localStorage = {
    getItem: (k) => (store.has(k) ? store.get(k) : null),
    setItem: (k, v) => store.set(k, String(v)),
  };
  writeJson("k", { a: 1 });
  assert.deepEqual(readJson("k"), { a: 1 });
  assert.equal(readJson("missing"), null);
  store.set("bad", "{nope");
  assert.equal(readJson("bad"), null);
  globalThis.localStorage = { getItem: () => { throw new Error("blocked"); }, setItem: () => { throw new Error("full"); } };
  assert.equal(readJson("k"), null);
  writeJson("k", 1); // does not throw
  delete globalThis.localStorage;
});

test("isSafeUrl accepts http, https, mailto, relative and fragment references", () => {
  for (const url of [
    "https://leetcode.com/problems/two-sum/",
    "http://example.com",
    "HTTPS://EXAMPLE.COM",
    "mailto:someone@example.com",
    "#the-three-conditions",
    "00-before-you-start.md#counting-loops",
    "../reference/python-toolkit.md",
    "/static/x.png",
    "?a=1",
    "",
  ]) {
    assert.equal(isSafeUrl(url), true, url);
  }
});

test("isSafeUrl rejects script-capable and unknown schemes, however they are disguised", () => {
  for (const url of [
    "javascript:alert(1)",
    "JavaScript:alert(1)",
    "  javascript:alert(1)",
    "java\nscript:alert(1)",
    "java\tscript:alert(1)",
    "\u0000javascript:alert(1)",
    "vbscript:msgbox(1)",
    "data:text/html,<script>alert(1)</script>",
    "file:///etc/passwd",
    "blob:http://x/1",
  ]) {
    assert.equal(isSafeUrl(url), false, JSON.stringify(url));
  }
});

test("isSafeUrl rejects non-strings", () => {
  assert.equal(isSafeUrl(null), false);
  assert.equal(isSafeUrl(undefined), false);
  assert.equal(isSafeUrl(42), false);
});

test("fmtDuration reads as minutes, then hours with one decimal", () => {
  assert.equal(fmtDuration(0), "0 min");
  assert.equal(fmtDuration(1), "under 1 min");
  assert.equal(fmtDuration(20), "under 1 min");
  assert.equal(fmtDuration(59), "under 1 min");
  assert.equal(fmtDuration(60), "1 min");
  assert.equal(fmtDuration(9 * 60 + 29), "9 min");
  assert.equal(fmtDuration(59 * 60), "59 min");
  assert.equal(fmtDuration(3600), "1 h");
  assert.equal(fmtDuration(77400), "21.5 h");
  assert.equal(fmtDuration(-5), "0 min");
  assert.equal(fmtDuration(NaN), "0 min");
});

test("fmtDate gives day, short month and year; bad input gives an empty string", () => {
  assert.equal(fmtDate("2024-03-07"), "7 Mar 2024");
  assert.equal(fmtDate("2024-12-31T23:10:00"), "31 Dec 2024");
  assert.equal(fmtDate(""), "");
  assert.equal(fmtDate(null), "");
  assert.equal(fmtDate("not a date"), "");
});

test("statusLabel maps the three states to plain words", () => {
  assert.equal(statusLabel("solved"), "solved");
  assert.equal(statusLabel("attempted"), "in progress");
  assert.equal(statusLabel("new"), "not started");
  assert.equal(statusLabel(undefined), "not started");
});

test("allowAttr drops every author id and name, whatever the element", () => {
  assert.equal(allowAttr("img", "name", "getElementById"), null);
  assert.equal(allowAttr("img", "name", "body"), null);
  assert.equal(allowAttr("a", "name", "top"), null);
  assert.equal(allowAttr("h2", "id", "intro"), null);
  assert.equal(allowAttr("div", "id", "main"), null);
  assert.equal(allowAttr("img", "ID", "x"), null);
});

test("allowAttr keeps class only as language tokens on code and pre", () => {
  assert.equal(allowAttr("code", "class", "language-python"), "language-python");
  assert.equal(allowAttr("pre", "class", "language-c++ hljs"), "language-c++");
  assert.equal(allowAttr("code", "class", "Language-Python"), "language-python");
  assert.equal(allowAttr("code", "class", "toasts"), null);
  assert.equal(allowAttr("div", "class", "toasts"), null);
  assert.equal(allowAttr("a", "class", "nav-link on"), null);
  assert.equal(allowAttr("span", "class", "language-python"), null);
});

test("allowAttr keeps safe plain attributes and checks URLs", () => {
  assert.equal(allowAttr("a", "href", "https://leetcode.com/problems/two-sum/"), "https://leetcode.com/problems/two-sum/");
  assert.equal(allowAttr("a", "href", "javascript:alert(1)"), null);
  assert.equal(allowAttr("img", "src", " java\tscript:x"), null);
  assert.equal(allowAttr("img", "alt", "a tree"), "a tree");
  assert.equal(allowAttr("td", "colspan", "2"), "2");
  assert.equal(allowAttr("img", "onerror", "alert(1)"), null);
  assert.equal(allowAttr("div", "style", "position:fixed"), null);
});

test("createBeatCredit: a plain beat credits the whole window", () => {
  const credit = createBeatCredit(30);
  assert.equal(credit.next(), 30);
  assert.equal(credit.next(), 30);
});

test("createBeatCredit: seconds a page already sent are not credited again by the next beat", () => {
  const credit = createBeatCredit(30);
  credit.took(11); // the practice page sent 11 s when the learner left it
  assert.equal(credit.next(), 19);
  assert.equal(credit.next(), 30); // only the one beat is shortened
});

test("createBeatCredit: several pages in one window add up, and a full window sends nothing", () => {
  const credit = createBeatCredit(30);
  credit.took(12);
  credit.took(18);
  assert.equal(credit.next(), 0);
  assert.equal(credit.next(), 30);
});

test("createBeatCredit: more than a window carries the rest over to the following beat", () => {
  const credit = createBeatCredit(30);
  credit.took(30);
  credit.took(10);
  assert.equal(credit.next(), 0);
  assert.equal(credit.next(), 20);
});

test("createBeatCredit: seconds given back after a failed submit are credited by the next beat, up to 60", () => {
  const credit = createBeatCredit(30);
  credit.took(14);
  credit.took(-14); // the submit failed, so nothing was credited
  assert.equal(credit.next(), 30);
  credit.took(-20); // given back after the beat that was shortened for them
  assert.equal(credit.next(), 50);
  credit.took(-45);
  assert.equal(credit.next(), 60); // the server takes at most 60 s per beat
  assert.equal(credit.next(), 45); // 30 + the 15 s that did not fit
});

test("createBeatCredit ignores values that are not whole seconds", () => {
  const credit = createBeatCredit(30);
  credit.took(NaN);
  credit.took("7");
  credit.took(2.5);
  assert.equal(credit.next(), 30);
});

test("createBeatCredit: a skipped beat drops what was taken in its window but keeps seconds given back", () => {
  const credit = createBeatCredit(30);
  credit.took(10);
  credit.skip(); // the tab was hidden at the beat, so that window is not credited at all
  assert.equal(credit.next(), 30);
  credit.took(-8);
  credit.skip();
  assert.equal(credit.next(), 38);
});
