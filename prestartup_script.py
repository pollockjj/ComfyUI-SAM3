"""ComfyUI-SAM3 prestartup asset copy."""

import os
from pathlib import Path
import shutil


SCRIPT_PATH = Path(__file__)
SCRIPT_DIR = SCRIPT_PATH.resolve().parent
ASSETS_DIR = SCRIPT_DIR / "assets"


def _find_comfyui_dir() -> Path:
    comfy_root = os.environ.get("COMFY_ROOT")
    if comfy_root:
        return Path(comfy_root)

    candidates = [SCRIPT_PATH.absolute(), SCRIPT_PATH.resolve()]
    for candidate in candidates:
        parents = [candidate.parent, *candidate.parents]
        for parent in parents:
            if parent.name == "custom_nodes":
                return parent.parent
            if (parent / "main.py").exists() and (parent / "folder_paths.py").exists():
                return parent

    # Fallback for legacy in-tree installs.
    return SCRIPT_DIR.parent.parent


COMFYUI_DIR = _find_comfyui_dir()
INPUT_DIR = COMFYUI_DIR / "input"


def copy_assets() -> None:
    if not ASSETS_DIR.exists():
        return
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    for source in ASSETS_DIR.rglob("*"):
        if not source.is_file():
            continue
        relative_path = source.relative_to(ASSETS_DIR)
        target = INPUT_DIR / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


copy_assets()
