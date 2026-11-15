// Which coach is connected: reading the /api/setup/coach payload. No DOM in here, so node can
// test it. The coach runs through a command-line tool on the learner's own computer (Claude
// Code, or OpenAI Codex); the server looks for both and remembers which one was picked.
//
// A server from before this choice existed sends no `coach` payload. Everything here then
// falls back to what that server did: Claude Code, found or not.

/** Is this a coach payload ({choice, active, providers}) and not an error or an older answer? */
export function isCoachPayload(p) {
  return !!p && typeof p === "object" && "choice" in p
    && Array.isArray(p.providers) && p.providers.length > 0;
}

/** Show the welcome page first? Only while nothing has been picked yet. */
export function needsWelcome(p) {
  return isCoachPayload(p) && p.choice === null;
}

/**
 * One card per tool, in the server's order: [{key, label, command, found, installUrl,
 * recommended, connected}]. `connected` is the tool the learner picked; `recommended` marks
 * Claude Code, which the coaching rules were written for.
 */
export function cards(p) {
  if (!isCoachPayload(p)) return [];
  return p.providers.filter((x) => x && typeof x === "object" && x.key).map((x) => ({
    key: String(x.key),
    label: String(x.label || x.key),
    command: String(x.command || x.key),
    found: !!x.found,
    installUrl: typeof x.install_url === "string" ? x.install_url : "",
    recommended: x.key === "claude",
    connected: p.choice === x.key,
  }));
}

/**
 * Where the coach stands, from the `setup` part of the overview or of /api/setup/status:
 * {kind, label, command}. `kind` is "ready", "missing" (the tool is not on this computer) or
 * "none" (the learner chose to go without). `label` and `command` name the tool in use, or
 * are null when there is none to name.
 */
export function coachStatus(setup) {
  const c = setup && setup.coach;
  if (!isCoachPayload(c)) {
    return { kind: setup && setup.claude === false ? "missing" : "ready",
      label: "Claude Code", command: "claude" };
  }
  if (c.choice === "none") return { kind: "none", label: null, command: null };
  const a = cards(c).find((x) => x.key === c.active);
  if (!a) return { kind: "missing", label: null, command: null };
  return { kind: a.found ? "ready" : "missing", label: a.label, command: a.command };
}

/** The sentence a page shows when the coach cannot answer; "" when it can. */
export function unavailableText(status) {
  if (!status || status.kind === "ready") return "";
  if (status.kind === "none") return "No coach is connected.";
  if (status.label) return status.label + " was not found on this computer.";
  return "No coach tool was found on this computer.";
}

/** The menu's line for the coach: the tool's name, or "Not connected". */
export function navLabel(p) {
  if (!isCoachPayload(p) || p.choice === "none") return "Not connected";
  const a = cards(p).find((x) => x.key === p.active);
  return a && a.found ? a.label : "Not connected";
}

/** A `back` address from the welcome page's query: an in-app route, or "#/" for anything else. */
export function backHash(value) {
  const v = String(value || "");
  if (!/^\/[A-Za-z0-9/._?=&%-]*$/.test(v) || v.startsWith("//") || v.startsWith("/welcome")) return "#/";
  return "#" + v;
}
