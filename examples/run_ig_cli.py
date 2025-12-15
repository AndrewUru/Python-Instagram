from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List

import pandas as pd

# Allow `python examples/run_ig_cli.py` from repo root.
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from ig_public.cache import read_cache, write_cache
from ig_public.client import InstagramPublicFetchError, build_instagram_headers, fetch_public_profile
from ig_public.normalize import normalize_posts, normalize_profile
from ig_public.utils import (
    get_env_float,
    get_env_int,
    now_utc_for_filename,
    now_utc_iso,
    parse_username,
)


def _compute_posts_kpis(posts: List[Dict[str, object]], followers: int) -> List[Dict[str, object]]:
    followers_safe = int(followers or 0)
    enriched: List[Dict[str, object]] = []
    for post in posts:
        likes = int(post.get("likes_count") or 0)
        comments = int(post.get("comments_count") or 0)
        interactions = likes + comments
        er_estimated = (interactions / followers_safe) if followers_safe > 0 else None
        enriched.append(
            {
                **post,
                "likes_count": likes,
                "comments_count": comments,
                "interactions": interactions,
                "er_estimated": er_estimated,
            }
        )
    return enriched


def _build_summary(profile: Dict[str, object], posts: List[Dict[str, object]]) -> Dict[str, object]:
    followers = int(profile.get("followers") or 0)
    media_count = int(profile.get("media_count") or 0)
    posts_analizados = int(len(posts))

    er_values = [p.get("er_estimated") for p in posts if isinstance(p.get("er_estimated"), (int, float))]
    er_promedio = float(sum(er_values) / len(er_values)) if er_values else None

    cols = ("shortcode", "permalink", "likes_count", "comments_count", "interactions", "er_estimated")
    top_3_posts = [
        {col: post.get(col) for col in cols}
        for post in sorted(posts, key=lambda p: int(p.get("interactions") or 0), reverse=True)[:3]
    ]

    return {
        "followers": followers,
        "media_count": media_count,
        "posts_analizados": posts_analizados,
        "ER_promedio": er_promedio,
        "top_3_posts": top_3_posts,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Instagram Public Analyzer (unofficial)")
    parser.add_argument("--username", required=True, help="Username o URL (ej: @notjustanalytics)")
    parser.add_argument(
        "--max-posts",
        type=int,
        default=get_env_int("IG_MAX_POSTS", 24),
        help="Cantidad máxima de posts a analizar",
    )
    parser.add_argument("--out", default="out", help="Carpeta de salida (default: out/)")
    args = parser.parse_args()

    username = parse_username(args.username)
    if not username:
        raise SystemExit("Username inválido. Usa '@usuario', 'usuario' o URL de perfil.")

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    ttl_hours = float(get_env_float("IG_CACHE_TTL_HOURS", 6.0))
    delay_sec = float(get_env_float("IG_REQUEST_DELAY_SEC", 2.5))

    cached = read_cache(username, ttl_hours=ttl_hours)
    if cached:
        raw = cached["data"]
        fetched_at = str(cached.get("cached_at_utc") or now_utc_iso())
        source = "cache"
    else:
        raw = fetch_public_profile(
            username,
            headers=build_instagram_headers(),
            request_delay_sec=delay_sec,
        )
        write_cache(username, raw, ttl_hours=ttl_hours)
        fetched_at = now_utc_iso()
        source = "live"

    profile = normalize_profile(raw, fetched_at_utc=fetched_at)
    posts = normalize_posts(raw, max_posts=int(args.max_posts))
    posts_kpis = _compute_posts_kpis(posts, int(profile.get("followers") or 0))
    summary = _build_summary(profile, posts_kpis)

    pd.DataFrame([profile]).to_csv(out_dir / "perfil.csv", index=False, encoding="utf-8")
    pd.DataFrame(posts_kpis).to_csv(out_dir / "posts.csv", index=False, encoding="utf-8")

    (out_dir / "perfil.json").write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "posts.json").write_text(json.dumps(posts_kpis, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    snapshot = {
        "generated_at_utc": now_utc_iso(),
        "source": source,
        "profile": profile,
        "posts": posts_kpis,
        "summary": summary,
    }
    snapshot_name = f"report_ig_{username}_{now_utc_for_filename()}.json"
    (out_dir / snapshot_name).write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"@{username}: {len(posts_kpis)} posts, followers={profile.get('followers')} (source={source})")
    print(f"Salida: {out_dir.resolve()}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except InstagramPublicFetchError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2)
