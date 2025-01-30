"""DataUpdateCoordinator for the Tyne and Wear Metro integration."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import _LOGGER
from .metro import MetroNetwork

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import MetroConfigEntry


class MetroDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API and updating the sensor."""

    config_entry: MetroConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        name: str,
        api: MetroNetwork,
        config_entry: MetroConfigEntry,
    ):
        super().__init__(
            hass,
            _LOGGER,
            name=name,
            config_entry=config_entry,
            # update_method=None,
            # update_interval=None,
            update_interval=timedelta(seconds=45),
            always_update=True,
        )
        self.api = api
        self.data = {
            "last_update": self.api.last_update,
            "trains": defaultdict(lambda: defaultdict(list)),
            "refreshed": defaultdict(lambda: defaultdict(lambda: None)),
        }

    async def _async_setup(self) -> None:
        await self.api.hydrate()

    async def _async_update_data(self) -> Any:
        data = self.data or {}
        try:
            subscription_cutoff = datetime.now() - timedelta(minutes=30)
            refresh_cutoff = datetime.now() - timedelta(seconds=30)
            # _LOGGER.warning(f"{self.api.last_update} Starting refresh")
            for platform_sensor in self.async_contexts():
                station_code, platform_code, subscribed_time = (
                    platform_sensor.refresh_params()
                )
                if subscribed_time is None or subscribed_time < subscription_cutoff:
                    data["trains"][station_code][platform_code] = []
                    data["refreshed"][station_code][platform_code] = None
                elif (
                    data["refreshed"][station_code][platform_code] is None
                    or data["refreshed"][station_code][platform_code] < refresh_cutoff
                ):
                    # _LOGGER.warning(
                    #     f"{self.api.last_update} Refreshing {station_code} platform {platform_code}"
                    # )
                    await self.api.update(station_code, platform_code)
                    trains = [
                        train.as_dict(station_code, platform_code)
                        for train in self.api.list_trains(station_code, platform_code)
                    ]
                    # _LOGGER.warning(
                    #     f"{self.api.last_update} Got {len(trains)} for {station_code} platform {platform_code}"
                    # )
                    data["trains"][station_code][platform_code] = trains
                    data["refreshed"][station_code][platform_code] = (
                        self.api.last_update
                    )
                # else:
                #     _LOGGER.warning(
                #         f"{self.api.last_update} Nothing to do for {station_code} platform {platform_code}"
                #     )
            data["last_update"] = self.api.last_update
            # _LOGGER.warning(f"{self.api.last_update} Refresh finished")
        except Exception as e:  # noqa: BLE001
            raise UpdateFailed(f"Error updating MetroDataUpdateCoordinator: {e}")
        return data

    def next_train(self, station_code: str, platform_code: str) -> str:
        try:
            train = self.data["trains"][station_code][platform_code][0]
            return f"{train['trn']} For {train['destination_name']} in {train['due_in']} mins"
        except (IndexError, KeyError) as e:  # noqa: F841
            return "Unknown"

    def trains(self, station_code: str, platform_code: str) -> list[dict[str, str]]:
        try:
            return self.data["trains"][station_code][platform_code]
        except (IndexError, KeyError) as e:  # noqa: F841
            return []
