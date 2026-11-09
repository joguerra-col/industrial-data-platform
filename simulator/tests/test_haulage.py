import json
import random
import tempfile
import time
import unittest
from dataclasses import replace
from datetime import date
from pathlib import Path

from quarry_sim.calendar import build_calendar
from quarry_sim.config import load_config
from quarry_sim.haulage import simulate_haulage
from quarry_sim.writers import write_fms_events

CONFIG = load_config(Path(__file__).parents[1] / "config" / "plant.toml")
MONDAY = date(2026, 11, 2)
CYCLE = ["zone_enter", "payload_step", "zone_exit", "zone_enter", "body_up", "body_down",
         "zone_exit"]


def simulate(config=CONFIG, days=2, seed=42):
    shifts = build_calendar(config, MONDAY, days, random.Random(f"{seed}:calendar"))
    return shifts, simulate_haulage(config, shifts, MONDAY, random.Random(f"{seed}:haulage"))


def by_truck(events):
    out = {}
    for e in events:
        out.setdefault(e["equipment_id"], []).append(e)
    return out


class HaulageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.shifts, cls.result = simulate()
        cls.units = {e.equipment_id: e for e in CONFIG.equipment}

    def test_same_seed_gives_identical_files(self):
        def files(seed):
            with tempfile.TemporaryDirectory() as tmp:
                paths = write_fms_events(simulate(seed=seed)[1].events, Path(tmp))
                return {p.name: p.read_bytes() for p in paths}
        self.assertEqual(files(42), files(42))
        self.assertNotEqual(files(42), files(7))

    def test_every_trip_has_a_complete_sequence(self):
        for truck, events in by_truck(self.result.events).items():
            types = [e["event_type"] for e in events if not e["event_type"].startswith("operator")]
            collapsed = [t for i, t in enumerate(types) if t != "payload_step" or types[i - 1] != t]
            self.assertEqual(len(collapsed) % len(CYCLE), 0, truck)
            for i in range(0, len(collapsed), len(CYCLE)):
                self.assertEqual(collapsed[i:i + len(CYCLE)], CYCLE, f"{truck} cycle {i // 7}")

    def test_payload_within_10_percent_of_nominal(self):
        for trip in self.result.trips:
            nominal = self.units[trip.truck_id].nominal_payload_t
            self.assertLessEqual(abs(trip.payload_t / nominal - 1), 0.10, trip)

    def test_no_activity_outside_shifts_or_without_operator(self):
        windows = [(s.work_start_utc, s.work_end_utc) for s in self.shifts]
        for truck, events in by_truck(self.result.events).items():
            logged_in = False
            for e in events:
                self.assertTrue(any(a <= e["event_ts"] <= b for a, b in windows), e)
                if e["event_type"] == "operator_login":
                    self.assertFalse(logged_in, e)
                    logged_in = True
                elif e["event_type"] == "operator_logout":
                    self.assertTrue(logged_in, e)
                    logged_in = False
                else:
                    self.assertTrue(logged_in, f"cycle event without operator: {e}")
            self.assertFalse(logged_in, f"{truck} never logged out")

    def test_waste_goes_to_dump_and_ore_to_hopper(self):
        for trip in self.result.trips:
            expected = CONFIG.plant.waste_dump_id if trip.material_type == "WASTE" \
                else CONFIG.plant.hopper_id
            self.assertEqual(trip.destination_id, expected, trip)

    def test_counters_monotonic_and_ids_unique(self):
        for truck, events in by_truck(self.result.events).items():
            for prev, cur in zip(events, events[1:]):
                self.assertGreaterEqual(cur["odometer_km"], prev["odometer_km"], truck)
                self.assertGreaterEqual(cur["fuel_used_cum_l"], prev["fuel_used_cum_l"], truck)
        ids = [e["event_id"] for e in self.result.events]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(e["received_ts"] > e["event_ts"] for e in self.result.events))

    def test_bench_stock_never_exceeded(self):
        tiny = replace(CONFIG, benches=tuple(
            replace(b, initial_broken_stock_t=500) if b.bench_id == "1-11-BNK-01" else b
            for b in CONFIG.benches))
        hauled = sum(t.payload_t for t in simulate(tiny)[1].trips if t.bench_id == "1-11-BNK-01")
        self.assertLess(hauled, 500 + 60)  # at most one truckload past the remaining stock

    def test_one_week_runs_fast(self):
        start = time.perf_counter()
        simulate(days=7)
        self.assertLess(time.perf_counter() - start, 30)

    def test_jsonl_rows_are_valid_json_in_utc(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write_fms_events(self.result.events, Path(tmp))[0]
            row = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
        self.assertTrue(row["event_ts"].endswith("Z"))
        self.assertEqual(path.name, row["event_ts"][:10] + ".jsonl")


if __name__ == "__main__":
    unittest.main()
