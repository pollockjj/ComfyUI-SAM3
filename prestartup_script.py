"""ComfyUI-SAM3 Prestartup Script."""

import importlib.util
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
INSTALLER_PATH = SCRIPT_DIR / "installer.py"
SPEC = importlib.util.spec_from_file_location("comfyui_sam3_installer", INSTALLER_PATH)
INSTALLER = importlib.util.module_from_spec(SPEC)
assert SPEC is not None and SPEC.loader is not None
SPEC.loader.exec_module(INSTALLER)

INSTALLER.ensure_installed()
