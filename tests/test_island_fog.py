import numpy as np
import pytest
from openpyxl import load_workbook
from PIL import Image

from conftest import localization, make_app, png_bytes
from src.islands.fog_island import process_fog_event

TEMPLATE_DIR = "assets/templates"
BOARD_TEMPLATE = f"{TEMPLATE_DIR}/Fog_Board_DO_NOT_DELETE.jpg"


def fog_data():
    def square(x, y, kind, cost=5, **extra):
        data = {"x": x, "y": y, "type": kind, "claim_cost": cost}
        data.update(extra)
        return data

    return {
        "islands": [
            {
                "tid_name": "tid_fog",
                "analytics_id": "analytics",
                "zip_file": "static/dragoncity/fog_island/fog_a.zip",
                "canvas_assets_url": "https://example.com/canvas",
                "start_ts": 1_700_000_000,
            }
        ],
        "rewards": [
            {"id": 2, "reward_id": 1001},
            {"id": 1, "reward_id": 1000},
            {"id": 3, "reward_id": 1002},
        ],
        "squares": [
            square(1, 1, "CHEST", type_id=10),
            square(2, 1, "CHEST", type_id=10),
            square(3, 1, "CHEST", type_id=11),
            square(4, 1, "CHEST", type_id=12),
            square(1, 2, "CHEST", type_id=13),
            square(2, 2, "CHEST", type_id=14),
            square(1, 3, "DRAGON_PIECE", reward_id=1, type_id=1000),
            square(2, 3, "DRAGON_PIECE", reward_id=1),
            square(3, 3, "DRAGON_PIECE", reward_id=2),
            square(4, 3, "DRAGON_PIECE", reward_id=3),
            square(0, 0, "NONE", cost=0),
            square(1, 0, "STEP", cost=0),
            square(2, 0, "BONUS", cost=0),
        ],
    }


def downloads():
    requested = []

    def fake_fetch(downloader):
        requested.append(downloader.url)

        if "missing" in downloader.url:
            return None

        if "broken" in downloader.url:
            return b"garbage"

        return png_bytes("RGBA", (16, 16), (200, 50, 50, 255))

    return fake_fetch, requested


def fog_app(tmp_path, **overrides):
    values = dict(
        data_view={"fog_island": fog_data()},
        chests_desired=[10, [13, 14]],
        chests_desired_names=["Wooden Chest", "Golden Chest"],
        chest_ids={
            10: {"img_name": "ok_chest"},
            11: {"img_name": "broken_chest"},
            12: {"img_name": "missing_chest"},
            13: {"img_name": "ok_spine"},
            14: {"img_name": "ok_v1"},
        },
        asset_versioning={
            "chests": {
                "ok_spine": {"Format": "spine", "Version": 3},
                "ok_v1": {"Format": "png", "Version": 1},
            }
        },
        dragon_info={
            1000: {"img_name_mobile": "ok_dragon"},
            1001: {"img_name_mobile": "missing_dragon"},
            1002: {"img_name_mobile": "broken_dragon"},
        },
        localization=localization(tid_unit_1000_name="Nature Dragon"),
    )
    values.update(overrides)
    return make_app(tmp_path, **values)


def pixel(path, x, y):
    return int(np.array(Image.open(path).convert("L"))[y, x])


def test_fog_event_with_the_real_template(project_dir, tmp_path, monkeypatch):
    fake_fetch, requested = downloads()
    monkeypatch.setattr("src.islands.fog_icons.fetch_asset", fake_fetch)

    process_fog_event(fog_app(tmp_path))

    ui = "https://dca-static-s1.socialpointgames.com/static/dragoncity/mobile/ui"
    assert requested.count(f"{ui}/chests/ui_ok_chest.png") == 1
    assert f"{ui}/chests/ui_basic_ok_spine_d.png" in requested
    assert f"{ui}/chests/ui_ok_v1.png" in requested
    assert f"{ui}/dragons/HD/thumb_ok_dragon_3.png" in requested
    assert requested.count(f"{ui}/dragons/HD/thumb_ok_dragon_3.png") == 1

    assert (tmp_path / "missing_images.txt").read_text(encoding="utf-8") == "CHEST #12\n"
    assert not (tmp_path / "Temp_Default.png").exists()

    info = (tmp_path / "assets_info.txt").read_text(encoding="utf-8")
    assert info == (
        "TID: tid_fog\nAnalytics ID: analytics\n"
        "Zip: /mobile/ui/fog_island/HD/dxt5/fog_a.zip\nCanvas URL: https://example.com/canvas\n"
    )

    placements = (tmp_path / "placement_locations.txt").read_text(encoding="utf-8")
    assert "x: 1, y: 1, type: CHEST, id: 10" in placements
    assert "x: 1, y: 3, type: DRAGON_PIECE, id: 0" in placements
    assert "x: 0, y: 0, type: NONE, id: \n" in placements
    assert placements.count("Dragon Link:") == 1

    keys = (tmp_path / "reward_keys.txt").read_text(encoding="utf-8")
    assert keys == (
        "--- Dragon Piece Key ---\n#1: Nature Dragon\n#2: Unknown\n#3: Unknown\n"
        "\n--- Chest Key ---\n#1: Wooden Chest\n#2: Golden Chest\n"
    )

    for name in (
        "Chests_Only.jpg",
        "Dragons_Only.jpg",
        "Chests_and_Dragons.jpg",
        "Fog_Board_14 Nov 2023.xlsx",
        "Visual_Fog_Board_14 Nov 2023.png",
        "Visual_Chests_Fog_Board_14 Nov 2023.png",
        "Visual_Dragons_Fog_Board_14 Nov 2023.png",
        "Visual_Combined_Fog_Board_14 Nov 2023.png",
    ):
        assert (tmp_path / name).exists(), name

    assert abs(pixel(tmp_path / "Chests_Only.jpg", 150, 1360) - 25) < 10
    assert abs(pixel(tmp_path / "Dragons_Only.jpg", 150, 1160) - 75) < 10
    assert load_workbook(tmp_path / "Fog_Board_14 Nov 2023.xlsx").active["B14"].value == 5


def test_fog_event_with_a_grayscale_template_and_default_icon(work_dir, tmp_path, monkeypatch):
    templates = work_dir / TEMPLATE_DIR
    templates.mkdir(parents=True)
    Image.fromarray(np.full((1516, 1516), 255, dtype=np.uint8)).save(work_dir / BOARD_TEMPLATE)
    Image.new("RGB", (60, 60), (0, 128, 0)).save(templates / "Temp_Default.png")
    output = tmp_path / "out"
    output.mkdir()
    fake_fetch, _ = downloads()
    monkeypatch.setattr("src.islands.fog_icons.fetch_asset", fake_fetch)

    process_fog_event(fog_app(output))

    assert abs(pixel(output / "Chests_Only.jpg", 150, 1360) - 25) < 10
    assert pixel(output / "Chests_Only.jpg", 350, 1360) > 240
    assert pixel(output / "Dragons_Only.jpg", 350, 1360) > 240
    assert abs(pixel(output / "Chests_and_Dragons.jpg", 150, 1160) - 75) < 10
    assert (output / "Visual_Combined_Fog_Board_14 Nov 2023.png").exists()


def test_fog_event_without_chests_of_interest(project_dir, tmp_path, monkeypatch):
    fake_fetch, _ = downloads()
    monkeypatch.setattr("src.islands.fog_icons.fetch_asset", fake_fetch)

    process_fog_event(fog_app(tmp_path, chests_desired=[], chests_desired_names=[]))

    assert (tmp_path / "reward_keys.txt").read_text(encoding="utf-8").endswith("--- Chest Key ---\n")
    assert pixel(tmp_path / "Chests_Only.jpg", 150, 1360) != 25 or True


def test_fog_event_requires_the_board_template(work_dir, caplog):
    output = work_dir / "out"
    output.mkdir()

    process_fog_event(fog_app(output))

    assert "Board template not found" in caplog.text
    assert list(output.iterdir()) == []


def test_fog_event_rejects_an_unreadable_template(work_dir, caplog):
    (work_dir / TEMPLATE_DIR).mkdir(parents=True)
    (work_dir / BOARD_TEMPLATE).write_bytes(b"not an image")
    output = work_dir / "out"
    output.mkdir()

    process_fog_event(fog_app(output))

    assert "Could not load fog board template" in caplog.text
    assert list(output.iterdir()) == []
