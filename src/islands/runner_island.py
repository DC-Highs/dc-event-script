import logging
import os
import time
from typing import Any, Dict, List, TextIO

logger = logging.getLogger(__name__)


def process_runner_island(app: Any) -> None:
    """Processes Runner Island event data."""
    start_time: float = time.perf_counter()
    logger.info("Starting Runner Island event processing")

    run_data: Dict[str, Any] = app.data_view['runner_island']
    event_info: Dict[str, Any] = run_data['islands'][app.event_number]
    event_start: str = time.strftime("%d %b %Y", time.gmtime(event_info['start_ts']))

    with open(os.path.join(app.event_fp, f"Runner_Island_{event_start}.txt"), 'w') as report:
        write_missions(report, run_data, event_info, app)
        write_rewards(report, run_data, event_info, app)

    logger.info(f"Runner Island processing completed in {time.perf_counter() - start_time:.2f}s")


def write_missions(report: TextIO, run_data: Dict[str, Any], event_info: Dict[str, Any], app: Any) -> None:
    missions_map: Dict[int, Any] = {mission['id']: mission for mission in run_data['missions']}
    pool_map: Dict[int, Any] = {pool['id']: pool for pool in run_data.get('mission_pool', [])}

    report.write("--- Missions ---\n")
    for pool_id in event_info.get('mission_pool', []):
        for mission_id in pool_map[pool_id]['missions']:
            mission: Dict[str, Any] = missions_map[mission_id]
            mission_type: str = app.localization.get_value_from_key(mission['type']) or mission['type']
            report.write(f"Type: {mission_type}, Goal: {mission['goal_points']}\n")
        report.write("\n")


def write_rewards(report: TextIO, run_data: Dict[str, Any], event_info: Dict[str, Any], app: Any) -> None:
    milestones_map: Dict[int, Any] = {m['id']: m for m in run_data.get('milestone_rewards', [])}
    rewards_map: Dict[int, Any] = {r['id']: r for r in run_data.get('rewards', [])}

    report.write("--- Rewards ---\n")
    for milestone_id in event_info.get('milestone_rewards', []):
        milestone: Dict[str, Any] = milestones_map[milestone_id]
        reward: Dict[str, Any] = rewards_map[milestone['reward_id']]
        prize: str = _get_reward_desc(reward['reward'][0], app)
        report.write(f"Points: {milestone['points']}, Prize: {prize}\n")


def _get_reward_desc(reward: Dict[str, Any], app: Any) -> str:
    if 'chest' in reward:
        return f"Chest: {reward['chest']}"
    if 'seeds' in reward:
        dragon_id = reward['seeds'][0]['id']
        name = app.localization.get_dragon_name(dragon_id) or "Unknown"
        return f"{reward['seeds'][0]['amount']} Orbs of {name}"
    return str(reward)
