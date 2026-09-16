"""Bundled NC residential tariff defaults and rate-period classification."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from functools import lru_cache

from .const import (
    CONF_BASIC_CHARGE,
    CONF_CRITICAL_PEAK_RATE,
    CONF_DISCOUNT_RATE,
    CONF_MAX_DEMAND_RATE,
    CONF_OFF_PEAK_RATE,
    CONF_ON_PEAK_DEMAND_RATE,
    CONF_ON_PEAK_RATE,
    CONF_STANDARD_RATE,
    CONF_SUMMER_RATE,
    CONF_THREE_PHASE_CHARGE,
    CONF_TIER_KWH,
    CONF_WINTER_ADDITIONAL_RATE,
    CONF_WINTER_FIRST_RATE,
    SCHEDULE_RES,
    SCHEDULE_R_TOU,
    SCHEDULE_R_TOU_CPP,
    SCHEDULE_R_TOU_EV,
    SCHEDULE_R_TOUD,
)

PERIOD_STANDARD = "standard"
PERIOD_ON_PEAK = "on_peak"
PERIOD_OFF_PEAK = "off_peak"
PERIOD_DISCOUNT = "discount"
PERIOD_CRITICAL_PEAK = "critical_peak"
PERIOD_SUMMER = "summer"
PERIOD_WINTER_FIRST = "winter_first"
PERIOD_WINTER_ADDITIONAL = "winter_additional"

SCHEDULE_NAMES = {
    SCHEDULE_RES: "Schedule RES (leaf 500)",
    SCHEDULE_R_TOUD: "Schedule R-TOUD (leaf 501)",
    SCHEDULE_R_TOU: "Schedule R-TOU (leaf 502)",
    SCHEDULE_R_TOU_CPP: "Schedule R-TOU-CPP (leaf 503)",
    SCHEDULE_R_TOU_EV: "Schedule R-TOU-EV (leaf 504)",
}

DEFAULTS: dict[str, dict[str, float]] = {
    SCHEDULE_RES: {
        CONF_BASIC_CHARGE: 14.0,
        CONF_THREE_PHASE_CHARGE: 9.0,
        CONF_SUMMER_RATE: 0.12623,
        CONF_WINTER_FIRST_RATE: 0.12623,
        CONF_WINTER_ADDITIONAL_RATE: 0.11623,
        CONF_TIER_KWH: 800.0,
    },
    SCHEDULE_R_TOUD: {
        CONF_BASIC_CHARGE: 14.0,
        CONF_THREE_PHASE_CHARGE: 9.0,
        CONF_ON_PEAK_RATE: 0.15638,
        CONF_OFF_PEAK_RATE: 0.06633,
        CONF_DISCOUNT_RATE: 0.04347,
        CONF_ON_PEAK_DEMAND_RATE: 1.99,
        CONF_MAX_DEMAND_RATE: 3.91,
    },
    SCHEDULE_R_TOU: {
        CONF_BASIC_CHARGE: 14.0,
        CONF_THREE_PHASE_CHARGE: 9.0,
        CONF_ON_PEAK_RATE: 0.29905,
        CONF_OFF_PEAK_RATE: 0.11321,
        CONF_DISCOUNT_RATE: 0.07372,
    },
    SCHEDULE_R_TOU_CPP: {
        CONF_BASIC_CHARGE: 14.0,
        CONF_THREE_PHASE_CHARGE: 9.0,
        CONF_CRITICAL_PEAK_RATE: 0.41002,
        CONF_ON_PEAK_RATE: 0.21952,
        CONF_OFF_PEAK_RATE: 0.11000,
        CONF_DISCOUNT_RATE: 0.08274,
    },
    SCHEDULE_R_TOU_EV: {
        CONF_BASIC_CHARGE: 14.0,
        CONF_THREE_PHASE_CHARGE: 9.0,
        CONF_STANDARD_RATE: 0.13096,
        CONF_DISCOUNT_RATE: 0.06548,
    },
}


@dataclass(frozen=True, slots=True)
class CppEvent:
    """A critical peak date and optional local start hour."""

    day: date
    start_hour: int | None = None


def parse_cpp_events(value: str) -> dict[date, CppEvent]:
    """Parse comma/newline separated YYYY-MM-DD or YYYY-MM-DD@HH entries."""
    result: dict[date, CppEvent] = {}
    for raw in value.replace("\n", ",").split(","):
        item = raw.strip()
        if not item:
            continue
        day_text, separator, hour_text = item.partition("@")
        day = date.fromisoformat(day_text)
        start_hour = int(hour_text) if separator else None
        if start_hour is not None and not 0 <= start_hour <= 23:
            raise ValueError("CPP start hour must be between 0 and 23")
        result[day] = CppEvent(day, start_hour)
    return result


def _nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    first = date(year, month, 1)
    return first + timedelta(days=(weekday - first.weekday()) % 7 + 7 * (n - 1))


def _last_weekday(year: int, month: int, weekday: int) -> date:
    if month == 12:
        cursor = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        cursor = date(year, month + 1, 1) - timedelta(days=1)
    return cursor - timedelta(days=(cursor.weekday() - weekday) % 7)


def _observed(day: date) -> date:
    if day.weekday() == 5:
        return day - timedelta(days=1)
    if day.weekday() == 6:
        return day + timedelta(days=1)
    return day


def _easter(year: int) -> date:
    """Return Gregorian Easter Sunday (Meeus/Jones/Butcher algorithm)."""
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = (h + l - 7 * m + 114) % 31 + 1
    return date(year, month, day)


@lru_cache(maxsize=32)
def holidays(year: int) -> frozenset[date]:
    """Return tariff holidays for a year, including observed fixed holidays."""
    thanksgiving = _nth_weekday(year, 11, 3, 4)
    values = {
        _observed(date(year, 1, 1)),
        _easter(year) - timedelta(days=2),
        _last_weekday(year, 5, 0),
        _observed(date(year, 7, 4)),
        _nth_weekday(year, 9, 0, 1),
        thanksgiving,
        thanksgiving + timedelta(days=1),
        _observed(date(year, 12, 25)),
    }
    return frozenset(values)


def is_tariff_holiday(day: date) -> bool:
    """Return whether a local date is an applicable tariff holiday."""
    return day in holidays(day.year) or day in holidays(day.year - 1) or day in holidays(day.year + 1)


def tou_period(local_time: datetime, schedule: str, cpp_events: dict[date, CppEvent]) -> str:
    """Classify one local hourly interval."""
    hour = local_time.hour
    day = local_time.date()

    if schedule == SCHEDULE_R_TOU_EV:
        return PERIOD_DISCOUNT if hour >= 23 or hour < 5 else PERIOD_STANDARD

    summer = 5 <= local_time.month <= 9
    if summer:
        if 1 <= hour < 6:
            return PERIOD_DISCOUNT
        on_peak_start, on_peak_end = 18, 21
    else:
        if 1 <= hour < 3 or 11 <= hour < 16:
            return PERIOD_DISCOUNT
        on_peak_start, on_peak_end = 6, 9

    weekday_on_peak = local_time.weekday() < 5 and not is_tariff_holiday(day)
    if weekday_on_peak and schedule == SCHEDULE_R_TOU_CPP and day in cpp_events:
        event_start = cpp_events[day].start_hour
        if event_start is None:
            event_start = on_peak_start
        if event_start <= hour < event_start + 3:
            return PERIOD_CRITICAL_PEAK
        if cpp_events[day].start_hour is not None and on_peak_start <= hour < on_peak_end:
            return PERIOD_OFF_PEAK
    if weekday_on_peak and on_peak_start <= hour < on_peak_end:
        return PERIOD_ON_PEAK
    return PERIOD_OFF_PEAK


def rate_for_period(schedule: str, period: str, config: dict) -> float:
    """Return configured USD/kWh for a classified period."""
    mapping = {
        PERIOD_STANDARD: CONF_STANDARD_RATE,
        PERIOD_ON_PEAK: CONF_ON_PEAK_RATE,
        PERIOD_OFF_PEAK: CONF_OFF_PEAK_RATE,
        PERIOD_DISCOUNT: CONF_DISCOUNT_RATE,
        PERIOD_CRITICAL_PEAK: CONF_CRITICAL_PEAK_RATE,
        PERIOD_SUMMER: CONF_SUMMER_RATE,
        PERIOD_WINTER_FIRST: CONF_WINTER_FIRST_RATE,
        PERIOD_WINTER_ADDITIONAL: CONF_WINTER_ADDITIONAL_RATE,
    }
    return float(config[mapping[period]])
