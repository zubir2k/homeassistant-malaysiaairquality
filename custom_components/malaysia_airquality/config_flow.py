"""Config flow: nearest-to-home or a fixed station, picked from the live feed."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    NumberSelector, NumberSelectorConfig, NumberSelectorMode,
    SelectOptionDict, SelectSelector, SelectSelectorConfig, SelectSelectorMode,
)

from .api import ApimsError, Station, async_fetch_stations, distance_km, short_name
from .const import (
    CONF_SCAN_INTERVAL, CONF_STATION, DEFAULT_SCAN_INTERVAL, DOMAIN, MIN_SCAN_INTERVAL, STATION_NEAREST,
)

_LOGGER = logging.getLogger(__name__)


class MalaysiaAirQualityFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._stations: dict[str, Station] = {}

    async def _async_load_stations(self, errors: dict[str, str]) -> None:
        if self._stations:
            return
        try:
            self._stations = await async_fetch_stations(async_get_clientsession(self.hass))
        except ApimsError:
            errors["base"] = "cannot_connect"
        except Exception:  # noqa: BLE001
            _LOGGER.exception("Unexpected error fetching APIMS stations")
            errors["base"] = "unknown"

    def _build_schema(self, default_station: str) -> vol.Schema:
        lat, lon = self.hass.config.latitude, self.hass.config.longitude
        has_coords = lat is not None and lon is not None
        if has_coords:
            ranked = sorted(
                self._stations.values(),
                key=lambda s: distance_km(lat, lon, s.latitude, s.longitude),
            )
        else:
            ranked = sorted(self._stations.values(), key=lambda s: s.name)

        options = [SelectOptionDict(value=STATION_NEAREST, label="Home (auto, nearest station)")]
        for s in ranked:
            dist_part = (
                f" ({distance_km(lat, lon, s.latitude, s.longitude):.0f} km)"
                if has_coords
                else ""
            )
            mobile_part = " [mobile]" if s.mobile else ""
            options.append(
                SelectOptionDict(
                    value=s.station_id,
                    label=f"{s.name}{dist_part}{mobile_part}",
                )
            )
        return vol.Schema({
            vol.Required(CONF_STATION, default=default_station): SelectSelector(
                SelectSelectorConfig(options=options, mode=SelectSelectorMode.DROPDOWN)
            )
        })

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        await self._async_load_stations(errors)

        if user_input is not None and not errors:
            station = user_input[CONF_STATION]
            if station != STATION_NEAREST and station not in self._stations:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(station)
                self._abort_if_unique_id_configured()
                title = (
                    "Home"
                    if station == STATION_NEAREST
                    else short_name(self._stations[station].name)
                )
                return self.async_create_entry(title=title, data={CONF_STATION: station})

        return self.async_show_form(
            step_id="user",
            data_schema=self._build_schema(STATION_NEAREST),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        reconfigure_entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        await self._async_load_stations(errors)

        if user_input is not None and not errors:
            station = user_input[CONF_STATION]
            if station != STATION_NEAREST and station not in self._stations:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(station)
                self._abort_if_unique_id_configured()
                title = (
                    "Home"
                    if station == STATION_NEAREST
                    else short_name(self._stations[station].name)
                )
                return self.async_update_reload_and_abort(
                    reconfigure_entry,
                    unique_id=station,
                    title=title,
                    data_updates={CONF_STATION: station},
                )

        current_station = reconfigure_entry.data.get(CONF_STATION, STATION_NEAREST)
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self._build_schema(current_station),
            errors=errors,
        )

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
