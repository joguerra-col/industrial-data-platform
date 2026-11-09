"""Load and validate the plant configuration (config/plant.toml)."""

import re
import tomllib
from dataclasses import MISSING, dataclass, fields, replace
from datetime import date
from pathlib import Path
from zoneinfo import ZoneInfo

ASSET_ID = re.compile(r"^\d-\d{2}-[A-Z]{3}-\d{2}$")  # A-GL-TTT-NN
ZONE_ID = re.compile(r"^ZN-[A-Z]{3}-\d{2}$")
HHMM = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$|^24:00$")

EQUIPMENT_PREFIX = {
    "drill": "1-11-DRL",
    "excavator": "1-11-EXC",
    "loader": "1-11-LDR",
    "haul_truck": "1-91-TRK",
}
PLANT_ASSET_PREFIX = {
    "hopper_id": "2-11-HOP",
    "crusher_id": "2-11-CRS",
    "belt_scale_id": "2-11-BWS",
    "analyzer_id": "2-11-ANZ",
    "stockpile_id": "2-91-STK",
    "waste_dump_id": "1-81-DMP",
}
MATERIALS = {"HG", "MG", "WASTE"}
BENCH_STATUSES = {"active", "planned", "exhausted"}
ZONE_TYPES = {"load", "queue", "dump_crusher", "dump_waste", "workshop", "parking"}
# Design assumption from data-requirements.md 3.7: (min, max) % per oxide.
CHEMISTRY_RANGES = {
    "HG": {"expected_cao_pct": (50, 54), "expected_mgo_pct": (0, 2), "expected_sio2_pct": (1, 5)},
    "MG": {"expected_cao_pct": (44, 50), "expected_mgo_pct": (1, 3), "expected_sio2_pct": (5, 12)},
}


class ConfigError(Exception):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("\n".join(errors))


@dataclass(frozen=True)
class Plant:
    timezone: str
    hopper_id: str
    crusher_id: str
    belt_scale_id: str
    analyzer_id: str
    stockpile_id: str
    waste_dump_id: str
    hopper_live_capacity_t: float
    crusher_nominal_tph: float
    crusher_to_scale_delay_s: float
    scale_to_analyzer_delay_s: float


@dataclass(frozen=True)
class Shift:
    name: str
    start: str  # "HH:MM" local time; "24:00" = midnight at the end of the day
    end: str
    meal_window_start: str
    meal_window_end: str


@dataclass(frozen=True)
class Calendar:
    operating_weekdays: tuple[int, ...]  # 0 = Monday
    handover_min: int
    meal_break_min: int
    shifts: tuple[Shift, ...]


@dataclass(frozen=True)
class Equipment:
    equipment_id: str
    equipment_type: str
    model_class: str
    fuel_tank_l: float
    commissioned_date: date
    nominal_payload_t: float | None = None  # haul trucks only
    bucket_capacity_t: float | None = None  # excavators and loaders only


@dataclass(frozen=True)
class Bench:
    bench_id: str
    elevation_m: int
    material_type: str
    rock_density_t_m3: float
    available_tonnage_t: float
    initial_broken_stock_t: float
    status: str
    expected_cao_pct: float | None = None  # None for WASTE
    expected_mgo_pct: float | None = None
    expected_sio2_pct: float | None = None


@dataclass(frozen=True)
class Zone:
    zone_id: str
    zone_type: str
    polygon_wkt: str


@dataclass(frozen=True)
class LoadingAssignment:
    loading_unit_id: str
    bench_id: str
    dispatch_weight: float


@dataclass(frozen=True)
class Haulage:
    distance_to_hopper_km: float
    distance_to_dump_km: float
    loaded_speed_kmh: float
    empty_speed_kmh: float
    bucket_pass_s: float
    dump_s: float
    fuel_l_per_h_per_t_loaded: float
    fuel_l_per_h_per_t_empty: float
    fuel_l_per_h_per_t_idle: float
    loading: tuple[LoadingAssignment, ...]


@dataclass(frozen=True)
class PlantConfig:
    plant: Plant
    calendar: Calendar
    equipment: tuple[Equipment, ...]
    benches: tuple[Bench, ...]
    zones: tuple[Zone, ...]
    haulage: Haulage


def hhmm_minutes(value: str) -> int:
    hours, minutes = value.split(":")
    return int(hours) * 60 + int(minutes)


def load_config(path: Path) -> PlantConfig:
    """Read and validate plant.toml. Raises ConfigError listing every problem found."""
    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ConfigError([f"cannot read {path}: {exc}"]) from exc
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError([f"invalid TOML: {exc}"]) from exc

    errors: list[str] = []
    plant = _build(Plant, raw.get("plant"), "plant", errors)
    cal_raw = raw.get("calendar") or {}
    shifts = [_build(Shift, t, f"calendar.shifts[{i}]", errors)
              for i, t in enumerate(cal_raw.get("shifts", []))]
    calendar = _build(Calendar, {**cal_raw, "shifts": ()}, "calendar", errors)
    equipment = [_build(Equipment, t, f"equipment[{i}]", errors)
                 for i, t in enumerate(raw.get("equipment", []))]
    benches = [_build(Bench, t, f"benches[{i}]", errors)
               for i, t in enumerate(raw.get("benches", []))]
    zones = [_build(Zone, t, f"zones[{i}]", errors) for i, t in enumerate(raw.get("zones", []))]
    haul_raw = raw.get("haulage") or {}
    loading = [_build(LoadingAssignment, t, f"haulage.loading[{i}]", errors)
               for i, t in enumerate(haul_raw.get("loading", []))]
    haulage = _build(Haulage, {**haul_raw, "loading": ()}, "haulage", errors)
    if errors:  # structural problems: validating values would only add noise
        raise ConfigError(errors)

    config = PlantConfig(
        plant=plant,
        calendar=Calendar(tuple(calendar.operating_weekdays), calendar.handover_min,
                          calendar.meal_break_min, tuple(shifts)),
        equipment=tuple(equipment),
        benches=tuple(benches),
        zones=tuple(zones),
        haulage=replace(haulage, loading=tuple(loading)),
    )
    _validate(config, errors)
    if errors:
        raise ConfigError(errors)
    return config


def _build(cls, table, where: str, errors: list[str]):
    """Instantiate a dataclass from a TOML table, recording missing or unknown keys."""
    if not isinstance(table, dict):
        errors.append(f"{where}: section is missing")
        return None
    names = {f.name for f in fields(cls)}
    required = {f.name for f in fields(cls) if f.default is MISSING}
    missing, unknown = required - table.keys(), table.keys() - names
    if missing:
        errors.append(f"{where}: missing {', '.join(sorted(missing))}")
    if unknown:
        errors.append(f"{where}: unknown {', '.join(sorted(unknown))}")
    if missing or unknown:
        return None
    return cls(**table)


def _positive(value, where: str, errors: list[str], allow_zero: bool = False) -> None:
    ok = isinstance(value, (int, float)) and not isinstance(value, bool) and (
        value >= 0 if allow_zero else value > 0)
    if not ok:
        errors.append(f"{where}: must be a number {'>= 0' if allow_zero else '> 0'}, got {value!r}")


def _validate(cfg: PlantConfig, errors: list[str]) -> None:
    p = cfg.plant
    try:
        ZoneInfo(p.timezone)
    except Exception:
        errors.append(f"plant.timezone: unknown time zone {p.timezone!r}")
    for field, prefix in PLANT_ASSET_PREFIX.items():
        value = getattr(p, field)
        if not (ASSET_ID.match(value) and value.startswith(prefix + "-")):
            errors.append(f"plant.{field}: {value!r} must look like {prefix}-NN")
    for field in ("hopper_live_capacity_t", "crusher_nominal_tph",
                  "crusher_to_scale_delay_s", "scale_to_analyzer_delay_s"):
        _positive(getattr(p, field), f"plant.{field}", errors)

    _validate_calendar(cfg.calendar, errors)

    for e in cfg.equipment:
        where = f"equipment {e.equipment_id}"
        prefix = EQUIPMENT_PREFIX.get(e.equipment_type)
        if prefix is None:
            errors.append(f"{where}: unknown equipment_type {e.equipment_type!r}")
        elif not (ASSET_ID.match(e.equipment_id) and e.equipment_id.startswith(prefix + "-")):
            errors.append(f"{where}: ID must look like {prefix}-NN for a {e.equipment_type}")
        _positive(e.fuel_tank_l, f"{where}.fuel_tank_l", errors)
        if not isinstance(e.commissioned_date, date):
            errors.append(f"{where}.commissioned_date: must be a date like 2021-03-15")
        if e.equipment_type == "haul_truck":
            _positive(e.nominal_payload_t, f"{where}.nominal_payload_t", errors)
        elif e.nominal_payload_t is not None:
            errors.append(f"{where}: nominal_payload_t is for haul trucks only")
        if e.equipment_type in ("excavator", "loader"):
            _positive(e.bucket_capacity_t, f"{where}.bucket_capacity_t", errors)
        elif e.bucket_capacity_t is not None:
            errors.append(f"{where}: bucket_capacity_t is for excavators and loaders only")

    types = {e.equipment_type for e in cfg.equipment}
    if "haul_truck" not in types:
        errors.append("equipment: at least one haul_truck is required")
    if not types & {"excavator", "loader"}:
        errors.append("equipment: at least one excavator or loader is required")

    for b in cfg.benches:
        where = f"bench {b.bench_id}"
        if not (ASSET_ID.match(b.bench_id) and b.bench_id.startswith("1-11-BNK-")):
            errors.append(f"{where}: ID must look like 1-11-BNK-NN")
        if b.material_type not in MATERIALS:
            errors.append(f"{where}: material_type must be one of {sorted(MATERIALS)}")
        if b.status not in BENCH_STATUSES:
            errors.append(f"{where}: status must be one of {sorted(BENCH_STATUSES)}")
        _positive(b.rock_density_t_m3, f"{where}.rock_density_t_m3", errors)
        _positive(b.available_tonnage_t, f"{where}.available_tonnage_t", errors, allow_zero=True)
        _positive(b.initial_broken_stock_t, f"{where}.initial_broken_stock_t", errors,
                  allow_zero=True)
        ranges = CHEMISTRY_RANGES.get(b.material_type)
        for oxide in ("expected_cao_pct", "expected_mgo_pct", "expected_sio2_pct"):
            value = getattr(b, oxide)
            if ranges is None:  # WASTE
                if value is not None:
                    errors.append(f"{where}.{oxide}: WASTE benches have no expected chemistry")
            elif value is None or not ranges[oxide][0] <= value <= ranges[oxide][1]:
                low, high = ranges[oxide]
                errors.append(f"{where}.{oxide}: {value!r} outside {b.material_type} range "
                              f"{low}-{high}")
    if not any(b.status == "active" and b.material_type in ("HG", "MG") for b in cfg.benches):
        errors.append("benches: at least one active HG or MG bench is required")

    bench_ids = {b.bench_id for b in cfg.benches}
    for z in cfg.zones:
        where = f"zone {z.zone_id}"
        expected = {
            "load": bench_ids,
            "dump_crusher": {p.hopper_id},
            "dump_waste": {p.waste_dump_id},
        }.get(z.zone_type)
        if z.zone_type not in ZONE_TYPES:
            errors.append(f"{where}: zone_type must be one of {sorted(ZONE_TYPES)}")
        elif expected is not None and z.zone_id not in expected:
            errors.append(f"{where}: a {z.zone_type} zone must reuse its asset ID "
                          f"({', '.join(sorted(expected))})")
        elif expected is None and not ZONE_ID.match(z.zone_id):
            errors.append(f"{where}: ID must look like ZN-TTT-NN")
        if not z.polygon_wkt.startswith("POLYGON(("):
            errors.append(f"{where}.polygon_wkt: must be a WKT POLYGON((...))")

    ids = ([e.equipment_id for e in cfg.equipment] + [b.bench_id for b in cfg.benches]
           + [getattr(p, f) for f in PLANT_ASSET_PREFIX])
    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        errors.append(f"asset ID {dup} is used more than once")
    zone_ids = [z.zone_id for z in cfg.zones]
    for dup in sorted({i for i in zone_ids if zone_ids.count(i) > 1}):
        errors.append(f"zone ID {dup} is used more than once")

    _validate_haulage(cfg, errors)


def _validate_haulage(cfg: PlantConfig, errors: list[str]) -> None:
    h = cfg.haulage
    for f in fields(Haulage):
        if f.name != "loading":
            _positive(getattr(h, f.name), f"haulage.{f.name}", errors)
    units = {e.equipment_id: e for e in cfg.equipment}
    benches = {b.bench_id: b for b in cfg.benches}
    zone_ids = {z.zone_id for z in cfg.zones}
    for zone in (cfg.plant.hopper_id, cfg.plant.waste_dump_id):
        if zone not in zone_ids:
            errors.append(f"zones: haulage needs a zone for {zone}")
    if not h.loading:
        errors.append("haulage: at least one [[haulage.loading]] assignment is required")
    for a in h.loading:
        where = f"haulage.loading {a.loading_unit_id}"
        unit = units.get(a.loading_unit_id)
        if unit is None or unit.equipment_type not in ("excavator", "loader"):
            errors.append(f"{where}: must be an excavator or loader in [[equipment]]")
        bench = benches.get(a.bench_id)
        if bench is None or bench.status != "active":
            errors.append(f"{where}: bench {a.bench_id} must exist and be active")
        if a.bench_id not in zone_ids:
            errors.append(f"{where}: bench {a.bench_id} has no load zone")
        _positive(a.dispatch_weight, f"{where}.dispatch_weight", errors)
    assigned = [a.loading_unit_id for a in h.loading]
    for dup in sorted({u for u in assigned if assigned.count(u) > 1}):
        errors.append(f"haulage.loading: {dup} is assigned more than once")
    if not any(benches.get(a.bench_id) and benches[a.bench_id].material_type in ("HG", "MG")
               for a in h.loading):
        errors.append("haulage.loading: at least one HG or MG bench must be worked")


def _validate_calendar(cal: Calendar, errors: list[str]) -> None:
    if not cal.operating_weekdays or not set(cal.operating_weekdays) <= set(range(7)):
        errors.append("calendar.operating_weekdays: use numbers 0 (Monday) to 6 (Sunday)")
    _positive(cal.handover_min, "calendar.handover_min", errors)
    _positive(cal.meal_break_min, "calendar.meal_break_min", errors)
    if not cal.shifts:
        errors.append("calendar: at least one shift is required")
    # Bad values were reported above; use 0 so the shift checks below don't crash on them.
    handover = cal.handover_min if isinstance(cal.handover_min, int) else 0
    meal_break = cal.meal_break_min if isinstance(cal.meal_break_min, int) else 0
    for s in cal.shifts:
        where = f"shift {s.name}"
        times = (s.start, s.end, s.meal_window_start, s.meal_window_end)
        if not all(isinstance(t, str) and HHMM.match(t) for t in times):
            errors.append(f"{where}: times must be HH:MM (00:00 to 24:00)")
            continue
        start, end, meal_start, meal_end = map(hhmm_minutes, times)
        if not start < end:
            errors.append(f"{where}: start must be before end")
        if not start + handover <= meal_start < meal_end <= end - handover:
            errors.append(f"{where}: meal window must fall inside the shift, outside handovers")
        if meal_end - meal_start < meal_break:
            errors.append(f"{where}: meal window is shorter than one meal break")
