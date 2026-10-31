import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import asyncio
import json
import os
import sys
import time
import threading
import logging
import numpy as np
from typing import Any, Callable, Dict, List, Optional, Tuple

import httpx
from dc_config import Config, FetchOptions
from dc_core import ConfigLanguage
from dc_localization import Localization

# Fix imports for local structure
from src.common.logger import setup_logging
from src.common.config_manager import ConfigManager
from src.islands.fog_island import process_fog_event
from src.islands.grid_island import process_grid_event
from src.islands.heroic_race import process_heroic_race
from src.islands.maze_island import process_maze_island
from src.islands.puzzle_island import process_puzzle_island
from src.islands.runner_island import process_runner_island
from src.islands.tower_island import process_tower_island
from src.utils.events import EVENT_SECTIONS, STATUS_STYLES, EventStatus, format_island_label, get_event_status

REQUEST_TIMEOUT_SECONDS: float = 120.0

class DragonCityEventApp(tk.Tk):
    """Main Application for Dragon City Event tools."""
    
    def __init__(self) -> None:
        super().__init__()
        self.logger: logging.Logger = setup_logging()
        self.logger.info("Initializing Dragon City Event App")
        
        self.config_manager: ConfigManager = ConfigManager()
        self.style_prefs: Dict[str, str] = {}
        self._set_style_preferences()
        
        self.data_view: Dict[str, Any] = {}
        self.dragon_info: Dict[int, Any] = {}
        self.chest_ids: Dict[int, Any] = {}
        self.localization: Localization = Localization(ConfigLanguage.ENGLISH, {})
        self.asset_versioning: Dict[str, Any] = {'chests': {}}
        
        # Internal state for islands
        self.event_number: int = 0
        self.chests_desired: List[int] = []
        self.chests_desired_names: List[str] = []
        self.event_fp: str = ""
        self.last_save_dir: str = os.getcwd()
        self.clock: Callable[[], float] = time.time

        # UI state variables
        self.event_chosen: tk.StringVar = tk.StringVar(value="Select One")
        self.event_dates_string: tk.StringVar = tk.StringVar(value="Select Event Type First")
        self.event_order_reversed: tk.IntVar = tk.IntVar(value=int(self.config_manager.app_config.get("event_date_order", 0)))
        self.select_all_chests: tk.IntVar = tk.IntVar(value=int(self.config_manager.app_config.get("chest_selection_status", 1)))
        
        self.asset_zip_fp: List[str] = ['/mobile/ui/', '/HD/dxt5/']
        self.image_formats: Dict[str, str] = {
            "DRAGON": "http://dci-static-s1.socialpointgames.com/static/dragoncity/mobile/ui/dragons/ui_",
            "CHEST": "https://dca-static-s1.socialpointgames.com/static/dragoncity/mobile/ui/chests/ui_",
            "DECO": "https://dca-static-s1.socialpointgames.com/static/dragoncity/mobile/ui/decorations/ui_",
            "HABITAT": "https://dca-static-s1.socialpointgames.com/static/dragoncity/mobile/ui/habitats/ui_",
            "BUILDING": "https://dca-static-s1.socialpointgames.com/static/dragoncity/mobile/ui/buildings/ui_"
        }

        # Setup GUI
        self.title("DC Event Script - Fork by DC Highs")
        self.geometry("450x300")
        self.resizable(False, False)
        self._setup_ui()
        
        # Load Initial Data
        self._load_initial_data()

    def _set_style_preferences(self) -> None:
        ui_cfg = self.config_manager.ui_config
        mode: str = ui_cfg.get("window_mode", "Dark Mode")
        themes = ui_cfg.get("themes", {})
        
        self.style_prefs = themes.get(mode, {
            "window_background": "black", 
            "window_foreground": "white",
            "menu_background": "#333333",
            "menu_foreground": "white"
        })

    def _load_initial_data(self) -> None:
        """Fetches game configuration and translations."""
        credentials: Dict[str, str] = self.config_manager.get_credentials()
        
        # Fallback to sys args if .env is empty
        if not credentials['userId'] and len(sys.argv) >= 3:
            credentials = {'userId': sys.argv[1], 'authToken': sys.argv[2]}
            
        if not credentials['userId'] or not credentials['authToken']:
            self.logger.warning("No credentials found in .env or sys args.")
            
        try:
            asyncio.run(self._fetch_game_data(credentials))

            # Parse Chests and Dragons
            for chest in self.data_view.get('chests', {}).get('chests', []):
                self.chest_ids[chest['id']] = {"chest_name_key": chest['chest_name_key'], "img_name": chest['img_name']}
            
            for item in self.data_view.get('items', []):
                if item.get('group_type') == 'DRAGON':
                    self.dragon_info[item['id']] = item
                    
            for asset in self.data_view.get('asset_versioning', {}).get('chests', []):
                self.asset_versioning['chests'][asset['name']] = {
                    'Format': asset['format'], 
                    "Version": asset['asset_version']
                }
            self.logger.info("Data loaded successfully.")
            
        except Exception as e:
            self.logger.error(f"Failed to load data: {e}")
            messagebox.showerror("Error", f"Failed to load game data: {e}")

    async def _fetch_game_data(self, credentials: Dict[str, str]) -> None:
        """Fetches the game configuration sections and the English translations."""
        url: str = self.config_manager.get_game_config_url()

        if not url:
            raise ValueError("DC_GAME_CONFIG_URL is not set in the .env file.")

        options: FetchOptions = FetchOptions(
            url=url,
            user_id=credentials['userId'],
            auth_token=credentials['authToken']
        )

        # Social Point's dynamic URLs do not always present a valid certificate
        async with httpx.AsyncClient(verify=False, timeout=REQUEST_TIMEOUT_SECONDS, follow_redirects=True) as client:
            self.logger.info("Fetching game configuration...")
            game_config = await Config.fetch(options, client)
            self.data_view = game_config.config.sections

        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS, follow_redirects=True) as client:
            self.logger.info("Fetching translations...")
            self.localization = await Localization.create(ConfigLanguage.ENGLISH, client)

    def _setup_ui(self) -> None:
        self.configure(bg=self.style_prefs.get("window_background", "black"))
        
        canvas: tk.Canvas = tk.Canvas(self, bg=self.style_prefs.get("window_background", "black"), highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)
        
        # Event Type List
        tk.Label(self, text="Event Type", bg=self.style_prefs.get("window_background", "black"), fg=self.style_prefs.get("window_foreground", "white")).place(x=20, y=20)
        
        self.event_listbox: tk.Listbox = tk.Listbox(self, selectmode="SINGLE", exportselection=0)
        self.event_listbox.configure(
            bg=self.style_prefs.get("menu_background", "#333"),
            fg=self.style_prefs.get("menu_foreground", "white"),
            selectbackground=self.style_prefs.get("menu_list_active_background", "blue")
        )
        types: List[str] = ["Fog Island", "Grid Island", "Heroic Race", "Maze Island", "Puzzle Island", "Runner Island", "Tower Island"]
        for idx, name in enumerate(types):
            self.event_listbox.insert(idx, name)
            
        self.event_listbox.bind('<<ListboxSelect>>', self._on_event_type_select)
        self.event_listbox.place(x=20, y=50, width=120, height=150)
        
        # Event Dates List
        tk.Label(self, text="Available Events", bg=self.style_prefs.get("window_background", "black"), fg=self.style_prefs.get("window_foreground", "white")).place(x=160, y=20)
        
        date_frame: tk.Frame = tk.Frame(self)
        date_frame.place(x=160, y=50, width=240, height=150)
        
        scrollbar: tk.Scrollbar = tk.Scrollbar(date_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.dates_listbox: tk.Listbox = tk.Listbox(date_frame, selectmode="SINGLE", yscrollcommand=scrollbar.set, exportselection=0)
        self.dates_listbox.configure(
            bg=self.style_prefs.get("menu_background", "#333"),
            fg=self.style_prefs.get("menu_foreground", "white")
        )
        self.dates_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.dates_listbox.yview)
        
        # Actions
        btn_start: tk.Button = tk.Button(self, text="Process Event", command=self._start_processing)
        btn_start.place(x=20, y=220, width=120)
        
        btn_save: tk.Button = tk.Button(self, text="Save JSON", command=self._save_game_data)
        btn_save.place(x=160, y=220, width=120)

        btn_creds: tk.Button = tk.Button(self, text="API Credentials", command=self._show_credentials_dialog)
        btn_creds.place(x=300, y=220, width=120)

        # Status
        self.status_label: tk.Label = tk.Label(self, text="", bg=self.style_prefs.get("window_background", "black"))
        self.status_label.place(x=20, y=260)
        self._build_status_legend()

    def _build_status_legend(self) -> None:
        """Explains the colors of the event list."""
        legend: List[Tuple[str, EventStatus, int]] = [
            ("Active", EventStatus.ACTIVE, 200),
            ("Upcoming", EventStatus.UPCOMING, 262),
            ("Past", EventStatus.PAST, 345),
        ]
        for text, status, x in legend:
            tk.Label(self, text=text, bg=STATUS_STYLES[status]["background"], fg="black", width=8).place(x=x, y=262)

    def _show_credentials_dialog(self) -> None:
        """Shows a dialog to update the API credentials and the game configuration endpoint."""
        dialog = tk.Toplevel(self)
        dialog.title("API Credentials")
        dialog.geometry("360x280")
        dialog.configure(bg=self.style_prefs.get("window_background", "black"))

        credentials = self.config_manager.get_credentials()
        user_entry = self._add_labeled_entry(dialog, "User ID:", credentials['userId'])
        token_entry = self._add_labeled_entry(dialog, "Auth Token:", credentials['authToken'])
        url_entry = self._add_labeled_entry(dialog, "Endpoint URL:", self.config_manager.get_game_config_url())

        def save() -> None:
            self._save_credentials(dialog, user_entry.get(), token_entry.get(), url_entry.get())

        tk.Button(dialog, text="Save & Persist", command=save).pack(pady=15)

    def _add_labeled_entry(self, parent: tk.Misc, label: str, value: str) -> tk.Entry:
        """Adds a label (readable in both themes) with its entry below it."""
        tk.Label(
            parent,
            text=label,
            bg=self.style_prefs.get("window_background", "black"),
            fg=self.style_prefs.get("window_foreground", "white")
        ).pack(pady=5)
        entry = tk.Entry(parent, width=45)
        entry.insert(0, value)
        entry.pack()
        return entry

    def _save_credentials(self, dialog: tk.Toplevel, user_id: str, auth_token: str, game_config_url: str) -> None:
        """Persists the dialog values when none of them is empty."""
        user_id, auth_token, game_config_url = user_id.strip(), auth_token.strip(), game_config_url.strip()

        if not (user_id and auth_token and game_config_url):
            messagebox.showwarning("Error", "Fields cannot be empty")
            return

        self.config_manager.set_credentials(user_id, auth_token, game_config_url)
        messagebox.showinfo("Success", "Credentials saved and persisted!")
        dialog.destroy()

    def _save_game_data(self) -> None:
        """Saves the current game data to a JSON file chosen by the user."""
        if not self.data_view:
            messagebox.showwarning("Warning", "There is no game data to save.")
            return

        file_path: str = filedialog.asksaveasfilename(
            parent=self,
            title="Save game data",
            initialdir=self.last_save_dir,
            initialfile="game_data.json",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if not file_path:
            return

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.data_view, f, indent=4)
            self.last_save_dir = os.path.dirname(file_path)
            self.logger.info(f"Game data saved to {file_path}")
            messagebox.showinfo("Success", f"Game data saved to {file_path}")
        except Exception as e:
            self.logger.error(f"Failed to save game data: {e}")
            messagebox.showerror("Error", f"Failed to save game data: {e}")

    def _on_event_type_select(self, event: tk.Event) -> None:
        selection: tuple = self.event_listbox.curselection()
        if not selection: return
        
        event_name: str = self.event_listbox.get(selection[0])
        self.event_chosen.set(event_name)
        self.logger.info(f"Selected event type: {event_name}")
        self._update_dates_list()

    def _update_dates_list(self) -> None:
        self.dates_listbox.delete(0, tk.END)
        section: Optional[str] = EVENT_SECTIONS.get(self.event_chosen.get())

        if not section or section not in self.data_view:
            self.dates_listbox.insert(0, "No data available")
            return

        now: int = int(self.clock())
        islands: List[Dict[str, Any]] = self.data_view[section].get('islands', [])
        for idx, island in enumerate(islands):
            self.dates_listbox.insert(tk.END, format_island_label(idx, island))
            self.dates_listbox.itemconfig(idx, **STATUS_STYLES[get_event_status(island, now)])

    def _get_selected_island_index(self) -> Optional[int]:
        selection: tuple = self.dates_listbox.curselection()
        if not selection: return None
        text: str = self.dates_listbox.get(selection[0])
        try:
            return int(text.split(']')[0][1:])
        except (IndexError, ValueError):
            return None

    def _start_processing(self) -> None:
        idx: Optional[int] = self._get_selected_island_index()
        if idx is None:
            messagebox.showwarning("Warning", "Please select an event date.")
            return
            
        self.event_number = idx
        self.event_dates_string.set(self.dates_listbox.get(self.dates_listbox.curselection()[0]))
        
        # Prepare output dir
        event_name: str = self.event_chosen.get().replace(" ", "_")
        safe_date_str: str = self.event_dates_string.get().replace(" ", "_").replace("[", "").replace("]", "")
        self.event_fp = os.path.join("output", event_name, safe_date_str)
        if not os.path.exists(self.event_fp):
            os.makedirs(self.event_fp)

        # Mock chests for now or trigger selection popup
        self.chests_desired = [] 
        self.chests_desired_names = []
        
        self.status_label.config(text="Processing...", fg="orange")
        threading.Thread(target=self._run_event_logic).start()

    def _run_event_logic(self) -> None:
        start_time: float = time.time()
        try:
            event_type: str = self.event_chosen.get()
            if event_type == "Fog Island":
                process_fog_event(self)
            elif event_type == "Grid Island":
                process_grid_event(self)
            elif event_type == "Heroic Race":
                process_heroic_race(self)
            elif event_type == "Maze Island":
                process_maze_island(self)
            elif event_type == "Puzzle Island":
                process_puzzle_island(self)
            elif event_type == "Runner Island":
                process_runner_island(self)
            elif event_type == "Tower Island":
                process_tower_island(self)
            
            self.logger.info(f"Finished processing {event_type} in {time.time() - start_time:.2f}s")
            self.after(0, lambda: self.status_label.config(text="Completed!", fg="green"))
        except Exception as e:
            self.logger.error(f"Error during event processing: {e}", exc_info=True)
            self.after(0, lambda: self.status_label.config(text="Failed!", fg="red"))
            self.after(0, lambda err=e: messagebox.showerror("Error", str(err)))

def main() -> None:
    """Poetry entry point."""
    app = DragonCityEventApp()
    app.mainloop()

if __name__ == "__main__":
    main()
