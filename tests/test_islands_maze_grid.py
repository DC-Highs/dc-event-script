import numpy as np
import pytest
from openpyxl import load_workbook
from PIL import Image

from conftest import localization, make_app
from src.islands.grid_island import process_grid_event
from src.islands.maze_island import determine_text_color, ensure_dir, process_maze_island, rgb_to_hex


def maze_data():
    return {
        "islands": [
            {
                "paths": [1, 2],
                "zip_file": "path/to/maze_island_a.zip",
                "availability": {"from": 0, "to": 86400 * 3},
                "initial_points": 100,
            }
        ],
        "paths": [
            {"id": 1, "color": [255, 0, 0], "nodes": [1], "dragon_type": 1000},
            {"id": 2, "color": [0, 0, 255], "nodes": [2], "dragon_type": 2000},
        ],
        "nodes": [{"id": 1, "reward_id": 5}, {"id": 2}],
        "rewards": [{"id": 5, "reward": [{"g": 10}, {"c": 1}]}],
    }


def test_color_helpers():
    assert rgb_to_hex(255, 0, 16) == "#ff0010"
    assert determine_text_color(255, 0, 0) == 0
    assert determine_text_color(0, 0, 255) == 255
    assert determine_text_color(0, 0, 0) == 255
    assert determine_text_color(255, 255, 255) == 0


def test_ensure_dir(tmp_path):
    target = tmp_path / "a" / "b"

    ensure_dir(str(target))
    ensure_dir(str(target))

    assert target.is_dir()


def test_maze_color_check_returns_colors_and_current_rewards(tmp_path):
    app = make_app(tmp_path, data_view={"maze_island": maze_data()})

    colors, maze_map = process_maze_island(app)

    assert colors == [(255, 0, 0), (0, 0, 255)]
    assert maze_map["current_rewards"] == {5: {"g": 10}}
    assert list(tmp_path.iterdir()) == []


def test_maze_without_paths_section(tmp_path):
    data = maze_data()
    del data["paths"]
    data["islands"][0]["paths"] = []
    app = make_app(tmp_path, data_view={"maze_island": data})

    assert process_maze_island(app) == ([], {"nodes": {1: data["nodes"][0], 2: data["nodes"][1]}, "paths": {}, "rewards": {5: {"g": 10}}, "current_rewards": {}})


@pytest.mark.parametrize("existing_output", [True, False])
def test_maze_writes_the_workbook(tmp_path, existing_output):
    output = tmp_path / "out"

    if existing_output:
        output.mkdir()

    app = make_app(
        tmp_path,
        event_fp=str(output),
        data_view={"maze_island": maze_data()},
        localization=localization(tid_unit_1000_name="Nature Dragon"),
        maze_color_check_status=True,
    )

    assert process_maze_island(app) is None

    workbook = load_workbook(output / "Maze_Island_01 Jan 1970.xlsx")
    assert workbook.active is not None


def grid_data():
    def square(square_id, kind, x, y, cost, **extra):
        data = {"id": square_id, "type": kind, "x": x, "y": y, "claim_cost": cost}
        data.update(extra)
        return data

    return {
        "islands": [{"start_ts": 1_700_000_000}],
        "episodes": [{"board_size": [3, 3]}],
        "squares": [
            square(1, "CHEST", 1, 1, 5, type_id=10, wall="V"),
            square(2, "CHEST", 2, 1, 0, type_id=11, wall="H"),
            square(3, "DRAGON", 1, 2, 120, type_id=1000, wall="VH"),
            square(4, "DRAGON", 2, 2, 1000, type_id=2000),
            square(5, "NONE", 3, 3, 7),
            square(3, "CHEST", 3, 1, 1, type_id=99),
            square(4, "NONE", 3, 2, 1),
        ],
    }


def test_grid_board_and_reports(tmp_path):
    app = make_app(
        tmp_path,
        data_view={"grid_island": grid_data()},
        chests_desired=[10],
        chests_desired_names=["Wooden Chest"],
        localization=localization(tid_unit_1000_name="Nature Dragon"),
    )

    process_grid_event(app)

    board = np.array(Image.open(tmp_path / "Grid_Board_14 Nov 2023.jpg"))
    assert board.shape == (300, 300)
    assert abs(int(board[90, 90]) - 75) < 12
    assert abs(int(board[90, 190]) - 150) < 12
    assert int(board[190, 90]) < 12
    assert int(board[190, 290]) > 240
    assert int(board[0, 150]) < 12 and int(board[299, 150]) < 12

    assert (tmp_path / "dragon_list.txt").read_text(encoding="utf-8") == "D1: Nature Dragon\nD2: Dragon 2000\n"
    assert (tmp_path / "grid_key.txt").read_text(encoding="utf-8") == "#1 - Wooden Chest\n"


def test_grid_without_chests_of_interest(tmp_path):
    process_grid_event(make_app(tmp_path, data_view={"grid_island": grid_data()}))

    assert (tmp_path / "grid_key.txt").read_text(encoding="utf-8") == ""
