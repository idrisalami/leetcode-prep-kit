"""Test helpers: a temporary kit root, a tiny catalog and a controllable clock."""
from __future__ import annotations

import json
import os
import shutil
import tempfile
from datetime import datetime, timedelta

from app.prep import paths


def make_kit(case, problems=None, with_course=True):
    """Build a temporary kit root; the course tree is copied in, never the user's notes."""
    tmp = tempfile.mkdtemp(prefix="prepkit-")
    case.addCleanup(shutil.rmtree, tmp, True)
    kit = paths.Paths(tmp)
    if with_course:
        shutil.copytree(paths.default().course, kit.course)
    os.makedirs(kit.data)
    with open(os.path.join(kit.data, "problems.json"), "w", encoding="utf-8") as fh:
        json.dump(problems if problems is not None else [], fh)
    return kit


def prob(slug, module, difficulty="Easy", category="Cat"):
    return {"slug": slug, "number": 1, "title": slug.replace("-", " ").title(),
            "difficulty": difficulty, "module": module, "category": category,
            "url": "https://example.invalid/" + slug, "premium": False,
            "statement_source": "leetcode", "skeleton": "class Solution:\n    pass"}


class Clock:
    def __init__(self, start=None):
        self.t = start or datetime(2026, 11, 12, 9, 0, 0)

    def __call__(self):
        return self.t

    def advance(self, **kwargs):
        self.t += timedelta(**kwargs)
