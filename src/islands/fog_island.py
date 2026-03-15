import time
import os
import string
import logging
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import xlsxwriter
from typing import Dict, List, Any, Tuple, Optional

from src.utils.network import download_file, ensure_directory
from src.utils.image_processing import (
    load_image_as_array, 
    apply_transparency_mask, 
    resize_icon, 
    draw_text_with_offset
)

logger = logging.getLogger(__name__)

def process_fog_event(app: Any) -> None:
    """Processes the Fog Island event data and generates reports/images."""
    start_time: float = time.perf_counter()
    logger.info("Starting Fog Island event processing")

    fog_data: Dict[str, Any] = app.data_view['fog_island']
    event_info: Dict[str, Any] = fog_data['islands'][app.event_number]
    
    # Paths configuration
    base_assets_path: str = os.path.join("assets", "templates")
    board_template_path: str = os.path.join(base_assets_path, "Fog_Board_DO_NOT_DELETE.jpg")
    
    if not os.path.exists(board_template_path):
        logger.error(f"Board template not found at {board_template_path}")
        return

    board_array: Optional[np.ndarray] = load_image_as_array(board_template_path)
    if board_array is None:
        logger.error("Could not load fog board template.")
        return

    # Initialize board variants
    board_template: np.ndarray = np.copy(board_array)
    chests_only: np.ndarray = np.copy(board_array)
    dragons_only: np.ndarray = np.copy(board_array)
    chests_and_dragons: np.ndarray = np.copy(board_array)

    # Asset zip path (logging only)
    zip_filename: str = event_info['zip_file'].split('.')[0].split('/')[-1]
    asset_zip: str = f"{app.asset_zip_fp[0]}fog_island{app.asset_zip_fp[1]}{zip_filename}.zip"
    
    logger.debug(f"Event TID: {event_info['tid_name']}")
    
    # Prepare output directories
    ensure_directory(app.event_fp)
    
    # Save asset info
    with open(os.path.join(app.event_fp, "assets_info.txt"), 'w') as f:
        f.write(f"TID: {event_info['tid_name']}\n")
        f.write(f"Analytics ID: {event_info['analytics_id']}\n")
        f.write(f"Zip: {asset_zip}\n")
        f.write(f"Canvas URL: {event_info['canvas_assets_url']}\n")
    
    # Download and prepare icons
    temp_path: str = os.path.join(app.event_fp, "temp_icon.png")
    temp_default_path: str = os.path.join(base_assets_path, "Temp_Default.png")
    
    default_icon_arr: Optional[np.ndarray] = load_image_as_array(temp_default_path)
    default_icon: np.ndarray = default_icon_arr if default_icon_arr is not None else np.zeros((60, 60, 3), dtype=np.uint8)
    icon_size: Tuple[int, int] = (60, 60)
    
    rewards: Dict[str, Any] = {'CHEST': {}, 'DRAGON_PIECE': {}, 'Rewards': []}
    
    # Map desired chests
    chests_of_interest: List[int] = []
    for chest in app.chests_desired:
        if isinstance(chest, list):
            chests_of_interest.extend(chest)
        else:
            chests_of_interest.append(chest)
            
    # Process dragon rewards
    dragon_reward_map: Dict[int, int] = {drag['id']: idx for idx, drag in enumerate(fog_data["rewards"])}
    # Sort rewards by ID
    fog_data["rewards"] = sorted(fog_data["rewards"], key=lambda x: x['id'])

    location_log_path: str = os.path.join(app.event_fp, "placement_locations.txt")
    missing_images_path: str = os.path.join(app.event_fp, "missing_images.txt")

    with open(location_log_path, 'w') as loc_file:
        for square in fog_data['squares']:
            grid_id: Union[str, int] = ''
            dragon_url: str = ''
            
            if square['type'] == 'CHEST':
                grid_id = square['type_id']
                if grid_id not in rewards['CHEST']:
                    chest_name: str = app.chest_ids[grid_id]['img_name']
                    prefix: str = ""
                    suffix: str = ""
                    
                    if chest_name in app.asset_versioning['chests']:
                        version_info = app.asset_versioning['chests'][chest_name]
                        if version_info['Format'] == 'spine':
                            prefix = "basic_"
                        if version_info['Version'] != 1:
                            suffix = "_" + string.ascii_lowercase[version_info['Version']]
                    
                    chest_url: str = f"{app.image_formats['CHEST']}{prefix}{chest_name}{suffix}.png"
                    loc_file.write(f"Chest Link: {chest_url}\n")
                    
                    if download_file(chest_url, temp_path):
                        img_arr = load_image_as_array(temp_path)
                        if img_arr is not None:
                            processed_img = apply_transparency_mask(img_arr)
                            rewards['CHEST'][grid_id] = resize_icon(processed_img, icon_size)
                        else:
                            rewards['CHEST'][grid_id] = Image.fromarray(default_icon)
                    else:
                        with open(missing_images_path, 'a') as missing_file:
                            missing_file.write(f"CHEST #{grid_id}\n")
                        rewards['CHEST'][grid_id] = Image.fromarray(default_icon)

            elif square['type'] == 'DRAGON_PIECE':
                grid_id = dragon_reward_map[square['reward_id']]
                if grid_id not in rewards['DRAGON_PIECE']:
                    dragon_id: int = fog_data['rewards'][square['reward_id']-1]['reward_id']
                    dragon_img_name: str = app.dragon_info[dragon_id]['img_name_mobile']
                    dragon_url = f"https://dca-static-s1.socialpointgames.com/static/dragoncity/mobile/ui/dragons/HD/thumb_{dragon_img_name}_3.png"
                    
                    if download_file(dragon_url, temp_path):
                        img_arr = load_image_as_array(temp_path)
                        if img_arr is not None:
                            processed_img = apply_transparency_mask(img_arr)
                            rewards['DRAGON_PIECE'][grid_id] = {
                                "image": resize_icon(processed_img, icon_size),
                                "url": dragon_url
                            }
                            rewards["Rewards"].append(grid_id)
                            loc_file.write(f"Dragon Link: {dragon_url}\n")
            
            loc_file.write(f"x: {square['x']}, y: {square['y']}, type: {square['type']}, id: {grid_id}\n")

    # Mark board locations
    for square in fog_data['squares']:
        y_val: int = square['y']
        x_val: int = square['x']
        y1: int = 1515 - (100 * (y_val + 1) + y_val)
        y2: int = 1515 - (100 * y_val + y_val)
        x1: int = (100 * x_val + x_val + 1)
        x2: int = (100 * (x_val + 1) + x_val + 1)

        if 'type_id' in square and square['type_id'] in chests_of_interest:
            board_array[y1:y2, x1:x2] = 25
            chests_only[y1:y2, x1:x2] = 25
            chests_and_dragons[y1:y2, x1:x2] = 25
            
        if square['type'] == 'DRAGON_PIECE':
            board_array[y1:y2, x1:x2] = 75
            dragons_only[y1:y2, x1:x2] = 75
            chests_and_dragons[y1:y2, x1:x2] = 75

    # Save processed boards
    event_start_str: str = time.strftime("%d %b %Y", time.gmtime(event_info['start_ts']))
    board_filename_base: str = f"Fog_Board_{event_start_str}"
    
    Image.fromarray(chests_only).save(os.path.join(app.event_fp, 'Chests_Only.jpg'))
    Image.fromarray(dragons_only).save(os.path.join(app.event_fp, 'Dragons_Only.jpg'))
    Image.fromarray(chests_and_dragons).save(os.path.join(app.event_fp, 'Chests_and_Dragons.jpg'))
    
    # Visual Output Processing
    visual_base: np.ndarray
    if board_template.ndim == 2:
        visual_base = np.stack([board_template]*3, axis=-1)
    else:
        visual_base = np.copy(board_template)
        
    boards_visual: Dict[str, Image.Image] = {
        "all": Image.fromarray(visual_base),
        "chests": Image.fromarray(visual_base),
        "dragons": Image.fromarray(visual_base),
        "both": Image.fromarray(visual_base)
    }
    
    draw_objs: Dict[str, ImageDraw.ImageDraw] = {k: ImageDraw.Draw(v) for k, v in boards_visual.items()}
    
    # Excel setup
    excel_path: str = os.path.join(app.event_fp, f"{board_filename_base}.xlsx")
    workbook: xlsxwriter.Workbook = xlsxwriter.Workbook(excel_path)
    worksheet: xlsxwriter.worksheet.Worksheet = workbook.add_worksheet()
    
    font: ImageFont.FreeTypeFont = ImageFont.truetype("arial.ttf", 20)
    
    for square in fog_data['squares']:
        x_p: int = 100 * square['x'] + square['x'] + 5
        y_p: int = 1515 - (100 * (square['y'] + 1) + square['y'] + 5)
        
        output_text: str = ""
        cost_text: str = f"cost:{square['claim_cost']}"
        fill_color: int = 0 # Black
        
        if square['type'] == 'CHEST':
            grid_id = square['type_id']
            if grid_id in chests_of_interest:
                try:
                    chest_idx: int = chests_of_interest.index(grid_id) + 1
                    output_text = f"Chest #{chest_idx}"
                    fill_color = 255 # White
                except ValueError:
                    fill_color = 0
            
            # Place Icon
            if grid_id in rewards['CHEST']:
                icon: Image.Image = rewards['CHEST'][grid_id]
                boards_visual["all"].paste(icon, (x_p + 15, y_p + 15))
                if grid_id in chests_of_interest:
                    boards_visual["chests"].paste(icon, (x_p + 15, y_p + 15))
                    boards_visual["both"].paste(icon, (x_p + 15, y_p + 15))

        elif square['type'] == 'DRAGON_PIECE':
            grid_idx: int = dragon_reward_map[square['reward_id']]
            output_text = f"Dragon #{square['reward_id']}"
            fill_color = 255
            
            if grid_idx in rewards['DRAGON_PIECE']:
                icon = rewards['DRAGON_PIECE'][grid_idx]['image']
                boards_visual["all"].paste(icon, (x_p + 15, y_p + 15))
                boards_visual["dragons"].paste(icon, (x_p + 15, y_p + 15))
                boards_visual["both"].paste(icon, (x_p + 15, y_p + 15))

        elif square['type'] == 'NONE':
            output_text = "Start"
        elif square['type'] == 'STEP':
            output_text = "Tutorial"

        # Draw labels
        for k, draw in draw_objs.items():
            if output_text and k == "all":
                draw.text((x_p, y_p), output_text, fill=fill_color, font=font)
            draw.text((x_p + 10, y_p + 75), cost_text, fill=fill_color, font=font)
            
        worksheet.write(14 - square['y'], square['x'], square['claim_cost'])

    workbook.close()
    
    # Save visual boards
    boards_visual["all"].save(os.path.join(app.event_fp, f"Visual_{board_filename_base}.png"))
    boards_visual["chests"].save(os.path.join(app.event_fp, f"Visual_Chests_{board_filename_base}.png"))
    boards_visual["dragons"].save(os.path.join(app.event_fp, f"Visual_Dragons_{board_filename_base}.png"))
    boards_visual["both"].save(os.path.join(app.event_fp, f"Visual_Combined_{board_filename_base}.png"))

    # Generate keys
    with open(os.path.join(app.event_fp, "reward_keys.txt"), 'w') as key_file:
        key_file.write("--- Dragon Piece Key ---\n")
        for drag in fog_data['rewards']:
            name: str = app.local_dict.get(f"tid_unit_{drag['reward_id']}_name", "Unknown")
            key_file.write(f"#{drag['id']}: {name}\n")
            
        key_file.write("\n--- Chest Key ---\n")
        for idx, name in enumerate(app.chests_desired_names):
            key_file.write(f"#{idx+1}: {name}\n")

    logger.info(f"Fog Island processing completed in {time.perf_counter() - start_time:.2f}s")
