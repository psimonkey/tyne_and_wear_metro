"""DataUpdateCoordinator for Tyne and Wear Metro."""

from __future__ import annotations
import logging
from typing import Any
import datetime

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)

from metro import MetroAPI


class TyneAndWearMetroPlatformDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API and updating the sensor."""

    config_entry: ConfigEntry
    _api: MetroAPI

    async def _async_setup(self) -> None:
        self._api = MetroAPI()
        self.data = await self._async_update_data()

    async def _async_update_data(self) -> Any:
        try:
            times = await self.hass.async_add_executor_job(self._api.get_times, self.config_entry.data.get('code'), self.config_entry.data.get('platform'))
            if len(times) > 0:
                next_train = f"{times[0]['dueIn']} mins to {times[0]['destination']} (Train {times[0]['trn']}"
            else:
                next_train = 'None'
            data = {
                'next_train': next_train,
                'times': times,
                'last_update': datetime.datetime.now(),
            }
            # _LOGGER.warning(f'async_step_station: {data}')
            return data
        except Exception as e:
            raise UpdateFailed(f'Error updating TyneAndWearMetroPlatformDataUpdateCoordinator: {e}')