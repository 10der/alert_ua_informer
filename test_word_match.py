"""Unit tests for telegram_fetcher threat-detection patterns."""

import pytest

from .telegram_fetcher import ChannelMessage


@pytest.mark.parametrize(
    ("text", "has_missile", "has_shahed", "is_clear"),
    [
        # --- missile ---
        pytest.param(
            "Виявлено балістичну ракету", True, False, False, id="missile_balistychna"
        ),
        pytest.param(
            "Загроза аеробалістичної цілі (Кинджал)",
            True,
            False,
            False,
            id="missile_aerobalistics",
        ),
        pytest.param(
            "Виявлено крилату ракету", True, False, False, id="missile_krylata"
        ),
        pytest.param("Пуск КАБів з Су-34", True, False, False, id="missile_kab"),
        pytest.param(
            "загроза авіаційних засобів ураження",
            True,
            False,
            False,
            id="missile_aviaztv",
        ),
        pytest.param("Пуск Х-101 з акваторії", True, False, False, id="missile_x101"),
        pytest.param("Іскандер зафіксовано", True, False, False, id="missile_iskander"),
        pytest.param(
            "Виявлено ракету на Київ", True, False, False, id="missile_raketa"
        ),
        # --- shahed ---
        pytest.param("Дніпро шахід", False, True, False, id="shahed_shahed"),
        pytest.param("Летить БпЛА з півдня", False, True, False, id="shahed_bpla"),
        pytest.param(
            "Безпілотник курсом на місто", False, True, False, id="shahed_bezpilot"
        ),
        pytest.param(
            "Група дронів зафіксована", False, True, False, id="shahed_group_drones"
        ),
        pytest.param(
            "реактивний бпла над містом", False, True, False, id="shahed_reactive_bpla"
        ),
        pytest.param("мопед летить", False, True, False, id="shahed_moped"),
        # --- clear ---
        pytest.param("Відбій тривоги", False, False, True, id="clear_vidbiy"),
        pytest.param(
            "Небо чисто, загрози немає", False, False, True, id="clear_chysto"
        ),
        pytest.param("Загрозу знято", False, False, True, id="clear_zniato"),
        pytest.param("Гроза пройшла", False, False, True, id="clear_proishla"),
        # --- combined ---
        pytest.param("Шахед, відбій", False, True, True, id="combined_shahed_clear"),
        pytest.param(
            "Балістика і шахед", True, True, False, id="combined_missile_shahed"
        ),
        # --- no match ---
        pytest.param("Нічого підозрілого", False, False, False, id="no_match"),
        pytest.param("", False, False, False, id="empty"),

        pytest.param("шахедів немає", False, True, True, id="negative_shahed"),
        pytest.param(
            "ракетної загрози немає", True, False, True, id="negative_missile"
        ),
        pytest.param(
            "відбій шахедної небезпеки", False, True, True, id="negative_shahed"
        ),
    ],
)
def test_channel_message_flags(
    text: str,
    has_missile: bool,
    has_shahed: bool,
    is_clear: bool,
) -> None:
    msg = ChannelMessage(msg_id=1, text=text)
    assert msg.has_missile is has_missile
    assert msg.has_shahed is has_shahed
    assert msg.is_clear is is_clear
