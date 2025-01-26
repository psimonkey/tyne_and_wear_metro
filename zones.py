import json

with open("stations.json") as f:
    stations = json.load(f)

with open("platforms.json") as f:
    platforms = json.load(f)


for code, data in platforms.items():
    if code != "MTW":
        if code == "MTS":
            name = "Monument"
        else:
            name = stations[code]
        print(f"""- name: {name} Metro Station
  latitude: {data[0]["coordinates"]["latitude"]}
  longitude: {data[0]["coordinates"]["longitude"]}
  radius: 70
  passive: true
  icon: mdi:alpha-m-box-outline
""")

for code, data in platforms.items():
    if code != "MTW":
        if code == "MTS":
            name = "Monument"
        else:
            name = stations[code]
        print(f"""- name: {name} Metro Station
  latitude: {data[0]["coordinates"]["latitude"]}
  longitude: {data[0]["coordinates"]["longitude"]}
  radius: 70
  passive: true
  icon: mdi:alpha-m-box-outline
""")


print("""input_select:
  show_metro_station_simon_key:
    name: Show Metro Station Simon Key
    initial: Nearest
    icon: mdi:alpha-m-box-outline
    options:
      - Nearest""")
for code, data in platforms.items():
    if code != "MTW":
        if code == "MTS":
            name = "Monument"
        else:
            name = stations[code]
        print(f"      - {name}")
