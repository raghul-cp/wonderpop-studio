"""
Loads config/config.yaml and the .env file, and exposes one `get_config()`
function the rest of the project uses. Environment variables always win
over config.yaml, so GitHub Actions secrets can override local defaults
without editing any file.
"""

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT_DIR / "config" / "config.yaml"

load_dotenv(ROOT_DIR / ".env")  # no-op if the file doesn't exist (e.g. in CI, which uses real env vars)

_cached_config = None


def get_config() -> dict:
    """Return the merged config dict (config.yaml + environment overrides)."""
    global _cached_config
    if _cached_config is not None:
        return _cached_config

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    # Environment overrides for the handful of settings that commonly change
    # per-environment (local dev vs. GitHub Actions) without editing yaml.
    cfg["content_engine"] = os.getenv("CONTENT_ENGINE", cfg.get("content_engine", "template"))

    cfg["upload"]["enabled"] = _env_bool("ENABLE_UPLOAD", cfg["upload"]["enabled"])
    cfg["video_assembly"]["enabled"] = _env_bool("ENABLE_VIDEO_ASSEMBLY", cfg["video_assembly"]["enabled"])
    cfg["voiceover_audio"]["enabled"] = _env_bool("ENABLE_VOICEOVER_AUDIO", cfg["voiceover_audio"]["enabled"])
    cfg["image_generation"]["enabled"] = _env_bool("ENABLE_IMAGE_GENERATION", cfg["image_generation"]["enabled"])

    _cached_config = cfg
    return cfg


def _env_bool(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


def data_dir(*parts) -> Path:
    p = ROOT_DIR / "data"
    for part in parts:
        p = p / part
    p.mkdir(parents=True, exist_ok=True)
    return p
