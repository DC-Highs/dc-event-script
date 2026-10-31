import os
from typing import Any, Dict, Optional, TextIO, Union

import numpy as np
from PIL import Image

from src.utils.image_processing import (
    apply_transparency_mask,
    load_image_as_array,
    load_image_from_bytes,
    resize_icon,
)
from src.utils.static_assets import chest_sprite_downloader, dragon_thumbnail_downloader, fetch_asset

ICON_SIZE = (60, 60)
DEFAULT_ICON_PATH = os.path.join("assets", "templates", "Temp_Default.png")


def load_default_icon() -> Image.Image:
    """Icon used when a chest image cannot be downloaded or decoded."""
    array: Optional[np.ndarray] = load_image_as_array(DEFAULT_ICON_PATH)
    return Image.fromarray(array if array is not None else np.zeros((*ICON_SIZE, 3), dtype=np.uint8))


def build_icon(data: bytes) -> Optional[Image.Image]:
    """Turns downloaded image bytes into a board icon."""
    array: Optional[np.ndarray] = load_image_from_bytes(data)
    if array is None:
        return None
    return resize_icon(apply_transparency_mask(array), ICON_SIZE)


class FogIconCollector:
    """Downloads the chest and dragon icons of a Fog Island and logs where each square got its icon."""

    def __init__(self, app: Any, fog_data: Dict[str, Any], dragon_reward_map: Dict[int, int], location_log: TextIO) -> None:
        self.app = app
        self.fog_data = fog_data
        self.dragon_reward_map = dragon_reward_map
        self.location_log = location_log
        self.default_icon: Image.Image = load_default_icon()
        self.chest_icons: Dict[int, Image.Image] = {}
        self.dragon_icons: Dict[int, Image.Image] = {}

    def collect(self) -> None:
        for square in self.fog_data['squares']:
            grid_id: Union[str, int] = self._collect_square(square)
            self.location_log.write(f"x: {square['x']}, y: {square['y']}, type: {square['type']}, id: {grid_id}\n")

    def _collect_square(self, square: Dict[str, Any]) -> Union[str, int]:
        if square['type'] == 'CHEST':
            return self._collect_chest(square['type_id'])
        if square['type'] == 'DRAGON_PIECE':
            return self._collect_dragon(square['reward_id'])
        return ''

    def _collect_chest(self, chest_type_id: int) -> int:
        if chest_type_id not in self.chest_icons:
            self.chest_icons[chest_type_id] = self._download_chest_icon(chest_type_id)
        return chest_type_id

    def _download_chest_icon(self, chest_type_id: int) -> Image.Image:
        chest_name: str = self.app.chest_ids[chest_type_id]['img_name']
        downloader = chest_sprite_downloader(chest_name, self.app.asset_versioning['chests'].get(chest_name))
        self.location_log.write(f"Chest Link: {downloader.url}\n")

        data: Optional[bytes] = fetch_asset(downloader)
        if data is None:
            self._record_missing_chest(chest_type_id)
            return self.default_icon

        icon: Optional[Image.Image] = build_icon(data)
        return icon if icon is not None else self.default_icon

    def _record_missing_chest(self, chest_type_id: int) -> None:
        with open(os.path.join(self.app.event_fp, "missing_images.txt"), 'a') as missing_file:
            missing_file.write(f"CHEST #{chest_type_id}\n")

    def _collect_dragon(self, reward_id: int) -> int:
        reward_index: int = self.dragon_reward_map[reward_id]
        if reward_index not in self.dragon_icons:
            self._download_dragon_icon(reward_index)
        return reward_index

    def _download_dragon_icon(self, reward_index: int) -> None:
        dragon_id: int = self.fog_data['rewards'][reward_index]['reward_id']
        downloader = dragon_thumbnail_downloader(self.app.dragon_info[dragon_id]['img_name_mobile'])

        data: Optional[bytes] = fetch_asset(downloader)
        icon: Optional[Image.Image] = build_icon(data) if data is not None else None
        if icon is not None:
            self.dragon_icons[reward_index] = icon
            self.location_log.write(f"Dragon Link: {downloader.url}\n")
