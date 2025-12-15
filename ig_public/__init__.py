from __future__ import annotations

"""Public Instagram profile analyzer (unofficial).

Fetches public profile data from:
`https://i.instagram.com/api/v1/users/web_profile_info/?username=<username>`

Includes:
- Local JSON cache under `.ig_cache/`
- Basic rate limiting and per-username locking
- Normalization helpers for profile + recent posts
"""

from ig_public.client import (
    InstagramPublicFetchError,
    build_instagram_headers,
    fetch_public_profile,
)
from ig_public.normalize import normalize_posts, normalize_profile
from ig_public.utils import parse_username

__all__ = [
    "InstagramPublicFetchError",
    "build_instagram_headers",
    "fetch_public_profile",
    "normalize_profile",
    "normalize_posts",
    "parse_username",
]

