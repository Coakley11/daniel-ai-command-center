"""
Command Center branding — reuses each app's canonical icon/colors where possible.

Applied Intelligence: loads ``suite_branding`` from the sibling repo or the
synced copy produced by ``scripts/sync_suite_branding.py``.
"""

from __future__ import annotations

import importlib.util
import base64
import html
from functools import lru_cache
from pathlib import Path
from types import ModuleType
from typing import Any

_CC_ROOT = Path(__file__).resolve().parent
_SYNCED_AMI = _CC_ROOT / "branding" / "applied_intelligence_suite_branding.py"

_BASE_ICONS: dict[str, str] = {
    "music": "🎵",
    "investment": "📊",
    "baseball": "⚾",
    "nba": "🏀",
    "future_lens": "🔮",
}

_BASE_THEMES: dict[str, dict[str, str]] = {
    "robotics": {"accent": "#0066cc", "bg": "#f0f9ff", "border": "#bae6fd"},
    "music": {"accent": "#a855f7", "bg": "#faf5ff", "border": "#e9d5ff"},
    "investment": {"accent": "#0d9488", "bg": "#f0fdfa", "border": "#99f6e4"},
    "baseball": {"accent": "#16a34a", "bg": "#f0fdf4", "border": "#bbf7d0"},
    "nba": {"accent": "#ea580c", "bg": "#fff7ed", "border": "#fed7aa"},
    "future_lens": {"accent": "#7c3aed", "bg": "#f5f3ff", "border": "#ddd6fe"},
}

# Approved App Directory product logos. Other apps retain their existing icons.
_LOGO_DIR = _CC_ROOT / "branding" / "logos"
_APP_LOGO_FILES: dict[str, str] = {
    "robotics": "robotics_official.png",
    "music": "music_official_4050c33c0ac1.png",
    "command_center": "command_160.png",
    "investment": "investment_official_885952150f87.png",
    "baseball": "baseball_official_d9f0256884bd.png",
}


_ami_module: ModuleType | None = None
_ami_loaded_from: str | None = None


@lru_cache(maxsize=32)
def _logo_uri_for_revision(path: str, modified_ns: int, size: int) -> str:
    """File revision participates in the cache key; never cache a missing asset."""
    return "data:image/png;base64," + base64.b64encode(Path(path).read_bytes()).decode("ascii")


def app_logo_data_uri(app_key: str) -> str:
    """The locally shipped approved asset, refreshed when its bytes are replaced."""
    name = _APP_LOGO_FILES.get(app_key)
    if not name:
        return ""
    path = _LOGO_DIR / name
    try:
        revision = path.stat()
        return _logo_uri_for_revision(str(path), revision.st_mtime_ns, revision.st_size)
    except OSError:
        return ""


def uses_official_logo(app_key: str) -> bool:
    return app_key in _APP_LOGO_FILES


def app_brand_html(app_key: str, css_class: str, *, fallback_icon: str = "") -> str:
    """One brand renderer for cards and navigation; approved apps never revert to emoji."""
    uri = app_logo_data_uri(app_key)
    names = {"robotics": "Daniel AI Robotics", "music": "Music Practice Coach", "investment": "Investment Portfolio Analyzer",
             "baseball": "Baseball Explorer", "command_center": "Command Center"}
    label = names.get(app_key, app_key)
    if uri:
        return (f'<img class="{html.escape(css_class, quote=True)}" src="{uri}" '
                f'data-app-logo="{html.escape(app_key, quote=True)}" '
                f'alt="{html.escape(label, quote=True)} logo">')
    if uses_official_logo(app_key):
        return f'<span class="cc-logo-unavailable">{html.escape(label)} logo unavailable</span>'
    return html.escape(fallback_icon or app_icon(app_key))


def _load_module_from_path(path: Path, module_name: str) -> ModuleType | None:
    if not path.is_file():
        return None
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _applied_intelligence_branding_module() -> ModuleType | None:
    global _ami_module, _ami_loaded_from
    if _ami_module is not None:
        return _ami_module

    candidates: list[tuple[str, Path]] = [
        (
            "sibling",
            _CC_ROOT.parent
            / "Applied-mathematical-intelligence"
            / "suite_branding.py",
        ),
        ("synced", _SYNCED_AMI),
    ]
    for label, path in candidates:
        mod = _load_module_from_path(path, f"ami_suite_branding_{label}")
        if mod is not None and getattr(mod, "PAGE_ICON", ""):
            _ami_module = mod
            _ami_loaded_from = label
            return mod
    return None


def applied_intelligence_branding_source() -> str:
    """Where AMI branding was loaded from: sibling, synced, or fallback."""
    mod = _applied_intelligence_branding_module()
    if mod is not None:
        return _ami_loaded_from or "unknown"
    return "fallback"


def app_icon(app_key: str) -> str:
    if app_key == "applied_intelligence":
        mod = _applied_intelligence_branding_module()
        if mod is not None:
            return str(getattr(mod, "PAGE_ICON", "📐"))
        return "📐"
    return _BASE_ICONS.get(app_key, "▶")


def app_theme(app_key: str) -> dict[str, str]:
    base = dict(_BASE_THEMES.get(app_key, {"accent": "#6366f1", "bg": "#f8fafc", "border": "#e2e8f0"}))
    base["emoji"] = app_icon(app_key)
    if app_key == "applied_intelligence":
        mod = _applied_intelligence_branding_module()
        if mod is not None:
            base["accent"] = str(getattr(mod, "ACCENT_COLOR", base["accent"]))
            base["bg"] = str(getattr(mod, "CARD_BACKGROUND", base["bg"]))
            base["border"] = str(getattr(mod, "CARD_BORDER", base["border"]))
            base["emoji"] = str(getattr(mod, "PAGE_ICON", base["emoji"]))
        else:
            base["accent"] = "#0ea5e9"
            base["bg"] = "#f0f9ff"
            base["border"] = "#7dd3fc"
    return base


def build_app_themes() -> dict[str, dict[str, str]]:
    keys = set(_BASE_THEMES) | {"applied_intelligence"}
    return {key: app_theme(key) for key in keys}


def suite_app_icons() -> dict[str, str]:
    keys = set(_BASE_ICONS) | {"applied_intelligence"}
    return {key: app_icon(key) for key in keys}
