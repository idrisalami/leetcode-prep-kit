"""Read-only view of app/data: problems.json, tests/<slug>.json, statements/<slug>.json."""
from __future__ import annotations

import json
import os

from app.prep import harness

MODULE_IDS = ["%02d" % i for i in range(1, 11)]


class Catalog:
    def __init__(self, paths):
        self.paths = paths
        self._problems = None
        self._by_slug = None
        self._specs = {}

    def _load(self):
        if self._problems is None:
            with open(os.path.join(self.paths.data, "problems.json"), encoding="utf-8") as fh:
                self._problems = json.load(fh)
            self._by_slug = {p["slug"]: p for p in self._problems}

    def problems(self):
        self._load()
        return list(self._problems)

    def get(self, slug):
        self._load()
        return self._by_slug[slug]

    def spec(self, slug):
        self.get(slug)  # unknown slugs raise KeyError, never touch the file system
        if slug not in self._specs:
            with open(os.path.join(self.paths.tests_dir, slug + ".json"), encoding="utf-8") as fh:
                self._specs[slug] = json.load(fh)
        return self._specs[slug]

    def examples(self, slug):
        spec = self.spec(slug)
        out = []
        for case in spec.get("cases", []):
            if case.get("example"):
                out.append({"name": case.get("name", ""),
                            "input": harness.display_input(spec, case),
                            "expected": harness.display_value(case.get("expected"))})
        return out

    def statement(self, slug):
        self.get(slug)
        path = os.path.join(self.paths.statements_dir, slug + ".json")
        try:
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, ValueError):
            return None
        if not isinstance(data, dict) or not isinstance(data.get("body"), str) or not data["body"]:
            return None
        return data

    def module_ids(self):
        return list(MODULE_IDS)

    def by_module(self, module_id):
        self._load()
        return [p for p in self._problems if p["module"] == module_id]

    def statements_have(self):
        return sum(1 for p in self.problems() if self.statement(p["slug"]) is not None)
