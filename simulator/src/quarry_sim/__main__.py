"""Command-line entry point: python -m quarry_sim --start-date 2026-11-02 --days 7"""

import argparse
import logging
import os
import random
import sys
from datetime import date
from pathlib import Path

from quarry_sim.calendar import build_calendar
from quarry_sim.config import ConfigError, load_config
from quarry_sim.haulage import simulate_haulage
from quarry_sim.writers import write_fms_events, write_reference

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
    parser.add_argument("--config", type=Path, default=Path("config/plant.toml"),
                        help="plant configuration file (default: config/plant.toml)")
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

    try:
        config = load_config(args.config)
    except ConfigError as exc:
        log.error("Invalid configuration %s:", args.config)
        for error in exc.errors:
            log.error("  - %s", error)
        return 1
    log.info("Loaded %s: %d equipment, %d benches, %d zones", args.config,
             len(config.equipment), len(config.benches), len(config.zones))

    log.info("Simulating %d day(s) from %s with seed %d into %s",
             args.days, args.start_date, args.seed, args.output.resolve())
    try:
        write_reference(config, args.output)
    except OSError as exc:
        log.error("Could not write output: %s", exc)
        return 1

    # One random stream per component, so changing one component never shifts another's output.
    shifts = build_calendar(config, args.start_date, args.days,
                            random.Random(f"{args.seed}:calendar"))
    if not shifts:
        log.warning("No scheduled shifts in the requested dates: nothing to simulate")
        log.info("Done")
        return 0
    log.info("Calendar: %d shifts, %s to %s", len(shifts), shifts[0].shift_id,
             shifts[-1].shift_id)

    haulage = simulate_haulage(config, shifts, args.start_date,
                               random.Random(f"{args.seed}:haulage"))
    tonnes = {}
    for trip in haulage.trips:
        tonnes[trip.material_type] = tonnes.get(trip.material_type, 0) + trip.payload_t
    log.info("Haulage: %d trips, %d events, tonnes %s", len(haulage.trips), len(haulage.events),
             {m: round(t) for m, t in sorted(tonnes.items())})
    try:
        paths = write_fms_events(haulage.events, args.output)
    except OSError as exc:
        log.error("Could not write output: %s", exc)
        return 1
    log.info("Wrote %d FMS event files to %s", len(paths), args.output / "fms" / "events")
    log.info("Done")
    return 0


def run() -> None:
    sys.exit(main())


if __name__ == "__main__":
    run()
