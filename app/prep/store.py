"""The app's state: my-prep/app/state.json plus the solution files in my-prep/solutions/.

One lock guards every read and write; the state file is replaced atomically (temp file and
os.replace), so a crash leaves either the old file or the new one. A state file of the wrong
shape is set aside and the app starts fresh; malformed inner records are normalised on load.
"""
from __future__ import annotations

import copy
import json
import os
import re
import threading
import uuid
from datetime import datetime

NOTE_KEYS = ("pattern", "complexity", "trace", "tests")
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
MAX_HEARTBEAT = 60


def _blank_notes():
    return {key: "" for key in NOTE_KEYS}


def _blank_problem():
    return {"status": "new", "first_opened": None, "seconds": 0, "hints_used": 0, "runs": 0,
            "submits": [], "solved_at": None, "first_try": None, "notes": _blank_notes(),
            "chat": [], "attempt": 1, "attempt_seconds": 0, "attempt_hints": 0,
            "last_solved_at": None, "rev": 0, "touched_at": None}


def _blank_day():
    return {"seconds": 0, "runs": 0, "submits": 0, "solved": []}


def _blank_state():
    return {"version": 1, "problems": {}, "days": {}, "modules_read": {}, "reps": {},
            "matrix_written": {}, "warmup": None}


# Known top-level keys and the types they must have; any other type sets the file aside.
STATE_TYPES = {"version": int, "problems": dict, "days": dict, "modules_read": dict,
               "reps": dict, "matrix_written": dict, "warmup": (dict, type(None))}


def _typed(value, default):
    """`value` when it has the type of `default` (a None default accepts anything), else a copy of it."""
    if default is None:
        return value
    if isinstance(value, type(default)) and isinstance(value, bool) == isinstance(default, bool):
        return value
    return copy.deepcopy(default)


class WriteFailed(OSError):
    """A file the app owns could not be written; `rel_path` is relative to the kit root."""

    def __init__(self, rel_path, reason):
        OSError.__init__(self, "could not write %s: %s" % (rel_path, reason))
        self.rel_path = rel_path
        self.reason = reason


def _normal_problem(raw):
    entry = {}
    for key, default in _blank_problem().items():
        entry[key] = _typed(raw.get(key, default), default)
    for key, value in raw.items():
        entry.setdefault(key, value)
    notes = {k: v for k, v in entry["notes"].items() if k not in NOTE_KEYS}  # a newer version's keys
    notes.update({k: _typed(entry["notes"].get(k, ""), "") for k in NOTE_KEYS})
    entry["notes"] = notes
    entry["submits"] = [r for r in entry["submits"] if isinstance(r, dict)]
    entry["chat"] = [r for r in entry["chat"] if isinstance(r, dict)]
    if entry["attempt"] < 1:
        entry["attempt"] = 1
    return entry


def _normal_day(raw):
    day = dict(raw)  # keys this version does not know stay
    day.update({key: _typed(raw.get(key, default), default) for key, default in _blank_day().items()})
    day["solved"] = [s for s in day["solved"] if isinstance(s, str)]
    return day


def _normal_rows(rows):
    out = []
    for row in rows:
        if not isinstance(row, dict) or "slug" not in row or "attempt" not in row:
            continue
        row = dict(row)
        row["level"] = _typed(row.get("level", 0), 0)
        row["at"] = row["at"] if isinstance(row.get("at"), str) else ""
        out.append(row)
    return out


def _normalise(data):
    """Fill defaults and drop entries that are not dicts; the rest of the code indexes directly."""
    state = _blank_state()
    state.update(data)
    state["problems"] = {k: _normal_problem(v) for k, v in data["problems"].items()
                         if isinstance(k, str) and isinstance(v, dict)} if "problems" in data else {}
    state["days"] = {k: _normal_day(v) for k, v in data["days"].items()
                     if isinstance(k, str) and isinstance(v, dict)} if "days" in data else {}
    state["reps"] = {k: _normal_rows(v) for k, v in data["reps"].items()
                     if isinstance(k, str) and isinstance(v, list)} if "reps" in data else {}
    warmup = state["warmup"]
    if isinstance(warmup, dict):
        warmup = dict(warmup)
        warmup["skipped"] = _typed(warmup.get("skipped", []), [])
        state["warmup"] = warmup
    return state


def _check_slug(slug):
    if not isinstance(slug, str) or not SLUG_RE.match(slug):
        raise ValueError("unsafe slug: %r" % (slug,))
    return slug


class Store:
    def __init__(self, paths, now=datetime.now, log=None):
        self.paths = paths
        self._now = now
        self._log = log  # a text stream; the first failed save and the recovery are printed once
        self._lock = threading.RLock()
        self.recovered = None  # set-aside path (or a note that setting aside failed); None if fine
        self.save_error = None  # message of the last failed save; None when the last save worked
        self._state = self._load()

    # ---- file handling -------------------------------------------------

    def _load(self):
        path = self.paths.state_file
        try:
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
            if not isinstance(data, dict):
                raise ValueError("state is not an object")
            for key, kind in STATE_TYPES.items():
                if key in data and (not isinstance(data[key], kind)
                                    or (kind is int and isinstance(data[key], bool))):
                    raise ValueError("state key %r has the wrong type" % key)
        except FileNotFoundError:
            return _blank_state()
        except (OSError, ValueError):
            self._set_aside(path)
            return _blank_state()
        return _normalise(data)

    def _set_aside(self, path):
        stamp = self._now().strftime("%Y%m%d-%H%M%S")
        target = "%s.broken-%s" % (path, stamp)
        n = 1
        while os.path.exists(target):
            n += 1
            target = "%s.broken-%s-%d" % (path, stamp, n)
        try:
            os.replace(path, target)
        except OSError as exc:
            self.recovered = "could not set %s aside (%s); starting fresh in memory" % (path, exc)
        else:
            self.recovered = target

    def _save(self):
        """Write the state; a failure keeps the in-memory state and is left in `save_error`."""
        path = self.paths.state_file
        tmp = path + ".tmp"
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(tmp, "w", encoding="utf-8") as fh:
                json.dump(self._state, fh, indent=1, ensure_ascii=False)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, path)
        except OSError as exc:
            first = self.save_error is None
            rel = os.path.relpath(path, self.paths.root).replace(os.sep, "/")
            self.save_error = "Could not write %s: %s." % (rel, exc.strerror or str(exc))
            try:
                os.remove(tmp)
            except OSError:
                pass
            if first:
                self._say(self.save_error + " Progress is kept in memory until saving works.")
        else:
            if self.save_error is not None:
                self._say("Saving progress works again.")
            self.save_error = None

    def _say(self, line):
        if self._log is None:
            return
        try:
            self._log.write(line + "\n")
            self._log.flush()
        except Exception:
            pass

    def _solution_path(self, slug, suffix=".py"):
        return os.path.join(self.paths.solutions_dir, _check_slug(slug) + suffix)

    def _write_file(self, path, text):
        tmp = path + ".tmp"
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(tmp, "w", encoding="utf-8", newline="") as fh:
                fh.write(text)
            os.replace(tmp, path)
        except OSError as exc:
            try:
                os.remove(tmp)
            except OSError:
                pass
            raise WriteFailed(os.path.relpath(path, self.paths.root).replace(os.sep, "/"),
                              exc.strerror or str(exc))

    # ---- helpers -------------------------------------------------------

    def _stamp(self):
        return self._now().isoformat(timespec="seconds")

    def _today(self):
        return self._now().date().isoformat()

    def _entry(self, slug):
        """The stored entry, created (with defaults) on first touch. Caller holds the lock."""
        _check_slug(slug)
        problems = self._state["problems"]
        if slug not in problems:
            entry = _blank_problem()
            entry["first_opened"] = self._stamp()
            problems[slug] = entry
        entry = problems[slug]
        for key, value in _blank_problem().items():
            entry.setdefault(key, value)
        return entry

    def _day(self):
        return self._state["days"].setdefault(self._today(), _blank_day())

    @staticmethod
    def _touch(entry):
        if entry["status"] == "new":
            entry["status"] = "attempted"

    # ---- reading -------------------------------------------------------

    def snapshot(self):
        with self._lock:
            return copy.deepcopy(self._state)

    def problem(self, slug):
        _check_slug(slug)
        with self._lock:
            entry = copy.deepcopy(self._state["problems"].get(slug, {}))
        for key, value in _blank_problem().items():
            entry.setdefault(key, value)
        return entry

    def code(self, slug):
        try:
            with open(self._solution_path(slug), encoding="utf-8", newline="") as fh:
                return fh.read()
        except FileNotFoundError:
            return None

    def draft_saved_at(self, slug):
        """When the solution file was last written (the draft save time), as the store's local
        ISO stamp, or None when there is no file."""
        try:
            mtime = os.stat(self._solution_path(slug)).st_mtime
        except OSError:
            return None
        return datetime.fromtimestamp(mtime).isoformat(timespec="seconds")

    def submit(self, slug, submit_id):
        for rec in self.problem(slug)["submits"]:
            if rec.get("id") == submit_id:
                return rec
        return None

    def warmup(self):
        with self._lock:
            return copy.deepcopy(self._state.get("warmup"))

    def matrix_written(self, row_id):
        with self._lock:
            return self._state["matrix_written"].get(row_id)

    # ---- writing -------------------------------------------------------

    def rev(self, slug):
        """How many times the saved code or notes of `slug` have changed; 0 when never."""
        _check_slug(slug)
        with self._lock:
            entry = self._state["problems"].get(slug) or {}
            return _typed(entry.get("rev", 0), 0)

    @staticmethod
    def _bump(entry):
        entry["rev"] = _typed(entry.get("rev", 0), 0) + 1

    def save_draft(self, slug, code, notes):
        with self._lock:
            # write the file first: a failed write raises before any state changes
            if code is not None:
                self._write_file(self._solution_path(slug), code)
            entry = self._entry(slug)
            if notes:
                for key in NOTE_KEYS:
                    if isinstance(notes.get(key), str):
                        entry["notes"][key] = notes[key]
            self._touch(entry)
            self._bump(entry)
            entry["touched_at"] = self._stamp()
            self._save()

    def record_run(self, slug):
        with self._lock:
            entry = self._entry(slug)
            entry["runs"] += 1
            entry["touched_at"] = self._stamp()
            self._touch(entry)
            self._day()["runs"] += 1
            self._save()

    def record_submit(self, slug, passed, total):
        with self._lock:
            entry = self._entry(slug)
            at = self._stamp()
            ok = total > 0 and passed == total
            record = {"id": uuid.uuid4().hex[:12], "at": at, "attempt": entry["attempt"],
                      "passed": passed, "total": total, "ok": ok,
                      "seconds": entry["attempt_seconds"], "hints_used": entry["attempt_hints"],
                      "reviewed": False}
            if entry["first_try"] is None and not entry["submits"]:
                entry["first_try"] = ok
            entry["submits"].append(record)
            entry["touched_at"] = at
            day = self._day()
            day["submits"] += 1
            if ok:
                entry["status"] = "solved"
                entry["last_solved_at"] = at
                if entry["solved_at"] is None:
                    entry["solved_at"] = at
                if slug not in day["solved"]:
                    day["solved"].append(slug)
            else:
                self._touch(entry)
            self._save()
            return copy.deepcopy(record)

    def mark_reviewed(self, slug, submit_id, review):
        _check_slug(slug)
        with self._lock:
            entry = self._state["problems"].get(slug)
            for rec in entry["submits"] if entry else []:
                if rec.get("id") == submit_id:
                    rec["reviewed"] = True
                    rec["review"] = copy.deepcopy(review)
                    self._save()
                    return

    def add_chat(self, slug, role, kind, text):
        with self._lock:
            entry = self._entry(slug)
            entry["chat"].append({"role": role, "kind": kind, "text": text, "at": self._stamp()})
            self._save()

    def add_hint(self, slug):
        with self._lock:
            entry = self._entry(slug)
            entry["hints_used"] += 1
            entry["attempt_hints"] += 1
            self._save()

    def add_seconds(self, slug, seconds):
        seconds = max(0, min(MAX_HEARTBEAT, int(seconds)))
        if seconds == 0:
            return
        with self._lock:
            self._day()["seconds"] += seconds
            if slug is not None:
                entry = self._entry(slug)
                entry["seconds"] += seconds
                entry["attempt_seconds"] += seconds
            self._save()

    def reset_code(self, slug, skeleton=None):
        """Remove the solution file. Code that differs from `skeleton` is kept as
        `<slug>.prev.py`, as Redo does. The rev rises only for a problem that has an entry or had
        a file, so resetting an untouched problem creates no state."""
        with self._lock:
            current = self._solution_path(slug)
            try:
                saved = self.code(slug)
            except ValueError:  # not UTF-8: keep it, it is not the skeleton
                saved = False
            existed = saved is not None
            if existed and skeleton is not None and saved != skeleton:
                os.replace(current, self._solution_path(slug, ".prev.py"))
            elif existed:
                try:
                    os.remove(current)
                except FileNotFoundError:
                    pass
            if existed or slug in self._state["problems"]:
                self._bump(self._entry(slug))
                self._save()

    def redo(self, slug):
        with self._lock:
            entry = self._entry(slug)
            current = self._solution_path(slug)
            if os.path.exists(current):
                os.replace(current, self._solution_path(slug, ".prev.py"))
            entry["attempt"] += 1
            entry["attempt_seconds"] = 0
            entry["attempt_hints"] = 0
            entry["notes"] = _blank_notes()
            entry["chat"] = []
            self._bump(entry)
            self._save()
            return entry["attempt"]

    def set_module_read(self, module_id, read):
        with self._lock:
            self._state["modules_read"][module_id] = bool(read)
            self._save()

    def set_warmup(self, date, slug, skipped):
        with self._lock:
            self._state["warmup"] = {"date": date, "slug": slug, "skipped": list(skipped)}
            self._save()

    def add_rep(self, row_id, slug, attempt, level):
        with self._lock:
            rows = [r for r in self._state["reps"].get(row_id, [])
                    if not (r["slug"] == slug and r["attempt"] == attempt)]
            rows.append({"slug": slug, "attempt": attempt, "level": level, "at": self._stamp()})
            rows.sort(key=lambda r: r["at"])
            self._state["reps"][row_id] = rows
            self._save()
            return [r["level"] for r in rows[-3:]]

    def set_matrix_written(self, row_id, value):
        with self._lock:
            self._state["matrix_written"][row_id] = value
            self._save()
