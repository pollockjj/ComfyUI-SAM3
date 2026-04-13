#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def _detect_comfy_root() -> Path:
    configured_root = os.environ.get("COMFY_ROOT")
    if configured_root:
        return Path(configured_root).expanduser().resolve()

    script_dir = Path(__file__).resolve().parent
    if script_dir.parent.name == "custom_nodes":
        return script_dir.parent.parent.resolve()

    raise RuntimeError("Unable to determine COMFY_ROOT for ComfyUI-SAM3 uninstall.")


def _ensure_comfy_python() -> None:
    comfy_root = _detect_comfy_root()
    target_python = comfy_root / ".venv" / "bin" / "python"
    current_python = Path(sys.executable).resolve()
    if current_python == target_python.resolve():
        return
    os.execv(str(target_python), [str(target_python), str(Path(__file__).resolve())])


_ensure_comfy_python()

from installer import uninstall_everything


if __name__ == "__main__":
    print(json.dumps(uninstall_everything(), indent=2, sort_keys=True))
