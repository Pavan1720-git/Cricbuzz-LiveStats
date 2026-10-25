"""
config.py — Central configuration for Cricbuzz LiveStats.

Reads all settings from environment variables (via .env file).
Never hardcode secrets here.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the project root (one level up if running from a sub-package)
_BASE_DIR = Path(__file__).resolve().parent
load_dotenv(_BASE_DIR / ".env", override=False)

# ── Database ─────────────────────────────────────────────────────────────────
# Default to SQLite so the app runs without a MySQL installation.
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///cricbuzz.db")

# ── Cricket API ───────────────────────────────────────────────────────────────
CRICKET_API_KEY: str = os.getenv("CRICKET_API_KEY", "")
CRICKET_API_HOST: str = os.getenv("CRICKET_API_HOST", "cricbuzz-cricket.p.rapidapi.com")
CRICKET_API_BASE_URL: str = os.getenv(
    "CRICKET_API_BASE_URL", "https://cricbuzz-cricket.p.rapidapi.com"
)

# ── Application Behaviour ─────────────────────────────────────────────────────
APP_ENV: str = os.getenv("APP_ENV", "development")

# DEMO_MODE defaults to True when no API key is configured.
_demo_env = os.getenv("DEMO_MODE", "").lower()
if _demo_env in ("false", "0", "no"):
    DEMO_MODE: bool = False
elif _demo_env in ("true", "1", "yes"):
    DEMO_MODE: bool = True
else:
    # Auto-detect: enable demo mode when no API key is present.
    DEMO_MODE = not bool(CRICKET_API_KEY)

API_CACHE_SECONDS: int = int(os.getenv("API_CACHE_SECONDS", "60"))
API_TIMEOUT_SECONDS: int = int(os.getenv("API_TIMEOUT_SECONDS", "10"))

# ── Paths ─────────────────────────────────────────────────────────────────────
DATA_DIR: Path = _BASE_DIR / "data"
