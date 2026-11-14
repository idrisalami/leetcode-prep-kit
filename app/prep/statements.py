"""Problem statements: fetched once into app/data/statements/<slug>.json, never executed.

LeetCode's public GraphQL endpoint serves most of them (HTML); the five premium problems come
from NeetCode's free pages (Markdown). Requests carry only the headers listed in the spec.
"""
from __future__ import annotations

import json
import os
import re
import time
import urllib.request
from datetime import datetime

LEETCODE_URL = "https://leetcode.com/graphql"
LEETCODE_QUERY = "query q($s:String!){question(titleSlug:$s){content}}"
LEETCODE_HEADERS = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0",
                    "Referer": "https://leetcode.com/problemset/"}
NEETCODE_URL = "https://neetcode.io/problems/%s/question"
NEETCODE_HEADERS = {"User-Agent": "Mozilla/5.0"}
PAUSE_S = 0.7
TIMEOUT_S = 20
MAX_RESPONSE = 5 * 1024 * 1024  # a statement page is far smaller; refuse anything bigger

NC_SLUGS = {
    "encode-and-decode-strings": "string-encode-and-decode",
    "walls-and-gates": "islands-and-treasure",
    "graph-valid-tree": "valid-tree",
    "number-of-connected-components-in-an-undirected-graph": "count-connected-components",
    "alien-dictionary": "foreign-dictionary",
}

FORMATS = ("html", "markdown")
SCRIPT_RE = re.compile(r"<script\b([^>]*)>(.*?)</script>", re.S | re.I)
NG_STATE_RE = re.compile(r"""\bid\s*=\s*["']ng-state["']""", re.I)


def parse_leetcode(data):
    try:
        obj = json.loads(data.decode("utf-8") if isinstance(data, bytes) else data)
        content = obj["data"]["question"]["content"]
    except (ValueError, KeyError, TypeError, AttributeError, UnicodeDecodeError):
        return None
    return content if isinstance(content, str) and content.strip() else None


DETAILS_RE = re.compile(r"<details\b[^>]*>(?:(?!<details\b).)*?</details\s*>", re.I | re.S)


def drop_details(text):
    """Remove every <details> element with its content (Topics, hints, recommended complexity),
    innermost first so nested ones go too. Blank lines left behind collapse to one."""
    out = text
    while True:
        new = DETAILS_RE.sub("", out)
        if new == out:
            break
        out = new
    if out != text:
        out = re.sub(r"\n{3,}", "\n\n", out).strip()
    return out


def parse_neetcode(html, nc_slug):
    for attrs, body in SCRIPT_RE.findall(html):
        if not NG_STATE_RE.search(attrs):
            continue
        try:
            state = json.loads(body)
            desc = state["problem-" + nc_slug]["description"]
        except (ValueError, KeyError, TypeError):
            return None
        if not isinstance(desc, str):
            return None
        desc = drop_details(desc)
        return desc if desc.strip() else None
    return None


def _urlopen(req, timeout):
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = resp.read(MAX_RESPONSE + 1)
    if len(data) > MAX_RESPONSE:
        raise ValueError("the response is larger than %d MB" % (MAX_RESPONSE // (1024 * 1024)))
    return data


def _leetcode_request(slug):
    body = json.dumps({"query": LEETCODE_QUERY, "variables": {"s": slug}}).encode("utf-8")
    return urllib.request.Request(LEETCODE_URL, data=body, headers=dict(LEETCODE_HEADERS),
                                  method="POST")


def _neetcode_request(nc_slug):
    return urllib.request.Request(NEETCODE_URL % nc_slug, headers=dict(NEETCODE_HEADERS),
                                  method="GET")


def source_of(problem):
    """The five premium problems have NeetCode pages; everything else comes from LeetCode."""
    return "neetcode" if problem["slug"] in NC_SLUGS else "leetcode"


def valid(data):
    return (isinstance(data, dict) and data.get("format") in FORMATS
            and isinstance(data.get("body"), str) and bool(data["body"].strip()))


def have(paths, slug):
    try:
        with open(os.path.join(paths.statements_dir, slug + ".json"), encoding="utf-8") as fh:
            return valid(json.load(fh))
    except (OSError, ValueError):
        return False


def _save(paths, slug, fmt, body, source, now):
    os.makedirs(paths.statements_dir, exist_ok=True)
    path = os.path.join(paths.statements_dir, slug + ".json")
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump({"slug": slug, "format": fmt, "body": body, "source": source,
                   "fetched_at": now().isoformat(timespec="seconds")}, fh, ensure_ascii=False)
    os.replace(tmp, path)


def _fetch_one(problem, opener):
    """(format, body, source) or raises; a page without a statement raises LookupError."""
    slug = problem["slug"]
    if source_of(problem) == "neetcode":
        nc = NC_SLUGS[slug]
        raw = opener(_neetcode_request(nc), TIMEOUT_S)
        body = parse_neetcode(raw.decode("utf-8", "replace"), nc)
        if body is None:
            raise LookupError("no statement found in the NeetCode page for %s" % nc)
        return "markdown", body, "neetcode"
    raw = opener(_leetcode_request(slug), TIMEOUT_S)
    body = parse_leetcode(raw)
    if body is None:
        raise LookupError("LeetCode returned no statement for %s" % slug)
    return "html", body, "leetcode"


def fetch_all(paths, catalog, only_missing=True, progress=None, opener=None, sleep=time.sleep,
              only=None, now=datetime.now):
    """Fetch statements; never raises for network trouble. Returns {"have", "total", "failed"}."""
    opener = opener or _urlopen
    report = progress or (lambda slug, status, detail: None)
    problems = catalog.problems()
    known = {p["slug"] for p in problems}
    if only is not None:
        wanted = set(only)
        problems = [p for p in problems if p["slug"] in wanted]
    failed = []
    count = 0
    requested = False
    for problem in problems:
        slug = problem["slug"]
        if only_missing and have(paths, slug):
            count += 1
            report(slug, "have", "")
            continue
        if requested:
            sleep(PAUSE_S)
        requested = True
        try:
            fmt, body, source = _fetch_one(problem, opener)
            _save(paths, slug, fmt, body, source, now)
        except Exception as exc:  # network, HTTP, parsing, disk: report and go on
            failed.append(slug)
            report(slug, "failed", "%s: %s" % (type(exc).__name__, exc))
            continue
        count += 1
        report(slug, "ok", source)
    for slug in only or []:
        if slug not in known and slug not in failed:
            failed.append(slug)
            report(slug, "failed", "not in the problem list")
    return {"have": count, "total": len(problems), "failed": failed}
