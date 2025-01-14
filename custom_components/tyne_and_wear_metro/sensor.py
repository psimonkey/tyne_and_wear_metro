"""Sensor platform for Tyne and Wear Metro."""

from __future__ import annotations
import logging
from typing import TYPE_CHECKING
from datetime import timedelta

_LOGGER = logging.getLogger(__name__)

from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import TyneAndWearMetroPlatformDataUpdateCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = TyneAndWearMetroPlatformDataUpdateCoordinator(hass, _LOGGER, config_entry=entry, name='Tyne and Wear Metro Coordinator', update_interval=timedelta(seconds=45))
    await coordinator.async_config_entry_first_refresh()
    async_add_entities([
        TyneAndWearMetroPlatformSensor(
            coordinator=coordinator,
        )]
    )


class TyneAndWearMetroPlatformSensor(CoordinatorEntity, SensorEntity):

    coordinator: TyneAndWearMetroPlatformDataUpdateCoordinator
    _attr_icon = "mdi:train-car-passenger-door"

    def __init__(self, coordinator: TyneAndWearMetroPlatformDataUpdateCoordinator) -> None:
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
        return 'ok'

    @property
    def extra_state_attributes(self):
        return {
            'next_train': self.coordinator.data['next_train'],
            'times': self.coordinator.data['times'],
            'last_update': self.coordinator.data['last_update'],
        }