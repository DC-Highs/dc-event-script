from openpyxl import load_workbook, Workbook
from openpyxl.worksheet.worksheet import Worksheet
import time
import datetime
import os
import logging
import numpy as np
from typing import Dict, Any, List, Optional, Union

logger = logging.getLogger(__name__)

def process_heroic_race(app: Any) -> None:
    """Processes Heroic Race event data."""
    start_time: float = time.perf_counter()
    logger.info("Starting Heroic Race event processing")

    hr_data: Dict[str, Any] = app.data_view['heroic_races']
    event_info: Dict[str, Any] = hr_data['islands'][app.event_number]
    
    # Mapping for quick access
    race_map: Dict[str, Any] = {
        'rewards': {v['id']: v for v in hr_data['rewards']},
        'laps': {v['id']: v for v in hr_data['laps']},
        'nodes': {v['id']: v for v in hr_data['nodes']},
        'missions': {v['id']: v for v in hr_data['missions']},
        'encounters': {v['id']: v for v in hr_data['encounters']},
        'enemies': {v['id']: v for v in hr_data['enemies']},
        'lap_rewards': {v['id']: v for v in hr_data['lap_rewards']}
    }

    event_start_str: str = time.strftime("%d %b %Y", time.gmtime(event_info['start_ts']))
    
    # Paths for reports
    report_path: str = os.path.join(app.event_fp, f"Heroic_Race_{event_start_str}.txt")
    template_path: str = os.path.join("assets", "templates", "Kedai_Template.xlsx")
    excel_output_path: str = os.path.join(app.event_fp, f"Heroic_Race_{event_start_str}.xlsx")

    heroic_name: str = app.localization.get_dragon_name(event_info['dragon_race_id']) or "Heroic Dragon"

    with open(report_path, 'w') as f:
        # Load Excel if template exists
        workbook: Optional[Workbook] = None
        worksheet: Optional[Worksheet] = None
        if os.path.exists(template_path):
            workbook = load_workbook(template_path)
            worksheet = workbook.active

        lap_counter: int = 1
        for lap_id in event_info['laps']:
            f.write(f"Heroic Race: {heroic_name} - Lap {lap_counter}\n")
            
            # Check for lap rewards
            hr_rewards: Dict[str, Any] = hr_data['lap_rewards'][app.event_number].get('lap_rewards', {})
            if str(lap_counter) in hr_rewards:
                lap_reward = hr_rewards[str(lap_counter)]
                if 'limited_time' in lap_reward:
                    hours: int = int(lap_reward['limited_time'] / 3600)
                    f.write(f"Timed Lap: Prize x{lap_reward['multiplier']} ({hours}h)\n")

            lap_info: Dict[str, Any] = race_map['laps'][lap_id]
            node_counter: int = 1
            for node_id in lap_info['nodes']:
                node_info: Dict[str, Any] = race_map['nodes'][node_id]
                mission_counter: int = 0
                for mission_id in node_info['missions']:
                    mission_counter += 1
                    mission: Dict[str, Any] = race_map['missions'][mission_id]
                    
                    goal: int = mission['goal_points']
                    pool: Union[int, str] = mission['pool_size'] if mission['spawn_time'] != 1 else '-'
                    wait_time: Union[int, str] = mission['spawn_time'] if mission['spawn_time'] != 1 else '-'
                    
                    wait_str: str = str(wait_time)
                    total_wait: str = "-"
                    
                    mission_type: str = mission['type']
                    if mission_type == 'pvp':
                        mission_type = 'league'
                        
                    f.write(f"\tLap {lap_counter} - Node {node_counter}: Task-{mission_type}, Goal-{goal}, Pool-{pool}\n")
                    
                    if worksheet:
                        _write_to_heroic_excel(worksheet, lap_counter, node_counter, mission_type, goal, pool, wait_str, total_wait, mission_counter)
                
                node_counter += 1
                f.write('\n')
            lap_counter += 1
            f.write('\n')

        if workbook:
            workbook.save(excel_output_path)

    logger.info(f"Heroic Race processing completed in {time.perf_counter() - start_time:.2f}s")

def _write_to_heroic_excel(ws: Worksheet, lap: int, node: int, m_type: str, goal: Union[int, str], pool: Union[int, str], wait: str, total: str, m_num: int) -> None:
    cols: Dict[str, str] = {'gold': 'E', 'food': 'F', 'feed': 'G', 'breed': 'H', 'hatch': 'I', 'fight': 'J', 'league': 'K'}
    if m_type not in cols: return
    
    col: str = cols[m_type]
    row: int = 14 + 22 * (lap - 1) + 4 * (node - 1)
    ws[f"{col}{row}"] = goal
    ws[f"{col}{row+1}"] = pool
    ws[f"{col}{row+2}"] = wait
    ws[f"{col}{row+3}"] = total
