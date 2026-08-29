"""
Version-check helper for the Flask app.

Compares the running app version (baked into a VERSION file at build time)
against the latest GitHub release, with the GitHub lookup cached for a
configurable TTL so we don't hit the API on every page load.
"""

import threading
import time
from pathlib import Path

import requests

GITHUB_REPO = "leginreklaw/supreme-pancake"
CACHE_TTL_SECONDS = 60 * 60  # 1 hour — plenty fresh, keeps us well under the
                              # 60 requests/hour unauthenticated GitHub API limit

_cache_lock = threading.Lock()
_cache = {"latest_version": None, "fetched_at": 0.0}


def get_running_version() -> str:
    """Read the version baked into the image/deploy at build time."""
    try:
        return Path(__file__).parent.joinpath("VERSION").read_text().strip()
    except FileNotFoundError:
        return "dev"


def _fetch_latest_version() -> str | None:
    """Hit the GitHub API directly. Returns None on any failure."""
    try:
        r = requests.get(
            f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest",
            timeout=3,
        )
        r.raise_for_status()
        tag = r.json().get("tag_name", "")
        return tag.lstrip("v") or None
    except requests.RequestException:
        return None


def get_latest_version() -> str | None:
    """
    Return the latest release version, using a cached value if it's still
    fresh. Only one thread does the actual network fetch when the cache
    expires; others reuse whatever is cached (even if stale) rather than
    piling on redundant requests.
    """
    now = time.monotonic()

    with _cache_lock:
        is_stale = (now - _cache["fetched_at"]) > CACHE_TTL_SECONDS
        if not is_stale:
            return _cache["latest_version"]

    # Fetch outside the lock so a slow network call doesn't block other
    # requests reading the (still-valid-enough) cached value.
    fetched = _fetch_latest_version()

    with _cache_lock:
        # If the fetch failed, keep whatever we had before rather than
        # blanking it out — better to show a slightly stale "latest" than
        # none at all.
        if fetched is not None:
            _cache["latest_version"] = fetched
        _cache["fetched_at"] = now

    return _cache["latest_version"]


def get_version_info() -> dict:
    """Convenience wrapper for use directly in a Flask route."""
    running = get_running_version().lstrip("v")
    latest = get_latest_version()
    return {
        "running_version": running,
        "latest_version": latest,
        "update_available": latest is not None and latest != running,
    }
