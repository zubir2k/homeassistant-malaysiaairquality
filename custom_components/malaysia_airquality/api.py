"""Client for the DOE APIMS public ArcGIS layer."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
import math

import aiohttp

from .const import API_PARAMS, API_URL, MYT, USER_AGENT


class ApimsError(Exception):
    """Raised when APIMS cannot be read."""


@dataclass(frozen=True)
class Station:
    station_id: str
    name: str
    place: str | None
    state: str | None
    region: str | None
    category: str | None  # Urban / Sub Urban / Rural / Industry / Mobile
    latitude: float
    longitude: float
    api: float | None
    pollutant: str | None
    api_class: str | None
    updated: datetime | None

    @property
    def mobile(self) -> bool:
        return self.station_id.startswith("MCAQM")


def _parse_time(ms: int | None) -> datetime | None:
    """DATETIME is MYT wall-clock stored as a UTC epoch: reinterpret it."""
    if ms is None:
        return None
    naive = datetime.fromtimestamp(ms / 1000, timezone.utc).replace(tzinfo=None)
    return naive.replace(tzinfo=MYT)


def _parse(attrs: dict) -> Station | None:
    try:
        lat = float(attrs["LATITUDE"])
        lon = float(attrs["LONGITUDE"])
    except (KeyError, TypeError, ValueError):
        return None
    api = attrs.get("API")
    return Station(
        station_id=str(attrs.get("STATION_ID", "")).strip(),
        name=(attrs.get("STATION_LOCATION") or "").strip(),
        place=(attrs.get("PLACE") or "").replace("\u00a0", " ").strip() or None,
        state=attrs.get("STATE_NAME"),
        region=attrs.get("REGION_NAME"),
        category=(attrs.get("STATION_CATEGORY") or "").strip() or None,
        latitude=lat,
        longitude=lon,
        api=float(api) if api is not None and api >= 0 else None,
        pollutant=attrs.get("PARAM_SELECTED"),
        api_class=attrs.get("CLASS"),
        updated=_parse_time(attrs.get("DATETIME")),
    )


async def async_fetch_stations(session: aiohttp.ClientSession) -> dict[str, Station]:
    """Fetch every station's current reading in one call."""
    try:
        async with asyncio.timeout(30):
            resp = await session.get(API_URL, params=API_PARAMS, headers={"User-Agent": USER_AGENT})
            resp.raise_for_status()
            payload = await resp.json(content_type=None)
    except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as err:
        raise ApimsError(f"APIMS request failed: {err}") from err
    if "error" in payload:
        raise ApimsError(f"APIMS returned an error: {payload['error']}")
    stations: dict[str, Station] = {}
    for feat in payload.get("features", []):
        st = _parse(feat.get("attributes") or {})
        if st and st.station_id:
            stations[st.station_id] = st
    if not stations:
        raise ApimsError("APIMS returned no stations")
    return stations


def distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Haversine distance."""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def nearest(stations: dict[str, Station], lat: float, lon: float, include_mobile: bool = False) -> Station:
    # Skip stations that are offline (no API reading) so Home always has a number.
    pool = [s for s in stations.values() if (include_mobile or not s.mobile) and s.api is not None]
    pool = pool or [s for s in stations.values() if include_mobile or not s.mobile] or list(stations.values())
    return min(pool, key=lambda s: distance_km(lat, lon, s.latitude, s.longitude))


def short_name(name: str) -> str:
    """'Putrajaya, W.P. PUTRAJAYA' -> 'Putrajaya' (keeps entity ids short)."""
    return name.split(",")[0].strip() or name
