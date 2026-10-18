"""Coordinator: one APIMS call per interval, resolved to the configured station."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ApimsError, Station, async_fetch_stations, distance_km, nearest
from .const import CONF_SCAN_INTERVAL, CONF_STATION, DEFAULT_SCAN_INTERVAL, DOMAIN, STATION_NEAREST

_LOGGER = logging.getLogger(__name__)


@dataclass
class AirQualityData:
    station: Station
    distance_km: float | None
    stations: dict[str, Station]


class AirQualityCoordinator(DataUpdateCoordinator[AirQualityData]):
    """Polls APIMS and picks one station."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        opts = {**entry.data, **entry.options}
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(minutes=opts.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)),
        )
        self.station_conf: str = opts.get(CONF_STATION, STATION_NEAREST)
        self._session = async_get_clientsession(hass)

    @property
    def follows_home(self) -> bool:
        return self.station_conf == STATION_NEAREST

    async def _async_update_data(self) -> AirQualityData:
        try:
            stations = await async_fetch_stations(self._session)
        except ApimsError as err:
            raise UpdateFailed(str(err)) from err

        lat, lon = self.hass.config.latitude, self.hass.config.longitude
        if self.follows_home:
            st = nearest(stations, lat, lon)
        else:
            st = stations.get(self.station_conf)
            if st is None:
                raise UpdateFailed(f"Station {self.station_conf} not in APIMS feed")
        dist = round(distance_km(lat, lon, st.latitude, st.longitude), 1) if lat and lon else None
        return AirQualityData(station=st, distance_km=dist, stations=stations)
