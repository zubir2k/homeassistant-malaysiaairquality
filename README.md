![APIMS](custom_components/malaysia_airquality/brand/logo.png)

[![GitHub Repo stars](https://img.shields.io/github/stars/zubir2k/homeassistant-malaysiaairquality?style=social)](https://github.com/zubir2k/homeassistant-malaysiaairquality/stargazers)
[![hacs_badge](https://img.shields.io/badge/HACS-Integration-41BDF5.svg)](https://github.com/hacs/integration)
![GitHub all releases](https://img.shields.io/badge/dynamic/json?color=41BDF5&logo=home-assistant&label=Download%20Count&suffix=%20installs&cacheSeconds=15600&url=https://analytics.home-assistant.io/custom_integrations.json&query=$.malaysia_airquality.total)
[![Buy](https://img.shields.io/badge/Belanja-Coffee-yellow.svg)](https://zubirco.de/buymecoffee)
[![GitHub Release](https://img.shields.io/github/release/zubir2k/homeassistant-malaysiaairquality.svg)](https://github.com/zubir2k/homeassistant-malaysiaairquality/releases/)

Air Pollutant Index (API / IPU) from the Department of Environment Malaysia's **APIMS** network in Home Assistant. It covers 66 fixed stations plus mobile units, refreshed hourly by DOE.

## Features
- One request covers every station; no API key needed
- **Home (auto)** mode follows your Home zone, or pin any station (the list is sorted by distance)
- Sensors: Air Pollutant Index (`aqi`), Status (Good to Hazardous), Dominant Pollutant, Station, Last Reading, Station Distance (disabled by default)
- Built-in map card coloured by API band
- English and Bahasa Melayu translations

## Installation

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=malaysia_airquality)

HACS → Custom repositories → `zubir2k/homeassistant-malaysiaairquality` (Integration), install, then restart.

## Setup
Settings → Devices & Services → Add Integration → **Malaysia Air Quality Status**, then pick *Home (auto)* or a station. Add more stations by adding the integration again.

## Map card
The integration ships its own Lovelace card, so there's nothing extra to install. It shows every station, coloured by the official DOE band (blue, green, yellow, orange, red), with your Home marked and your selected station outlined.

<img width="511" height="452" alt="image" src="https://github.com/user-attachments/assets/4b115e7d-6e56-4fa0-aad7-6c90711fe462" />

```yaml
type: custom:malaysia-airquality-card
entity: sensor.apims_home_all_stations
title: Jerebu
height: 420        # px
zoom: 9
show_mobile: true
show_legend: true
dark_mode: auto    # auto | true | false
language: auto     # auto | en | ms
# center: [3.139, 101.687]   # defaults to Home
```
The `All Stations` sensor feeds the card. Its station list is kept out of the recorder, so it doesn't bloat your database. Map tiles come from OpenStreetMap, so the card needs internet; Leaflet itself is bundled.

## Gauge card
A stock gauge in the DOE colours. The band name shows in place of the number; drop the `label` lines to show the reading instead.

<img width="511" height="211" alt="image" src="https://github.com/user-attachments/assets/b80c1b7f-77ab-49ce-8feb-2f5daba170b6" />


```yaml
type: gauge
entity: sensor.apims_home_air_pollutant_index
name: Air Quality Status Indication
min: 0
max: 500
needle: true
segments:
  - from: 0
    color: '#1E5AC8'
    label: Good
  - from: 51
    color: '#2E9E44'
    label: Moderate
  - from: 101
    color: '#F2C200'
    label: Unhealthy
  - from: 201
    color: '#F07C00'
    label: Very Unhealthy
  - from: 301
    color: '#D0021B'
    label: Hazardous
```

## Example: haze automation
```yaml
alias: Haze - protect the house
triggers:
  - trigger: numeric_state
    entity_id: sensor.apims_home_air_pollutant_index
    above: 100
actions:
  - action: fan.turn_on
    target: {entity_id: fan.living_room_purifier}
    data: {percentage: 100}
  - action: cover.close_cover
    target: {entity_id: cover.living_room_windows}
  - action: notify.notify
    data:
      title: "Jerebu: API {{ states('sensor.apims_home_air_pollutant_index') }}"
      message: "{{ state_attr('sensor.apims_home_air_pollutant_index','station') }} is Unhealthy. Purifier on, windows closed."
```

## Categories (DOE)
| API | Status |
|---|---|
| 0–50 | Good |
| 51–100 | Moderate |
| 101–200 | Unhealthy |
| 201–300 | Very Unhealthy |
| >300 | Hazardous |

## Notes
- The data is a 24-hour running average of the dominant pollutant, so polling more often than every 15–30 min gains nothing.
- APIMS encodes its timestamp as Malaysia time inside a UTC epoch; the integration corrects this.
- Unofficial. Data © Jabatan Alam Sekitar Malaysia.
