"""ComfyUI-SAM3 prestartup asset copy."""

from pathlib import Path
import shutil


SCRIPT_DIR = Path(__file__).resolve().parent
COMFYUI_DIR = SCRIPT_DIR.parent.parent
ASSETS_DIR = SCRIPT_DIR / "assets"
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
