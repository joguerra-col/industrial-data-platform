"""Write simulator output files."""

import csv
from dataclasses import fields
from pathlib import Path

from quarry_sim.config import PlantConfig, Zone

# Column order of the FMS /equipment endpoint (data-requirements.md 3.2).
EQUIPMENT_COLUMNS = ("equipment_id", "equipment_type", "model_class", "nominal_payload_t",
                     "bucket_capacity_t", "fuel_tank_l", "commissioned_date")
# Column order of the geological model (data-requirements.md 2.3).
BENCH_COLUMNS = ("bench_id", "elevation_m", "material_type", "expected_cao_pct",
                 "expected_mgo_pct", "expected_sio2_pct", "rock_density_t_m3",
                 "available_tonnage_t", "initial_broken_stock_t", "status")


def write_csv(path: Path, rows, columns) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        for row in rows:
            writer.writerow(getattr(row, c) for c in columns)  # None -> empty cell


def write_reference(config: PlantConfig, output: Path) -> None:
    """Publish master data so Silver can build dimensions."""
    ref = output / "reference"
    write_csv(ref / "equipment.csv", config.equipment, EQUIPMENT_COLUMNS)
    write_csv(ref / "benches.csv", config.benches, BENCH_COLUMNS)
    write_csv(ref / "zones.csv", config.zones, tuple(f.name for f in fields(Zone)))
