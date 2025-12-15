from __future__ import annotations

import json
import os
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterator, Optional

from ig_public.utils import get_cache_ttl_hours, now_utc_iso, parse_utc_iso, parse_username


CACHE_DIR = Path(".ig_cache")
LOCKS_DIR = CACHE_DIR / "locks"
CACHE_SCHEMA_VERSION = 1


def _ensure_dirs() -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    LOCKS_DIR.mkdir(parents=True, exist_ok=True)


def _cache_path(username: str) -> Path:
    clean = parse_username(username) or (username or "").strip().lower()
    return CACHE_DIR / f"{clean}.json"


def read_cache(username: str, ttl_hours: float | None = None) -> Optional[Dict[str, object]]:
    """Return cache envelope if fresh; otherwise None.

    Envelope format:
    - cached_at_utc: str (UTC ISO)
    - ttl_hours: float
    - data: dict (raw API payload)
    """
    ttl = float(ttl_hours) if ttl_hours is not None else float(get_cache_ttl_hours())
    path = _cache_path(username)
    if not path.exists():
        return None
    try:
        envelope = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(envelope, dict):
        return None
    cached_at = envelope.get("cached_at_utc")
    data = envelope.get("data")
    if not isinstance(cached_at, str) or not isinstance(data, dict):
        return None

    try:
        cached_dt = parse_utc_iso(cached_at)
    except Exception:
        return None

    age_hours = (datetime.now(timezone.utc) - cached_dt).total_seconds() / 3600.0
    if ttl <= 0:
        return None
    if age_hours > ttl:
        return None

    envelope["age_hours"] = age_hours
    return envelope  # type: ignore[return-value]


def write_cache(username: str, data: Dict[str, object], ttl_hours: float | None = None) -> Path:
    _ensure_dirs()
    ttl = float(ttl_hours) if ttl_hours is not None else float(get_cache_ttl_hours())
    clean = parse_username(username) or (username or "").strip().lower()
    path = _cache_path(clean)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    payload: Dict[str, object] = {
        "schema_version": CACHE_SCHEMA_VERSION,
        "username": clean,
        "cached_at_utc": now_utc_iso(),
        "ttl_hours": ttl,
        "data": data,
    }
    tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp_path.replace(path)
    return path


@contextmanager
def username_lock(username: str, timeout_sec: float = 60.0) -> Iterator[None]:
    """A simple per-username file lock to avoid concurrent requests."""
    _ensure_dirs()
    clean = parse_username(username) or (username or "").strip().lower()
    lock_path = LOCKS_DIR / f"{clean}.lock"
    start = time.monotonic()

    while True:
        try:
            fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            break
        except FileExistsError:
            try:
                mtime = lock_path.stat().st_mtime
            except FileNotFoundError:
                continue
            if time.time() - mtime > max(10.0, timeout_sec * 2):
                try:
                    lock_path.unlink()
                except FileNotFoundError:
                    pass
                continue
            if time.monotonic() - start > timeout_sec:
                raise TimeoutError(f"Hay otra consulta en progreso para @{clean}.")
            time.sleep(0.2)

    try:
        yield
    finally:
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass

