"""Constants for Malaysia Air Quality Status."""
from __future__ import annotations

from datetime import timedelta
from zoneinfo import ZoneInfo

DOMAIN = "malaysia_airquality"
VERSION = "0.2.5"
CARD_URL = f"/{DOMAIN}"

API_URL = (
    "https://eqms.doe.gov.my/api3/publicmapproxy/PUBLIC_DISPLAY/"
    "CAQM_MCAQM_Current_Reading/MapServer/0/query"
)
API_PARAMS = {
    "f": "json",
    "outFields": "*",
    "returnGeometry": "false",
    "where": "1=1",
}
USER_AGENT = "HomeAssistant-MalaysiaAirQuality/0.1 (+https://github.com/zubir2k/homeassistant-malaysiaairquality)"

# APIMS stores DATETIME as Malaysia wall-clock time encoded as a UTC epoch.
MYT = ZoneInfo("Asia/Kuala_Lumpur")

CONF_STATION = "station"
CONF_SCAN_INTERVAL = "scan_interval"
STATION_NEAREST = "nearest"  # follow zone.home

DEFAULT_SCAN_INTERVAL = 30  # minutes; API is an hourly 24h running average
MIN_SCAN_INTERVAL = 15
SCAN_INTERVAL = timedelta(minutes=DEFAULT_SCAN_INTERVAL)

# DOE API categories (doe.gov.my)
CATEGORIES = ["good", "moderate", "unhealthy", "very_unhealthy", "hazardous", "unavailable"]


def category_for(api: float | None) -> str:
    """Map an API value to its DOE category."""
    if api is None or api < 0:
        return "unavailable"
    if api <= 50:
        return "good"
    if api <= 100:
        return "moderate"
    if api <= 200:
        return "unhealthy"
    if api <= 300:
        return "very_unhealthy"
    return "hazardous"
