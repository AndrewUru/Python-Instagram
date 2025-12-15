from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ig_public.utils import now_utc_iso, optional_int


def _dig(obj: object, *path: object) -> object:
    current: object = obj
    for key in path:
        if isinstance(key, int):
            if not isinstance(current, list) or key >= len(current) or key < 0:
                return None
            current = current[key]
            continue
        if not isinstance(current, dict):
            return None
        current = current.get(key)  # type: ignore[arg-type]
    return current


def _as_str(value: object, default: str = "") -> str:
    if isinstance(value, str):
        return value
    return default


def _as_bool(value: object) -> Optional[bool]:
    if isinstance(value, bool):
        return value
    return None


def _ts_to_utc_iso(value: object) -> str:
    ts = optional_int(value)
    if ts is None:
        return ""
    try:
        return (
            datetime.fromtimestamp(ts, tz=timezone.utc)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z")
        )
    except (OverflowError, OSError, ValueError):
        return ""


def _extract_user(raw: Dict[str, object]) -> Dict[str, object]:
    user = _dig(raw, "data", "user")
    if isinstance(user, dict):
        return user  # type: ignore[return-value]
    user = raw.get("user")
    if isinstance(user, dict):
        return user  # type: ignore[return-value]
    return {}


def normalize_profile(raw: Dict[str, object], fetched_at_utc: str | None = None) -> Dict[str, object]:
    """Normalize profile fields from the raw API payload."""
    user = _extract_user(raw)

    followers = optional_int(_dig(user, "edge_followed_by", "count"))
    following = optional_int(_dig(user, "edge_follow", "count"))
    media_count = optional_int(_dig(user, "edge_owner_to_timeline_media", "count"))

    username = _as_str(user.get("username")).lower()
    return {
        "username": username,
        "full_name": _as_str(user.get("full_name")),
        "biography": _as_str(user.get("biography")),
        "external_url": _as_str(user.get("external_url")),
        "is_private": _as_bool(user.get("is_private")),
        "is_verified": _as_bool(user.get("is_verified")),
        "profile_pic_url_hd": _as_str(user.get("profile_pic_url_hd")) or _as_str(user.get("profile_pic_url")),
        "followers": int(followers or 0),
        "following": int(following or 0),
        "media_count": int(media_count or 0),
        "fetched_at_utc": fetched_at_utc or now_utc_iso(),
    }


def normalize_posts(raw: Dict[str, object], max_posts: int = 24) -> List[Dict[str, object]]:
    """Normalize recent posts from the raw API payload."""
    user = _extract_user(raw)
    edges = _dig(user, "edge_owner_to_timeline_media", "edges")
    if not isinstance(edges, list):
        return []

    posts: List[Dict[str, object]] = []
    for edge in edges[: max(0, int(max_posts))]:
        if not isinstance(edge, dict):
            continue
        node = edge.get("node")
        if not isinstance(node, dict):
            continue

        shortcode = _as_str(node.get("shortcode"))
        if not shortcode:
            continue

        caption = _dig(node, "edge_media_to_caption", "edges", 0, "node", "text")
        caption_text = _as_str(caption) or _as_str(node.get("caption"))

        likes = optional_int(_dig(node, "edge_liked_by", "count"))
        if likes is None:
            likes = optional_int(_dig(node, "edge_media_preview_like", "count"))
        comments = optional_int(_dig(node, "edge_media_to_comment", "count"))
        if comments is None:
            comments = optional_int(_dig(node, "edge_media_to_parent_comment", "count"))

        posts.append(
            {
                "shortcode": shortcode,
                "permalink": f"https://www.instagram.com/p/{shortcode}/",
                "is_video": bool(node.get("is_video") is True),
                "display_url": _as_str(node.get("display_url")) or _as_str(node.get("thumbnail_src")),
                "accessibility_caption": _as_str(node.get("accessibility_caption")),
                "taken_at_utc": _ts_to_utc_iso(node.get("taken_at_timestamp") or node.get("taken_at")),
                "comments_count": int(comments or 0),
                "likes_count": int(likes or 0),
                "caption": caption_text,
            }
        )

    return posts

