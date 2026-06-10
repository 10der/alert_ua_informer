"""Sensor platform: last message per channel."""

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTRIBUTION,
    CHAN_NAME,
    CHAN_SLUG,
    CONF_CITY_NAME,
    DEVICE_NAME,
    DOMAIN,
)
from .coordinator import EventFinderDataUpdateCoordinator

# Home Assistant limits state values to 255 characters
STATE_MAX_LEN = 255


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up last-message sensors, one per channel."""

    city = entry.data[CONF_CITY_NAME]
    coordinator: EventFinderDataUpdateCoordinator = entry.runtime_data.coordinator

    entities = [
        LastMessageSensor(coordinator, city, ch[CHAN_SLUG], ch.get(CHAN_NAME, ch[CHAN_SLUG]))
        for ch in coordinator.channels
    ]
    async_add_entities(entities)


class LastMessageSensor(
    CoordinatorEntity[EventFinderDataUpdateCoordinator], SensorEntity
):
    """Sensor whose state is the last message text of a channel."""

    _attr_attribution = ATTRIBUTION
    _attr_icon = "mdi:message-text"

    def __init__(
        self,
        coordinator: EventFinderDataUpdateCoordinator,
        city: str,
        slug: str,
        friendly_name: str,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)

        self._slug = slug

        city_slug = city.lower().replace(" ", "_")
        self._attr_unique_id = f"{DOMAIN}_{city_slug}_last_message_{slug}"
        self._attr_name = f"{friendly_name} last message"
        self.entity_id = f"sensor.{DOMAIN}_{city_slug}_last_message_{slug}"

        self._attr_device_info = DeviceInfo(
            name=DEVICE_NAME,
            manufacturer="UA",
            sw_version="1.0",
            identifiers={
                (
                    coordinator.config_entry.domain,
                    coordinator.config_entry.entry_id,
                ),
            },
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update state from coordinator."""
        self.async_write_ha_state()

    @property
    def native_value(self) -> str | None:
        """Return the last message text (truncated to HA state limit)."""
        data = self.coordinator.data
        if not data:
            return None

        msg = data.get_last_message(self._slug)
        if msg is None:
            return None

        text = msg.text
        if len(text) > STATE_MAX_LEN:
            return text[: STATE_MAX_LEN - 1] + "…"
        return text

    @property
    def extra_state_attributes(self):
        """Return full message and metadata."""
        data = self.coordinator.data
        if not data:
            return {}

        msg = data.get_last_message(self._slug)
        if msg is None:
            return {}

        return {
            "channel": self._slug,
            "full_text": msg.text,
            "msg_id": msg.msg_id,
            "received": msg.received,
            "matched": msg.matched,
        }
