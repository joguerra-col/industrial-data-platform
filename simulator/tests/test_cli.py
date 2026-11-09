import tempfile
import unittest
from datetime import date
from pathlib import Path

from quarry_sim.__main__ import main, parse_args

CONFIG = str(Path(__file__).parents[1] / "config" / "plant.toml")


class CliTest(unittest.TestCase):
    def test_parses_valid_arguments(self):
        args = parse_args(["--start-date", "2026-11-02", "--days", "3", "--seed", "7"])
        self.assertEqual(args.start_date, date(2026, 11, 2))
        self.assertEqual(args.days, 3)
        self.assertEqual(args.seed, 7)

    def test_rejects_bad_date_and_days(self):
        for argv in (["--start-date", "2026-13-01"],
                     ["--start-date", "2026-11-02", "--days", "0"]):
            with self.subTest(argv=argv), self.assertRaises(SystemExit):
                parse_args(argv)

    def test_writes_reference_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "raw"
            argv = ["--start-date", "2026-11-02", "--output", str(out), "--config", CONFIG]
            self.assertEqual(main(argv), 0)
            for name in ("equipment.csv", "benches.csv", "zones.csv"):
                self.assertTrue((out / "reference" / name).is_file(), name)

    def test_invalid_config_returns_1(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "plant.toml"
            bad.write_text("[plant]\n", encoding="utf-8")
            argv = ["--start-date", "2026-11-02", "--output", tmp, "--config", str(bad)]
            self.assertEqual(main(argv), 1)

    def test_unwritable_output_returns_1(self):
        with tempfile.TemporaryDirectory() as tmp:
            blocker = Path(tmp) / "file"
            blocker.touch()  # a file where a directory is expected
            self.assertEqual(main(["--start-date", "2026-11-02", "--output", str(blocker / "x")]), 1)


if __name__ == "__main__":
    unittest.main()
