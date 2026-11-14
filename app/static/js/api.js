// The one place that talks to the local server. Every call is same-origin under /api/.

/** A failed request: HTTP status, the server's error code and its human-readable detail. */
export class ApiError extends Error {
  constructor(status, code, detail) {
    super(detail || code || "Request failed (" + status + ")");
    this.name = "ApiError";
    this.status = status;
    this.code = code || "error";
    this.detail = detail || this.message;
  }
}

async function request(method, path, body, signal, keepalive) {
  const opts = { method, headers: { Accept: "application/json" }, signal };
  if (keepalive) opts.keepalive = true;
  if (body !== undefined) {
    opts.headers["Content-Type"] = "application/json";
    opts.body = JSON.stringify(body);
  }
  let res;
  try {
    res = await fetch("/api" + path, opts);
  } catch (e) {
    if (e && e.name === "AbortError") throw e;
    throw new ApiError(0, "offline", "The app's server is not answering. Is it still running?");
  }
  let data = null;
  const text = await res.text();
  if (text) {
    try { data = JSON.parse(text); } catch (e) { data = null; }
  }
  if (!res.ok) {
    throw new ApiError(res.status, data && data.error, data && data.detail);
  }
  return data;
}

/** GET /api<path> -> parsed JSON. Throws ApiError. */
export function get(path, { signal } = {}) {
  return request("GET", path, undefined, signal);
}

/**
 * POST /api<path> with a JSON body -> parsed JSON. Throws ApiError. `keepalive` lets the request
 * outlive the page (the leave-page heartbeat).
 */
export function post(path, body = {}, { signal, keepalive = false } = {}) {
  return request("POST", path, body, signal, keepalive);
}

/**
 * PUT /api<path> with a JSON body -> parsed JSON. Throws ApiError. `keepalive` lets the request
 * outlive the page (a save on pagehide); browsers cap such bodies at about 64 KB.
 */
export function put(path, body = {}, { signal, keepalive = false } = {}) {
  return request("PUT", path, body, signal, keepalive);
}

/**
 * POST and read a server-sent event stream (the coach). Each `data:` line holds JSON:
 * {delta} -> onDelta(text), {done, text} -> onDone(text), {error, detail} -> onError(ApiError
 * with status 0 and the event's code). An HTTP failure before the stream opens keeps its status
 * (409 busy).
 * Comment lines (": open", ": ping") are ignored. Aborting `signal` stops quietly.
 * Resolves when the stream ends.
 */
export async function stream(path, body, { onDelta, onDone, onError, signal } = {}) {
  const fail = (err) => { if (onError) onError(err); };
  let res;
  try {
    res = await fetch("/api" + path, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
      body: JSON.stringify(body || {}),
      signal,
    });
  } catch (e) {
    if (e && e.name === "AbortError") return;
    fail(new ApiError(0, "offline", "The app's server is not answering. Is it still running?"));
    return;
  }
  if (!res.ok) {
    let data = null;
    try { data = await res.json(); } catch (e) { data = null; }
    fail(new ApiError(res.status, data && data.error, data && data.detail));
    return;
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let finished = false;
  const handle = (block) => {
    const lines = block.split("\n").filter((l) => l.startsWith("data:"));
    if (!lines.length) return;
    let ev;
    try { ev = JSON.parse(lines.map((l) => l.slice(5).trimStart()).join("\n")); } catch (e) { return; }
    if (typeof ev.delta === "string") { if (onDelta) onDelta(ev.delta); }
    else if (ev.done) { finished = true; if (onDone) onDone(ev.text || ""); }
    else if (ev.error) { finished = true; fail(new ApiError(0, ev.error, ev.detail)); }
  };
  try {
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, "\n");
      let at;
      while ((at = buffer.indexOf("\n\n")) !== -1) {
        handle(buffer.slice(0, at));
        buffer = buffer.slice(at + 2);
      }
    }
    if (buffer.trim()) handle(buffer);
  } catch (e) {
    if (e && e.name === "AbortError") return;
    fail(new ApiError(0, "stream", "The coach's answer was cut off."));
    return;
  }
  if (!finished) fail(new ApiError(0, "stream", "The coach stopped without an answer."));
}
