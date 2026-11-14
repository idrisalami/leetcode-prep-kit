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

// ---- the editor -------------------------------------------------------------------

/**
 * Build the editor inside `host`.
 *   value      the starting code
 *   label      the accessible name of the editing area
 *   onChange() called after every user edit (not after setValue)
 *   onRun()    Cmd/Ctrl-Enter
 *   onSave()   Cmd/Ctrl-S
 * Tab indents (or inserts four spaces); Shift-Tab dedents. Escape, then Tab, moves the focus out
 * of the editor instead, so a keyboard user is never trapped. Cmd/Ctrl-/ toggles a comment.
 * Returns {cm, getValue, setValue, focus, refresh, markError(line), clearError(), destroy}.
 */
export function createEditor(host, { value = "", label = "Code editor", onChange, onRun, onSave } = {}) {
  const CM = window.CodeMirror;
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
    mode: { name: "python", version: 3 },
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

  let marked = null;
  const clearError = () => {
    if (marked !== null) {
      cm.removeLineClass(marked, "background", "cm-err-line");
      cm.removeLineClass(marked, "gutter", "cm-err-gutter");
      marked = null;
    }
  };
  return {
    cm,
    getValue: () => cm.getValue(),
    setValue: (text) => { clearError(); cm.setValue(text); cm.clearHistory(); },
    focus: () => cm.focus(),
    refresh: () => cm.refresh(),
    /** Mark the 1-based line of the user's code; returns true when the line exists. */
    markError(line) {
      clearError();
      const at = clampLine(line, cm.lineCount());
      if (at === null) return false;
      marked = cm.getLineHandle(at);
      cm.addLineClass(marked, "background", "cm-err-line");
      cm.addLineClass(marked, "gutter", "cm-err-gutter");
      cm.scrollIntoView({ line: at, ch: 0 }, 40);
      return true;
    },
    clearError,
    destroy() {
      const el = cm.getWrapperElement();
      if (el && el.parentNode) el.parentNode.removeChild(el);
    },
  };
}
