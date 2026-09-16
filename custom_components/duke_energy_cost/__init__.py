"""Duke Energy Cost integration."""

from __future__ import annotations

import asyncio
import logging

from homeassistant.components.recorder import get_instance
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_SOURCE_STATISTIC, DOMAIN, PLATFORMS, cost_statistic_ids
from .coordinator import DukeEnergyCostCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a rate calculator config entry."""
    coordinator = DukeEnergyCostCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload after options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Remove all external statistics owned by a deleted config entry."""
    statistic_ids = list(cost_statistic_ids(entry.data[CONF_SOURCE_STATISTIC]))
    done = asyncio.Event()

    def _on_done() -> None:
        hass.loop.call_soon_threadsafe(done.set)

    get_instance(hass).async_clear_statistics(statistic_ids, on_done=_on_done)
    try:
        await asyncio.wait_for(done.wait(), timeout=10)
    except TimeoutError:
        _LOGGER.warning(
            "Timed out while removing external statistics: %s", statistic_ids
        )
