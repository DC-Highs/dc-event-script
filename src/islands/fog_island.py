import logging
import os
import time
from typing import Any, Dict, List

from src.islands.fog_board import (
    load_board_template,
    mark_boards,
    render_visual_boards,
    save_marked_boards,
    write_cost_sheet,
)
from src.islands.fog_icons import FogIconCollector
from src.islands.fog_reports import write_assets_info, write_reward_keys
from src.utils.network import ensure_directory

logger = logging.getLogger(__name__)


def flatten_desired_chests(chests_desired: List[Any]) -> List[int]:
    """The chosen chests may come grouped in lists; the board needs them in a single list."""
    chests: List[int] = []
    for chest in chests_desired:
        if isinstance(chest, list):
            chests.extend(chest)
        else:
            chests.append(chest)
    return chests


def collect_icons(app: Any, fog_data: Dict[str, Any], dragon_reward_map: Dict[int, int]) -> FogIconCollector:
    with open(os.path.join(app.event_fp, "placement_locations.txt"), 'w') as location_log:
        collector = FogIconCollector(app, fog_data, dragon_reward_map, location_log)
        collector.collect()
    return collector


def process_fog_event(app: Any) -> None:
    """Processes the Fog Island event data and generates reports/images."""
    start_time: float = time.perf_counter()
    logger.info("Starting Fog Island event processing")

    fog_data: Dict[str, Any] = app.data_view['fog_island']
    event_info: Dict[str, Any] = fog_data['islands'][app.event_number]

    template = load_board_template()
    if template is None:
        return

    logger.debug(f"Event TID: {event_info['tid_name']}")
    ensure_directory(app.event_fp)
    write_assets_info(app.event_fp, app.asset_zip_fp, event_info)

    chests_of_interest: List[int] = flatten_desired_chests(app.chests_desired)
    fog_data["rewards"] = sorted(fog_data["rewards"], key=lambda reward: reward['id'])
    dragon_reward_map: Dict[int, int] = {reward['id']: index for index, reward in enumerate(fog_data["rewards"])}
    icons: FogIconCollector = collect_icons(app, fog_data, dragon_reward_map)

    squares: List[Dict[str, Any]] = fog_data['squares']
    save_marked_boards(mark_boards(template, squares, chests_of_interest), app.event_fp)

    event_start: str = time.strftime("%d %b %Y", time.gmtime(event_info['start_ts']))
    board_name: str = f"Fog_Board_{event_start}"
    write_cost_sheet(os.path.join(app.event_fp, f"{board_name}.xlsx"), squares)
    render_visual_boards(
        template, squares, chests_of_interest, dragon_reward_map, icons.chest_icons, icons.dragon_icons
    ).save(app.event_fp, board_name)

    write_reward_keys(app.event_fp, fog_data['rewards'], app.localization, app.chests_desired_names)
    logger.info(f"Fog Island processing completed in {time.perf_counter() - start_time:.2f}s")
