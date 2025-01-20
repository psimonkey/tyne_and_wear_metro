"""DataUpdateCoordinator for the Tyne and Wear Metro integration."""

from __future__ import annotations
from typing import TYPE_CHECKING, Any
from .const import DOMAIN, _LOGGER

from datetime import timedelta

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .metro import MetroNetwork, MetroStation, MetroPlatform

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from .data import MetroConfigEntry


class MetroDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API and updating the sensor."""

    config_entry: MetroConfigEntry

    def __init__(self, hass: HomeAssistant, name: str, api: MetroNetwork, config_entry: MetroConfigEntry):
        super().__init__(hass, _LOGGER, name=name, config_entry=config_entry, update_interval=timedelta(seconds=45))
        self.api = api
        self.data = {}

    async def _async_setup(self) -> None:
        await self.api.hydrate()
        self.api.subscribe(
            self.config_entry.runtime_data.start,
            self.config_entry.runtime_data.platform,
            self.config_entry.runtime_data.end
        )

    async def _async_update_data(self) -> Any:
        try:
            data = self.data or {}
            await self.api.update(self.config_entry.runtime_data.start, self.config_entry.runtime_data.platform)
            data['last_update'] = self.api.last_update
            return data
        except Exception as e:
            raise e
            raise UpdateFailed(f'Error updating MetroDataUpdateCoordinator: {e}')

    def next_train_description(self, from_station: str, from_platform: str, to_station: str, offset: int = 0) -> str | None:
        return self.api.next_train_description(from_station, from_platform, to_station, offset)

    def platform_description(self, from_station: str, from_platform: str, to_station: str) -> str | None:
        return self.api.platform_description(from_station, from_platform, to_station)

    def trains(self, from_station: str, from_platform: str, to_station: str) -> list[dict[str, str]]:
        return self.api.trains(from_station, from_platform, to_station)

