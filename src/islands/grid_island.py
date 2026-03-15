import logging
import time
from PIL import Image, ImageDraw, ImageFont
import os
import numpy as np
from typing import Dict, Any, List, Optional

from src.utils.image_processing import load_image_as_array

logger = logging.getLogger(__name__)

def process_grid_event(app: Any) -> None:
    """Processes Grid Island event data."""
    start_time: float = time.perf_counter()
    logger.info("Starting Grid Island event processing")

    grid_data: Dict[str, Any] = app.data_view['grid_island']
    island_info: Dict[str, Any] = grid_data['islands'][app.event_number]
    episode_info: Dict[str, Any] = grid_data['episodes'][app.event_number]
    
    board_size: Tuple[int, int] = episode_info['board_size']
    # Use SP coordinates logic
    board_grid: np.ndarray = np.full(board_size, 255, dtype='uint8')
    
    locations_of_interest: List[int] = []
    for square in grid_data['squares']:
        x, y = square['x'] - 1, square['y'] - 1
        if square['type'] == 'CHEST':
            if square['type_id'] in app.chests_desired:
                board_grid[x, y] = 75
                locations_of_interest.append(square['id'])
            else:
                board_grid[x, y] = 150
        elif square['type'] == 'DRAGON':
            board_grid[x, y] = 0
            locations_of_interest.append(square['id'])

    # Expand pixels to 100x100 blocks
    expanded_board: np.ndarray = np.repeat(np.repeat(board_grid, 100, axis=0), 100, axis=1)

    # Draw walls
    wall_width: int = 7
    wall_color: int = 0
    for square in grid_data['squares']:
        if "wall" in square:
            x_w, y_w = (square['x'] - 1) * 100, (square['y'] - 1) * 100
            if 'V' in square['wall']:
                expanded_board[x_w : x_w + wall_width, y_w : y_w + 100] = wall_color
            if 'H' in square['wall']:
                expanded_board[x_w : x_w + 100, y_w : y_w + wall_width] = wall_color

    # Add border
    expanded_board[0, :] = wall_color
    expanded_board[-1, :] = wall_color
    expanded_board[:, 0] = wall_color
    expanded_board[:, -1] = wall_color

    # Convert to image
    img: Image.Image = Image.fromarray(np.transpose(expanded_board))
    
    # Draw labels
    draw: ImageDraw.ImageDraw = ImageDraw.Draw(img)
    font: ImageFont.FreeTypeFont = ImageFont.truetype("arial.ttf", 40)
    
    dragon_report_path: str = os.path.join(app.event_fp, "dragon_list.txt")
    with open(dragon_report_path, 'w') as f:
        dragon_count: int = 1
        for square in grid_data['squares']:
            if square['claim_cost'] > 0:
                cost_str: str = str(square['claim_cost'])
                x_pos: int = 100 * (square['x'] - 1) + 20 * (4 - len(cost_str))
                y_pos: int = 100 * (square['y'] - 1)
                draw.text((x_pos, y_pos), cost_str, fill=255, font=font)
                
                label_y: int = y_pos + 50
                if square['id'] in locations_of_interest:
                    if square['type'] == 'CHEST':
                        try:
                            idx: int = app.chests_desired.index(square['type_id']) + 1
                            draw.text((x_pos, label_y), str(idx), fill=255, font=font)
                        except ValueError:
                            pass
                    elif square['type'] == 'DRAGON':
                        name: str = app.local_dict.get(f"tid_unit_{square['type_id']}_name", f"Dragon {square['type_id']}")
                        f.write(f"D{dragon_count}: {name}\n")
                        draw.text((x_pos, label_y), f"D{dragon_count}", fill=255, font=font)
                        dragon_count += 1

    event_start: str = time.strftime("%d %b %Y", time.gmtime(island_info['start_ts']))
    final_img_path: str = os.path.join(app.event_fp, f"Grid_Board_{event_start}.jpg")
    img.save(final_img_path)

    # Save key
    with open(os.path.join(app.event_fp, "grid_key.txt"), 'w') as f:
        for i, name in enumerate(app.chests_desired_names):
            f.write(f"#{i+1} - {name}\n")

    logger.info(f"Grid Island processing completed in {time.perf_counter() - start_time:.2f}s")
