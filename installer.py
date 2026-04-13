from __future__ import annotations

import platform
import re
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent
ASSETS_DIR = REPO_ROOT / "assets"
REQUIREMENTS_FILE = REPO_ROOT / "requirements.txt"
SPECIAL_WHEEL_INDEXES = {
    "cc-torch": "https://pozzettiandrea.github.io/cuda-wheels/cc-torch/",
    "torch-generic-nms": "https://pozzettiandrea.github.io/cuda-wheels/torch-generic-nms/",
    "flash-attn": "https://pozzettiandrea.github.io/cuda-wheels/flash-attn/",
}

TORCH_TAG_PREFERENCES = {
    "cc-torch": ("2.11", "2.10", "2.9"),
    "torch-generic-nms": ("2.11", "2.10", "2.9"),
    "flash-attn": ("2.11", "2.10", "2.9"),
}


def detect_comfy_root() -> Path:
    import os

    configured_root = os.environ.get("COMFY_ROOT")
    if configured_root:
        comfy_root = Path(configured_root).expanduser().resolve()
        if comfy_root.exists():
            return comfy_root

    if REPO_ROOT.parent.name == "custom_nodes":
        return REPO_ROOT.parent.parent.resolve()

    sibling_comfy = (REPO_ROOT.parent / "ComfyUI").resolve()
    if sibling_comfy.exists():
        return sibling_comfy

    raise RuntimeError("Unable to determine COMFY_ROOT for ComfyUI-SAM3 install.")


def copy_assets(comfy_root: Path) -> list[Path]:
    destination_dir = comfy_root / "input"
    destination_dir.mkdir(parents=True, exist_ok=True)
    copied: list[Path] = []
    for source in sorted(ASSETS_DIR.iterdir()):
        if not source.is_file():
            continue
        destination = destination_dir / source.name
        shutil.copy2(source, destination)
        copied.append(destination)
    return copied


def install_requirements() -> None:
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE)],
        cwd=str(REPO_ROOT),
    )


def _read_index(package_name: str) -> str:
    url = SPECIAL_WHEEL_INDEXES[package_name]
    with urllib.request.urlopen(url) as response:
        return response.read().decode("utf-8")


def _select_linux_wheel(package_name: str, html: str) -> str:
    py_tag = f"cp{sys.version_info.major}{sys.version_info.minor}"
    machine = platform.machine().lower()
    hrefs = re.findall(r'href="([^"]+\.whl)"', html)
    linux_hrefs = []
    for href in hrefs:
        filename = href.rsplit("/", 1)[-1]
        lower_name = filename.lower()
        if py_tag not in lower_name:
            continue
        if machine not in lower_name and "manylinux" not in lower_name and "linux" not in lower_name:
            continue
        linux_hrefs.append((href, lower_name))

    if not linux_hrefs:
        raise RuntimeError(f"No Linux wheel candidates found for {package_name}.")

    preferred_torch_tags = TORCH_TAG_PREFERENCES[package_name]
    for torch_tag in preferred_torch_tags:
        token_variants = (f"torch{torch_tag}", f"torch{torch_tag.replace('.', '')}")
        for href, lower_name in linux_hrefs:
            if "cu130" not in lower_name:
                continue
            if any(token in lower_name for token in token_variants):
                return href

    raise RuntimeError(f"No matching wheel found for {package_name} on this host.")


def resolve_special_wheel_urls() -> dict[str, str]:
    resolved: dict[str, str] = {}
    for package_name in SPECIAL_WHEEL_INDEXES:
        html = _read_index(package_name)
        resolved[package_name] = _select_linux_wheel(package_name, html)
    return resolved


def install_special_wheels() -> dict[str, str]:
    resolved = resolve_special_wheel_urls()
    for package_name in ("cc-torch", "torch-generic-nms", "flash-attn"):
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", resolved[package_name]],
            cwd=str(REPO_ROOT),
        )
    return resolved


def install_everything() -> dict[str, object]:
    comfy_root = detect_comfy_root()
    install_requirements()
    wheel_urls = install_special_wheels()
    copied_assets = copy_assets(comfy_root)
    return {
        "comfy_root": str(comfy_root),
        "wheel_urls": wheel_urls,
        "copied_assets": [str(path) for path in copied_assets],
    }
