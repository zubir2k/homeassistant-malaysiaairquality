"""Fixtures for Malaysia Air Quality tests."""
from __future__ import annotations

import sys
from unittest.mock import patch
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.malaysia_airquality.const import API_URL, DOMAIN

if sys.platform == "win32":
    try:
        import pytest_socket
        def _win_disable_socket(allow_unix_socket=False):
            pass
        pytest_socket.disable_socket = _win_disable_socket
    except ImportError:
        pass


MOCK_FEATURES = [
    {
        "attributes": {
            "STATION_ID": "CAQM001",
            "STATION_LOCATION": "Cheras, Kuala Lumpur",
            "PLACE": "Kuala Lumpur",
            "STATE_NAME": "W.P. Kuala Lumpur",
            "REGION_NAME": "Central",
            "STATION_CATEGORY": "Urban",
            "LATITUDE": 3.106,
            "LONGITUDE": 101.725,
            "API": 52,
            "PARAM_SELECTED": "PM2.5",
            "CLASS": "Moderate",
            "DATETIME": 1731801600000,
            "PM25_CONC": 15.2,
            "PM10_CONC": 25.4,
        }
    },
    {
        "attributes": {
            "STATION_ID": "CAQM002",
            "STATION_LOCATION": "Putrajaya, W.P. PUTRAJAYA",
            "PLACE": "Putrajaya",
            "STATE_NAME": "W.P. Putrajaya",
            "REGION_NAME": "Central",
            "STATION_CATEGORY": "Urban",
            "LATITUDE": 2.926,
            "LONGITUDE": 101.696,
            "API": 45,
            "PARAM_SELECTED": "PM2.5",
            "CLASS": "Good",
            "DATETIME": 1731801600000,
            "PM25_CONC": 11.0,
            "PM10_CONC": 18.0,
        }
    },
]


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations in all tests."""
    yield


@pytest.fixture(autouse=True)
def no_http_server():
    """Card needs http/frontend; don't bind a port."""
    with patch("homeassistant.components.http.HomeAssistantHTTP.start"):
        yield


@pytest.fixture(autouse=True)
def mock_apims(aioclient_mock):
    """Mock APIMS endpoint returning test features."""
    aioclient_mock.get(
        API_URL,
        json={"features": MOCK_FEATURES},
    )
    return aioclient_mock


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Cheras",
        data={"station": "CAQM001"},
        entry_id="test_airquality_entry",
        unique_id="CAQM001",
    )


@pytest.fixture(autouse=True)
async def cleanup_entries(hass):
    """Ensure any loaded config entries are unloaded after each test."""
    yield
    for entry in list(hass.config_entries.async_entries()):
        if entry.state.loaded:
            await hass.config_entries.async_unload(entry.entry_id)
