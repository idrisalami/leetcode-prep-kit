"""Parent side of a run: spawns the harness child, enforces the whole-run limit, reads results.

run(spec, code, examples_only=False) -> {"fatal", "results", "passed", "total"}. It never raises.

Known limits: comparing and displaying a case's result happen outside the per-case time limit; only
the whole-run limit bounds them.
"""
from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile

from app.prep import harness

HARNESS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "harness.py")
EXTRA_S = 5.0
STDERR_TAIL = 600
STDERR_READ_MAX = 64 * 1024  # bytes read from the end of the child's stderr file, however big it grew


def _fatal(type_name, message, total, line=None):
    return {"fatal": {"type": type_name, "message": message, "line": line},
            "results": [], "passed": 0, "total": total}


def run(spec, code, examples_only=False):
    total = 0
    try:
        cases = harness.selected_cases(spec, examples_only)
        total = len(cases)
        return _run(spec, code, examples_only, cases)
    except Exception as exc:  # the caller (the server) must always get an answer
        return _fatal("RunnerError", "%s: %s" % (type(exc).__name__, exc), total)


def _read_lines(path):
    rows = []
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except ValueError:
                    break  # a line cut off by a kill; nothing after it is trustworthy
    except OSError:
        pass
    return rows


def _stderr_tail(path):
    try:
        with open(path, "rb") as fh:
            fh.seek(0, os.SEEK_END)
            fh.seek(max(0, fh.tell() - STDERR_READ_MAX))
            data = fh.read(STDERR_READ_MAX)
    except OSError:
        return ""
    return data.decode("utf-8", errors="replace").strip()[-STDERR_TAIL:]


def _kill_group(pid):
    """Kill the child's whole process group (the child leads its own session), so a process the
    solution started cannot outlive the run."""
    try:
        os.killpg(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass  # nothing of the group is left
    except OSError:
        pass


def _run(spec, code, examples_only, cases):
    total = len(cases)
    limit = sum(harness.case_limit(spec, c) for c in cases) + harness.LOAD_LIMIT_S + EXTRA_S
    tmp = tempfile.mkdtemp(prefix="prep-run-")
    try:
        spec_path = os.path.join(tmp, "spec.json")
        solution_path = os.path.join(tmp, "solution.py")
        results_path = os.path.join(tmp, "results.jsonl")
        stderr_path = os.path.join(tmp, "stderr.txt")
        with open(spec_path, "w", encoding="utf-8") as fh:
            json.dump(spec, fh)
        with open(solution_path, "w", encoding="utf-8") as fh:
            fh.write(code)
        argv = [sys.executable, "-I", HARNESS_PATH, spec_path, solution_path, results_path]
        if examples_only:
            argv.append("--examples-only")
        killed = False
        with open(stderr_path, "w", encoding="utf-8") as err:
            proc = subprocess.Popen(argv, cwd=tmp, stdin=subprocess.DEVNULL,
                                    stdout=subprocess.DEVNULL, stderr=err, start_new_session=True)
            try:
                try:
                    proc.wait(timeout=limit)
                except subprocess.TimeoutExpired:
                    killed = True
                    _kill_group(proc.pid)
                    proc.wait()
            finally:
                _kill_group(proc.pid)  # also after a normal exit: leftovers of the solution's own children
        return _collect(spec, cases, _read_lines(results_path), killed, proc.returncode,
                        _stderr_tail(stderr_path))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _collect(spec, cases, rows, killed, returncode, stderr):
    total = len(cases)
    for row in rows:
        if "fatal" in row:
            fatal = row["fatal"]
            return _fatal(fatal.get("type"), fatal.get("message"), total, fatal.get("line"))
    finished = {}
    started = set()
    for row in rows:
        if "start" in row:
            started.add(row["start"])
        elif "case" in row:
            k = row.pop("case")
            finished[k] = row
    if not started and not finished:
        if killed:
            return _fatal("Timeout", "your code did not finish loading in time", total)
        message = "the test process ended before any case ran (exit code %s)" % returncode
        if stderr:
            message += ": " + stderr
        return _fatal("ProcessExit", message, total)
    results = []
    cut = False
    for k, case in enumerate(cases):
        if k in finished:
            results.append(finished[k])
            continue
        if cut or k not in started:
            results.append(harness.blank_result(spec, case, "not_run"))
            cut = True
            continue
        cut = True
        if killed:
            row = harness.blank_result(spec, case, "timeout")
            row["ms"] = round(harness.case_limit(spec, case) * 1000, 1)
        else:
            row = harness.blank_result(spec, case, "error")
            message = "the process ended during this case (exit code %s)" % returncode
            if stderr:
                message += ": " + stderr
            row["error"] = {"type": "ProcessExit", "message": message, "line": None, "trace": stderr}
        results.append(row)
    passed = sum(1 for r in results if r["status"] == "pass")
    return {"fatal": None, "results": results, "passed": passed, "total": total}
