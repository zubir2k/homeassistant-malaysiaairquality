"""Re-export apims library objects with integration-specific helpers."""
from __future__ import annotations

import aiohttp
from apims import (
    ApimsClient,
    ApimsConnectionError,
    ApimsError,
    Station,
    distance_km,
)

__all__ = [
    "ApimsClient",
    "ApimsConnectionError",
    "ApimsError",
    "Station",
    "async_fetch_stations",
    "distance_km",
    "nearest",
    "short_name",
]


async def async_fetch_stations(session: aiohttp.ClientSession) -> dict[str, Station]:
    """Fetch every station's current reading using ApimsClient."""
    client = ApimsClient(session=session)
    return await client.async_get_stations()


def nearest(
    stations: dict[str, Station],
    lat: float,
    lon: float,
    include_mobile: bool = False,
) -> Station:
    """Find the nearest active station to coordinates."""
    pool = [
        s
        for s in stations.values()
        if (include_mobile or not s.mobile) and s.api is not None
    ]
    pool = (
        pool
        or [s for s in stations.values() if include_mobile or not s.mobile]
        or list(stations.values())
    )
    return min(pool, key=lambda s: distance_km(lat, lon, s.latitude, s.longitude))


def short_name(name: str) -> str:
    """'Putrajaya, W.P. PUTRAJAYA' -> 'Putrajaya' (keeps entity ids short)."""
    return name.split(",")[0].strip() or name
