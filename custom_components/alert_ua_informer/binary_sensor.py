"""Binary sensor platform."""
from datetime import UTC, datetime, timedelta

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_CITY_NAME, DOMAIN, MAX_AGE_MINUTES
from .coordinator import EventFinderDataUpdateCoordinator
from .entity import EventFinderEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set binary sensors."""

    city = entry.data[CONF_CITY_NAME]
    coordinator: EventFinderDataUpdateCoordinator = entry.runtime_data.coordinator

    actions = coordinator.actions
    for entity_name in actions:
        sensor = EventFinderBinarySensor(hass, coordinator, city, entity_name)
        async_add_entities([sensor])

class EventFinderBinarySensor(EventFinderEntity, BinarySensorEntity):
    """Binary sensor: True when threat is active and official alarm is on."""

    _attr_device_class = BinarySensorDeviceClass.SAFETY

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: EventFinderDataUpdateCoordinator,
        city: str,
        threat_key: str,
    ) -> None:
        """Initialize."""

        self.hass = hass
        self._city = city
        self._threat_key = threat_key

        city_slug = city.lower().replace(" ", "_")
        self._attr_unique_id = f"{DOMAIN}_{city_slug}_{threat_key}"
        self._attr_name = (
            f"{city} {threat_key.capitalize()}"
        )
        self.entity_id = f"binary_sensor.{DOMAIN}_{city_slug}_{threat_key}"

        self._attr_is_on = False

        super().__init__(coordinator, city_slug, threat_key)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update sensor with latest data from coordinator."""

        data = self.coordinator.data
        if not data:
            self._attr_is_on = False
            self.async_write_ha_state()
            return

        ts = data.get_ts(self._threat_key, None)
        if ts is None:
            self._attr_is_on = False
            self.async_write_ha_state()
            return

        self._attr_is_on = (datetime.now(UTC) - ts) < timedelta(minutes=MAX_AGE_MINUTES)

        self.async_write_ha_state()

    @property
    def extra_state_attributes(self):
        """Return the extra state attributes."""
        # Add any additional attributes you want on your sensor.
        attrs = {}

        data = self.coordinator.data
        if data:
            attrs["seen"] = data.get_ts(self._threat_key, None)
            attrs["debug_info"] = data.debug_info.get(f"{self._threat_key}", "N/A")
        return attrs
