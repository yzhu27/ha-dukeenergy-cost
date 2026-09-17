"""Config flow for Duke Energy Cost."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components.recorder.statistics import async_list_statistic_ids
from homeassistant.core import callback

from .const import *  # noqa: F403 - schemas use the configuration keys directly
from .tariffs import PROFILES, SERVICE_AREAS, STATE_NAMES, profiles_for_area, parse_cpp_events


def _number(*, minimum: float = 0, maximum: float | None = None):
    return vol.All(vol.Coerce(float), vol.Range(min=minimum, max=maximum))


def _general_schema(defaults: dict[str, Any], *, source_options: dict[str, str] | None = None) -> vol.Schema:
    fields: dict[Any, Any] = {}
    if source_options is not None:
        fields[vol.Required(CONF_SOURCE_STATISTIC)] = vol.In(source_options)  # noqa: F405
    fields[vol.Required(CONF_NAME, default=defaults.get(CONF_NAME, "Duke Energy Cost"))] = str  # noqa: F405
    fields[vol.Required(CONF_BILLING_CYCLE_DAY, default=defaults.get(CONF_BILLING_CYCLE_DAY, 1))] = vol.All(vol.Coerce(int), vol.Range(min=1, max=28))  # noqa: F405
    fields[vol.Required(CONF_CURRENCY, default=defaults.get(CONF_CURRENCY, "USD"))] = str  # noqa: F405
    return vol.Schema(fields)


def _state_schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema({vol.Required(CONF_STATE, default=defaults.get(CONF_STATE, "NC")): vol.In(STATE_NAMES)})  # noqa: F405


def _service_area_schema(state: str, defaults: dict[str, Any]) -> vol.Schema:
    choices = {key: name for key, (area_state, name) in SERVICE_AREAS.items() if area_state == state}
    default = defaults.get(CONF_SERVICE_AREA)
    if default not in choices:
        default = next(iter(choices))
    return vol.Schema({vol.Required(CONF_SERVICE_AREA, default=default): vol.In(choices)})  # noqa: F405


def _plan_schema(area: str, defaults: dict[str, Any]) -> vol.Schema:
    choices = profiles_for_area(area)
    default = defaults.get(CONF_TARIFF_PROFILE)
    if default not in choices:
        default = next(iter(choices))
    return vol.Schema({vol.Required(CONF_TARIFF_PROFILE, default=default): vol.In(choices)})  # noqa: F405


def _rates_schema(profile_id: str, current: dict[str, Any]) -> vol.Schema:
    profile = PROFILES[profile_id]
    defaults = {**(profile.defaults or {}), **current}
    fields: dict[Any, Any] = {}
    for key, published in (profile.defaults or {}).items():
        fields[vol.Required(key, default=defaults.get(key, published))] = _number()

    if CONF_THREE_PHASE_CHARGE in (profile.defaults or {}):  # noqa: F405
        fields[vol.Required(CONF_THREE_PHASE, default=defaults.get(CONF_THREE_PHASE, False))] = bool  # noqa: F405
    if profile.model == "tou_demand":
        fields[vol.Required(CONF_DEMAND_MODE, default=defaults.get(CONF_DEMAND_MODE, DEMAND_MODE_HOURLY))] = vol.In({  # noqa: F405
            DEMAND_MODE_HOURLY: "Estimate from hourly-average kW",  # noqa: F405
            DEMAND_MODE_MANUAL: "Use monthly kW values from the bill",  # noqa: F405
            DEMAND_MODE_NONE: "Exclude demand charges",  # noqa: F405
        })
        fields[vol.Required(CONF_MANUAL_ON_PEAK_KW, default=defaults.get(CONF_MANUAL_ON_PEAK_KW, 0.0))] = _number()  # noqa: F405
        fields[vol.Required(CONF_MANUAL_MAX_KW, default=defaults.get(CONF_MANUAL_MAX_KW, 0.0))] = _number()  # noqa: F405
    if profile.model in {"tou_cpp", "solar_tou_cpp"}:
        fields[vol.Optional(CONF_CPP_EVENTS, default=defaults.get(CONF_CPP_EVENTS, ""))] = str  # noqa: F405

    fields[vol.Required(CONF_ADDITIONAL_KWH_RATE, default=defaults.get(CONF_ADDITIONAL_KWH_RATE, 0.0))] = _number(minimum=-10)  # noqa: F405
    fields[vol.Required(CONF_MONTHLY_ADJUSTMENT, default=defaults.get(CONF_MONTHLY_ADJUSTMENT, 0.0))] = _number(minimum=-1000)  # noqa: F405
    fields[vol.Required(CONF_TAX_PERCENT, default=defaults.get(CONF_TAX_PERCENT, 0.0))] = _number(maximum=100)  # noqa: F405
    return vol.Schema(fields)


class _TariffSteps:
    """Shared state, service-area, plan and rate steps."""

    _pending: dict[str, Any]
    _current: dict[str, Any]

    async def async_step_state(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            self._pending.update(user_input)
            areas = [key for key, (state, _) in SERVICE_AREAS.items() if state == user_input[CONF_STATE]]  # noqa: F405
            if len(areas) == 1:
                self._pending[CONF_SERVICE_AREA] = areas[0]  # noqa: F405
                return await self.async_step_plan()
            return await self.async_step_service_area()
        return self.async_show_form(step_id="state", data_schema=_state_schema({**self._current, **self._pending}))

    async def async_step_service_area(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            self._pending.update(user_input)
            return await self.async_step_plan()
        state = self._pending[CONF_STATE]  # noqa: F405
        return self.async_show_form(
            step_id="service_area",
            data_schema=_service_area_schema(state, {**self._current, **self._pending}),
            description_placeholders={"state": STATE_NAMES[state]},
        )

    async def async_step_plan(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            self._pending.update(user_input)
            return await self.async_step_rates()
        area = self._pending[CONF_SERVICE_AREA]  # noqa: F405
        return self.async_show_form(
            step_id="plan",
            data_schema=_plan_schema(area, {**self._current, **self._pending}),
            description_placeholders={"service_area": SERVICE_AREAS[area][1]},
        )

    async def async_step_rates(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                parse_cpp_events(str(user_input.get(CONF_CPP_EVENTS, "")))  # noqa: F405
            except (TypeError, ValueError):
                errors[CONF_CPP_EVENTS] = "invalid_cpp_events"  # noqa: F405
            if not errors:
                return await self._async_finish({**self._pending, **user_input})
        profile_id = self._pending[CONF_TARIFF_PROFILE]  # noqa: F405
        profile = PROFILES[profile_id]
        same_profile = profile_id == self._current.get(CONF_TARIFF_PROFILE)  # noqa: F405
        current = self._current if same_profile else {}
        details = "; ".join(part for part in (profile.reference, profile.effective, profile.warning) if part)
        return self.async_show_form(
            step_id="rates",
            data_schema=_rates_schema(profile_id, current),
            errors=errors,
            description_placeholders={"plan": profile.label, "details": details or "Published tariff defaults are prefilled."},
        )


class DukeEnergyCostConfigFlow(_TariffSteps, config_entries.ConfigFlow, domain=DOMAIN):  # noqa: F405
    """Handle setup in the UI."""

    VERSION = 1

    def __init__(self) -> None:
        self._pending: dict[str, Any] = {}
        self._current: dict[str, Any] = {}

    async def _async_energy_statistic_options(self) -> dict[str, str]:
        metadata = await async_list_statistic_ids(self.hass, None, "sum")
        candidates = [item for item in metadata if item.get("statistics_unit_of_measurement") == "kWh"]
        candidates.sort(key=lambda item: str(item.get("statistic_id", "")))
        return {str(item["statistic_id"]): f"{item.get('name') or item['statistic_id']} — {item['statistic_id']}" for item in candidates}

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        options = await self._async_energy_statistic_options()
        if user_input is not None:
            statistic_id = user_input[CONF_SOURCE_STATISTIC]  # noqa: F405
            metadata = await async_list_statistic_ids(self.hass, {statistic_id}, "sum")
            if not metadata or metadata[0].get("unit_class") != "energy" or metadata[0].get("statistics_unit_of_measurement") != "kWh":
                errors[CONF_SOURCE_STATISTIC] = "invalid_energy_statistic"  # noqa: F405
            if not errors:
                await self.async_set_unique_id(statistic_id)
                self._abort_if_unique_id_configured()
                self._pending = dict(user_input)
                return await self.async_step_state()
        return self.async_show_form(
            step_id="user", data_schema=_general_schema({}, source_options=options),
            errors=errors, description_placeholders={"version": "0.3.1"},
        )

    async def _async_finish(self, data: dict[str, Any]):
        return self.async_create_entry(title=data[CONF_NAME], data=data)  # noqa: F405

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return DukeEnergyCostOptionsFlow(config_entry)


class DukeEnergyCostOptionsFlow(_TariffSteps, config_entries.OptionsFlow):
    """Edit the service area, plan, and all calculation inputs."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._entry = config_entry
        self._current = {**config_entry.data, **config_entry.options}
        self._pending: dict[str, Any] = {}

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            self._pending.update(user_input)
            return await self.async_step_state()
        return self.async_show_form(step_id="init", data_schema=_general_schema(self._current))

    async def _async_finish(self, data: dict[str, Any]):
        return self.async_create_entry(title="", data=data)
