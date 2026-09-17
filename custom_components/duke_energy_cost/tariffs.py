"""Bundled residential tariff catalogue and time-period rules."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from functools import lru_cache
from typing import Any

from .const import *  # noqa: F403 - tariff tables use the configuration keys directly

PERIOD_STANDARD = "standard"
PERIOD_ON_PEAK = "on_peak"
PERIOD_OFF_PEAK = "off_peak"
PERIOD_DISCOUNT = "discount"
PERIOD_SUPER_OFF_PEAK = "super_off_peak"
PERIOD_CRITICAL_PEAK = "critical_peak"
PERIOD_SUMMER = "summer"
PERIOD_WINTER_FIRST = "winter_first"
PERIOD_WINTER_ADDITIONAL = "winter_additional"

STATE_NAMES = {
    "NC": "North Carolina",
    "SC": "South Carolina",
    "OH": "Ohio",
    "KY": "Kentucky",
    "IN": "Indiana",
    "FL": "Florida",
}

SERVICE_AREAS = {
    "nc_dep": ("NC", "Duke Energy Progress"),
    "nc_dec": ("NC", "Duke Energy Carolinas"),
    "sc_dep": ("SC", "Duke Energy Progress"),
    "sc_dec": ("SC", "Duke Energy Carolinas"),
    "oh_deo": ("OH", "Duke Energy Ohio"),
    "ky_dek": ("KY", "Duke Energy Kentucky"),
    "in_dei": ("IN", "Duke Energy Indiana"),
    "fl_def": ("FL", "Duke Energy Florida"),
}


@dataclass(frozen=True, slots=True)
class TariffProfile:
    """One selectable bill plan and its published default values."""

    profile_id: str
    service_area: str
    code: str
    name: str
    model: str
    period_scheme: str = "none"
    defaults: dict[str, Any] | None = None
    effective: str = ""
    reference: str = ""
    warning: str = ""

    @property
    def state(self) -> str:
        return SERVICE_AREAS[self.service_area][0]

    @property
    def label(self) -> str:
        return f"{self.name} ({self.code})"


def _base(basic: float, **values: float) -> dict[str, Any]:
    return {CONF_BASIC_CHARGE: basic, **values}


def _profile(pid: str, area: str, code: str, name: str, model: str, defaults: dict,
             *, scheme: str = "none", effective: str = "", reference: str = "",
             warning: str = "") -> TariffProfile:
    return TariffProfile(pid, area, code, name, model, scheme, defaults, effective,
                         reference, warning or _MISSING_RIDERS)


_MISSING_RIDERS = (
    "Published base/distribution rates are prefilled. Add current riders, fuel or "
    "supplier charges from the bill under Additional rider/adjustment per kWh."
)

PROFILES_LIST = [
    # North Carolina — Duke Energy Progress
    _profile("nc_dep_res", "nc_dep", "RES", "Residential Service — Standard Rate", "seasonal_tiered",
             _base(14, summer_rate=.12623, winter_first_rate=.12623,
                   winter_additional_rate=.11623, tier_kwh=800,
                   three_phase_charge=9), effective="2025-10-01", reference="Leaf 500"),
    _profile("nc_dep_r_toud", "nc_dep", "R-TOUD", "Residential Service Time-of-Use — Smart Usage Select Option",
             "tou_demand", _base(14, on_peak_rate=.15638, off_peak_rate=.06633,
                   discount_rate=.04347, on_peak_demand_rate=1.99,
                   max_demand_rate=3.91, three_phase_charge=9),
             scheme="carolinas", effective="2025-10-01", reference="Leaf 501"),
    _profile("nc_dep_r_tou", "nc_dep", "R-TOU", "Residential Service Time-of-Use — Smart Usage Option", "tou",
             _base(14, on_peak_rate=.29905, off_peak_rate=.11321,
                   discount_rate=.07372, three_phase_charge=9),
             scheme="carolinas", effective="2025-10-01", reference="Leaf 502"),
    _profile("nc_dep_r_tou_cpp", "nc_dep", "R-TOU-CPP", "Residential Time-of-Use CPP — Flex Savings Option",
             "tou_cpp", _base(14, critical_peak_rate=.41002, on_peak_rate=.21952,
                   off_peak_rate=.11000, discount_rate=.08274,
                   three_phase_charge=9), scheme="carolinas", effective="2025-10-01",
             reference="Leaf 503"),
    _profile("nc_dep_r_tou_ev", "nc_dep", "R-TOU-EV", "Residential Time-of-Use EV — EV Overnight Advantage",
             "two_period", _base(14, standard_rate=.13096, discount_rate=.06548,
                   three_phase_charge=9), scheme="ev_23_5", effective="2026-01-01",
             reference="Leaf 504"),

    # North Carolina — Duke Energy Carolinas
    _profile("nc_dec_rs", "nc_dec", "RS", "Residential Service — Standard Rate", "flat",
             _base(14, energy_rate=.122603), effective="2026-01-01"),
    _profile("nc_dec_re", "nc_dec", "RE", "Residential Service, Electric Water Heating and Space Conditioning",
             "seasonal_tiered", _base(14, summer_rate=.117845,
                   winter_first_rate=.117845, winter_additional_rate=.106061,
                   tier_kwh=800), effective="2026-01-01"),
    _profile("nc_dec_es_standard", "nc_dec", "ES", "Residential Service, Energy Star — standard column",
             "seasonal_tiered", _base(14, summer_rate=.116473,
                   winter_first_rate=.116473, winter_additional_rate=.116473,
                   tier_kwh=800), effective="2026-01-01"),
    _profile("nc_dec_es_all_electric", "nc_dec", "ES", "Residential Service, Energy Star — all-electric column",
             "seasonal_tiered", _base(14, summer_rate=.111953,
                   winter_first_rate=.111953, winter_additional_rate=.100758,
                   tier_kwh=800), effective="2026-01-01"),
    _profile("nc_dec_rt", "nc_dec", "RT", "Residential Time-of-Use — Smart Usage Select Option",
             "tou_demand", _base(14, on_peak_rate=.171204, off_peak_rate=.078411,
                   discount_rate=.053929, on_peak_demand_rate=2.34,
                   max_demand_rate=4.47), scheme="carolinas", effective="2026-01-01"),
    _profile("nc_dec_rstc", "nc_dec", "RSTC", "Residential Time-of-Use CPP — Flex Savings Option",
             "tou_cpp", _base(14, critical_peak_rate=.427695, on_peak_rate=.234984,
                   off_peak_rate=.102875, discount_rate=.074375),
             scheme="carolinas", effective="2026-01-01"),
    _profile("nc_dec_retc", "nc_dec", "RETC", "All-Electric Time-of-Use CPP — Flex Savings Option",
             "tou_cpp", _base(14, critical_peak_rate=.442601, on_peak_rate=.213412,
                   off_peak_rate=.097428, discount_rate=.070480),
             scheme="carolinas", effective="2026-01-01"),
    _profile("nc_dec_rt_ev", "nc_dec", "RT-EV", "Residential Time-of-Use EV — EV Overnight Advantage",
             "two_period", _base(14, standard_rate=.123504, discount_rate=.061752),
             scheme="ev_23_5", effective="2026-01-01"),

    # South Carolina — Duke Energy Carolinas
    _profile("sc_dec_rs", "sc_dec", "RS", "Residential Service — Standard Rate", "tiered_2",
             _base(11.96, tier_kwh=1000, winter_first_rate=.138125,
                   winter_additional_rate=.144661)),
    _profile("sc_dec_re", "sc_dec", "RE", "Residential Service, Electric Water Heating and Space Conditioning",
             "tiered_2", _base(11.96, tier_kwh=1000, winter_first_rate=.128547,
                   winter_additional_rate=.134604)),
    _profile("sc_dec_es_standard", "sc_dec", "ES", "Residential Service, Energy Star — standard column",
             "tiered_2", _base(11.96, tier_kwh=1000, winter_first_rate=.131589,
                   winter_additional_rate=.137798)),
    _profile("sc_dec_es_all_electric", "sc_dec", "ES", "Residential Service, Energy Star — all-electric column",
             "tiered_2", _base(11.96, tier_kwh=1000, winter_first_rate=.122490,
                   winter_additional_rate=.128244)),
    _profile("sc_dec_rt", "sc_dec", "RT", "Residential Time-of-Use — Smart Usage Select Option",
             "tou_demand", _base(13.09, on_peak_rate=.216118, off_peak_rate=.096597,
                   discount_rate=.059814, on_peak_demand_rate=2.02,
                   max_demand_rate=4.72), scheme="carolinas"),
    _profile("sc_dec_rstc", "sc_dec", "RSTC", "Residential Time-of-Use CPP — Flex Savings Option",
             "tou_cpp", _base(13.09, critical_peak_rate=.403705,
                   on_peak_rate=.264869, off_peak_rate=.131171,
                   discount_rate=.088409), scheme="carolinas"),
    _profile("sc_dec_retc", "sc_dec", "RETC", "All-Electric Time-of-Use CPP — Flex Savings Option",
             "tou_cpp", _base(13.09, critical_peak_rate=.392575,
                   on_peak_rate=.257296, off_peak_rate=.123157,
                   discount_rate=.080971), scheme="carolinas"),
    _profile("sc_dec_rt_ev", "sc_dec", "RT-EV", "Residential Time-of-Use Electric Vehicle",
             "two_period", _base(13.09, standard_rate=.149616,
                   discount_rate=.100753), scheme="ev_23_5"),
    _profile("sc_dec_r_stou", "sc_dec", "R-STOU", "Solar Choice Time-of-Use CPP",
             "solar_tou_cpp", _base(13.09, critical_peak_rate=.332758,
                   on_peak_rate=.209021, off_peak_rate=.128191,
                   super_off_peak_rate=.093782, non_bypassable_rate=.47,
                   grid_access_rate=5.86, system_size_kw=0, minimum_bill=30),
             scheme="solar_sc", warning="Export credits are not estimated; use net import statistics."),

    # South Carolina — Duke Energy Progress
    _profile("sc_dep_res", "sc_dep", "RES", "Residential Service — Standard Rate", "seasonal_tiered",
             _base(11.78, summer_rate=.14949, winter_first_rate=.14949,
                   winter_additional_rate=.13949, tier_kwh=800, three_phase_charge=9)),
    _profile("sc_dep_r_toud", "sc_dep", "R-TOUD", "Residential Time-of-Use with Demand",
             "tou_demand", _base(14.63, on_peak_rate=.20402, off_peak_rate=.09569,
                   discount_rate=.06768, on_peak_demand_rate=2.47,
                   max_demand_rate=4.85, three_phase_charge=9), scheme="carolinas"),
    _profile("sc_dep_r_stou", "sc_dep", "R-STOU", "Solar Choice Time-of-Use CPP",
             "solar_tou_cpp", _base(14.63, critical_peak_rate=.31865,
                   on_peak_rate=.21044, off_peak_rate=.13584,
                   super_off_peak_rate=.10588, non_bypassable_rate=.49,
                   grid_access_rate=4.29, system_size_kw=0, minimum_bill=30,
                   three_phase_charge=9), scheme="solar_sc",
             warning="Export credits are not estimated; use net import statistics."),
    _profile("sc_dep_r_tou_cpp", "sc_dep", "R-TOU-CPP", "Residential Time-of-Use CPP",
             "tou_cpp", _base(14.63, critical_peak_rate=.38147,
                   on_peak_rate=.29480, off_peak_rate=.13301,
                   discount_rate=.09272, three_phase_charge=9), scheme="carolinas"),
    _profile("sc_dep_r_tou_ev", "sc_dep", "R-TOU-EV", "Residential Time-of-Use EV",
             "two_period", _base(14.63, standard_rate=.15756,
                   discount_rate=.10244, three_phase_charge=9), scheme="ev_23_5"),

    # Ohio — distribution/base charges; riders are bill-specific.
    _profile("oh_deo_rs", "oh_deo", "RS", "Residential Service", "flat",
             _base(8, energy_rate=.039693), warning=_MISSING_RIDERS),
    _profile("oh_deo_orh", "oh_deo", "ORH", "Optional Residential Service",
             "oh_orh", _base(8, summer_rate=.039693, tier_kwh=1000,
                   winter_first_rate=.039298, winter_additional_rate=.021706,
                   tier_3_rate=.014632),
             warning=_MISSING_RIDERS + " The demand-dependent third block is estimated from hourly data."),
    _profile("oh_deo_td_cpp", "oh_deo", "TD-CPP", "Time-of-Day Critical Peak Pricing",
             "tou_cpp", _base(8, critical_peak_rate=.096514,
                   on_peak_rate=.057908, off_peak_rate=.038605,
                   discount_rate=.030884), scheme="oh_td_cpp", warning=_MISSING_RIDERS),
    _profile("oh_deo_td", "oh_deo", "TD", "Optional Time-of-Day Rate",
             "seasonal_tou", _base(17.50, summer_on_peak_rate=.079950,
                   summer_off_peak_rate=.013960, winter_on_peak_rate=.063519,
                   winter_off_peak_rate=.013976), scheme="oh_td", warning=_MISSING_RIDERS),
    _profile("oh_deo_rs3p", "oh_deo", "RS3P", "Residential Three-Phase Service",
             "flat", _base(10.50, energy_rate=.039693), warning=_MISSING_RIDERS),
    _profile("oh_deo_rsli", "oh_deo", "RSLI", "Residential Low Income Service",
             "flat", _base(2, energy_rate=.039693), warning=_MISSING_RIDERS),

    # Kentucky
    _profile("ky_dek_rs", "ky_dek", "RS", "Residential Service", "flat",
             _base(14.75, energy_rate=.128121), effective="2026-09-01",
             warning=_MISSING_RIDERS),

    # Indiana
    _profile("in_dei_rs", "in_dei", "RS", "Residential Service", "tiered_3",
             _base(13.70, tier_1_kwh=300, tier_1_rate=.186556,
                   tier_2_kwh=1000, tier_2_rate=.135777, tier_3_rate=.123051),
             warning=_MISSING_RIDERS),
    _profile("in_dei_rs_he", "in_dei", "RS", "High Efficiency Residential Service",
             "indiana_high_eff", _base(13.70, tier_1_kwh=300,
                   tier_1_rate=.208501, tier_2_kwh=1000, tier_2_rate=.151748,
                   summer_rate=.112521, winter_additional_rate=.109746),
             warning=_MISSING_RIDERS),
    _profile("in_dei_rs_tou", "in_dei", "RS-TOU", "Residential Time-of-Use — Smart Usage Option",
             "tou", _base(13.70, on_peak_rate=.214198, off_peak_rate=.142799,
                   discount_rate=.085679), scheme="indiana", warning=_MISSING_RIDERS),

    # Florida — base/non-fuel rates; bill riders remain configurable.
    _profile("fl_def_rs1", "fl_def", "RS-1", "Residential Service", "florida_tiered",
             _base(14.35, tier_kwh=1000, summer_rate=.07686,
                   winter_first_rate=.08754, winter_additional_rate=.10242,
                   tier_3_rate=.08453, minimum_bill=30), warning=_MISSING_RIDERS),
    _profile("fl_def_rst1", "fl_def", "RST-1", "Residential Time-of-Use",
             "tou", _base(14.35, on_peak_rate=.11090, off_peak_rate=.08215,
                   discount_rate=.04984, minimum_bill=30), scheme="florida",
             warning=_MISSING_RIDERS),
]

PROFILES = {item.profile_id: item for item in PROFILES_LIST}

def profiles_for_area(area: str) -> dict[str, str]:
    """Return bill-facing plan choices for a service area."""
    return {p.profile_id: p.label for p in PROFILES_LIST if p.service_area == area}


@dataclass(frozen=True, slots=True)
class CppEvent:
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
    cursor = (date(year + (month == 12), month % 12 + 1, 1) - timedelta(days=1))
    return cursor - timedelta(days=(cursor.weekday() - weekday) % 7)


def _observed(day: date) -> date:
    return day - timedelta(days=1) if day.weekday() == 5 else day + timedelta(days=1) if day.weekday() == 6 else day


def _easter(year: int) -> date:
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
    return date(year, month, (h + l - 7 * m + 114) % 31 + 1)


@lru_cache(maxsize=32)
def holidays(year: int) -> frozenset[date]:
    thanksgiving = _nth_weekday(year, 11, 3, 4)
    return frozenset({
        _observed(date(year, 1, 1)), _easter(year) - timedelta(days=2),
        _last_weekday(year, 5, 0), _observed(date(year, 7, 4)),
        _nth_weekday(year, 9, 0, 1), thanksgiving, thanksgiving + timedelta(days=1),
        _observed(date(year, 12, 25)),
    })


def is_tariff_holiday(day: date) -> bool:
    return any(day in holidays(year) for year in (day.year - 1, day.year, day.year + 1))


def tou_period(local: datetime, profile: TariffProfile, events: dict[date, CppEvent]) -> str:
    """Classify an hourly interval using the selected tariff's clock rules."""
    hour, day = local.hour, local.date()
    weekday = local.weekday() < 5 and not is_tariff_holiday(day)
    scheme = profile.period_scheme

    if scheme == "ev_23_5":
        return PERIOD_DISCOUNT if hour >= 23 or hour < 5 else PERIOD_STANDARD
    if scheme == "solar_sc":
        if 3 <= local.month <= 11 and hour < 6:
            return PERIOD_SUPER_OFF_PEAK
        peaks = ((18, 21),) if 3 <= local.month <= 11 else ((6, 9), (18, 21))
        if weekday and any(start <= hour < end for start, end in peaks):
            return PERIOD_CRITICAL_PEAK if day in events else PERIOD_ON_PEAK
        return PERIOD_OFF_PEAK
    if scheme == "oh_td_cpp":
        if hour < 5:
            return PERIOD_DISCOUNT
        if 5 <= local.month <= 9 and weekday and 14 <= hour < 20:
            return PERIOD_CRITICAL_PEAK if day in events else PERIOD_ON_PEAK
        if day in events:
            start = events[day].start_hour if events[day].start_hour is not None else 6
            if start <= hour < start + 6:
                return PERIOD_CRITICAL_PEAK
        return PERIOD_OFF_PEAK
    if scheme == "oh_td":
        summer = 6 <= local.month <= 9
        peak = 11 <= hour < 20 if summer else 9 <= hour < 14 or 17 <= hour < 21
        return PERIOD_ON_PEAK if weekday and peak else PERIOD_OFF_PEAK
    if scheme == "indiana":
        # Filed clock hours move one hour later while daylight saving time is active.
        shift = 1 if local.dst() and local.dst() != timedelta(0) else 0
        if hour < 4 + shift:
            return PERIOD_DISCOUNT
        winter = not bool(local.dst())
        peak = 17 + shift <= hour < 21 + shift or (winter and 6 + shift <= hour < 8 + shift)
        return PERIOD_ON_PEAK if weekday and peak else PERIOD_OFF_PEAK
    if scheme == "florida":
        if 3 <= local.month <= 11 and hour < 6 or local.month in (12, 1, 2) and hour < 3:
            return PERIOD_DISCOUNT
        peak = 18 <= hour < 21 or (local.month in (12, 1, 2) and 5 <= hour < 10)
        return PERIOD_ON_PEAK if weekday and peak else PERIOD_OFF_PEAK

    # Shared Carolinas TOU calendar.
    summer = 5 <= local.month <= 9
    if summer:
        if 1 <= hour < 6:
            return PERIOD_DISCOUNT
        start, end = 18, 21
    else:
        if 1 <= hour < 3 or 11 <= hour < 16:
            return PERIOD_DISCOUNT
        start, end = 6, 9
    if weekday and profile.model in {"tou_cpp", "solar_tou_cpp"} and day in events:
        event_start = events[day].start_hour if events[day].start_hour is not None else start
        if event_start <= hour < event_start + 3:
            return PERIOD_CRITICAL_PEAK
        if events[day].start_hour is not None and start <= hour < end:
            return PERIOD_OFF_PEAK
    return PERIOD_ON_PEAK if weekday and start <= hour < end else PERIOD_OFF_PEAK


RATE_KEYS = {
    PERIOD_STANDARD: CONF_STANDARD_RATE,
    PERIOD_ON_PEAK: CONF_ON_PEAK_RATE,
    PERIOD_OFF_PEAK: CONF_OFF_PEAK_RATE,
    PERIOD_DISCOUNT: CONF_DISCOUNT_RATE,
    PERIOD_SUPER_OFF_PEAK: CONF_SUPER_OFF_PEAK_RATE,
    PERIOD_CRITICAL_PEAK: CONF_CRITICAL_PEAK_RATE,
    PERIOD_SUMMER: CONF_SUMMER_RATE,
    PERIOD_WINTER_FIRST: CONF_WINTER_FIRST_RATE,
    PERIOD_WINTER_ADDITIONAL: CONF_WINTER_ADDITIONAL_RATE,
}


def rate_for_period(profile: TariffProfile, period: str, config: dict) -> float:
    """Return the configured energy price for a classified period."""
    return float(config[RATE_KEYS[period]])
