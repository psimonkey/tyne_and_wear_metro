from __future__ import annotations

from collections import defaultdict
from datetime import datetime

import aiohttp


class MetroException(Exception):
    pass


class MetroStationNameException(Exception):
    pass


class MetroStationCodeException(Exception):
    pass


class MetroTrain:
    line: str
    destination: MetroStation
    last_event: str
    last_event_location: str
    last_event_time: datetime
    _data: defaultdict[str, defaultdict[str, dict]]

    def __init__(
        self,
        network: MetroNetwork,
        platform: MetroPlatform,
        train_data: dict[str, str],
    ) -> None:
        self.network = network
        self.trn = train_data["trn"]
        self._focus_station_code, self._focus_platform_code = "", ""
        self._data = defaultdict(lambda: defaultdict(dict))
        self.update(platform, train_data)

    def update(self, platform: MetroPlatform, train_data: dict[str, str]) -> None:
        self._focus_station_code, self._focus_platform_code = (
            platform.station.station_code,
            platform.platform_code,
        )
        self.line = train_data["line"]
        self.destination = self.network.get_station_by_name(train_data["destination"])
        self.last_event = train_data["lastEvent"]
        self.last_event_location = train_data["lastEventLocation"]
        self.last_event_time = datetime.fromisoformat(train_data["lastEventTime"])
        self._data[platform.station.station_code][platform.platform_code] = {
            "due_in": train_data["dueIn"],
            "due_time": train_data["actualPredictedTime"],
        }

    def focus(self, station_code: str, platform_code: str) -> tuple[str, str]:
        was_station_code, was_platform_code = (
            self._focus_station_code,
            self._focus_platform_code,
        )
        self._focus_station_code, self._focus_platform_code = (
            station_code,
            platform_code,
        )
        return was_station_code, was_platform_code

    @property
    def due_in(self):
        return self._data[self._focus_station_code][self._focus_platform_code]["due_in"]

    @property
    def due_time(self):
        return self._data[self._focus_station_code][self._focus_platform_code][
            "due_time"
        ]

    def as_dict(
        self, station_code: str | None = None, platform_code: str | None = None
    ) -> dict[str, str]:
        if station_code is not None and platform_code is not None:
            was_station, was_platform = self.focus(station_code, platform_code)
        data = {
            "trn": self.trn,
            "line": self.line,
            "destination_name": self.destination.station_name,
            "destination_code": self.destination.station_code,
            "due_in": self.due_in,
            "due_time": self.due_time,
        }
        if station_code is not None and platform_code is not None:
            self.focus(was_station, was_platform)
        return data


class MetroPlatform:
    def __init__(
        self,
        network: MetroNetwork,
        station: MetroStation,
        platform_code: str,
        platform_description: str,
    ):
        self.network, self.station = network, station
        self.platform_code, self.platform_description = (
            platform_description,
            platform_code,
        )
        self.arrivals: list[MetroTrain] = []

    async def update(self):
        self.arrivals = []
        for time in await self.network.api.async_get_times(
            self.station.station_code, self.platform_code
        ):
            if time["trn"] in self.network.trains:
                train = self.network.trains["trn"]
                train.update(self, time)
            else:
                train = MetroTrain(self.network, self, time)
            self.arrivals.append(train)
        self.arrivals.sort(key=lambda x: x.due_in)

    def list_trains(self):
        yield from self.arrivals


class MetroStation:
    def __init__(self, network: MetroNetwork, station_name, station_code):
        self.network, self.station_name, self.station_code = (
            network,
            station_name,
            station_code,
        )
        self.platforms: dict[str, MetroPlatform] = {}
        self._hydrated = False

    async def hydrate(self, platform_data):
        if self._hydrated:
            return
        for platform in platform_data:
            self.platforms[f"{platform['platformNumber']}"] = MetroPlatform(
                self.network,
                self,
                platform["helperText"],
                f"{platform['platformNumber']}",
            )
        self.hydrated = True

    async def update(self, platform_code: str):
        await self.platforms[platform_code].update()

    def list_platforms(self):
        yield from self.platforms.values()

    def list_trains(self, platform_code):
        yield from self.platforms[platform_code].list_trains()


class MetroNetwork:
    def __init__(self):
        self.api = MetroAPI()
        self.stations: dict[str, MetroStation] = {}
        self.trains: dict[str, MetroTrain] = {}
        self.name_to_code = {}
        self._hydrated = False

    @property
    def last_update(self):
        return self.api.last_update

    async def hydrate(self):
        if self._hydrated:
            return
        platform_data = await self.api.async_get_platforms()
        station_data = await self.api.async_get_stations()
        self.stations = {
            station_code: MetroStation(self, station_name, station_code)
            for station_code, station_name in station_data.items()
        }
        self.name_to_code = {
            station.station_name: station_code
            for station_code, station in self.stations.items()
        }
        self.name_to_code["Monument"] = "MTS"
        self.name_to_code["St. James"] = "SJM"
        for station_code, station in self.stations.items():
            await station.hydrate(platform_data[station_code])
        self._hydrated = True

    async def update(self, station_code: str, platform_code: str):
        await self.stations[station_code].update(platform_code)

    def list_stations(self):
        yield from self.stations.values()

    def list_platforms(self):
        for station in self.stations.values():
            yield from station.list_platforms()

    def list_trains(self, station_code, platform_code):
        yield from self.stations[station_code].list_trains(platform_code)

    def get_station_by_code(self, station_code: str) -> MetroStation:
        try:
            return self.stations[station_code]
        except KeyError as e:  # noqa: F841
            raise MetroStationCodeException(f"No station with code {station_code}")

    def get_station_by_name(self, station_name: str) -> MetroStation:
        try:
            return self.stations[self.name_to_code[station_name]]
        except KeyError as e:  # noqa: F841
            pass
        raise MetroStationNameException(f"No station called {station_name}")


class MetroAPI:
    API_BASE = "https://metro-rti.nexus.org.uk/api/"

    def __init__(self):
        self.last_update = datetime.now()

    async def async_get_json(self, path):
        async with aiohttp.ClientSession() as session:  # noqa: SIM117
            async with session.request("GET", f"{self.API_BASE}{path}") as response:
                response.raise_for_status()
                j = await response.json()
        self.last_update = datetime.now()
        return j

    async def async_get_times(self, station_code, platform_number):
        return await self.async_get_json(f"times/{station_code}/{platform_number}")

    async def async_get_stations(self):
        return await self.async_get_json("stations")

    async def async_get_platforms(self):
        return await self.async_get_json("stations/platforms")
