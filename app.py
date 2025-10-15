from __future__ import annotations

from io import BytesIO
from typing import Dict, Iterable, List, Sequence, Tuple

import pandas as pd
import streamlit as st

from parsers import parse_followers_from_instagram_json
from scraper import (
    ScrapeSettings,
    create_loader_anonymous,
    get_public_profile_data_anonymous,
    username_from_url,
    validate_email_mx,
)


APP_TITLE = "Instagram Public Email Collector"
APP_TAGLINE = "Extrae emails publicos visibles de perfiles de Instagram sin login."


st.set_page_config(
    page_title=APP_TITLE,
    page_icon="@",
    layout="wide",
    initial_sidebar_state="expanded",
)


def init_session_state() -> None:
    if "results" not in st.session_state:
        st.session_state["results"]: List[Dict[str, object]] = []
    if "profile_cache" not in st.session_state:
        st.session_state["profile_cache"]: Dict[Tuple[str, int, int], Dict[str, object]] = {}


@st.cache_resource(show_spinner=False)
def get_loader():
    return create_loader_anonymous()


def normalise_usernames(entries: Iterable[str]) -> List[str]:
    seen: Dict[str, None] = {}
    for entry in entries:
        username = username_from_url(entry)
        if username:
            username = username.lower()
            if username not in seen:
                seen[username] = None
    return list(seen.keys())


def get_base_profile(
    username: str,
    loader,
    settings: ScrapeSettings,
) -> Dict[str, object]:
    cache_key = (username, settings.max_links, int(settings.timeout))
    cache = st.session_state["profile_cache"]
    if cache_key not in cache:
        cache[cache_key] = get_public_profile_data_anonymous(loader, username, settings=settings)
    return cache[cache_key]


def build_success_record(
    base: Dict[str, object],
    source: str,
    validate_mx: bool,
) -> Dict[str, object]:
    emails_raw = list(base.get("emails", []))
    record: Dict[str, object] = {
        "username": base.get("username", ""),
        "full_name": base.get("full_name", ""),
        "is_private": base.get("is_private"),
        "external_url": base.get("external_url", ""),
        "bio": base.get("bio", ""),
        "emails_raw": emails_raw,
        "emails": list(emails_raw),
        "emails_count": len(emails_raw),
        "email_sources": list(base.get("email_sources", [])),
        "source": source,
        "validation_applied": bool(validate_mx),
        "error": "",
    }
    if validate_mx:
        valid_emails = [email for email in emails_raw if validate_email_mx(email)]
        record["emails"] = valid_emails
        record["emails_count"] = len(valid_emails)
    return record


def build_error_record(username: str, error: str, source: str) -> Dict[str, object]:
    return {
        "username": username,
        "full_name": "",
        "is_private": None,
        "external_url": "",
        "bio": "",
        "emails_raw": [],
        "emails": [],
        "emails_count": 0,
        "email_sources": [],
        "source": source,
        "validation_applied": False,
        "error": error,
    }


def process_username(
    username_input: str,
    loader,
    settings: ScrapeSettings,
    validate_mx: bool,
    source: str,
) -> Dict[str, object]:
    username = username_from_url(username_input)
    if not username:
        raise ValueError("Ingresa un username o URL valido.")
    base = get_base_profile(username, loader, settings)
    return build_success_record(base, source, validate_mx)


def process_batch(
    usernames: Sequence[str],
    loader,
    settings: ScrapeSettings,
    validate_mx: bool,
    source: str,
    progress_label: str,
) -> Tuple[List[Dict[str, object]], List[Dict[str, object]]]:
    total = len(usernames)
    results: List[Dict[str, object]] = []
    errors: List[Dict[str, object]] = []
    progress = st.progress(0.0, text=progress_label)
    for index, username in enumerate(usernames, start=1):
        try:
            record = process_username(username, loader, settings, validate_mx, source)
            results.append(record)
            st.toast(f"Perfil @{record['username']} listo.")
        except Exception as exc:  # pylint: disable=broad-except
            clean_name = username_from_url(username) or username
            error_record = build_error_record(clean_name, str(exc), source)
            errors.append(error_record)
            st.toast(f"Error con @{clean_name}: {exc}")
        progress.progress(index / total, text=f"{progress_label} {index}/{total}")
    progress.empty()
    return results, errors


def append_results(records: Sequence[Dict[str, object]]) -> None:
    st.session_state["results"].extend(records)


def results_dataframe(records: Sequence[Dict[str, object]]) -> pd.DataFrame:
    if not records:
        return pd.DataFrame()
    df = pd.DataFrame(records)
    list_columns = ("emails", "emails_raw", "email_sources")
    for column in list_columns:
        if column in df.columns:
            df[column] = df[column].apply(
                lambda value: ", ".join(value) if isinstance(value, list) else value
            )
    return df


def download_buttons(df: pd.DataFrame) -> None:
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Descargar CSV",
        data=csv_bytes,
        file_name="emails_instagram.csv",
        mime="text/csv",
        use_container_width=True,
    )
    excel_buffer = BytesIO()
    df.to_excel(excel_buffer, index=False)
    st.download_button(
        "Descargar Excel",
        data=excel_buffer.getvalue(),
        file_name="emails_instagram.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )


def show_batch_summary(success_count: int, error_records: Sequence[Dict[str, object]]) -> None:
    if success_count:
        st.success(f"{success_count} perfiles procesados correctamente.")
    if error_records:
        st.warning(f"{len(error_records)} perfiles con error. Revisa los detalles en la pestaña Resultados.")


def main() -> None:
    init_session_state()
    loader = get_loader()

    st.title(APP_TITLE)
    st.caption(APP_TAGLINE)

    st.sidebar.header("Configuracion")
    delay_min = st.sidebar.number_input("Delay minimo (s)", min_value=0.0, max_value=10.0, value=1.0, step=0.1)
    delay_max = st.sidebar.number_input("Delay maximo (s)", min_value=0.0, max_value=20.0, value=2.5, step=0.1)
    if delay_max < delay_min:
        delay_min, delay_max = delay_max, delay_min
    max_links = st.sidebar.slider("Enlaces externos a seguir", min_value=0, max_value=10, value=5, step=1)
    max_retries = st.sidebar.slider("Reintentos HTTP", min_value=1, max_value=5, value=3, step=1)
    timeout = st.sidebar.number_input("Timeout peticiones (s)", min_value=5.0, max_value=60.0, value=12.0, step=1.0)
    validate_mx = st.sidebar.checkbox("Validar emails con MX (puede tardar mas)", value=False)

    st.sidebar.info(
        "Usa delays aleatorios para evitar bloqueos. Solo se analizan datos publicos "
        "y no se requiere login."
    )

    settings = ScrapeSettings(
        timeout=float(timeout),
        delay_range=(float(delay_min), float(delay_max)),
        max_links=int(max_links),
        max_retries=int(max_retries),
    )

    tab_profiles, tab_followers, tab_results = st.tabs(
        ["Perfiles", "Importar seguidores", "Resultados"]
    )

    with tab_profiles:
        st.subheader("Analisis rapido de un perfil")
        with st.form("single_profile_form"):
            single_input = st.text_input(
                "URL o @username",
                placeholder="https://www.instagram.com/usuario",
            )
            submit_single = st.form_submit_button("Analizar perfil")
        if submit_single:
            try:
                record = process_username(single_input, loader, settings, validate_mx, "perfil")
                append_results([record])
                st.toast(f"Perfil @{record['username']} analizado.")
                st.success(f"Se encontraron {record['emails_count']} emails visibles.")
            except Exception as exc:  # pylint: disable=broad-except
                st.error(f"No se pudo analizar el perfil: {exc}")

        st.divider()
        st.subheader("Procesamiento masivo de perfiles")
        with st.form("bulk_form"):
            bulk_text = st.text_area(
                "Perfiles (uno por linea)",
                placeholder="@usuario1\nhttps://instagram.com/usuario2",
                height=160,
            )
            bulk_limit = st.number_input(
                "Limite de perfiles",
                min_value=1,
                max_value=1000,
                value=100,
                step=1,
            )
            submit_bulk = st.form_submit_button("Procesar lista")

        if submit_bulk:
            usernames = normalise_usernames(bulk_text.splitlines())
            if not usernames:
                st.warning("Agrega al menos un perfil.")
            else:
                usernames = usernames[: int(bulk_limit)]
                st.info(f"Procesando {len(usernames)} perfiles...")
                results, errors = process_batch(
                    usernames,
                    loader,
                    settings,
                    validate_mx,
                    "lista",
                    "Procesando perfiles",
                )
                append_results([*results, *errors])
                show_batch_summary(len(results), errors)

    with tab_followers:
        st.subheader("Importar archivo oficial de seguidores")
        st.write(
            "Carga el ZIP o JSON descargado desde Instagram (Configuracion > Descarga tu informacion)."
        )
        uploaded = st.file_uploader(
            "Archivo de seguidores",
            type=["zip", "json"],
            accept_multiple_files=False,
        )
        followers_limit = st.number_input(
            "Limite de seguidores a procesar",
            min_value=1,
            max_value=5000,
            value=500,
            step=1,
        )
        if uploaded and st.button("Procesar seguidores"):
            usernames = parse_followers_from_instagram_json(uploaded.getvalue(), uploaded.name)
            if not usernames:
                st.error("No se encontraron seguidores validos en el archivo.")
            else:
                usernames = usernames[: int(followers_limit)]
                st.info(f"Analizando {len(usernames)} seguidores...")
                results, errors = process_batch(
                    usernames,
                    loader,
                    settings,
                    validate_mx,
                    "seguidores",
                    "Analizando seguidores",
                )
                append_results([*results, *errors])
                show_batch_summary(len(results), errors)

    with tab_results:
        st.subheader("Resultados acumulados")
        df = results_dataframe(st.session_state["results"])
        if df.empty:
            st.info("Todavia no hay resultados. Analiza un perfil o importa seguidores.")
        else:
            metrics_cols = st.columns(3)
            with metrics_cols[0]:
                st.metric("Perfiles analizados", len(df))
            with metrics_cols[1]:
                st.metric("Emails encontrados", int(df["emails_count"].astype(int).sum()))
            with metrics_cols[2]:
                error_count = int((df["error"].astype(str) != "").sum())
                st.metric("Perfiles con error", error_count)

            st.dataframe(df, use_container_width=True, height=400)
            download_buttons(df)

            if st.button("Limpiar resultados"):
                st.session_state["results"].clear()
                st.session_state["profile_cache"].clear()
                st.toast("Resultados reiniciados.")
                st.rerun()


if __name__ == "__main__":
    main()
