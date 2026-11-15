"""The app's state: my-prep/app/state.json plus the solution files in my-prep/solutions/.

A problem has one main solution file, `<slug>.py`, and may have more editor tabs, each its own
file `<slug>.<id>.py`. Earlier versions of the code (every submit, and what a reset, a redo or a
closed tab replaced) are kept under `solutions/history/<slug>/`.

One lock guards every read and write; the state file is replaced atomically (temp file and
os.replace), so a crash leaves either the old file or the new one. A state file of the wrong
shape is set aside and the app starts fresh; malformed inner records are normalised on load.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import threading
import uuid
from datetime import datetime

NOTE_KEYS = ("pattern", "complexity", "trace", "tests")
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
MAX_HEARTBEAT = 60
MAIN_TAB = 1
MAIN_NAME = "solution.py"
MAX_TABS = 8
MAX_TAB_NAME = 40
MAX_HISTORY = 60
LEGACY_HISTORY = 0  # the history id of a `<slug>.prev.py` that no history entry covers


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
            "matrix_written": {}, "warmup": None, "starred": {}, "setup": {}}


# Known top-level keys and the types they must have; any other type sets the file aside.
STATE_TYPES = {"version": int, "problems": dict, "days": dict, "modules_read": dict,
               "reps": dict, "matrix_written": dict, "warmup": (dict, type(None)),
               "starred": dict, "setup": dict}


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
    state["starred"] = {k: v for k, v in state["starred"].items()
                        if isinstance(k, str) and SLUG_RE.match(k) and isinstance(v, str)}
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


class TabError(ValueError):
    """A tab request that cannot be done; `code` is "tab_limit", "no_tab" or "main_tab"."""

    def __init__(self, code, detail):
        ValueError.__init__(self, detail)
        self.code = code


def _is_id(value, low):
    return isinstance(value, int) and not isinstance(value, bool) and value >= low


def clean_tab_name(name, fallback):
    """A tab name on one line, printable and short; `fallback` when nothing is left."""
    if not isinstance(name, str):
        return fallback
    name = "".join(ch for ch in " ".join(name.split()) if ch.isprintable())
    return name[:MAX_TAB_NAME].strip() or fallback


def _tab_list(entry):
    """The tabs of an entry, the main one first. An entry with no `tabs` has the main tab only."""
    out = [{"id": MAIN_TAB, "name": MAIN_NAME}]
    seen = {MAIN_TAB}
    raw = entry.get("tabs")
    for item in raw if isinstance(raw, list) else []:
        if not isinstance(item, dict) or not _is_id(item.get("id"), MAIN_TAB):
            continue
        tab = item["id"]
        if tab == MAIN_TAB:
            out[0]["name"] = clean_tab_name(item.get("name"), MAIN_NAME)
        elif tab not in seen:
            seen.add(tab)
            out.append({"id": tab, "name": clean_tab_name(item.get("name"), "solution-%d.py" % tab)})
    return out


def _free_tab_name(tabs):
    taken = {t["name"] for t in tabs}
    n = 2
    while "solution-%d.py" % n in taken:
        n += 1
    return "solution-%d.py" % n


def _history_list(entry):
    """The well-formed history records of an entry, oldest first."""
    raw = entry.get("history")
    return [r for r in raw if isinstance(r, dict) and _is_id(r.get("id"), 1)
            and isinstance(r.get("sha"), str)] if isinstance(raw, list) else []


def _sha(code):
    return hashlib.sha256(code.encode("utf-8")).hexdigest()[:16]


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

    def _tab_path(self, slug, tab):
        if not _is_id(tab, MAIN_TAB):
            raise ValueError("unsafe tab: %r" % (tab,))
        return self._solution_path(slug, ".py" if tab == MAIN_TAB else ".%d.py" % tab)

    def _history_path(self, slug, hid):
        if not _is_id(hid, 1):
            raise ValueError("unsafe history id: %r" % (hid,))
        return os.path.join(self.paths.solutions_dir, "history", _check_slug(slug), "%d.py" % hid)

    @staticmethod
    def _read_file(path):
        try:
            with open(path, encoding="utf-8", newline="") as fh:
                return fh.read()
        except FileNotFoundError:
            return None

    @staticmethod
    def _remove_file(path):
        try:
            os.remove(path)
        except FileNotFoundError:
            pass

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

    def code(self, slug, tab=MAIN_TAB):
        return self._read_file(self._tab_path(slug, tab))

    def tabs(self, slug):
        """The editor tabs of `slug` as `[{id, name}]`, the main one (id 1) first."""
        _check_slug(slug)
        with self._lock:
            return _tab_list(self._state["problems"].get(slug) or {})

    def tab_name(self, slug, tab):
        """The name of the tab, or None when the problem has no such tab."""
        for item in self.tabs(slug):
            if item["id"] == tab:
                return item["name"]
        return None

    def history(self, slug):
        """Earlier versions of the code, oldest first: `[{id, at, attempt, tab, why, sha}]`, a
        submitted one also with `submit_id, ok, passed, total`. A `<slug>.prev.py` left by an
        older version of the app is listed with id 0 when no record holds the same code."""
        _check_slug(slug)
        with self._lock:
            items = copy.deepcopy(_history_list(self._state["problems"].get(slug) or {}))
        path = self._solution_path(slug, ".prev.py")
        try:
            prev = self._read_file(path)
        except ValueError:  # not UTF-8
            prev = None
        if prev and prev.strip() and _sha(prev) not in {r["sha"] for r in items}:
            try:
                at = datetime.fromtimestamp(os.stat(path).st_mtime).isoformat(timespec="seconds")
            except OSError:
                at = ""
            items.append({"id": LEGACY_HISTORY, "at": at, "attempt": None, "tab": MAIN_NAME,
                          "why": "previous", "sha": _sha(prev)})
            items.sort(key=lambda r: r.get("at") if isinstance(r.get("at"), str) else "")
        return items

    def history_code(self, slug, hid):
        """The code of one history record, or None when there is no such record or file."""
        _check_slug(slug)
        if not _is_id(hid, LEGACY_HISTORY):
            return None
        if hid == LEGACY_HISTORY:
            return self._read_file(self._solution_path(slug, ".prev.py"))
        with self._lock:
            known = any(r["id"] == hid for r in
                        _history_list(self._state["problems"].get(slug) or {}))
        return self._read_file(self._history_path(slug, hid)) if known else None

    def draft_saved_at(self, slug):
        """When a solution file was last written (the draft save time), as the store's local
        ISO stamp, or None when there is no file."""
        times = []
        for tab in self.tabs(slug):
            try:
                times.append(os.stat(self._tab_path(slug, tab["id"])).st_mtime)
            except OSError:
                pass
        if not times:
            return None
        return datetime.fromtimestamp(max(times)).isoformat(timespec="seconds")

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

    def save_draft(self, slug, code, notes, codes=None):
        """Save the main tab's `code`, the code of other tabs (`codes`, by tab id) and the notes;
        each may be None."""
        with self._lock:
            files = dict(codes or {})
            if code is not None:
                files[MAIN_TAB] = code
            known = {t["id"] for t in self.tabs(slug)}
            for tab in files:
                if tab not in known:
                    raise TabError("no_tab", "This problem has no tab %r." % (tab,))
            # write the files first: a failed write raises before any state changes
            for tab, text in files.items():
                self._write_file(self._tab_path(slug, tab), text)
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

    def record_submit(self, slug, passed, total, code=None, tab=MAIN_TAB, skeleton=None):
        """Record a submit. With `code`, the submitted code is kept in the history and the
        record points at it (`history`), so a later look or review sees what was submitted."""
        with self._lock:
            entry = self._entry(slug)
            at = self._stamp()
            ok = total > 0 and passed == total
            record = {"id": uuid.uuid4().hex[:12], "at": at, "attempt": entry["attempt"],
                      "passed": passed, "total": total, "ok": ok,
                      "seconds": entry["attempt_seconds"], "hints_used": entry["attempt_hints"],
                      "reviewed": False}
            if code is not None:
                name = self.tab_name(slug, tab) or MAIN_NAME
                record["tab"] = name
                try:
                    hid = self._archive(entry, slug, code, "submit", name, skeleton,
                                        {"submit_id": record["id"], "ok": ok, "passed": passed,
                                         "total": total})
                except WriteFailed:  # the code is still in its tab; the submit counts all the same
                    hid = None
                if hid is not None:
                    record["history"] = hid
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

    def _archive(self, entry, slug, code, why, tab_name, skeleton=None, result=None):
        """Keep `code` in the history of `slug` and return the record's id; None for code not
        worth keeping (blank, or the skeleton). The same code within one attempt is kept once: a
        submit of it adds its result to the record. Caller holds the lock and saves."""
        if not isinstance(code, str) or not code.strip():
            return None
        if skeleton is not None and code.strip() == skeleton.strip():
            return None
        sha = _sha(code)
        history = _history_list(entry)
        entry["history"] = history
        for rec in history:
            if rec["sha"] == sha and rec.get("attempt") == entry["attempt"]:
                if result:
                    rec.update(result, why="submit", at=self._stamp(), tab=tab_name)
                    history.remove(rec)
                    history.append(rec)
                return rec["id"]
        hid = max([r["id"] for r in history] + [_typed(entry.get("history_seq", 0), 0)]) + 1
        self._write_file(self._history_path(slug, hid), code)
        rec = {"id": hid, "at": self._stamp(), "attempt": entry["attempt"], "tab": tab_name,
               "why": why, "sha": sha}
        rec.update(result or {})
        history.append(rec)
        entry["history_seq"] = hid
        while len(history) > MAX_HISTORY:
            # the oldest version goes first, an accepted one only when nothing else is left
            old = next((r for r in history[:-1] if not r.get("ok")), history[0])
            history.remove(old)
            try:
                self._remove_file(self._history_path(slug, old["id"]))
            except OSError:
                pass
        return hid

    def add_tab(self, slug, name=None, code=None):
        """Open one more editor tab and return it as `{id, name}`. An id is never used twice."""
        with self._lock:
            entry = self._entry(slug)
            tabs = _tab_list(entry)
            if len(tabs) >= MAX_TABS:
                raise TabError("tab_limit", "A problem can have %d tabs at most. Close one first."
                               % MAX_TABS)
            tab = max([t["id"] for t in tabs] + [_typed(entry.get("tab_seq", MAIN_TAB), MAIN_TAB)]) + 1
            if code is not None:
                self._write_file(self._tab_path(slug, tab), code)
            item = {"id": tab, "name": clean_tab_name(name, _free_tab_name(tabs))}
            tabs.append(item)
            entry["tabs"] = tabs
            entry["tab_seq"] = tab
            self._bump(entry)
            self._save()
            return dict(item)

    def rename_tab(self, slug, tab, name):
        with self._lock:
            entry = self._entry(slug)
            tabs = _tab_list(entry)
            for item in tabs:
                if item["id"] == tab:
                    item["name"] = clean_tab_name(name, item["name"])
                    entry["tabs"] = tabs
                    self._bump(entry)
                    self._save()
                    return dict(item)
            raise TabError("no_tab", "This problem has no tab %r." % (tab,))

    def close_tab(self, slug, tab, skeleton=None):
        """Close an extra tab. Its code moves to the history first, so nothing is lost."""
        with self._lock:
            entry = self._entry(slug)
            tabs = _tab_list(entry)
            if tab == MAIN_TAB:
                raise TabError("main_tab", "The first tab stays open.")
            item = next((t for t in tabs if t["id"] == tab), None)
            if item is None:
                raise TabError("no_tab", "This problem has no tab %r." % (tab,))
            path = self._tab_path(slug, tab)
            self._archive(entry, slug, self._read_file(path), "closed", item["name"], skeleton)
            self._remove_file(path)
            tabs.remove(item)
            entry["tabs"] = tabs
            self._bump(entry)
            self._save()

    def reset_code(self, slug, skeleton=None, tab=MAIN_TAB):
        """Remove the solution file of a tab. Code that differs from `skeleton` goes to the
        history, and the main tab's also stays as `<slug>.prev.py`, as Redo does. The rev rises
        only for a problem that has an entry or had a file, so resetting an untouched problem
        creates no state."""
        with self._lock:
            current = self._tab_path(slug, tab)
            try:
                saved = self.code(slug, tab)
            except ValueError:  # not UTF-8: keep it, it is not the skeleton
                if tab != MAIN_TAB:
                    raise
                saved = False
            existed = saved is not None
            changed = existed and skeleton is not None and saved != skeleton
            if changed and isinstance(saved, str):
                self._archive(self._entry(slug), slug, saved, "reset",
                              self.tab_name(slug, tab) or MAIN_NAME, skeleton)
            if changed and tab == MAIN_TAB:
                os.replace(current, self._solution_path(slug, ".prev.py"))
            elif existed:
                self._remove_file(current)
            if existed or slug in self._state["problems"]:
                self._bump(self._entry(slug))
                self._save()

    def redo(self, slug, skeleton=None):
        """Start a new attempt from one empty tab. The code of every tab goes to the history
        first; the main tab's also stays as `<slug>.prev.py`."""
        with self._lock:
            entry = self._entry(slug)
            for tab in _tab_list(entry):
                path = self._tab_path(slug, tab["id"])
                try:
                    code = self._read_file(path)
                except ValueError:  # not UTF-8: left where it is
                    continue
                self._archive(entry, slug, code, "redo", tab["name"], skeleton)
                if tab["id"] != MAIN_TAB:
                    self._remove_file(path)
            entry.pop("tabs", None)
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

    def starred(self):
        """The starred slugs. A star is kept apart from the problem's entry: it is not an attempt."""
        with self._lock:
            return set(self._state["starred"])

    def set_starred(self, slug, on):
        _check_slug(slug)
        with self._lock:
            stars = self._state["starred"]
            if on:
                stars.setdefault(slug, self._stamp())
            else:
                stars.pop(slug, None)
            self._save()
            return slug in stars

    def set_module_read(self, module_id, read):
        with self._lock:
            self._state["modules_read"][module_id] = bool(read)
            self._save()

    def setup(self, part):
        """A copy of one part of the in-app setup (the discovery chat, the self-check, the
        diagnostic), or {} when it has not started."""
        with self._lock:
            value = self._state["setup"].get(part)
            return copy.deepcopy(value) if isinstance(value, dict) else {}

    def update_setup(self, part, fn):
        """Change one part of the setup under the lock: fn(part_dict) edits it in place.
        Returns a copy of the part after the change."""
        with self._lock:
            value = self._state["setup"].get(part)
            value = value if isinstance(value, dict) else {}
            fn(value)
            self._state["setup"][part] = value
            self._save()
            return copy.deepcopy(value)

    def stamp(self):
        return self._stamp()

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
