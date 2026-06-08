"""BlueprintEntity class."""

from propcache.api import cached_property

from homeassistant.components.binary_sensor import ENTITY_ID_FORMAT
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import generate_entity_id
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DEVICE_NAME
from .coordinator import EventFinderDataUpdateCoordinator


class EventFinderEntity(CoordinatorEntity[EventFinderDataUpdateCoordinator]):
    """BlueprintEntity class."""

    _attr_attribution = ATTRIBUTION

    def __init__(
        self,
        coordinator: EventFinderDataUpdateCoordinator,
        city_slug: str,
        threat_key: str,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)

        self._attr_unique_id = generate_entity_id(
            ENTITY_ID_FORMAT, city_slug + "_" + threat_key, hass=self.hass
        )

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

    @cached_property
    def available(self) -> bool:  # type: ignore
        """Entity gets data from ezviz API so always available."""
        return True
