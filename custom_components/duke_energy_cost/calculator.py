"""Pure tariff calculation engine."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from .const import (
    CONF_ADDITIONAL_KWH_RATE,
    CONF_BASIC_CHARGE,
    CONF_BILLING_CYCLE_DAY,
    CONF_DEMAND_MODE,
    CONF_MANUAL_MAX_KW,
    CONF_MANUAL_ON_PEAK_KW,
    CONF_MAX_DEMAND_RATE,
    CONF_MONTHLY_ADJUSTMENT,
    CONF_ON_PEAK_DEMAND_RATE,
    CONF_TAX_PERCENT,
    CONF_THREE_PHASE,
    CONF_THREE_PHASE_CHARGE,
    CONF_TIER_KWH,
    DEMAND_MODE_HOURLY,
    DEMAND_MODE_MANUAL,
    SCHEDULE_RES,
    SCHEDULE_R_TOUD,
    TIME_ZONE,
)
from .tariffs import (
    PERIOD_ON_PEAK,
    PERIOD_SUMMER,
    PERIOD_WINTER_ADDITIONAL,
    PERIOD_WINTER_FIRST,
    parse_cpp_events,
    rate_for_period,
    tou_period,
)

LOCAL_TZ = ZoneInfo(TIME_ZONE)


@dataclass(frozen=True, slots=True)
class UsageInterval:
    """A usage total covering a UTC interval."""

    start: datetime
    end: datetime
    kwh: float


@dataclass(frozen=True, slots=True)
class CostPoint:
    """One derived hourly cost point."""

    start: datetime
    energy_cost: float
    energy_cost_sum: float
    total_cost: float
    total_cost_sum: float
    kwh: float
    period: str
    rate: float
    cycle_key: str
    cycle_kwh: float
    cycle_energy_cost: float
    cycle_total_cost: float
    on_peak_demand_kw: float
    max_demand_kw: float


def billing_cycle_key(local_time: datetime, start_day: int) -> str:
    """Return a stable YYYY-MM-DD key for the configured billing cycle."""
    if local_time.day >= start_day:
        return f"{local_time.year:04d}-{local_time.month:02d}-{start_day:02d}"
    if local_time.month == 1:
        return f"{local_time.year - 1:04d}-12-{start_day:02d}"
    return f"{local_time.year:04d}-{local_time.month - 1:02d}-{start_day:02d}"


def expand_to_hours(intervals: list[UsageInterval]) -> list[UsageInterval]:
    """Uniformly split aggregate intervals into no-more-than-hourly buckets."""
    expanded: list[UsageInterval] = []
    for item in intervals:
        if item.kwh < 0 or item.end <= item.start:
            continue
        duration = item.end - item.start
        hours = duration.total_seconds() / 3600
        pieces = max(1, round(hours))
        step = duration / pieces
        for index in range(pieces):
            expanded.append(
                UsageInterval(
                    item.start + step * index,
                    item.start + step * (index + 1),
                    item.kwh / pieces,
                )
            )
    return expanded


def calculate(intervals: list[UsageInterval], schedule: str, config: dict) -> list[CostPoint]:
    """Calculate cumulative energy-only and estimated-total costs."""
    cpp_events = parse_cpp_events(str(config.get("cpp_events", "")))
    cycle_day = int(config[CONF_BILLING_CYCLE_DAY])
    additional_kwh = float(config.get(CONF_ADDITIONAL_KWH_RATE, 0))
    tax_multiplier = 1 + float(config.get(CONF_TAX_PERCENT, 0)) / 100
    demand_mode = str(config.get(CONF_DEMAND_MODE, DEMAND_MODE_HOURLY))

    energy_sum = 0.0
    total_sum = 0.0
    cycle_key = ""
    cycle_kwh = cycle_energy = cycle_total = 0.0
    max_kw = on_peak_kw = 0.0
    points: list[CostPoint] = []

    for item in expand_to_hours(intervals):
        local = item.start.astimezone(LOCAL_TZ)
        new_cycle_key = billing_cycle_key(local, cycle_day)
        fixed_increment = 0.0
        if new_cycle_key != cycle_key:
            cycle_key = new_cycle_key
            cycle_kwh = cycle_energy = cycle_total = 0.0
            max_kw = on_peak_kw = 0.0
            fixed_increment = float(config[CONF_BASIC_CHARGE]) + float(
                config.get(CONF_MONTHLY_ADJUSTMENT, 0)
            )
            if bool(config.get(CONF_THREE_PHASE, False)):
                fixed_increment += float(config[CONF_THREE_PHASE_CHARGE])
            if schedule == SCHEDULE_R_TOUD and demand_mode == DEMAND_MODE_MANUAL:
                on_peak_kw = float(config.get(CONF_MANUAL_ON_PEAK_KW, 0))
                max_kw = float(config.get(CONF_MANUAL_MAX_KW, 0))
                fixed_increment += on_peak_kw * float(config[CONF_ON_PEAK_DEMAND_RATE])
                fixed_increment += max_kw * float(config[CONF_MAX_DEMAND_RATE])

        if schedule == SCHEDULE_RES:
            if 5 <= local.month <= 9:
                period = PERIOD_SUMMER
                rate = rate_for_period(schedule, period, config)
                energy_increment = item.kwh * rate
            else:
                tier = float(config[CONF_TIER_KWH])
                first_kwh = min(item.kwh, max(0.0, tier - cycle_kwh))
                extra_kwh = item.kwh - first_kwh
                period = (
                    PERIOD_WINTER_FIRST if extra_kwh == 0 else PERIOD_WINTER_ADDITIONAL
                )
                energy_increment = first_kwh * rate_for_period(
                    schedule, PERIOD_WINTER_FIRST, config
                ) + extra_kwh * rate_for_period(
                    schedule, PERIOD_WINTER_ADDITIONAL, config
                )
                rate = energy_increment / item.kwh if item.kwh else rate_for_period(
                    schedule, PERIOD_WINTER_FIRST, config
                )
        else:
            period = tou_period(local, schedule, cpp_events)
            rate = rate_for_period(schedule, period, config)
            energy_increment = item.kwh * rate

        demand_increment = 0.0
        duration_hours = max((item.end - item.start).total_seconds() / 3600, 1 / 60)
        interval_kw = item.kwh / duration_hours
        if schedule == SCHEDULE_R_TOUD and demand_mode == DEMAND_MODE_HOURLY:
            if interval_kw > max_kw:
                demand_increment += (interval_kw - max_kw) * float(
                    config[CONF_MAX_DEMAND_RATE]
                )
                max_kw = interval_kw
            if period == PERIOD_ON_PEAK and interval_kw > on_peak_kw:
                demand_increment += (interval_kw - on_peak_kw) * float(
                    config[CONF_ON_PEAK_DEMAND_RATE]
                )
                on_peak_kw = interval_kw

        pre_tax_total = (
            energy_increment
            + item.kwh * additional_kwh
            + fixed_increment
            + demand_increment
        )
        total_increment = pre_tax_total * tax_multiplier
        energy_sum += energy_increment
        total_sum += total_increment
        cycle_kwh += item.kwh
        cycle_energy += energy_increment
        cycle_total += total_increment
        points.append(
            CostPoint(
                start=item.start,
                energy_cost=energy_increment,
                energy_cost_sum=energy_sum,
                total_cost=total_increment,
                total_cost_sum=total_sum,
                kwh=item.kwh,
                period=period,
                rate=rate,
                cycle_key=cycle_key,
                cycle_kwh=cycle_kwh,
                cycle_energy_cost=cycle_energy,
                cycle_total_cost=cycle_total,
                on_peak_demand_kw=on_peak_kw,
                max_demand_kw=max_kw,
            )
        )
    return points

