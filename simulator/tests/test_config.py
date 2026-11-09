import csv
import tempfile
import unittest
from dataclasses import fields
from pathlib import Path

from quarry_sim.config import Bench, ConfigError, Equipment, load_config
from quarry_sim.writers import BENCH_COLUMNS, EQUIPMENT_COLUMNS, write_reference

PLANT_TOML = Path(__file__).parents[1] / "config" / "plant.toml"
LOAD_ZONE_WITHOUT_BENCH_ID = """
[[zones]]
zone_id = "ZN-LOD-01"
zone_type = "load"
polygon_wkt = "POLYGON((0 0, 0 1, 1 1, 0 0))"
"""


def load_with(text: str):
    """Load a config whose text is the real plant.toml after an edit."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "plant.toml"
        path.write_text(text, encoding="utf-8")
        return load_config(path)


class ConfigTest(unittest.TestCase):
    def setUp(self):
        self.text = PLANT_TOML.read_text(encoding="utf-8")

    def assert_rejected(self, text: str, expected: str):
        with self.assertRaises(ConfigError) as ctx:
            load_with(text)
        self.assertTrue(any(expected in e for e in ctx.exception.errors), ctx.exception.errors)

    def test_real_config_loads(self):
        cfg = load_config(PLANT_TOML)
        self.assertEqual(sum(e.equipment_type == "haul_truck" for e in cfg.equipment), 7)
        self.assertEqual(len(cfg.benches), 5)
        self.assertIsNone(cfg.benches[3].expected_cao_pct)  # WASTE

    def test_real_config_has_every_zone_type(self):
        cfg = load_config(PLANT_TOML)
        self.assertEqual({z.zone_type for z in cfg.zones},
                         {"load", "queue", "dump_crusher", "dump_waste", "workshop", "parking"})
        self.assertEqual({z.zone_id for z in cfg.zones if z.zone_type == "load"},
                         {b.bench_id for b in cfg.benches})

    def test_bad_id_format(self):
        self.assert_rejected(self.text.replace('"1-91-TRK-03"', '"1-91-TRK-3"'), "1-91-TRK-NN")

    def test_id_does_not_match_type(self):
        self.assert_rejected(self.text.replace('"1-11-EXC-02"', '"1-91-TRK-08"', 1), "1-11-EXC-NN")

    def test_duplicate_id(self):
        self.assert_rejected(self.text.replace('"1-91-TRK-02"', '"1-91-TRK-01"'), "more than once")

    def test_hg_chemistry_out_of_range(self):
        self.assert_rejected(self.text.replace("expected_cao_pct = 52.4", "expected_cao_pct = 45.0"),
                             "outside HG range")

    def test_missing_and_unknown_keys(self):
        self.assert_rejected(self.text.replace("fuel_tank_l = 600", "fuel_tank = 600"),
                             "missing fuel_tank_l")

    def test_load_zone_must_reuse_bench_id(self):
        self.assert_rejected(self.text + LOAD_ZONE_WITHOUT_BENCH_ID, "must reuse its asset ID")

    def test_duplicate_zone_id(self):
        dup = '\n[[zones]]\nzone_id = "ZN-QUE-01"\nzone_type = "queue"\npolygon_wkt = "POLYGON((0 0))"\n'
        self.assert_rejected(self.text + dup, "zone ID ZN-QUE-01 is used more than once")

    def test_meal_window_inside_handover_rejected(self):
        self.assert_rejected(self.text.replace('meal_window_start = "12:00"',
                                               'meal_window_start = "08:05"'),
                             "outside handovers")

    def test_loading_unit_must_be_excavator_or_loader(self):
        self.assert_rejected(self.text.replace('loading_unit_id = "1-11-LDR-01"',
                                               'loading_unit_id = "1-91-TRK-01"'),
                             "must be an excavator or loader")

    def test_loading_bench_must_be_active(self):
        self.assert_rejected(self.text.replace('bench_id = "1-11-BNK-03"\ndispatch_weight',
                                               'bench_id = "1-11-BNK-05"\ndispatch_weight'),
                             "must exist and be active")

    def test_all_errors_reported_together(self):
        text = self.text.replace('"1-91-TRK-03"', '"1-91-TRK-3"').replace(
            'status = "planned"', 'status = "closed"')
        with self.assertRaises(ConfigError) as ctx:
            load_with(text)
        self.assertGreaterEqual(len(ctx.exception.errors), 2)


class ReferenceFilesTest(unittest.TestCase):
    def test_headers_match_dataclasses(self):
        self.assertEqual(set(EQUIPMENT_COLUMNS), {f.name for f in fields(Equipment)})
        self.assertEqual(set(BENCH_COLUMNS), {f.name for f in fields(Bench)})

    def test_waste_chemistry_written_as_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_reference(load_config(PLANT_TOML), Path(tmp))
            with (Path(tmp) / "reference" / "benches.csv").open(encoding="utf-8") as f:
                rows = {r["bench_id"]: r for r in csv.DictReader(f)}
        self.assertEqual(rows["1-11-BNK-04"]["expected_cao_pct"], "")
        self.assertEqual(rows["1-11-BNK-01"]["expected_cao_pct"], "52.4")


if __name__ == "__main__":
    unittest.main()
