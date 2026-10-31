import pytest

from src.utils.events import (
    EVENT_SECTIONS,
    STATUS_STYLES,
    EventStatus,
    format_island_label,
    get_event_status,
    island_time_range,
)

NOW = 1_700_000_000


@pytest.mark.parametrize(
    "island, expected",
    [
        ({"start_ts": NOW - 10, "end_ts": NOW + 10}, EventStatus.ACTIVE),
        ({"start_ts": NOW + 10, "end_ts": NOW + 20}, EventStatus.UPCOMING),
        ({"start_ts": NOW - 20, "end_ts": NOW - 10}, EventStatus.PAST),
        ({"availability": {"from": NOW - 10, "to": NOW + 10}}, EventStatus.ACTIVE),
        ({"availability": {"from": NOW + 10, "to": NOW + 20}}, EventStatus.UPCOMING),
        ({"availability": {"from": NOW - 20, "to": NOW - 10}}, EventStatus.PAST),
        ({"start_ts": NOW - 10}, EventStatus.UNKNOWN),
        ({}, EventStatus.UNKNOWN),
    ],
)
def test_event_status(island, expected):
    assert get_event_status(island, NOW) is expected


def test_event_status_defaults_to_the_current_time():
    assert get_event_status({"start_ts": 0, "end_ts": 1}) is EventStatus.PAST
    assert get_event_status({"start_ts": 4_000_000_000, "end_ts": 4_100_000_000}) is EventStatus.UPCOMING


def test_every_status_has_a_style():
    assert set(STATUS_STYLES) == set(EventStatus)
    assert STATUS_STYLES[EventStatus.UNKNOWN] == {}
    assert len({STATUS_STYLES[status]["background"] for status in EventStatus if status is not EventStatus.UNKNOWN}) == 3


def test_time_range_and_label():
    assert island_time_range({"start_ts": 1, "end_ts": 2}) == (1, 2)
    assert island_time_range({"availability": {"from": 3, "to": 4}}) == (3, 4)
    assert island_time_range({}) == (0, 0)
    assert format_island_label(2, {"start_ts": NOW, "end_ts": NOW + 86400}) == "[2] 14 Nov 2023 - 15 Nov 2023"


def test_event_sections_use_the_configuration_names():
    assert EVENT_SECTIONS["Heroic Race"] == "heroic_races"
    assert EVENT_SECTIONS["Fog Island"] == "fog_island"
    assert len(EVENT_SECTIONS) == 7
