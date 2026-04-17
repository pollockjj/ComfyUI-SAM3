from __future__ import annotations

import json
import platform
import re
import shutil
import subprocess
import sys
import urllib.request
import urllib.error
from importlib import metadata
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent
ASSETS_DIR = REPO_ROOT / "assets"
RECEIPT_FILE = REPO_ROOT / ".sam3_install_receipt.json"
SITE_PACKAGES = Path(sys.prefix) / f"lib/python{sys.version_info.major}.{sys.version_info.minor}/site-packages"
SPECIAL_WHEEL_INDEX_CANDIDATES = {
    "cc-torch": (
        "https://comfy-org.github.io/wheels/cc-torch/",
        "https://pozzettiandrea.github.io/cuda-wheels/cc-torch/",
    ),
    "torch-generic-nms": (
        "https://comfy-org.github.io/wheels/torch-generic-nms/",
        "https://pozzettiandrea.github.io/cuda-wheels/torch-generic-nms/",
    ),
    "flash-attn": (
        "https://comfy-org.github.io/wheels/flash-attn/",
        "https://pozzettiandrea.github.io/cuda-wheels/flash-attn/",
    ),
}

TORCH_TAG_PREFERENCES = {
    "cc-torch": ("2.11", "2.10", "2.9"),
    "torch-generic-nms": ("2.11", "2.10", "2.9"),
    "flash-attn": ("2.11", "2.10", "2.9"),
}
SPECIAL_WHEEL_PACKAGE_ORDER = ("cc-torch", "torch-generic-nms", "flash-attn")
MANAGED_PACKAGES = SPECIAL_WHEEL_PACKAGE_ORDER


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


def _expected_asset_paths(comfy_root: Path) -> tuple[Path, ...]:
    return tuple(
        (comfy_root / "input" / source.name)
        for source in sorted(ASSETS_DIR.iterdir())
        if source.is_file()
    )


def _receipt_asset_paths(receipt: dict[str, object] | None, comfy_root: Path) -> tuple[Path, ...]:
    if receipt and receipt.get("copied_assets"):
        return tuple(Path(path) for path in receipt["copied_assets"])
    return _expected_asset_paths(comfy_root)


def _receipt_managed_packages(receipt: dict[str, object] | None) -> tuple[str, ...]:
    if receipt and receipt.get("managed_packages"):
        receipt_packages = tuple(
            package_name for package_name in receipt["managed_packages"]
            if package_name in SPECIAL_WHEEL_PACKAGE_ORDER
        )
        if receipt_packages:
            return receipt_packages
    return MANAGED_PACKAGES


def _missing_managed_packages(package_names: tuple[str, ...]) -> list[str]:
    missing: list[str] = []
    for package_name in package_names:
        try:
            metadata.distribution(package_name)
        except metadata.PackageNotFoundError:
            missing.append(package_name)
    return missing


def install_needed(comfy_root: Path) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    receipt = read_receipt()
    if receipt is None:
        reasons.append(f"missing install receipt {RECEIPT_FILE}")
    package_names = _receipt_managed_packages(receipt)
    missing_packages = _missing_managed_packages(package_names)
    if missing_packages:
        reasons.append(f"missing managed packages: {', '.join(missing_packages)}")
    missing_assets = [path for path in _receipt_asset_paths(receipt, comfy_root) if not path.exists()]
    if missing_assets:
        reasons.append(
            "missing bundled assets: " + ", ".join(str(path) for path in missing_assets)
        )
    return (len(reasons) > 0, reasons)


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


def _read_index(package_name: str) -> tuple[str, str]:
    last_error: Exception | None = None
    for url in SPECIAL_WHEEL_INDEX_CANDIDATES[package_name]:
        try:
            log_action(f"checking wheel index {url}")
            with urllib.request.urlopen(url) as response:
                html = response.read().decode("utf-8")
            log_action(f"using wheel index {url}")
            return url, html
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
            log_action(f"wheel index unavailable {url}: {exc}")
            last_error = exc
    raise RuntimeError(
        f"No wheel index available for {package_name}. Last error: {last_error}"
    )


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
    for package_name in SPECIAL_WHEEL_INDEX_CANDIDATES:
        _, html = _read_index(package_name)
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


def ensure_installed() -> dict[str, object]:
    comfy_root = detect_comfy_root()
    needed, reasons = install_needed(comfy_root)
    if not needed:
        log_action("startup check: SAM3 install already complete")
        existing_receipt = read_receipt()
        assert existing_receipt is not None
        return existing_receipt
    for reason in reasons:
        log_action(f"startup check: {reason}")
    log_action("startup check: completing SAM3 setup automatically")
    return install_everything()


def uninstall_everything() -> dict[str, object]:
    comfy_root = detect_comfy_root()
    log_action(f"resolved COMFY_ROOT={comfy_root}")
    log_action(f"managed site-packages target={SITE_PACKAGES}")
    prior_receipt = read_receipt()
    package_names = _receipt_managed_packages(prior_receipt)
    asset_paths = tuple(prior_receipt.get("copied_assets", [])) if prior_receipt else tuple(
        str(path) for path in _expected_asset_paths(comfy_root)
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
