"""Sensors for Malaysia Air Quality Status."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass, SensorEntity, SensorEntityDescription, SensorStateClass,
)
from homeassistant.const import (
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER, EntityCategory, UnitOfLength,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import AirQualityConfigEntry
from .const import CATEGORIES, category_for
from .coordinator import AirQualityCoordinator, AirQualityData
from .entity import MalaysiaAirQualityEntity, make_entity_id

PARALLEL_UPDATES = 0


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
    "pm25": "pm2_5",
    "pm10": "pm10",
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
        key="pm25",
        translation_key="pm25",
        device_class=SensorDeviceClass.PM25,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        suggested_display_precision=1,
        value_fn=lambda d: d.station.pm25,
    ),
    AQSensorDescription(
        key="pm10",
        translation_key="pm10",
        device_class=SensorDeviceClass.PM10,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        suggested_display_precision=1,
        value_fn=lambda d: d.station.pm10,
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
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.station.name,
    ),
    AQSensorDescription(
        key="distance",
        translation_key="distance",
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda d: d.distance_km,
    ),
    AQSensorDescription(
        key="updated",
        translation_key="updated",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.station.updated,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: AirQualityConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    entities: list[SensorEntity] = [AQSensor(coordinator, entry, desc) for desc in SENSORS]
    entities.append(AllStationsSensor(coordinator, entry))
    async_add_entities(entities)


class AQSensor(MalaysiaAirQualityEntity, SensorEntity):
    entity_description: AQSensorDescription

    def __init__(self, coordinator: AirQualityCoordinator, entry: AirQualityConfigEntry,
                 description: AQSensorDescription) -> None:
        super().__init__(coordinator, entry)
        self.entity_description = description
        self._attr_unique_id = f"apims_{entry.unique_id}_{description.key}"
        self.entity_id = make_entity_id(entry, ENTITY_KEYS[description.key])

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


class AllStationsSensor(MalaysiaAirQualityEntity, SensorEntity):
    """Every APIMS station in one entity, for the map card. Not written to history."""

    _attr_translation_key = "stations"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _unrecorded_attributes = frozenset({"stations", "selected"})

    def __init__(self, coordinator: AirQualityCoordinator, entry: AirQualityConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"apims_{entry.unique_id}_stations"
        self.entity_id = make_entity_id(entry, "all_stations")

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
