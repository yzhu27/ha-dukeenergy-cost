"""Sensor entities for Duke Energy Cost."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .calculator import LOCAL_TZ, billing_cycle_key, current_period_rate
from .const import (
    CONF_BILLING_CYCLE_DAY,
    CONF_CURRENCY,
    CONF_NAME,
    CONF_TARIFF_PROFILE,
    DOMAIN,
)
from .coordinator import DukeEnergyCostCoordinator, DukeEnergyCostData
from .tariffs import PROFILES


@dataclass(frozen=True, kw_only=True)
class DukeEnergyCostSensorDescription(SensorEntityDescription):
    """Describe a calculated sensor."""

    value_fn: Callable[[DukeEnergyCostData], Any]


SENSORS = (
    DukeEnergyCostSensorDescription(
        key="current_rate",
        translation_key="current_rate",
        icon="mdi:currency-usd",
        suggested_display_precision=5,
        value_fn=lambda data: data.current_rate,
    ),
    DukeEnergyCostSensorDescription(
        key="current_period",
        translation_key="current_period",
        icon="mdi:clock-outline",
        value_fn=lambda data: data.current_period,
    ),
    DukeEnergyCostSensorDescription(
        key="cycle_energy",
        translation_key="cycle_energy",
        icon="mdi:lightning-bolt",
        suggested_display_precision=2,
        value_fn=lambda data: data.cycle_kwh,
    ),
    DukeEnergyCostSensorDescription(
        key="cycle_energy_cost",
        translation_key="cycle_energy_cost",
        icon="mdi:cash",
        suggested_display_precision=2,
        value_fn=lambda data: data.cycle_energy_cost,
    ),
    DukeEnergyCostSensorDescription(
        key="cycle_total_cost",
        translation_key="cycle_total_cost",
        icon="mdi:cash-multiple",
        suggested_display_precision=2,
        value_fn=lambda data: data.cycle_total_cost,
    ),
    DukeEnergyCostSensorDescription(
        key="on_peak_demand",
        translation_key="on_peak_demand",
        icon="mdi:gauge",
        entity_registry_enabled_default=False,
        value_fn=lambda data: data.on_peak_demand_kw,
    ),
    DukeEnergyCostSensorDescription(
        key="maximum_demand",
        translation_key="maximum_demand",
        icon="mdi:gauge-full",
        entity_registry_enabled_default=False,
        value_fn=lambda data: data.max_demand_kw,
    ),
    DukeEnergyCostSensorDescription(
        key="last_usage",
        translation_key="last_usage",
        icon="mdi:calendar-clock",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.last_usage_start,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up calculated sensors."""
    coordinator: DukeEnergyCostCoordinator = entry.runtime_data
    async_add_entities(DukeEnergyCostSensor(coordinator, entry, description) for description in SENSORS)


class DukeEnergyCostSensor(CoordinatorEntity[DukeEnergyCostCoordinator], SensorEntity):
    """A Duke rate calculation sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DukeEnergyCostCoordinator,
        entry: ConfigEntry,
        description: DukeEnergyCostSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=str(coordinator.config[CONF_NAME]),
            manufacturer="Duke Energy",
            model=PROFILES[str(coordinator.config[CONF_TARIFF_PROFILE])].label,
        )
        if description.key in {"current_rate"}:
            self._attr_native_unit_of_measurement = (
                f"{str(coordinator.config[CONF_CURRENCY]).upper()}/kWh"
            )
        elif description.key == "cycle_energy":
            self._attr_native_unit_of_measurement = "kWh"
        elif description.key in {"cycle_energy_cost", "cycle_total_cost"}:
            self._attr_native_unit_of_measurement = str(
                coordinator.config[CONF_CURRENCY]
            ).upper()
        elif description.key in {"on_peak_demand", "maximum_demand"}:
            self._attr_native_unit_of_measurement = "kW"

    async def async_added_to_hass(self) -> None:
        """Refresh wall-clock tariff sensors at each rate boundary."""
        await super().async_added_to_hass()
        if self.entity_description.key in {"current_rate", "current_period"}:
            self.async_on_remove(
                async_track_time_change(
                    self.hass,
                    self._handle_time_change,
                    minute=0,
                    second=0,
                )
            )

    @callback
    def _handle_time_change(self, _now) -> None:
        """Write the current tariff state without recalculating usage history."""
        self.async_write_ha_state()

    def _current_period_rate(self) -> tuple[str, float]:
        """Calculate the current marginal rate from the wall clock."""
        now = dt_util.utcnow()
        data = self.coordinator.data
        config = self.coordinator.config
        current_cycle = billing_cycle_key(
            now.astimezone(LOCAL_TZ),
            int(config[CONF_BILLING_CYCLE_DAY]),
        )
        same_cycle = current_cycle == data.cycle_key
        return current_period_rate(
            now,
            str(config[CONF_TARIFF_PROFILE]),
            config,
            data.cycle_kwh if same_cycle else 0.0,
            data.max_demand_kw if same_cycle else 0.0,
        )

    @property
    def native_value(self) -> Any:
        """Return the latest value."""
        if self.entity_description.key == "current_rate":
            return self._current_period_rate()[1]
        if self.entity_description.key == "current_period":
            return self._current_period_rate()[0]
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Expose calculation provenance on the primary total sensor."""
        if self.entity_description.key != "cycle_total_cost":
            return None
        data = self.coordinator.data
        return {
            "billing_cycle": data.cycle_key,
            "source_statistic": self.coordinator.config["source_statistic"],
            "energy_cost_statistic": data.energy_cost_statistic_id,
            "estimated_total_cost_statistic": data.total_cost_statistic_id,
            "aggregate_data_estimated": data.aggregate_data_estimated,
            "source_points": data.source_points,
            "derived_points": data.derived_points,
            "last_calculated": data.last_update.isoformat(),
        }
