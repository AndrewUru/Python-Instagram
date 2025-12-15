from __future__ import annotations

import os
import re
import time
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlparse


DEFAULT_IG_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124 Safari/537.36"
)
USERNAME_REGEX = re.compile(r"^[a-z0-9._]{1,30}$")

_DOTENV_LOADED = False


def load_dotenv_once() -> None:
    """Load `.env` once if python-dotenv is installed (optional at runtime)."""
    global _DOTENV_LOADED  # noqa: PLW0603 - module-level cache flag.
    if _DOTENV_LOADED:
        return
    _DOTENV_LOADED = True
    try:
        from dotenv import load_dotenv  # type: ignore
    except Exception:
        return
    load_dotenv(override=False)


def get_env_str(name: str, default: str) -> str:
    load_dotenv_once()
    value = os.getenv(name)
    return value.strip() if value else default


def get_env_int(name: str, default: int) -> int:
    load_dotenv_once()
    value = os.getenv(name)
    if not value:
        return default
    try:
        return int(value.strip())
    except ValueError:
        return default


def get_env_float(name: str, default: float) -> float:
    load_dotenv_once()
    value = os.getenv(name)
    if not value:
        return default
    try:
        return float(value.strip().replace(",", "."))
    except ValueError:
        return default


def now_utc_iso() -> str:
    """Return current time as UTC ISO string, e.g. '2025-01-01T12:00:00Z'."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def now_utc_for_filename() -> str:
    """Return a filesystem-safe UTC timestamp, e.g. '20250101_120000Z'."""
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")


def parse_utc_iso(value: str) -> datetime:
    """Parse a UTC ISO string supporting a trailing 'Z'."""
    if not value:
        raise ValueError("Empty datetime value.")
    text = value.strip()
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def parse_username(username_or_url: str) -> str:
    """Parse '@handle', 'handle' or an Instagram profile URL into a username.

    Accepts:
    - @usuario
    - usuario
    - https://instagram.com/usuario/
    - https://www.instagram.com/usuario
    Returns:
    - usuario (lowercase, no spaces) or "" if invalid.
    """
    value = (username_or_url or "").strip()
    if not value:
        return ""

    candidate = re.sub(r"\s+", "", value.strip())
    if candidate.startswith(("http://", "https://")):
        parsed = urlparse(candidate)
        host = (parsed.netloc or "").lower()
        if not host.endswith("instagram.com"):
            return ""
        path = (parsed.path or "").strip("/")
        if not path:
            return ""
        parts = [part for part in path.split("/") if part]
        if not parts:
            return ""
        first = parts[0].lower()
        if first == "stories":
            candidate = parts[1] if len(parts) >= 2 else ""
        else:
            reserved = {"p", "reel", "tv", "explore", "accounts", "about", "developer", "press"}
            if first in reserved:
                return ""
            candidate = parts[0]

    candidate = candidate.lstrip("@").lower()
    if USERNAME_REGEX.match(candidate):
        return candidate
    return ""


def sleep_with_spinner(seconds: float) -> None:
    """Sleep for `seconds` showing a Streamlit spinner when available."""
    seconds = float(seconds or 0.0)
    if seconds <= 0:
        return
    try:
        import streamlit as st  # type: ignore
    except Exception:
        time.sleep(seconds)
        return

    with st.spinner(f"Esperando {seconds:.1f}s…"):
        time.sleep(seconds)


def get_ig_user_agent() -> str:
    return get_env_str("IG_USER_AGENT", DEFAULT_IG_USER_AGENT)


def get_cache_ttl_hours(default: float = 6.0) -> float:
    return get_env_float("IG_CACHE_TTL_HOURS", default)


def get_request_delay_sec(default: float = 2.5) -> float:
    return get_env_float("IG_REQUEST_DELAY_SEC", default)


def optional_float(value: object) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def optional_int(value: object) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
