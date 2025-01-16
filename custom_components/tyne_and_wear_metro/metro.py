from __future__ import annotations
from typing import TYPE_CHECKING

from datetime import datetime
from PIL import Image, ImageDraw
import aiofiles, aiohttp
import asyncio
import json

import requests #, requests_cache


class MetroException(Exception): pass
class MetroStationNameException(Exception): pass


class MetroTrain:

    def __init__(self, network, train_data):
        self._network = network
        self.name = train_data['trn']
        self._data = train_data

    def get_time(self, station_code, platform_code=None):
        return {
            'trn': self.name,
            'line': self._data['line'],
            'destination': self._network.get_station_by_name(self._data['destination']).code,
            'destination_text': self._data['destination'],
            'dueIn': self._data['dueIn'],
            'dueTime': datetime.fromisoformat(self._data['actualPredictedTime']),
        }


class MetroPlatform:

    def __init__(self, network: MetroNetwork, station: MetroStation, name: str, platform_codes: list[str], destination_codes: list[str]):
        self._network, self._station = network, station
        self.name, self._platform_codes, self._destination_codes = name, platform_codes, destination_codes
        self.arrivals: list[MetroTrain] = []

    async def get_times(self, destination_code):
        times = []
        for platform_code in self._platform_codes:
            times += [MetroTrain(self._network, time).get_time(self._station.code) for time in await self._network.api.async_get_times(self._station.code, platform_code)]
        times.sort(key=lambda x: x['dueIn'])
        if len(times) > 0:
            next_train = f'Train {times[0]['trn']} for {times[0]['destination_text']} due in {times[0]['dueIn']} minutes'
        else:
            next_train = 'None'
        return {
            'lastUpdated': self._network.api.last_update,
            'next_train': next_train,
            'trains': times,
        }

    def __repr__(self):
        return f'{self.name} | {self._platform_codes} | {self._destination_codes}'


class MetroStation:

    def __init__(self, network: MetroNetwork, name, code):
        self._network, self.name, self.code = network, name, code
        self._platforms: dict[str, MetroPlatform] = {}
        self._hydrated = False

    async def hydrate(self, platform_data):
        if self._hydrated:
            return
        platform_codes = []
        all_destination_codes = []
        for platform in platform_data:
            platform_codes.append(f'{platform['platformNumber']}')
            destination_texts = [platform['helperText'][8:]]
            if ' and ' in destination_texts[0]:
                destination_texts = destination_texts[0].split(' and ')
            destination_codes = []
            for destination_text in destination_texts:
                if ' via ' in destination_text:
                    destination_text = destination_text.split(' via ')[0]
                destination_codes.append(self._network.get_station_by_name(destination_text).code)
            all_destination_codes += destination_codes
            self._platforms[f'{platform['platformNumber']}'] = MetroPlatform(self._network, self, platform['helperText'], [f'{platform['platformNumber']}'], destination_codes)
        self._platforms['all'] = MetroPlatform(self._network, self, 'All platforms', platform_codes, all_destination_codes)
        self.hydrated = True

    async def get_times(self, platform_code, destination_code):
        return await self._platforms[platform_code].get_times(destination_code)

    async def get_platforms_select(self):
        available_platforms = []
        for platform_code, platform in self._platforms.items():
            available_platforms.append({'label': f'{self.name} platform {platform_code} ({platform.name})', 'value': f'{self.code}|{platform_code}'} )
        return available_platforms


    def __repr__(self):
        return f'{self.code} | {self.name}\n' + '\n'.join(f'{code}: {platform}' for code, platform in self._platforms.items())


class MetroNetwork:

    def __init__(self):
        self.api = MetroAPI()
        self._stations: dict[str, MetroStation] = {}
        self._trains: dict[str, MetroTrain] = {}
        self._hydrated = False

    async def hydrate(self):
        if self._hydrated:
            return
        platform_data = await self.api.async_get_platforms()
        station_data = await self.api.async_get_stations()
        self._stations = {code: MetroStation(self, station_name, code) for code, station_name in station_data.items()}
        for code, station in self._stations.items():
            await station.hydrate(platform_data[code])
        self._hydrated = True

    async def get_times(self, station_code, platform_code, destination_code=None):
        return await self._stations[station_code].get_times(platform_code, destination_code)

    async def get_platforms_select(self):
        available_platforms = []
        for code, station in self._stations.items():
            available_platforms += await station.get_platforms_select()
        return available_platforms

    def get_station_by_name(self, station_name: str) -> MetroStation:
        if station_name == 'St. James':
            return self._stations['SJM']
        for code, station in self._stations.items():
            if station.name == station_name:
                return station
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

    def get_json(self, path):
        r = requests.get(f'{self.API_BASE}{path}')
        return r.json()

    async def async_get_json(self, path):
        async with aiohttp.ClientSession() as session:
            async with session.request('GET', f'{self.API_BASE}{path}') as response:
                response.raise_for_status()
                j = await response.json()
        return j

    async def async_get_times(self, station_code, platform_number):
        return await self.async_get_json(f'times/{station_code}/{platform_number}')

    def get_stations(self):
        with open('stations.json', 'r') as f:
            return json.load(f)
        # return self.get_json('stations')

    async def async_get_stations(self):
        async with aiofiles.open('stations.json', 'r') as f:
            content = await f.read()
        return json.loads(content)

    def get_platforms(self):
        with open('platforms.json', 'r') as f:
            return json.load(f)
        # return self.get_json('stations/platforms')

    async def async_get_platforms(self):
        async with aiofiles.open('platforms.json', 'r') as f:
            content = await f.read()
        return json.loads(content)


async def main():
    m = MetroNetwork()
    await m.hydrate()
    print(await m.get_platforms_select())
    # print(m)
    # print(await m.get_times('WTL', '1'))

if __name__ == '__main__':
    asyncio.run(main())