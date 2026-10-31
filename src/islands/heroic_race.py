import logging
import os
import time
from typing import Any, Dict, Optional, TextIO, Tuple, Union

from openpyxl import Workbook, load_workbook
from openpyxl.worksheet.worksheet import Worksheet

logger = logging.getLogger(__name__)

TEMPLATE_PATH = os.path.join("assets", "templates", "Kedai_Template.xlsx")
SECONDS_PER_HOUR = 3600
INSTANT_SPAWN_TIME = 1
EXCEL_COLUMNS: Dict[str, str] = {
    'gold': 'E', 'food': 'F', 'feed': 'G', 'breed': 'H', 'hatch': 'I', 'fight': 'J', 'league': 'K'
}
FIRST_EXCEL_ROW = 14
EXCEL_ROWS_PER_LAP = 22
EXCEL_ROWS_PER_NODE = 4


def build_race_map(hr_data: Dict[str, Any]) -> Dict[str, Dict[int, Any]]:
    """Laps, nodes and missions indexed by id."""
    return {
        'laps': {lap['id']: lap for lap in hr_data['laps']},
        'nodes': {node['id']: node for node in hr_data['nodes']},
        'missions': {mission['id']: mission for mission in hr_data['missions']},
    }


def open_template_workbook() -> Optional[Workbook]:
    return load_workbook(TEMPLATE_PATH) if os.path.exists(TEMPLATE_PATH) else None


def write_lap_header(report: TextIO, heroic_name: str, lap_counter: int, lap_rewards: Dict[str, Any]) -> None:
    report.write(f"Heroic Race: {heroic_name} - Lap {lap_counter}\n")

    lap_reward: Optional[Dict[str, Any]] = lap_rewards.get(str(lap_counter))
    if lap_reward is not None and 'limited_time' in lap_reward:
        hours: int = int(lap_reward['limited_time'] / SECONDS_PER_HOUR)
        report.write(f"Timed Lap: Prize x{lap_reward['multiplier']} ({hours}h)\n")


def describe_mission(mission: Dict[str, Any]) -> Tuple[str, int, Union[int, str], str]:
    """Mission type (as named in the report), goal, pool size and wait time."""
    instant: bool = mission['spawn_time'] == INSTANT_SPAWN_TIME
    mission_type: str = 'league' if mission['type'] == 'pvp' else mission['type']
    pool: Union[int, str] = '-' if instant else mission['pool_size']
    wait: str = '-' if instant else str(mission['spawn_time'])
    return mission_type, mission['goal_points'], pool, wait


def write_node(
    report: TextIO,
    worksheet: Optional[Worksheet],
    missions: Dict[int, Any],
    node: Dict[str, Any],
    lap_counter: int,
    node_counter: int,
) -> None:
    for mission_id in node['missions']:
        mission_type, goal, pool, wait = describe_mission(missions[mission_id])
        report.write(f"\tLap {lap_counter} - Node {node_counter}: Task-{mission_type}, Goal-{goal}, Pool-{pool}\n")

        if worksheet:
            _write_to_heroic_excel(worksheet, lap_counter, node_counter, mission_type, goal, pool, wait, "-")

    report.write('\n')


def write_lap(
    report: TextIO,
    worksheet: Optional[Worksheet],
    race_map: Dict[str, Dict[int, Any]],
    lap_id: int,
    lap_counter: int,
) -> None:
    for node_counter, node_id in enumerate(race_map['laps'][lap_id]['nodes'], start=1):
        write_node(report, worksheet, race_map['missions'], race_map['nodes'][node_id], lap_counter, node_counter)

    report.write('\n')


def process_heroic_race(app: Any) -> None:
    """Processes Heroic Race event data."""
    start_time: float = time.perf_counter()
    logger.info("Starting Heroic Race event processing")

    hr_data: Dict[str, Any] = app.data_view['heroic_races']
    event_info: Dict[str, Any] = hr_data['islands'][app.event_number]
    race_map: Dict[str, Dict[int, Any]] = build_race_map(hr_data)

    event_start: str = time.strftime("%d %b %Y", time.gmtime(event_info['start_ts']))
    heroic_name: str = app.localization.get_dragon_name(event_info['dragon_race_id']) or "Heroic Dragon"
    workbook: Optional[Workbook] = open_template_workbook()
    worksheet: Optional[Worksheet] = workbook.active if workbook else None

    with open(os.path.join(app.event_fp, f"Heroic_Race_{event_start}.txt"), 'w') as report:
        for lap_counter, lap_id in enumerate(event_info['laps'], start=1):
            lap_rewards: Dict[str, Any] = hr_data['lap_rewards'][app.event_number].get('lap_rewards', {})
            write_lap_header(report, heroic_name, lap_counter, lap_rewards)
            write_lap(report, worksheet, race_map, lap_id, lap_counter)

        if workbook:
            workbook.save(os.path.join(app.event_fp, f"Heroic_Race_{event_start}.xlsx"))

    logger.info(f"Heroic Race processing completed in {time.perf_counter() - start_time:.2f}s")


def _write_to_heroic_excel(
    ws: Worksheet, lap: int, node: int, m_type: str, goal: Union[int, str], pool: Union[int, str], wait: str, total: str
) -> None:
    column: Optional[str] = EXCEL_COLUMNS.get(m_type)
    if column is None:
        return

    row: int = FIRST_EXCEL_ROW + EXCEL_ROWS_PER_LAP * (lap - 1) + EXCEL_ROWS_PER_NODE * (node - 1)
    ws[f"{column}{row}"] = goal
    ws[f"{column}{row + 1}"] = pool
    ws[f"{column}{row + 2}"] = wait
    ws[f"{column}{row + 3}"] = total
