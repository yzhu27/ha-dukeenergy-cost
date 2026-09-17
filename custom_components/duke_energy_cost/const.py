"""Constants for Duke Energy Cost."""

import re
from typing import Final

DOMAIN: Final = "duke_energy_cost"
PLATFORMS: Final = ["sensor"]

CONF_SOURCE_STATISTIC: Final = "source_statistic"
CONF_NAME: Final = "name"
CONF_STATE: Final = "state"
CONF_SERVICE_AREA: Final = "service_area"
CONF_TARIFF_PROFILE: Final = "tariff_profile"
CONF_BILLING_CYCLE_DAY: Final = "billing_cycle_day"
CONF_CURRENCY: Final = "currency"
CONF_THREE_PHASE: Final = "three_phase"

CONF_BASIC_CHARGE: Final = "basic_charge"
CONF_THREE_PHASE_CHARGE: Final = "three_phase_charge"
CONF_ADDITIONAL_KWH_RATE: Final = "additional_kwh_rate"
CONF_MONTHLY_ADJUSTMENT: Final = "monthly_adjustment"
CONF_TAX_PERCENT: Final = "tax_percent"
CONF_MINIMUM_BILL: Final = "minimum_bill"
CONF_CPP_EVENTS: Final = "cpp_events"
CONF_DEMAND_MODE: Final = "demand_mode"
CONF_MANUAL_ON_PEAK_KW: Final = "manual_on_peak_kw"
CONF_MANUAL_MAX_KW: Final = "manual_max_kw"

CONF_ENERGY_RATE: Final = "energy_rate"
CONF_SUMMER_RATE: Final = "summer_rate"
CONF_WINTER_FIRST_RATE: Final = "winter_first_rate"
CONF_WINTER_ADDITIONAL_RATE: Final = "winter_additional_rate"
CONF_TIER_KWH: Final = "tier_kwh"
CONF_TIER_1_KWH: Final = "tier_1_kwh"
CONF_TIER_1_RATE: Final = "tier_1_rate"
CONF_TIER_2_KWH: Final = "tier_2_kwh"
CONF_TIER_2_RATE: Final = "tier_2_rate"
CONF_TIER_3_RATE: Final = "tier_3_rate"
CONF_ON_PEAK_RATE: Final = "on_peak_rate"
CONF_OFF_PEAK_RATE: Final = "off_peak_rate"
CONF_DISCOUNT_RATE: Final = "discount_rate"
CONF_SUPER_OFF_PEAK_RATE: Final = "super_off_peak_rate"
CONF_CRITICAL_PEAK_RATE: Final = "critical_peak_rate"
CONF_STANDARD_RATE: Final = "standard_rate"
CONF_SUMMER_ON_PEAK_RATE: Final = "summer_on_peak_rate"
CONF_SUMMER_OFF_PEAK_RATE: Final = "summer_off_peak_rate"
CONF_WINTER_ON_PEAK_RATE: Final = "winter_on_peak_rate"
CONF_WINTER_OFF_PEAK_RATE: Final = "winter_off_peak_rate"
CONF_ON_PEAK_DEMAND_RATE: Final = "on_peak_demand_rate"
CONF_MAX_DEMAND_RATE: Final = "max_demand_rate"
CONF_SYSTEM_SIZE_KW: Final = "system_size_kw"
CONF_NON_BYPASSABLE_RATE: Final = "non_bypassable_rate"
CONF_GRID_ACCESS_RATE: Final = "grid_access_rate"

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
