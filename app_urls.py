"""
App URL constants for the Daniel AI Command Center.

Edit these links when deployments change. Imported by ai_command_center.py and app_registry.py.
"""

# ── Deployed Streamlit URLs (DEV unless noted) ───────────────────────────────

MUSIC_APP_URL = (
    "https://share.streamlit.io/Coakley11/ai-music-practice-coach/dev/streamlit_music_practice_app.py"
)
INVESTMENT_APP_URL = (
    "https://share.streamlit.io/Coakley11/investment-portfolio-analyzer/dev/streamlit_app.py"
)
BASEBALL_APP_URL = (
    "https://share.streamlit.io/Coakley11/baseball-stat-app/main/streamlit_app.py"
)
NBA_APP_URL = (
    "https://share.streamlit.io/Coakley11/nba-playoff-companion-ai/dev/streamlit_app.py"
)
MATH_APP_URL = (
    "https://share.streamlit.io/Coakley11/Applied-mathematical-intelligence/dev/streamlit_app.py"
)
FUTURE_LENS_URL = (
    "https://share.streamlit.io/Coakley11/future-lens-ai-transition-simulator/main/streamlit_app.py"
)

# ── GitHub fallbacks (used if Streamlit URL is unreachable) ───────────────────

MUSIC_GITHUB_URL = "https://github.com/Coakley11/ai-music-practice-coach/tree/dev"
INVESTMENT_GITHUB_URL = "https://github.com/Coakley11/investment-portfolio-analyzer/tree/dev"
BASEBALL_GITHUB_URL = "https://github.com/Coakley11/baseball-stat-app/tree/main"
NBA_GITHUB_URL = "https://github.com/Coakley11/nba-playoff-companion-ai/tree/dev"
MATH_GITHUB_URL = "https://github.com/Coakley11/Applied-mathematical-intelligence/tree/dev"
FUTURE_LENS_GITHUB_URL = "https://github.com/Coakley11/future-lens-ai-transition-simulator/tree/main"

# Branch label shown in Connected Apps Status
APP_BRANCH: dict[str, str] = {
    "music": "DEV",
    "investment": "DEV",
    "baseball": "MAIN",
    "nba": "DEV",
    "math": "DEV",
    "future_lens": "MAIN",
}
