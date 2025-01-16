"""DataUpdateCoordinator for the Tyne and Wear Metro integration."""

from __future__ import annotations
from typing import TYPE_CHECKING, Any
from .const import DOMAIN, _LOGGER

# import datetime

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

if TYPE_CHECKING:
    from .data import MetroConfigEntry


class MetroDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API and updating the sensor."""

    config_entry: MetroConfigEntry

    def get_platforms(self):
        for platform in self.config_entry.data['platforms']:
            yield platform

    async def _async_update_data(self) -> Any:
        try:
            data = self.data or {'platforms': {}}
            # _LOGGER.warning(f'async_step_station: {data}')
            for platform in self.config_entry.data['platforms']:
                times = await self.config_entry.runtime_data.api.get_times(platform['station_code'], platform['platform_code'])
                data['platforms'][platform['name']] = times
            # _LOGGER.warning(f'async_step_station: {data}')
            return data
        except Exception as e:
            raise UpdateFailed(f'Error updating MetroDataUpdateCoordinator: {e}')