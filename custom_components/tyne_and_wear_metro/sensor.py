"""Sensor platform for the Tyne and Wear Metro integration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import MetroDataUpdateCoordinator
from .metro import MetroPlatform

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import MetroConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MetroConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data.coordinator
    entities: list[SensorEntity] = [
        MetroPlatformSensor(platform, coordinator=coordinator)
        for platform in entry.runtime_data.api.list_platforms()
    ]
    async_add_entities(entities)


class MetroSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = False
    _attr_icon = "mdi:subway-variant"
    coordinator: MetroDataUpdateCoordinator

    def __init__(
        self, name: str | None, unique_id: str, coordinator: MetroDataUpdateCoordinator
    ) -> None:
        super().__init__(coordinator)
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._attr_device_info = DeviceInfo(
            name="Tyne and Wear Metro",
            identifiers={
                (
                    coordinator.config_entry.domain,
                    coordinator.config_entry.entry_id,
                ),
            },
        )


class MetroPlatformSensor(MetroSensor):
    _attr_icon = "mdi:train-car-passenger-door"

    def __init__(
        self,
        platform: MetroPlatform,
        coordinator: MetroDataUpdateCoordinator,
    ):
        super().__init__(
            name=f"{platform.station.station_name} platform {platform.platform_code}",
            unique_id=f"metro_{platform.station.station_name}_platform_{platform.platform_code}",
            coordinator=coordinator,
        )
        self._attr_station_code = platform.station.station_code
        self._attr_station_name = platform.station.station_name
        self._attr_platform_code = platform.platform_code
        self._attr_platform_description = platform.platform_description

    @property
    def state(self) -> str | None:
        return self.coordinator.next_train(
            self._attr_station_code,
            self._attr_platform_code,
        )

    @property
    def extra_state_attributes(self):
        return {
            "station": self._attr_station_code,
            "station_code": self._attr_station_name,
            "platform": self._attr_platform_code,
            "description": self._attr_platform_description,
            "last_update": self.coordinator.data.get("last_update", "None"),
            "trains": self.coordinator.trains(
                self._attr_station_code, self._attr_platform_code
            ),
        }

    async def async_update(self, **kwargs):
        self.coordinator.subscribe(
            self._attr_station_code,
            self._attr_platform_code,
        )
        await self.coordinator.async_request_refresh()
