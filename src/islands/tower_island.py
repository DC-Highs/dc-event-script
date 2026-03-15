import time
import logging
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, Any, List, Optional, Tuple

from src.utils.image_processing import load_image_as_array

logger = logging.getLogger(__name__)

def process_tower_island(app: Any) -> None:
    """Processes Tower Island event data."""
    start_time: float = time.perf_counter()
    logger.info("Starting Tower Island event processing")

    # Assets configuration
    template_path: str = os.path.join("assets", "templates", "Tower_Template_DO_NOT_DELETE.jpg")
    if not os.path.exists(template_path):
        # Fallback to older logic if assets missing
        template_path = os.path.join("Archive", 'Tower_Island', 'Tower_Template_DO_NOT_DELETE.jpg')
        
    tower_array: Optional[np.ndarray] = load_image_as_array(template_path)
    if tower_array is None:
        logger.error("Could not load tower template.")
        return

    tower_data: Dict[str, Any] = app.data_view['tower_island']
    # Use selected event number
    event_info: Dict[str, Any] = tower_data['islands'][app.event_number]
    
    event_start_str: str = time.strftime("%d %b %Y", time.gmtime(event_info['start_ts']))
    report_path: str = os.path.join(app.event_fp, f"Tower_Island_Key_{event_start_str}.txt")
    output_img_path: str = os.path.join(app.event_fp, f"Tower_Map_{event_start_str}.jpg")

    # Marking locations on board
    for square in tower_data.get('squares', []):
        draw_rect: bool = False
        color: int = 255
        
        sq_type: str = square.get('type', '')
        if sq_type == 'CATAPULT':
            color = 150
            draw_rect = True
        elif sq_type == 'SINGLE_REWARD':
            color = 100
            draw_rect = True
        elif sq_type == 'SINGLE_DRAGON_PIECE':
            color = 175
            draw_rect = True
        elif sq_type == 'FINAL_DRAGON_SQUARE':
            color = 0
            draw_rect = True
            
        if draw_rect:
            y, x = square['y'], square['x']
            # Original complex coordinate mapping for the Tower board
            y1: int = tower_array.shape[0] - (100 * (y - 1) + y + 5 * int((y - 1) / 5))
            y2: int = tower_array.shape[0] - (100 * (y - 1) + y + 100 + 5 * int((y - 1) / 5))
            x1: int = 100 * (x - 1) + x
            x2: int = 101 * x
            
            # Bound checking
            y2 = max(0, y2)
            y1 = min(tower_array.shape[0], y1)
            x1 = max(0, x1)
            x2 = min(tower_array.shape[1], x2)
            
            tower_array[y2:y1, x1:x2] = color

    img: Image.Image = Image.fromarray(tower_array)
    # Output file creation
    with open(report_path, 'w') as f:
        f.write("Tower Island Rewards Key\n")
        # Simplified reward list
        
    img.save(output_img_path)
    logger.info(f"Tower Island processing completed in {time.perf_counter() - start_time:.2f}s")
