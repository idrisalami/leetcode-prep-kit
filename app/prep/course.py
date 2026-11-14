"""Read-only view of course/ and the user's notes: listings and the whitelisted document reader."""
from __future__ import annotations

import os
import re

NOTES_DOCS = [("skills-matrix", "Skills matrix"), ("bugs", "Bugs"), ("learnings", "Learnings"),
              ("plan", "Plan"), ("next-session", "Next session"), ("profile", "Profile"),
              ("diagnostic-report", "Diagnostic report")]
MODULE_FILE_RE = re.compile(r"^(\d\d)-.*\.md$")
MODULE_PREFIX_RE = re.compile(r"^Module\s+\d+\s*[:—–-]\s*")
ROOTS = ("course", "my-prep")
MAX_DOC = 2 * 1024 * 1024  # bytes; a larger file is refused


class Forbidden(Exception):
    """The path is outside course/**/*.md and my-prep/**/*.md."""


class TooLarge(Exception):
    """The file is over MAX_DOC bytes."""


class NotFound(Exception):
    """The path is allowed but no such file exists."""


def _first_heading(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if line.startswith("# "):
                    return line[2:].strip()
    except OSError:
        pass
    return None


def _md_files(folder):
    try:
        return sorted(f for f in os.listdir(folder) if f.endswith(".md"))
    except OSError:
        return []


def modules(paths):
    folder = os.path.join(paths.course, "modules")
    out = []
    for name in _md_files(folder):
        match = MODULE_FILE_RE.match(name)
        if match:
            heading = _first_heading(os.path.join(folder, name)) or name[:-3]
            out.append({"id": match.group(1), "title": MODULE_PREFIX_RE.sub("", heading),
                        "path": "course/modules/" + name})
    return out


def reference(paths):
    folder = os.path.join(paths.course, "reference")
    return [{"title": _first_heading(os.path.join(folder, name)) or name[:-3],
             "path": "course/reference/" + name} for name in _md_files(folder)]


def _same_bytes(a, b):
    try:
        with open(a, "rb") as fa, open(b, "rb") as fb:
            return fa.read() == fb.read()
    except OSError:
        return False


def notes_docs(paths):
    """`is_template` is true when the user's file is byte-identical to its template."""
    out = []
    for key, title in NOTES_DOCS:
        mine = os.path.join(paths.my_prep, key + ".md")
        exists = os.path.isfile(mine)
        out.append({"key": key, "title": title, "path": "my-prep/%s.md" % key, "exists": exists,
                    "is_template": exists and _same_bytes(
                        mine, os.path.join(paths.templates, key + ".md"))})
    return out


def _inside(path, folder):
    return path == folder or path.startswith(folder + os.sep)


def read_doc(paths, rel):
    """Read one Markdown file under course/ or my-prep/; anything else is Forbidden."""
    if not isinstance(rel, str) or not rel or "\x00" in rel or "\\" in rel or rel.startswith("/"):
        raise Forbidden(rel)
    parts = rel.split("/")
    if ".." in parts or "" in parts or len(parts) < 2 or parts[0] not in ROOTS \
            or not parts[-1].endswith(".md"):
        raise Forbidden(rel)
    root = os.path.realpath(paths.root)
    allowed = os.path.join(root, parts[0])
    real = os.path.realpath(os.path.join(root, *parts))
    if not _inside(real, allowed) or not real.endswith(".md"):
        raise Forbidden(rel)
    if not os.path.isfile(real):
        raise NotFound(rel)
    with open(real, "rb") as fh:
        raw = fh.read(MAX_DOC + 1)  # never more than the cap and one byte, whatever the size is
    if len(raw) > MAX_DOC:
        raise TooLarge(rel)
    markdown = raw.decode("utf-8", errors="replace")
    title = _first_heading(real) or parts[-1][:-3]
    return {"path": "/".join(parts), "title": title, "markdown": markdown}
