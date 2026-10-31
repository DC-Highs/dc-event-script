import time
import logging
import os
from typing import Dict, Any, List, Optional, Union

logger = logging.getLogger(__name__)

def process_runner_island(app: Any) -> None:
    """Processes Runner Island event data."""
    start_time: float = time.perf_counter()
    logger.info("Starting Runner Island event processing")

    run_data: Dict[str, Any] = app.data_view['runner_island']
    event_info: Dict[str, Any] = run_data['islands'][app.event_number]
    
    event_start_str: str = time.strftime("%d %b %Y", time.gmtime(event_info['start_ts']))
    report_path: str = os.path.join(app.event_fp, f"Runner_Island_{event_start_str}.txt")

    # Mappings
    missions_map: Dict[int, Any] = {m['id']: m for m in run_data['missions']}
    milestones_map: Dict[int, Any] = {m['id']: m for m in run_data.get('milestone_rewards', [])}
    rewards_map: Dict[int, Any] = {r['id']: r for r in run_data.get('rewards', [])}
    pool_map: Dict[int, Any] = {p['id']: p for p in run_data.get('mission_pool', [])}

    with open(report_path, 'w') as f:
        f.write("--- Missions ---\n")
        pool_ids: List[int] = event_info.get('mission_pool', [])
        for pool_id in pool_ids:
            pool: List[int] = pool_map[pool_id]['missions']
            for m_id in pool:
                m: Dict[str, Any] = missions_map[m_id]
                m_type: str = app.localization.get_value_from_key(m['type']) or m['type']
                f.write(f"Type: {m_type}, Goal: {m['goal_points']}\n")
            f.write("\n")

        f.write("--- Rewards ---\n")
        milestone_ids: List[int] = event_info.get('milestone_rewards', [])
        for milestone_id in milestone_ids:
            ms: Dict[str, Any] = milestones_map[milestone_id]
            rew_id: int = ms['reward_id']
            rew: Dict[str, Any] = rewards_map[rew_id]
            prize: str = _get_reward_desc(rew['reward'][0], app)
            f.write(f"Points: {ms['points']}, Prize: {prize}\n")

    logger.info(f"Runner Island processing completed in {time.perf_counter() - start_time:.2f}s")

def _get_reward_desc(reward: Dict[str, Any], app: Any) -> str:
    if 'chest' in reward:
        return f"Chest: {reward['chest']}"
    if 'seeds' in reward:
        d_id = reward['seeds'][0]['id']
        name = app.localization.get_dragon_name(d_id) or "Unknown"
        return f"{reward['seeds'][0]['amount']} Orbs of {name}"
    return str(reward)
