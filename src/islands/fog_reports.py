import os
from typing import Any, Dict, Iterable

from dc_localization import Localization


def write_assets_info(folder: str, asset_zip_fp: Iterable[str], event_info: Dict[str, Any]) -> None:
    """Writes the identifiers and download locations of the event assets."""
    prefix, suffix = asset_zip_fp
    zip_filename: str = event_info['zip_file'].split('.')[0].split('/')[-1]

    with open(os.path.join(folder, "assets_info.txt"), 'w') as f:
        f.write(f"TID: {event_info['tid_name']}\n")
        f.write(f"Analytics ID: {event_info['analytics_id']}\n")
        f.write(f"Zip: {prefix}fog_island{suffix}{zip_filename}.zip\n")
        f.write(f"Canvas URL: {event_info['canvas_assets_url']}\n")


def write_reward_keys(
    folder: str,
    rewards: Iterable[Dict[str, Any]],
    localization: Localization,
    chest_names: Iterable[str],
) -> None:
    """Writes the legend that maps the numbers drawn on the boards to dragon and chest names."""
    with open(os.path.join(folder, "reward_keys.txt"), 'w') as key_file:
        key_file.write("--- Dragon Piece Key ---\n")
        for reward in rewards:
            name: str = localization.get_dragon_name(reward['reward_id']) or "Unknown"
            key_file.write(f"#{reward['id']}: {name}\n")

        key_file.write("\n--- Chest Key ---\n")
        for index, name in enumerate(chest_names):
            key_file.write(f"#{index + 1}: {name}\n")
