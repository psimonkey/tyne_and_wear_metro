from datetime import datetime
import json

import aiofiles
from PIL import Image, ImageDraw
import requests  # , requests_cache


class MetroNetwork:
    def __init__(self, update=False):
        self.api = MetroAPI()
        platforms = self.api.get_platforms()
        self.trains = {}
        self.station_names = self.api.get_stations()
        self.stations = {
            name: MetroStation(self, name, code, platforms[code])
            for code, name in self.station_names.items()
        }
        if update:
            self.update()

    def get_stations_select(self):
        return [
            {"label": station.name, "value": station.code}
            for station in self.stations.values()
        ]

    def get_platforms_select(self, station):
        return [
            {"label": platform.text, "value": number}
            for number, platform in self.stations[station].platforms.items()
        ]

    def valid_station(self, code):
        if code not in self.stations.keys():
            return False, f"Invalid station {code}"
        return True, ""

    def valid_platform(self, code, number):
        if number not in self.stations[code].platforms.keys():
            return False, f"Invalid platform {number} for station {code}"
        return True, ""

    def get_stations(self):
        return [station.name for station in self.stations.keys()]

    def get_codes(self):
        return [station.name for station in self.stations.keys()]

    def update(self, station=None, platform=None):
        if station is None:
            for name, station in self.stations.items():
                station.update()
        else:
            self.stations[station].update(platform)

    def add_train(self, platform, train_data):
        if train_data["trn"] in self.trains:
            train = self.trains[train_data["trn"]]
            train.update(train_data, platform)
        else:
            train = MetroTrain(self, train_data, platform)
            self.trains[train.id] = train
        return train.arrival(platform)

    def print_map(self):
        map = MetroMap()
        for number, train in self.trains.items():
            map.add_train(number, (train.x, train.y), train.d, train.colour)
        map.save()

    def __repr__(self):
        return "\n\n".join(f"{station}" for station in self.stations.values())


class MetroStation:
    def __init__(self, network, name, code, platforms=None):
        self.network, self.name, self.code = network, name, code
        self.platforms = {}
        if platforms is not None:
            for platform in platforms:
                self.add_platform(platform)

    def add_platform(self, data):
        p = MetroPlatform(self, data)
        self.platforms[p.number] = p

    def update(self, platform=None):
        if platform is None:
            for number, platform in self.platforms.items():
                platform.update()
        else:
            self.platforms[platform].update()

    def __repr__(self):
        return f"{self.name} ({self.code})\n" + "\n".join(
            f"{platform}" for platform in self.platforms.values()
        )


class MetroPlatform:
    def __init__(self, station, data):
        self.station = station
        self.number = str(data.get("platformNumber", "???"))
        self.direction = data.get("direction", "???")
        self.text = data.get("helperText", "???")
        coords = data.get(
            "coordinates",
            {"longitude": -1.64502501487732, "latitude": 55.0135612487793},
        )
        self.lat = coords.get("latitude", "0")
        self.lon = coords.get("longitude", "0")
        self.x = coords.get("x", "0")
        self.y = coords.get("y", "0")
        self.d = coords.get("d", "0")
        self.arrivals = []

    def update(self):
        train_datas = self.station.network.api.get_times(self.station.code, self.number)
        for train_data in train_datas:
            self.arrivals.append(self.station.network.add_train(self, train_data))

    def __repr__(self):
        return f"{self.station.name}, Platform {self.number}"


class MetroTrain:
    OFFSETS = {
        "READY_TO_START": {
            "N": (0, 0),
            "S": (0, 0),
            "E": (0, 0),
            "W": (0, 0),
            "U": (0, 0),
            "D": (0, 0),
        },
        "APPROACHING": {
            "N": (0, 20),
            "S": (0, -20),
            "E": (-20, 0),
            "W": (20, 0),
            "U": (9, 15),
            "D": (-7, -15),
        },
        "ARRIVED": {
            "N": (0, 0),
            "S": (0, 0),
            "E": (0, 0),
            "W": (0, 0),
            "U": (0, 0),
            "D": (0, 0),
        },
        "DEPARTED": {
            "N": (0, -20),
            "S": (0, 20),
            "E": (20, 0),
            "W": (-20, 0),
            "U": (-7, -15),
            "D": (9, 15),
        },
    }

    def __init__(self, network, train_data, platform):
        self.network = network
        self.id = train_data.get("trn", "???")
        self.colour = "red"
        if self.id == "121":
            self.colour = "blue"
        self.destination = train_data.get("destination", "???")
        self.line = train_data.get("line", "???")
        self.event = []
        self.arrivals = {}
        self.update(train_data, platform)

    def update(self, train_data, platform):
        self.event = {
            "lastEvent": train_data["lastEvent"],
            "lastEventLocation": train_data["lastEventLocation"],
            "lastEventTime": train_data["lastEventTime"],
        }
        self.arrivals[(platform.station, platform.number)] = {
            "station": platform.station,
            "platform": platform.number,
            "dueIn": train_data["dueIn"],
            "actualPredictedTime": datetime.fromisoformat(
                train_data["actualPredictedTime"]
            ),
        }
        station, platform = (
            train_data["lastEventLocation"][:-11],
            train_data["lastEventLocation"][-1],
        )
        if station == "Monument":
            if platform in ("3", "4"):
                station = "Monument W-E"
            else:
                station = "Monument N-S"
        try:
            self.position = (
                self.event["lastEvent"],
                self.network.stations[station].platforms[platform],
            )
        except KeyError as e:
            print(station)
            print(platform)
            raise e

    @property
    def x(self):
        return self.position[1].x + self.OFFSETS[self.position[0]][self.d][0]

    @property
    def y(self):
        return self.position[1].y + self.OFFSETS[self.position[0]][self.d][1]

    @property
    def d(self):
        return self.position[1].d

    def arrival(self, platform):
        return self, self.arrivals[(platform.station, platform.number)]

    def __repr__(self):
        return f"Train {self.id}, {self.line} line towards {self.destination}, last reported {self.position[0]} {self.position[1]}"


class MetroMap:
    OFFSETS = {
        "N": [(0, 10), (0, -10), (-5, -5), (5, -5), (-24, 0)],
        "S": [(0, -10), (0, 10), (-5, 5), (5, 5), (8, 0)],
        "E": [(-10, 0), (10, 0), (5, 5), (5, -5), (-16, -12)],
        "W": [(10, 0), (-10, 0), (-5, 5), (-5, -5), (0, 5)],
        "U": [(5, 8), (-6, -9), (-6, -1), (0, -5), (-8, 8)],
        "D": [(-6, -9), (5, 8), (6, 1), (0, 5), (8, 8)],
    }

    def __init__(self):
        self.trains = []

    def add_train(self, name, position, direction, colour="red"):
        self.trains.append(
            {
                "name": name,
                "position": position,
                "direction": direction,
                "colour": colour,
            }
        )

    def arrow_parts(self, position, os):
        parts = []
        parts.append(
            (
                (position[0] + os[0][0], position[1] + os[0][1]),
                (position[0] + os[1][0], position[1] + os[1][1]),
            )
        )
        parts.append(
            (
                (position[0] + os[1][0], position[1] + os[1][1]),
                (position[0] + os[2][0], position[1] + os[2][1]),
            )
        )
        parts.append(
            (
                (position[0] + os[1][0], position[1] + os[1][1]),
                (position[0] + os[3][0], position[1] + os[3][1]),
            )
        )
        return parts

    def save(self):
        with Image.open("map.png") as im:
            draw = ImageDraw.Draw(im)
            for train in self.trains:
                os = self.OFFSETS[train["direction"]]
                for f, t in self.arrow_parts(train["position"], os):
                    draw.line([f, t], fill=train["colour"], width=4)
                draw.text(
                    (train["position"][0] + os[4][0], train["position"][1] + os[4][1]),
                    train["name"],
                    fill=train["colour"],
                )
            draw.text(
                (200, 400),
                f"Last Updated {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                fill="black",
            )
            im.save("map-annotated.png")


class MetroAPI:
    API_BASE = "https://metro-rti.nexus.org.uk/api/"

    def __init__(self):
        pass

    def get_json(self, path):
        r = requests.get(f"{self.API_BASE}{path}")
        return r.json()

    def get_times(self, station_code, platform_number):
        return self.get_json(f"times/{station_code}/{platform_number}")

    def get_stations(self):
        with open("stations.json") as f:
            return json.load(f)
        # return self.get_json('stations')

    async def async_get_stations(self):
        async with aiofiles.open("stations.json") as f:
            content = await f.read()
        return json.loads(content)

    def get_platforms(self):
        with open("platforms.json") as f:
            return json.load(f)
        # return self.get_json('stations/platforms')

    async def async_get_platforms(self):
        async with aiofiles.open("platforms.json") as f:
            content = await f.read()
        return json.loads(content)


def main():
    # requests_cache.install_cache('metro_cache')
    m = MetroNetwork()
    m.update()
    m.print_map()


if __name__ == "__main__":
    main()
