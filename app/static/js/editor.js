// The code editor: CodeMirror 5 (loaded globally by index.html) set up for Python with the
// workspace's key bindings. The pure helpers at the top never touch the DOM, so node can import
// this file for the unit tests.

// ---- pure helpers ---------------------------------------------------------------

/** True on macOS and iOS, where the shortcuts use Command instead of Ctrl. */
export function isMacPlatform(nav) {
  if (!nav) return false;
  const p = (nav.userAgentData && nav.userAgentData.platform) || nav.platform || "";
  return /mac|iphone|ipad|ipod/i.test(p);
}

/** The shortcut labels the page prints next to the buttons. */
export function keyLabels(mac) {
  return mac ? { run: "⌘↩", save: "⌘S", comment: "⌘/" }
    : { run: "Ctrl+Enter", save: "Ctrl+S", comment: "Ctrl+/" };
}

/** A 1-based line from the runner -> a 0-based editor line, or null when it is not in the file. */
export function clampLine(line, lineCount) {
  const n = Number(line);
  if (!Number.isInteger(n) || n < 1 || n > lineCount) return null;
  return n - 1;
}

/**
 * How many characters Backspace removes when `before` is the text between the start of the line
 * and the cursor. Inside the indentation (spaces only) it goes back to the previous indent stop,
 * so the four spaces a Tab typed leave in one press. 0 means: not in the indentation, the editor's
 * own Backspace handles it.
 */
export function indentBackspace(before, unit = 4) {
  const text = String(before || "");
  if (!text || /[^ ]/.test(text) || !(unit > 0)) return 0;
  return text.length % unit || unit;
}

// ---- the editor -------------------------------------------------------------------

/**
 * Build the editor inside `host`.
 *   value      the starting code of the first document
 *   docId      the id of that first document (the main solution tab)
 *   label      the accessible name of the editing area
 *   onChange() called after every user edit (not after setValue)
 *   onRun()    Cmd/Ctrl-Enter
 *   onSave()   Cmd/Ctrl-S
 * Tab indents (or inserts four spaces); Shift-Tab dedents. Backspace in the indentation removes a
 * whole indent step. Escape, then Tab, moves the focus out of the editor instead, so a keyboard
 * user is never trapped. Cmd/Ctrl-/ toggles a comment.
 * One editor shows several documents, one per solution tab: openDoc, showDoc and closeDoc manage
 * them, and getValue, setValue and markError take the id of the document they mean.
 * Returns {cm, getValue, setValue, focus, refresh, markError(line), clearError(), destroy}.
 */
export function createEditor(host, { value = "", label = "Code editor", docId = 1, onChange, onRun, onSave } = {}) {
  const CM = window.CodeMirror;
  const MODE = { name: "python", version: 3 };
  let escaped = false;
  const run = () => { if (onRun) onRun(); };
  const save = () => { if (onSave) onSave(); };
  const tab = (cm) => {
    if (escaped) { escaped = false; return CM.Pass; }
    if (cm.somethingSelected()) cm.indentSelection("add");
    else cm.execCommand("insertSoftTab");
    return undefined;
  };
  const untab = (cm) => {
    if (escaped) { escaped = false; return CM.Pass; }
    cm.indentSelection("subtract");
    return undefined;
  };
  // Backspace with every cursor in the indentation: each goes back to its previous indent stop.
  // Anything else (a selection, a cursor after code, a bracket pair) is left to the editor.
  const backspace = (cm) => {
    if (cm.somethingSelected()) return CM.Pass;
    const unit = cm.getOption("indentUnit");
    const cuts = [];
    for (const r of cm.listSelections()) {
      const n = indentBackspace(cm.getLine(r.head.line).slice(0, r.head.ch), unit);
      if (!n) return CM.Pass;
      cuts.push([CM.Pos(r.head.line, r.head.ch - n), CM.Pos(r.head.line, r.head.ch)]);
    }
    // Last cursor first, so the earlier positions stay valid.
    cm.operation(() => {
      for (let i = cuts.length - 1; i >= 0; i--) cm.replaceRange("", cuts[i][0], cuts[i][1], "+delete");
    });
    return undefined;
  };
  // A passed Tab would otherwise fall through to the "basic" map, whose Tab inserts a tab character
  // and whose Shift-Tab re-indents. Without them, nothing handles it and the browser moves the focus.
  if (!CM.keyMap.prepBasic) {
    const basic = { ...CM.keyMap.basic };
    delete basic.Tab;
    delete basic["Shift-Tab"];
    CM.keyMap.prepBasic = basic;
    CM.keyMap.prep = { ...CM.keyMap.default, fallthrough: "prepBasic" };
  }
  const cm = CM(host, {
    value,
    keyMap: "prep",
    mode: MODE,
    theme: "prep",
    lineNumbers: true,
    indentUnit: 4,
    tabSize: 4,
    indentWithTabs: false,
    smartIndent: true,
    matchBrackets: true,
    autoCloseBrackets: true,
    styleActiveLine: true,
    screenReaderLabel: label,
    extraKeys: {
      Tab: tab,
      "Shift-Tab": untab,
      Backspace: backspace,
      "Shift-Backspace": backspace,
      Esc: () => { escaped = true; return CM.Pass; },
      "Cmd-Enter": run, "Ctrl-Enter": run,
      "Cmd-S": save, "Ctrl-S": save,
      "Cmd-/": "toggleComment", "Ctrl-/": "toggleComment",
    },
  });
  // Any key other than Escape (or the Tab right after it) ends the "leave the editor" mode.
  cm.on("keydown", (_cm, e) => {
    if (e.key !== "Escape" && e.key !== "Tab" && e.key !== "Shift") escaped = false;
  });
  cm.on("blur", () => { escaped = false; });
  cm.on("changes", (_cm, changes) => {
    if (!onChange) return;
    if (changes.every((c) => c.origin === "setValue")) return;
    onChange();
  });

  // One document per tab: each keeps its own text, cursor, scroll position and undo history.
  const docs = new Map([[docId, cm.getDoc()]]);
  let current = docId;
  const docOf = (id) => docs.get(id === undefined ? current : id) || null;

  let marked = null; // {doc, handle}: the one error line, in whichever document it was found
  const clearError = () => {
    if (marked !== null) {
      marked.doc.removeLineClass(marked.handle, "background", "cm-err-line");
      marked.doc.removeLineClass(marked.handle, "gutter", "cm-err-gutter");
      marked = null;
    }
  };
  return {
    cm,
    /** The text of document `id` (the one on screen when left out); "" for an unknown id. */
    getValue: (id) => { const doc = docOf(id); return doc ? doc.getValue() : ""; },
    setValue(text, id) {
      const doc = docOf(id);
      if (!doc) return;
      if (marked && marked.doc === doc) clearError();
      doc.setValue(text);
      doc.clearHistory();
    },
    has: (id) => docs.has(id),
    get current() { return current; },
    /** Add document `id` with `text`, or replace its text when it is already there. */
    openDoc(id, text = "") {
      if (docs.has(id)) this.setValue(text, id);
      else docs.set(id, new CM.Doc(text, MODE));
    },
    /** Put document `id` on screen. Returns false for an unknown id. */
    showDoc(id) {
      const doc = docs.get(id);
      if (!doc) return false;
      if (id !== current) {
        cm.swapDoc(doc);
        current = id;
      }
      return true;
    },
    /** Drop document `id`. The one on screen cannot be dropped: show another first. */
    closeDoc(id) {
      const doc = docs.get(id);
      if (!doc || id === current) return false;
      if (marked && marked.doc === doc) clearError();
      docs.delete(id);
      return true;
    },
    setLabel: (text) => cm.setOption("screenReaderLabel", text),
    focus: () => cm.focus(),
    refresh: () => cm.refresh(),
    /** Mark the 1-based line of the user's code in document `id`; true when the line exists. */
    markError(line, id) {
      clearError();
      const doc = docOf(id);
      if (!doc) return false;
      const at = clampLine(line, doc.lineCount());
      if (at === null) return false;
      const handle = doc.getLineHandle(at);
      doc.addLineClass(handle, "background", "cm-err-line");
      doc.addLineClass(handle, "gutter", "cm-err-gutter");
      marked = { doc, handle };
      if (doc === cm.getDoc()) cm.scrollIntoView({ line: at, ch: 0 }, 40);
      return true;
    },
    clearError,
    destroy() {
      const el = cm.getWrapperElement();
      if (el && el.parentNode) el.parentNode.removeChild(el);
    },
  };
}
