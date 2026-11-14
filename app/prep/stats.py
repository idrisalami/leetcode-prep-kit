"""Numbers derived from the state and the catalog: kpis, streaks, warm-up, rep levels."""
from __future__ import annotations

from datetime import date, datetime, timedelta

STREAK_SECONDS = 300
WEEK_DAYS = 7
REDO_AFTER_DAYS = 7
LEVEL_3_SECONDS = 25 * 60

MODULE_ROW = {"01": "A1", "02": "A2", "04": "A6", "05": "A7", "06": "A8", "07": "A9",
              "08": "A10", "09": "A11", "10": "A12"}
MODULE_03_ROW = {"Two Pointers": "A4", "Sliding Window": "A5"}


def minutes_text(seconds):
    """Minutes as the app shows them everywhere: `under 1 min` below 60 s, else `<n> min`."""
    seconds = seconds if isinstance(seconds, (int, float)) and not isinstance(seconds, bool) else 0
    if seconds < 60:
        return "under 1 min"
    return "%d min" % (seconds // 60)


def _pct(part, whole):
    return int(100 * part / whole + 0.5) if whole else 0


def _date(text):
    try:
        return date.fromisoformat(str(text)[:10])
    except ValueError:
        return None


def _num(record, key):
    value = record.get(key)
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) else 0


def _only_dicts(days):
    return {k: v for k, v in days.items() if isinstance(v, dict)} if isinstance(days, dict) else {}


def _problems(state):
    return _only_dicts(state.get("problems"))


def _days(state):
    return _only_dicts(state.get("days"))


def _is_solved(state, slug):
    return _problems(state).get(slug, {}).get("status") == "solved"


def _active_dates(days):
    out = set()
    for key, d in _only_dicts(days).items():
        when = _date(key)
        if when and (_num(d, "runs") or _num(d, "submits") or _num(d, "seconds") >= STREAK_SECONDS):
            out.add(when)
    return out


def streak(days, today):
    """(current, best): runs of consecutive active days; current must end today or yesterday."""
    active = _active_dates(days)
    best = run = 0
    previous = None
    for when in sorted(active):
        run = run + 1 if previous is not None and when - previous == timedelta(days=1) else 1
        best = max(best, run)
        previous = when
    end = today if today in active else today - timedelta(days=1)
    current = 0
    while end in active:
        current += 1
        end -= timedelta(days=1)
    return current, best


def kpis(state, catalog, today):
    slugs = [p["slug"] for p in catalog.problems()]
    problems = _problems(state)
    days = _days(state)
    week = {today - timedelta(days=i) for i in range(WEEK_DAYS)}
    solved_week = set()
    seconds_week = 0
    for key, d in days.items():
        if _date(key) in week:
            solved_week.update(x for x in (d.get("solved") or []) if isinstance(x, str))
            seconds_week += _num(d, "seconds")
    submitted = [s for s in slugs if problems.get(s, {}).get("submits")]
    first_try = [s for s in submitted if problems[s].get("first_try") is True]
    current, best = streak(days, today)
    return {"solved": sum(1 for s in slugs if _is_solved(state, s)), "total": len(slugs),
            "solved_week": len(solved_week & set(slugs)),
            "seconds": sum(_num(d, "seconds") for d in days.values()),
            "seconds_week": seconds_week, "streak": current, "best_streak": best,
            "first_try_pct": _pct(len(first_try), len(submitted)),
            "first_try_n": len(first_try), "submitted_n": len(submitted)}


def module_progress(state, catalog):
    out = []
    for module_id in catalog.module_ids():
        slugs = [p["slug"] for p in catalog.by_module(module_id)]
        solved = sum(1 for s in slugs if _is_solved(state, s))
        out.append({"id": module_id, "solved": solved, "total": len(slugs),
                    "pct": _pct(solved, len(slugs))})
    return out


def current_module(state, catalog):
    for row in module_progress(state, catalog):
        if row["solved"] < row["total"]:
            return row["id"]
    return "10"


def day_number(state, today):
    firsts = [d for d in (_date(k) for k in _days(state)) if d]
    firsts += [d for d in (_date(e.get("first_opened")) for e in _problems(state).values()
                           if e.get("first_opened")) if d]
    if not firsts:
        return 1
    return max(1, (today - min(firsts)).days + 1)


# ---- warm-up ------------------------------------------------------------

def _warmup_candidates(state, catalog, today):
    """Easy problems in the current or earlier modules, in the order of the spec's rule."""
    current = current_module(state, catalog)
    easy = [p for p in catalog.problems() if p["difficulty"] == "Easy" and p["module"] <= current]
    redo = []
    for p in easy:
        solved_on = _date(_problems(state).get(p["slug"], {}).get("last_solved_at"))
        if solved_on and (today - solved_on).days > REDO_AFTER_DAYS:
            redo.append((solved_on, p["slug"]))
    ordered = [slug for _, slug in sorted(redo)]
    ordered += [p["slug"] for p in easy if not _is_solved(state, p["slug"])]
    ordered += [p["slug"] for p in easy]
    seen = set()
    return [s for s in ordered if not (s in seen or seen.add(s))]


def warmup(store, catalog, today, another=False):
    """One warm-up per calendar day, persisted; another=True moves on to the next candidate."""
    state = store.snapshot()
    stored = state.get("warmup")
    stored = stored if isinstance(stored, dict) else {}
    day = today.isoformat()
    known = {p["slug"] for p in catalog.problems()}
    current = stored.get("slug") if stored.get("date") == day and stored.get("slug") in known else None
    if current and not another:
        pick, skipped = current, list(stored.get("skipped", []))
    else:
        skipped = list(stored.get("skipped", [])) if stored.get("date") == day else []
        if current:
            skipped.append(current)
        candidates = _warmup_candidates(state, catalog, today)
        fresh = [s for s in candidates if s not in skipped]
        if not fresh:
            skipped = [current] if current else []
            fresh = [s for s in candidates if s != current] or candidates
        pick = fresh[0] if fresh else None
        store.set_warmup(day, pick, skipped)
    done = pick is not None and pick in (_days(state).get(day, {}).get("solved") or [])
    return {"slug": pick, "done": done}


# ---- matrix -------------------------------------------------------------

def rep_level(problem, entry, submit):
    """The level of one attempt at one problem, judged on its submits up to `submit`."""
    attempt = submit.get("attempt", 1)
    subs = [s for s in entry.get("submits", []) if s.get("attempt", 1) == attempt]
    ids = [s.get("id") for s in subs]
    if submit.get("id") in ids:
        subs = subs[:ids.index(submit.get("id")) + 1]
    else:
        subs.append(submit)
    solved = next((i for i, s in enumerate(subs) if s.get("ok")), None)
    if solved is not None:
        won = subs[solved]
        no_hints = won.get("hints_used", 0) == 0
        first_try = solved == 0
        if (first_try and no_hints and problem.get("difficulty") != "Easy"
                and won.get("seconds", 0) <= LEVEL_3_SECONDS):
            return 3
        if no_hints or (first_try and problem.get("difficulty") == "Easy"):
            return 2
        return 1
    total = submit.get("total", 0)
    return 1 if total > 0 and 2 * submit.get("passed", 0) >= total else 0


def matrix_row(problem):
    if problem.get("module") == "03":
        return MODULE_03_ROW.get(problem.get("category"))
    return MODULE_ROW.get(problem.get("module"))


def practise_slug(row_id, state, catalog):
    """The first unsolved problem for a matrix row, else the one solved longest ago."""
    mine = [p["slug"] for p in catalog.problems() if matrix_row(p) == row_id]
    for slug in mine:
        if not _is_solved(state, slug):
            return slug
    if not mine:
        return None
    return min(mine, key=lambda s: _problems(state).get(s, {}).get("last_solved_at") or "")
