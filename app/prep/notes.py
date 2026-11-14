"""The user's notes in my-prep/: bootstrap from the templates, and surgical line edits.

Every edit rewrites only the lines it means to; the rest of the file stays byte-identical, CRLF
files stay CRLF, and when the expected table or heading is missing the file is left untouched
and the call returns False.
"""
from __future__ import annotations

import os
import re
import stat
import tempfile
import threading

ENC = {"encoding": "utf-8", "errors": "surrogateescape", "newline": ""}
MATRIX_COLUMNS = ("id", "requirement", "module", "priority", "start", "now", "evidence", "last_tested")
ROW_ID_RE = re.compile(r"^[A-Z]\d+$")
HEADING_RE = re.compile(r"^#{1,6}\s+(.*?)\s*$")
ENTRY_RE = re.compile(r"^###\s+(\d{4}-\d{2}-\d{2})(?:\s+\[[^\]]*\])?\s+[—–-]\s*(.*?)\s*$")
# One lock across the whole read-modify-write of every writer in this module.
_LOCK = threading.RLock()
ESCAPED_PIPE_RE = re.compile(r"(\\+)\|")  # a run of backslashes and the pipe it escapes
UNESCAPED_PIPE_RUN_RE = re.compile(r"(\\*)\|")
START_COL, NOW_COL, EVIDENCE_COL, TESTED_COL = 4, 5, 6, 7


def _path(paths, name):
    return os.path.join(paths.my_prep, name)


def _read_lines(path):
    """The file's lines split on \\n only (a CRLF line keeps its trailing \\r), or None when it
    is missing or cannot be read (a directory, no permission, any OSError)."""
    try:
        with open(path, "r", **ENC) as fh:
            return fh.read().split("\n")
    except OSError:
        return None


def _atomic_write(path, text, mode=None):
    """Temp file in the same directory, fsync, os.replace; True on success. On any OSError the
    temp file is removed, the original is untouched and the result is False."""
    tmp = None
    try:
        if mode is None:
            try:
                mode = stat.S_IMODE(os.stat(path).st_mode)
            except FileNotFoundError:
                mode = 0o644
        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path) or ".", prefix=".notes-", suffix=".tmp")
        with os.fdopen(fd, "w", **ENC) as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.chmod(tmp, mode)
        os.replace(tmp, path)
        return True
    except OSError:
        if tmp is not None:
            try:
                os.remove(tmp)
            except OSError:
                pass
        return False


def _write_lines(path, lines):
    return _atomic_write(path, "\n".join(lines))


def _eol(line):
    return "\r" if line.endswith("\r") else ""


def _bare(line):
    return line.rstrip("\r")


def _split_pipes(text):
    """Split on pipes that are not escaped. A pipe is escaped when an odd number of backslashes
    directly precedes it, the rule a GFM renderer uses: `\\|` is a backslash then a column break."""
    parts, cur, run = [], [], 0
    for ch in text:
        if ch == "|" and run % 2 == 0:
            parts.append("".join(cur))
            cur, run = [], 0
            continue
        cur.append(ch)
        run = run + 1 if ch == "\\" else 0
    parts.append("".join(cur))
    return parts


def _unescape_pipes(cell):
    """Undo _cell_text: a run of 2k+1 backslashes before a pipe is k backslashes and the pipe."""
    return ESCAPED_PIPE_RE.sub(lambda m: "\\" * (len(m.group(1)) // 2) + "|", cell)


def _cells(line):
    s = _bare(line).strip()
    if not s.startswith("|"):
        return None
    parts = _split_pipes(s)
    inner = parts[1:-1] if parts[-1] == "" else parts[1:]
    return [_unescape_pipes(c).strip() for c in inner]


def _is_separator(cells):
    return bool(cells) and all(re.match(r"^:?-+:?$", c) for c in cells)


def _one_line(text):
    return " ".join(str(text).split())


def _cell_text(text):
    """One-line cell text; every pipe is escaped, and the backslashes right before it are doubled
    so that the escape is not swallowed (`a\\|b` must not turn into a column break)."""
    return UNESCAPED_PIPE_RUN_RE.sub(lambda m: m.group(1) * 2 + "\\|", _one_line(text))


def _outside_fences(lines):
    """(index, line) for every line that is not inside a ``` block."""
    fenced = False
    for i, line in enumerate(lines):
        if _bare(line).lstrip().startswith("```"):
            fenced = not fenced
            continue
        if not fenced:
            yield i, line


def _section(lines, heading):
    """(start, end) of the lines under `## heading`, or None."""
    for i, line in enumerate(lines):
        if _bare(line).strip() == heading:
            end = len(lines)
            for j in range(i + 1, len(lines)):
                if _bare(lines[j]).startswith("## "):
                    end = j
                    break
            return i + 1, end
    return None


def bootstrap(paths):
    """CLAUDE.md section 1: every template except lesson.md, plus an empty lessons/ directory."""
    with _LOCK:
        os.makedirs(paths.my_prep, exist_ok=True)
        os.makedirs(os.path.join(paths.my_prep, "lessons"), exist_ok=True)
        created = []
        for name in sorted(os.listdir(paths.templates)):
            source = os.path.join(paths.templates, name)
            if name == "lesson.md" or name.startswith(".") or not os.path.isfile(source):
                continue
            target = _path(paths, name)
            if os.path.exists(target):
                continue
            try:
                with open(source, "r", **ENC) as fh:
                    text = fh.read()
                mode = stat.S_IMODE(os.stat(source).st_mode)
            except OSError:
                continue
            if _atomic_write(target, text, mode):
                created.append(name)
        return created


# ---- skills matrix --------------------------------------------------------

def read_matrix(paths):
    lines = _read_lines(_path(paths, "skills-matrix.md"))
    if lines is None:
        return []
    groups = []
    title = ""
    for _, line in _outside_fences(lines):
        heading = HEADING_RE.match(_bare(line))
        if heading:
            title = heading.group(1)
            continue
        cells = _cells(line)
        if cells and len(cells) >= len(MATRIX_COLUMNS) and ROW_ID_RE.match(cells[0]):
            row = dict(zip(MATRIX_COLUMNS, cells))
            if not groups or groups[-1]["title"] != title:
                groups.append({"title": title, "rows": []})
            groups[-1]["rows"].append(row)
    return groups


EVIDENCE_PLACEHOLDERS = ("", "?", "-", "\u2014")


def merge_evidence(old, app_segment):
    """The Evidence cell after a submit: segments split on `; `, every one that ends in `(app)`
    dropped, the rest kept in order, the new app segment last. Hand-written text stays."""
    old = (old or "").strip()
    if old in EVIDENCE_PLACEHOLDERS:
        return app_segment
    kept = [seg for seg in old.split("; ") if seg.strip() and not seg.strip().endswith("(app)")]
    return "; ".join(kept + [app_segment])


def update_matrix_row(paths, row_id, now, evidence, day):
    """Set Now (and Start while it is `?`), Last tested, and the app's segment of Evidence
    (hand-written segments are kept, see merge_evidence) on one row."""
    with _LOCK:
        path = _path(paths, "skills-matrix.md")
        lines = _read_lines(path)
        if lines is None:
            return False
        for i, line in _outside_fences(lines):
            cells = _cells(line)
            if not cells or len(cells) < len(MATRIX_COLUMNS) or cells[0] != row_id:
                continue
            segs = _split_pipes(_bare(line))  # segs[0] is the text before the first pipe

            def put(col, value):
                segs[col + 1] = " %s " % value if value else " "
            if now is not None:
                if cells[START_COL] == "?":
                    put(START_COL, _cell_text(now))
                put(NOW_COL, _cell_text(now))
            put(EVIDENCE_COL, _cell_text(merge_evidence(cells[EVIDENCE_COL], evidence)))
            put(TESTED_COL, _cell_text(day))
            lines[i] = "|".join(segs) + _eol(line)
            return _write_lines(path, lines)
        return False


# ---- bugs ----------------------------------------------------------------

def _table_rows(lines, heading, header_first_cell):
    """Data rows (as cell lists) of the first table under `## heading`."""
    span = _section(lines, heading)
    if not span:
        return []
    rows = []
    for line in lines[span[0]:span[1]]:
        cells = _cells(line)
        if cells and len(cells) >= 2 and not _is_separator(cells) \
                and cells[0].lower() != header_first_cell:
            rows.append(cells)
    return rows


def _is_real(text):
    return bool(text) and not (text.startswith("<") and text.endswith(">"))


def top_bugs(paths):
    lines = _read_lines(_path(paths, "bugs.md"))
    if lines is None:
        return []
    out = []
    for cells in _table_rows(lines, "## My top 5", "#"):
        if len(cells) >= 3 and _is_real(cells[1]):
            out.append({"bug": cells[1], "check": cells[2]})
    return out


def bug_log(paths):
    lines = _read_lines(_path(paths, "bugs.md"))
    if lines is None:
        return []
    return [cells[0] for cells in _table_rows(lines, "## Log", "bug") if _is_real(cells[0])]


def _log_header_ok(cells):
    """The Log table must read Bug | The check that catches it | Where it appeared ..."""
    return (cells is not None and len(cells) == 3 and cells[0].lower() == "bug"
            and cells[1].lower().startswith("the check") and cells[2].lower().startswith("where"))


def append_bug_log_result(paths, bug, check, where):
    """Newest first: the new row goes first, taking over the template's empty placeholder row.
    Returns (True, None) or (False, reason); a table with other columns is left untouched."""
    with _LOCK:
        path = _path(paths, "bugs.md")
        lines = _read_lines(path)
        span = _section(lines, "## Log") if lines is not None else None
        if not span:
            return False, "the file or its Log section is missing"
        table = [i for i in range(*span) if _cells(lines[i]) is not None]
        if len(table) < 2 or not _is_separator(_cells(lines[table[1]])) or table[1] != table[0] + 1:
            return False, "the Log section has no table"
        if not _log_header_ok(_cells(lines[table[0]])):
            return False, ("the Log table does not have the columns Bug, The check that catches "
                           "it, Where it appeared, so the file was left as it is")
        eol = _eol(lines[table[0]])
        row = "| %s | %s | %s |%s" % (_cell_text(bug), _cell_text(check), _cell_text(where), eol)
        first = table[1] + 1
        cells = _cells(lines[first]) if first < len(lines) else None
        if cells is not None and not any(cells):
            lines[first] = row
        else:
            lines.insert(first, row)
        if not _write_lines(path, lines):
            return False, "the write failed"
        return True, None


def append_bug_log(paths, bug, check, where):
    return append_bug_log_result(paths, bug, check, where)[0]


# ---- learnings -----------------------------------------------------------

def recent_learnings(paths, n=3):
    lines = _read_lines(_path(paths, "learnings.md"))
    span = _section(lines, "## Entries") if lines is not None else None
    if not span:
        return []
    entries = []
    collecting = False
    for line in lines[span[0]:span[1]]:
        line = _bare(line)
        match = ENTRY_RE.match(line)
        if match:
            entries.append({"date": match.group(1), "title": match.group(2), "parts": []})
            collecting = False
        elif entries and line.startswith("**The rule:**"):
            entries[-1]["parts"].append(line[len("**The rule:**"):].strip())
            collecting = True
        elif collecting and line.strip() and not line.startswith("#"):
            entries[-1]["parts"].append(line.strip())
        else:
            collecting = False
    return [{"date": e["date"], "title": e["title"], "rule": " ".join(p for p in e["parts"] if p)}
            for e in entries[:n]]


def append_learning(paths, day, finding, what_happened, rule):
    """Insert a dated entry straight under `## Entries`, in the template's entry format."""
    with _LOCK:
        path = _path(paths, "learnings.md")
        lines = _read_lines(path)
        if lines is None:
            return False
        for i, line in enumerate(lines):
            if _bare(line).strip() == "## Entries":
                break
        else:
            return False
        eol = _eol(lines[i])
        block = ["", "### %s — %s" % (_one_line(day), _one_line(finding)), "",
                 "**What happened:** %s" % _one_line(what_happened), "",
                 "**The rule:** %s" % _one_line(rule)]
        block = [b + eol for b in block]
        after = lines[i + 1] if i + 1 < len(lines) else None
        if after is None or after.strip() != "":
            block.append(eol)
        lines[i + 1:i + 1] = block
        if after is None:
            lines.append("")
        return _write_lines(path, lines)
