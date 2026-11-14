"""Stats: kpis, streaks, module progress, warm-up, rep levels, matrix rows."""
from __future__ import annotations

import unittest
from datetime import date, datetime, timedelta

from app.prep import catalog, stats, store
from app.tests.kit import Clock, make_kit, prob

TODAY = date(2026, 11, 12)


def day(offset, **kw):
    d = {"seconds": 0, "runs": 0, "submits": 0, "solved": []}
    d.update(kw)
    return (TODAY - timedelta(days=offset)).isoformat(), d


def days(*pairs):
    return dict(pairs)


def solved_entry(first_try=True, at="2026-11-01T09:00:00"):
    return {"status": "solved", "submits": [{"id": "x"}], "first_try": first_try,
            "solved_at": at, "last_solved_at": at}


class MinutesTextTests(unittest.TestCase):
    def test_under_a_minute_and_whole_minutes(self):
        for seconds, text in ((0, "under 1 min"), (59, "under 1 min"), (60, "1 min"),
                              (179, "2 min"), (3600, "60 min"), (None, "under 1 min")):
            self.assertEqual(stats.minutes_text(seconds), text, seconds)


class StreakTests(unittest.TestCase):
    def test_nothing_recorded(self):
        self.assertEqual(stats.streak({}, TODAY), (0, 0))

    def test_today_active(self):
        d = days(day(0, runs=1), day(1, submits=1), day(2, seconds=300))
        self.assertEqual(stats.streak(d, TODAY), (3, 3))

    def test_yesterday_active_but_not_today_still_counts(self):
        d = days(day(1, runs=1), day(2, runs=2))
        self.assertEqual(stats.streak(d, TODAY), (2, 2))

    def test_a_gap_resets_and_best_is_kept(self):
        d = days(day(0, runs=1), day(2, runs=1), day(3, runs=1), day(4, runs=1), day(5, runs=1))
        self.assertEqual(stats.streak(d, TODAY), (1, 4))

    def test_two_days_without_activity_means_zero_current(self):
        d = days(day(2, runs=1), day(3, runs=1))
        self.assertEqual(stats.streak(d, TODAY), (0, 2))

    def test_under_five_minutes_of_time_alone_is_not_activity(self):
        d = days(day(0, seconds=299), day(1, seconds=300))
        self.assertEqual(stats.streak(d, TODAY), (1, 1))  # yesterday only; today's 299 s do not extend it
        self.assertEqual(stats.streak(days(day(0, seconds=299)), TODAY), (0, 0))

    def test_a_null_or_malformed_day_record_is_not_activity_and_does_not_raise(self):
        d = {TODAY.isoformat(): {"seconds": None, "runs": None, "submits": None},
             (TODAY - timedelta(days=1)).isoformat(): {},
             (TODAY - timedelta(days=2)).isoformat(): None,
             (TODAY - timedelta(days=3)).isoformat(): {"runs": 1}}
        self.assertEqual(stats.streak(d, TODAY), (0, 1))


class CatalogCase(unittest.TestCase):
    PROBLEMS = [prob("a1", "01"), prob("a2", "01"), prob("a3", "01", "Medium"),
                prob("b1", "02"), prob("b2", "02", "Medium"),
                prob("c1", "03", category="Two Pointers"), prob("c2", "03", "Medium", "Sliding Window")]

    def setUp(self):
        self.paths = make_kit(self, self.PROBLEMS)
        self.cat = catalog.Catalog(self.paths)
        self.clock = Clock(datetime(2026, 11, 12, 9, 0, 0))
        self.store = store.Store(self.paths, now=self.clock)


class KpiTests(CatalogCase):
    def test_empty_state(self):
        k = stats.kpis(self.store.snapshot(), self.cat, TODAY)
        self.assertEqual(k, {"solved": 0, "total": 7, "solved_week": 0, "seconds": 0,
                             "seconds_week": 0, "streak": 0, "best_streak": 0,
                             "first_try_pct": 0, "first_try_n": 0, "submitted_n": 0})

    def test_sums_week_and_first_try(self):
        state = {"problems": {"a1": solved_entry(True), "a2": solved_entry(False),
                              "b1": {"status": "attempted", "submits": [{"id": "x"}], "first_try": False},
                              "b2": {"status": "attempted", "submits": []},
                              "gone": solved_entry(True)},
                 "days": days(day(0, seconds=100, solved=["a1"]), day(6, seconds=50, solved=["a1", "a2"]),
                              day(7, seconds=1000, solved=["b1"]), day(30, seconds=10))}
        k = stats.kpis(state, self.cat, TODAY)
        self.assertEqual((k["solved"], k["total"]), (2, 7))
        self.assertEqual(k["solved_week"], 2)  # a1 counted once, day 7 is outside the week
        self.assertEqual((k["seconds"], k["seconds_week"]), (1160, 150))
        self.assertEqual((k["first_try_n"], k["submitted_n"], k["first_try_pct"]), (1, 3, 33))
        self.assertEqual((k["streak"], k["best_streak"]), (0, 1))  # only day 7 reaches 5 minutes

    def test_first_try_rounds_half_up(self):
        state = {"problems": {"a1": solved_entry(True), "a2": solved_entry(True),
                              "a3": {"status": "attempted", "submits": [{"id": "x"}], "first_try": False}},
                 "days": {}}
        self.assertEqual(stats.kpis(state, self.cat, TODAY)["first_try_pct"], 67)


class MalformedStateTests(CatalogCase):
    def test_kpis_with_null_seconds(self):
        state = {"days": {TODAY.isoformat(): {"seconds": None, "runs": 1, "submits": 0,
                                               "solved": None}, "junk": 4},
                 "problems": {"a1": None, "a2": {"submits": [{}], "first_try": True}}}
        out = stats.kpis(state, self.cat, TODAY)
        self.assertEqual((out["seconds"], out["seconds_week"], out["streak"]), (0, 0, 1))
        self.assertEqual((out["solved"], out["submitted_n"]), (0, 1))


class ProgressTests(CatalogCase):
    def test_module_progress_and_percentages(self):
        state = {"problems": {"a1": solved_entry(), "a2": solved_entry(), "b1": solved_entry()}}
        rows = stats.module_progress(state, self.cat)
        self.assertEqual([r["id"] for r in rows], ["%02d" % i for i in range(1, 11)])
        self.assertEqual(rows[0], {"id": "01", "solved": 2, "total": 3, "pct": 67})
        self.assertEqual(rows[1], {"id": "02", "solved": 1, "total": 2, "pct": 50})
        self.assertEqual(rows[2], {"id": "03", "solved": 0, "total": 2, "pct": 0})
        self.assertEqual(rows[9], {"id": "10", "solved": 0, "total": 0, "pct": 0})

    def test_current_module(self):
        self.assertEqual(stats.current_module({"problems": {}}, self.cat), "01")
        one = {"a1": solved_entry(), "a2": solved_entry(), "a3": solved_entry()}
        self.assertEqual(stats.current_module({"problems": one}, self.cat), "02")
        everything = {p["slug"]: solved_entry() for p in self.PROBLEMS}
        self.assertEqual(stats.current_module({"problems": everything}, self.cat), "10")

    def test_day_number(self):
        self.assertEqual(stats.day_number({"days": {}, "problems": {}}, TODAY), 1)
        state = {"days": days(day(2, runs=1), day(0, runs=1)), "problems": {}}
        self.assertEqual(stats.day_number(state, TODAY), 3)
        self.assertEqual(stats.day_number({"days": days(day(0, runs=1)), "problems": {}}, TODAY), 1)


class WarmupTests(CatalogCase):
    def test_before_any_progress_it_is_the_first_easy_of_module_01(self):
        self.assertEqual(stats.warmup(self.store, self.cat, TODAY), {"slug": "a1", "done": False})
        self.assertEqual(self.store.warmup(), {"date": "2026-11-12", "slug": "a1", "skipped": []})

    def test_the_pick_is_stable_within_a_day(self):
        first = stats.warmup(self.store, self.cat, TODAY)
        self.store.record_submit("a1", 5, 5)
        self.assertEqual(stats.warmup(self.store, self.cat, TODAY), {"slug": first["slug"], "done": True})
        again = stats.warmup(self.store, self.cat, TODAY)
        self.assertEqual(again["slug"], "a1")

    def test_a_new_day_picks_again(self):
        stats.warmup(self.store, self.cat, TODAY)
        self.store.record_submit("a1", 5, 5)
        tomorrow = stats.warmup(self.store, self.cat, TODAY + timedelta(days=1))
        self.assertEqual(tomorrow, {"slug": "a2", "done": False})

    def test_an_easy_solved_over_a_week_ago_comes_first(self):
        state_clock = self.clock
        state_clock.t = datetime(2026, 11, 1, 9, 0, 0)
        self.store.record_submit("a1", 5, 5)
        state_clock.t = datetime(2026, 11, 3, 9, 0, 0)
        self.store.record_submit("a2", 5, 5)
        self.assertEqual(stats.warmup(self.store, self.cat, TODAY)["slug"], "a1")

    def test_a_recent_solve_is_not_a_redo_candidate(self):
        self.clock.t = datetime(2026, 11, 8, 9, 0, 0)
        self.store.record_submit("a1", 5, 5)
        self.assertEqual(stats.warmup(self.store, self.cat, TODAY)["slug"], "a2")

    def test_exactly_seven_days_is_not_more_than_seven(self):
        self.clock.t = datetime(2026, 11, 5, 9, 0, 0)
        self.store.record_submit("a1", 5, 5)
        self.assertEqual(stats.warmup(self.store, self.cat, TODAY)["slug"], "a2")

    def test_unsolved_easy_only_from_current_or_earlier_modules(self):
        self.clock.t = datetime(2026, 11, 11, 9, 0, 0)
        for slug in ("a1", "a2", "a3"):
            self.store.record_submit(slug, 5, 5)
        self.assertEqual(stats.warmup(self.store, self.cat, TODAY)["slug"], "b1")

    def test_any_easy_when_everything_eligible_is_solved_recently(self):
        self.clock.t = datetime(2026, 11, 11, 9, 0, 0)
        for slug in ("a1", "a2", "a3", "b1", "b2", "c1", "c2"):
            self.store.record_submit(slug, 5, 5)
        pick = stats.warmup(self.store, self.cat, TODAY)["slug"]
        self.assertIn(pick, ("a1", "a2", "b1", "c1"))

    def test_another_moves_on_and_never_returns_a_skipped_slug_until_all_are_skipped(self):
        # the eligible Easy pool is a1, a2 (a3 is Medium)
        self.assertEqual(stats.warmup(self.store, self.cat, TODAY)["slug"], "a1")
        self.assertEqual(stats.warmup(self.store, self.cat, TODAY, another=True)["slug"], "a2")
        self.assertEqual(self.store.warmup()["skipped"], ["a1"])
        # both skipped now: the pool starts over, but not on the slug just shown
        self.assertEqual(stats.warmup(self.store, self.cat, TODAY, another=True)["slug"], "a1")
        self.assertEqual(stats.warmup(self.store, self.cat, TODAY)["slug"], "a1")

    def test_another_with_one_candidate_returns_it_again(self):
        paths = make_kit(self, [prob("only", "01")])
        cat = catalog.Catalog(paths)
        st = store.Store(paths, now=self.clock)
        self.assertEqual(stats.warmup(st, cat, TODAY)["slug"], "only")
        self.assertEqual(stats.warmup(st, cat, TODAY, another=True)["slug"], "only")

    def test_no_easy_problems_gives_an_empty_pick(self):
        paths = make_kit(self, [prob("m", "01", "Medium")])
        out = stats.warmup(store.Store(paths, now=self.clock), catalog.Catalog(paths), TODAY)
        self.assertEqual(out, {"slug": None, "done": False})

    def test_a_stored_slug_missing_from_the_catalog_is_replaced(self):
        self.store.set_warmup("2026-11-12", "removed", [])
        self.assertEqual(stats.warmup(self.store, self.cat, TODAY)["slug"], "a1")


class RepLevelTests(unittest.TestCase):
    def sub(self, i, ok, passed=5, total=5, seconds=600, hints=0, attempt=1):
        return {"id": "s%d" % i, "ok": ok, "passed": passed, "total": total, "seconds": seconds,
                "hints_used": hints, "attempt": attempt}

    def level(self, difficulty, subs, which=-1):
        entry = {"submits": subs}
        return stats.rep_level({"difficulty": difficulty}, entry, subs[which])

    def test_three_medium_first_submit_in_25_minutes_no_hints(self):
        self.assertEqual(self.level("Medium", [self.sub(1, True, seconds=1500)]), 3)
        self.assertEqual(self.level("Hard", [self.sub(1, True, seconds=60)]), 3)

    def test_two_medium_first_submit_over_25_minutes(self):
        self.assertEqual(self.level("Medium", [self.sub(1, True, seconds=1501)]), 2)

    def test_two_solved_without_hints_after_a_failed_submit(self):
        subs = [self.sub(1, False, passed=1), self.sub(2, True, seconds=60)]
        self.assertEqual(self.level("Medium", subs), 2)

    def test_two_easy_first_try_even_with_hints_or_slow(self):
        self.assertEqual(self.level("Easy", [self.sub(1, True, seconds=5000, hints=2)]), 2)

    def test_one_solved_with_hints(self):
        self.assertEqual(self.level("Medium", [self.sub(1, True, hints=1)]), 1)
        subs = [self.sub(1, False, passed=0), self.sub(2, True, hints=1)]
        self.assertEqual(self.level("Easy", subs), 1)

    def test_one_not_solved_but_half_the_tests_pass(self):
        self.assertEqual(self.level("Medium", [self.sub(1, False, passed=5, total=10)]), 1)

    def test_zero_otherwise(self):
        self.assertEqual(self.level("Medium", [self.sub(1, False, passed=4, total=10)]), 0)
        self.assertEqual(self.level("Easy", [self.sub(1, False, passed=0, total=0)]), 0)

    def test_a_failing_submit_after_a_pass_in_the_same_attempt_keeps_the_solved_level(self):
        subs = [self.sub(1, True, seconds=60), self.sub(2, False, passed=0)]
        self.assertEqual(self.level("Medium", subs), 3)

    def test_only_the_submits_of_the_same_attempt_count(self):
        subs = [self.sub(1, False, passed=0, attempt=1), self.sub(2, True, seconds=60, attempt=2)]
        self.assertEqual(self.level("Medium", subs), 3)

    def test_a_submit_missing_from_the_entry_is_scored_as_the_latest(self):
        latest = self.sub(9, True, seconds=60)
        self.assertEqual(stats.rep_level({"difficulty": "Medium"}, {"submits": []}, latest), 3)


class MatrixRowTests(unittest.TestCase):
    def test_every_module(self):
        expected = {"01": "A1", "02": "A2", "04": "A6", "05": "A7", "06": "A8", "07": "A9",
                    "08": "A10", "09": "A11", "10": "A12"}
        for module, row in expected.items():
            self.assertEqual(stats.matrix_row({"module": module, "category": "x"}), row, module)

    def test_module_03_splits_on_category(self):
        self.assertEqual(stats.matrix_row({"module": "03", "category": "Two Pointers"}), "A4")
        self.assertEqual(stats.matrix_row({"module": "03", "category": "Sliding Window"}), "A5")
        self.assertIsNone(stats.matrix_row({"module": "03", "category": "Other"}))

    def test_unknown_module(self):
        self.assertIsNone(stats.matrix_row({"module": "00", "category": ""}))


class PractiseTests(CatalogCase):
    def test_first_unsolved_for_the_row(self):
        self.assertEqual(stats.practise_slug("A1", self.store.snapshot(), self.cat), "a1")
        self.store.record_submit("a1", 5, 5)
        self.assertEqual(stats.practise_slug("A1", self.store.snapshot(), self.cat), "a2")
        self.assertEqual(stats.practise_slug("A5", self.store.snapshot(), self.cat), "c2")

    def test_oldest_solved_when_all_are_solved(self):
        self.clock.t = datetime(2026, 11, 3, 9, 0, 0)
        self.store.record_submit("a2", 5, 5)
        self.clock.t = datetime(2026, 11, 1, 9, 0, 0)
        self.store.record_submit("a1", 5, 5)
        self.clock.t = datetime(2026, 11, 5, 9, 0, 0)
        self.store.record_submit("a3", 5, 5)
        self.assertEqual(stats.practise_slug("A1", self.store.snapshot(), self.cat), "a1")

    def test_none_for_rows_without_problems(self):
        for row in ("A3", "A13", "B1", "C4", "A12", "nonsense"):
            self.assertIsNone(stats.practise_slug(row, self.store.snapshot(), self.cat), row)


if __name__ == "__main__":
    unittest.main()
