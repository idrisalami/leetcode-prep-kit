// The star toggle: mark a problem to find it again. Used by the problem browser and the
// practice page. The star is saved by the app's server (POST /api/problem/<slug>/star), next
// to the rest of the progress, so it follows the kit folder and not the browser.
//
// The button shows the new state at once and goes back if the save fails.

import { post } from "./api.js";
import { h, toast } from "./ui.js";

/** What to tell the user when a star could not be saved. */
export function starFailure(e) {
  // A 404 here means the page is newer than the running server: the route does not exist yet.
  if (e && e.status === 404) {
    return "Could not save the star. Stop the app (Ctrl+C), start it again with "
      + "python3 app/server.py, and try again.";
  }
  return "Could not save the star. " + ((e && e.detail) || "The app's server did not answer.");
}

/**
 * A star button for `p` ({slug, title, starred}). `onChange(on)` runs after a save that
 * changed the state; `p.starred` is updated first, so a caller can repaint from its own list.
 */
export function starButton(p, { onChange, isStale, cls = "" } = {}) {
  let on = !!p.starred;
  let busy = false;
  const icon = h("span", { class: "star-icon", "aria-hidden": "true" });
  const b = h("button", { class: "star-btn" + (cls ? " " + cls : ""), type: "button",
    "aria-label": "Star: " + p.title, dataset: { slug: p.slug } }, icon);
  const paint = () => {
    b.setAttribute("aria-pressed", String(on));
    b.title = on ? "Remove the star" : "Star this problem";
    icon.textContent = on ? "★" : "☆";
  };
  paint();
  b.addEventListener("click", async () => {
    if (busy) return;
    busy = true;
    const want = !on;
    on = want;
    paint();
    let saved = false;
    try {
      const res = await post("/problem/" + p.slug + "/star", { starred: want });
      on = !!(res && res.starred);
      saved = true;
    } catch (e) {
      on = !want;
      if (!(isStale && isStale())) toast(starFailure(e), { kind: "error", ms: 7000 });
    }
    busy = false;
    p.starred = on;
    if (isStale && isStale()) return;
    paint();
    if (saved && onChange) onChange(on);
  });
  return b;
}
