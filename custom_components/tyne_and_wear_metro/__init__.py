"""The Tyne and Wear Metro integration."""

from __future__ import annotations
from typing import TYPE_CHECKING, Any
from .const import DOMAIN, _LOGGER

from datetime import timedelta

from homeassistant.const import Platform
from homeassistant.loader import async_get_loaded_integration

from .coordinator import MetroDataUpdateCoordinator
from .data import MetroData

from .metro import MetroNetwork

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from .data import MetroConfigEntry

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: MetroConfigEntry) -> bool:
    """Set up Tyne and Wear Metro from a config entry."""
    coordinator = MetroDataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_interval=timedelta(seconds=45),
    )
    api = MetroNetwork()
    await api.hydrate()
    entry.runtime_data = MetroData(
        api=api,
        coordinator=coordinator,
    )
    await coordinator.async_config_entry_first_refresh()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: MetroConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(hass: HomeAssistant, entry: MetroConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)