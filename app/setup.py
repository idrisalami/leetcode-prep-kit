"""Download the problem statements into app/data/statements/ (git-ignored, for personal study).

    python3 app/setup.py                 # every problem still missing
    python3 app/setup.py --only a,b,c    # just these slugs
    python3 app/setup.py --all           # refetch everything
"""
from __future__ import annotations

import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.prep import catalog as catalog_mod, paths as paths_mod, statements  # noqa: E402


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Download problem statements for the prep app.")
    parser.add_argument("--only", default="", help="comma-separated slugs to fetch")
    parser.add_argument("--all", action="store_true", help="refetch statements already on disk")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(sys.argv[1:] if argv is None else argv)
    paths = paths_mod.default()
    catalog = catalog_mod.Catalog(paths)
    only = [s.strip() for s in args.only.split(",") if s.strip()] or None
    if only:
        known = {p["slug"] for p in catalog.problems()}
        unknown = [s for s in only if s not in known]
        if unknown:
            print("Not in the catalogue: %s" % ", ".join(unknown), file=sys.stderr)
            return 2

    def progress(slug, status, detail):
        if status == "ok":
            print("%-40s ok (%s)" % (slug, detail))
        elif status == "have":
            print("%-40s already here" % slug)
        else:
            print("%-40s failed: %s" % (slug, detail))
        sys.stdout.flush()

    out = statements.fetch_all(paths, catalog, only_missing=not args.all, progress=progress,
                               only=only)
    print("%d of %d statements on disk." % (out["have"], out["total"]))
    if out["failed"]:
        failed = [f["slug"] if isinstance(f, dict) else str(f) for f in out["failed"]]
        print("These failed: %s" % ", ".join(failed))
        print("Try again later with: python3 app/setup.py --only %s" % ",".join(failed))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
