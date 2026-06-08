"""Constants for Air Danger Monitor."""

from logging import Logger, getLogger

DOMAIN = "air_danger"

ATTRIBUTION = "Data provided by Telegram channels"

# Config keys
CONF_CITY_NAME = "city_name"
CONF_CHANNELS = "channels"  # list of {slug, local, friendly_name}
CONF_KEY_WORDS = "keywords"

DEVICE_NAME = "Air Danger Monitor"

# Channel dict keys
CHAN_SLUG = "slug"
CHAN_LOCAL = "local"
CHAN_NAME = "friendly_name"

# Defaults
DEFAULT_POLL_LOCAL = 10   # seconds
DEFAULT_POLL_GLOBAL = 10  # seconds
MAX_AGE_MINUTES = 15  # minutes after which a threat is considered stale

# Telegram web preview base URL
TG_WEB_BASE = "https://t.me/s/{channel}"

LOGGER: Logger = getLogger(__package__)

