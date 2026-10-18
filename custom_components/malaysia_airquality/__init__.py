"""Malaysia Air Quality Status: DOE APIMS Air Pollutant Index for Home Assistant."""
from __future__ import annotations

from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import CARD_URL, DOMAIN, VERSION
from .coordinator import AirQualityCoordinator

PLATFORMS = [Platform.SENSOR]
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Serve the bundled Lovelace card, so no separate HACS plugin is needed."""
    await hass.http.async_register_static_paths(
        [StaticPathConfig(CARD_URL, str(Path(__file__).parent / "frontend"), True)]
    )
    add_extra_js_url(hass, f"{CARD_URL}/malaysia-airquality-card.js?v={VERSION}")
    return True

type AirQualityConfigEntry = ConfigEntry[AirQualityCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: AirQualityConfigEntry) -> bool:
    coordinator = AirQualityCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    entry.async_on_unload(entry.add_update_listener(_async_reload))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: AirQualityConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_reload(hass: HomeAssistant, entry: AirQualityConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
