// A tiny stand-in for DOMParser and document, just enough for ui.js sanitizeHtml to run in node.
// Not a test file itself (no .test.mjs suffix). It parses tags, attributes, text and comments;
// it does not decode entities or apply HTML's implied-end-tag rules, which the tests do not need.

const XHTML = "http://www.w3.org/1999/xhtml";
const VOID = new Set(["area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
  "source", "track", "wbr"]);

class FakeNode {
  constructor(type, doc) { this.nodeType = type; this.ownerDocument = doc; this.parentNode = null; this.childNodes = []; }
  appendChild(child) {
    if (child.nodeType === 11) { for (const c of [...child.childNodes]) this.appendChild(c); return child; }
    if (child.parentNode) child.parentNode._drop(child);
    child.parentNode = this;
    this.childNodes.push(child);
    return child;
  }
  _drop(child) {
    const i = this.childNodes.indexOf(child);
    if (i !== -1) this.childNodes.splice(i, 1);
    child.parentNode = null;
  }
  remove() { if (this.parentNode) this.parentNode._drop(this); }
  replaceWith(...nodes) {
    const parent = this.parentNode;
    if (!parent) return;
    for (const n of nodes) if (n.parentNode) n.parentNode._drop(n);
    const i = parent.childNodes.indexOf(this);
    parent.childNodes.splice(i, 1, ...nodes);
    for (const n of nodes) n.parentNode = parent;
    this.parentNode = null;
  }
  get textContent() {
    if (this.nodeType === 3) return this.data;
    return this.childNodes.map((c) => (c.nodeType === 8 ? "" : c.textContent)).join("");
  }
}

class FakeElement extends FakeNode {
  constructor(tag, doc) { super(1, doc); this.localName = tag; this.namespaceURI = XHTML; this.attributes = []; }
  getAttribute(n) { const a = this.attributes.find((x) => x.name === n); return a ? a.value : null; }
  hasAttribute(n) { return this.attributes.some((x) => x.name === n); }
  setAttribute(n, v) {
    const a = this.attributes.find((x) => x.name === n);
    if (a) a.value = String(v); else this.attributes.push({ name: n, value: String(v) });
  }
  removeAttribute(n) { this.attributes = this.attributes.filter((x) => x.name !== n); }
}

class FakeDocument extends FakeNode {
  constructor() { super(9, null); this.ownerDocument = this; this.body = new FakeElement("body", this); }
  createTextNode(text) { const t = new FakeNode(3, this); t.data = String(text); return t; }
  createElement(tag) { return new FakeElement(tag, this); }
  createDocumentFragment() { return new FakeNode(11, this); }
  adoptNode(node) {
    if (node.parentNode) node.parentNode._drop(node);
    const walk = (n) => { n.ownerDocument = this; n.childNodes.forEach(walk); };
    walk(node);
    this.adopted.push(node);
    return node;
  }
}

const ATTR = /([^\s"'>\/=]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+)))?/g;

function parseInto(doc, html) {
  const stack = [doc.body];
  const top = () => stack[stack.length - 1];
  const re = /<!--([\s\S]*?)-->|<!doctype[^>]*>|<\/([a-zA-Z][\w-]*)\s*>|<([a-zA-Z][\w-]*)((?:[^>"']|"[^"]*"|'[^']*')*)>|([^<]+|<)/gi;
  let m;
  while ((m = re.exec(html))) {
    if (m[1] !== undefined) {
      const c = new FakeNode(8, doc); c.data = m[1]; top().appendChild(c);
    } else if (m[2]) {
      const tag = m[2].toLowerCase();
      if (tag === "html" || tag === "body") continue;
      for (let i = stack.length - 1; i > 0; i--) {
        if (stack[i].localName === tag) { stack.length = i; break; }
      }
    } else if (m[3]) {
      const tag = m[3].toLowerCase();
      if (tag === "html" || tag === "body") continue;
      const el = doc.createElement(tag);
      let a;
      ATTR.lastIndex = 0;
      while ((a = ATTR.exec(m[4] || ""))) {
        el.setAttribute(a[1].toLowerCase(), a[2] ?? a[3] ?? a[4] ?? "");
      }
      top().appendChild(el);
      if (!VOID.has(tag) && !/\/\s*$/.test(m[4] || "")) stack.push(el);
    } else if (m[5] !== undefined && m[5] !== "") {
      top().appendChild(doc.createTextNode(m[5]));
    }
  }
}

/** Install DOMParser and document on globalThis. Returns the live document; `.adopted` lists every adopted node. */
export function installFakeDom() {
  const live = new FakeDocument();
  live.adopted = [];
  globalThis.document = live;
  globalThis.DOMParser = class {
    parseFromString(html) { const d = new FakeDocument(); d.adopted = []; parseInto(d, String(html)); return d; }
  };
  return live;
}

/** Every element with this tag name under `node`, the node included. */
export function findAll(node, tag) {
  const out = [];
  const walk = (n) => { if (n.nodeType === 1 && n.localName === tag) out.push(n); n.childNodes.forEach(walk); };
  walk(node);
  return out;
}
