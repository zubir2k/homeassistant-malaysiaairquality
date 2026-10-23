"""Malaysia Air Quality Status: DOE APIMS Air Pollutant Index for Home Assistant."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .card_registration import async_register_card, async_unregister_card
from .const import DOMAIN
from .coordinator import AirQualityCoordinator

PLATFORMS = [Platform.SENSOR]
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Serve the bundled Lovelace card and register it for dashboards (runs once per HA start)."""
    await async_register_card(hass)
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


async def async_remove_entry(hass: HomeAssistant, entry: AirQualityConfigEntry) -> None:
    """Remove the card's dashboard resource when the last entry is deleted.

    Not done on unload: reloading an entry should not make the card disappear.
    """
    if not [e for e in hass.config_entries.async_entries(DOMAIN) if e.entry_id != entry.entry_id]:
        await async_unregister_card(hass)
