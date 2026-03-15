# Dragon City Event Script (Refactored)

This project is a Dragon City event tool that generates event data, images, and Excel reports. It has been refactored for better performance, modularity, and Python community standards.

## Authors

- **Apod** - Original Creator
- **Marcuth** ([me@marcuth.dev](mailto:me@marcuth.dev)) - Lead Refactor & Collaborator

## Features

- **Modular Architecture**: Clean separation between GUI, island logic, and utilities.
- **Type Safety**: Full use of Python type annotations.
- **Improved Logging**: Native Python logging with timestamped files.
- **Environment and Config**: Sensitive data moved to `.env`, application state in `Configuration.json`.
- **Aesthetic GUI**: Refined Tkinter interface with support for dark/light themes.

## How to Run

### 1. Prerequisites
You need [Poetry](https://python-poetry.org/) installed.

### 2. Install Dependencies
```bash
poetry install
```

### 3. Setup Environment
Copy `.env.example` to `.env` and fill in your credentials:
```bash
cp .env.example .env
```

### 4. Execute
```bash
poetry run start
```

## Building the Executable

To generate a standalone Windows executable:
```bash
poetry run build
```
The output will be in the `dist/` folder.

## Project Structure

- `src/`: Core source code.
  - `main.py`: Main GUI application.
  - `islands/`: Logic for events like Fog, Grid, Heroic Race, etc.
  - `utils/`: Helpers for networking and image manipulation.
  - `common/`: Logging and configuration management.
- `assets/`: Static templates and resources.
- `output/`: Processed event data and images.
- `logs/`: Application execution logs.
