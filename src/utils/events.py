import time
from enum import Enum
from typing import Any, Dict, Optional, Tuple

from dc_core import ConfigFilter
from dc_statistics import is_active_island, is_past_island, is_upcoming_island

EVENT_SECTIONS: Dict[str, str] = {
    'Fog Island': str(ConfigFilter.FOG_ISLAND),
    'Grid Island': str(ConfigFilter.GRID_ISLAND),
    'Heroic Race': str(ConfigFilter.HEROIC_RACES),
    'Maze Island': str(ConfigFilter.MAZE_ISLAND),
    'Puzzle Island': str(ConfigFilter.PUZZLE_ISLAND),
    'Runner Island': str(ConfigFilter.RUNNER_ISLAND),
    'Tower Island': str(ConfigFilter.TOWER_ISLAND),
}


class EventStatus(Enum):
    PAST = "past"
    ACTIVE = "active"
    UPCOMING = "upcoming"
    UNKNOWN = "unknown"


STATUS_STYLES: Dict[EventStatus, Dict[str, str]] = {
    EventStatus.PAST: {
        "background": "#f4a3a3", "foreground": "black", "selectbackground": "#c0392b", "selectforeground": "white",
    },
    EventStatus.ACTIVE: {
        "background": "#9ee09e", "foreground": "black", "selectbackground": "#2e8b2e", "selectforeground": "white",
    },
    EventStatus.UPCOMING: {
        "background": "#fff3a3", "foreground": "black", "selectbackground": "#c9a400", "selectforeground": "white",
    },
    EventStatus.UNKNOWN: {},
}


def get_event_status(island: Dict[str, Any], now: Optional[int] = None) -> EventStatus:
    """Tells whether an event already ended, is running or has not started, based on its timestamps."""
    moment: int = int(time.time()) if now is None else now

    if is_active_island(island, moment):
        return EventStatus.ACTIVE
    if is_upcoming_island(island, moment):
        return EventStatus.UPCOMING
    if is_past_island(island, moment):
        return EventStatus.PAST
    return EventStatus.UNKNOWN


def island_time_range(island: Dict[str, Any]) -> Tuple[int, int]:
    """Start and end timestamps of an event (`start_ts`/`end_ts` or `availability`)."""
    availability: Dict[str, int] = island.get('availability', {})
    return (
        island.get('start_ts', availability.get('from', 0)),
        island.get('end_ts', availability.get('to', 0)),
    )


def format_island_label(index: int, island: Dict[str, Any]) -> str:
    """Text shown in the list of events, e.g. `[0] 14 Nov 2023 - 15 Nov 2023`."""
    start_ts, end_ts = island_time_range(island)
    start: str = time.strftime("%d %b %Y", time.gmtime(start_ts))
    end: str = time.strftime("%d %b %Y", time.gmtime(end_ts))
    return f"[{index}] {start} - {end}"
