"""
tdu_common.py - Shared utilities for Test Drive Unlimited (TDU) tools.
Provides path auto-detection, configuration handling, and console helpers.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

# Audio extensions supported by Test Drive Unlimited
AUDIO_EXTENSIONS: Set[str] = {".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma"}

# Configuration file name
CONFIG_FILE_NAME = "config.json"
EXAMPLE_CONFIG_FILE_NAME = "config.example.json"


# ==========================================
# Console Formatting
# ==========================================

class Colors:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


def _supports_color() -> bool:
    """Check whether the console supports ANSI escape colors."""
    if not hasattr(sys.stdout, "isatty") or not sys.stdout.isatty():
        return False
    # Windows 10+ supports ANSI if VT100 is enabled, or in modern terminals
    if sys.platform == "win32":
        return os.environ.get("WT_SESSION") is not None or "ANSICON" in os.environ or os.environ.get("TERM") == "xterm-256color" or True
    return True


_USE_COLOR = _supports_color()


def print_info(msg: str) -> None:
    prefix = f"{Colors.CYAN}ℹ{Colors.RESET} " if _USE_COLOR else "[INFO] "
    print(f"{prefix}{msg}")


def print_success(msg: str) -> None:
    prefix = f"{Colors.GREEN}✔{Colors.RESET} " if _USE_COLOR else "[OK] "
    print(f"{prefix}{msg}")


def print_warning(msg: str) -> None:
    prefix = f"{Colors.YELLOW}⚠{Colors.RESET} " if _USE_COLOR else "[WARN] "
    print(f"{prefix}{msg}")


def print_error(msg: str) -> None:
    prefix = f"{Colors.RED}✖{Colors.RESET} " if _USE_COLOR else "[ERROR] "
    print(f"{prefix}{msg}", file=sys.stderr)


# ==========================================
# Configuration Handling
# ==========================================

def get_script_dir() -> Path:
    """Return the directory containing this script."""
    return Path(__file__).resolve().parent


def get_config_path() -> Path:
    """Return the path to config.json."""
    return get_script_dir() / CONFIG_FILE_NAME


def load_config() -> Dict[str, Any]:
    """Load configuration from config.json if it exists."""
    cfg_path = get_config_path()
    if cfg_path.is_file():
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print_warning(f"Could not load '{CONFIG_FILE_NAME}': {e}")
    return {}


def save_config(config: Dict[str, Any]) -> None:
    """Save configuration to config.json."""
    cfg_path = get_config_path()
    try:
        with open(cfg_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        print_success(f"Configuration saved to {cfg_path.name}")
    except Exception as e:
        print_error(f"Failed to save {CONFIG_FILE_NAME}: {e}")


# ==========================================
# Path Discovery & Auto-Detection
# ==========================================

COMMON_TDU_PATHS: List[Path] = [
    Path(r"C:\Program Files (x86)\Atari\Test Drive Unlimited"),
    Path(r"D:\Program Files (x86)\Atari\Test Drive Unlimited"),
    Path(r"C:\Program Files\Atari\Test Drive Unlimited"),
    Path(r"D:\Program Files\Atari\Test Drive Unlimited"),
    Path(r"C:\Games\Test Drive Unlimited"),
    Path(r"D:\Games\Test Drive Unlimited"),
    Path(r"C:\Program Files (x86)\Steam\steamapps\common\Test Drive Unlimited"),
    Path(r"D:\SteamLibrary\steamapps\common\Test Drive Unlimited"),
]


def find_tdu_install_dir(preferred: Optional[str] = None) -> Optional[Path]:
    """
    Attempt to locate the Test Drive Unlimited game directory.
    Checks:
    1. Preferred argument (from CLI)
    2. config.json ('tdu_install_dir')
    3. Environment variable 'TDU_DIR' or 'TDU_INSTALL_DIR'
    4. Windows registry
    5. Common default installation paths
    """
    # 1. Preferred argument
    if preferred:
        p = Path(preferred).resolve()
        if p.is_dir():
            return p
        print_warning(f"Specified TDU directory does not exist: {preferred}")

    # 2. Config file
    config = load_config()
    cfg_dir = config.get("tdu_install_dir")
    if cfg_dir:
        p = Path(cfg_dir).resolve()
        if p.is_dir():
            return p

    # 3. Environment variables
    for env_var in ("TDU_DIR", "TDU_INSTALL_DIR"):
        env_val = os.environ.get(env_var)
        if env_val:
            p = Path(env_val).resolve()
            if p.is_dir():
                return p

    # 4. Windows Registry
    if sys.platform == "win32":
        try:
            import winreg
            reg_keys = [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Atari\Test Drive Unlimited"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Atari\Test Drive Unlimited"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Atari\Test Drive Unlimited"),
            ]
            for hkey, subkey in reg_keys:
                try:
                    with winreg.OpenKey(hkey, subkey) as key:
                        val, _ = winreg.QueryValueEx(key, "InstallPath")
                        if val and Path(val).is_dir():
                            return Path(val).resolve()
                except OSError:
                    continue
        except ImportError:
            pass

    # 5. Common installation paths
    for candidate in COMMON_TDU_PATHS:
        if candidate.is_dir():
            return candidate

    return None


def find_tdu_savegame_dir(preferred: Optional[str] = None) -> Optional[Path]:
    """
    Locate the TDU savegame directory (usually in Documents/Test Drive Unlimited/savegame).
    """
    if preferred:
        p = Path(preferred).resolve()
        if p.is_dir():
            return p
        print_warning(f"Specified savegame directory does not exist: {preferred}")

    config = load_config()
    cfg_dir = config.get("savegame_dir")
    if cfg_dir:
        p = Path(cfg_dir).resolve()
        if p.is_dir():
            return p

    # Documents directory
    docs_dir = Path.home() / "Documents" / "Test Drive Unlimited" / "savegame"
    if docs_dir.is_dir():
        return docs_dir

    # OneDrive Documents fallback
    onedrive_docs = Path.home() / "OneDrive" / "Dokumenty" / "Test Drive Unlimited" / "savegame"
    if onedrive_docs.is_dir():
        return onedrive_docs
    onedrive_docs_en = Path.home() / "OneDrive" / "Documents" / "Test Drive Unlimited" / "savegame"
    if onedrive_docs_en.is_dir():
        return onedrive_docs_en

    return None


def get_savegame_profiles(savegame_dir: Path) -> List[str]:
    """Return a list of profile folder names inside the savegame directory."""
    if not savegame_dir.is_dir():
        return []
    profiles = [
        item.name for item in savegame_dir.iterdir()
        if item.is_dir() and not item.name.startswith(".")
    ]
    return sorted(profiles)


def prompt_for_directory(prompt_text: str, default: Optional[str] = None) -> Optional[Path]:
    """Prompt the user interactively to enter a valid directory path."""
    if not sys.stdin.isatty():
        return None

    full_prompt = f"{prompt_text} "
    if default:
        full_prompt += f"[{default}]: "
    else:
        full_prompt += ": "

    try:
        user_input = input(full_prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return None

    chosen = user_input or default
    if not chosen:
        return None

    path = Path(chosen).resolve()
    if not path.is_dir():
        print_error(f"Directory not found: {path}")
        return None
    return path
