"""
Command Center branding — reuses each app's canonical icon/colors where possible.

Applied Intelligence: loads ``suite_branding`` from the sibling repo or the
synced copy produced by ``scripts/sync_suite_branding.py``.
"""

from __future__ import annotations

import importlib.util
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
    "music": {"accent": "#a855f7", "bg": "#faf5ff", "border": "#e9d5ff"},
    "investment": {"accent": "#0d9488", "bg": "#f0fdfa", "border": "#99f6e4"},
    "baseball": {"accent": "#16a34a", "bg": "#f0fdf4", "border": "#bbf7d0"},
    "nba": {"accent": "#ea580c", "bg": "#fff7ed", "border": "#fed7aa"},
    "future_lens": {"accent": "#7c3aed", "bg": "#f5f3ff", "border": "#ddd6fe"},
}

_ami_module: ModuleType | None = None
_ami_loaded_from: str | None = None


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
