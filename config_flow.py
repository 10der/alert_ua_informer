"""Config flow for Air Danger Monitor."""

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CHAN_LOCAL,
    CHAN_NAME,
    CHAN_SLUG,
    CONF_CHANNELS,
    CONF_CITY_NAME,
    CONF_KEY_WORDS,
    DOMAIN,
)

CLEAR_ACTION = "__clear__"

DEFAULT_ACTIONS: list[dict[str, list[str] | str]] = [
    {
        "key": "shahed",
        "words": [
            "шахед",
            "мопед",
            "бпла",
            "дрон",
        ],
    },
    {
        "key": "missile",
        "words": [
            "бб",
            "рн",
            "ракет",
            "каб",
            "швидкісна",
        ],
    },
    {"key": CLEAR_ACTION, "words": ["відбій"]},
]


def _keywords_to_dict(
    raw: list[dict[str, str | list[str]]],
) -> dict[str, list[str]]:
    """Convert UI-friendly keyword list into matcher dict."""

    result: dict[str, list[str]] = {}

    for item in raw:
        key = str(item.get("key", "")).strip()
        words = item.get("words", [])

        if not key:
            continue

        if isinstance(words, str):
            words = [w.strip() for w in words.split(",")]

        result[key] = [str(word).strip() for word in words if str(word).strip()]

    return result


def _parse_channels(raw: str) -> list[dict]:
    """Parse comma-separated channel slugs into channel dicts (no local flag)."""
    result = []
    for part in raw.split(","):
        slug = part.strip().lstrip("@")
        if slug:
            result.append({CHAN_SLUG: slug, CHAN_LOCAL: False, CHAN_NAME: slug})
    return result


class AirDangerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Air Danger Monitor."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""

        errors = {}

        if user_input is not None:
            city = user_input[CONF_CITY_NAME].strip()

            # Unique ID = city name (lower), prevent duplicates
            await self.async_set_unique_id(city.lower())
            self._abort_if_unique_id_configured()

            channels_raw = user_input.get(CONF_CHANNELS, "")
            channels = _parse_channels(channels_raw)
            if not channels:
                errors[CONF_CHANNELS] = "no_channels"
            else:
                return self.async_create_entry(
                    title=f"Air Danger — {city}",
                    data={
                        CONF_CITY_NAME: city,
                        CONF_CHANNELS: channels,
                        CONF_KEY_WORDS: DEFAULT_ACTIONS,  # TODO: Default keywords, can be updated later in options
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CITY_NAME): str,
                    vol.Required(CONF_CHANNELS): selector.TextSelector(
                        selector.TextSelectorConfig(
                            multiline=False,
                        )
                    ),
                }
            ),
            description_placeholders={
                "channels_hint": "dnipro_alerts, kpszsu, war_monitor"
            },
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this config entry."""

        return AirDangerOptionsFlow(config_entry)


class AirDangerOptionsFlow(config_entries.OptionsFlow):
    """Options flow — manage channels after initial setup."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize."""

        self._entry = config_entry
        # Working copy of channel list
        self._channels: list[dict] = list(config_entry.data.get(CONF_CHANNELS, []))
        self._step = "menu"

    async def async_step_init(self, user_input=None):
        """Start options flow."""

        return await self.async_step_menu()

    async def async_step_menu(self, user_input=None):
        """Show channel list and action buttons."""
        menu_options = ["add_channel", "edit_channels", "finish"]
        return self.async_show_menu(
            step_id="menu",
            menu_options=menu_options,
        )

    async def async_step_add_channel(self, user_input=None):
        """Add a new Telegram channel."""
        errors = {}

        if user_input is not None:
            slug = user_input["slug"].strip().lstrip("@")
            if not slug:
                errors["slug"] = "no_channels"
            else:
                # Check duplicate
                existing_slugs = [c[CHAN_SLUG] for c in self._channels]
                if slug in existing_slugs:
                    errors["slug"] = "already_configured"
                else:
                    self._channels.append(
                        {
                            CHAN_SLUG: slug,
                            CHAN_LOCAL: user_input.get("local", False),
                            CHAN_NAME: user_input.get("friendly_name", "").strip()
                            or slug,
                        }
                    )
                    # Persist and go back to menu
                    return await self._save_and_menu()

        return self.async_show_form(
            step_id="add_channel",
            data_schema=vol.Schema(
                {
                    vol.Required("slug"): str,
                    vol.Optional("friendly_name", default=""): str,
                    vol.Optional("local", default=False): selector.BooleanSelector(),
                }
            ),
            description_placeholders={
                "local_hint": "Позначте якщо це канал вашого міста (локальний моніторинг)"
            },
            errors=errors,
        )

    async def async_step_edit_channels(self, user_input=None):
        """Show current channels; user can remove them."""
        errors = {}

        if user_input is not None:
            keep_slugs = user_input.get("keep", [])
            self._channels = [c for c in self._channels if c[CHAN_SLUG] in keep_slugs]
            return await self._save_and_menu()

        options = {
            c[
                CHAN_SLUG
            ]: f"{'🏠 ' if c[CHAN_LOCAL] else '🌍 '}{c[CHAN_NAME]} (@{c[CHAN_SLUG]})"
            for c in self._channels
        }

        return self.async_show_form(
            step_id="edit_channels",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        "keep",
                        default=list(options.keys()),
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                {"value": k, "label": v} for k, v in options.items()
                            ],
                            multiple=True,
                        )
                    )
                }
            ),
            description_placeholders={"hint": "Зніміть галочку щоб видалити канал"},
            errors=errors,
        )

    async def async_step_finish(self, user_input=None):
        """Save and close options flow."""
        return self.async_create_entry(title="", data={})

    async def _save_and_menu(self):
        """Persist channel list to config entry data and return to menu."""
        new_data = dict(self._entry.data)
        new_data[CONF_CHANNELS] = self._channels
        new_data[CONF_KEY_WORDS] = DEFAULT_ACTIONS
        self.hass.config_entries.async_update_entry(self._entry, data=new_data)
        return await self.async_step_menu()
