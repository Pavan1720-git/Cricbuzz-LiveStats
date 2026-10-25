"""
services/cricket_api.py — Authorized REST API client for live cricket data.

Reads configuration from environment variables.
Never exposes API keys in logs or UI.
Falls back gracefully when credentials are absent or the API is unavailable.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Optional

import requests

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import (
    CRICKET_API_KEY,
    CRICKET_API_HOST,
    CRICKET_API_BASE_URL,
    API_CACHE_SECONDS,
    API_TIMEOUT_SECONDS,
    DEMO_MODE,
)

logger = logging.getLogger(__name__)

# ── In-memory response cache ──────────────────────────────────────────────────
_cache: dict[str, tuple[dict, datetime]] = {}


def _cached_get(endpoint: str, params: dict = None) -> Optional[dict]:
    """GET request with simple TTL cache and error handling."""
    cache_key = f"{endpoint}?{params}"
    cached_val, cached_at = _cache.get(cache_key, (None, datetime.min))
    if cached_val is not None and datetime.now() - cached_at < timedelta(seconds=API_CACHE_SECONDS):
        return cached_val

    if not CRICKET_API_KEY:
        return None  # Demo mode — no API key

    headers = {
        "x-rapidapi-key":  CRICKET_API_KEY,
        "x-rapidapi-host": CRICKET_API_HOST,
    }
    url = f"{CRICKET_API_BASE_URL.rstrip('/')}/{endpoint.lstrip('/')}"
    try:
        response = requests.get(
            url, headers=headers, params=params, timeout=API_TIMEOUT_SECONDS
        )
        response.raise_for_status()
        data = response.json()
        _cache[cache_key] = (data, datetime.now())
        return data
    except requests.exceptions.Timeout:
        logger.warning("API timeout for %s", endpoint)
    except requests.exceptions.HTTPError as exc:
        if exc.response.status_code == 429:
            logger.warning("API rate limit hit — waiting 5 s")
            time.sleep(5)
        else:
            logger.warning("HTTP %s for %s", exc.response.status_code, endpoint)
    except requests.exceptions.RequestException as exc:
        logger.warning("API request failed: %s", exc)
    except ValueError:
        logger.warning("Invalid JSON from %s", endpoint)
    return None


# ── Public API surface ────────────────────────────────────────────────────────

def get_live_matches() -> Optional[dict]:
    """Fetch currently live matches."""
    return _cached_get("matches/v1/live")


def get_recent_matches() -> Optional[dict]:
    """Fetch recently completed matches."""
    return _cached_get("matches/v1/recent")


def get_upcoming_matches() -> Optional[dict]:
    """Fetch upcoming matches."""
    return _cached_get("matches/v1/upcoming")


def get_match_scorecard(match_id: str) -> Optional[dict]:
    """Fetch detailed scorecard for a match."""
    return _cached_get(f"mcenter/v1/{match_id}/scard")


def get_series_matches(series_id: str) -> Optional[dict]:
    return _cached_get(f"series/v1/{series_id}/matches")


def clear_cache():
    """Clear the in-memory response cache (e.g., on manual refresh)."""
    _cache.clear()
    logger.info("API cache cleared.")


def last_refresh_time() -> Optional[datetime]:
    """Return the most recent cache entry timestamp."""
    if not _cache:
        return None
    return max(ts for _, ts in _cache.values())
