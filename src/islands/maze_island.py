import time
import logging
import numpy as np
import xlsxwriter
import os
from typing import Dict, Any, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)

def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Converts RGB values to a hex string for Excel."""
    return '#%02x%02x%02x' % (r, g, b)

def determine_text_color(r: int, g: int, b: int) -> int:
    """Determines if black or white text should be used based on background brightness."""
    # Using luminosity formula
    brightness: float = (0.299 * r**2 + 0.587 * g**2 + 0.114 * b**2)
    return 255 if brightness < (127**2) else 0

def process_maze_island(app: Any) -> Optional[Tuple[List[Tuple[int, int, int]], Dict[str, Any]]]:
    """Processes Maze Island event data and generating reports/Excel."""
    start_time: float = time.perf_counter()
    logger.info("Starting Maze Island event processing")

    maze_data: Dict[str, Any] = app.data_view['maze_island']
    islands: List[Dict[str, Any]] = maze_data['islands']
    paths_data: List[Dict[str, Any]] = maze_data.get('paths', [])
    event_info: Dict[str, Any] = islands[app.event_number]
    
    # Build dictionary for easier lookup
    maze_map: Dict[str, Any] = {
        'nodes': {node['id']: node for node in maze_data['nodes']},
        'paths': {path['id']: path for path in paths_data},
        'rewards': {rew['id']: rew['reward'][0] for rew in maze_data['rewards']},
        'current_rewards': {}
    }

    # Identify colors used for paths
    colors_used: List[Tuple[int, int, int]] = []
    for path_id in event_info['paths']:
        p = maze_map['paths'][path_id]
        colors_used.append(tuple(p['color']))
        
        # Extract current rewards from the event pathways
        path_nodes: List[str] = p['nodes']
        for node_id in path_nodes:
            node = maze_map['nodes'][node_id]
            if 'reward_id' in node:
                reward_id = node['reward_id']
                maze_map['current_rewards'][reward_id] = maze_map['rewards'][reward_id]
    
    # This check seems to be a pre-step for the GUI (based on original script logic)
    if not getattr(app, 'maze_color_check_status', False):
        return colors_used, maze_map
    
    # Preparing for full processing
    ensure_dir(app.event_fp)
    
    # Logging asset info
    zip_filename: str = event_info['zip_file'].split('.')[0].split('/')[-1]
    asset_zip: str = f"{app.asset_zip_fp[0]}maze_island{app.asset_zip_fp[1]}{zip_filename}.zip"
    
    # Report info
    event_start_str: str = time.strftime("%d %b %Y", time.gmtime(event_info['availability']['from']))
    output_base_name: str = f"Maze_Island_{event_start_str}"
    
    # Initialize Excel
    excel_path: str = os.path.join(app.event_fp, f"{output_base_name}.xlsx")
    workbook: xlsxwriter.Workbook = xlsxwriter.Workbook(excel_path)
    worksheet: xlsxwriter.worksheet.Worksheet = workbook.add_worksheet()
    
    # Set up some formatting
    align_right = workbook.add_format({'align': 'right'})
    worksheet.set_column('A:XFD', None, align_right)
    
    # Initial coin count calculation
    days: int = int((event_info['availability']['to'] - event_info['availability']['from']) / (3600 * 24)) + 1
    # total_coins: int = 1800 * days + event_info['initial_points']
    
    path_numbers: List[int] = []
    dragon_names: List[str] = []
    color_formats: List[xlsxwriter.format.Format] = []
    
    for idx, path_id in enumerate(event_info['paths']):
        path = maze_map['paths'][path_id]
        rgb = colors_used[idx]
        text_color_val = determine_text_color(*rgb)
        
        fmt = workbook.add_format({
            'bg_color': rgb_to_hex(*rgb),
            'font_color': rgb_to_hex(text_color_val, text_color_val, text_color_val),
            'align': 'right'
        })
        color_formats.append(fmt)
        path_numbers.append(path_id)
        
        d_id = path['dragon_type']
        d_name: str = app.local_dict.get(f"tid_unit_{d_id}_name", "Unknown Dragon")
        dragon_names.append(d_name.replace(" Dragon", ""))

    # Iterating through nodes and writing to excel (simplified logic)
    # ...
    
    workbook.close()
    logger.info(f"Maze Island processing completed in {time.perf_counter() - start_time:.2f}s")
    return None

def ensure_dir(path: str) -> None:
    if not os.path.exists(path):
        os.makedirs(path)
