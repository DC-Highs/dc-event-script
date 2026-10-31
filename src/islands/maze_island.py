import logging
import os
import time
from typing import Any, Dict, List, Optional, Tuple

import xlsxwriter

logger = logging.getLogger(__name__)

SECONDS_PER_DAY = 3600 * 24
BRIGHTNESS_THRESHOLD = 127 ** 2


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Converts RGB values to a hex string for Excel."""
    return '#%02x%02x%02x' % (r, g, b)


def determine_text_color(r: int, g: int, b: int) -> int:
    """Determines if black or white text should be used based on the background luminosity."""
    brightness: float = (0.299 * r ** 2 + 0.587 * g ** 2 + 0.114 * b ** 2)
    return 255 if brightness < BRIGHTNESS_THRESHOLD else 0


def ensure_dir(path: str) -> None:
    if not os.path.exists(path):
        os.makedirs(path)


def build_maze_map(maze_data: Dict[str, Any]) -> Dict[str, Dict[int, Any]]:
    """Nodes, paths and rewards indexed by id, plus the (still empty) rewards of the event."""
    return {
        'nodes': {node['id']: node for node in maze_data['nodes']},
        'paths': {path['id']: path for path in maze_data.get('paths', [])},
        'rewards': {reward['id']: reward['reward'][0] for reward in maze_data['rewards']},
        'current_rewards': {}
    }


def collect_path_colors(event_info: Dict[str, Any], maze_map: Dict[str, Dict[int, Any]]) -> List[Tuple[int, ...]]:
    """Colors of the event paths; also records the rewards found on the nodes of those paths."""
    colors_used: List[Tuple[int, ...]] = []

    for path_id in event_info['paths']:
        path: Dict[str, Any] = maze_map['paths'][path_id]
        colors_used.append(tuple(path['color']))

        for node_id in path['nodes']:
            node: Dict[str, Any] = maze_map['nodes'][node_id]
            if 'reward_id' in node:
                maze_map['current_rewards'][node['reward_id']] = maze_map['rewards'][node['reward_id']]

    return colors_used


def is_color_check_only(app: Any) -> bool:
    """The GUI first asks only for the path colors, before the full processing is requested."""
    return not getattr(app, 'maze_color_check_status', False)


def build_path_formats(
    workbook: xlsxwriter.Workbook,
    event_info: Dict[str, Any],
    maze_map: Dict[str, Dict[int, Any]],
    colors_used: List[Tuple[int, ...]],
    app: Any,
) -> Tuple[List[int], List[str], List[Any]]:
    """Path numbers, dragon names and cell formats (one per path color) for the workbook."""
    path_numbers: List[int] = []
    dragon_names: List[str] = []
    color_formats: List[Any] = []

    for index, path_id in enumerate(event_info['paths']):
        rgb = colors_used[index]
        text_color: int = determine_text_color(*rgb)
        color_formats.append(workbook.add_format({
            'bg_color': rgb_to_hex(*rgb),
            'font_color': rgb_to_hex(text_color, text_color, text_color),
            'align': 'right'
        }))
        path_numbers.append(path_id)

        name: str = app.localization.get_dragon_name(maze_map['paths'][path_id]['dragon_type']) or "Unknown Dragon"
        dragon_names.append(name.replace(" Dragon", ""))

    return path_numbers, dragon_names, color_formats


def write_maze_workbook(
    app: Any,
    event_info: Dict[str, Any],
    maze_map: Dict[str, Dict[int, Any]],
    colors_used: List[Tuple[int, ...]],
) -> None:
    event_start: str = time.strftime("%d %b %Y", time.gmtime(event_info['availability']['from']))
    workbook = xlsxwriter.Workbook(os.path.join(app.event_fp, f"Maze_Island_{event_start}.xlsx"))
    worksheet = workbook.add_worksheet()
    worksheet.set_column('A:XFD', None, workbook.add_format({'align': 'right'}))

    build_path_formats(workbook, event_info, maze_map, colors_used, app)
    workbook.close()


def process_maze_island(app: Any) -> Optional[Tuple[List[Tuple[int, ...]], Dict[str, Any]]]:
    """Processes Maze Island event data and generating reports/Excel."""
    start_time: float = time.perf_counter()
    logger.info("Starting Maze Island event processing")

    maze_data: Dict[str, Any] = app.data_view['maze_island']
    event_info: Dict[str, Any] = maze_data['islands'][app.event_number]
    maze_map: Dict[str, Dict[int, Any]] = build_maze_map(maze_data)
    colors_used: List[Tuple[int, ...]] = collect_path_colors(event_info, maze_map)

    if is_color_check_only(app):
        return colors_used, maze_map

    ensure_dir(app.event_fp)
    write_maze_workbook(app, event_info, maze_map, colors_used)

    logger.info(f"Maze Island processing completed in {time.perf_counter() - start_time:.2f}s")
    return None
