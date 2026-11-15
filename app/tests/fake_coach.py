"""Stands in for `claude` in tests (selected through PREP_COACH_CMD); never calls anything.

Modes, from FAKE_COACH_MODE:
  stream   (default) three text deltas in Claude Code's stream-json format, then a result line
  json     one JSON object with `structured_output` (FAKE_COACH_REVIEW, else a default review)
  json_result  the review only as a JSON string in `result` (the fallback path)
  fail     a line of stderr, exit 1
  garbage  stream mode with non-JSON and unrelated JSON lines mixed in
  hang     read the prompt, then sleep for a long time
  spawn    start a grandchild (`sleep 60`, same process group), send one delta, then hang
  orphan   start a grandchild with its own stdio closed, then answer normally and exit 0
           (json when --json-schema is on the command line, else stream)
  slow     sleep FAKE_COACH_SLOW seconds (default 1), then stream normally
  auto     json when the command line carries --json-schema, else stream
When the command line starts with `exec`, it stands in for `codex exec` instead (selected through
PREP_CODEX_CMD): nothing useful goes to stdout and the answer is written to the `-o` file. That
is the three deltas joined, or the review as JSON when `--output-schema` is given. Codex modes:
fail and hang as above, `empty` (no answer file), `garbage` (a review that is not JSON), `wrapped`
(the review with words around it).
With a schema and no FAKE_COACH_REVIEW, the answer follows the schema's top-level properties:
`profile` (the discovery notes), `marks` (the self-check: every question right but 3 and 7) and
`blocks` (the diagnostic score and plan), each built from the numbers, slugs and rows in the prompt.
When FAKE_COACH_LOG is set, argv, the working directory and the prompt (stdin) are written there.
When FAKE_COACH_CHILD_LOG is set, spawn and orphan write the grandchild's pid there.
"""
from __future__ import annotations

import datetime
import json
import os
import re
import subprocess
import sys
import time

DELTAS = ["First ", "point.", "\n2. Second point."]

DEFAULT_REVIEW = {"verdict": "pass", "good": ["clear names"], "wrong": [],
                  "edge_cases": ["empty input"], "next_step": "try the follow-up",
                  "mistakes": [{"bug": "off by one on the last index",
                                "check": "trace the last element by hand", "repeat": False}]}


NEXT = {"next_up": "the next step", "where": "the app", "why": "it comes next",
        "what_to_do": "open it from Home", "watch_for": "rushing", "at_the_end": "tick it",
        "pending": "none"}


def setup_answer(props, prompt):
    """A plausible answer to one of the in-app setup schemas, or None for any other schema."""
    if "profile" in props:
        return {"profile": {k: "said: " + k for k in props["profile"]["properties"]},
                "timeline": {"interview_dates": "2026-12-15", "weeks_left": "4",
                             "hours_per_week": "10", "coding_rounds": "two"},
                "priorities": [{"id": "C9", "priority": "not flagged", "why": "first language"},
                               {"id": "ZZ9", "priority": "P0", "why": "not a row"}],
                "what_next": "The module 00 self-check, then the diagnostic.",
                "next_session": dict(NEXT, next_up="Module 00 self-check")}
    if "marks" in props:
        ns = [int(n) for n in re.findall(r"^(\d+)\. Question:", prompt, re.M)]
        return {"marks": [{"n": n, "correct": n not in (3, 7),
                           "note": "missed the key point" if n in (3, 7) else "right"} for n in ns],
                "next_session": dict(NEXT, next_up="The diagnostic")}
    if "blocks" in props:
        today = re.search(r"Today is (\d{4}-\d{2}-\d{2})", prompt)
        day = datetime.date.fromisoformat(today.group(1)) if today else datetime.date(2026, 1, 1)
        slugs = re.findall(r", slug ([a-z0-9-]+)\)", prompt)
        rows = re.findall(r"^([ABC]\d+) \| ", prompt, re.M)
        blocks = []
        for i in range(10):
            start = day + datetime.timedelta(days=1 + 3 * i)
            blocks.append({"module": "%02d" % (i + 1), "start": start.isoformat(),
                           "end": (start + datetime.timedelta(days=2)).isoformat(), "hours": "6"})
        return {"problems": [{"slug": s, "outcome": "partial", "rows_scored": rows[:1],
                              "comment": "a working idea, one bug"} for s in slugs],
                "matrix": [{"id": r, "level": "1", "evidence": "diagnostic: partial"}
                           for r in rows[:3]],
                "known_gaps": ["A1 hashing: slow"], "blocks": blocks,
                "weekly_hours": {"read": "3", "drills": "4", "review": "1", "revision": "1",
                                 "other": "1"},
                "what_next": "Block 01, Arrays and hashing.",
                "next_session": dict(NEXT, next_up="Block 01")}
    return None


def review_for(schema_text, prompt):
    if os.environ.get("FAKE_COACH_REVIEW"):
        return os.environ["FAKE_COACH_REVIEW"]
    try:
        props = json.loads(schema_text).get("properties") or {}
    except (TypeError, ValueError):
        props = {}
    answer = setup_answer(props, prompt)
    return json.dumps(DEFAULT_REVIEW if answer is None else answer)


def emit(obj):
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()


def delta(text):
    return {"type": "stream_event",
            "event": {"type": "content_block_delta", "index": 0,
                      "delta": {"type": "text_delta", "text": text}}}


def grandchild():
    child = subprocess.Popen(["sleep", "60"], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
    log = os.environ.get("FAKE_COACH_CHILD_LOG")
    if log:
        with open(log + ".tmp", "w") as fh:
            fh.write(str(child.pid))
        os.replace(log + ".tmp", log)
    return child


def codex(mode, prompt):
    argv = sys.argv[1:]
    out = argv[argv.index("-o") + 1]
    if mode == "fail":
        sys.stderr.write("something went wrong in the fake coach\n")
        sys.exit(1)
    if mode == "hang":
        time.sleep(60)
        return
    if mode == "slow":
        time.sleep(float(os.environ.get("FAKE_COACH_SLOW") or 1))
    print("thinking about it")  # progress chatter, which the app must ignore
    if mode == "empty":
        return
    if "--output-schema" in argv:
        with open(argv[argv.index("--output-schema") + 1], encoding="utf-8") as fh:
            review = review_for(fh.read(), prompt)
        text = {"garbage": "no review here", "wrapped": "Here it is:\n" + review + "\nDone."}.get(mode, review)
    else:
        text = "".join(DELTAS)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(text)


def main():
    prompt = sys.stdin.read()
    log = os.environ.get("FAKE_COACH_LOG")
    if log:
        with open(log + ".tmp", "w", encoding="utf-8") as fh:
            json.dump({"pid": os.getpid(), "argv": sys.argv[1:], "cwd": os.getcwd(),
                       "files": os.listdir("."), "stdin": prompt}, fh)
        os.replace(log + ".tmp", log)
    mode = os.environ.get("FAKE_COACH_MODE", "stream")
    if sys.argv[1:2] == ["exec"]:
        codex(mode, prompt)
        return
    if mode == "auto":
        mode = "json" if "--json-schema" in sys.argv else "stream"
    if mode == "fail":
        sys.stderr.write("something went wrong in the fake coach\n")
        sys.exit(1)
    if mode == "hang":
        time.sleep(60)
        return
    if mode == "spawn":
        grandchild()
        emit({"type": "system", "subtype": "init"})
        emit(delta(DELTAS[0]))
        time.sleep(60)
        return
    if mode == "orphan":
        grandchild()
        mode = "json" if "--json-schema" in sys.argv else "stream"
    if mode == "slow":
        time.sleep(float(os.environ.get("FAKE_COACH_SLOW") or 1))
        mode = "stream"
    if mode in ("json", "json_result"):
        argv = sys.argv[1:]
        schema = argv[argv.index("--json-schema") + 1] if "--json-schema" in argv else ""
        review = json.loads(review_for(schema, prompt))
        out = {"type": "result", "subtype": "success", "is_error": False}
        if mode == "json":
            out["structured_output"] = review
            out["result"] = ""
        else:
            out["result"] = json.dumps(review)
        emit(out)
        return
    emit({"type": "system", "subtype": "init"})
    for text in DELTAS:
        if mode == "garbage":
            sys.stdout.write("not json at all\n")
            emit({"type": "stream_event", "event": {"type": "message_start"}})
            emit([1, 2, 3])
        emit(delta(text))
    emit({"type": "result", "subtype": "success", "is_error": False, "result": "".join(DELTAS)})


if __name__ == "__main__":
    main()
