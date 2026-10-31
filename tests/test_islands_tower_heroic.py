import os

import numpy as np
import pytest
from openpyxl import load_workbook
from PIL import Image

from conftest import localization, make_app
from src.islands.heroic_race import process_heroic_race
from src.islands.tower_island import process_tower_island

TOWER_SQUARES = [
    {"type": "CATAPULT", "x": 1, "y": 1},
    {"type": "SINGLE_REWARD", "x": 2, "y": 1},
    {"type": "SINGLE_DRAGON_PIECE", "x": 3, "y": 1},
    {"type": "FINAL_DRAGON_SQUARE", "x": 1, "y": 7},
    {"type": "NORMAL", "x": 5, "y": 3},
    {"x": 6, "y": 3},
    {"type": "CATAPULT", "x": 200, "y": 100},
]


def tower_app(tmp_path):
    data = {"islands": [{"start_ts": 1_700_000_000}], "squares": TOWER_SQUARES}
    return make_app(tmp_path, data_view={"tower_island": data})


def test_tower_marks_the_squares_on_the_template(project_dir, tmp_path):
    process_tower_island(tower_app(tmp_path))

    board = np.array(Image.open(tmp_path / "Tower_Map_14 Nov 2023.jpg"))
    template = np.array(Image.open("assets/templates/Tower_Template_DO_NOT_DELETE.jpg"))

    assert abs(int(board[4000, 50]) - 150) < 12
    assert abs(int(board[4000, 150]) - 100) < 12
    assert abs(int(board[4000, 250]) - 175) < 12
    assert int(board[3400, 50]) < 12
    assert int(board[500, 500]) == int(template[500, 500])
    assert board.shape == template.shape
    assert (tmp_path / "Tower_Island_Key_14 Nov 2023.txt").read_text(encoding="utf-8").startswith("Tower Island Rewards Key")


def test_tower_falls_back_to_the_archive_template(work_dir, tmp_path_factory):
    archive = work_dir / "Archive" / "Tower_Island"
    archive.mkdir(parents=True)
    Image.fromarray(np.full((600, 400), 255, dtype=np.uint8)).save(archive / "Tower_Template_DO_NOT_DELETE.jpg")
    output = work_dir / "out"
    output.mkdir()

    process_tower_island(tower_app(output))

    assert (output / "Tower_Map_14 Nov 2023.jpg").exists()


def test_tower_stops_without_a_template(work_dir, caplog):
    output = work_dir / "out"
    output.mkdir()

    process_tower_island(tower_app(output))

    assert os.listdir(output) == []
    assert "Could not load tower template" in caplog.text


def heroic_data():
    def mission(mission_id, kind, goal, pool, spawn):
        return {"id": mission_id, "type": kind, "goal_points": goal, "pool_size": pool, "spawn_time": spawn}

    return {
        "islands": [{"start_ts": 1_700_000_000, "dragon_race_id": 1000, "laps": [1, 2, 3]}],
        "laps": [
            {"id": 1, "nodes": [1, 2]},
            {"id": 2, "nodes": [3]},
            {"id": 3, "nodes": []},
        ],
        "nodes": [
            {"id": 1, "missions": [1, 2, 3]},
            {"id": 2, "missions": [4]},
            {"id": 3, "missions": [5, 6]},
        ],
        "missions": [
            mission(1, "gold", 10, 4, 1),
            mission(2, "food", 20, 5, 60),
            mission(3, "pvp", 3, 2, 1),
            mission(4, "feed", 7, 3, 30),
            mission(5, "teleport", 1, 1, 1),
            mission(6, "breed", 9, 6, 15),
        ],
        "rewards": [{"id": 1}],
        "encounters": [{"id": 1}],
        "enemies": [{"id": 1}],
        "lap_rewards": [
            {"id": 1, "lap_rewards": {"1": {"limited_time": 7200, "multiplier": 3}, "2": {"multiplier": 2}}},
        ],
    }


def test_heroic_race_report_and_template(project_dir, tmp_path):
    app = make_app(
        tmp_path,
        data_view={"heroic_races": heroic_data()},
        localization=localization(tid_unit_1000_name="Nature Dragon"),
    )

    process_heroic_race(app)

    report = (tmp_path / "Heroic_Race_14 Nov 2023.txt").read_text(encoding="utf-8")
    assert report.startswith("Heroic Race: Nature Dragon - Lap 1\nTimed Lap: Prize x3 (2h)\n")
    assert "\tLap 1 - Node 1: Task-gold, Goal-10, Pool--\n" in report
    assert "\tLap 1 - Node 1: Task-food, Goal-20, Pool-5\n" in report
    assert "\tLap 1 - Node 1: Task-league, Goal-3, Pool--\n" in report
    assert "\tLap 1 - Node 2: Task-feed, Goal-7, Pool-3\n" in report
    assert "Heroic Race: Nature Dragon - Lap 2\n\tLap 2 - Node 1: Task-teleport" in report
    assert report.count("Timed Lap") == 1

    sheet = load_workbook(tmp_path / "Heroic_Race_14 Nov 2023.xlsx").active
    assert [sheet[f"E{row}"].value for row in (14, 15, 16, 17)] == [10, "-", "-", "-"]
    assert [sheet[f"F{row}"].value for row in (14, 15, 16, 17)] == [20, 5, "60", "-"]
    assert sheet["K14"].value == 3
    assert sheet["G18"].value == 7
    assert sheet["H36"].value == 9
    assert sheet["E36"].value is None


def test_heroic_race_without_a_template(work_dir):
    output = work_dir / "out"
    output.mkdir()
    app = make_app(output, data_view={"heroic_races": heroic_data()})

    process_heroic_race(app)

    assert os.listdir(output) == ["Heroic_Race_14 Nov 2023.txt"]
    assert (output / "Heroic_Race_14 Nov 2023.txt").read_text(encoding="utf-8").startswith("Heroic Race: Heroic Dragon - Lap 1")
