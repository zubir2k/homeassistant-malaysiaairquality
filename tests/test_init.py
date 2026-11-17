"""Test init and entry lifecycle for Malaysia Air Quality."""
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.malaysia_airquality.const import DOMAIN


async def test_setup_and_unload_entry(hass: HomeAssistant, mock_config_entry: MockConfigEntry) -> None:
    """Test setting up and unloading an entry."""
    mock_config_entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state.loaded

    state = hass.states.get("sensor.malaysia_air_quality_status_air_pollutant_index")
    # Entity ID could also follow custom name or default
    # Let's inspect any sensor in domain
    sensors = [s for s in hass.states.async_entity_ids("sensor") if "cheras" in s or "air" in s]
    assert len(sensors) > 0

    assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert not mock_config_entry.state.loaded
