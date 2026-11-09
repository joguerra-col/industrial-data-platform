import tempfile
import unittest
from datetime import date
from pathlib import Path

from quarry_sim.__main__ import main, parse_args


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

    def test_creates_output_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "raw"
            self.assertEqual(main(["--start-date", "2026-11-02", "--output", str(out)]), 0)
            self.assertTrue(out.is_dir())

    def test_unwritable_output_returns_1(self):
        with tempfile.TemporaryDirectory() as tmp:
            blocker = Path(tmp) / "file"
            blocker.touch()  # a file where a directory is expected
            self.assertEqual(main(["--start-date", "2026-11-02", "--output", str(blocker / "x")]), 1)


if __name__ == "__main__":
    unittest.main()
