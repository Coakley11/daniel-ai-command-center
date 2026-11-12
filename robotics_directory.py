"""Robotics-only card artwork and configuration notice; no cloud side effects."""
import base64
from pathlib import Path
from urllib.parse import urlsplit
import html


def logo_html():
    logo = Path(__file__).parent / "branding" / "logos" / "robotics_official.png"
    encoded = base64.b64encode(logo.read_bytes()).decode("ascii")
    return f'<img src="data:image/png;base64,{encoded}" alt="Daniel AI Robotics" style="width:100%;height:100%;object-fit:contain;border-radius:18px;">'


def description_html(app):
    return (f'<div class="cc-app-highlight">{html.escape(app.category)}</div>'
            f'<p class="cc-activity-detail">{html.escape(app.description)}</p>')


def launch_notice(url):
    if not url:
        return "Robotics Lab has no configured deployment URL. Open is unavailable until an administrator connects it."
    if urlsplit(url).hostname in ("127.0.0.1", "localhost", "::1"):
        return "Local development: start Robotics Lab on this computer before selecting Open."
    return ""
