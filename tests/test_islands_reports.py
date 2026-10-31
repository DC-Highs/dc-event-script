import logging
from pathlib import Path

from conftest import localization, make_app
from src.islands.placeholders import (
    process_heroic_race,
    process_maze_island,
    process_puzzle_island,
    process_runner_island,
    process_tower_island,
)
from src.islands.puzzle_island import process_puzzle_island as real_puzzle
from src.islands.runner_island import process_runner_island as real_runner


def puzzle_data():
    def mission(mission_id, activity, amount, loopable=None):
        data = {
            "id": mission_id, "moves": mission_id, "skip_cost": {"c": 5 * mission_id},
            "activity_type": activity, "required_amount": amount,
        }
        if loopable is not None:
            data["loopable"] = loopable
        return data

    return {
        "islands": [
            {
                "start_ts": 1_700_000_000,
                "top_reward_queue": [1],
                "middle_reward_queue": [2],
                "bottom_reward_queue": [3, 4],
                "mission_queue1": [1, 2],
                "mission_queue2": [3],
                "mission_queue3": [],
                "mission_queue4": [1, 3],
            }
        ],
        "rewards": [
            {"id": 1, "reward": {"chest": 7}, "loopable": False, "required_pieces": 5, "colors": 2},
            {"id": 2, "reward": {"seeds": [{"id": 1000, "amount": 3}]}, "loopable": True, "required_pieces": 8, "colors": 3},
            {"id": 3, "reward": {"seeds": [{"id": 999, "amount": 1}]}, "loopable": False, "required_pieces": 1, "colors": 1},
            {"id": 4, "reward": {"g": 100}, "loopable": False, "required_pieces": 2, "colors": 1},
        ],
        "missions": [
            mission(1, "COLLECT_GOLD", 5000),
            mission(2, "FEED_DRAGON", 12000, loopable=True),
            mission(3, "BREED", 4, loopable=False),
        ],
    }


def test_puzzle_island_report(tmp_path):
    app = make_app(tmp_path, data_view={"puzzle_island": puzzle_data()}, localization=localization(tid_unit_1000_name="Nature"))

    real_puzzle(app)

    report = (tmp_path / "Puzzle_Island_14 Nov 2023.txt").read_text(encoding="utf-8")
    assert "Top Rewards\nPieces: 5, Color: 2, Loop: No, Prize: Chest: 7" in report
    assert "Middle Rewards\nPieces: 8, Color: 3, Loop: Yes, Prize: 3 Orbs of Nature" in report
    assert "Prize: 1 Orbs of Unknown" in report
    assert "Prize: {'g': 100}" in report
    assert "Mission Set #1:\nMoves: 1, Skip: 5 - Action: Collect 5k Gold\nLoop:\nMoves: 2, Skip: 10 - Action: Feed 12k Food" in report
    assert "Mission Set #2:\nMoves: 3, Skip: 15 - Action: BREED - 4\nLoop:\n" in report
    assert "Mission Set #3:\nLoop:\n" in report
    assert report.count("Mission Set #") == 4


def runner_data():
    return {
        "islands": [{"start_ts": 1_700_000_000, "mission_pool": [1, 2], "milestone_rewards": [1, 2, 3]}],
        "missions": [
            {"id": 1, "type": "feed", "goal_points": 6},
            {"id": 2, "type": "gold", "goal_points": 1},
        ],
        "mission_pool": [{"id": 1, "missions": [1]}, {"id": 2, "missions": [2]}],
        "milestone_rewards": [
            {"id": 1, "points": 10, "reward_id": 1},
            {"id": 2, "points": 20, "reward_id": 2},
            {"id": 3, "points": 30, "reward_id": 3},
        ],
        "rewards": [
            {"id": 1, "reward": [{"chest": 3}]},
            {"id": 2, "reward": [{"seeds": [{"id": 1000, "amount": 2}]}]},
            {"id": 3, "reward": [{"g": 50}]},
        ],
    }


def test_runner_island_report(tmp_path):
    app = make_app(tmp_path, data_view={"runner_island": runner_data()}, localization=localization(feed="Feed", tid_unit_1000_name="Nature"))

    real_runner(app)

    report = (tmp_path / "Runner_Island_14 Nov 2023.txt").read_text(encoding="utf-8")
    assert "Type: Feed, Goal: 6\n\nType: gold, Goal: 1\n\n" in report
    assert "Points: 10, Prize: Chest: 3" in report
    assert "Points: 20, Prize: 2 Orbs of Nature" in report
    assert "Points: 30, Prize: {'g': 50}" in report


def test_runner_island_without_optional_sections(tmp_path):
    data = {"islands": [{"start_ts": 0}], "missions": []}

    real_runner(make_app(tmp_path, data_view={"runner_island": data}))

    assert (tmp_path / "Runner_Island_01 Jan 1970.txt").read_text(encoding="utf-8") == "--- Missions ---\n--- Rewards ---\n"


def test_runner_island_unknown_dragon_name(tmp_path):
    data = runner_data()
    data["islands"][0]["milestone_rewards"] = [2]

    real_runner(make_app(tmp_path, data_view={"runner_island": data}))

    assert "2 Orbs of Unknown" in (tmp_path / "Runner_Island_14 Nov 2023.txt").read_text(encoding="utf-8")


def test_placeholders_only_warn(caplog, tmp_path):
    app = make_app(tmp_path)

    with caplog.at_level(logging.WARNING):
        for process in (
            process_heroic_race,
            process_maze_island,
            process_puzzle_island,
            process_runner_island,
            process_tower_island,
        ):
            process(app)

    assert caplog.text.count("not yet refactored") == 5
    assert list(Path(tmp_path).iterdir()) == []
