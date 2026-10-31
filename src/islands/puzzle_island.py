import logging
import os
import time
from typing import Any, Dict, List, TextIO

logger = logging.getLogger(__name__)

MISSION_QUEUES: List[str] = ['mission_queue1', 'mission_queue2', 'mission_queue3', 'mission_queue4']
REWARD_QUEUES: Dict[str, str] = {
    'Top Rewards': 'top_reward_queue',
    'Middle Rewards': 'middle_reward_queue',
    'Bottom Rewards': 'bottom_reward_queue',
}


def process_puzzle_island(app: Any) -> None:
    """Processes Puzzle Island event data."""
    start_time: float = time.perf_counter()
    logger.info("Starting Puzzle Island event processing")

    puzzle_data: Dict[str, Any] = app.data_view['puzzle_island']
    island_event: Dict[str, Any] = puzzle_data['islands'][app.event_number]
    rewards_map: Dict[int, Any] = {reward['id']: reward for reward in puzzle_data['rewards']}
    missions_map: Dict[int, Any] = {mission['id']: mission for mission in puzzle_data['missions']}

    event_start: str = time.strftime("%d %b %Y", time.gmtime(island_event['start_ts']))
    with open(os.path.join(app.event_fp, f"Puzzle_Island_{event_start}.txt"), 'w') as report:
        write_reward_queues(report, island_event, rewards_map, app)
        write_mission_queues(report, island_event, missions_map)

    logger.info(f"Puzzle Island processing completed in {time.perf_counter() - start_time:.2f}s")


def write_reward_queues(report: TextIO, island_event: Dict[str, Any], rewards_map: Dict[int, Any], app: Any) -> None:
    for title, queue_key in REWARD_QUEUES.items():
        report.write(f"{title}\n")
        for reward_id in island_event[queue_key]:
            reward = rewards_map[reward_id]
            prize_name = _get_reward_name(reward['reward'], app)
            loop = "Yes" if reward['loopable'] else "No"
            report.write(
                f"Pieces: {reward['required_pieces']}, Color: {reward['colors']}, Loop: {loop}, Prize: {prize_name}\n"
            )
        report.write("\n")


def write_mission_queues(report: TextIO, island_event: Dict[str, Any], missions_map: Dict[int, Any]) -> None:
    report.write("---- Missions ----\n")
    for index, queue_key in enumerate(MISSION_QUEUES):
        report.write(f"Mission Set #{index + 1}:\n")
        mission_ids: List[int] = island_event[queue_key]

        for mission_id in (m for m in mission_ids if not missions_map[m].get('loopable')):
            _write_mission(report, missions_map[mission_id])
        report.write("Loop:\n")
        for mission_id in (m for m in mission_ids if missions_map[m].get('loopable')):
            _write_mission(report, missions_map[mission_id])
        report.write("\n")


def _get_reward_name(reward: Dict[str, Any], app: Any) -> str:
    if 'chest' in reward:
        return f"Chest: {reward['chest']}"
    if 'seeds' in reward:
        dragon_id = reward['seeds'][0]['id']
        name = app.localization.get_dragon_name(dragon_id) or "Unknown"
        return f"{reward['seeds'][0]['amount']} Orbs of {name}"
    return str(reward)


def _write_mission(report: TextIO, mission: Dict[str, Any]) -> None:
    report.write(
        f"Moves: {mission['moves']}, Skip: {mission['skip_cost']['c']} - Action: {_parse_activity(mission)}\n"
    )


def _parse_activity(mission: Dict[str, Any]) -> str:
    activity_type: str = mission['activity_type']
    quantity: int = mission['required_amount']
    if activity_type == 'COLLECT_GOLD':
        return f"Collect {quantity // 1000}k Gold"
    if activity_type == 'FEED_DRAGON':
        return f"Feed {quantity // 1000}k Food"
    return f"{activity_type} - {quantity}"
