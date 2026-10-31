import json
import os
import time
import tkinter as tk
from tkinter import filedialog, messagebox

import httpx
import pytest

import src.main as main_module
from src.main import DragonCityEventApp

CONFIG_URL = "https://config.example.com/game-config"

GAME_CONFIG = {
    "chests": {"chests": [{"id": 1, "chest_name_key": "tid_chest", "img_name": "wood_chest"}], "rewards": []},
    "items": [
        {"id": 1000, "group_type": "DRAGON", "img_name_mobile": "nature"},
        {"id": 5, "group_type": "BUILDING"},
    ],
    "asset_versioning": {"chests": [{"name": "wood_chest", "format": "spine", "asset_version": 2}]},
    "fog_island": {"islands": [{"start_ts": 1_700_000_000, "end_ts": 1_700_086_400}, {}]},
    "maze_island": {"islands": [{"availability": {"from": 1_700_000_000, "to": 1_700_172_800}}]},
}


class Dialogs:
    """Records the message boxes instead of opening them."""

    def __init__(self, monkeypatch):
        self.calls = []

        for name in ("showinfo", "showwarning", "showerror"):
            monkeypatch.setattr(messagebox, name, lambda title, message, _name=name, **kw: self.calls.append((_name, message)))

    def kinds(self):
        return [kind for kind, _ in self.calls]

    def last(self):
        return self.calls[-1]


class Network:
    """Answers the game config and translation requests of the app."""

    def __init__(self, monkeypatch):
        self.requests = []
        self.config_status = 200
        self.config = {"game_data": {"config": GAME_CONFIG}}
        real_client = httpx.AsyncClient

        def handler(request: httpx.Request) -> httpx.Response:
            self.requests.append(request)

            if request.url.host == "config.example.com":
                if self.config_status != 200:
                    return httpx.Response(self.config_status)

                return httpx.Response(200, json=self.config)

            return httpx.Response(200, json=[{"tid_unit_1000_name": "Nature Dragon"}, {"tid_chest": "Wooden Chest"}])

        monkeypatch.setattr(httpx, "AsyncClient", lambda **kw: real_client(transport=httpx.MockTransport(handler), **kw))


@pytest.fixture
def dialogs(monkeypatch):
    return Dialogs(monkeypatch)


@pytest.fixture
def network(monkeypatch):
    return Network(monkeypatch)


@pytest.fixture
def credentials(monkeypatch):
    monkeypatch.setenv("DC_GAME_CONFIG_URL", CONFIG_URL)
    monkeypatch.setenv("DC_USER_ID", "42")
    monkeypatch.setenv("DC_AUTH_TOKEN", "secret-token")


def create_with_retries(attempts=8):
    """On Windows, Tcl/Tk sometimes fails to load its own script files (init.tcl, tk.tcl) when interpreters
    are created back to back, which surfaces as different TclError messages. The failure is transient, so
    creating the window is simply retried."""
    for attempt in range(attempts):
        try:
            return DragonCityEventApp()
        except tk.TclError:
            if attempt == attempts - 1:
                raise

            time.sleep(0.5)


@pytest.fixture
def make_app(work_dir, dialogs, network, credentials):
    apps = []

    def create():
        app = create_with_retries()
        app.withdraw()
        app.after = lambda delay, callback, *args: callback(*args)
        apps.append(app)
        return app

    yield create

    for app in apps:
        app.destroy()


@pytest.fixture
def app(make_app):
    return make_app()


def select(listbox, index):
    listbox.selection_clear(0, tk.END)
    listbox.selection_set(index)


def choose_event(app, name, index=0):
    app.event_listbox.selection_clear(0, tk.END)
    app.event_listbox.selection_set(app.event_listbox.get(0, tk.END).index(name))
    app._on_event_type_select(None)

    if app.dates_listbox.size():
        select(app.dates_listbox, index)


def test_startup_loads_the_configuration_and_translations(app, network):
    assert app.title() == "DC Event Script - Fork by DC Highs"
    assert not app.resizable()[0]
    assert app.event_listbox.get(0, tk.END)[0] == "Fog Island"
    assert app.chest_ids == {1: {"chest_name_key": "tid_chest", "img_name": "wood_chest"}}
    assert list(app.dragon_info) == [1000]
    assert app.asset_versioning["chests"] == {"wood_chest": {"Format": "spine", "Version": 2}}
    assert app.localization.get_dragon_name(1000) == "Nature Dragon"
    assert app.data_view["fog_island"]["islands"][0]["start_ts"] == 1_700_000_000

    config_request = network.requests[0]
    assert config_request.method == "POST"
    assert dict(config_request.url.params) == {"authToken": "secret-token", "userId": "42"}


def test_startup_uses_the_command_line_credentials(make_app, network, monkeypatch):
    monkeypatch.delenv("DC_USER_ID")
    monkeypatch.delenv("DC_AUTH_TOKEN")
    monkeypatch.setattr("sys.argv", ["start", "7", "cli-token"])

    make_app()

    assert dict(network.requests[0].url.params) == {"authToken": "cli-token", "userId": "7"}


def test_startup_warns_when_there_are_no_credentials(make_app, network, monkeypatch, caplog):
    monkeypatch.delenv("DC_USER_ID")
    monkeypatch.delenv("DC_AUTH_TOKEN")
    monkeypatch.setattr("sys.argv", ["start"])

    with caplog.at_level("WARNING"):
        make_app()

    assert "No credentials found" in caplog.text


def test_startup_reports_request_failures(make_app, network, dialogs):
    network.config_status = 500

    app = make_app()

    assert dialogs.last()[0] == "showerror"
    assert "Failed to load game data" in dialogs.last()[1]
    assert app.data_view == {}


def test_startup_requires_the_config_url(make_app, dialogs, monkeypatch):
    monkeypatch.delenv("DC_GAME_CONFIG_URL")

    make_app()

    assert "DC_GAME_CONFIG_URL is not set" in dialogs.last()[1]


def test_unknown_window_mode_falls_back_to_a_default_theme(work_dir, make_app):
    (work_dir / "settings.json").write_text(json.dumps({"ui": {"window_mode": "Neon", "themes": {}}}), encoding="utf-8")

    app = make_app()

    assert app.style_prefs["window_background"] == "black"


def test_event_dates_are_listed_per_event_type(app):
    choose_event(app, "Fog Island")
    assert app.event_chosen.get() == "Fog Island"
    assert app.dates_listbox.get(0, tk.END) == (
        "[0] 14 Nov 2023 - 15 Nov 2023",
        "[1] 01 Jan 1970 - 01 Jan 1970",
    )

    choose_event(app, "Maze Island")
    assert app.dates_listbox.get(0, tk.END) == ("[0] 14 Nov 2023 - 16 Nov 2023",)

    choose_event(app, "Tower Island")
    assert app.dates_listbox.get(0, tk.END) == ("No data available",)


def test_selecting_nothing_keeps_the_current_event(app):
    app.event_listbox.selection_clear(0, tk.END)

    app._on_event_type_select(None)

    assert app.event_chosen.get() == "Select One"


def test_selected_island_index(app):
    assert app._get_selected_island_index() is None

    choose_event(app, "Fog Island", index=1)
    assert app._get_selected_island_index() == 1

    choose_event(app, "Tower Island")
    assert app._get_selected_island_index() is None


def test_processing_requires_a_selected_event(app, dialogs):
    app._start_processing()

    assert dialogs.last() == ("showwarning", "Please select an event date.")


def test_processing_creates_the_output_folder_and_runs_the_island(app, monkeypatch):
    calls = []
    monkeypatch.setattr(main_module, "process_fog_event", lambda current: calls.append(current.event_fp))

    class ImmediateThread:
        def __init__(self, target):
            self.target = target

        def start(self):
            self.target()

    monkeypatch.setattr(main_module.threading, "Thread", lambda target: ImmediateThread(target))

    for _ in range(2):
        choose_event(app, "Fog Island", index=1)
        app._start_processing()

    expected = os.path.join("output", "Fog_Island", "1_01_Jan_1970_-_01_Jan_1970")
    assert calls == [expected, expected]
    assert os.path.isdir(expected)
    assert app.event_number == 1
    assert app.status_label.cget("text") == "Completed!"


@pytest.mark.parametrize(
    "event_name, function",
    [
        ("Fog Island", "process_fog_event"),
        ("Grid Island", "process_grid_event"),
        ("Heroic Race", "process_heroic_race"),
        ("Maze Island", "process_maze_island"),
        ("Puzzle Island", "process_puzzle_island"),
        ("Runner Island", "process_runner_island"),
        ("Tower Island", "process_tower_island"),
    ],
)
def test_each_event_type_runs_its_island(app, monkeypatch, event_name, function):
    calls = []

    for name in (
        "process_fog_event", "process_grid_event", "process_heroic_race", "process_maze_island",
        "process_puzzle_island", "process_runner_island", "process_tower_island",
    ):
        monkeypatch.setattr(main_module, name, lambda current, _name=name: calls.append(_name))

    app.event_chosen.set(event_name)
    app._run_event_logic()

    assert calls == [function]
    assert app.status_label.cget("text") == "Completed!"


def test_unknown_event_type_runs_nothing(app, monkeypatch):
    app.event_chosen.set("Select One")

    app._run_event_logic()

    assert app.status_label.cget("text") == "Completed!"


def test_island_failures_are_reported(app, dialogs, monkeypatch):
    def explode(current):
        raise RuntimeError("island exploded")

    monkeypatch.setattr(main_module, "process_grid_event", explode)
    app.event_chosen.set("Grid Island")

    app._run_event_logic()

    assert app.status_label.cget("text") == "Failed!"
    assert dialogs.last() == ("showerror", "island exploded")


def test_save_game_data_asks_where_to_save(app, dialogs, monkeypatch, tmp_path):
    asked = []
    answers = ["", str(tmp_path / "chosen.json"), str(tmp_path / "missing" / "x.json")]
    monkeypatch.setattr(filedialog, "asksaveasfilename", lambda **kw: asked.append(kw) or answers.pop(0))

    app._save_game_data()
    assert dialogs.calls == []

    app._save_game_data()
    assert json.loads((tmp_path / "chosen.json").read_text(encoding="utf-8"))["items"][0]["id"] == 1000
    assert dialogs.last()[0] == "showinfo"
    assert app.last_save_dir == str(tmp_path)

    app._save_game_data()
    assert dialogs.last()[0] == "showerror"
    assert asked[1]["initialfile"] == "game_data.json" and asked[2]["initialdir"] == str(tmp_path)


def test_save_game_data_needs_data(app, dialogs):
    app.data_view = {}

    app._save_game_data()

    assert dialogs.last() == ("showwarning", "There is no game data to save.")


def open_credentials_dialog(app):
    app._show_credentials_dialog()
    dialog = [child for child in app.winfo_children() if isinstance(child, tk.Toplevel)][-1]
    entries = [child for child in dialog.winfo_children() if isinstance(child, tk.Entry)]
    button = [child for child in dialog.winfo_children() if isinstance(child, tk.Button)][0]
    return dialog, entries, button


def test_credentials_dialog_persists_the_credentials(app, dialogs, work_dir):
    dialog, (user_entry, token_entry), button = open_credentials_dialog(app)
    assert (user_entry.get(), token_entry.get()) == ("42", "secret-token")

    user_entry.delete(0, tk.END)
    user_entry.insert(0, " 99 ")
    token_entry.delete(0, tk.END)
    token_entry.insert(0, " new-token ")
    button.invoke()

    saved = json.loads((work_dir / "settings.json").read_text(encoding="utf-8"))
    assert saved["credentials"] == {"userId": "99", "authToken": "new-token"}
    assert dialogs.last()[0] == "showinfo"
    assert not dialog.winfo_exists()


def test_credentials_dialog_rejects_empty_fields(app, dialogs, work_dir):
    dialog, (user_entry, _), button = open_credentials_dialog(app)
    user_entry.delete(0, tk.END)

    button.invoke()

    assert dialogs.last() == ("showwarning", "Fields cannot be empty")
    assert not (work_dir / "settings.json").exists()
    assert dialog.winfo_exists()


def test_main_runs_the_application(monkeypatch):
    started = []

    class FakeApp:
        def mainloop(self):
            started.append("mainloop")

    monkeypatch.setattr(main_module, "DragonCityEventApp", FakeApp)

    main_module.main()

    assert started == ["mainloop"]
