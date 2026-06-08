"""Async Telegram web preview scraper."""

from dataclasses import dataclass, field
import os
from pathlib import Path
import re

import aiohttp
import anyio
from bs4 import BeautifulSoup

from .const import LOGGER, TG_WEB_BASE

# Set TG_FETCHER_DEBUG=1 to read from sample_message.txt instead of real fetch
DEBUG_FROM_FILE = os.getenv("TG_FETCHER_DEBUG") == "1"

def _build_regex(words: list[str]) -> re.Pattern:
    """Build a regex pattern that matches any of the provided words."""

    escaped = [re.escape(word.strip()) for word in words if word.strip()]

    if not escaped:
        return re.compile(r"a^")  # matches nothing

    pattern = r"\b(?:" + "|".join(escaped) + r")"
    return re.compile(pattern, re.IGNORECASE)


@dataclass
class KeywordMatcher:
    """Generic keyword matcher."""

    keywords: dict[str, list[str]]
    patterns: dict[str, re.Pattern] = field(init=False)

    def __post_init__(self) -> None:
        """Compile regex patterns for each keyword list."""
        self.patterns = {
            key: _build_regex(words)
            for key, words in self.keywords.items()
        }

    def matches(self, text: str) -> dict[str, bool]:
        """Return match flags for configured keys."""

        return {
            key: bool(pattern.search(text))
            for key, pattern in self.patterns.items()
        }

@dataclass
class ChannelMessage:
    """Parsed Telegram channel message with derived match flags."""

    msg_id: int
    text: str
    source: str = ""

    matcher: KeywordMatcher | None = None
    found: dict[str, bool] = field(init=False)

    def __post_init__(self) -> None:
        """Run keyword matcher if provided to set found flags."""

        if self.matcher is None:
            self.found = {}
            return

        self.found = self.matcher.matches(self.text.lower())

    def has(self, key: str) -> bool:
        """Return True if key was found in message."""

        return self.found.get(key, False)

async def fetch_latest(
    session: aiohttp.ClientSession,
    channel: str,
    matcher: KeywordMatcher,
    last_id: int = -1,
) -> ChannelMessage | None:
    """Fetch latest message from a Telegram channel preview page.

    Returns None if no new message or on fetch error.
    """

    if DEBUG_FROM_FILE:
        msg_id = 777
        file_path = Path(__file__).parent / "sample_message.txt"

        async with await anyio.open_file(file_path, encoding="utf-8") as file:
            msg_text = await file.read()

        return ChannelMessage(
            msg_id=msg_id,
            text=msg_text,
            source=channel,
            matcher=matcher,
        )

    url = TG_WEB_BASE.format(channel=channel)

    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            if resp.status != 200:
                LOGGER.warning("[%s] HTTP %s", channel, resp.status)
                return None

            html = await resp.text()

    except Exception as exc:  # noqa: BLE001
        LOGGER.error("[%s] fetch failed: %s", channel, exc)
        return None

    soup = BeautifulSoup(html, "html.parser")
    messages = soup.select("div.tgme_widget_message[data-post]")

    if not messages:
        LOGGER.debug("[%s] no messages on page", channel)
        return None

    last_msg = messages[-1]

    try:
        msg_id = int(last_msg["data-post"].split("/")[-1])
    except (KeyError, ValueError) as exc:
        LOGGER.error("[%s] cannot parse msg_id: %s", channel, exc)
        return None

    if msg_id <= last_id:
        return None

    text_el = last_msg.select_one("div.tgme_widget_message_text.js-message_text")
    msg_text = ""

    if text_el:
        for br in text_el.find_all("br"):
            br.replace_with(" ")

        msg_text = " ".join(text_el.get_text().split())

    return ChannelMessage(
        msg_id=msg_id,
        text=msg_text,
        source=channel,
        matcher=matcher,
    )
