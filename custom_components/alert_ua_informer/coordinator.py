"""DataUpdateCoordinator."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .config_flow import CLEAR_ACTION, keywords_to_dict
from .const import (
    CHAN_LOCAL,
    CHAN_SLUG,
    CONF_CHANNELS,
    CONF_CITY_NAME,
    CONF_KEY_WORDS,
    DEFAULT_POLL_LOCAL,
    DOMAIN,
    LOGGER,
)
from .telegram_fetcher import ChannelMessage, KeywordMatcher, fetch_latest


@dataclass
class RuntimeData:
    """Class to hold data."""

    coordinator: DataUpdateCoordinator[EventFinderData]


type EventFinderConfigEntry = ConfigEntry[RuntimeData]


class EventFinderData:
    """Class to hold data retrieved from the API."""

    found: dict[str, datetime] = {}
    debug_info: dict[str, Any] = {}

    def get_ts(self, key: str, default: datetime | None = None) -> datetime | None:
        """Повертає час знайденої дії за ключем."""

        return self.found.get(key, default)


class EventFinderDataUpdateCoordinator(DataUpdateCoordinator[EventFinderData]):
    """Class to manage fetching data from the API."""

    def __init__(
        self, hass: HomeAssistant, config_entry: EventFinderConfigEntry
    ) -> None:
        """Initialize coordinator."""
        self.hass = hass
        self.config_entry = config_entry

        # Persisted found times by action key
        self._found: dict[str, datetime] = {}
        self._debug_info: dict[str, Any] = {}

        raw_keywords = config_entry.data.get(CONF_KEY_WORDS, [])

        keywords = keywords_to_dict(raw_keywords)
        self.actions = [key for key in keywords if key != CLEAR_ACTION]

        self._matcher = KeywordMatcher(keywords)

        # Per-channel last message ID cache
        self._last_ids: dict[str, int] = {}

        # Shared aiohttp session
        self._session = async_get_clientsession(hass)

        self._city = config_entry.data[CONF_CITY_NAME]
        self._channels = config_entry.data.get(CONF_CHANNELS, [])

        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_POLL_LOCAL),
        )

    async def _async_update_data(self) -> EventFinderData:
        """Update data via library."""
        try:
            return await self._poll_channels()
        except Exception:  # pylint: disable=broad-except  # noqa: BLE001
            LOGGER.exception("Failed to poll channels")
            return EventFinderData()

    async def _poll_channels(self) -> EventFinderData:
        event_finder_data = EventFinderData()

        if not self._session or self._session.closed:
            return event_finder_data

        city_lower = self._city.lower()

        results: dict[str, ChannelMessage | None] = {}

        for c in self._channels:
            slug = c[CHAN_SLUG]
            results[slug] = await fetch_latest(
                self._session,
                slug,
                self._matcher,
                self._last_ids.get(slug, -1),
            )

        for ch in self._channels:
            slug = ch[CHAN_SLUG]
            msg = results.get(slug)

            if msg is None:
                continue

            self._last_ids[slug] = msg.msg_id

            if not ch[CHAN_LOCAL] and city_lower not in msg.text.lower():
                continue

            if msg.has(CLEAR_ACTION):
                self._found.clear()
                continue

            now = datetime.now(UTC)

            for action in self.actions:
                if not msg.has(action):
                    continue

                self._found[action] = now
                self._debug_info[action] = f"{slug}: {msg.text[:100]}"

        event_finder_data.found = self._found.copy()
        event_finder_data.debug_info = self._debug_info.copy()

        return event_finder_data
