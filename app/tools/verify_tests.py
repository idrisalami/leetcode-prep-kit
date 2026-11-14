"""Maintainer tool: run a folder of solutions against the committed test specs.

    python3 app/tools/verify_tests.py --solutions <dir> [--only a,b] [--module 05]
                                      [--allow-missing] [--mutants <dir>]

<dir>/<slug>.py is the solution for <slug>. With --mutants, every <slug>.<anything>.py in that
folder is a deliberately broken solution, and any mutant that passes every case is reported.
Exit status is 1 when a case fails, a solution file is missing (unless --allow-missing), or a
mutant survives.
"""
from __future__ import annotations

import argparse
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.prep import catalog, paths, runner  # noqa: E402


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _describe_failure(row):
    line = "    %-8s %s" % (row["status"], row["name"])
    if row.get("error"):
        err = row["error"]
        line += "  %s: %s" % (err.get("type"), err.get("message"))
    elif row["status"] == "fail":
        line += "  expected %s, got %s" % (row["expected"], row["got"])
        if row.get("message"):
            line += " (%s)" % row["message"]
    return line


def _select(cat, only, module):
    problems = cat.problems()
    if module:
        problems = [p for p in problems if p["module"] == module.zfill(2)]
    if only:
        wanted = [s.strip() for s in only.split(",") if s.strip()]
        unknown = [s for s in wanted if s not in {p["slug"] for p in cat.problems()}]
        if unknown:
            raise SystemExit("unknown slug: %s" % ", ".join(unknown))
        problems = [p for p in problems if p["slug"] in wanted]
    return problems


def verify(solutions, problems, cat, allow_missing, out):
    bad = 0
    missing = 0
    for p in problems:
        slug = p["slug"]
        path = os.path.join(solutions, slug + ".py")
        if not os.path.isfile(path):
            missing += 1
            out.write("missing   %s\n" % slug)
            continue
        started = time.monotonic()
        res = runner.run(cat.spec(slug), _read(path))
        ms = int((time.monotonic() - started) * 1000)
        if res["fatal"]:
            bad += 1
            f = res["fatal"]
            out.write("FATAL     %s  %s: %s (line %s)\n" % (slug, f["type"], f["message"], f["line"]))
            continue
        ok = res["passed"] == res["total"]
        out.write("%s %d/%d  %s  %dms\n" % ("ok  " if ok else "FAIL", res["passed"], res["total"], slug, ms))
        if not ok:
            bad += 1
            for row in res["results"]:
                if row["status"] != "pass":
                    out.write(_describe_failure(row) + "\n")
    out.write("\n%d checked, %d passed, %d failed, %d missing\n"
              % (len(problems), len(problems) - bad - missing, bad, missing))
    return bad == 0 and (missing == 0 or allow_missing)


def mutants(folder, problems, cat, out):
    slugs = {p["slug"] for p in problems}
    survivors = 0
    checked = 0
    for name in sorted(os.listdir(folder)):
        if not name.endswith(".py"):
            continue
        slug = name.split(".", 1)[0]
        if slug not in slugs or name == slug + ".py":
            continue
        checked += 1
        res = runner.run(cat.spec(slug), _read(os.path.join(folder, name)))
        if not res["fatal"] and res["total"] and res["passed"] == res["total"]:
            survivors += 1
            out.write("SURVIVED  %s  passes all %d cases\n" % (name, res["total"]))
        else:
            out.write("killed    %s  %d/%d\n" % (name, res["passed"], res["total"]))
    out.write("\n%d mutants, %d survived\n" % (checked, survivors))
    return survivors == 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run solutions against the app's test specs.")
    parser.add_argument("--solutions", required=True, help="folder holding <slug>.py files")
    parser.add_argument("--only", help="comma-separated slugs")
    parser.add_argument("--module", help="module id, e.g. 05")
    parser.add_argument("--allow-missing", action="store_true", help="do not fail on missing files")
    parser.add_argument("--mutants", help="folder of <slug>.<name>.py broken solutions")
    args = parser.parse_args(argv)
    cat = catalog.Catalog(paths.default())
    problems = _select(cat, args.only, args.module)
    ok = verify(args.solutions, problems, cat, args.allow_missing, sys.stdout)
    if args.mutants:
        sys.stdout.write("\n")
        ok = mutants(args.mutants, problems, cat, sys.stdout) and ok
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
