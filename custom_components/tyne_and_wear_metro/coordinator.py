"""DataUpdateCoordinator for the Tyne and Wear Metro integration."""

from __future__ import annotations
from typing import TYPE_CHECKING, Any
from .const import DOMAIN, _LOGGER

import datetime

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

if TYPE_CHECKING:
    from .data import MetroConfigEntry


class MetroDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API and updating the sensor."""

    config_entry: MetroConfigEntry

    async def _async_update_data(self) -> Any:
        try:
            times = await self.config_entry.runtime_data.api.get_times(self.config_entry.data.get('code'), self.config_entry.data.get('platform'))
            _LOGGER.warning(f'async_step_station: {times}')
            return times
        except Exception as e:
            raise UpdateFailed(f'Error updating MetroDataUpdateCoordinator: {e}')