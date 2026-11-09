"""Shift calendar: when each shift runs and when each operator takes a meal break (section 2.4)."""

import random
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from quarry_sim.config import PlantConfig, hhmm_minutes

LOADING_TYPES = ("excavator", "loader")


@dataclass(frozen=True)
class MealBreak:
    equipment_id: str
    start_utc: datetime
    end_utc: datetime


@dataclass(frozen=True)
class ShiftWindow:
    shift_id: str           # YYYYMMDD-A, local date
    name: str
    start_utc: datetime     # scheduled start
    end_utc: datetime       # scheduled end
    work_start_utc: datetime  # after the start handover
    work_end_utc: datetime    # before the end handover
    meal_breaks: tuple[MealBreak, ...]


def build_calendar(config: PlantConfig, start_date: date, days: int,
                   rng: random.Random) -> list[ShiftWindow]:
    """All scheduled shifts in [start_date, start_date + days), in chronological order."""
    cal = config.calendar
    tz = ZoneInfo(config.plant.timezone)
    handover = timedelta(minutes=cal.handover_min)
    shifts = []
    for offset in range(days):
        day = start_date + timedelta(days=offset)
        if day.weekday() not in cal.operating_weekdays:
            continue
        midnight = datetime(day.year, day.month, day.day, tzinfo=tz)

        def utc(hhmm: str) -> datetime:
            return (midnight + timedelta(minutes=hhmm_minutes(hhmm))).astimezone(timezone.utc)

        for s in cal.shifts:
            shifts.append(ShiftWindow(
                shift_id=f"{day:%Y%m%d}-{s.name}",
                name=s.name,
                start_utc=utc(s.start),
                end_utc=utc(s.end),
                work_start_utc=utc(s.start) + handover,
                work_end_utc=utc(s.end) - handover,
                meal_breaks=_meal_breaks(config.equipment, utc(s.meal_window_start),
                                         utc(s.meal_window_end), cal.meal_break_min, rng),
            ))
    return sorted(shifts, key=lambda s: s.start_utc)


def _meal_breaks(equipment, window_start: datetime, window_end: datetime, break_min: int,
                 rng: random.Random) -> tuple[MealBreak, ...]:
    """Staggered breaks: the window is cut into back-to-back slots and units are spread across
    them. Loading units get different slots first, so loading never stops at once."""
    length = timedelta(minutes=break_min)
    slot_count = int((window_end - window_start) / length)  # config validation ensures >= 1
    loading = [e for e in equipment if e.equipment_type in LOADING_TYPES]
    others = [e for e in equipment if e.equipment_type not in LOADING_TYPES]
    rng.shuffle(loading)
    rng.shuffle(others)
    first_slot = rng.randrange(slot_count)  # vary which slot the rotation starts on
    breaks = []
    for i, unit in enumerate(loading + others):
        start = window_start + ((first_slot + i) % slot_count) * length
        breaks.append(MealBreak(unit.equipment_id, start, start + length))
    return tuple(sorted(breaks, key=lambda b: (b.start_utc, b.equipment_id)))
