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
When FAKE_COACH_LOG is set, argv, the working directory and the prompt (stdin) are written there.
When FAKE_COACH_CHILD_LOG is set, spawn and orphan write the grandchild's pid there.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time

DELTAS = ["First ", "point.", "\n2. Second point."]

DEFAULT_REVIEW = {"verdict": "pass", "good": ["clear names"], "wrong": [],
                  "edge_cases": ["empty input"], "next_step": "try the follow-up",
                  "mistakes": [{"bug": "off by one on the last index",
                                "check": "trace the last element by hand", "repeat": False}]}


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


def main():
    prompt = sys.stdin.read()
    log = os.environ.get("FAKE_COACH_LOG")
    if log:
        with open(log + ".tmp", "w", encoding="utf-8") as fh:
            json.dump({"pid": os.getpid(), "argv": sys.argv[1:], "cwd": os.getcwd(),
                       "files": os.listdir("."), "stdin": prompt}, fh)
        os.replace(log + ".tmp", log)
    mode = os.environ.get("FAKE_COACH_MODE", "stream")
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
        review = json.loads(os.environ.get("FAKE_COACH_REVIEW") or json.dumps(DEFAULT_REVIEW))
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
