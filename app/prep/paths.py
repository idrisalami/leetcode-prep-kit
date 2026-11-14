"""Where everything lives, relative to one kit root (tests pass a temporary root)."""
from __future__ import annotations

import os


class Paths:
    def __init__(self, root):
        self.root = os.path.abspath(str(root))
        self.app = os.path.join(self.root, "app")
        self.data = os.path.join(self.app, "data")
        self.tests_dir = os.path.join(self.data, "tests")
        self.statements_dir = os.path.join(self.data, "statements")
        self.static = os.path.join(self.app, "static")
        self.course = os.path.join(self.root, "course")
        self.templates = os.path.join(self.course, "templates")
        self.my_prep = os.path.join(self.root, "my-prep")
        self.state_file = os.path.join(self.my_prep, "app", "state.json")
        self.solutions_dir = os.path.join(self.my_prep, "solutions")

    def __repr__(self):
        return "Paths(%r)" % self.root


def default():
    """The kit root: two levels above app/prep/."""
    here = os.path.dirname(os.path.abspath(__file__))
    return Paths(os.path.dirname(os.path.dirname(here)))
