# ------------------------------------------------------------------------------------------
# commands
# ------------------------------------------------------------------------------------------

import pickle
import os
import platform
import subprocess
import tomllib
import csv
from pathlib import Path

from .prompt_gateway import PromptGateway
from .iterator import Iterator, PICKLE_NAME
from . import ding

# ------------------------------------------------------------------------------------------

package_folder = Path(__file__).resolve().parent
parent_folder = package_folder.parent
settings_path = parent_folder / "settings.toml"

CSV_NAME = "procrustean_output"

# ------------------------------------------------------------------------------------------

def inquire():

    if settings_path.exists():
    
        settings = _load_settings(settings_path)

        # initialize the two main objects
        gate = PromptGateway(settings)
        iterator = Iterator(gate)

        # start the process
        iterator.resume_inquiry()
        _print_to_csv(iterator.filled_entries)
        print(ding.DING)

    else:
        open_settings()
        print("Save settings and try again.")


def resume():

    iterator = _load_pickle(PICKLE_NAME)
    
    iterator.resume_inquiry()
    _print_to_csv(iterator.filled_entries)
    print(ding.DING)

# ------------------------------------------------------------------------------------------

def open_settings() -> None:

    if not settings_path.exists():
        print("File settings.toml not found. Creating new one...")
        reset()

    _open_file(settings_path)


def reset() -> None:

    default_settings_path = package_folder / "default_settings.toml"

    if not default_settings_path.exists():
        raise FileNotFoundError(f"Could not find: {default_settings_path}")

    default_content = default_settings_path.read_text(encoding="utf-8")
    settings_path.write_text(default_content, encoding="utf-8")
    
# ------------------------------------------------------------------------------------------
# i/o
# ------------------------------------------------------------------------------------------

def _load_pickle(filename):
    with open(filename, "rb") as f:
        return pickle.load(f)

def _load_settings(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return tomllib.loads(f.read())
    
# ------------------------------------------------------------------------------------------

def _print_to_csv(data):
    with open(f"{CSV_NAME}.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        for key, values in data.items():
            writer.writerow([key, *values])

# ------------------------------------------------------------------------------------------

def _open_file(path: str | Path) -> None:
    path = Path(path)

    system = platform.system()

    if system == "Windows":
        os.startfile(path)

    elif system == "Darwin":  # macOS
        subprocess.run(["open", path], check=True)

    elif system == "Linux":
        subprocess.run(["xdg-open", path], check=True)

    else:
        raise RuntimeError(f"Unsupported operating system: {system}")
