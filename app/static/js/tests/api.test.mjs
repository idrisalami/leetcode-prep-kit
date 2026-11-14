// stream() error statuses, with fetch replaced by a fake. Run with: node --test app/static/js/tests/
import test from "node:test";
import assert from "node:assert/strict";
import { stream, ApiError } from "../api.js";

function fakeFetch(status, body, type) {
  globalThis.fetch = async () => new Response(body, { status, headers: { "Content-Type": type } });
}

async function errorOf(path) {
  let err = null;
  await stream(path, {}, { onError: (e) => { err = e; } });
  return err;
}

test("an error event inside the stream keeps its code and has status 0", async () => {
  fakeFetch(200, ": open\n\ndata: {\"delta\":\"Hi\"}\n\ndata: {\"error\":\"coach_failed\",\"detail\":\"The coach stopped.\"}\n\n",
    "text/event-stream");
  const err = await errorOf("/coach");
  assert.ok(err instanceof ApiError);
  assert.equal(err.status, 0);
  assert.equal(err.code, "coach_failed");
  assert.equal(err.detail, "The coach stopped.");
});

test("an HTTP failure before the stream opens keeps its real status", async () => {
  fakeFetch(409, JSON.stringify({ error: "busy", detail: "The coach is already answering." }), "application/json");
  const err = await errorOf("/coach");
  assert.equal(err.status, 409);
  assert.equal(err.code, "busy");
});
