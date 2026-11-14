"""The JSON API as a pure object: App.handle(method, path, query, headers, body) -> Response.

The HTTP server (app/server.py) is a thin adapter around this. Every /api/ request passes the
Host check; every non-GET request also passes the Content-Type and Origin checks.
"""
from __future__ import annotations

import json
import os
import re
import sys
import threading
import traceback
from datetime import datetime

from app.prep import catalog as catalog_mod
from app.prep import coach, course, notes, runner, statements, stats
from app.prep.store import MAX_HEARTBEAT, NOTE_KEYS, Store, WriteFailed

MAX_CODE = 200000
MAX_BODY = 2000000
COACH_IDLE_S = 15
MODULE_IDS = ["%02d" % i for i in range(0, 11)]
MATRIX_ROW_RE = re.compile(r"^A(\d+)$")
SLUG = r"([a-z0-9][a-z0-9-]*)"
JSON_TYPE = "application/json; charset=utf-8"


class Response:
    """stream, when set, is an iterable of bytes with close(); cancel, when set, is a
    threading.Event the server sets when the client goes away mid-stream."""

    def __init__(self, status, headers=None, body=None, stream=None, cancel=None):
        self.status = status
        self.headers = dict(headers or {})
        self.body = body
        self.stream = stream
        self.cancel = cancel
        self.headers.setdefault("X-Content-Type-Options", "nosniff")
        self.headers.setdefault("Cache-Control", "no-store")


def json_response(status, obj, headers=None):
    h = {"Content-Type": JSON_TYPE}
    h.update(headers or {})
    return Response(status, h, json.dumps(obj, ensure_ascii=False).encode("utf-8"))


class ApiError(Exception):
    """`extra` holds more keys for the error body, such as the current `rev` of a stale save."""

    def __init__(self, status, code, detail, headers=None, extra=None):
        Exception.__init__(self, detail)
        self.status = status
        self.code = code
        self.detail = detail
        self.headers = headers or {}
        self.extra = extra or {}


def bad(detail):
    return ApiError(400, "bad_request", detail)


def _sse(obj):
    return ("data: %s\n\n" % json.dumps(obj, ensure_ascii=False)).encode("utf-8")


STALE_DETAIL = "This problem changed in another tab. Reload to see the newer code."
BUSY_DETAIL = "The coach is already answering. Wait for that answer, or stop it, then try again."


class _Stream:
    """Wraps a generator and releases the coach slot exactly once: at its end or on close(),
    even when it was never started."""

    def __init__(self, gen, release):
        self._gen = gen
        self._release = release
        self._released = False

    def __iter__(self):
        return self

    def __next__(self):
        try:
            return next(self._gen)
        except BaseException:
            self.close()
            raise

    def close(self):
        try:
            self._gen.close()
        finally:
            if not self._released:
                self._released = True
                self._release()


def _floor_median(levels):
    s = sorted(levels)
    n = len(s)
    if n % 2:
        return s[n // 2]
    return (s[n // 2 - 1] + s[n // 2]) // 2


class App:
    def __init__(self, paths, port, coach_cmd=None, now=datetime.now, log=None):
        self.paths = paths
        self.port = port
        self.coach_cmd = list(coach_cmd) if coach_cmd else None
        self.now = now
        self.log = log if log is not None else sys.stderr
        self.created = notes.bootstrap(paths)
        self.store = Store(paths, now=now, log=self.log)
        self.catalog = catalog_mod.Catalog(paths)
        self.lock = threading.RLock()
        self.coach_idle = COACH_IDLE_S
        self.last_results = {}
        self.reviewing = set()
        self.coach_slot = threading.Lock()  # one coach process at a time, hints and reviews alike
        self.statements_error = None
        self.statements_opener = None
        self.statements_sleep = None
        self.statements_running = False
        self.statements_failed = []
        self.hosts = {"127.0.0.1:%d" % port, "localhost:%d" % port}
        self.origins = {"http://127.0.0.1:%d" % port, "http://localhost:%d" % port}
        self.routes = [
            (r"/api/overview", {"GET": self.overview}),
            (r"/api/warmup/another", {"POST": self.warmup_another}),
            (r"/api/problems", {"GET": self.problems}),
            (r"/api/problem/%s" % SLUG, {"GET": self.problem}),
            (r"/api/problem/%s/draft" % SLUG, {"PUT": self.draft}),
            (r"/api/problem/%s/run" % SLUG, {"POST": self.run}),
            (r"/api/problem/%s/submit" % SLUG, {"POST": self.submit}),
            (r"/api/problem/%s/coach" % SLUG, {"POST": self.coach}),
            (r"/api/problem/%s/review" % SLUG, {"POST": self.review}),
            (r"/api/problem/%s/reset" % SLUG, {"POST": self.reset}),
            (r"/api/problem/%s/redo" % SLUG, {"POST": self.redo}),
            (r"/api/heartbeat", {"POST": self.heartbeat}),
            (r"/api/course", {"GET": self.course}),
            (r"/api/doc", {"GET": self.doc}),
            (r"/api/module/(\d\d)/read", {"POST": self.module_read}),
            (r"/api/matrix", {"GET": self.matrix}),
            (r"/api/setup/statements", {"POST": self.setup_statements}),
            (r"/api/setup/status", {"GET": self.setup_status}),
        ]
        self.routes = [(re.compile("^%s$" % pat), methods) for pat, methods in self.routes]

    # ---- start-up -------------------------------------------------------

    def startup_lines(self):
        lines = []
        rec = self.store.recovered
        if rec:
            if "state.json.broken-" in rec and not rec.startswith("could not"):
                lines.append("The saved state.json was broken, so it was set aside as %s and a "
                             "fresh one was started." % rec)
            else:
                lines.append("The saved state.json was broken: %s." % rec)
        if self.created:
            lines.append("Created in my-prep: %s" % ", ".join(self.created))
        return lines

    def notices(self):
        """What Home must tell the learner: a failed save, and a state file set aside at start
        (that one lasts as long as the server runs)."""
        out = []
        err = self.store.save_error
        if err:
            out.append({"kind": "save_error", "text": err})
        rec = self.store.recovered
        if rec:
            if "state.json.broken-" in rec and not rec.startswith("could not"):
                text = ("Your saved progress could not be read and was set aside as %s. The app "
                        "started with empty progress." % os.path.basename(rec))
            else:
                text = ("Your saved progress could not be read, and it could not be set aside "
                        "either. The app started with empty progress.")
            out.append({"kind": "state_recovered", "text": text})
        return out

    def shutdown(self):
        """Kill any live coach process group and remove its folder."""
        coach.kill_all()

    # ---- dispatch -------------------------------------------------------

    def handle(self, method, path, query, headers, body):
        resp = self._answer(method, path, query, headers, body)
        err = self.store.save_error
        if err and method != "GET" and resp.stream is None and resp.body \
                and resp.headers.get("Content-Type") == JSON_TYPE:
            try:
                out = json.loads(resp.body.decode("utf-8"))
            except ValueError:
                out = None
            if isinstance(out, dict):
                out["save_error"] = err
                resp.body = json.dumps(out, ensure_ascii=False).encode("utf-8")
        return resp

    def _answer(self, method, path, query, headers, body):
        try:
            return self._handle(method, path, query or {}, headers or {}, body or b"")
        except ApiError as exc:
            body = dict(exc.extra)
            body.update(error=exc.code, detail=exc.detail)
            return json_response(exc.status, body, exc.headers)
        except WriteFailed as exc:
            return json_response(500, {"error": "write_failed",
                                       "detail": "Could not write %s: %s." % (exc.rel_path, exc.reason)})
        except ValueError as exc:
            return json_response(400, {"error": "bad_request", "detail": str(exc) or "Bad request."})
        except Exception as exc:
            try:
                self.log.write(traceback.format_exc())
                self.log.flush()
            except Exception:
                pass
            return json_response(500, {"error": "internal",
                                       "detail": "%s: %s" % (type(exc).__name__, exc)})

    def _handle(self, method, path, query, headers, body):
        h = {str(k).lower(): v for k, v in headers.items() if v is not None}
        if not path.startswith("/api/"):
            raise ApiError(404, "not_found", "Nothing at %s." % path)
        if str(h.get("host", "")).lower() not in self.hosts:
            raise ApiError(403, "forbidden", "The API answers only to 127.0.0.1:%d or localhost:%d."
                           % (self.port, self.port))
        for pattern, methods in self.routes:
            match = pattern.match(path)
            if not match:
                continue
            if method not in methods:
                allow = ", ".join(sorted(methods))
                raise ApiError(405, "method_not_allowed", "Use %s for %s." % (allow, path),
                               {"Allow": allow})
            args = match.groups()
            if method != "GET":
                self._check_write(h)
                data = self._parse(body)
            else:
                data = {}
            return methods[method](*args, query=query, data=data)
        raise ApiError(404, "not_found", "No API route at %s." % path)

    def _check_write(self, h):
        ctype = str(h.get("content-type", "")).split(";")[0].strip().lower()
        if ctype != "application/json":
            raise ApiError(403, "forbidden", "Requests that change things must send JSON.")
        origin = h.get("origin")
        if origin is not None and str(origin).lower() not in self.origins:
            raise ApiError(403, "forbidden", "Requests from %s are not accepted." % origin)

    @staticmethod
    def _parse(body):
        if len(body) > MAX_BODY:
            raise ApiError(413, "too_large", "The request body is too large.")
        try:
            data = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, ValueError, RecursionError):
            raise bad("The body is not valid JSON.")
        if not isinstance(data, dict):
            raise bad("The body must be a JSON object.")
        return data

    # ---- helpers --------------------------------------------------------

    def _today(self):
        return self.now().date()

    def _problem(self, slug):
        try:
            return self.catalog.get(slug)
        except KeyError:
            raise ApiError(404, "not_found", "There is no problem called %s." % slug)

    def _titles(self):
        titles = {m["id"]: m["title"] for m in course.modules(self.paths)}
        for mid in MODULE_IDS:
            titles.setdefault(mid, "Module %s" % mid)
        return titles

    @staticmethod
    def _code(data, required):
        code = data.get("code")
        if code is None:
            if required:
                raise bad("The body needs the code as a string.")
            return None
        if not isinstance(code, str):
            raise bad("code must be a string.")
        if len(code) > MAX_CODE:
            raise ApiError(413, "too_large", "The code is longer than %d characters." % MAX_CODE)
        return code

    @staticmethod
    def _notes(data):
        value = data.get("notes")
        if value is None:
            return None
        if not isinstance(value, dict):
            raise bad("notes must be an object.")
        for key, text in value.items():
            if not isinstance(text, str):
                raise bad("The note %s must be a string." % key)
            if len(text) > MAX_CODE:
                raise ApiError(413, "too_large", "The note %s is too long." % key)
        return value

    @staticmethod
    def _base_rev(data):
        """The optional `base_rev` of a save: the rev the page loaded. None when absent."""
        value = data.get("base_rev")
        if value is None:
            return None
        if isinstance(value, bool) or not isinstance(value, int):
            raise bad("base_rev must be a whole number.")
        return value

    def _check_rev(self, slug, base_rev):
        """409 stale when the page's rev is not the stored one. Caller holds self.lock."""
        if base_rev is not None:
            current = self.store.rev(slug)
            if base_rev != current:
                raise ApiError(409, "stale", STALE_DETAIL, extra={"rev": current})

    def _save_changed(self, slug, problem, code, notes_in, base_rev=None):
        """Save the draft only when the code or a note differs from what is stored. A stale
        `base_rev` raises 409 before anything is written."""
        with self.lock:
            self._check_rev(slug, base_rev)
            stored = self.store.code(slug)
            current = stored if stored is not None else problem.get("skeleton", "")
            code_changed = code is not None and code != current
            old = self.store.problem(slug)["notes"]
            notes_changed = bool(notes_in) and any(
                isinstance(notes_in.get(k), str) and notes_in[k] != old.get(k, "")
                for k in NOTE_KEYS)
            if code_changed or notes_changed:
                self.store.save_draft(slug, code if code_changed else None,
                                      notes_in if notes_changed else None)

    def _statement(self, slug):
        data = self.catalog.statement(slug)
        if not statements.valid(data):
            return None
        return {"format": data["format"], "body": data["body"]}

    def _statements_have(self):
        return sum(1 for p in self.catalog.problems() if statements.have(self.paths, p["slug"]))

    @staticmethod
    def _summary(kind, result):
        failing = [{k: r.get(k) for k in ("name", "status", "input", "expected", "got", "message")}
                   for r in result.get("results") or [] if r.get("status") != "pass"]
        return {"kind": kind, "passed": result.get("passed", 0), "total": result.get("total", 0),
                "fatal": result.get("fatal"), "failing": failing}

    def _context(self, slug, problem, entry, code=None, message=""):
        stored = self.store.code(slug)
        if code is None:
            code = stored if stored is not None else problem.get("skeleton", "")
        return {"title": problem["title"], "number": problem.get("number"),
                "difficulty": problem.get("difficulty"), "statement": self._statement(slug),
                "code": code, "notes": entry.get("notes") or {},
                "results": self.last_results.get(slug), "chat": entry.get("chat") or [],
                "top_bugs": notes.top_bugs(self.paths), "message": message}

    def _warmup(self, another=False):
        pick = stats.warmup(self.store, self.catalog, self._today(), another=another)
        if not pick.get("slug"):
            return None
        p = self.catalog.get(pick["slug"])
        return {"slug": p["slug"], "title": p["title"], "difficulty": p["difficulty"],
                "module": p["module"], "module_title": self._titles().get(p["module"], ""),
                "done": bool(pick.get("done"))}

    # ---- home -----------------------------------------------------------

    def overview(self, query, data):
        state = self.store.snapshot()
        today = self._today()
        titles = self._titles()
        read = state.get("modules_read") or {}
        modules = [{"id": m["id"], "title": titles[m["id"]], "solved": m["solved"],
                    "total": m["total"], "pct": m["pct"], "read": read.get(m["id"])}
                   for m in stats.module_progress(state, self.catalog)]
        modules.append({"id": "00", "title": titles["00"], "read": bool(read.get("00", False))})
        matrix = []
        for group in notes.read_matrix(self.paths):
            for row in group["rows"]:
                m = MATRIX_ROW_RE.match(row["id"])
                if m and 1 <= int(m.group(1)) <= 18:
                    matrix.append({"id": row["id"], "now": row["now"], "priority": row["priority"],
                                   "requirement": row["requirement"]})
        mistakes = [{"bug": b["bug"], "check": b["check"], "source": "bugs"}
                    for b in notes.top_bugs(self.paths)]
        if not mistakes:
            mistakes = [{"bug": e["title"], "check": e["rule"], "source": "learnings"}
                        for e in notes.recent_learnings(self.paths, 3)]
        current = stats.current_module(state, self.catalog)
        return json_response(200, {
            "day": stats.day_number(state, today),
            "current_module": {"id": current, "title": titles[current]},
            "warmup": self._warmup(),
            "kpis": stats.kpis(state, self.catalog, today),
            "modules": modules, "matrix": matrix, "mistakes": mistakes,
            "setup": {"statements_have": self._statements_have(),
                      "statements_total": len(self.catalog.problems()),
                      "claude": coach.available(self.coach_cmd)},
            "notices": self.notices()})

    def warmup_another(self, query, data):
        return json_response(200, {"warmup": self._warmup(another=True)})

    # ---- problems -------------------------------------------------------

    def problems(self, query, data):
        state = self.store.snapshot().get("problems") or {}
        titles = self._titles()
        out = []
        for p in self.catalog.problems():
            entry = state.get(p["slug"]) or {}
            row = {k: p.get(k) for k in ("slug", "number", "title", "difficulty", "module",
                                         "category", "url", "premium")}
            row.update(status=entry.get("status", "new"), seconds=entry.get("seconds", 0),
                       solved_at=entry.get("solved_at"), last_at=self._last_at(p["slug"], entry))
            out.append(row)
        return json_response(200, {"problems": out,
                                   "modules": [{"id": mid, "title": titles[mid]}
                                               for mid in self.catalog.module_ids()]})

    def _last_at(self, slug, entry):
        """The latest of: a submit, a chat turn, `touched_at` (the last draft save, notes-only
        too, run or submit) and the solution file's write time."""
        stamps = [r.get("at") for r in entry.get("submits") or [] if isinstance(r, dict)]
        stamps.append(entry.get("touched_at"))
        stamps += [r.get("at") for r in entry.get("chat") or [] if isinstance(r, dict)]
        stamps.append(self.store.draft_saved_at(slug))
        stamps = [s for s in stamps if isinstance(s, str) and s]
        return max(stamps) if stamps else None

    def problem(self, slug, query, data):
        p = self._problem(slug)
        entry = self.store.problem(slug)
        code = self.store.code(slug)
        out = dict(p)
        with self.lock:
            reviewing = set(self.reviewing)
        submits = []
        for rec in entry["submits"]:
            rec = dict(rec)
            rec["review_in_progress"] = (slug, rec.get("id")) in reviewing
            submits.append(rec)
        out.update(module_title=self._titles().get(p["module"], ""), status=entry["status"],
                   seconds=entry["seconds"], hints_used=entry["hints_used"],
                   submits=submits, code=code if code is not None else p.get("skeleton", ""),
                   notes=entry["notes"], chat=entry["chat"], examples=self.catalog.examples(slug),
                   statement=self._statement(slug), attempt=entry["attempt"],
                   solved_at=entry["solved_at"], first_try=entry["first_try"],
                   rev=self.store.rev(slug))
        return json_response(200, out)

    def draft(self, slug, query, data):
        p = self._problem(slug)
        code = self._code(data, required=False)
        notes_in = self._notes(data)
        self._save_changed(slug, p, code, notes_in, self._base_rev(data))
        return json_response(200, {"ok": True, "rev": self.store.rev(slug)})

    def run(self, slug, query, data):
        p = self._problem(slug)
        code = self._code(data, required=True)
        self._save_changed(slug, p, code, None, self._base_rev(data))
        result = runner.run(self.catalog.spec(slug), code, examples_only=True)
        self.store.record_run(slug)
        self.last_results[slug] = self._summary("run", result)
        out = dict(result)
        out["rev"] = self.store.rev(slug)
        return json_response(200, out)

    def submit(self, slug, query, data):
        p = self._problem(slug)
        code = self._code(data, required=True)
        notes_in = self._notes(data)
        base_rev = self._base_rev(data)
        elapsed = self._elapsed(data)
        with self.lock:
            self._save_changed(slug, p, code, notes_in, base_rev)
            if elapsed:
                self.store.add_seconds(slug, elapsed)
        result = runner.run(self.catalog.spec(slug), code, examples_only=False)
        with self.lock:
            record = self.store.record_submit(slug, result.get("passed", 0), result.get("total", 0))
            entry = self.store.problem(slug)
            same = [s for s in entry["submits"] if s.get("attempt", 1) == record["attempt"]]
            ids = [s.get("id") for s in same]
            n = ids.index(record["id"]) + 1 if record["id"] in ids else len(same)
            first_try = bool(record["ok"]) and n == 1
            matrix = self._update_matrix(p, entry, record, n)
        self.last_results[slug] = self._summary("submit", result)
        out = dict(result)
        out.update(solved=bool(record["ok"]), first_try=first_try, submit_id=record["id"],
                   matrix=matrix, rev=self.store.rev(slug))
        return json_response(200, out)

    @staticmethod
    def _elapsed(data):
        """Optional whole seconds since the page's last heartbeat, clamped to 0..MAX_HEARTBEAT."""
        value = data.get("elapsed")
        if value is None:
            return 0
        if isinstance(value, bool) or not isinstance(value, (int, float)) or value != value \
                or value < 0 or value in (float("inf"),):
            raise bad("elapsed must be a whole number of seconds, 0 or more.")
        return min(MAX_HEARTBEAT, int(value))

    def _evidence(self, p, record, n):
        if record["ok"]:
            how = "passes the app's tests, first try" if n == 1 else \
                "passes the app's tests after %d submits" % n
        else:
            how = "%d/%d of the app's tests pass" % (record["passed"], record["total"])
        hints = record.get("hints_used", 0)
        hint_text = "no hints" if not hints else "%d hint%s" % (hints, "" if hints == 1 else "s")
        return "LC %s %s: %s, in %s, %s (app)" % (p["number"], p["title"], how,
                                                  stats.minutes_text(record.get("seconds", 0)),
                                                  hint_text)

    def _update_matrix(self, p, entry, record, n):
        """One matrix row per submit, under the API lock; never lowers a level set by hand."""
        row_id = stats.matrix_row(p)
        if row_id is None:
            return None
        row = None
        for group in notes.read_matrix(self.paths):
            for r in group["rows"]:
                if r["id"] == row_id:
                    row = r
        if row is None:
            return None
        level = stats.rep_level(p, entry, record)
        levels = self.store.add_rep(row_id, p["slug"], record["attempt"], level)
        now = _floor_median(levels)
        cell = (row.get("now") or "").strip()
        written_before = self.store.matrix_written(row_id)
        keep = False
        if cell not in ("", "?") and cell != written_before:
            try:
                keep = now < int(cell)
            except ValueError:
                keep = True
        ok = notes.update_matrix_row(self.paths, row_id, None if keep else now,
                                     self._evidence(p, record, n), self._today().isoformat())
        written = bool(ok) and not keep
        if written:
            self.store.set_matrix_written(row_id, str(now))
        return {"row": row_id, "now": now, "written": written}

    def reset(self, slug, query, data):
        p = self._problem(slug)
        with self.lock:
            self.store.reset_code(slug, p.get("skeleton", ""))
        return json_response(200, {"code": p.get("skeleton", ""), "rev": self.store.rev(slug)})

    def redo(self, slug, query, data):
        p = self._problem(slug)
        with self.lock:
            if self.store.problem(slug)["status"] != "solved":
                raise ApiError(409, "not_solved", "Redo starts a new attempt of a solved problem; "
                               "this one is not solved yet.")
            attempt = self.store.redo(slug)
        self.last_results.pop(slug, None)
        return json_response(200, {"code": p.get("skeleton", ""), "attempt": attempt,
                                   "rev": self.store.rev(slug)})

    def heartbeat(self, query, data):
        slug = data.get("slug")
        if slug is not None:
            if not isinstance(slug, str):
                raise bad("slug must be a string or null.")
            self._problem(slug)
        seconds = data.get("seconds")
        if isinstance(seconds, bool) or not isinstance(seconds, (int, float)) \
                or seconds != seconds or seconds in (float("inf"), float("-inf")):
            raise bad("seconds must be a number.")
        self.store.add_seconds(slug, seconds)
        return json_response(200, {"ok": True})

    # ---- coach ----------------------------------------------------------

    def coach(self, slug, query, data):
        p = self._problem(slug)
        kind = data.get("kind")
        if kind not in coach.KINDS:
            raise bad("kind must be one of %s." % ", ".join(coach.KINDS))
        message = data.get("message")
        if message is not None and not isinstance(message, str):
            raise bad("message must be a string.")
        message = (message or "").strip()
        if len(message) > MAX_CODE:
            raise ApiError(413, "too_large", "The message is too long.")
        if kind == "question" and not message:
            raise bad("Type a question first.")
        code = self._code(data, required=False)
        notes_in = self._notes(data)
        self._save_changed(slug, p, code, notes_in)
        entry = self.store.problem(slug)
        context = self._context(slug, p, entry, code, message)
        if not self.coach_slot.acquire(blocking=False):
            raise ApiError(409, "busy", BUSY_DETAIL)
        cancel = threading.Event()
        try:
            gen = self._coach_stream(slug, kind, context, message or coach.KINDS[kind]["label"],
                                     cancel)
        except BaseException:
            self.coach_slot.release()
            raise
        return Response(200, {"Content-Type": "text/event-stream; charset=utf-8"},
                        stream=_Stream(gen, self.coach_slot.release), cancel=cancel)

    def _coach_stream(self, slug, kind, context, user_text, cancel):
        """The user turn and the reply are stored together, and only after `done`."""
        events = coach.ask(kind, context, cmd=self.coach_cmd, idle=self.coach_idle, cancel=cancel)
        try:
            yield b": open\n\n"
            for ev in events:
                if ev.get("idle"):
                    yield b": ping\n\n"
                    continue
                if ev.get("done"):
                    self.store.add_chat(slug, "user", kind, user_text)
                    self.store.add_chat(slug, "coach", kind, ev["text"])
                    if kind == "hint":
                        self.store.add_hint(slug)
                yield _sse(ev)
                if "done" in ev or "error" in ev:
                    return
        except Exception as exc:
            try:
                self.log.write(traceback.format_exc())
                self.log.flush()
            except Exception:
                pass
            yield _sse({"error": "internal", "detail": "%s: %s" % (type(exc).__name__, exc)})
        finally:
            events.close()

    def review(self, slug, query, data):
        p = self._problem(slug)
        submit_id = data.get("submit_id")
        if not isinstance(submit_id, str) or not submit_id:
            raise bad("The body needs the submit_id of the submit to review.")
        key = (slug, submit_id)
        with self.lock:
            record = self.store.submit(slug, submit_id)
            if record is None:
                raise ApiError(404, "not_found", "No submit %s for %s." % (submit_id, slug))
            if record.get("reviewed") or key in self.reviewing:
                raise ApiError(409, "already_reviewed", "That submit already has its final review.")
            if not self.coach_slot.acquire(blocking=False):
                raise ApiError(409, "busy", BUSY_DETAIL)
            self.reviewing.add(key)
        try:
            entry = self.store.problem(slug)
            context = self._context(slug, p, entry)
            if not context["results"] or context["results"].get("kind") != "submit":
                context["results"] = {"kind": "submit", "passed": record["passed"],
                                      "total": record["total"], "fatal": None, "failing": []}
            context["learnings"] = [e["title"] for e in notes.recent_learnings(self.paths, 50)]
            context["bug_log"] = notes.bug_log(self.paths)
            review = coach.final_review(context, cmd=self.coach_cmd)
            if "error" in review:
                status = 503 if review["error"] == "claude_not_found" else 502
                raise ApiError(status, review["error"], review.get("detail") or "The coach failed.")
            saved = {"learnings": 0, "bugs": 0, "skipped": []}
            day = self._today().isoformat()
            with self.lock:
                for m in review["mistakes"]:
                    happened = "LC %s %s (%s), final review in the app: %s" % (
                        p["number"], p["title"], p.get("url", ""), m["bug"])
                    if notes.append_learning(self.paths, day, m["bug"], happened, m["check"]):
                        saved["learnings"] += 1
                    else:
                        saved["skipped"].append("learnings.md: could not add \"%s\" (the file or "
                                                "its entries section is missing, or the write "
                                                "failed)" % m["bug"])
                    if m["repeat"]:
                        ok, why = notes.append_bug_log_result(self.paths, m["bug"], m["check"],
                                                              "%s, %s" % (p["title"], day))
                        if ok:
                            saved["bugs"] += 1
                        else:
                            saved["skipped"].append("bugs.md: could not add \"%s\" to the Log "
                                                    "table: %s" % (m["bug"], why))
                self.store.mark_reviewed(slug, submit_id, review)
            return json_response(200, {"review": review, "saved": saved})
        finally:
            with self.lock:
                self.reviewing.discard(key)
                self.coach_slot.release()

    # ---- course and notes -----------------------------------------------

    def course(self, query, data):
        state = self.store.snapshot()
        read = state.get("modules_read") or {}
        progress = {m["id"]: m for m in stats.module_progress(state, self.catalog)}
        modules = []
        for m in course.modules(self.paths):
            pr = progress.get(m["id"], {"solved": 0, "total": 0})
            modules.append({"id": m["id"], "title": m["title"], "path": m["path"],
                            "solved": pr["solved"], "total": pr["total"],
                            "read": bool(read.get(m["id"], False))})
        return json_response(200, {"modules": modules, "reference": course.reference(self.paths),
                                   "notes": course.notes_docs(self.paths)})

    def doc(self, query, data):
        rel = query.get("path")
        if isinstance(rel, list):
            rel = rel[0] if rel else None
        if not isinstance(rel, str) or not rel or ".." in rel:
            raise ApiError(403, "forbidden", "Only Markdown files under course/ and my-prep/ can "
                           "be opened.")
        try:
            return json_response(200, course.read_doc(self.paths, rel))
        except course.Forbidden:
            raise ApiError(403, "forbidden", "Only Markdown files under course/ and my-prep/ can "
                           "be opened.")
        except course.NotFound:
            raise ApiError(404, "not_found", "There is no file at %s." % rel)
        except course.TooLarge:
            raise ApiError(413, "too_large", "%s is larger than %d MB, so it is not opened here."
                           % (rel, course.MAX_DOC // (1024 * 1024)))

    def module_read(self, module_id, query, data):
        if module_id not in MODULE_IDS:
            raise ApiError(404, "not_found", "There is no module %s." % module_id)
        if not isinstance(data.get("read"), bool):
            raise bad("read must be true or false.")
        self.store.set_module_read(module_id, data["read"])
        return json_response(200, {"ok": True})

    def matrix(self, query, data):
        state = self.store.snapshot()
        groups = []
        for group in notes.read_matrix(self.paths):
            rows = []
            for r in group["rows"]:
                row = dict(r)
                row["practise"] = stats.practise_slug(r["id"], state, self.catalog)
                rows.append(row)
            groups.append({"title": group["title"], "rows": rows})
        return json_response(200, {"groups": groups})

    # ---- setup ----------------------------------------------------------

    def setup_status(self, query, data):
        out = {"statements": {"have": self._statements_have(),
                              "total": len(self.catalog.problems()),
                              "running": self.statements_running,
                              "failed": list(self.statements_failed)},
               "claude": coach.available(self.coach_cmd)}
        if self.statements_error:
            out["statements"]["error"] = self.statements_error
        err = getattr(self.store, "save_error", None)
        if err:
            out["save_error"] = err
        return json_response(200, out)

    def setup_statements(self, query, data):
        with self.lock:
            if self.statements_running:
                return json_response(200, {"started": False})
            self.statements_running = True
            self.statements_failed = []
            self.statements_error = None
        thread = threading.Thread(target=self._download, daemon=True)
        thread.start()
        return json_response(200, {"started": True})

    def _download(self):
        try:
            kw = {}
            if self.statements_opener is not None:
                kw["opener"] = self.statements_opener
            if self.statements_sleep is not None:
                kw["sleep"] = self.statements_sleep
            out = statements.fetch_all(self.paths, self.catalog, **kw)
            self.statements_failed = out["failed"]
        except Exception as exc:
            self.statements_error = "%s: %s" % (type(exc).__name__, exc)
            try:
                self.log.write(traceback.format_exc())
                self.log.flush()
            except Exception:
                pass
        finally:
            self.statements_running = False
