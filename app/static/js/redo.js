// "Redo" for a solved problem, shared by the problem browser and the module reader: ask first,
// POST /redo, then open the workspace. main.js is imported lazily (it touches `document` on
// import), so node can import redoFailure for the tests.

import { post } from "./api.js";
import { h, toast, confirmDialog } from "./ui.js";

/**
 * What a failed redo means for the user: {open, text}. A 409 not_solved (the problem lost its
 * solved mark since the page loaded) still opens the workspace, as it is; anything else stays.
 */
export function redoFailure(err, title) {
  if (err && err.code === "not_solved") {
    return { open: true, kind: "info",
      text: title + " is not solved yet, so there is nothing to redo. Opening it as it is." };
  }
  return { open: false, kind: "error", text: (err && err.detail) || "Could not start it again." };
}

/** The one question both Redo buttons ask. What it clears and what it keeps. */
export function redoQuestion(title) {
  return "Start " + title + " again from the skeleton? The code, the four boxes and the coach chat are cleared. "
    + "Your time and past submits stay.";
}

/**
 * The Redo button for problem `p`. `attrs` go on the button (class, aria-label); `onOpen` runs
 * just before the workspace opens (the browser records the problem as opened).
 */
export function redoButton(p, { attrs = {}, label = "Redo", isStale = () => false, onOpen = null } = {}) {
  const btn = h("button", { class: "btn btn-sm", type: "button", ...attrs }, label);
  btn.addEventListener("click", async () => {
    const ok = await confirmDialog(redoQuestion(p.title), { confirm: "Start again", focus: "cancel" });
    if (!ok || isStale()) return;
    btn.disabled = true;
    let failure = null;
    try {
      await post("/problem/" + p.slug + "/redo", {});
    } catch (e) {
      failure = redoFailure(e, p.title);
    }
    if (isStale()) return;
    const { navigate, refreshNav } = await import("./main.js");
    if (isStale()) return;
    if (failure && !failure.open) {
      btn.disabled = false;
      toast(failure.text, { kind: failure.kind });
      return;
    }
    if (failure) {
      toast(failure.text);
      // The page's data is out of date: refresh the nav counts now; the list itself is fetched
      // again when the user comes back to it.
      refreshNav();
    }
    if (onOpen) onOpen();
    navigate("#/practice/" + p.slug);
  });
  return btn;
}
