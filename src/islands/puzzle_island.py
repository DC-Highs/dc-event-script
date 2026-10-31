import time
import logging
import os
from typing import Dict, Any, List, Optional, Union

logger = logging.getLogger(__name__)

def process_puzzle_island(app: Any) -> None:
    """Processes Puzzle Island event data."""
    start_time: float = time.perf_counter()
    logger.info("Starting Puzzle Island event processing")

    puzzle_data: Dict[str, Any] = app.data_view['puzzle_island']
    island_event: Dict[str, Any] = puzzle_data['islands'][app.event_number]
    
    # Mappings
    rewards_map: Dict[int, Any] = {r['id']: r for r in puzzle_data['rewards']}
    missions_map: Dict[int, Any] = {m['id']: m for m in puzzle_data['missions']}

    event_start_str: str = time.strftime("%d %b %Y", time.gmtime(island_event['start_ts']))
    report_path: str = os.path.join(app.event_fp, f"Puzzle_Island_{event_start_str}.txt")

    with open(report_path, 'w') as f:
        # Process rewards
        queues: Dict[str, List[int]] = {
            'Top Rewards': island_event['top_reward_queue'],
            'Middle Rewards': island_event['middle_reward_queue'],
            'Bottom Rewards': island_event['bottom_reward_queue']
        }
        
        for name, queue in queues.items():
            f.write(f"{name}\n")
            for r_id in queue:
                rew = rewards_map[r_id]
                prize_name = _get_reward_name(rew['reward'], app)
                loop = "Yes" if rew['loopable'] else "No"
                f.write(f"Pieces: {rew['required_pieces']}, Color: {rew['colors']}, Loop: {loop}, Prize: {prize_name}\n")
            f.write("\n")

        # Process missions
        f.write("---- Missions ----\n")
        mission_queues: List[str] = ['mission_queue1', 'mission_queue2', 'mission_queue3', 'mission_queue4']
        for i, q_name in enumerate(mission_queues):
            f.write(f"Mission Set #{i+1}:\n")
            m_ids: List[int] = island_event[q_name]
            
            non_loop: List[int] = [m_id for m_id in m_ids if not missions_map[m_id].get('loopable')]
            loopable: List[int] = [m_id for m_id in m_ids if missions_map[m_id].get('loopable')]
            
            for m_id in non_loop:
                _write_mission(f, missions_map[m_id], app)
            f.write("Loop:\n")
            for m_id in loopable:
                _write_mission(f, missions_map[m_id], app)
            f.write("\n")

    logger.info(f"Puzzle Island processing completed in {time.perf_counter() - start_time:.2f}s")

def _get_reward_name(reward: Dict[str, Any], app: Any) -> str:
    if 'chest' in reward:
        return f"Chest: {reward['chest']}" 
    if 'seeds' in reward:
        d_id = reward['seeds'][0]['id']
        name = app.localization.get_dragon_name(d_id) or "Unknown"
        return f"{reward['seeds'][0]['amount']} Orbs of {name}"
    return str(reward)

def _write_mission(f: Any, m_info: Dict[str, Any], app: Any) -> None:
    moves: int = m_info['moves']
    skip: int = m_info['skip_cost']['c']
    action: str = _parse_activity(m_info, app)
    f.write(f"Moves: {moves}, Skip: {skip} - Action: {action}\n")

def _parse_activity(m: Dict[str, Any], app: Any) -> str:
    act_type: str = m['activity_type']
    qty: int = m['required_amount']
    if act_type == 'COLLECT_GOLD':
        return f"Collect {qty//1000}k Gold"
    if act_type == 'FEED_DRAGON':
        return f"Feed {qty//1000}k Food"
    return f"{act_type} - {qty}"
