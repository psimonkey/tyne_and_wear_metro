"""Sensor platform for the Tyne and Wear Metro integration."""

from __future__ import annotations
from typing import TYPE_CHECKING, Any
from .const import DOMAIN, _LOGGER

from datetime import timedelta

from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import MetroDataUpdateCoordinator

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from .data import MetroConfigEntry

async def async_setup_entry(hass: HomeAssistant, entry: MetroConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([
        MetroPlatformSensor(
            coordinator=entry.runtime_data.coordinator,
        )]
    )


class MetroPlatformSensor(CoordinatorEntity, SensorEntity):

    coordinator: MetroDataUpdateCoordinator
    _attr_icon = "mdi:train-car-passenger-door"

    def __init__(self, coordinator: MetroDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = coordinator.config_entry.entry_id
        self._attr_device_info = DeviceInfo(
            identifiers={
                (
                    coordinator.config_entry.domain,
                    coordinator.config_entry.entry_id,
                ),
            },
        )
        self._attr_name = f"{coordinator.config_entry.data['station']} platform {coordinator.config_entry.data['platform']}"

    @property
    def state(self) -> str:
        return 'apologising'

    @property
    def extra_state_attributes(self):
        return self.coordinator.data