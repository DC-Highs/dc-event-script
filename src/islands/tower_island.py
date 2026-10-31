import logging
import os
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from PIL import Image

from src.utils.image_processing import load_image_as_array

logger = logging.getLogger(__name__)

TEMPLATE_PATH = os.path.join("assets", "templates", "Tower_Template_DO_NOT_DELETE.jpg")
LEGACY_TEMPLATE_PATH = os.path.join("Archive", "Tower_Island", "Tower_Template_DO_NOT_DELETE.jpg")
CELL_SIZE = 100
FLOOR_HEIGHT_IN_SQUARES = 5
SQUARE_COLORS: Dict[str, int] = {
    'CATAPULT': 150,
    'SINGLE_REWARD': 100,
    'SINGLE_DRAGON_PIECE': 175,
    'FINAL_DRAGON_SQUARE': 0,
}


def load_tower_template() -> Optional[np.ndarray]:
    """Loads the empty tower, falling back to the legacy location when the template is missing."""
    path: str = TEMPLATE_PATH if os.path.exists(TEMPLATE_PATH) else LEGACY_TEMPLATE_PATH
    return load_image_as_array(path)


def square_bounds(shape: Tuple[int, ...], x: int, y: int) -> Tuple[int, int, int, int]:
    """Pixel rows and columns `(y_start, y_end, x_start, x_end)` of a square, clipped to the template."""
    floor_gap: int = FLOOR_HEIGHT_IN_SQUARES * int((y - 1) / FLOOR_HEIGHT_IN_SQUARES)
    y_bottom: int = shape[0] - (CELL_SIZE * (y - 1) + y + floor_gap)
    y_top: int = shape[0] - (CELL_SIZE * (y - 1) + y + CELL_SIZE + floor_gap)
    x_start: int = CELL_SIZE * (x - 1) + x
    x_end: int = (CELL_SIZE + 1) * x
    return max(0, y_top), min(shape[0], y_bottom), max(0, x_start), min(shape[1], x_end)


def mark_squares(tower_array: np.ndarray, squares: List[Dict[str, Any]]) -> None:
    """Paints the squares that hold something (catapults, rewards, dragon pieces and the final dragon)."""
    for square in squares:
        color: Optional[int] = SQUARE_COLORS.get(square.get('type', ''))
        if color is None:
            continue

        y_start, y_end, x_start, x_end = square_bounds(tower_array.shape, square['x'], square['y'])
        tower_array[y_start:y_end, x_start:x_end] = color


def process_tower_island(app: Any) -> None:
    """Processes Tower Island event data."""
    start_time: float = time.perf_counter()
    logger.info("Starting Tower Island event processing")

    tower_array: Optional[np.ndarray] = load_tower_template()
    if tower_array is None:
        logger.error("Could not load tower template.")
        return

    tower_data: Dict[str, Any] = app.data_view['tower_island']
    event_info: Dict[str, Any] = tower_data['islands'][app.event_number]
    event_start: str = time.strftime("%d %b %Y", time.gmtime(event_info['start_ts']))

    mark_squares(tower_array, tower_data.get('squares', []))

    with open(os.path.join(app.event_fp, f"Tower_Island_Key_{event_start}.txt"), 'w') as report:
        report.write("Tower Island Rewards Key\n")

    Image.fromarray(tower_array).save(os.path.join(app.event_fp, f"Tower_Map_{event_start}.jpg"))
    logger.info(f"Tower Island processing completed in {time.perf_counter() - start_time:.2f}s")
