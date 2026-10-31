# Agent Guidelines for dc-event-script

## Project Overview

This is a Python-based Dragon City event tool that generates event data, images, and Excel files. The project consists of a main GUI (Dragon_City_Island_Events_GUI.py) and several island scripts in the Scripts/ folder.

## Running the Project

- **Main entry point**: `python Dragon_City_Island_Events_GUI.py`
- **Prerequisites**: Requires Python with dependencies installed (see below)
- **Credentials**: Can be passed as CLI args or stored in `Credentials.json` / `Credentials.txt`

## Dependencies

Required packages (install via pip):
- `requests` - HTTP requests
- `numpy` - Array operations
- `Pillow` (PIL) - Image processing
- `xlsxwriter` - Excel file generation
- `opencv-python` (cv2) - Image manipulation
- `urllib3` - URL handling (included with requests)

Install all at once:
```bash
pip install requests numpy Pillow xlsxwriter opencv-python urllib3
```

## Build/Lint/Test Commands

- **Run the main GUI**: `poetry run start`
- **Build executable**: `poetry run build`
- **Check all scripts**: `python -m py_compile src/**/*.py`
- **Run the tests**: `poetry run pytest`
- **Run the tests with coverage**: `poetry run pytest --cov` (fails below 100%)

Tests live in `tests/` (pytest). Keep the coverage at 100% and do not call the real network, `.env` or credentials from tests; the fixtures in `tests/conftest.py` already isolate them.

## Code Style Guidelines

### General Principles

- Write clean, readable code with meaningful variable names
- Keep functions focused on a single responsibility
- Use docstrings for module-level and class-level documentation
- Avoid deeply nested code; use early returns when possible

### Naming Conventions

- **Classes**: PascalCase (e.g., `GUI`, `Fog_Event_`)
- **Functions**: snake_case with trailing underscore for event handlers (e.g., `Event_Processing`, `Fog_Event_`)
- **Variables**: snake_case (e.g., `initial_fP`, `chest_ids`)
- **Constants**: UPPER_CASE (e.g., `TEMP_FP`, `IMAGE_FORMATS`)
- **Private methods**: prefix with underscore (e.g., `_internal_method`)

### Imports

- Standard library imports first, then third-party, then local
- Use explicit imports (avoid `from X import *`)
- Group related imports together
- Example:
```python
import json
import sys
import time

import requests
import numpy as np
import PIL.Image, PIL.ImageDraw, PIL.ImageFont

from Scripts.Fog_Island import Fog_Event_
```

### Formatting

- Indentation: 4 spaces (no tabs)
- Maximum line length: ~120 characters (soft limit)
- Use blank lines to separate logical sections
- Operators should have spaces around them (`a + b`, not `a+b`)
- No spaces around `=` in keyword arguments (`key=value`)

### Type Annotations

- Not currently used in this codebase, but adding type hints is encouraged for new code
- Example:
```python
def process_event(event_id: int, event_name: str) -> dict:
    ...
```

### Error Handling

- Use try/except blocks for operations that may fail (file I/O, network requests)
- Catch specific exceptions when possible
- Log or print meaningful error messages
- Example:
```python
try:
    urllib.request.urlretrieve(url, filepath)
except urllib.request.HTTPError:
    with open(missing_file, 'a') as f:
        f.write(f"Failed to download {url}\n")
```

### Comments

- Use inline comments sparingly to explain non-obvious logic
- Add docstrings for classes and complex functions
- Comment-out code should be removed, not left in place

### GUI Code (Tkinter)

- Use consistent spacing in geometry managers
- Store widget references as instance variables when needed
- Use `ttk` widgets where possible for better styling
- Keep callback functions focused

### File Operations

- Use context managers (`with open(...) as f:`) for file I/O
- Close files explicitly when not using context managers
- Use `json.load()` / `json.dump()` for JSON files

### Data Structures

- Use dictionaries for structured data (e.g., config, mappings)
- Use lists for sequential data
- Use numpy arrays for numerical operations and image data
- Avoid deeply nested data structures

### Performance Considerations

- Use numpy operations instead of Python loops where possible
- Cache repeated calculations
- Consider lazy loading for large assets

## Directory Structure

```
dc-event-script/
├── Dragon_City_Island_Events_GUI.py  # Main GUI entry point
├── Scripts/                           # Event script modules
│   ├── __init__.py
│   ├── Fog_Island.py
│   ├── Grid_Island.py
│   ├── Heroic_Race.py
│   ├── Maze_Island.py
│   ├── Puzzle_Island.py
│   ├── Runner_Island.py
│   ├── Tower_Island.py
│   └── Install_Required_Mods.py
├── Configuration.json                 # App configuration
├── Credentials.json                   # User credentials (do not commit)
├── Preferences.txt                    # GUI preferences
└── [Event_Folders]/                  # Generated output folders
    ├── Fog_Island/
    ├── Grid_Island/
    └── ...
```

## What NOT To Do

- Do NOT commit `Credentials.json`, `Credentials.txt`, or any file containing secrets
- Do NOT modify the .gitignore (if exists) to bypass secret handling
- Do NOT leave debug print statements in production code
- Do NOT use hardcoded URLs or API keys in the source code
- Do NOT commit large binary files (images, zips) to git

## Common Tasks

- **Add a new island type**: Create new script in `Scripts/`, import in main GUI, add to event menu
- **Modify existing island**: Edit the corresponding file in `Scripts/`
- **Change GUI styling**: Modify the `Preferences.txt` file or GUI code directly
- **Debug an event**: Check the generated output folder for logs and images