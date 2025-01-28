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
            update_method=None,
            update_interval=None,
            # update_interval=timedelta(seconds=45),
            always_update=False,
        )
        self.api = api
        self.data = {
            "last_update": self.api.last_update,
            "trains": defaultdict(lambda: defaultdict(list)),
            "subscriptions": [],
        }

    async def _async_setup(self) -> None:
        await self.api.hydrate()

    async def _async_update_data(self) -> Any:
        data = self.data or {}
        try:
            now = datetime.now()
            too_old = timedelta(minutes=30)
            data["subscriptions"] = [
                (station_code, platform_code, subscription_time)
                for station_code, platform_code, subscription_time in data[
                    "subscriptions"
                ]
                if now - subscription_time <= too_old
            ]
            to_refresh = [
                (station_code, platform_code)
                for station_code, platform_code, _ in data["subscriptions"]
            ]
            for station_code, platform_data in data["trains"].items():
                for platform_code in platform_data:
                    if (station_code, platform_code) not in to_refresh:
                        data["trains"][station_code][platform_code] = []
            for station_code, platform_code in to_refresh:
                await self.api.update(station_code, platform_code)
                data["trains"][station_code][platform_code] = [
                    train.as_dict(station_code, platform_code)
                    for train in self.api.list_trains(station_code, platform_code)
                ]
            data["last_update"] = datetime.now()
        except Exception as e:  # noqa: BLE001
            raise UpdateFailed(f"Error updating MetroDataUpdateCoordinator: {e}")
        return data

    def subscribe(self, station_code: str, platform_code: str) -> None:
        self.data["subscriptions"].append((station_code, platform_code, datetime.now()))

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
