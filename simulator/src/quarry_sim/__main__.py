"""Command-line entry point: python -m quarry_sim --start-date 2026-11-02 --days 7"""

import argparse
import logging
import os
import sys
from datetime import date
from pathlib import Path

log = logging.getLogger("quarry_sim")


def positive_int(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be 1 or greater")
    return number


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="quarry_sim",
        description="Generate raw source-system data for the quarry and crushing plant.",
    )
    parser.add_argument("--start-date", type=date.fromisoformat, required=True,
                        help="first simulated day, YYYY-MM-DD")
    parser.add_argument("--days", type=positive_int, default=7,
                        help="number of days to simulate (default: 7)")
    parser.add_argument("--seed", type=int, default=42,
                        help="random seed; same seed + same dates = identical output (default: 42)")
    parser.add_argument("--output", type=Path,
                        default=Path(os.environ.get("QUARRY_SIM_OUTPUT", "output")),
                        help="output directory (default: $QUARRY_SIM_OUTPUT or ./output)")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    )
    args = parse_args(argv)

    try:
        args.output.mkdir(parents=True, exist_ok=True)
        probe = args.output / ".write_test"
        probe.touch()
        probe.unlink()
    except OSError as exc:
        log.error("Output directory %s is not writable: %s", args.output, exc)
        return 1

    log.info("Simulating %d day(s) from %s with seed %d into %s",
             args.days, args.start_date, args.seed, args.output.resolve())
    # Next activities plug in here: load config (1.2), build shift calendar (1.3), simulate.
    log.info("Done")
    return 0


def run() -> None:
    sys.exit(main())


if __name__ == "__main__":
    run()
