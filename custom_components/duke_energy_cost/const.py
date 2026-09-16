"""Constants for Duke Energy Cost."""

import re
from typing import Final

DOMAIN: Final = "duke_energy_cost"
PLATFORMS: Final = ["sensor"]

CONF_SOURCE_STATISTIC: Final = "source_statistic"
CONF_SCHEDULE: Final = "schedule"
CONF_NAME: Final = "name"
CONF_BILLING_CYCLE_DAY: Final = "billing_cycle_day"
CONF_CURRENCY: Final = "currency"
CONF_THREE_PHASE: Final = "three_phase"
CONF_BASIC_CHARGE: Final = "basic_charge"
CONF_THREE_PHASE_CHARGE: Final = "three_phase_charge"
CONF_ADDITIONAL_KWH_RATE: Final = "additional_kwh_rate"
CONF_MONTHLY_ADJUSTMENT: Final = "monthly_adjustment"
CONF_TAX_PERCENT: Final = "tax_percent"
CONF_CPP_EVENTS: Final = "cpp_events"
CONF_DEMAND_MODE: Final = "demand_mode"
CONF_MANUAL_ON_PEAK_KW: Final = "manual_on_peak_kw"
CONF_MANUAL_MAX_KW: Final = "manual_max_kw"

CONF_SUMMER_RATE: Final = "summer_rate"
CONF_WINTER_FIRST_RATE: Final = "winter_first_rate"
CONF_WINTER_ADDITIONAL_RATE: Final = "winter_additional_rate"
CONF_TIER_KWH: Final = "tier_kwh"
CONF_ON_PEAK_RATE: Final = "on_peak_rate"
CONF_OFF_PEAK_RATE: Final = "off_peak_rate"
CONF_DISCOUNT_RATE: Final = "discount_rate"
CONF_CRITICAL_PEAK_RATE: Final = "critical_peak_rate"
CONF_STANDARD_RATE: Final = "standard_rate"
CONF_ON_PEAK_DEMAND_RATE: Final = "on_peak_demand_rate"
CONF_MAX_DEMAND_RATE: Final = "max_demand_rate"

SCHEDULE_RES: Final = "res"
SCHEDULE_R_TOUD: Final = "r_toud"
SCHEDULE_R_TOU: Final = "r_tou"
SCHEDULE_R_TOU_CPP: Final = "r_tou_cpp"
SCHEDULE_R_TOU_EV: Final = "r_tou_ev"
SCHEDULES: Final = (
    SCHEDULE_RES,
    SCHEDULE_R_TOUD,
    SCHEDULE_R_TOU,
    SCHEDULE_R_TOU_CPP,
    SCHEDULE_R_TOU_EV,
)

DEMAND_MODE_HOURLY: Final = "hourly_estimate"
DEMAND_MODE_MANUAL: Final = "manual"
DEMAND_MODE_NONE: Final = "none"

DEFAULT_SCAN_INTERVAL_HOURS: Final = 12
DEFAULT_HISTORY_DAYS: Final = 3 * 366
TIME_ZONE: Final = "America/New_York"


def cost_statistic_ids(source_statistic: str) -> tuple[str, str]:
    """Return the two external statistic IDs owned for a source statistic."""
    suffix = re.sub(
        r"[^a-z0-9_]+", "_", source_statistic.lower().replace(":", "_")
    ).strip("_")[:120]
    return (
        f"{DOMAIN}:{suffix}_energy_cost",
        f"{DOMAIN}:{suffix}_estimated_total_cost",
    )
