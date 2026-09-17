"""Pure tariff calculation engine."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from .const import *  # noqa: F403 - calculation keys are intentionally declarative
from .tariffs import (
    PERIOD_OFF_PEAK,
    PERIOD_ON_PEAK,
    PERIOD_STANDARD,
    PERIOD_SUMMER,
    PERIOD_WINTER_ADDITIONAL,
    PERIOD_WINTER_FIRST,
    PROFILES,
    parse_cpp_events,
    rate_for_period,
    tou_period,
)

LOCAL_TZ = ZoneInfo(TIME_ZONE)  # noqa: F405


@dataclass(frozen=True, slots=True)
class UsageInterval:
    start: datetime
    end: datetime
    kwh: float


@dataclass(frozen=True, slots=True)
class CostPoint:
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
    if local_time.day >= start_day:
        return f"{local_time.year:04d}-{local_time.month:02d}-{start_day:02d}"
    if local_time.month == 1:
        return f"{local_time.year - 1:04d}-12-{start_day:02d}"
    return f"{local_time.year:04d}-{local_time.month - 1:02d}-{start_day:02d}"


def expand_to_hours(intervals: list[UsageInterval]) -> list[UsageInterval]:
    """Uniformly split aggregate readings into no-more-than-hourly buckets."""
    expanded: list[UsageInterval] = []
    for item in intervals:
        if item.kwh < 0 or item.end <= item.start:
            continue
        duration = item.end - item.start
        pieces = max(1, round(duration.total_seconds() / 3600))
        step = duration / pieces
        for index in range(pieces):
            expanded.append(UsageInterval(
                item.start + step * index,
                item.start + step * (index + 1),
                item.kwh / pieces,
            ))
    return expanded


def _two_tier(kwh: float, prior: float, threshold: float,
              first_rate: float, extra_rate: float) -> tuple[float, str, float]:
    first = min(kwh, max(0.0, threshold - prior))
    extra = kwh - first
    cost = first * first_rate + extra * extra_rate
    period = PERIOD_WINTER_FIRST if not extra else PERIOD_WINTER_ADDITIONAL
    return cost, period, cost / kwh if kwh else first_rate


def _three_tier(kwh: float, prior: float, first_end: float, second_end: float,
                first_rate: float, second_rate: float,
                third_rate: float) -> tuple[float, str, float]:
    first = min(kwh, max(0.0, first_end - prior))
    second = min(kwh - first, max(0.0, second_end - max(prior, first_end)))
    third = kwh - first - second
    cost = first * first_rate + second * second_rate + third * third_rate
    period = "tier_1" if not second and not third else "tier_2" if not third else "tier_3"
    return cost, period, cost / kwh if kwh else first_rate


def calculate(intervals: list[UsageInterval], profile_id: str, config: dict) -> list[CostPoint]:
    """Calculate cumulative energy-only and estimated-total costs."""
    profile = PROFILES[profile_id]
    cpp_events = parse_cpp_events(str(config.get(CONF_CPP_EVENTS, "")))  # noqa: F405
    cycle_day = int(config[CONF_BILLING_CYCLE_DAY])  # noqa: F405
    additional_kwh = float(config.get(CONF_ADDITIONAL_KWH_RATE, 0))  # noqa: F405
    tax_multiplier = 1 + float(config.get(CONF_TAX_PERCENT, 0)) / 100  # noqa: F405
    demand_mode = str(config.get(CONF_DEMAND_MODE, DEMAND_MODE_HOURLY))  # noqa: F405

    energy_sum = total_sum = 0.0
    cycle_key = ""
    cycle_kwh = cycle_energy = cycle_total = cycle_raw_total = 0.0
    max_kw = on_peak_kw = 0.0
    points: list[CostPoint] = []

    for item in expand_to_hours(intervals):
        local = item.start.astimezone(LOCAL_TZ)
        new_cycle_key = billing_cycle_key(local, cycle_day)
        fixed_increment = 0.0
        if new_cycle_key != cycle_key:
            cycle_key = new_cycle_key
            cycle_kwh = cycle_energy = cycle_total = cycle_raw_total = 0.0
            max_kw = on_peak_kw = 0.0
            fixed_increment = float(config[CONF_BASIC_CHARGE])  # noqa: F405
            fixed_increment += float(config.get(CONF_MONTHLY_ADJUSTMENT, 0))  # noqa: F405
            if bool(config.get(CONF_THREE_PHASE, False)):  # noqa: F405
                fixed_increment += float(config.get(CONF_THREE_PHASE_CHARGE, 0))  # noqa: F405
            size = float(config.get(CONF_SYSTEM_SIZE_KW, 0))  # noqa: F405
            fixed_increment += size * float(config.get(CONF_NON_BYPASSABLE_RATE, 0))  # noqa: F405
            fixed_increment += max(0.0, size - 15) * float(config.get(CONF_GRID_ACCESS_RATE, 0))  # noqa: F405
            if profile.model == "tou_demand" and demand_mode == DEMAND_MODE_MANUAL:  # noqa: F405
                on_peak_kw = float(config.get(CONF_MANUAL_ON_PEAK_KW, 0))  # noqa: F405
                max_kw = float(config.get(CONF_MANUAL_MAX_KW, 0))  # noqa: F405
                fixed_increment += on_peak_kw * float(config[CONF_ON_PEAK_DEMAND_RATE])  # noqa: F405
                fixed_increment += max_kw * float(config[CONF_MAX_DEMAND_RATE])  # noqa: F405

        duration_hours = max((item.end - item.start).total_seconds() / 3600, 1 / 60)
        interval_kw = item.kwh / duration_hours

        if profile.model == "flat":
            period, rate = PERIOD_STANDARD, float(config[CONF_ENERGY_RATE])  # noqa: F405
            energy_increment = item.kwh * rate
        elif profile.model == "tiered_2":
            energy_increment, period, rate = _two_tier(
                item.kwh, cycle_kwh, float(config[CONF_TIER_KWH]),  # noqa: F405
                float(config[CONF_WINTER_FIRST_RATE]),  # noqa: F405
                float(config[CONF_WINTER_ADDITIONAL_RATE]),  # noqa: F405
            )
        elif profile.model == "tiered_3":
            energy_increment, period, rate = _three_tier(
                item.kwh, cycle_kwh, float(config[CONF_TIER_1_KWH]),  # noqa: F405
                float(config[CONF_TIER_2_KWH]), float(config[CONF_TIER_1_RATE]),  # noqa: F405
                float(config[CONF_TIER_2_RATE]), float(config[CONF_TIER_3_RATE]),  # noqa: F405
            )
        elif profile.model == "seasonal_tiered":
            if 5 <= local.month <= 9:
                period, rate = PERIOD_SUMMER, float(config[CONF_SUMMER_RATE])  # noqa: F405
                energy_increment = item.kwh * rate
            else:
                energy_increment, period, rate = _two_tier(
                    item.kwh, cycle_kwh, float(config[CONF_TIER_KWH]),  # noqa: F405
                    float(config[CONF_WINTER_FIRST_RATE]),  # noqa: F405
                    float(config[CONF_WINTER_ADDITIONAL_RATE]),  # noqa: F405
                )
        elif profile.model == "florida_tiered":
            first_rate = float(config[CONF_WINTER_FIRST_RATE] if local.month in (12, 1, 2) else config[CONF_SUMMER_RATE])  # noqa: F405
            extra_rate = float(config[CONF_WINTER_ADDITIONAL_RATE] if local.month in (12, 1, 2) else config[CONF_TIER_3_RATE])  # noqa: F405
            energy_increment, period, rate = _two_tier(
                item.kwh, cycle_kwh, float(config[CONF_TIER_KWH]), first_rate, extra_rate  # noqa: F405
            )
        elif profile.model == "indiana_high_eff":
            third_rate = float(config[CONF_SUMMER_RATE] if 7 <= local.month <= 10 else config[CONF_WINTER_ADDITIONAL_RATE])  # noqa: F405
            energy_increment, period, rate = _three_tier(
                item.kwh, cycle_kwh, float(config[CONF_TIER_1_KWH]),  # noqa: F405
                float(config[CONF_TIER_2_KWH]), float(config[CONF_TIER_1_RATE]),  # noqa: F405
                float(config[CONF_TIER_2_RATE]), third_rate,  # noqa: F405
            )
        elif profile.model == "oh_orh":
            if 6 <= local.month <= 9:
                period, rate = PERIOD_SUMMER, float(config[CONF_SUMMER_RATE])  # noqa: F405
                energy_increment = item.kwh * rate
            else:
                max_kw = max(max_kw, interval_kw, 10.0)
                second_end = max(float(config[CONF_TIER_KWH]), 150 * max_kw)  # noqa: F405
                energy_increment, period, rate = _three_tier(
                    item.kwh, cycle_kwh, float(config[CONF_TIER_KWH]), second_end,  # noqa: F405
                    float(config[CONF_WINTER_FIRST_RATE]),  # noqa: F405
                    float(config[CONF_WINTER_ADDITIONAL_RATE]),  # noqa: F405
                    float(config[CONF_TIER_3_RATE]),  # noqa: F405
                )
        else:
            period = tou_period(local, profile, cpp_events)
            if profile.model == "seasonal_tou":
                summer = 6 <= local.month <= 9
                rate = float(config[
                    CONF_SUMMER_ON_PEAK_RATE if summer and period == PERIOD_ON_PEAK else  # noqa: F405
                    CONF_SUMMER_OFF_PEAK_RATE if summer else  # noqa: F405
                    CONF_WINTER_ON_PEAK_RATE if period == PERIOD_ON_PEAK else  # noqa: F405
                    CONF_WINTER_OFF_PEAK_RATE  # noqa: F405
                ])
            else:
                rate = rate_for_period(profile, period, config)
            energy_increment = item.kwh * rate

        demand_increment = 0.0
        if profile.model == "tou_demand" and demand_mode == DEMAND_MODE_HOURLY:  # noqa: F405
            if interval_kw > max_kw:
                demand_increment += (interval_kw - max_kw) * float(config[CONF_MAX_DEMAND_RATE])  # noqa: F405
                max_kw = interval_kw
            if period == PERIOD_ON_PEAK and interval_kw > on_peak_kw:
                demand_increment += (interval_kw - on_peak_kw) * float(config[CONF_ON_PEAK_DEMAND_RATE])  # noqa: F405
                on_peak_kw = interval_kw

        raw_increment = energy_increment + item.kwh * additional_kwh + fixed_increment + demand_increment
        previous_billed = max(cycle_raw_total, float(config.get(CONF_MINIMUM_BILL, 0)))  # noqa: F405
        cycle_raw_total += raw_increment
        billed = max(cycle_raw_total, float(config.get(CONF_MINIMUM_BILL, 0)))  # noqa: F405
        total_increment = (billed - previous_billed if cycle_kwh else billed) * tax_multiplier

        energy_sum += energy_increment
        total_sum += total_increment
        cycle_kwh += item.kwh
        cycle_energy += energy_increment
        cycle_total += total_increment
        points.append(CostPoint(
            item.start, energy_increment, energy_sum, total_increment, total_sum,
            item.kwh, period, rate, cycle_key, cycle_kwh, cycle_energy, cycle_total,
            on_peak_kw, max_kw,
        ))
    return points
