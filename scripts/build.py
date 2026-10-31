import os
import subprocess
import sys

def run_build():
    """Builds the standalone executable using PyInstaller."""
    print("🚀 Starting build process...")
    
    args = [
        "pyinstaller",
        "--noconsole",
        "--onefile",
        "--add-data", "assets;assets",
        "--add-data", "settings.json;.",
        "--name", "DragonCityEvents",
        "src/main.py"
    ]
    
    try:
        subprocess.run(args, check=True)
        print("\n✅ Build successful! The executable can be found in the 'dist' folder.")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Build failed with error: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("\n❌ PyInstaller not found. Please run 'poetry install' first.")
        sys.exit(1)

if __name__ == "__main__":
    run_build()
