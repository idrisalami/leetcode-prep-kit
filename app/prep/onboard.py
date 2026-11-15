"""The first steps, done in the app: discovery, the module 00 self-check, the diagnostic and the
scoring. The coach only talks and answers in JSON; every file in my-prep/ is written here, so the
coach never gets a write tool. The files are the same ones the terminal route writes (CLAUDE.md
section 3), so either route can pick up where the other left off.
"""
from __future__ import annotations

import glob
import os
import re
from datetime import date

from app.prep import notes
from app.prep.notes import (_LOCK, _bare, _cell_text, _cells, _eol, _one_line, _outside_fences,
                            _path, _read_lines, _section, _split_pipes, _write_lines)

# ---- the course files -------------------------------------------------------

PROBLEM_ROW_RE = re.compile(
    r"^\|\s*(\d+)\s*\|\s*\[([^\]]+)\]\((https?://[^)]+)\)\s*\(LC\s*(\d+)\)\s*\|\s*(\w+)\s*\|"
    r"\s*(\d+)\s*min\s*\|")
SLUG_FROM_URL_RE = re.compile(r"/problems/([a-z0-9-]+)/?")
NUMBERED_RE = re.compile(r"^(\d+)\.\s+(.*)$")
BLOCK_HEADING_RE = re.compile(r"^###\s+(Block \d+)\s+[—–-]\s+(.*?)\s*(?:\((\d+) min\))?\s*$")

MODULE_BLOCKS = (("01", "Arrays and hashing"), ("02", "Stacks and queues"),
                 ("03", "Two pointers and sliding window"), ("04", "Binary search"),
                 ("05", "Linked lists"), ("06", "Trees"), ("07", "Backtracking"),
                 ("08", "Graphs"), ("09", "Dynamic programming"),
                 ("10", "Heaps, top-K and selection"))
OUTCOMES = ("solved clean", "solved with bugs", "partial", "stuck")
LEVELS = ("0", "1", "2", "3")
PRIORITIES = ("P0", "P1", "P2", "not flagged")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
OVERALL_QUESTIONS = (
    ("worst", "Which problem felt worst, and why?"),
    ("idea", "At any point did you know the idea but not how to write it?"),
    ("aloud", "How did talking out loud feel: natural, or did it interfere with thinking?"))


def _read(path):
    lines = _read_lines(path)
    return [] if lines is None else [_bare(line) for line in lines]


def _module00_path(paths):
    found = sorted(glob.glob(os.path.join(paths.course, "modules", "00-*.md")))
    return found[0] if found else None


def _numbered(lines, start, end):
    """{n: text} of the `1. ...` items between two line numbers; a wrapped item continues."""
    out, cur = {}, None
    for line in lines[start:end]:
        m = NUMBERED_RE.match(line.strip())
        if m:
            cur = int(m.group(1))
            out[cur] = m.group(2).strip()
        elif cur is not None and line.strip() and not line.startswith(("#", "---")):
            out[cur] += " " + line.strip()
        elif not line.strip():
            cur = None if cur is not None and out.get(cur) else cur
    return out


def self_check(paths):
    """The module 00 self-check: [{n, question, answer}] from its two sections, in order."""
    path = _module00_path(paths)
    lines = _read(path) if path else []
    q = _section(lines, "## Self-check")
    a = _section(lines, "## Self-check answers")
    if not q or not a:
        return []
    questions, answers = _numbered(lines, *q), _numbered(lines, *a)
    return [{"n": n, "question": questions[n], "answer": answers.get(n, "")}
            for n in sorted(questions)]


def diagnostic(paths):
    """The diagnostic from course/diagnostic.md: its problems, rules and scoring rows."""
    lines = _read(os.path.join(paths.course, "diagnostic.md"))
    problems, block = [], None
    for line in lines:
        b = BLOCK_HEADING_RE.match(line)
        if b:
            block = "%s, %s" % (b.group(1), b.group(2).strip())
            continue
        m = PROBLEM_ROW_RE.match(line)
        if not m:
            continue
        slug = SLUG_FROM_URL_RE.search(m.group(3))
        problems.append({"n": int(m.group(1)), "title": m.group(2), "url": m.group(3),
                         "slug": slug.group(1) if slug else "", "number": int(m.group(4)),
                         "difficulty": m.group(5), "minutes": int(m.group(6)), "block": block})
    rules = []
    for i, line in enumerate(lines):
        if line.startswith("## Rules"):
            end = next((j for j in range(i + 1, len(lines)) if lines[j].startswith("## ")),
                       len(lines))
            rules = [text for _, text in sorted(_numbered(lines, i + 1, end).items())]
            break
    rows = {}
    span = _section(lines, "## For scoring — read after you finish")
    if span:
        for line in lines[span[0]:span[1]]:
            cells = _cells(line)
            if cells and cells[0].isdigit() and len(cells) >= 4:
                rows[int(cells[0])] = {"tests": cells[2],
                                       "rows": [r.strip() for r in cells[3].split(",") if r.strip()]}
    for p in problems:
        p.update(rows.get(p["n"], {"tests": "", "rows": []}))
    return {"problems": problems, "rules": rules}


# ---- the coach: rules, prompts and answer shapes -----------------------------

TOPICS = (
    ("target", "Target", "the role and level, the companies or kind of company, the interview "
     "format if known, how many coding rounds, and the language the interviews are in"),
    ("timeline", "Timeline", "the interview dates if known, and the hours per week they have"),
    ("goals", "Goals", "what success looks like, and which rounds worry them"),
    ("experience", "Experience", "years and kind of engineering work, CS background, and how "
     "fluent they are in Python"),
    ("leetcode_history", "LeetCode history", "roughly how many problems solved, which topics, "
     "the Easy/Medium/Hard mix, and past technical interviews and how they went"),
    ("self_assessment", "Self-assessment", "the topics they think are strong and weak"),
    ("preferences", "Preferences", "anything they want changed in how the coach works"),
    ("other_rounds", "Other rounds", "whether they also face system design or behavioural "
     "rounds (outside this kit)"))

CHAT_SYSTEM = """You run the discovery conversation of a coding-interview prep kit, inside its app. \
The answers set the plan: pace, priorities, and which modules get the most time. Rules:
1. Ask one or two questions at a time, in plain words, then stop and wait for the answer.
2. Cover these topics in this order, skipping anything the user already answered:
%s
3. Keep each reply short: a few words on what they said, then the next question. No praise, no \
advice, no lists.
4. "I don't know" is a fine answer: say it will be recorded as unknown, and move on.
5. Do not teach, solve problems or plan here. That comes later.
6. When every topic is covered, sum up what you heard in three or four short lines, and tell \
the user to press "Finish discovery" under the chat when it looks right.
7. Plain text. No Markdown headings or tables.""" % "\n".join(
    "- %s: %s." % (label, what) for _, label, what in TOPICS)

FILL_SYSTEM = """You turn the notes of a coding-interview prep kit's first steps into JSON. \
The app writes the files from your answer; you never write files. Write in the second person \
("you"), in plain words, one or two lines per field. Use only what the user said or did. Where \
something was not said, write "unknown". Never invent dates, companies or numbers."""

_STR = {"type": "string"}


def _obj(props):
    return {"type": "object", "additionalProperties": False,
            "properties": props, "required": list(props)}


def _arr(items):
    return {"type": "array", "items": items}


NEXT_SESSION_SCHEMA = _obj({k: _STR for k in ("next_up", "where", "why", "what_to_do",
                                              "watch_for", "at_the_end", "pending")})

DISCOVERY_SCHEMA = _obj({
    "profile": _obj({key: _STR for key, _, _ in TOPICS}),
    "timeline": _obj({k: _STR for k in ("interview_dates", "weeks_left", "hours_per_week",
                                        "coding_rounds")}),
    "priorities": _arr(_obj({"id": _STR, "priority": {"type": "string", "enum": list(PRIORITIES)},
                             "why": _STR})),
    "what_next": _STR,
    "next_session": NEXT_SESSION_SCHEMA})

SELFCHECK_SCHEMA = _obj({
    "marks": _arr(_obj({"n": {"type": "integer"}, "correct": {"type": "boolean"}, "note": _STR})),
    "next_session": NEXT_SESSION_SCHEMA})

DIAGNOSTIC_SCHEMA = _obj({
    "problems": _arr(_obj({"slug": _STR, "outcome": {"type": "string", "enum": list(OUTCOMES)},
                           "rows_scored": _arr(_STR), "comment": _STR})),
    "matrix": _arr(_obj({"id": _STR, "level": {"type": "string", "enum": list(LEVELS)},
                         "evidence": _STR})),
    "known_gaps": _arr(_STR),
    "blocks": _arr(_obj({"module": _STR, "start": _STR, "end": _STR, "hours": _STR})),
    "weekly_hours": _obj({k: _STR for k in ("read", "drills", "review", "revision", "other")}),
    "what_next": _STR,
    "next_session": NEXT_SESSION_SCHEMA})


def _transcript(chat):
    return "\n\n".join("%s: %s" % ("Coach" if m.get("role") == "coach" else "User",
                                   (m.get("text") or "").strip()) for m in chat)


def chat_prompt(chat, today):
    if not chat:
        return ("Today is %s. Open the discovery: one line of greeting, one line on what this is "
                "for (about ten minutes, and it sets the plan), then the first question."
                % today.isoformat())
    return ("Today is %s.\n\nThe conversation so far:\n\n%s\n\nWrite the coach's next message."
            % (today.isoformat(), _transcript(chat)))


def _matrix_lines(paths):
    out = []
    for group in notes.read_matrix(paths):
        for r in group["rows"]:
            out.append("%s | %s | priority %s | now %s" % (r["id"], r["requirement"],
                                                            r["priority"], r["now"]))
    return "\n".join(out)


def discovery_prompt(paths, chat, today):
    return """Today is %s. The discovery conversation is over. Fill the JSON from it.

profile: one entry per topic, in the user's own words, tidied. "unknown" where it was not said.
timeline: interview_dates as YYYY-MM-DD (comma-separated if several), or "not set";
weeks_left from today to the first interview date, or "unknown"; hours_per_week and
coding_rounds as said, or "unknown".
priorities: only the matrix rows whose priority changes. Always set A13 to A18 (outside the kit:
high only if the target needs them) and C9 (P0 if the interviews are in a language that is not
the user's first, else "not flagged"). Re-set an A row only when the target, level or timeline
clearly calls for it. why: a few words.
what_next: one or two lines: the module 00 self-check comes next, then the diagnostic, which takes
about 2h50 in one sitting, so it needs a long free slot soon.
next_session: the handoff for the next session, which is the module 00 self-check. next_up is a
few words. The other fields are one or two lines each.

The matrix rows (id | requirement | priority | now):
%s

The conversation:

%s""" % (today.isoformat(), _matrix_lines(paths), _transcript(chat))


def selfcheck_prompt(items, answers):
    parts = []
    for it in items:
        parts.append("%d. Question: %s\nReference answer: %s\nThe user's answer: %s" % (
            it["n"], it["question"], it["answer"],
            (answers.get(str(it["n"])) or "").strip() or "(blank)"))
    return """Mark the module 00 self-check of a coding-interview prep kit.

marks: one per question. correct is true when the answer has the key point of the reference
answer, in any words; a blank or a wrong key point is false. note: one short line on what was
right or what was missing. Do not restate the whole reference answer: the app shows it.
next_session: the handoff for the next session, which is the coding diagnostic (seven problems,
about 2h50 in one sitting, no running the code). Mention the sections to re-read for the missed
questions under what_to_do.

%s""" % "\n\n".join(parts)


def _fence(code):
    code = code or ""
    ticks = "```"
    while ticks in code:
        ticks += "`"
    return "%spython\n%s\n%s" % (ticks, code.rstrip("\n"), ticks)


def diagnostic_prompt(paths, problems, overall, today):
    blocks = []
    for p in problems:
        blocks.append("""%d. %s (LC %d, %s, slug %s). Scores rows %s. It tests: %s
Time used: %s of %d min.
Result when run on the kit's tests: %s
The user's notes: %s
Code:
%s""" % (p["n"], p["title"], p["number"], p["difficulty"], p["slug"],
         ", ".join(p["rows"]) or "-",
         p["tests"], _minutes(p.get("seconds")), p["minutes"], p["result_line"],
         _one_line(p.get("notes") or "") or "(none)", _fence(p.get("code"))))
    over = "\n".join("- %s %s" % (q, _one_line(overall.get(k) or "") or "(blank)")
                     for k, q in OVERALL_QUESTIONS)
    profile = "\n".join(_read(_path(paths, "profile.md")))
    timeline = "\n".join(_read(_path(paths, "plan.md"))[:14])
    return """Today is %s. Score the coding diagnostic of a coding-interview prep kit and write
the plan. The user wrote every answer with no way to run it; the app has now run each one on the
kit's tests, and the results are below.

Levels: 0 can't start a standard problem on the topic; 1 solves with hints or past the time
limit (a working idea that did not reach a correct solution in time is 1, no working idea is 0);
2 solves a Medium unaided but slowly or with bugs; 3 solves a Medium in 25 minutes or less,
clean, complexity stated. For the B and C rows the scale is the habit: 0 never, 3 every time.

problems: one per problem, by slug. outcome from the test results and the code. rows_scored: the
problem's A rows plus the B and C rows it showed (B1 complexity stated, B2 Python without an IDE,
B3 stdlib toolkit, B4 invariants, B5 reading the signature, B6 built-ins, C1 clarifies, C2 brute
force first, C3 gets unstuck, C4 readable code, C5 time, C10 traces by hand, C11 edge cases).
comment: one line on what the code shows. Never write a corrected solution.
matrix: one entry per row the diagnostic touched, with the level and one line of evidence (the
problems and what happened). Rows it did not touch are left out.
known_gaps: the rows that matter most for the target and score lowest, one line each.
blocks: all ten modules in order (01 to 10), each with start and end dates (YYYY-MM-DD, from
tomorrow, back to back, fitting the time left before the interview if there is a date) and the
hours, as a number. A module the diagnostic shows the user owns gets fewer hours, never removed.
weekly_hours: hours per week for reading, drills, review, revision, and other rounds, adding up
to the hours per week in the profile.
what_next: one or two lines: block 01 comes next, and why.
next_session: the handoff for the next session, which is block 01, Arrays and hashing.

The profile:
%s

The plan so far:
%s

The matrix rows (id | requirement | priority | now):
%s

The seven problems:

%s

The overall questions:
%s""" % (today.isoformat(), profile, timeline, _matrix_lines(paths), "\n\n".join(blocks), over)


def _minutes(seconds):
    try:
        return "%d min" % max(0, round(int(seconds) / 60))
    except (TypeError, ValueError):
        return "unknown"


# ---- normalising the coach's answers -----------------------------------------

def _s(value, limit=600):
    return _one_line(value)[:limit] if isinstance(value, (str, int, float)) else ""


def _next_session(raw):
    raw = raw if isinstance(raw, dict) else {}
    return {k: _s(raw.get(k), 1200) for k in NEXT_SESSION_SCHEMA["properties"]}


def _row_ids(paths):
    return {r["id"] for g in notes.read_matrix(paths) for r in g["rows"]}


def normalise_discovery(raw, paths):
    if not isinstance(raw, dict) or not isinstance(raw.get("profile"), dict):
        return None
    ids = _row_ids(paths)
    prio = []
    for p in raw.get("priorities") or []:
        if isinstance(p, dict) and p.get("id") in ids and p.get("priority") in PRIORITIES:
            prio.append({"id": p["id"], "priority": p["priority"], "why": _s(p.get("why"))})
    tl = raw.get("timeline") if isinstance(raw.get("timeline"), dict) else {}
    return {"profile": {k: _s(raw["profile"].get(k), 2000) or "unknown" for k, _, _ in TOPICS},
            "timeline": {k: _s(tl.get(k)) or "unknown"
                         for k in DISCOVERY_SCHEMA["properties"]["timeline"]["properties"]},
            "priorities": prio, "what_next": _s(raw.get("what_next"), 1200),
            "next_session": _next_session(raw.get("next_session"))}


def normalise_selfcheck(raw, items):
    if not isinstance(raw, dict) or not isinstance(raw.get("marks"), list):
        return None
    by_n = {}
    for m in raw["marks"]:
        if isinstance(m, dict) and isinstance(m.get("n"), int):
            by_n[m["n"]] = {"n": m["n"], "correct": m.get("correct") is True,
                            "note": _s(m.get("note"))}
    marks = [by_n.get(it["n"], {"n": it["n"], "correct": False, "note": "not marked"})
             for it in items]
    return {"marks": marks, "next_session": _next_session(raw.get("next_session"))}


def normalise_diagnostic(raw, paths, problems):
    if not isinstance(raw, dict) or not isinstance(raw.get("problems"), list):
        return None
    ids = _row_ids(paths)
    slugs = {p["slug"] for p in problems}
    per = {}
    for p in raw["problems"]:
        if isinstance(p, dict) and p.get("slug") in slugs:
            per[p["slug"]] = {"outcome": p.get("outcome") if p.get("outcome") in OUTCOMES
                              else "stuck",
                              "rows_scored": [r for r in p.get("rows_scored") or []
                                              if isinstance(r, str) and r in ids],
                              "comment": _s(p.get("comment"))}
    matrix = []
    for m in raw.get("matrix") or []:
        if isinstance(m, dict) and m.get("id") in ids and str(m.get("level")) in LEVELS:
            matrix.append({"id": m["id"], "level": str(m["level"]),
                           "evidence": _s(m.get("evidence"), 300)})
    blocks = {}
    for b in raw.get("blocks") or []:
        if not isinstance(b, dict):
            continue
        mid = str(b.get("module", "")).strip()[:2]
        start, end = _s(b.get("start")), _s(b.get("end"))
        hours = re.sub(r"[^\d.]", "", _s(b.get("hours")))
        if mid in dict(MODULE_BLOCKS) and DATE_RE.match(start) and DATE_RE.match(end) and hours:
            blocks[mid] = {"start": start, "end": end, "hours": hours}
    wh = raw.get("weekly_hours") if isinstance(raw.get("weekly_hours"), dict) else {}
    return {"problems": per, "matrix": matrix,
            "known_gaps": [_s(g, 300) for g in raw.get("known_gaps") or [] if _s(g)],
            "blocks": blocks,
            "weekly_hours": {k: _s(wh.get(k), 40)
                             for k in DIAGNOSTIC_SCHEMA["properties"]["weekly_hours"]["properties"]},
            "what_next": _s(raw.get("what_next"), 1200),
            "next_session": _next_session(raw.get("next_session"))}


# ---- writing the notes --------------------------------------------------------

class _File:
    """One my-prep file read under the notes lock, edited as a list of lines, written once."""

    def __init__(self, paths, name, report):
        self.name, self.report = name, report
        self.path = _path(paths, name)
        self.lines = _read_lines(self.path)
        self.changed = False

    def ok(self):
        if self.lines is None:
            self.report["skipped"].append("%s: the file is missing." % self.name)
        return self.lines is not None

    def miss(self, what):
        self.report["skipped"].append("%s: %s" % (self.name, what))

    def save(self):
        if not self.changed:
            return
        if _write_lines(self.path, self.lines):
            self.report["written"].append(self.name)
        else:
            self.report["skipped"].append("%s: the write failed." % self.name)


def _report():
    return {"written": [], "skipped": []}


def _replace_body(f, heading, body):
    """Everything under `heading` up to the next `## ` becomes the body, set off by blank lines."""
    span = _section(f.lines, heading)
    if span is None:
        f.miss("no %s heading." % heading)
        return False
    eol = _eol(f.lines[span[0] - 1])
    f.lines[span[0]:span[1]] = [eol] + [line + eol for line in body] + [eol]
    f.changed = True
    return True


def _label(cell):
    return cell.strip().strip("*`_ ").lower()


def _set_cells(f, heading, values):
    """In the table under `heading`, put values[label] in the second cell of the row whose first
    cell (bold and backticks stripped) is that label."""
    span = _section(f.lines, heading)
    if span is None:
        f.miss("no %s heading." % heading)
        return
    left = dict(values)
    for i in range(*span):
        cells = _cells(f.lines[i])
        if not cells or len(cells) < 2 or _label(cells[0]) not in left:
            continue
        segs = _split_pipes(_bare(f.lines[i]))
        segs[2] = " %s " % _cell_text(left.pop(_label(cells[0])))
        f.lines[i] = "|".join(segs) + _eol(f.lines[i])
        f.changed = True
    for label in left:
        f.miss("no \"%s\" row under %s." % (label, heading))


def _tick(f, prefix, edit=None):
    """Tick the Blocks line whose label starts with prefix; edit(label) may rewrite the label."""
    for i, line in _outside_fences(f.lines):
        m = notes.PLAN_TICK_RE.match(_bare(line))
        if not m or not m.group(2).lstrip("*_` ").lower().startswith(prefix):
            continue
        label = edit(m.group(2)) if edit else m.group(2)
        head = _bare(line)[:m.start(1) - 1]
        f.lines[i] = "%s[x] %s%s" % (head, label, _eol(line))
        f.changed = True
        return True
    f.miss("no \"%s\" line under ## Blocks." % prefix)
    return False


def _quote(value):
    return "`%s`" % str(value).replace("`", "'")


def write_next_session(paths, ns, read_also, report):
    """Rewrite next-session.md below its preamble (everything up to the first `---` line)."""
    f = _File(paths, "next-session.md", report)
    if not f.ok():
        return
    cut = next((i for i, line in enumerate(f.lines) if _bare(line).strip() == "---"), None)
    if cut is None:
        f.miss("no --- line after the preamble.")
        return
    eol = _eol(f.lines[cut])
    body = ["", "## Next up: %s" % (ns["next_up"] or "the next step"), "",
            "## Read first", "",
            "- `my-prep/profile.md`, `my-prep/plan.md`, `my-prep/skills-matrix.md`",
            "- `my-prep/bugs.md` (the top 5), `my-prep/learnings.md` (the latest entries)",
            "- %s" % read_also]
    for heading, key in (("Where things stand", "where"), ("Why this step, and why now", "why"),
                         ("What to do", "what_to_do"), ("Watch for", "watch_for"),
                         ("At the end", "at_the_end"), ("Pending", "pending")):
        body += ["", "## %s" % heading, "", ns[key] or "Nothing."]
    f.lines[cut + 1:] = [line + eol for line in body] + [""]
    f.changed = True
    f.save()


def write_discovery(paths, answer, today):
    """profile.md, the plan's Timeline and What's next, the matrix Priority column and
    next-session.md; then Discovery is ticked. Returns {"written", "skipped"}."""
    report = _report()
    with _LOCK:
        f = _File(paths, "profile.md", report)
        if f.ok():
            for key, label, _ in TOPICS:
                _replace_body(f, "## %s" % label, [answer["profile"][key]])
            f.save()
        f = _File(paths, "skills-matrix.md", report)
        if f.ok():
            want = {p["id"]: p["priority"] for p in answer["priorities"]}
            for i, line in _outside_fences(f.lines):
                cells = _cells(line)
                if cells and len(cells) >= len(notes.MATRIX_COLUMNS) and cells[0] in want:
                    segs = _split_pipes(_bare(line))
                    segs[notes.MATRIX_COLUMNS.index("priority") + 1] = " %s " % want[cells[0]]
                    f.lines[i] = "|".join(segs) + _eol(line)
                    f.changed = True
            f.save()
        f = _File(paths, "plan.md", report)
        if f.ok():
            tl = answer["timeline"]
            _set_cells(f, "## Timeline", {"today": _quote(today.isoformat()),
                                          "interview date(s)": tl["interview_dates"],
                                          "weeks left": tl["weeks_left"],
                                          "hours per week": tl["hours_per_week"],
                                          "coding rounds expected": tl["coding_rounds"]})
            if answer["what_next"]:
                _replace_body(f, "## What's next", [answer["what_next"]])
            _tick(f, "discovery")
            f.save()
        write_next_session(paths, answer["next_session"],
                           "`course/modules/00-before-you-start.md`, its §Self-check", report)
    return report


def selfcheck_summary(marks):
    missed = [str(m["n"]) for m in marks if not m["correct"]]
    return {"score": len(marks) - len(missed), "total": len(marks), "missed": missed}


def write_selfcheck(paths, result):
    report = _report()
    s = selfcheck_summary(result["marks"])
    text = "Self-check: `%d/%d`, missed `%s`" % (s["score"], s["total"],
                                                 ", ".join(s["missed"]) or "none")
    with _LOCK:
        f = _File(paths, "plan.md", report)
        if f.ok():
            _tick(f, "module 00", lambda label: re.sub(r"Self-check: .*$", text, label)
                  if "Self-check:" in label else label.rstrip(". ") + ". " + text)
            f.save()
        write_next_session(paths, result["next_session"],
                           "`course/diagnostic.md`, the rules first", report)
    return report


def result_line(result):
    """The Review table's "Result when run" and "First failing input" for one run."""
    fatal = result.get("fatal")
    if fatal:
        where = " on line %s" % fatal["line"] if fatal.get("line") else ""
        return ("did not run: %s%s" % (fatal.get("type") or "error", where),
                _s(fatal.get("message"), 200) or "-")
    passed, total = result.get("passed", 0), result.get("total", 0)
    first = next((r for r in result.get("results") or [] if r.get("status") != "pass"), None)
    if first is None:
        return "%d/%d passed" % (passed, total), "-"
    got = first.get("got") if first.get("status") == "fail" else first.get("message") or \
        first.get("status")
    return ("%d/%d passed" % (passed, total),
            _s("%s; expected %s, got %s" % (first.get("input"), first.get("expected"), got), 300))


def write_diagnostic(paths, problems, overall, scored, today):
    """diagnostic-report.md, the matrix (Start, Now, Evidence, Last tested, Known gaps), the
    plan (Weekly hours, Blocks, What's next) and next-session.md; then Diagnostic and Scoring
    are ticked."""
    report = _report()
    day = today.isoformat()
    with _LOCK:
        f = _File(paths, "diagnostic-report.md", report)
        if f.ok():
            body = []
            for p in problems:
                s = scored["problems"].get(p["slug"], {"outcome": "stuck", "rows_scored": [],
                                                       "comment": ""})
                body += ["```",
                         "Problem:              %d. %s (LC %d)" % (p["n"], p["title"], p["number"]),
                         "Time used:            %s / %d min" % (_minutes(p.get("seconds")),
                                                                p["minutes"]),
                         "Outcome:              %s" % s["outcome"],
                         "Result when run:      %s" % p["result_line"],
                         "My notes:             %s" % (_one_line(p.get("notes") or "") or "none"),
                         "Coach:                %s" % (s["comment"] or "-"),
                         "```", "", "Code:", "", _fence(p.get("code")), ""]
            _replace_body(f, "## Per problem", body[:-1])
            _replace_body(f, "## Overall, at the end",
                          ["- %s %s" % (q, _one_line(overall.get(k) or "") or "(blank)")
                           for k, q in OVERALL_QUESTIONS])
            rows = ["*Filled in by the app after running each answer on the kit's tests, and "
                    "scored by the coach on %s.*" % day, "",
                    "| # | Problem | Result when run | First failing input | Rows scored |",
                    "|---|---|---|---|---|"]
            for p in problems:
                s = scored["problems"].get(p["slug"], {"rows_scored": []})
                rows.append("| %d | %s | %s | %s | %s |" % (
                    p["n"], _cell_text(p["title"]), _cell_text(p["result_line"]),
                    _cell_text(p["first_failing"]),
                    _cell_text(", ".join(s["rows_scored"]) or ", ".join(p["rows"]))))
            _replace_body(f, "## Review", rows)
            f.save()
        f = _File(paths, "skills-matrix.md", report)
        if f.ok():
            want = {m["id"]: m for m in scored["matrix"]}
            for i, line in _outside_fences(f.lines):
                cells = _cells(line)
                if not cells or len(cells) < len(notes.MATRIX_COLUMNS) or cells[0] not in want:
                    continue
                m = want[cells[0]]
                segs = _split_pipes(_bare(line))
                if cells[notes.START_COL] == "?":
                    segs[notes.START_COL + 1] = " %s " % m["level"]
                segs[notes.NOW_COL + 1] = " %s " % m["level"]
                old = [seg for seg in cells[notes.EVIDENCE_COL].split("; ")
                       if seg.strip() not in notes.EVIDENCE_PLACEHOLDERS
                       and not seg.strip().endswith("(diagnostic)")]
                segs[notes.EVIDENCE_COL + 1] = " %s " % _cell_text(
                    "; ".join(old + ["%s, %s (diagnostic)" % (m["evidence"] or "diagnostic",
                                                               day)]))
                segs[notes.TESTED_COL + 1] = " %s " % day
                f.lines[i] = "|".join(segs) + _eol(line)
                f.changed = True
            if scored["known_gaps"]:
                _replace_body(f, "## Known gaps", ["- %s" % g for g in scored["known_gaps"]])
            f.save()
        f = _File(paths, "plan.md", report)
        if f.ok():
            wh = scored["weekly_hours"]
            _set_cells(f, "## Weekly hours", {
                "read the module §0 and answer its self-check": wh["read"],
                "drills, cold, four-part submissions": wh["drills"],
                "review: adversarial testing of your submissions, then the lesson": wh["review"],
                "revision: the matrix rows with the oldest last tested, and the bugs.md top 5":
                    wh["revision"],
                "other rounds (outside the kit)": wh["other"]})
            for i, line in _outside_fences(f.lines):
                m = notes.PLAN_TICK_RE.match(_bare(line))
                if not m:
                    continue
                b = scored["blocks"].get(m.group(2).lstrip("*_` ")[:2])
                if b and "Planned:" in line:
                    planned = "Planned: `%s` to `%s`, `%s` hours" % (b["start"], b["end"],
                                                                      b["hours"])
                    f.lines[i] = re.sub(r"Planned: .*? hours", lambda _: planned, line, count=1)
                    f.changed = True
            if scored["what_next"]:
                _replace_body(f, "## What's next", [scored["what_next"]])
            _tick(f, "diagnostic")
            _tick(f, "scoring")
            f.save()
        write_next_session(paths, scored["next_session"],
                           "`course/modules/01-arrays-hashing.md`", report)
    return report


def today_iso(value):
    return value.isoformat() if isinstance(value, date) else str(value)
