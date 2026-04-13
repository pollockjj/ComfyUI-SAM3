from __future__ import annotations

import json
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
RECEIPT_FILE = REPO_ROOT / ".sam3_install_receipt.json"
SITE_PACKAGES = Path(sys.prefix) / f"lib/python{sys.version_info.major}.{sys.version_info.minor}/site-packages"
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
SPECIAL_WHEEL_PACKAGE_ORDER = ("cc-torch", "torch-generic-nms", "flash-attn")


def _normalize_requirement_name(requirement: str) -> str:
    return re.split(r"[<>=!~]", requirement, 1)[0].strip()


MANAGED_REQUIREMENTS = tuple(
    _normalize_requirement_name(line)
    for line in REQUIREMENTS_FILE.read_text().splitlines()
    if line.strip() and not line.lstrip().startswith("#")
)
MANAGED_PACKAGES = MANAGED_REQUIREMENTS + SPECIAL_WHEEL_PACKAGE_ORDER


def log_action(message: str) -> None:
    print(f"[SAM3 installer] {message}", flush=True)


def write_receipt(receipt: dict[str, object]) -> None:
    log_action(f"writing install receipt {RECEIPT_FILE}")
    RECEIPT_FILE.write_text(json.dumps(receipt, indent=2, sort_keys=True))
    log_action(f"wrote install receipt {RECEIPT_FILE}")


def read_receipt() -> dict[str, object] | None:
    if not RECEIPT_FILE.exists():
        return None
    return json.loads(RECEIPT_FILE.read_text())


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
        log_action(f"copying asset {source} -> {destination}")
        shutil.copy2(source, destination)
        log_action(f"copied asset {destination}")
        copied.append(destination)
    return copied


def install_requirements() -> None:
    log_action(f"installing requirements from {REQUIREMENTS_FILE} into {sys.executable}")
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE)],
        cwd=str(REPO_ROOT),
    )
    log_action(f"installed requirements from {REQUIREMENTS_FILE}")


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
    for package_name in SPECIAL_WHEEL_PACKAGE_ORDER:
        log_action(f"installing wheel {package_name} from {resolved[package_name]}")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", resolved[package_name]],
            cwd=str(REPO_ROOT),
        )
        log_action(f"installed wheel {package_name}")
    return resolved


def remove_assets(asset_paths: tuple[str, ...], comfy_root: Path) -> dict[str, list[str]]:
    destination_dir = comfy_root / "input"
    removed: list[str] = []
    missing: list[str] = []
    for asset_path in asset_paths:
        destination = Path(asset_path)
        if destination.parent != destination_dir:
            log_action(f"skipping out-of-scope asset path {destination}")
            missing.append(str(destination))
            continue
        log_action(f"removing managed asset {destination}")
        if destination.exists():
            destination.unlink()
            log_action(f"removed asset {destination}")
            removed.append(str(destination))
        else:
            log_action(f"asset not present {destination}")
            missing.append(str(destination))
    return {"removed": removed, "missing": missing}


def uninstall_packages(package_names: tuple[str, ...]) -> dict[str, list[str]]:
    removed: list[str] = []
    missing: list[str] = []
    for package_name in package_names:
        log_action(f"uninstalling managed package {package_name} from {SITE_PACKAGES}")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "uninstall", "-y", package_name],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        if stdout:
            log_action(stdout.replace("\n", " | "))
        if stderr:
            log_action(stderr.replace("\n", " | "))
        if result.returncode == 0:
            log_action(f"uninstalled package {package_name}")
            removed.append(package_name)
        elif "Skipping" in stdout:
            log_action(f"package not present {package_name}")
            missing.append(package_name)
        else:
            raise RuntimeError(f"Failed uninstall for package {package_name}: {stdout} {stderr}".strip())
    return {"removed": removed, "missing": missing}


def install_everything() -> dict[str, object]:
    comfy_root = detect_comfy_root()
    log_action(f"resolved COMFY_ROOT={comfy_root}")
    log_action(f"managed site-packages target={SITE_PACKAGES}")
    install_requirements()
    wheel_urls = install_special_wheels()
    copied_assets = copy_assets(comfy_root)
    receipt = {
        "comfy_root": str(comfy_root),
        "site_packages": str(SITE_PACKAGES),
        "managed_packages": list(MANAGED_PACKAGES),
        "wheel_urls": wheel_urls,
        "copied_assets": [str(path) for path in copied_assets],
    }
    write_receipt(receipt)
    return receipt


def uninstall_everything() -> dict[str, object]:
    comfy_root = detect_comfy_root()
    log_action(f"resolved COMFY_ROOT={comfy_root}")
    log_action(f"managed site-packages target={SITE_PACKAGES}")
    prior_receipt = read_receipt()
    package_names = tuple(prior_receipt.get("managed_packages", MANAGED_PACKAGES)) if prior_receipt else MANAGED_PACKAGES
    asset_paths = tuple(prior_receipt.get("copied_assets", [])) if prior_receipt else tuple(
        str((comfy_root / "input" / source.name))
        for source in sorted(ASSETS_DIR.iterdir())
        if source.is_file()
    )
    package_receipt = uninstall_packages(package_names)
    asset_receipt = remove_assets(asset_paths, comfy_root)
    receipt = {
        "comfy_root": str(comfy_root),
        "site_packages": str(SITE_PACKAGES),
        "package_receipt": package_receipt,
        "asset_receipt": asset_receipt,
    }
    if RECEIPT_FILE.exists():
        log_action(f"removing install receipt {RECEIPT_FILE}")
        RECEIPT_FILE.unlink()
        log_action(f"removed install receipt {RECEIPT_FILE}")
    return receipt
