"""Config flow for Duke Energy Cost."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components.recorder.statistics import async_list_statistic_ids
from homeassistant.core import callback

from .const import (
    CONF_ADDITIONAL_KWH_RATE,
    CONF_BASIC_CHARGE,
    CONF_BILLING_CYCLE_DAY,
    CONF_CPP_EVENTS,
    CONF_CRITICAL_PEAK_RATE,
    CONF_CURRENCY,
    CONF_DEMAND_MODE,
    CONF_DISCOUNT_RATE,
    CONF_MANUAL_MAX_KW,
    CONF_MANUAL_ON_PEAK_KW,
    CONF_MAX_DEMAND_RATE,
    CONF_MONTHLY_ADJUSTMENT,
    CONF_NAME,
    CONF_OFF_PEAK_RATE,
    CONF_ON_PEAK_DEMAND_RATE,
    CONF_ON_PEAK_RATE,
    CONF_SCHEDULE,
    CONF_SOURCE_STATISTIC,
    CONF_STANDARD_RATE,
    CONF_SUMMER_RATE,
    CONF_TAX_PERCENT,
    CONF_THREE_PHASE,
    CONF_THREE_PHASE_CHARGE,
    CONF_TIER_KWH,
    CONF_WINTER_ADDITIONAL_RATE,
    CONF_WINTER_FIRST_RATE,
    DEMAND_MODE_HOURLY,
    DEMAND_MODE_MANUAL,
    DEMAND_MODE_NONE,
    DOMAIN,
    SCHEDULE_RES,
    SCHEDULE_R_TOU,
    SCHEDULE_R_TOU_CPP,
    SCHEDULE_R_TOU_EV,
    SCHEDULE_R_TOUD,
)
from .tariffs import DEFAULTS, SCHEDULE_NAMES, parse_cpp_events


def _number(*, minimum: float = 0, maximum: float | None = None):
    """Return a basic numeric validator compatible with older HA frontends."""
    return vol.All(vol.Coerce(float), vol.Range(min=minimum, max=maximum))


def _base_schema(
    defaults: dict[str, Any],
    *,
    include_source: bool,
    source_options: dict[str, str] | None = None,
) -> vol.Schema:
    fields: dict[Any, Any] = {}
    if include_source:
        fields[vol.Required(CONF_SOURCE_STATISTIC)] = (
            vol.In(source_options) if source_options else str
        )
        fields[
            vol.Required(
                CONF_NAME, default=defaults.get(CONF_NAME, "Duke Energy Cost")
            )
        ] = str
    fields[
        vol.Required(
            CONF_SCHEDULE,
            default=defaults.get(CONF_SCHEDULE, SCHEDULE_R_TOU_CPP),
        )
    ] = vol.In(SCHEDULE_NAMES)
    fields[
        vol.Required(
            CONF_BILLING_CYCLE_DAY,
            default=defaults.get(CONF_BILLING_CYCLE_DAY, 1),
        )
    ] = vol.All(vol.Coerce(int), vol.Range(min=1, max=28))
    fields[
        vol.Required(CONF_CURRENCY, default=defaults.get(CONF_CURRENCY, "USD"))
    ] = str
    fields[
        vol.Required(
            CONF_THREE_PHASE, default=defaults.get(CONF_THREE_PHASE, False)
        )
    ] = bool
    return vol.Schema(fields)


def _rates_schema(schedule: str, current: dict[str, Any]) -> vol.Schema:
    defaults = {**DEFAULTS[schedule], **current}
    fields: dict[Any, Any] = {
        vol.Required(CONF_BASIC_CHARGE, default=defaults[CONF_BASIC_CHARGE]): _number(),
        vol.Required(CONF_THREE_PHASE_CHARGE, default=defaults[CONF_THREE_PHASE_CHARGE]): _number(),
    }
    if schedule == SCHEDULE_RES:
        fields.update(
            {
                vol.Required(CONF_SUMMER_RATE, default=defaults[CONF_SUMMER_RATE]): _number(),
                vol.Required(CONF_WINTER_FIRST_RATE, default=defaults[CONF_WINTER_FIRST_RATE]): _number(),
                vol.Required(CONF_WINTER_ADDITIONAL_RATE, default=defaults[CONF_WINTER_ADDITIONAL_RATE]): _number(),
                vol.Required(CONF_TIER_KWH, default=defaults[CONF_TIER_KWH]): _number(),
            }
        )
    elif schedule == SCHEDULE_R_TOUD:
        fields.update(
            {
                vol.Required(CONF_ON_PEAK_RATE, default=defaults[CONF_ON_PEAK_RATE]): _number(),
                vol.Required(CONF_OFF_PEAK_RATE, default=defaults[CONF_OFF_PEAK_RATE]): _number(),
                vol.Required(CONF_DISCOUNT_RATE, default=defaults[CONF_DISCOUNT_RATE]): _number(),
                vol.Required(CONF_ON_PEAK_DEMAND_RATE, default=defaults[CONF_ON_PEAK_DEMAND_RATE]): _number(),
                vol.Required(CONF_MAX_DEMAND_RATE, default=defaults[CONF_MAX_DEMAND_RATE]): _number(),
                vol.Required(CONF_DEMAND_MODE, default=defaults.get(CONF_DEMAND_MODE, DEMAND_MODE_HOURLY)): vol.In(
                    {
                        DEMAND_MODE_HOURLY: "Hourly-average estimate",
                        DEMAND_MODE_MANUAL: "Manual monthly kW",
                        DEMAND_MODE_NONE: "Exclude demand charges",
                    }
                ),
                vol.Required(CONF_MANUAL_ON_PEAK_KW, default=defaults.get(CONF_MANUAL_ON_PEAK_KW, 0.0)): _number(),
                vol.Required(CONF_MANUAL_MAX_KW, default=defaults.get(CONF_MANUAL_MAX_KW, 0.0)): _number(),
            }
        )
    elif schedule in (SCHEDULE_R_TOU, SCHEDULE_R_TOU_CPP):
        if schedule == SCHEDULE_R_TOU_CPP:
            fields[vol.Required(CONF_CRITICAL_PEAK_RATE, default=defaults[CONF_CRITICAL_PEAK_RATE])] = _number()
        fields.update(
            {
                vol.Required(CONF_ON_PEAK_RATE, default=defaults[CONF_ON_PEAK_RATE]): _number(),
                vol.Required(CONF_OFF_PEAK_RATE, default=defaults[CONF_OFF_PEAK_RATE]): _number(),
                vol.Required(CONF_DISCOUNT_RATE, default=defaults[CONF_DISCOUNT_RATE]): _number(),
            }
        )
        if schedule == SCHEDULE_R_TOU_CPP:
            fields[vol.Optional(CONF_CPP_EVENTS, default=defaults.get(CONF_CPP_EVENTS, ""))] = str
    elif schedule == SCHEDULE_R_TOU_EV:
        fields.update(
            {
                vol.Required(CONF_STANDARD_RATE, default=defaults[CONF_STANDARD_RATE]): _number(),
                vol.Required(CONF_DISCOUNT_RATE, default=defaults[CONF_DISCOUNT_RATE]): _number(),
            }
        )
    fields.update(
        {
            vol.Required(CONF_ADDITIONAL_KWH_RATE, default=defaults.get(CONF_ADDITIONAL_KWH_RATE, 0.0)): _number(),
            vol.Required(CONF_MONTHLY_ADJUSTMENT, default=defaults.get(CONF_MONTHLY_ADJUSTMENT, 0.0)): _number(minimum=-1000),
            vol.Required(CONF_TAX_PERCENT, default=defaults.get(CONF_TAX_PERCENT, 0.0)): _number(maximum=100),
        }
    )
    return vol.Schema(fields)


class DukeEnergyNCRatesConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle setup in the UI."""

    VERSION = 1

    def __init__(self) -> None:
        self._pending: dict[str, Any] = {}

    async def _async_energy_statistic_options(self) -> dict[str, str]:
        """Return kWh sum statistics as a basic select mapping."""
        metadata = await async_list_statistic_ids(self.hass, None, "sum")
        candidates = [
            item
            for item in metadata
            if item.get("statistics_unit_of_measurement") == "kWh"
        ]
        candidates.sort(key=lambda item: str(item.get("statistic_id", "")))
        return {
            str(item["statistic_id"]): (
                f"{item.get('name') or item['statistic_id']} — {item['statistic_id']}"
            )
            for item in candidates
        }

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            statistic_id = user_input[CONF_SOURCE_STATISTIC]
            metadata = await async_list_statistic_ids(
                self.hass, {statistic_id}, "sum"
            )
            if not metadata:
                errors[CONF_SOURCE_STATISTIC] = "invalid_energy_statistic"
            else:
                unit = metadata[0].get("statistics_unit_of_measurement")
                unit_class = metadata[0].get("unit_class")
                if unit_class != "energy" or unit != "kWh":
                    errors[CONF_SOURCE_STATISTIC] = "invalid_energy_statistic"
            if not errors:
                await self.async_set_unique_id(statistic_id)
                self._abort_if_unique_id_configured()
                self._pending = dict(user_input)
                return await self.async_step_rates()
        # Currency is an Energy dashboard preference, not a stable attribute of
        # HomeAssistant.config across supported releases. Duke Energy Carolinas
        # bills in USD, so use the tariff currency as the portable default.
        defaults = {CONF_CURRENCY: "USD"}
        source_options = await self._async_energy_statistic_options()
        return self.async_show_form(
            step_id="user",
            data_schema=_base_schema(
                defaults,
                include_source=True,
                source_options=source_options,
            ),
            errors=errors,
            description_placeholders={"version": "0.2.0"},
        )

    async def async_step_rates(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                parse_cpp_events(str(user_input.get(CONF_CPP_EVENTS, "")))
            except (TypeError, ValueError):
                errors[CONF_CPP_EVENTS] = "invalid_cpp_events"
            if not errors:
                data = {**self._pending, **user_input}
                return self.async_create_entry(title=data[CONF_NAME], data=data)
        schedule = self._pending[CONF_SCHEDULE]
        return self.async_show_form(
            step_id="rates",
            data_schema=_rates_schema(schedule, {}),
            errors=errors,
            description_placeholders={"schedule": SCHEDULE_NAMES[schedule]},
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return DukeEnergyNCRatesOptionsFlow(config_entry)


class DukeEnergyNCRatesOptionsFlow(config_entries.OptionsFlow):
    """Edit schedule and all calculation inputs."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._entry = config_entry
        self._current = {**config_entry.data, **config_entry.options}
        self._pending: dict[str, Any] = {}

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            self._pending = dict(user_input)
            return await self.async_step_rates()
        return self.async_show_form(
            step_id="init",
            data_schema=_base_schema(self._current, include_source=False),
        )

    async def async_step_rates(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                parse_cpp_events(str(user_input.get(CONF_CPP_EVENTS, "")))
            except (TypeError, ValueError):
                errors[CONF_CPP_EVENTS] = "invalid_cpp_events"
            if not errors:
                return self.async_create_entry(title="", data={**self._pending, **user_input})
        schedule = self._pending[CONF_SCHEDULE]
        return self.async_show_form(
            step_id="rates",
            data_schema=_rates_schema(
                schedule,
                self._current if schedule == self._current[CONF_SCHEDULE] else {},
            ),
            errors=errors,
            description_placeholders={"schedule": SCHEDULE_NAMES[schedule]},
        )
