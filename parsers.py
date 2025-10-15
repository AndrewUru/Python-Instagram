from __future__ import annotations

import io
import json
import zipfile
import re
from typing import Iterable, List, Set
from urllib.parse import urlparse

USERNAME_REGEX = re.compile(r"^[a-z0-9._]{1,30}$")


def parse_followers_from_instagram_json(
    file_bytes: bytes,
    filename: str | None = None,
) -> List[str]:
    """Parse usernames from Instagram followers export (.json or .zip)."""
    if not file_bytes:
        return []

    if _looks_like_zip(file_bytes, filename):
        usernames = _parse_zip_payload(file_bytes)
    else:
        usernames = _parse_json_bytes(file_bytes)

    return sorted(usernames)


def _looks_like_zip(data: bytes, filename: str | None) -> bool:
    if filename and filename.lower().endswith(".zip"):
        return True
    return data.startswith(b"PK\x03\x04")


def _parse_zip_payload(data: bytes) -> Set[str]:
    usernames: Set[str] = set()
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        for name in zf.namelist():
            if not name.lower().endswith(".json"):
                continue
            try:
                content = zf.read(name)
            except KeyError:
                continue
            usernames.update(_parse_json_bytes(content))
    return usernames


def _parse_json_bytes(data: bytes) -> Set[str]:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        text = data.decode("utf-8", errors="ignore")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return set()
    return _extract_usernames(payload)


def _extract_usernames(payload: object) -> Set[str]:
    usernames: Set[str] = set()
    stack: List[object] = [payload]

    while stack:
        current = stack.pop()
        if isinstance(current, dict):
            # Direct string fields that typically contain usernames.
            for key in ("value", "username", "name", "handle"):
                value = current.get(key)
                if isinstance(value, str):
                    candidate = _normalise_username(value)
                    if candidate:
                        usernames.add(candidate)
            # Instagram exports often use string_list_data arrays.
            string_list = current.get("string_list_data")
            if isinstance(string_list, list):
                stack.extend(string_list)

            for value in current.values():
                if isinstance(value, (dict, list)):
                    stack.append(value)
                elif isinstance(value, str):
                    candidate = _normalise_username(value)
                    if candidate:
                        usernames.add(candidate)
        elif isinstance(current, list):
            stack.extend(current)
        elif isinstance(current, str):
            candidate = _normalise_username(current)
            if candidate:
                usernames.add(candidate)

    return usernames


def _normalise_username(value: str | None) -> str | None:
    if not value:
        return None
    candidate = value.strip()
    if not candidate:
        return None
    if candidate.startswith(("http://", "https://")):
        parsed = urlparse(candidate)
        path = parsed.path.rstrip("/")
        if not path:
            return None
        candidate = path.split("/")[-1]
    candidate = candidate.lstrip("@").lower()
    if USERNAME_REGEX.match(candidate):
        return candidate
    return None
