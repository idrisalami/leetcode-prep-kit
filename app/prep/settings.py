"""The small choices the app keeps outside state.json: for now, which coach is connected.

They live in my-prep/app/settings.json. A missing or unreadable file means "nothing chosen yet",
never an error: the welcome page then asks again.
"""
from __future__ import annotations

import json
import os

COACH_CHOICES = ("claude", "codex", "none")


def _read(paths):
    try:
        with open(paths.settings_file, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def coach_choice(paths):
    """ "claude", "codex", "none", or None when nothing was chosen yet."""
    value = _read(paths).get("coach")
    return value if value in COACH_CHOICES else None


def set_coach_choice(paths, value):
    if value not in COACH_CHOICES:
        raise ValueError("coach must be one of %s." % ", ".join(COACH_CHOICES))
    data = _read(paths)
    data["coach"] = value
    folder = os.path.dirname(paths.settings_file)
    os.makedirs(folder, exist_ok=True)
    tmp = paths.settings_file + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
        fh.write("\n")
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, paths.settings_file)
