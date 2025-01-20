from __future__ import annotations
from typing import TYPE_CHECKING

from datetime import datetime
import aiohttp
from pprint import pp


class MetroException(Exception): pass
class MetroStationNameException(Exception): pass
class MetroStationCodeException(Exception): pass


class MetroTrain:

    def __init__(self, network: MetroNetwork, station_code: str, platform_code: str, train_data: dict[str, str]) -> None:
        self._network = network
        self.name = train_data['trn']
        self._station, self._platform = station_code, platform_code
        self._data = {
            station_code: {
                platform_code: train_data
            }
        }

    def focus(self, station_code: str, platform_code: str) -> tuple[str, str]:
        was_station, was_platform = self._station, self._platform
        self._station, self._platform = station_code, platform_code
        return was_station, was_platform

    @property
    def trn(self): return self.name
    @property
    def line(self): return self._data[self._station][self._platform]['line']
    @property
    def destination(self): return self._data[self._station][self._platform]['destination']
    @property
    def destination_code(self): return self._network.get_station_by_name(self._data[self._station][self._platform]['destination']).code
    @property
    def dueIn(self): return self._data[self._station][self._platform]['dueIn']
    @property
    def dueTime(self): return datetime.fromisoformat(self._data[self._station][self._platform]['actualPredictedTime'])

    def as_dict(self, station_code: str | None = None, platform_code: str | None = None) -> dict[str, str]:
        if station_code is not None and platform_code is not None:
            was_station, was_platform = self.focus(station_code, platform_code)
        data = {
            'trn': self.trn,
            'line': self.line,
            'destination': self.destination,
            'destination_code': self.destination_code,
            'dueIn': self.dueIn,
            'dueTime': self.dueTime,
        }
        if station_code is not None and platform_code is not None:
            self.focus(was_station, was_platform)
        return data

    def __repr__(self):
        return f'Train {self.trn} for {self.destination} due in {self.dueIn} minutes'


class MetroPlatform:

    # def __init__(self, network: MetroNetwork, station: MetroStation, name: str, platform_codes: list[str], destination_codes: list[str]):
    def __init__(self, network: MetroNetwork, station: MetroStation, name: str, platform_code: str):
        self._network, self._station = network, station
        # self.name, self._platform_codes, self._destination_codes = name, platform_codes, destination_codes
        self.name, self.code = name, platform_code
        self.arrivals: list[MetroTrain] = []

    # async def get_times(self, destination_code):
    #     times = []
    #     for platform_code in self._platform_codes:
    #         times += [MetroTrain(self._network, time).get_time(self._station.code) for time in await self._network.api.async_get_times(self._station.code, platform_code)]
    #     times.sort(key=lambda x: x['dueIn'])
    #     if len(times) > 0:
    #         next_train = f'Train {times[0]['trn']} for {times[0]['destination_text']} due in {times[0]['dueIn']} minutes'
    #     else:
    #         next_train = 'None'
    #     return {
    #         'lastUpdated': self._network.api.last_update,
    #         'next_train': next_train,
    #         'trains': times,
    #     }

    async def update(self):
        self.arrivals = [MetroTrain(self._network, self._station.code, self.code, time) for time in await self._network.api.async_get_times(self._station.code, self.code)]
        self.arrivals.sort(key=lambda x: x.dueIn)

    # For sensors

    def next_train_description(self, destination_code: str, offset: int = 0) -> str | None:
        try:
            return f'{self.arrivals[offset]}'
        except IndexError as e:
            return None

    def platform_description(self, destination_code: str) -> str | None:
        return f'{self._station.name} Platform {self.code}'

    def trains(self, destination_code: str) -> list[dict[str, str]]:
        return [train.as_dict() for train in self.arrivals]

    # def __repr__(self):
    #     return f'{self.name} | {self._platform_codes} | {self._destination_codes}'


class MetroStation:

    def __init__(self, network: MetroNetwork, name, code):
        self._network, self.name, self.code = network, name, code
        self._platforms: dict[str, MetroPlatform] = {}
        self._hydrated = False

    async def hydrate(self, platform_data):
        if self._hydrated:
            return
        # platform_codes = []
        # all_destination_codes = []
        for platform in platform_data:
            # platform_codes.append(f'{platform['platformNumber']}')
            # destination_texts = [platform['helperText'][8:]]
            # if ' and ' in destination_texts[0]:
            #     destination_texts = destination_texts[0].split(' and ')
            # destination_codes = []
            # for destination_text in destination_texts:
            #     if ' via ' in destination_text:
            #         destination_text = destination_text.split(' via ')[0]
            #     destination_codes.append(self._network.get_station_by_name(destination_text).code)
            # all_destination_codes += destination_codes
            # self._platforms[f'{platform['platformNumber']}'] = MetroPlatform(self._network, self, platform['helperText'], [f'{platform['platformNumber']}'], destination_codes)
            self._platforms[f'{platform['platformNumber']}'] = MetroPlatform(self._network, self, platform['helperText'], f'{platform['platformNumber']}')
        # self._platforms['all'] = MetroPlatform(self._network, self, 'All platforms', platform_codes, all_destination_codes)
        self.hydrated = True

    async def update(self, platform_code: str):
        await self._platforms[platform_code].update()

    # For sensors

    def next_train_description(self, platform_code: str, destination_code: str, offset: int = 0) -> str | None:
        return self._platforms[platform_code].next_train_description(destination_code, offset)

    def platform_description(self, platform_code: str, destination_code: str) -> str | None:
        return self._platforms[platform_code].platform_description(destination_code)

    def trains(self, platform_code: str, destination_code: str) -> list[dict[str, str]]:
        return self._platforms[platform_code].trains(destination_code)

    # async def get_times(self, platform_code, destination_code):
    #     return await self._platforms[platform_code].get_times(destination_code)

    # def get_platform(self, platform_code: str) -> MetroPlatform:
    #     return self._platforms[platform_code]

    # async def get_platforms_select(self):
    #     available_platforms = []
    #     for platform_code, platform in self._platforms.items():
    #         available_platforms.append({'label': f'{self.name} platform {platform_code} ({platform.name})', 'value': f'{self.code}|{platform_code}'} )
    #     return available_platforms

    def __repr__(self):
        return f'{self.code} | {self.name}\n' + '\n'.join(f'{code}: {platform}' for code, platform in self._platforms.items())


class MetroNetwork:

    GREEN_LINE = ('APT','CAL','BFT','KSP','FAW','WBR','RGC','SGF','ILF','WJS','JES','HAY','MTS','CEN','GHD','GST','FEL','HTH','PLW','FGT','BYW','EBO','SBN','SFC','MSP','SUN','PLI','UNI','MLF','PAL','SHL')
    YELLOW_LINE = ('SJM', 'MTW', 'MAN', 'BYK', 'CRD', 'WKG', 'WSD', 'HDR', 'HOW', 'PCM', 'MWL', 'NSH', 'TYN', 'CUL', 'WTL', 'MSN', 'WMN', 'SMR', 'NPK', 'PMV', 'BTN', 'FLE', 'LBN', 'SGF', 'ILF', 'WJS', 'JES', 'HAY', 'MTS', 'CEN', 'GHD', 'GST', 'FEL', 'HTH', 'PLW', 'HEB', 'JAR', 'BDE', 'SMD', 'TDK', 'CHI', 'SSS')

    def __init__(self):
        self.api = MetroAPI()
        self._stations: dict[str, MetroStation] = {}
        # self._trains: dict[str, MetroTrain] = {}
        self._name_to_code = {}
        self._subscriptions: list[tuple[str, str, str]] = []
        self._hydrated = False

    @property
    def last_update(self):
        return self.api.last_update

    async def hydrate(self):
        if self._hydrated:
            return
        platform_data = await self.api.async_get_platforms()
        station_data = await self.api.async_get_stations()
        self._stations = {code: MetroStation(self, station_name, code) for code, station_name in station_data.items()}
        self._name_to_code = {station.name: code for code, station in self._stations.items()}
        self._name_to_code['Monument'] = 'MTS'
        self._name_to_code['St. James'] = 'SJM'
        for code, station in self._stations.items():
            await station.hydrate(platform_data[code])
        self._hydrated = True

    def subscribe(self, station_code: str, platform_code: str, destination_code: str) -> bool:
        self._subscriptions.append((station_code, platform_code, destination_code))
        return True

    async def update(self, station_code: str, platform_code: str):
        await self._stations[station_code].update(platform_code)

    # For sensors

    def next_train_description(self, station_code: str, platform_code: str, destination_code: str, offset: int = 0) -> str | None:
        return self._stations[station_code].next_train_description(platform_code, destination_code, offset)

    def platform_description(self, station_code: str, platform_code: str, destination_code: str) -> str | None:
        return self._stations[station_code].platform_description(platform_code, destination_code)

    def trains(self, station_code: str, platform_code: str, destination_code: str) -> list[dict[str, str]]:
        return self._stations[station_code].trains(platform_code, destination_code)


    # async def get_times(self, station_code, platform_code, destination_code=None):
    #     return await self._stations[station_code].get_times(platform_code, destination_code)

    # def get_platform(self, station_code: str, platform_code: str) -> MetroPlatform:
    #     return self._stations[station_code].get_platform(platform_code)

    # For config flow

    async def get_station_select(self, from_station=None):
        stations = [{'label': f'{station.name}', 'value': f'{code}'} for code, station in self._stations.items() if code != from_station]
        stations.sort(key=lambda x: x['label'])
        return stations

    # async def get_platforms_select(self):
    #     available_platforms = []
    #     for code, station in self._stations.items():
    #         available_platforms += await station.get_platforms_select()
    #     return available_platforms

    def which_platform(self, from_station, to_station):
        print(from_station, to_station, end=' ')
        # Both stations are on the same line, so we just need to figure out which direction
        if (from_station in self.GREEN_LINE and to_station in self.GREEN_LINE) or (from_station in self.YELLOW_LINE and to_station in self.YELLOW_LINE):
            if from_station in self.GREEN_LINE and to_station in self.GREEN_LINE:
                line = self.GREEN_LINE
            elif from_station in self.YELLOW_LINE and to_station in self.YELLOW_LINE:
                line = self.YELLOW_LINE
            if line.index(from_station) < line.index(to_station):
                platform_number = '1'
            else:
                platform_number = '2'
        else:
            # The stations are on different lines, so head towards the nearest junction
            if from_station in ('APT', 'CAL', 'BFT', 'KSP', 'FAW', 'WBR', 'RGC'):
                platform_number = '1'
            elif from_station in ('FEL','HTH','PLW','FGT','BYW','EBO','SBN','SFC','MSP','SUN','PLI','UNI','MLF','PAL','SHL'):
                platform_number = '2'
            elif from_station in ('HEB', 'JAR', 'BDE', 'SMD', 'TDK', 'CHI', 'SSS'):
                platform_number = '2'
            elif from_station in ('SJM', 'MTW', 'WTL', 'MSN', 'WMN', 'SMR', 'NPK', 'PMV', 'BTN', 'FLE', 'LBN'):
                platform_number = '1'
            elif from_station in ('MAN', 'BYK', 'CRD', 'WKG', 'WSD', 'HDR', 'HOW', 'PCM', 'MWL', 'NSH', 'TYN', 'CUL'):
                platform_number = '2'

        return self._stations[from_station]._platforms[platform_number]

    def get_station_by_code(self, station_code: str) -> MetroStation:
        try:
            return self._stations[station_code]
        except KeyError as e:
            raise MetroStationCodeException(f'No station with code {station_code}')

    def get_station_by_name(self, station_name: str) -> MetroStation:
        try:
            return self._stations[self._name_to_code[station_name]]
        except KeyError as e:
            pass
        raise MetroStationNameException(f'No station called {station_name}')

    def __repr__(self):
        return '\n\n'.join(f'{code}: {station}' for code, station in self._stations.items())


class MetroAPI:

    API_BASE = 'https://metro-rti.nexus.org.uk/api/'

    def __init__(self):
        pass

    @property
    def last_update(self):
        return datetime.now()

    async def async_get_json(self, path):
        async with aiohttp.ClientSession() as session:
            async with session.request('GET', f'{self.API_BASE}{path}') as response:
                response.raise_for_status()
                j = await response.json()
        return j

    async def async_get_times(self, station_code, platform_number):
        return await self.async_get_json(f'times/{station_code}/{platform_number}')

    async def async_get_stations(self):
        return await self.async_get_json('stations')

    async def async_get_platforms(self):
        return await self.async_get_json('stations/platforms')


async def main():
    m = MetroNetwork()
    await m.hydrate()
    print()
    pp(await m.get_station_select())
    print()
    pp(await m.get_station_select('MSN'))
    pp(m.which_platform('MSN', 'JES'))
    pp(m.which_platform('MSN', 'MTS'))
    pp(m.which_platform('MSN', 'MTW'))
    pp(m.which_platform('KSP', 'GHD'))
    pp(m.which_platform('KSP', 'UNI'))
    pp(m.which_platform('SSS', 'HTH'))
    pp(m.which_platform('KSP', 'SSS'))
    pp(m.which_platform('KSP', 'HRD'))
    # print(m)
    # print(await m.get_times('WTL', '1'))

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())