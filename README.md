# Dragon City Event Script (Refactored)

This project is a Dragon City event tool that generates event data, images, and Excel reports. It has been refactored for better performance, modularity, and Python community standards.

## Authors

- **Apod** - Original Creator
- **Marcuth** ([me@marcuth.dev](mailto:me@marcuth.dev)) - Lead Refactor & Collaborator

## Features

- **Modular Architecture**: Clean separation between GUI, island logic, and utilities.
- **Built on DC Highs**: The game configuration, translations, static files and event status come from [`dchighs`](https://pypi.org/project/dchighs/) (`dc_config`, `dc_localization`, `dc_assets`, `dc_statistics` and `dc_core`).
- **Event activity colors**: The list of events is colored by activity, with a legend below it:
  - red: past events
  - green: active events
  - yellow: upcoming events
- **API Credentials dialog**: Edit the user id, the auth token and the endpoint URL of the game configuration inside the app.
- **Save JSON**: Choose where the downloaded game configuration is saved.
- **Type Safety**: Full use of Python type annotations.
- **Improved Logging**: Native Python logging with timestamped files.
- **Tested**: 100% test coverage, run on every push through GitHub Actions.
- **Aesthetic GUI**: Refined Tkinter interface with support for dark/light themes.

## How to Run

### 1. Prerequisites
You need [Poetry](https://python-poetry.org/) installed.

### 2. Install Dependencies
```bash
poetry install
```

### 3. Setup Environment
Copy `.env.example` to `.env` and fill it in:
```bash
cp .env.example .env
```

| Variable | Description |
| --- | --- |
| `DC_USER_ID` | Your Dragon City user id |
| `DC_AUTH_TOKEN` | Your Dragon City auth token |
| `DC_GAME_CONFIG_URL` | Endpoint that serves the game configuration |

You can also set these values from the **API Credentials** button inside the app. They are then saved in `settings.json`, which is ignored by git and must never be shared. A value in `.env` takes precedence over `settings.json`. If no user id is set, the app falls back to the first two command line arguments (`poetry run start <user id> <auth token>`).

### 4. Execute
```bash
poetry run start
```

Pick an event type, pick one of the events (colored by activity) and press **Process Event**. The files are generated in `output/<event type>/<event dates>/`.

## Building the Executable

To generate a standalone Windows executable:
```bash
poetry run build
```
The output will be in the `dist/` folder.

> The build bundles `settings.json`. Since credentials saved from the app live in that file, do not distribute an executable built after saving them.

## Project Structure

- `src/`: Core source code.
  - `main.py`: Main GUI application.
  - `islands/`: Logic for events like Fog, Grid, Heroic Race, etc. The Fog Island is split into `fog_icons.py` (icon downloads), `fog_board.py` (boards and spreadsheet) and `fog_reports.py` (text reports).
  - `utils/`: Helpers for events (activity status), static file downloads (`static_assets.py`), networking and image manipulation.
  - `common/`: Logging and configuration management.
- `tests/`: Automated tests.
- `assets/`: Static templates and resources.
- `output/`: Processed event data and images.
- `logs/`: Application execution logs.

## Running the Tests

```bash
poetry run pytest          # run the tests
poetry run pytest --cov    # run the tests with coverage (fails below 100%)
```

The tests never touch the network, your `.env` file or your credentials. They run on every push and pull request
through GitHub Actions (`.github/workflows/tests.yml`).
