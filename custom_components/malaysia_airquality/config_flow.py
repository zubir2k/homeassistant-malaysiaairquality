"""Config flow: nearest-to-home or a fixed station, picked from the live feed."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    NumberSelector, NumberSelectorConfig, NumberSelectorMode,
    SelectOptionDict, SelectSelector, SelectSelectorConfig, SelectSelectorMode,
)

from .api import ApimsError, async_fetch_stations, distance_km, short_name
from .const import (
    CONF_SCAN_INTERVAL, CONF_STATION, DEFAULT_SCAN_INTERVAL, DOMAIN, MIN_SCAN_INTERVAL, STATION_NEAREST,
)


class MalaysiaAirQualityFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._stations: dict = {}

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if not self._stations:
            try:
                self._stations = await async_fetch_stations(async_get_clientsession(self.hass))
            except ApimsError:
                errors["base"] = "cannot_connect"

        if user_input is not None and not errors:
            station = user_input[CONF_STATION]
            await self.async_set_unique_id(station)
            self._abort_if_unique_id_configured()
            title = "Home" if station == STATION_NEAREST else short_name(self._stations[station].name)
            return self.async_create_entry(title=title, data={CONF_STATION: station})

        lat, lon = self.hass.config.latitude, self.hass.config.longitude
        ranked = sorted(
            self._stations.values(), key=lambda s: distance_km(lat, lon, s.latitude, s.longitude)
        )
        options = [SelectOptionDict(value=STATION_NEAREST, label="Home (auto, nearest station)")] + [
            SelectOptionDict(
                value=s.station_id,
                label=f"{s.name} ({distance_km(lat, lon, s.latitude, s.longitude):.0f} km)"
                + (" [mobile]" if s.mobile else ""),
            )
            for s in ranked
        ]
        schema = vol.Schema({
            vol.Required(CONF_STATION, default=STATION_NEAREST): SelectSelector(
                SelectSelectorConfig(options=options, mode=SelectSelectorMode.DROPDOWN)
            )
        })
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(entry: ConfigEntry) -> OptionsFlow:
        return MalaysiaAirQualityOptions()


class MalaysiaAirQualityOptions(OptionsFlow):
    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        current = self.config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        schema = vol.Schema({
            vol.Required(CONF_SCAN_INTERVAL, default=current): NumberSelector(
                NumberSelectorConfig(min=MIN_SCAN_INTERVAL, max=180, step=5,
                                     unit_of_measurement="min", mode=NumberSelectorMode.BOX)
            )
        })
        return self.async_show_form(step_id="init", data_schema=schema)
