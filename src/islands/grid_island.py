import logging
import os
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

CELL_SIZE = 100
EMPTY_COLOR = 255
DESIRED_CHEST_COLOR = 75
OTHER_CHEST_COLOR = 150
DRAGON_COLOR = 0
WALL_WIDTH = 7
WALL_COLOR = 0
LABEL_COLOR = 255
FONT_SIZE = 40
LABEL_LINE_HEIGHT = 50


def build_board_grid(
    squares: List[Dict[str, Any]], board_size: List[int], chests_desired: List[int]
) -> Tuple[np.ndarray, List[int]]:
    """One pixel per square, colored by what it holds, and the ids of the squares worth labeling."""
    board_grid: np.ndarray = np.full(board_size, EMPTY_COLOR, dtype='uint8')
    locations_of_interest: List[int] = []

    for square in squares:
        x, y = square['x'] - 1, square['y'] - 1
        if square['type'] == 'CHEST':
            if square['type_id'] in chests_desired:
                board_grid[x, y] = DESIRED_CHEST_COLOR
                locations_of_interest.append(square['id'])
            else:
                board_grid[x, y] = OTHER_CHEST_COLOR
        elif square['type'] == 'DRAGON':
            board_grid[x, y] = DRAGON_COLOR
            locations_of_interest.append(square['id'])

    return board_grid, locations_of_interest


def expand_board(board_grid: np.ndarray) -> np.ndarray:
    """Turns every square pixel into a CELL_SIZE x CELL_SIZE block."""
    return np.repeat(np.repeat(board_grid, CELL_SIZE, axis=0), CELL_SIZE, axis=1)


def draw_walls(board: np.ndarray, squares: List[Dict[str, Any]]) -> None:
    for square in squares:
        if "wall" not in square:
            continue

        x_w, y_w = (square['x'] - 1) * CELL_SIZE, (square['y'] - 1) * CELL_SIZE
        if 'V' in square['wall']:
            board[x_w: x_w + WALL_WIDTH, y_w: y_w + CELL_SIZE] = WALL_COLOR
        if 'H' in square['wall']:
            board[x_w: x_w + CELL_SIZE, y_w: y_w + WALL_WIDTH] = WALL_COLOR


def add_border(board: np.ndarray) -> None:
    board[0, :] = WALL_COLOR
    board[-1, :] = WALL_COLOR
    board[:, 0] = WALL_COLOR
    board[:, -1] = WALL_COLOR


def label_position(square: Dict[str, Any]) -> Tuple[int, int]:
    cost_text: str = str(square['claim_cost'])
    return (
        CELL_SIZE * (square['x'] - 1) + 20 * (4 - len(cost_text)),
        CELL_SIZE * (square['y'] - 1),
    )


def chest_label(chests_desired: List[int], chest_type_id: int) -> Optional[str]:
    try:
        return str(chests_desired.index(chest_type_id) + 1)
    except ValueError:
        return None


def draw_square_labels(draw: ImageDraw.ImageDraw, font: ImageFont.FreeTypeFont, app: Any, locations_of_interest: List[int]) -> None:
    """Draws every claim cost and a chest number or dragon tag (D1, D2...) on the squares of interest."""
    with open(os.path.join(app.event_fp, "dragon_list.txt"), 'w') as dragon_list:
        dragon_count: int = 1

        for square in app.data_view['grid_island']['squares']:
            if square['claim_cost'] <= 0:
                continue

            x_pos, y_pos = label_position(square)
            draw.text((x_pos, y_pos), str(square['claim_cost']), fill=LABEL_COLOR, font=font)

            if square['id'] not in locations_of_interest:
                continue

            tag: Optional[str] = None
            if square['type'] == 'CHEST':
                tag = chest_label(app.chests_desired, square['type_id'])
            elif square['type'] == 'DRAGON':
                name: str = app.localization.get_dragon_name(square['type_id']) or f"Dragon {square['type_id']}"
                tag = f"D{dragon_count}"
                dragon_list.write(f"{tag}: {name}\n")
                dragon_count += 1

            if tag is not None:
                draw.text((x_pos, y_pos + LABEL_LINE_HEIGHT), tag, fill=LABEL_COLOR, font=font)


def write_chest_key(app: Any) -> None:
    with open(os.path.join(app.event_fp, "grid_key.txt"), 'w') as key_file:
        for index, name in enumerate(app.chests_desired_names):
            key_file.write(f"#{index + 1} - {name}\n")


def process_grid_event(app: Any) -> None:
    """Processes Grid Island event data."""
    start_time: float = time.perf_counter()
    logger.info("Starting Grid Island event processing")

    grid_data: Dict[str, Any] = app.data_view['grid_island']
    island_info: Dict[str, Any] = grid_data['islands'][app.event_number]
    episode_info: Dict[str, Any] = grid_data['episodes'][app.event_number]
    squares: List[Dict[str, Any]] = grid_data['squares']

    board_grid, locations_of_interest = build_board_grid(squares, episode_info['board_size'], app.chests_desired)
    board: np.ndarray = expand_board(board_grid)
    draw_walls(board, squares)
    add_border(board)

    image: Image.Image = Image.fromarray(np.transpose(board))
    font: ImageFont.FreeTypeFont = ImageFont.truetype("arial.ttf", FONT_SIZE)
    draw_square_labels(ImageDraw.Draw(image), font, app, locations_of_interest)

    event_start: str = time.strftime("%d %b %Y", time.gmtime(island_info['start_ts']))
    image.save(os.path.join(app.event_fp, f"Grid_Board_{event_start}.jpg"))
    write_chest_key(app)

    logger.info(f"Grid Island processing completed in {time.perf_counter() - start_time:.2f}s")
