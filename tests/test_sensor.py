"""Test Malaysia Air Quality sensors."""
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry


async def test_sensor_values(hass: HomeAssistant, mock_config_entry: MockConfigEntry) -> None:
    """Test sensor states and attributes."""
    mock_config_entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    # Check API sensor
    state_api = hass.states.get("sensor.apims_cheras_air_pollutant_index")
    assert state_api is not None
    assert state_api.state == "52.0"

    # Check Status sensor
    state_status = hass.states.get("sensor.apims_cheras_status")
    assert state_status is not None
    assert state_status.state == "moderate"

    # Check Dominant Pollutant sensor
    state_pollutant = hass.states.get("sensor.apims_cheras_dominant_pollutant")
    assert state_pollutant is not None
    assert state_pollutant.state == "PM2.5"

    # Check PM2.5 sensor
    state_pm25 = hass.states.get("sensor.apims_cheras_pm2_5")
    assert state_pm25 is not None
    assert state_pm25.state == "15.2"
