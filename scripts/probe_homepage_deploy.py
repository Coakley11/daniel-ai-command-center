"""Probe deployed homepage for build version and link patterns."""
from __future__ import annotations

import re
import sys

import requests

URL = "https://daniel-ai-command-center-dexxnd7bf8jalxzqbyq55i.streamlit.app"


def main() -> int:
    r = requests.get(URL, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
    print(f"Status: {r.status_code}")
    text = r.text
    builds = re.findall(r"build\s+[\w-]+", text, re.I)
    print("Build markers:", builds[:5] or "none in HTML shell")
    old = re.findall(r"share\.streamlit\.io[^\s\"'<>]+", text)
    print("share.streamlit.io refs:", len(old))
    apps = re.findall(r"https://[a-z0-9-]+\.streamlit\.app", text)
    print("streamlit.app refs in HTML:", len(set(apps)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
