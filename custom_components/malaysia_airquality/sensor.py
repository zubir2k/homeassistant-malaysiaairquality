"""Sensors for Malaysia Air Quality Status."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass, SensorEntity, SensorEntityDescription, SensorStateClass,
)
from homeassistant.const import UnitOfLength
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from . import AirQualityConfigEntry
from .const import CATEGORIES, CONF_STATION, DOMAIN, STATION_NEAREST, category_for
from .coordinator import AirQualityCoordinator, AirQualityData


@dataclass(frozen=True, kw_only=True)
class AQSensorDescription(SensorEntityDescription):
    value_fn: Callable[[AirQualityData], Any]


# object-id suffix per sensor (English, so ids stay stable whatever the UI language)
ENTITY_KEYS = {
    "api": "air_pollutant_index",
    "status": "status",
    "pollutant": "dominant_pollutant",
    "station": "station",
    "distance": "station_distance",
    "updated": "last_reading",
}

SENSORS: tuple[AQSensorDescription, ...] = (
    AQSensorDescription(
        key="api",
        translation_key="api",
        device_class=SensorDeviceClass.AQI,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.station.api,
    ),
    AQSensorDescription(
        key="status",
        translation_key="status",
        device_class=SensorDeviceClass.ENUM,
        options=CATEGORIES,
        value_fn=lambda d: category_for(d.station.api),
    ),
    AQSensorDescription(
        key="pollutant",
        translation_key="pollutant",
        value_fn=lambda d: d.station.pollutant,
    ),
    AQSensorDescription(
        key="station",
        translation_key="station",
        value_fn=lambda d: d.station.name,
    ),
    AQSensorDescription(
        key="distance",
        translation_key="distance",
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        entity_registry_enabled_default=False,
        value_fn=lambda d: d.distance_km,
    ),
    AQSensorDescription(
        key="updated",
        translation_key="updated",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda d: d.station.updated,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: AirQualityConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    entities: list[SensorEntity] = [AQSensor(coordinator, entry, desc) for desc in SENSORS]
    entities.append(AllStationsSensor(coordinator, entry))
    async_add_entities(entities)


def _label(entry: AirQualityConfigEntry) -> str:
    return "Home" if entry.data.get(CONF_STATION) == STATION_NEAREST else entry.title


def _entity_id(entry: AirQualityConfigEntry, key: str) -> str:
    """Fixed ids, independent of device/entry renames: sensor.apims_<home|station>_<key>."""
    return f"sensor.apims_{slugify(_label(entry))}_{key}"


def _device_info(entry: AirQualityConfigEntry) -> DeviceInfo:
    label = _label(entry)
    return DeviceInfo(
        identifiers={(DOMAIN, f"apims_{entry.unique_id or entry.entry_id}")},
        name=f"APIMS {label}",
        manufacturer="Jabatan Alam Sekitar (DOE)",
        model="APIMS",
        entry_type=DeviceEntryType.SERVICE,
            configuration_url="https://eqms.doe.gov.my/APIMS/main",
    )


class AQSensor(CoordinatorEntity[AirQualityCoordinator], SensorEntity):
    _attr_has_entity_name = True
    _attr_attribution = "Data provided by Department of Environment Malaysia (APIMS)"
    entity_description: AQSensorDescription

    def __init__(self, coordinator: AirQualityCoordinator, entry: AirQualityConfigEntry,
                 description: AQSensorDescription) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"apims_{entry.unique_id}_{description.key}"
        self.entity_id = _entity_id(entry, ENTITY_KEYS[description.key])
        self._attr_device_info = _device_info(entry)

    @property
    def native_value(self) -> Any:
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self.entity_description.key != "api":
            return None
        st = self.coordinator.data.station
        return {
            "station_id": st.station_id,
            "station": st.name,
            "place": st.place,
            "state": st.state,
            "region": st.region,
            "station_category": st.category,
            "doe_class": st.api_class,
            "latitude": st.latitude,
            "longitude": st.longitude,
            "follows_home": self.coordinator.follows_home,
        }


class AllStationsSensor(CoordinatorEntity[AirQualityCoordinator], SensorEntity):
    """Every APIMS station in one entity, for the map card. Not written to history."""

    _attr_has_entity_name = True
    _attr_translation_key = "stations"
    _attr_icon = "mdi:map-marker-radius"
    _attr_attribution = "Data provided by Department of Environment Malaysia (APIMS)"
    _unrecorded_attributes = frozenset({"stations", "selected"})

    def __init__(self, coordinator: AirQualityCoordinator, entry: AirQualityConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"apims_{entry.unique_id}_stations"
        self.entity_id = _entity_id(entry, "all_stations")
        self._attr_device_info = _device_info(entry)

    @property
    def native_value(self) -> int:
        return len(self.coordinator.data.stations)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data
        return {
            "selected": data.station.station_id,
            # compact: [id, name, lat, lon, api, pollutant, updated_iso, mobile]
            "stations": [
                [
                    s.station_id,
                    s.name,
                    round(s.latitude, 5),
                    round(s.longitude, 5),
                    s.api,
                    s.pollutant,
                    s.updated.isoformat() if s.updated else None,
                    s.mobile,
                ]
                for s in data.stations.values()
            ],
        }
