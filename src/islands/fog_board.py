import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np
import xlsxwriter
from PIL import Image, ImageDraw, ImageFont

from src.utils.image_processing import load_image_as_array

logger = logging.getLogger(__name__)

BOARD_TEMPLATE_PATH = os.path.join("assets", "templates", "Fog_Board_DO_NOT_DELETE.jpg")
BOARD_HEIGHT = 1515
CELL_SIZE = 100
CHEST_MARK = 25
DRAGON_MARK = 75
BLACK = 0
WHITE = 255
ICON_OFFSET = 15
COST_LABEL_OFFSET = (10, 75)
FONT_SIZE = 20
SHEET_LAST_ROW = 14

ALL_BOARD = "all"
CHESTS_BOARD = "chests"
DRAGONS_BOARD = "dragons"
BOTH_BOARD = "both"
VISUAL_FILE_PREFIXES = {
    ALL_BOARD: "Visual",
    CHESTS_BOARD: "Visual_Chests",
    DRAGONS_BOARD: "Visual_Dragons",
    BOTH_BOARD: "Visual_Combined",
}


def load_board_template() -> Optional[np.ndarray]:
    """Loads the empty Fog Island board; returns None (and logs why) when it is unavailable."""
    if not os.path.exists(BOARD_TEMPLATE_PATH):
        logger.error(f"Board template not found at {BOARD_TEMPLATE_PATH}")
        return None

    template: Optional[np.ndarray] = load_image_as_array(BOARD_TEMPLATE_PATH)
    if template is None:
        logger.error("Could not load fog board template.")
    return template


def cell_bounds(x: int, y: int) -> Tuple[int, int, int, int]:
    """Pixel rows and columns `(y1, y2, x1, x2)` covered by the board cell at `(x, y)`."""
    y1: int = BOARD_HEIGHT - (CELL_SIZE * (y + 1) + y)
    y2: int = BOARD_HEIGHT - (CELL_SIZE * y + y)
    x1: int = CELL_SIZE * x + x + 1
    x2: int = CELL_SIZE * (x + 1) + x + 1
    return y1, y2, x1, x2


def label_origin(x: int, y: int) -> Tuple[int, int]:
    """Top-left pixel of the text and icon of the cell at `(x, y)`."""
    return (
        CELL_SIZE * x + x + 5,
        BOARD_HEIGHT - (CELL_SIZE * (y + 1) + y + 5),
    )


@dataclass
class MarkedBoards:
    chests_only: np.ndarray
    dragons_only: np.ndarray
    chests_and_dragons: np.ndarray


def mark_boards(template: np.ndarray, squares: Iterable[Dict[str, Any]], chests_of_interest: List[int]) -> MarkedBoards:
    """Paints the squares of the chosen chests and of every dragon piece on copies of the template."""
    boards = MarkedBoards(np.copy(template), np.copy(template), np.copy(template))

    for square in squares:
        y1, y2, x1, x2 = cell_bounds(square['x'], square['y'])

        if 'type_id' in square and square['type_id'] in chests_of_interest:
            boards.chests_only[y1:y2, x1:x2] = CHEST_MARK
            boards.chests_and_dragons[y1:y2, x1:x2] = CHEST_MARK

        if square['type'] == 'DRAGON_PIECE':
            boards.dragons_only[y1:y2, x1:x2] = DRAGON_MARK
            boards.chests_and_dragons[y1:y2, x1:x2] = DRAGON_MARK

    return boards


def save_marked_boards(boards: MarkedBoards, folder: str) -> None:
    Image.fromarray(boards.chests_only).save(os.path.join(folder, 'Chests_Only.jpg'))
    Image.fromarray(boards.dragons_only).save(os.path.join(folder, 'Dragons_Only.jpg'))
    Image.fromarray(boards.chests_and_dragons).save(os.path.join(folder, 'Chests_and_Dragons.jpg'))


class VisualBoards:
    """The four illustrated boards (everything, chests, dragons and both) drawn from the same template."""

    def __init__(self, template: np.ndarray) -> None:
        base: np.ndarray = np.stack([template] * 3, axis=-1) if template.ndim == 2 else np.copy(template)
        self.images: Dict[str, Image.Image] = {name: Image.fromarray(base) for name in VISUAL_FILE_PREFIXES}
        self.draws: Dict[str, ImageDraw.ImageDraw] = {name: ImageDraw.Draw(image) for name, image in self.images.items()}
        self.font: ImageFont.FreeTypeFont = ImageFont.truetype("arial.ttf", FONT_SIZE)

    def paste_icon(self, icon: Image.Image, origin: Tuple[int, int], boards: Iterable[str]) -> None:
        position: Tuple[int, int] = (origin[0] + ICON_OFFSET, origin[1] + ICON_OFFSET)
        for name in boards:
            self.images[name].paste(icon, position)

    def draw_labels(self, origin: Tuple[int, int], text: str, cost_text: str, fill: int) -> None:
        cost_origin: Tuple[int, int] = (origin[0] + COST_LABEL_OFFSET[0], origin[1] + COST_LABEL_OFFSET[1])
        for name, draw in self.draws.items():
            if text and name == ALL_BOARD:
                draw.text(origin, text, fill=fill, font=self.font)
            draw.text(cost_origin, cost_text, fill=fill, font=self.font)

    def save(self, folder: str, base_name: str) -> None:
        for name, image in self.images.items():
            image.save(os.path.join(folder, f"{VISUAL_FILE_PREFIXES[name]}_{base_name}.png"))


def describe_square(
    square: Dict[str, Any],
    chests_of_interest: List[int],
    dragon_reward_map: Dict[int, int],
    chest_icons: Dict[int, Image.Image],
    dragon_icons: Dict[int, Image.Image],
) -> Tuple[str, int, Optional[Image.Image], Tuple[str, ...]]:
    """Label, text color, icon and the boards the icon goes on, for one square."""
    kind: str = square['type']

    if kind == 'CHEST':
        chest_id: int = square['type_id']
        icon: Image.Image = chest_icons[chest_id]
        if chest_id in chests_of_interest:
            label: str = f"Chest #{chests_of_interest.index(chest_id) + 1}"
            return label, WHITE, icon, (ALL_BOARD, CHESTS_BOARD, BOTH_BOARD)
        return "", BLACK, icon, (ALL_BOARD,)

    if kind == 'DRAGON_PIECE':
        dragon_icon: Optional[Image.Image] = dragon_icons.get(dragon_reward_map[square['reward_id']])
        return f"Dragon #{square['reward_id']}", WHITE, dragon_icon, (ALL_BOARD, DRAGONS_BOARD, BOTH_BOARD)

    if kind == 'NONE':
        return "Start", BLACK, None, ()
    if kind == 'STEP':
        return "Tutorial", BLACK, None, ()
    return "", BLACK, None, ()


def render_visual_boards(
    template: np.ndarray,
    squares: Iterable[Dict[str, Any]],
    chests_of_interest: List[int],
    dragon_reward_map: Dict[int, int],
    chest_icons: Dict[int, Image.Image],
    dragon_icons: Dict[int, Image.Image],
) -> VisualBoards:
    boards = VisualBoards(template)

    for square in squares:
        origin: Tuple[int, int] = label_origin(square['x'], square['y'])
        label, fill, icon, targets = describe_square(
            square, chests_of_interest, dragon_reward_map, chest_icons, dragon_icons
        )
        if icon is not None:
            boards.paste_icon(icon, origin, targets)
        boards.draw_labels(origin, label, f"cost:{square['claim_cost']}", fill)

    return boards


def write_cost_sheet(path: str, squares: Iterable[Dict[str, Any]]) -> None:
    """Writes the claim cost of every square into a spreadsheet laid out like the board."""
    workbook = xlsxwriter.Workbook(path)
    worksheet = workbook.add_worksheet()

    for square in squares:
        worksheet.write(SHEET_LAST_ROW - square['y'], square['x'], square['claim_cost'])

    workbook.close()
