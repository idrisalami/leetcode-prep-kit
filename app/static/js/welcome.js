// The welcome page (#/welcome): the first thing a new learner sees, and where the coach is
// changed later (the menu's "Coach" line). The server looks for the coach tools on this
// computer (Claude Code, OpenAI Codex); this page shows what it found and connects one.
// Nothing is typed here and no key or password is ever asked for: a tool is used through the
// account it is already signed in to.

import { get, post } from "./api.js";
import { h, clear, toast, emptyState } from "./ui.js";
import { navigate, setCoach } from "./main.js";
import { isCoachPayload, cards, backHash } from "./coachpick.js";

const ABOUT = {
  claude: "Anthropic's command-line tool. The coaching rules in this kit were written for it, "
    + "and its answers appear as they are written.",
  codex: "OpenAI's command-line tool. The coach works the same way; each answer arrives in one "
    + "piece when it is finished.",
};

const tick = () => h("span", { class: "wel-tick", "aria-hidden": "true" }, "✓");

export async function render(box, params) {
  document.title = "Welcome · LeetCode Prep";
  const back = backHash(params.query && params.query.back);
  const wrap = h("div", { class: "wel" });
  box.append(wrap);

  let data = null;
  try { data = await get("/setup/coach"); } catch (e) { data = null; }
  if (params.isStale()) return;
  if (!isCoachPayload(data)) {
    // A server started before this page existed is still running.
    wrap.append(h("div", { class: "brand wel-brand" }, "LeetCode Prep"),
      h("h1", null, "Choose your coach"),
      emptyState("This page needs the app to be started again. Stop it in its terminal "
        + "(Ctrl+C), run python3 app/server.py once more, then reload this page.",
      h("a", { class: "btn", href: "#/" }, "Go to Home")));
    return;
  }

  let busy = false;
  let note = "";
  let focusKey = "";

  async function reload() {
    try {
      const fresh = await get("/setup/coach");
      if (isCoachPayload(fresh)) data = fresh;
    } catch (e) { /* keep what is on screen */ }
  }

  async function choose(key, label) {
    if (busy) return;
    const first = data.choice === null;
    busy = true;
    draw();
    try {
      const res = await post("/setup/coach", { provider: key });
      if (params.isStale()) return;
      if (isCoachPayload(res)) data = res;
      setCoach(data);
      busy = false;
      const said = key === "none"
        ? (first ? "No coach for now. You can connect one later from the menu." : "The coach is disconnected.")
        : label + " is connected.";
      if (first) {
        toast(said);
        navigate(back);
        return;
      }
      note = said;
      focusKey = "back";
      draw();
    } catch (e) {
      if (params.isStale()) return;
      await reload();
      if (params.isStale()) return;
      busy = false;
      note = "";
      toast(e && e.detail ? e.detail : "The choice could not be saved.", { kind: "error" });
      draw();
    }
  }

  async function check() {
    if (busy) return;
    const before = cards(data).filter((c) => c.found).map((c) => c.key).join(",");
    busy = true;
    draw();
    await reload();
    if (params.isStale()) return;
    busy = false;
    setCoach(data);
    const now = cards(data).filter((c) => c.found);
    note = now.map((c) => c.key).join(",") === before ? "Checked again: nothing has changed."
      : now.length ? "Checked again: found " + now.map((c) => c.label).join(" and ") + "."
        : "Checked again: no coach tool was found.";
    focusKey = "check";
    draw();
  }

  function card(c, first, primaryKey) {
    const action = [];
    if (c.connected && c.found) {
      action.push(h("span", { class: "wel-on" }, tick(), "Connected"));
    } else if (c.found) {
      action.push(h("button", { class: "btn" + (c.key === primaryKey ? " btn-primary" : ""), type: "button",
        disabled: busy, onclick: () => choose(c.key, c.label) },
      (first ? "Connect " : "Switch to ") + c.label));
    } else {
      action.push(h("a", { class: "btn", href: c.installUrl, target: "_blank", rel: "noopener noreferrer" },
        "Get " + c.label),
      h("span", { class: "wel-hint" }, "Install it and sign in, then press Check again."));
    }
    return h("article", { class: "card wel-card" + (c.connected && c.found ? " wel-card-on" : "")
      + (c.found ? "" : " wel-card-off"), dataset: { coach: c.key } },
    h("div", { class: "wel-card-top" },
      h("h3", { class: "wel-name" }, c.label),
      c.recommended ? h("span", { class: "tag tag-next" }, "Recommended") : null),
    h("p", { class: "wel-status " + (c.found ? "wel-found" : "wel-missing") },
      h("span", { class: "wel-dot", "aria-hidden": "true" }),
      c.found ? "Found on this computer" : "Not found on this computer",
      c.connected && !c.found ? h("span", { class: "wel-lost" }, " (it was your coach)") : null),
    h("p", { class: "wel-about" }, ABOUT[c.key] || "A command-line coach tool."),
    h("p", { class: "wel-cmd" }, "Runs through the ", h("code", null, c.command), " command."),
    h("div", { class: "wel-action" }, action));
  }

  function draw() {
    const list = cards(data);
    const first = data.choice === null;
    const firstFound = list.find((c) => c.found);
    const primaryKey = first && firstFound ? firstFound.key : "";
    const none = data.choice === "none";
    clear(wrap);

    const checkBtn = h("button", { class: "btn btn-sm", type: "button", disabled: busy, onclick: check },
      busy ? "Checking…" : "Check again");
    const backLink = first ? null
      : h("a", { class: "btn btn-primary", href: back }, back === "#/" ? "Go to Home" : "Back to the app");

    wrap.append(
      h("div", { class: "brand wel-brand" }, "LeetCode Prep"),
      h("h1", { class: "wel-title" }, first ? "Welcome to LeetCode Prep" : "Your coach"),
      h("p", { class: "lede wel-lede" }, first
        ? "A course to read, a practice list to solve in the built-in editor, and a coach that "
          + "follows your progress. One choice before you start."
        : "Change the tool the coach runs through, or go without one."),
      h("section", { class: "wel-coach", "aria-labelledby": "wel-coach-title" },
        h("div", { class: "wel-coach-head" },
          h("div", { class: "wel-coach-text" },
            h("h2", { class: "wel-h2", id: "wel-coach-title" }, first ? "Connect your coach" : "Coach tools"),
            h("p", { class: "wel-sub" }, "The coach gives hints, reviews what you submit and builds "
              + "your plan. It runs through a command-line tool on this computer, on your own "
              + "account. The app never asks for a password or a key.")),
          checkBtn),
        h("div", { class: "wel-grid" }, list.map((c) => card(c, first, primaryKey))),
        h("p", { class: "wel-note", role: "status" }, note)),
      h("div", { class: "wel-foot" },
        none ? h("span", { class: "wel-on wel-on-none" }, tick(), "Going without a coach")
          : h("button", { class: "btn btn-quiet wel-skip", type: "button", disabled: busy,
            onclick: () => choose("none", "") }, first ? "Continue without a coach" : "Disconnect the coach"),
        h("p", { class: "wel-foot-text" }, "Lessons, the editor and the tests work without a coach. "
          + (first ? "You can connect one later from the menu." : "")),
        backLink),
    );
    // Native append() prints null as text, so the optional last line is added on its own.
    if (first) {
      wrap.append(h("p", { class: "wel-next" }, "Next, on Home: download the problem statements, set "
        + "up your plan with the coach, then take the diagnostic."));
    }

    if (focusKey === "check") checkBtn.focus({ preventScroll: true });
    else if (focusKey === "back" && backLink) backLink.focus({ preventScroll: true });
    focusKey = "";
  }

  draw();
}
