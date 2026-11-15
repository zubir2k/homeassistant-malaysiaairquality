"""Base entity for Malaysia Air Quality Status."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from . import AirQualityConfigEntry
from .const import CONF_STATION, DOMAIN, STATION_NEAREST
from .coordinator import AirQualityCoordinator

ATTRIBUTION = "Data provided by Department of Environment Malaysia (APIMS)"


def entry_label(entry: AirQualityConfigEntry) -> str:
    """Return 'Home' for nearest mode or the entry title for a fixed station."""
    return "Home" if entry.data.get(CONF_STATION) == STATION_NEAREST else entry.title


def make_entity_id(entry: AirQualityConfigEntry, key: str) -> str:
    """Fixed ids, independent of device/entry renames: sensor.apims_<home|station>_<key>."""
    return f"sensor.apims_{slugify(entry_label(entry))}_{key}"


class MalaysiaAirQualityEntity(CoordinatorEntity[AirQualityCoordinator]):
    """Common base class for Malaysia Air Quality entities."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION

    def __init__(
        self, coordinator: AirQualityCoordinator, entry: AirQualityConfigEntry
    ) -> None:
        """Initialize the base entity."""
        super().__init__(coordinator)
        label = entry_label(entry)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"apims_{entry.unique_id or entry.entry_id}")},
            name=f"APIMS {label}",
            manufacturer="Jabatan Alam Sekitar (DOE)",
            model="APIMS",
            entry_type=DeviceEntryType.SERVICE,
            configuration_url="https://eqms.doe.gov.my/APIMS/main",
        )
