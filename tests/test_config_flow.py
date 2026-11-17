"""Test config flow for Malaysia Air Quality."""
from unittest.mock import patch
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.malaysia_airquality.api import ApimsError
from custom_components.malaysia_airquality.const import CONF_STATION, DOMAIN, STATION_NEAREST


async def test_flow_nearest(hass: HomeAssistant) -> None:
    """Test user selecting nearest station."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_STATION: STATION_NEAREST},
    )
    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Home"
    assert result2["data"] == {CONF_STATION: STATION_NEAREST}


async def test_flow_specific_station(hass: HomeAssistant) -> None:
    """Test user selecting a specific station."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_STATION: "CAQM001"},
    )
    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Cheras"
    assert result2["data"] == {CONF_STATION: "CAQM001"}


async def test_flow_duplicate_abort(hass: HomeAssistant, mock_config_entry) -> None:
    """Test duplicate configuration aborts."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_STATION: "CAQM001"},
    )
    assert result2["type"] is FlowResultType.ABORT
    assert result2["reason"] == "already_configured"


async def test_flow_cannot_connect(hass: HomeAssistant) -> None:
    """Test handling connection failure."""
    with patch(
        "custom_components.malaysia_airquality.config_flow.async_fetch_stations",
        side_effect=ApimsError("Timeout"),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] is FlowResultType.FORM
        assert result["errors"] == {"base": "cannot_connect"}
