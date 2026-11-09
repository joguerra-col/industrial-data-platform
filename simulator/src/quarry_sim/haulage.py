"""Haul cycles -> raw FMS sensor events (data-requirements.md 3.2, events only).

Simplified on purpose (issue #2): no queues, every bench at the same haul distance, trucks start
each shift at the pit. The simulated trips are also returned as ground truth for tests and for
the plant simulation that will consume crusher dumps.
"""

import random
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from quarry_sim.calendar import ShiftWindow
from quarry_sim.config import Equipment, PlantConfig

EVENT_ID_NAMESPACE = uuid.UUID("6f1d9c52-3b1e-4c1a-9a57-2d6a0d4b8e10")  # fixed: stable event IDs
RECEIVE_DELAY_S = (1, 20)    # transmission delay from truck to FMS server
CARRYBACK_T = (0.0, 0.3)     # normal residual after dumping (section 3.2)
PAYLOAD_FILL = (0.95, 1.05)  # loaded tonnage vs. nominal payload
LOADING_WINDOW_MIN = 5       # upper bound of a truck's time at the loading unit
# shortcut: odometer and fuel start from a flat in-service average, so separate runs continue only
# approximately. Persist end-of-run state if runs ever need to chain exactly.
HISTORY_KM_PER_DAY = 90
HISTORY_FUEL_L_PER_KM = 4.5


@dataclass(frozen=True)
class Trip:
    truck_id: str
    loading_unit_id: str
    bench_id: str
    material_type: str
    destination_id: str
    payload_t: float       # last payload_step
    carryback_t: float     # residual at body_down
    load_start: datetime   # zone_enter at the bench
    dump_ts: datetime      # body_up at the destination


@dataclass
class _Truck:
    unit: Equipment
    odometer_km: float
    fuel_used_l: float
    seq: int = 0


@dataclass
class HaulageResult:
    events: list[dict]  # sorted by event_ts; timestamps are UTC datetimes
    trips: list[Trip]


def simulate_haulage(config: PlantConfig, shifts: list[ShiftWindow], start_date: date,
                     rng: random.Random) -> HaulageResult:
    stock = {b.bench_id: b.initial_broken_stock_t for b in config.benches}
    trucks = []
    for e in config.equipment:
        if e.equipment_type == "haul_truck":
            km = max((start_date - e.commissioned_date).days, 0) * HISTORY_KM_PER_DAY
            trucks.append(_Truck(e, km, km * HISTORY_FUEL_L_PER_KM))
    events: list[dict] = []
    trips: list[Trip] = []
    for shift in shifts:
        for i, truck in enumerate(trucks):
            _run_shift(config, shift, truck, i, stock, rng, events, trips)
    events.sort(key=lambda e: (e["event_ts"], e["equipment_id"], e["_seq"]))
    for e in events:
        del e["_seq"]
    return HaulageResult(events, trips)


def _run_shift(cfg: PlantConfig, shift: ShiftWindow, truck: _Truck, index: int,
               stock: dict[str, float], rng: random.Random, events: list, trips: list) -> None:
    h = cfg.haulage
    units = {e.equipment_id: e for e in cfg.equipment}
    benches = {b.bench_id: b for b in cfg.benches}
    breaks = {b.equipment_id: b for b in shift.meal_breaks}
    my_break = breaks[truck.unit.equipment_id]
    operator = f"OP-{shift.name}{index + 1:02d}"  # fixed crew per shift, anonymous code
    payload_nominal = truck.unit.nominal_payload_t

    def emit(ts, event_type, zone_id=None, payload_t=None, operator_id=None):
        truck.seq += 1
        events.append({
            "event_id": str(uuid.uuid5(EVENT_ID_NAMESPACE,
                                       f"{truck.unit.equipment_id}|{ts.isoformat()}|{truck.seq}")),
            "equipment_id": truck.unit.equipment_id,
            "event_ts": ts,
            "received_ts": ts + timedelta(seconds=rng.uniform(*RECEIVE_DELAY_S)),
            "event_type": event_type,
            "zone_id": zone_id,
            "payload_t": None if payload_t is None else round(payload_t, 2),
            "bucket_weight_t": None,
            "related_equipment_id": None,
            "operator_id": operator_id,
            "odometer_km": round(truck.odometer_km, 3),
            "fuel_used_cum_l": round(truck.fuel_used_l, 1),
            "_seq": truck.seq,  # tie-breaker for sorting, removed before returning
        })

    def idle(until: datetime, since: datetime) -> None:
        hours = max((until - since).total_seconds(), 0) / 3600
        truck.fuel_used_l += hours * h.fuel_l_per_h_per_t_idle * payload_nominal

    def drive(km: float, speed_kmh: float, fuel_rate: float) -> timedelta:
        hours = km / (speed_kmh * rng.uniform(0.9, 1.1))
        truck.odometer_km += km
        truck.fuel_used_l += hours * fuel_rate * payload_nominal
        return timedelta(hours=hours)

    t = shift.work_start_utc + timedelta(minutes=2 * index)  # stagger departures
    emit(t, "operator_login", operator_id=operator)
    while True:
        # Loading units free of meal breaks for the whole loading time, with stock on their bench.
        load_end = t + timedelta(minutes=LOADING_WINDOW_MIN)
        candidates = [a for a in h.loading
                      if not (breaks[a.loading_unit_id].start_utc < load_end
                              and t < breaks[a.loading_unit_id].end_utc)
                      and stock[a.bench_id] > 0]
        if not candidates:
            break  # shortcut: no waiting for a unit to come back; the truck ends its shift
        assignment = rng.choices(candidates, weights=[a.dispatch_weight for a in candidates])[0]
        bench = benches[assignment.bench_id]
        bucket = units[assignment.loading_unit_id].bucket_capacity_t
        target = payload_nominal * rng.uniform(*PAYLOAD_FILL)
        passes = max(1, round(target / bucket))
        steps = [target / passes * rng.uniform(0.97, 1.03) for _ in range(passes)]
        to_crusher = bench.material_type != "WASTE"
        destination = cfg.plant.hopper_id if to_crusher else cfg.plant.waste_dump_id
        distance = h.distance_to_hopper_km if to_crusher else h.distance_to_dump_km

        # Estimate the cycle with mean speeds; skip it if it would cross the break or shift end.
        estimate = timedelta(seconds=(passes + 2) * h.bucket_pass_s + h.dump_s + 60) + timedelta(
            hours=distance / h.loaded_speed_kmh + distance / h.empty_speed_kmh) * 1.15
        if t < my_break.end_utc and t + estimate > my_break.start_utc:
            idle(my_break.start_utc, t)
            emit(max(t, my_break.start_utc), "operator_logout", operator_id=operator)
            t = my_break.end_utc
            emit(t, "operator_login", operator_id=operator)
            continue
        if t + estimate > shift.work_end_utc:
            break

        load_start = t
        emit(t, "zone_enter", zone_id=bench.bench_id)
        payload = 0.0
        for step in steps:
            t += timedelta(seconds=h.bucket_pass_s * rng.uniform(0.85, 1.15))
            payload += step
            emit(t, "payload_step", zone_id=bench.bench_id, payload_t=payload)
        t += timedelta(seconds=30)
        emit(t, "zone_exit", zone_id=bench.bench_id, payload_t=payload)
        t += drive(distance, h.loaded_speed_kmh, h.fuel_l_per_h_per_t_loaded)
        emit(t, "zone_enter", zone_id=destination, payload_t=payload)
        t += timedelta(seconds=20)
        dump_ts = t
        emit(t, "body_up", zone_id=destination, payload_t=payload)
        carryback = rng.uniform(*CARRYBACK_T)
        t += timedelta(seconds=h.dump_s)
        emit(t, "body_down", zone_id=destination, payload_t=carryback)
        t += timedelta(seconds=20)
        emit(t, "zone_exit", zone_id=destination, payload_t=carryback)
        t += drive(distance, h.empty_speed_kmh, h.fuel_l_per_h_per_t_empty)

        stock[bench.bench_id] = max(stock[bench.bench_id] - payload, 0)
        trips.append(Trip(truck.unit.equipment_id, assignment.loading_unit_id, bench.bench_id,
                          bench.material_type, destination, round(payload, 2),
                          round(carryback, 2), load_start, dump_ts))

    idle(shift.work_end_utc, t)
    emit(max(t, shift.work_end_utc), "operator_logout", operator_id=operator)
