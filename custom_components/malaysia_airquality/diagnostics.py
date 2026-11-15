"""Diagnostics support for Malaysia Air Quality Status."""
from __future__ import annotations

from dataclasses import asdict
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from . import AirQualityConfigEntry

TO_REDACT_NEAREST = {"latitude", "longitude", "distance_km"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: AirQualityConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data
    data = coordinator.data

    station_dict = asdict(data.station)
    if station_dict.get("updated") is not None:
        station_dict["updated"] = data.station.updated.isoformat()

    diag: dict[str, Any] = {
        "entry": {
            "title": entry.title,
            "data": dict(entry.data),
            "options": dict(entry.options),
        },
        "follows_home": coordinator.follows_home,
        "station": station_dict,
        "distance_km": data.distance_km,
        "total_stations": len(data.stations),
    }

    if coordinator.follows_home:
        return async_redact_data(diag, TO_REDACT_NEAREST)
    return diag
