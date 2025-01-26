"""The Tyne and Wear Metro integration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.const import Platform

from .const import DOMAIN
from .coordinator import MetroDataUpdateCoordinator
from .data import MetroData
from .metro import MetroNetwork

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import MetroConfigEntry

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: MetroConfigEntry) -> bool:
    """Set up Tyne and Wear Metro from a config entry."""
    api = MetroNetwork()
    await api.hydrate()
    coordinator = MetroDataUpdateCoordinator(
        hass,
        name=DOMAIN,
        api=api,
        config_entry=entry,
    )
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
