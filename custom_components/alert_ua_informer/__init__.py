"""Alert UA Informer integration for Home Assistant."""

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import (
    EventFinderConfigEntry,
    EventFinderDataUpdateCoordinator,
    RuntimeData,
)

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EventFinderConfigEntry,
) -> bool:
    """Set up this integration using UI."""

    coordinator = EventFinderDataUpdateCoordinator(
        hass=hass,
        config_entry=entry,)

    entry.runtime_data = RuntimeData(
        coordinator=coordinator,
    )

    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: EventFinderConfigEntry,
) -> bool:
    """Handle removal of an entry."""

    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(
    hass: HomeAssistant,
    entry: EventFinderConfigEntry,
) -> None:
    """Reload config entry."""

    await hass.config_entries.async_reload(entry.entry_id)
