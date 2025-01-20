"""Sensor platform for the Tyne and Wear Metro integration."""

from __future__ import annotations
from typing import TYPE_CHECKING, Any
from .const import DOMAIN, _LOGGER

# from datetime import timedelta

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
    coordinator = entry.runtime_data.coordinator
    entities: list[SensorEntity] = [
        MetroJourneySensor(
            from_station=entry.runtime_data.start,
            from_platform=entry.runtime_data.platform,
            to_station=entry.runtime_data.end,
            coordinator=coordinator,
        )
    ]
    for i, t in (
        (0, 'Next'),
        (1, 'Second'),
        (2, 'Third'),
        (3, 'Fourth'),
    ):
        entities.append(
            MetroTrainSensor(
                from_station=entry.runtime_data.start,
                from_platform=entry.runtime_data.platform,
                to_station=entry.runtime_data.end,
                seq_index=i,
                seq_text=t,
                coordinator=coordinator,
            )
        )
    async_add_entities(entities)


class MetroSensor(CoordinatorEntity, SensorEntity):

    _attr_has_entity_name = True
    coordinator: MetroDataUpdateCoordinator
    _attr_icon = "mdi:subway-variant"

    def __init__(self, name: str|None, unique_id: str, coordinator: MetroDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._attr_device_info = DeviceInfo(
            name=f'Metro from {coordinator.api.get_station_by_code(coordinator.config_entry.runtime_data.start).name} to {coordinator.api.get_station_by_code(coordinator.config_entry.runtime_data.end).name}',
            identifiers={
                (
                    coordinator.config_entry.domain,
                    coordinator.config_entry.entry_id,
                ),
            },
        )


class MetroJourneySensor(MetroSensor):

    def __init__(self, from_station: str, from_platform: str, to_station: str, coordinator: MetroDataUpdateCoordinator):
        _LOGGER.warning(f'MetroJourneySensor.__init__ | {from_station = } | {from_platform = } | {to_station = }')
        # name=,
        super().__init__(
            name=None,
            unique_id=f'metro_{from_station}_{to_station}',
            coordinator=coordinator,
        )
        self._attr_from_station = from_station
        self._attr_from_platform = from_platform
        self._attr_to_station = to_station

    @property
    def state(self) -> str | None:
        return self.coordinator.next_train_description(
            self._attr_from_station,
            self._attr_from_platform,
            self._attr_to_station,
        )

    @property
    def extra_state_attributes(self):
        return {
            'last_update': self.coordinator.data.get('last_update', 'None'),
            'platform': self.coordinator.platform_description(self._attr_from_station, self._attr_from_platform, self._attr_to_station),
            'trains': self.coordinator.trains(
                self._attr_from_station,
                self._attr_from_platform,
                self._attr_to_station,
            ),
        }

class MetroTrainSensor(MetroSensor):

    _attr_icon = "mdi:train-car-passenger-door"

    def __init__(self, from_station: str, from_platform: str, to_station: str, seq_index: int, seq_text: str, coordinator: MetroDataUpdateCoordinator):
        super().__init__(
            name=f'{seq_text} Train',
            unique_id=f'metro_{from_station}_{to_station}_{seq_text}',
            coordinator=coordinator,
        )
        self._attr_from_station = from_station
        self._attr_from_platform = from_platform
        self._attr_to_station = to_station
        self._attr_seq_index = seq_index
        self._attr_seq_text = seq_text

    @property
    def state(self) -> str | None:
        return self.coordinator.next_train_description(
            self._attr_from_station,
            self._attr_from_platform,
            self._attr_to_station,
            self._attr_seq_index,
        )

    @property
    def extra_state_attributes(self):
        return {
            'last_update': self.coordinator.data.get('last_update', 'None'),
            'platform': self.coordinator.platform_description(self._attr_from_station, self._attr_from_platform, self._attr_to_station),
        }
