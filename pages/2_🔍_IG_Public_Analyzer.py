from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st

try:
    import altair as alt  # type: ignore
except Exception:  # pragma: no cover - altair is a declared dependency, keep runtime resilient.
    alt = None  # type: ignore

from ig_public.cache import read_cache, write_cache
from ig_public.client import InstagramPublicFetchError, build_instagram_headers, fetch_public_profile
from ig_public.normalize import normalize_posts, normalize_profile
from ig_public.utils import (
    get_env_float,
    get_env_int,
    get_env_str,
    now_utc_for_filename,
    now_utc_iso,
    parse_username,
)


APP_TITLE = "IG Public Analyzer"
DEFAULT_TIMEZONE = "Europe/Madrid"


st.set_page_config(page_title=APP_TITLE, page_icon="🔍", layout="wide")


@dataclass(frozen=True)
class AnalyzerSettings:
    max_posts: int
    cache_ttl_hours: float
    request_delay_sec: float
    timezone_name: str


def _safe_zoneinfo(name: str):
    try:
        from zoneinfo import ZoneInfo  # Python 3.9+

        return ZoneInfo(name)
    except Exception:
        return None


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


def _posts_dataframe(posts: List[Dict[str, object]], timezone_name: str) -> pd.DataFrame:
    df = pd.DataFrame(posts)
    if df.empty:
        return df

    df["likes_count"] = pd.to_numeric(df.get("likes_count"), errors="coerce").fillna(0).astype(int)
    df["comments_count"] = pd.to_numeric(df.get("comments_count"), errors="coerce").fillna(0).astype(int)
    df["interactions"] = pd.to_numeric(df.get("interactions"), errors="coerce").fillna(
        df["likes_count"] + df["comments_count"]
    )
    df["er_estimated"] = pd.to_numeric(df.get("er_estimated"), errors="coerce")

    df["taken_at_utc"] = pd.to_datetime(df.get("taken_at_utc"), errors="coerce", utc=True)

    tz = _safe_zoneinfo(timezone_name)
    if tz:
        local = df["taken_at_utc"].dt.tz_convert(tz)
    else:
        local = df["taken_at_utc"].dt.tz_convert("UTC")
    df["taken_local"] = local
    df["dow"] = df["taken_local"].dt.dayofweek
    df["hour"] = df["taken_local"].dt.hour
    return df


def _build_summary(profile: Dict[str, object], posts: List[Dict[str, object]]) -> Dict[str, object]:
    followers = int(profile.get("followers") or 0)
    media_count = int(profile.get("media_count") or 0)
    posts_analizados = int(len(posts))

    er_promedio = None
    er_values = [p.get("er_estimated") for p in posts if isinstance(p.get("er_estimated"), (int, float))]
    if er_values:
        er_promedio = float(sum(er_values) / len(er_values))

    top_3: List[Dict[str, object]] = []
    if posts_analizados:
        cols = ("shortcode", "permalink", "likes_count", "comments_count", "interactions", "er_estimated")
        ordered = sorted(posts, key=lambda p: int(p.get("interactions") or 0), reverse=True)[:3]
        for post in ordered:
            top_3.append({col: post.get(col) for col in cols})

    return {
        "followers": followers,
        "media_count": media_count,
        "posts_analizados": posts_analizados,
        "er_promedio": er_promedio,
        "top_3_posts": top_3,
    }


def _bar_chart(posts_df: pd.DataFrame):
    if alt is None or posts_df.empty:
        return None
    chart_df = posts_df.dropna(subset=["shortcode"]).copy()
    if chart_df.empty:
        return None
    return (
        alt.Chart(chart_df)
        .mark_bar()
        .encode(
            x=alt.X("shortcode:N", sort=None, title="Post"),
            y=alt.Y("interactions:Q", title="Interacciones (likes + comentarios)"),
            tooltip=[
                alt.Tooltip("shortcode:N", title="Shortcode"),
                alt.Tooltip("likes_count:Q", title="Likes"),
                alt.Tooltip("comments_count:Q", title="Comentarios"),
                alt.Tooltip("interactions:Q", title="Interacciones"),
                alt.Tooltip("er_estimated:Q", title="ER estimado", format=".2%"),
            ],
        )
    )


def _heatmap_chart(posts_df: pd.DataFrame):
    if alt is None or posts_df.empty:
        return None
    if "dow" not in posts_df.columns or "hour" not in posts_df.columns:
        return None
    heat = (
        posts_df.dropna(subset=["dow", "hour"])
        .groupby(["dow", "hour"], as_index=False)
        .size()
        .rename(columns={"size": "posts"})
    )
    if heat.empty:
        return None
    days = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
    heat["day"] = heat["dow"].astype(int).map(lambda idx: days[idx] if 0 <= idx < 7 else "")
    heat["hour"] = heat["hour"].astype(int)

    return (
        alt.Chart(heat)
        .mark_rect()
        .encode(
            x=alt.X("hour:O", title="Hora"),
            y=alt.Y("day:N", sort=days, title="Día de semana"),
            color=alt.Color("posts:Q", title="Posts"),
            tooltip=[
                alt.Tooltip("day:N", title="Día"),
                alt.Tooltip("hour:O", title="Hora"),
                alt.Tooltip("posts:Q", title="Posts"),
            ],
        )
    )


def _export_payloads(
    username: str,
    profile: Dict[str, object],
    posts: List[Dict[str, object]],
    summary: Dict[str, object],
) -> Tuple[bytes, bytes, bytes, bytes, bytes]:
    profile_df = pd.DataFrame([profile])
    perfil_csv = profile_df.to_csv(index=False).encode("utf-8")
    posts_df = pd.DataFrame(posts)
    posts_csv = posts_df.to_csv(index=False).encode("utf-8") if not posts_df.empty else b""

    perfil_json = json.dumps(profile, ensure_ascii=False, indent=2).encode("utf-8")
    posts_json = json.dumps(posts, ensure_ascii=False, indent=2).encode("utf-8")
    summary_json = json.dumps(summary, ensure_ascii=False, indent=2).encode("utf-8")

    return perfil_csv, posts_csv, perfil_json, posts_json, summary_json


def _analyze_username(
    username_or_url: str,
    settings: AnalyzerSettings,
) -> Tuple[Dict[str, object], List[Dict[str, object]], str, Optional[float]]:
    username = parse_username(username_or_url)
    if not username:
        raise ValueError("Ingresa un @username o URL de perfil válida.")

    cached = read_cache(username, ttl_hours=settings.cache_ttl_hours)
    if cached:
        raw = cached["data"]
        fetched_at = str(cached.get("cached_at_utc") or now_utc_iso())
        age_hours = float(cached.get("age_hours") or 0.0)
        source = "cache"
    else:
        raw = fetch_public_profile(
            username,
            headers=build_instagram_headers(),
            request_delay_sec=settings.request_delay_sec,
        )
        write_cache(username, raw, ttl_hours=settings.cache_ttl_hours)
        fetched_at = now_utc_iso()
        age_hours = None
        source = "live"

    profile = normalize_profile(raw, fetched_at_utc=fetched_at)
    posts = normalize_posts(raw, max_posts=settings.max_posts)

    return profile, posts, source, age_hours


def main() -> None:
    st.title("🔍 Análisis público de Instagram")
    st.caption("Sin Graph API (endpoint no oficial). Funciona local y en Streamlit Cloud.")
    st.warning(
        "Solo datos públicos; puede romperse si Instagram cambia la web. "
        "No incluye métricas privadas (reach/impresiones/saves).",
        icon="⚠️",
    )

    with st.sidebar:
        st.header("Configuración")
        max_posts = st.number_input(
            "Posts a analizar",
            min_value=1,
            max_value=60,
            value=get_env_int("IG_MAX_POSTS", 24),
            step=1,
        )
        cache_ttl = st.number_input(
            "TTL caché (horas)",
            min_value=0.0,
            max_value=168.0,
            value=float(get_env_float("IG_CACHE_TTL_HOURS", 6.0)),
            step=0.5,
        )
        delay = st.number_input(
            "Delay entre requests (seg)",
            min_value=0.0,
            max_value=30.0,
            value=float(get_env_float("IG_REQUEST_DELAY_SEC", 2.5)),
            step=0.5,
        )
        timezone_name = st.text_input(
            "Zona horaria para heatmap",
            value=get_env_str("IG_TIMEZONE", DEFAULT_TIMEZONE),
        )

        settings = AnalyzerSettings(
            max_posts=int(max_posts),
            cache_ttl_hours=float(cache_ttl),
            request_delay_sec=float(delay),
            timezone_name=timezone_name.strip() or DEFAULT_TIMEZONE,
        )

    username_or_url = st.text_input(
        "Username o URL",
        placeholder="@notjustanalytics o https://instagram.com/notjustanalytics",
    )

    cols = st.columns([1, 1, 2])
    with cols[0]:
        analyze_clicked = st.button("Analizar", type="primary", use_container_width=True)
    with cols[1]:
        clear_clicked = st.button("Limpiar resultado", use_container_width=True)

    if clear_clicked:
        for key in ("ig_profile", "ig_posts", "ig_source", "ig_age_hours", "ig_settings"):
            st.session_state.pop(key, None)
        st.rerun()

    if analyze_clicked:
        with st.status("Consultando…", expanded=False) as status:
            try:
                profile, posts, source, age_hours = _analyze_username(username_or_url, settings)
                st.session_state["ig_profile"] = profile
                st.session_state["ig_posts"] = posts
                st.session_state["ig_source"] = source
                st.session_state["ig_age_hours"] = age_hours
                st.session_state["ig_settings"] = asdict(settings)

                if source == "cache":
                    suffix = f" (caché, hace {age_hours:.1f}h)" if age_hours is not None else " (caché)"
                    status.update(label=f"Desde caché{suffix}", state="complete")
                else:
                    status.update(label="Listo", state="complete")
            except InstagramPublicFetchError as exc:
                status.update(label="Error", state="error")
                st.error(str(exc))
            except TimeoutError as exc:
                status.update(label="Error", state="error")
                st.error(str(exc))
            except Exception as exc:  # pylint: disable=broad-except
                status.update(label="Error", state="error")
                st.error(f"No se pudo analizar: {exc}")

    profile = st.session_state.get("ig_profile")
    posts = st.session_state.get("ig_posts")
    if not isinstance(profile, dict) or not isinstance(posts, list):
        st.info("Ingresa un @username o URL y pulsa Analizar.")
        return

    followers = int(profile.get("followers") or 0)
    posts_kpis = _compute_posts_kpis(posts, followers)
    posts_df = _posts_dataframe(posts_kpis, settings.timezone_name)

    st.divider()
    st.subheader("Perfil")
    photo_col, info_col = st.columns([1, 3])
    with photo_col:
        pic = str(profile.get("profile_pic_url_hd") or "")
        if pic:
            st.image(pic, width=160)
    with info_col:
        username = str(profile.get("username") or "")
        full_name = str(profile.get("full_name") or "")
        flags = []
        if profile.get("is_verified") is True:
            flags.append("verificado")
        if profile.get("is_private") is True:
            flags.append("privado")
        flags_text = f" ({', '.join(flags)})" if flags else ""
        st.markdown(f"### {full_name or '@' + username} `@{username}`{flags_text}")
        external_url = str(profile.get("external_url") or "")
        if external_url:
            st.write(f"External URL: {external_url}")
        bio = str(profile.get("biography") or "")
        if bio:
            st.write(bio)

    kpi_cols = st.columns(4)
    with kpi_cols[0]:
        st.metric("Followers", f"{followers:,}".replace(",", "."))
    with kpi_cols[1]:
        st.metric("Following", f"{int(profile.get('following') or 0):,}".replace(",", "."))
    with kpi_cols[2]:
        st.metric("Media count", f"{int(profile.get('media_count') or 0):,}".replace(",", "."))
    with kpi_cols[3]:
        st.metric("Posts analizados", len(posts_kpis))

    if profile.get("is_private") is True:
        st.warning("El perfil es privado. Es posible que no haya posts accesibles.", icon="🔒")

    st.divider()
    st.subheader("Posts recientes")
    if posts_df.empty:
        st.info("No se encontraron posts recientes (o no son accesibles).")
    else:
        display_cols = [
            "taken_at_utc",
            "shortcode",
            "likes_count",
            "comments_count",
            "interactions",
            "er_estimated",
            "caption",
            "permalink",
        ]
        existing = [col for col in display_cols if col in posts_df.columns]
        st.dataframe(posts_df[existing], use_container_width=True, height=420)

        chart_cols = st.columns(2)
        with chart_cols[0]:
            st.caption("Interacciones por post")
            chart = _bar_chart(posts_df)
            if chart is not None:
                st.altair_chart(chart, use_container_width=True)
            else:
                st.info("Altair no está disponible o faltan datos para el gráfico.")
        with chart_cols[1]:
            st.caption("Heatmap de publicaciones (día x hora, zona local)")
            heatmap = _heatmap_chart(posts_df)
            if heatmap is not None:
                st.altair_chart(heatmap, use_container_width=True)
            else:
                st.info("No hay suficientes datos con fecha para construir el heatmap.")

    summary = _build_summary(profile, posts_kpis)
    perfil_csv, posts_csv, perfil_json, posts_json, summary_json = _export_payloads(
        str(profile.get("username") or "perfil"),
        profile,
        posts_kpis,
        summary,
    )

    st.divider()
    st.subheader("Exportar")
    export_cols = st.columns(3)
    username = str(profile.get("username") or "perfil")
    with export_cols[0]:
        st.download_button(
            "Perfil CSV",
            data=perfil_csv,
            file_name="perfil.csv",
            mime="text/csv",
            use_container_width=True,
        )
        st.download_button(
            "Perfil JSON",
            data=perfil_json,
            file_name="perfil.json",
            mime="application/json",
            use_container_width=True,
        )
    with export_cols[1]:
        st.download_button(
            "Posts CSV",
            data=posts_csv,
            file_name="posts.csv",
            mime="text/csv",
            use_container_width=True,
            disabled=not bool(posts_csv),
        )
        st.download_button(
            "Posts JSON",
            data=posts_json,
            file_name="posts.json",
            mime="application/json",
            use_container_width=True,
        )
    with export_cols[2]:
        st.download_button(
            "summary.json",
            data=summary_json,
            file_name="summary.json",
            mime="application/json",
            use_container_width=True,
        )

        snapshot = {
            "generated_at_utc": now_utc_iso(),
            "profile": profile,
            "posts": posts_kpis,
            "summary": summary,
            "settings": st.session_state.get("ig_settings") or asdict(settings),
        }
        snapshot_name = f"report_ig_{username}_{now_utc_for_filename()}.json"
        st.download_button(
            "Guardar snapshot",
            data=json.dumps(snapshot, ensure_ascii=False, indent=2).encode("utf-8"),
            file_name=snapshot_name,
            mime="application/json",
            use_container_width=True,
        )


if __name__ == "__main__":
    main()
