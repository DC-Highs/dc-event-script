import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont
import logging
from typing import Tuple, Optional, Any

logger = logging.getLogger(__name__)

def load_image_as_array(path: str) -> Optional[np.ndarray]:
    """Loads an image and returns it as a numpy array."""
    try:
        return np.array(Image.open(path))
    except Exception as e:
        logger.error(f"Error loading image {path}: {e}")
        return None

def apply_transparency_mask(image_array: np.ndarray) -> np.ndarray:
    """Applies a white background to transparent pixels."""
    if image_array.ndim < 3 or image_array.shape[2] < 4:
        return image_array
    
    out_array = np.copy(image_array)
    mask = image_array[:, :, 3] != 255
    out_array[mask] = [255, 255, 255, 255]
    return out_array

def resize_icon(image_array: np.ndarray, size: Tuple[int, int] = (60, 60)) -> Image.Image:
    """Resizes an image array to the specified icon size."""
    if image_array.ndim >= 3 and image_array.shape[2] == 4:
        rgb_part = image_array[:, :, :3]
    else:
        rgb_part = image_array
        
    resized = cv2.resize(rgb_part, dsize=size, interpolation=cv2.INTER_CUBIC)
    return Image.fromarray(resized)

def draw_text_with_offset(
    draw_obj: ImageDraw.ImageDraw, 
    position: Tuple[int, int], 
    text: str, 
    font: ImageFont.FreeTypeFont, 
    color: Any, 
    y_offset: int = 0
) -> None:
    """Helper to draw text with an optional vertical offset."""
    x, y = position
    draw_obj.text((x, y + y_offset), text, fill=color, font=font)
