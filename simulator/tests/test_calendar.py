import random
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from quarry_sim.calendar import LOADING_TYPES, build_calendar
from quarry_sim.config import load_config

CONFIG = load_config(Path(__file__).parents[1] / "config" / "plant.toml")
MONDAY = date(2026, 11, 2)


def week(seed: int = 42):
    return build_calendar(CONFIG, MONDAY, 7, random.Random(seed))


class CalendarTest(unittest.TestCase):
    def test_monday_to_saturday_two_shifts_no_sunday(self):
        shifts = week()
        self.assertEqual(len(shifts), 12)
        self.assertNotIn("20261108-A", {s.shift_id for s in shifts})  # Sunday

    def test_local_times_converted_to_utc(self):
        a, b = week()[:2]
        self.assertEqual(a.shift_id, "20261102-A")
        self.assertEqual(a.start_utc, datetime(2026, 11, 2, 13, 0, tzinfo=timezone.utc))  # 08:00 COT
        self.assertEqual(b.end_utc, datetime(2026, 11, 3, 5, 0, tzinfo=timezone.utc))  # 24:00 COT

    def test_handover_excluded_from_work_window(self):
        s = week()[0]
        self.assertEqual(s.work_start_utc - s.start_utc, timedelta(minutes=10))
        self.assertEqual(s.end_utc - s.work_end_utc, timedelta(minutes=10))

    def test_every_unit_gets_one_break_inside_meal_window(self):
        for s in week():
            with self.subTest(shift=s.shift_id):
                self.assertEqual(sorted(b.equipment_id for b in s.meal_breaks),
                                 sorted(e.equipment_id for e in CONFIG.equipment))
                local = [b.start_utc.astimezone(timezone(timedelta(hours=-5))) for b in s.meal_breaks]
                window = (12, 14) if s.name == "A" else (19, 21)
                for b, start in zip(s.meal_breaks, local):
                    self.assertEqual(b.end_utc - b.start_utc, timedelta(minutes=30))
                    self.assertTrue(window[0] <= start.hour < window[1])

    def test_loading_never_stops_for_meals(self):
        loading = {e.equipment_id for e in CONFIG.equipment if e.equipment_type in LOADING_TYPES}
        for s in week():
            slots = [b.start_utc for b in s.meal_breaks if b.equipment_id in loading]
            self.assertEqual(len(slots), len(set(slots)), s.shift_id)  # all in different slots

    def test_same_seed_same_calendar_different_seed_differs(self):
        self.assertEqual(week(42), week(42))
        self.assertNotEqual([s.meal_breaks for s in week(42)], [s.meal_breaks for s in week(7)])

    def test_sunday_only_gives_no_shifts(self):
        self.assertEqual(build_calendar(CONFIG, date(2026, 11, 8), 1, random.Random(1)), [])


if __name__ == "__main__":
    unittest.main()
