# app.py
from __future__ import annotations
import time
import re
from io import BytesIO
from typing import Any, Dict, List
import pandas as pd
import streamlit as st

# --- IMPORTS PROYECTO ---
from scraper import (
    create_loader_anonymous,
    get_public_profile_data_anonymous,
    username_from_url,
)
from parsers import parse_followers_from_instagram_json

# =========================
# CONFIG GLOBAL + THEME
# =========================
st.set_page_config(
    page_title="Instagram Public Email Collector — sin login",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================
# STYLES MEJORADOS (moderno, elegante)
# =========================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

:root { 
    --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    --instagram-gradient: linear-gradient(45deg, #833ab4, #fd1d1d, #fcb045);
    --card-bg: #ffffff; 
    --card-hover: #f8fafc;
    --text-primary: #f7f7f7;
    --text-secondary: #64748b;
    --border-light: #e2e8f0;
    --shadow-sm: 0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1);
    --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
    --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
    --radius-lg: 16px;
    --radius-md: 12px;
    --spacing-xs: 0.5rem;
    --spacing-sm: 0.75rem;
    --spacing-md: 1rem;
    --spacing-lg: 1.5rem;
    --spacing-xl: 2rem;
}

[data-theme="dark"] :root { 
    --card-bg: #1e293b; 
    --card-hover: #334155;
    --text-primary: #f1f5f9;
    --text-secondary: #94a3b8;
    --border-light: #334155;
}

* {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

.main > div { 
    padding-top: 0rem; 
    max-width: 1400px;
    margin: 0 auto;
}

/* Header mejorado */
.header-container {
    background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%);
    border-bottom: 1px solid var(--border-light);
    margin: -1rem -1rem 2rem -1rem;
    padding: var(--spacing-xl) var(--spacing-md);
    position: relative;
    overflow: hidden;
}

.header-container::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23667eea' fill-opacity='0.03'%3E%3Ccircle cx='30' cy='30' r='4'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
    opacity: 0.5;
}

.main-title {
    position: relative;
    font-weight: 800; 
    font-size: clamp(2rem, 4vw, 3.5rem);
    letter-spacing: -0.03em;
    background: var(--instagram-gradient);
    -webkit-background-clip: text; 
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: var(--spacing-xs);
    text-align: center;
    margin-top: var(--navbar-height, 80px); /* Ajusta según el alto de la navbar */
}


.subtitle { 
    color: var(--text-secondary); 
    font-size: 1.1rem;
    font-weight: 500;
    text-align: center;
    margin-bottom: var(--spacing-lg);
}

.feature-badges {
    display: flex;
    justify-content: center;
    gap: var(--spacing-sm);
    flex-wrap: wrap;
    margin-top: var(--spacing-md);
}

.badge {
    background: rgba(102, 126, 234, 0.1);
    color: #667eea;
    padding: 0.4rem 0.8rem;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: 500;
    border: 1px solid rgba(102, 126, 234, 0.2);
}

/* Cards mejoradas */
.metrics-grid { 
    display: grid; 
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
    gap: var(--spacing-md); 
    margin: var(--spacing-lg) 0;
}

.metric-card {
    background: var(--card-bg); 
    border: 1px solid var(--border-light);
    border-radius: var(--radius-md); 
    padding: var(--spacing-lg);
    box-shadow: var(--shadow-sm);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
}

.metric-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: var(--primary-gradient);
    transform: scaleX(0);
    transition: transform 0.3s ease;
}

.metric-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-lg);
    background: var(--card-hover);
}

.metric-card:hover::before {
    transform: scaleX(1);
}

.metric-label { 
    color: var(--text-secondary); 
    font-size: 0.85rem; 
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.metric-value { 
    font-weight: 800; 
    font-size: 1.8rem; 
    margin-top: var(--spacing-xs);
    color: var(--text-primary);
}

/* Secciones mejoradas */
.section-header {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    margin: var(--spacing-xl) 0 var(--spacing-md) 0;
    padding-bottom: var(--spacing-sm);
    border-bottom: 2px solid var(--border-light);
}

.section-title { 
    font-weight: 700; 
    font-size: 1.4rem;
    color: var(--text-primary);
    margin: 0;
}

.section-icon {
    font-size: 1.5rem;
}

/* Inputs y controles mejorados */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stNumberInput > div > div > input {
    border-radius: var(--radius-md) !important;
    border: 2px solid var(--border-light) !important;
    transition: all 0.3s ease !important;
    font-size: 0.95rem !important;
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus,
.stNumberInput > div > div > input:focus {
    border-color: #667eea !important;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
}

/* Botones mejorados */
.stButton > button {
    background: var(--primary-gradient) !important;
    border: none !important;
    border-radius: var(--radius-md) !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    padding: 0.7rem 1.5rem !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: var(--shadow-sm) !important;
}

.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: var(--shadow-md) !important;
}

.stButton > button:disabled {
    background: var(--text-secondary) !important;
    opacity: 0.6 !important;
}

/* Sidebar mejorado */
.css-1d391kg {
    background: linear-gradient(135deg, rgba(102, 126, 234, 0.02) 0%, rgba(118, 75, 162, 0.02) 100%) !important;
}

/* Info boxes */
.info-box {
    border-left: 4px solid #667eea; 
    background: rgba(102, 126, 234, 0.08); 
    padding: var(--spacing-md); 
    border-radius: var(--radius-md);
    margin: var(--spacing-md) 0;
}

.warning-box {
    border-left: 4px solid #f59e0b; 
    background: rgba(245, 158, 11, 0.08); 
    padding: var(--spacing-md); 
    border-radius: var(--radius-md);
    margin: var(--spacing-md) 0;
}

.success-box {
    border-left: 4px solid #10b981; 
    background: rgba(16, 185, 129, 0.08); 
    padding: var(--spacing-md); 
    border-radius: var(--radius-md);
    margin: var(--spacing-md) 0;
}

/* Progress bars */
.stProgress > div > div {
    background: var(--primary-gradient) !important;
    border-radius: 10px !important;
}

/* Tabs mejoradas */
.stTabs [data-baseweb="tab-list"] {
    gap: 1rem;
}

.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    border-radius: var(--radius-md) !important;
    font-weight: 600 !important;
    padding: 0.7rem 1.2rem !important;
    transition: all 0.3s ease !important;
}

.stTabs [aria-selected="true"] {
    background: var(--primary-gradient) !important;
    color: white !important;
}

/* Responsivo mejorado */
@media (max-width: 768px) {
    .metrics-grid {
        grid-template-columns: repeat(2, 1fr);
        gap: var(--spacing-sm);
    }
    
    .main-title {
        font-size: 2rem;
    }
    
    .feature-badges {
        justify-content: center;
    }
    
    .section-header {
        flex-direction: column;
        align-items: flex-start;
        gap: var(--spacing-xs);
    }
}

/* Animaciones */
@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.fade-in {
    animation: fadeInUp 0.6s ease-out;
}

/* Mejoras en data editor */
.stDataFrame {
    border-radius: var(--radius-md) !important;
    overflow: hidden !important;
    box-shadow: var(--shadow-sm) !important;
}

hr { 
    opacity: 0.15;
    margin: var(--spacing-xl) 0;
}
</style>
""", unsafe_allow_html=True)

# =========================
# HELPERS
# =========================
EMAIL_REGEX = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

@st.cache_data(show_spinner=False)
def cached_profile(L: Any, target: str) -> Dict[str, Any]:
    """Cachea el fetch de un perfil público."""
    return get_public_profile_data_anonymous(L, target)

def safe_username_from_input(text: str) -> str:
    text = text.strip()
    if text.startswith("http"):
        try:
            return username_from_url(text)
        except Exception:
            return text.split("/")[-1].strip("@")
    return text.lstrip("@")

def as_df(rows: List[Dict[str, Any]]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame(columns=[
            "username","full_name","emails_count","emails",
            "bio","external_url","is_private","email_sources","error"
        ])
    df = pd.DataFrame(rows)
    # normaliza list->string
    if "emails" in df.columns:
        df["emails"] = df["emails"].apply(lambda x: ", ".join(x) if isinstance(x, list) else (x or ""))
    return df

def create_metric_card(label: str, value: str|int, icon: str = "📊"):
    return f"""
    <div class="metric-card fade-in">
        <div class="metric-label">{icon} {label}</div>
        <div class="metric-value">{value}</div>
    </div>
    """

def download_buttons(df: pd.DataFrame, base: str):
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "📄 Descargar CSV",
            df.to_csv(index=False).encode("utf-8"),
            file_name=f"{base}.csv",
            mime="text/csv",
            use_container_width=True,
            key=f"dl_csv_{base}",
            help="Descarga los resultados en formato CSV"
        )
    with col2:
        bio_buf = BytesIO()
        df.to_excel(bio_buf, index=False)
        st.download_button(
            "📊 Descargar Excel",
            bio_buf.getvalue(),
            file_name=f"{base}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            key=f"dl_xlsx_{base}",
            help="Descarga los resultados en formato Excel"
        )

def backoff_sleep(t: float):
    time.sleep(min(5.0, max(0.0, t)))

def show_info_box(content: str, box_type: str = "info"):
    box_class = f"{box_type}-box"
    st.markdown(f'<div class="{box_class}">{content}</div>', unsafe_allow_html=True)

# =========================
# HEADER MEJORADO
# =========================
st.markdown("""
<div class="header-container">
    <div class="main-title">📧 Instagram Email Collector</div>
    <div class="subtitle">Extrae emails públicos de manera ética y responsable</div>
    <div class="feature-badges">
        <span class="badge">🔒 Sin Login</span>
        <span class="badge">🛡️ Solo Datos Públicos</span>
        <span class="badge">⚡ Rápido y Eficiente</span>
        <span class="badge">📊 Exporta CSV/Excel</span>
    </div>
</div>
""", unsafe_allow_html=True)

# =========================
# SIDEBAR MEJORADO
# =========================
with st.sidebar:
    st.markdown('<div class="section-header"><span class="section-icon">🛡️</span><div class="section-title">Información</div></div>', unsafe_allow_html=True)
    
    show_info_box("""
    <strong>✅ Qué hace:</strong><br>
    • Extrae emails públicos de biografías<br>
    • Analiza enlaces externos en perfiles<br>
    • Procesa datos de manera masiva<br><br>
    <strong>❌ Qué NO hace:</strong><br>
    • No requiere credenciales<br>
    • No accede a datos privados<br>
    • No viola términos de Instagram
    """)
    
    with st.expander("⚙️ Configuración Avanzada", expanded=False):
        st.markdown("""
        **Delays recomendados:**
        - Perfil único: 1-2s
        - Lotes pequeños (<50): 1s
        - Lotes grandes (>100): 2-3s
        
        **Límites sugeridos:**
        - Pruebas: 10-20 perfiles
        - Uso normal: 50-200 perfiles
        - Uso intensivo: 200-500 perfiles
        """)
    
    with st.expander("📋 Buenas Prácticas", expanded=False):
        st.markdown("""
        - ✅ Respeta términos de servicio
        - ✅ Cumple con RGPD/CCPA
        - ✅ Usa para contacto legítimo
        - ✅ Solicita consentimiento
        - ❌ Evita spam masivo
        - ❌ No hagas scraping agresivo
        """)
    
    st.divider()
    st.markdown("""
    <div style="text-align: center; padding: 1rem; background: rgba(102, 126, 234, 0.05); border-radius: 12px;">
        <strong>🚀 Hecho con ❤️</strong><br>
        <small>Para growth hackers éticos</small>
    </div>
    """, unsafe_allow_html=True)

# Loader anónimo
L = create_loader_anonymous()

# =========================
# TABS MEJORADAS
# =========================
tab1, tab2, tab3 = st.tabs(["🎯 Perfil Único", "📊 Procesamiento Masivo", "👥 Análisis de Seguidores"])

# ========== TAB 1: PERFIL ÚNICO ==========
with tab1:
    st.markdown('<div class="section-header"><span class="section-icon">🔍</span><div class="section-title">Analizar Perfil Individual</div></div>', unsafe_allow_html=True)
    
    show_info_box("Perfecto para análisis rápidos o verificación de un perfil específico. Introduce la URL completa o solo el @username.")
    
    col1, col2, col3 = st.columns([4, 1, 1])
    with col1:
        url_or_user = st.text_input(
            "🔗 URL del perfil o @username",
            placeholder="https://www.instagram.com/instagram/ o @instagram",
            help="Puedes pegar la URL completa del perfil o simplemente escribir el @username",
            key="single_input_user"
        )
    with col2:
        delay_single = st.number_input(
            "⏱️ Delay (s)", 
            min_value=0.0, 
            max_value=5.0, 
            value=1.0, 
            step=0.5, 
            help="Pausa entre requests para evitar bloqueos",
            key="delay_single"
        )
    with col3:
        attempts = st.number_input(
            "🔄 Reintentos", 
            min_value=1, 
            max_value=5, 
            value=2, 
            step=1, 
            help="Número de intentos con backoff exponencial",
            key="attempts_single"
        )

    go = st.button("🚀 Extraer Perfil", type="primary", use_container_width=True, key="btn_single_go")

    if go:
        target = safe_username_from_input(url_or_user)
        if not target:
            st.error("⚠️ Por favor, introduce una URL válida o @username.")
            st.stop()

        with st.status(f"🔄 Procesando perfil @{target}...", expanded=True) as status:
            for i in range(int(attempts)):
                try:
                    if delay_single: 
                        backoff_sleep(delay_single * (1.6**i if i else 1))
                    st.write(f"📡 Intento {i+1}/{attempts}...")
                    data = cached_profile(L, target)
                    break
                except Exception as e:
                    last_err = str(e)
                    st.warning(f"❌ Fallo en intento {i+1}: {last_err}")
            else:
                status.update(label="❌ No fue posible procesar el perfil", state="error")
                st.error("Se agotaron todos los intentos. El perfil podría estar privado o temporalmente inaccesible.")
                st.stop()

            df = as_df([data])
            emails_count = int(data.get("emails_count", 0) or 0)
            status.update(label="✅ Perfil procesado exitosamente", state="complete")
            st.success("🎉 ¡Perfil analizado correctamente!")

        # Métricas con diseño mejorado
        st.markdown('<div class="section-header"><span class="section-icon">📈</span><div class="section-title">Métricas del Perfil</div></div>', unsafe_allow_html=True)
        
        metrics_html = f"""
        <div class="metrics-grid">
            {create_metric_card("Emails Encontrados", emails_count, "📧")}
            {create_metric_card("Tipo de Cuenta", "🔒 Privada" if data.get("is_private") else "🌐 Pública", "👤")}
            {create_metric_card("Nombre Completo", data.get("full_name") or "—", "📝")}
            {create_metric_card("Username", f"@{data.get('username') or target}", "🏷️")}
        </div>
        """
        st.markdown(metrics_html, unsafe_allow_html=True)

        # Resultados con mejor presentación
        st.markdown('<div class="section-header"><span class="section-icon">📋</span><div class="section-title">Resultados Detallados</div></div>', unsafe_allow_html=True)
        
        if emails_count > 0:
            show_info_box(f"🎯 Se encontraron <strong>{emails_count} emails</strong> en el perfil. Los datos están listos para descargar.", "success")
        else:
            show_info_box("ℹ️ No se encontraron emails públicos en este perfil. Esto es normal para muchas cuentas.", "info")
        
        st.data_editor(
            df,
            use_container_width=True,
            hide_index=True,
            key="editor_single",
            column_config={
                "username": st.column_config.TextColumn("👤 Username", width="medium"),
                "full_name": st.column_config.TextColumn("📝 Nombre Completo", width="medium"),
                "emails": st.column_config.TextColumn("📧 Emails Públicos", help="Separados por comas"),
                "emails_count": st.column_config.NumberColumn("🔢 N.º Emails", width="small"),
                "bio": st.column_config.TextColumn("📄 Biografía", width="large"),
                "external_url": st.column_config.LinkColumn("🔗 URL Externa", width="medium"),
                "is_private": st.column_config.CheckboxColumn("🔒 Privado", width="small"),
            }
        )

        download_buttons(df, base=f"{data.get('username') or target}_perfil")

# ========== TAB 2: LOTES ==========
with tab2:
    st.markdown('<div class="section-header"><span class="section-icon">📊</span><div class="section-title">Procesamiento Masivo</div></div>', unsafe_allow_html=True)
    
    show_info_box("Procesa múltiples perfiles de una vez. Perfecto para análisis de competidores, investigación de mercado o campañas de outreach.")
    
    method = st.radio(
        "📥 Método de entrada", 
        ["✏️ Escribir manualmente", "📁 Subir archivo CSV"], 
        horizontal=True, 
        key="batch_input_method",
        help="Elige cómo quieres proporcionar la lista de usernames"
    )

    usernames: List[str] = []
    if method == "✏️ Escribir manualmente":
        col1, col2 = st.columns([3, 1])
        with col1:
            sample = "@instagram\n@natgeo\n@github\n@spotify\n@nike\n@cocacola"
            raw = st.text_area(
                "📝 Lista de usernames (uno por línea)", 
                height=200, 
                placeholder=sample, 
                key="batch_textarea",
                help="Escribe un @username por línea. El @ es opcional."
            )
        with col2:
            st.markdown("""
            **💡 Consejos:**
            - El símbolo @ es opcional
            - Se eliminarán duplicados automáticamente
            - Los espacios extra se ignoran
            - Puedes mezclar URLs y usernames
            
            **📝 Ejemplos válidos:**
            ```
            @instagram
            instagram
            https://instagram.com/nike
            @spotify
            ```
            """)
        if raw.strip():
            usernames = [safe_username_from_input(x) for x in raw.splitlines() if x.strip()]
    else:
        st.markdown("**📁 Formato del archivo CSV:**")
        show_info_box("El archivo debe tener una columna llamada <strong>'username'</strong> con los usernames a procesar (con o sin @).")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            uploaded_file = st.file_uploader(
                "📤 Subir archivo CSV", 
                type=["csv"], 
                key="batch_csv",
                help="El CSV debe contener una columna 'username'"
            )
        with col2:
            if uploaded_file is None:
                st.markdown("""
                **📋 Ejemplo de CSV:**
                ```
                username
                @instagram
                @natgeo
                spotify
                nike
                ```
                """)
        
        if uploaded_file is not None:
            try:
                df_input = pd.read_csv(uploaded_file)
                if "username" not in df_input.columns:
                    st.error("❌ El archivo CSV debe incluir una columna llamada 'username'.")
                    show_info_box("Asegúrate de que tu CSV tenga exactamente una columna llamada <strong>'username'</strong> con los perfiles a analizar.", "warning")
                else:
                    usernames = [safe_username_from_input(str(x)) for x in df_input["username"]]
                    st.success(f"✅ Archivo cargado correctamente: {len(usernames)} perfiles encontrados.")
            except Exception as e:
                st.error(f"❌ Error al leer el archivo CSV: {e}")

    # Limpiar y deduplicar usernames
    usernames = sorted(set([u for u in usernames if u]))

    # Configuración del procesamiento
    st.markdown('<div class="section-header"><span class="section-icon">⚙️</span><div class="section-title">Configuración del Procesamiento</div></div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        delay_batch = st.number_input(
            "⏱️ Delay por perfil (s)", 
            min_value=0.0, 
            max_value=5.0, 
            value=1.0, 
            step=0.5,
            key="delay_batch_tab2",
            help="Pausa entre cada perfil procesado"
        )
    with col2:
        attempts_batch = st.number_input(
            "🔄 Reintentos", 
            min_value=1, 
            max_value=5, 
            value=2, 
            step=1,
            key="attempts_batch_tab2",
            help="Intentos por perfil con backoff"
        )
    with col3:
        batch_limit = st.number_input(
            "🎯 Límite a procesar", 
            min_value=1, 
            max_value=1000,
            value=min(100, len(usernames)) if usernames else 50, 
            step=10,
            key="batch_limit_tab2",
            help="Máximo número de perfiles a procesar"
        )
    with col4:
        st.metric("📋 Usernames únicos", len(usernames))

    if usernames:
        estimated_time = min(len(usernames), batch_limit) * delay_batch
        cost_estimate = min(len(usernames), batch_limit) * 0.001  # Estimación de "costo" en requests
        
        info_cols = st.columns(3)
        with info_cols[0]:
            st.metric("⏱️ Tiempo estimado", f"{estimated_time:.1f}s")
        with info_cols[1]:
            st.metric("📊 Perfiles a procesar", min(len(usernames), batch_limit))
        with info_cols[2]:
            st.metric("🎯 Tasa éxito estimada", "85-95%")

    run_batch = st.button(
        "🚀 Iniciar Procesamiento Masivo", 
        type="primary", 
        use_container_width=True, 
        key="btn_batch_go", 
        disabled=len(usernames)==0,
        help=f"Procesará {min(len(usernames), batch_limit) if usernames else 0} perfiles"
    )
    
    if run_batch and usernames:
        show_info_box(f"🚀 Iniciando procesamiento de <strong>{min(len(usernames), batch_limit)}</strong> perfiles. Esto puede tomar unos minutos.", "info")
        
        rows: List[Dict[str, Any]] = []
        emails_found = 0
        errors = 0
        private_profiles = 0
        work_list = usernames[:batch_limit]

        # Progress tracking mejorado
        progress = st.progress(0, text="Iniciando procesamiento...")
        
        # Métricas en tiempo real
        metrics_container = st.container()
        with metrics_container:
            live_cols = st.columns(4)
            live_metrics = {
                'processed': live_cols[0].empty(),
                'emails': live_cols[1].empty(),
                'errors': live_cols[2].empty(),
                'private': live_cols[3].empty()
            }

        # Log container
        log_container = st.expander("📋 Log de procesamiento", expanded=False)
        
        for i, username in enumerate(work_list, start=1):
            success = False
            last_error = ""
            
            # Intentos con backoff exponencial
            for attempt in range(int(attempts_batch)):
                try:
                    if delay_batch: 
                        backoff_sleep(delay_batch * (1.5**attempt if attempt else 1))
                    
                    with log_container:
                        st.text(f"🔄 Procesando @{username} (intento {attempt+1})")
                    
                    data = cached_profile(L, username)
                    rows.append(data)
                    
                    # Actualizar contadores
                    email_count = int(data.get("emails_count", 0) or 0)
                    emails_found += email_count
                    if data.get("is_private"):
                        private_profiles += 1
                    
                    success = True
                    
                    with log_container:
                        if email_count > 0:
                            st.text(f"✅ @{username}: {email_count} emails encontrados")
                        else:
                            st.text(f"✅ @{username}: Sin emails públicos")
                    break
                    
                except Exception as e:
                    last_error = str(e)
                    with log_container:
                        st.text(f"⚠️ @{username} intento {attempt+1} falló: {last_error}")
            
            if not success:
                errors += 1
                rows.append({
                    "username": username, "error": last_error, "emails": "", "emails_count": 0,
                    "bio": "", "external_url": "", "full_name": "", "is_private": None, "email_sources": ""
                })
                with log_container:
                    st.text(f"❌ @{username}: Error final después de {attempts_batch} intentos")

            # Actualizar progress y métricas
            progress_pct = int(i * 100 / len(work_list))
            progress.progress(progress_pct, text=f"Procesando... {i}/{len(work_list)} ({progress_pct}%)")
            
            # Actualizar métricas en tiempo real
            live_metrics['processed'].metric("✅ Procesados", f"{i}/{len(work_list)}")
            live_metrics['emails'].metric("📧 Emails", emails_found)
            live_metrics['errors'].metric("❌ Errores", errors)
            live_metrics['private'].metric("🔒 Privados", private_profiles)

        # Resultados finales
        df = as_df(rows)
        success_rate = ((len(work_list) - errors) / len(work_list) * 100) if work_list else 0
        
        st.balloons()  # Celebración visual
        st.success("🎉 ¡Procesamiento completado exitosamente!")

        # Métricas finales mejoradas
        st.markdown('<div class="section-header"><span class="section-icon">📈</span><div class="section-title">Resultados del Procesamiento</div></div>', unsafe_allow_html=True)
        
        final_metrics = f"""
        <div class="metrics-grid">
            {create_metric_card("Total Procesados", len(work_list), "📊")}
            {create_metric_card("Emails Encontrados", emails_found, "📧")}
            {create_metric_card("Tasa de Éxito", f"{success_rate:.1f}%", "🎯")}
            {create_metric_card("Perfiles Privados", private_profiles, "🔒")}
        </div>
        """
        st.markdown(final_metrics, unsafe_allow_html=True)

        # Análisis de resultados
        if emails_found > 0:
            show_info_box(f"🎯 <strong>Excelente!</strong> Se encontraron {emails_found} emails en {len(work_list)} perfiles procesados. Tasa de éxito: {success_rate:.1f}%", "success")
        elif errors > len(work_list) * 0.5:
            show_info_box(f"⚠️ <strong>Alta tasa de errores:</strong> {errors} de {len(work_list)} perfiles fallaron. Considera aumentar el delay o reducir el lote.", "warning")
        else:
            show_info_box("ℹ️ Procesamiento completado. Pocos emails encontrados - esto es normal para muchos perfiles públicos.", "info")

        # Tabla de resultados
        st.markdown('<div class="section-header"><span class="section-icon">📋</span><div class="section-title">Datos Extraídos</div></div>', unsafe_allow_html=True)
        
        st.data_editor(
            df,
            use_container_width=True,
            hide_index=True,
            key="editor_batch",
            column_config={
                "username": st.column_config.TextColumn("👤 Username", width="medium"),
                "full_name": st.column_config.TextColumn("📝 Nombre", width="medium"),
                "emails": st.column_config.TextColumn("📧 Emails", help="Separados por comas", width="large"),
                "emails_count": st.column_config.NumberColumn("🔢 N.º", width="small"),
                "bio": st.column_config.TextColumn("📄 Bio", width="large"),
                "external_url": st.column_config.LinkColumn("🔗 URL", width="medium"),
                "is_private": st.column_config.CheckboxColumn("🔒 Privado", width="small"),
                "error": st.column_config.TextColumn("❌ Error", width="medium")
            }
        )
        
        download_buttons(df, base="emails_publicos_lote")

# ========== TAB 3: SEGUIDORES ==========
with tab3:
    st.markdown('<div class="section-header"><span class="section-icon">👥</span><div class="section-title">Análisis de Seguidores</div></div>', unsafe_allow_html=True)
    
    show_info_box("""
    <strong>📱 Analiza los seguidores de tu cuenta</strong><br>
    Sube el archivo de datos de Instagram (ZIP/JSON) que descargaste desde tu cuenta personal.
    Perfecto para analizar tu audiencia y encontrar oportunidades de networking.
    """)
    
    with st.expander("📖 ¿Cómo obtener el archivo de seguidores?", expanded=False):
        st.markdown("""
        ### 📋 Pasos para descargar tus datos de Instagram:
        
        1. **Abre Instagram** en tu móvil o web
        2. Ve a **Configuración** → **Privacidad y seguridad**
        3. Busca **"Descargar datos"** o **"Tu información"**
        4. Selecciona **formato JSON** (no HTML)
        5. Marca **"Seguidores y seguidos"** en las categorías
        6. **Descarga** el archivo (puede tardar hasta 48h)
        7. **Descomprime** el ZIP si es necesario
        8. **Sube** el archivo `followers_*.json` o el ZIP completo aquí
        
        ---
        **📝 Nota:** Solo puedes descargar los datos de tu propia cuenta de Instagram.
        """)

    # Configuración de carga
    col1, col2 = st.columns([3, 1])
    with col1:
        uploaded_followers = st.file_uploader(
            "📁 Archivo de seguidores (ZIP o JSON)",
            type=["zip", "json"], 
            key="followers_zipjson",
            help="Sube el archivo completo de Instagram o el JSON específico de seguidores"
        )
    with col2:
        st.markdown("""
        **📄 Archivos válidos:**
        - `instagram-data.zip`
        - `followers_1.json`
        - `connections.zip`
        
        **📊 Formato esperado:**
        Instagram JSON oficial
        """)

    # Configuración del procesamiento
    st.markdown("**⚙️ Configuración del análisis:**")
    config_cols = st.columns(3)
    
    with config_cols[0]:
        followers_limit = st.number_input(
            "🎯 Límite a procesar", 
            min_value=1, 
            max_value=2000, 
            value=100, 
            step=25,
            key="followers_limit_tab3",
            help="Número máximo de seguidores a analizar"
        )
    with config_cols[1]:
        delay_followers = st.number_input(
            "⏱️ Delay por perfil (s)", 
            min_value=0.0, 
            max_value=5.0, 
            value=1.5, 
            step=0.5,
            key="followers_delay_tab3",
            help="Pausa entre requests (recomendado: 1.5s+)"
        )
    with config_cols[2]:
        attempts_followers = st.number_input(
            "🔄 Reintentos", 
            min_value=1, 
            max_value=5, 
            value=3, 
            step=1,
            key="attempts_followers_tab3",
            help="Intentos por seguidor"
        )

    # Botón de procesamiento
    process_followers = st.button(
        "🚀 Analizar Seguidores", 
        type="primary", 
        use_container_width=True, 
        key="btn_followers_go", 
        disabled=uploaded_followers is None,
        help="Inicia el análisis de los seguidores encontrados en el archivo"
    )

    if process_followers:
        if not uploaded_followers:
            st.error("⚠️ Por favor, sube un archivo ZIP o JSON de seguidores.")
            st.stop()

        with st.status("📂 Analizando archivo de seguidores...", expanded=True) as status:
            try:
                followers_usernames: List[str] = []
                
                # Procesar según el tipo de archivo
                if uploaded_followers.type == "application/zip" or uploaded_followers.name.lower().endswith(".zip"):
                    try:
                        import zipfile
                        with zipfile.ZipFile(uploaded_followers, "r") as zip_file:
                            json_files = [name for name in zip_file.namelist() 
                                         if name.lower().endswith(".json") and "followers" in name.lower()]
                            
                            st.write(f"📄 Archivos JSON encontrados: {len(json_files)}")
                            if json_files:
                                st.write(f"📋 Archivos: {', '.join(json_files[:3])}")
                            
                            if not json_files:
                                st.error("❌ No se encontraron archivos de seguidores en el ZIP.")
                                st.stop()
                            
                            for json_file in json_files:
                                st.write(f"🔍 Procesando {json_file}...")
                                data_bytes = zip_file.read(json_file)
                                parsed_followers = parse_followers_from_instagram_json(data_bytes)
                                followers_usernames.extend(parsed_followers)
                                
                    except Exception as zip_error:
                        # Fallback para archivos ZIP protegidos
                        st.warning(f"ZIP estándar falló: {zip_error}")
                        st.write("🔄 Intentando con pyzipper para archivos protegidos...")
                        try:
                            import pyzipper
                            with pyzipper.AESZipFile(uploaded_followers, "r") as aes_zip:
                                json_files = [n for n in aes_zip.namelist() 
                                             if n.lower().endswith(".json") and "followers" in n.lower()]
                                for json_file in json_files:
                                    data_bytes = aes_zip.read(json_file)
                                    parsed_followers = parse_followers_from_instagram_json(data_bytes)
                                    followers_usernames.extend(parsed_followers)
                        except ImportError:
                            st.error("❌ pyzipper no está instalado. Instala con: pip install pyzipper")
                            st.stop()
                else:
                    # Archivo JSON directo
                    st.write("📄 Procesando archivo JSON directo...")
                    followers_usernames = parse_followers_from_instagram_json(uploaded_followers.getvalue())
                
                status.update(label="✅ Archivo procesado correctamente", state="complete")
                
            except Exception as e:
                status.update(label="❌ Error procesando archivo", state="error")
                st.error(f"Error al leer el archivo: {e}")
                st.stop()

        # Limpiar y preparar lista de seguidores
        followers_usernames = sorted(set([safe_username_from_input(u) for u in followers_usernames if u]))
        
        if not followers_usernames:
            st.warning("❌ No se detectaron usernames de seguidores válidos en el archivo.")
            st.stop()

        total_followers = len(followers_usernames)
        to_process = followers_usernames[:followers_limit]
        estimated_time = len(to_process) * delay_followers

        # Información del procesamiento
        st.markdown('<div class="section-header"><span class="section-icon">📊</span><div class="section-title">Información del Procesamiento</div></div>', unsafe_allow_html=True)
        
        info_metrics = f"""
        <div class="metrics-grid">
            {create_metric_card("Seguidores Totales", total_followers, "👥")}
            {create_metric_card("A Procesar", len(to_process), "🎯")}
            {create_metric_card("Tiempo Estimado", f"{estimated_time/60:.1f} min", "⏱️")}
            {create_metric_card("Delay Configurado", f"{delay_followers}s", "⚙️")}
        </div>
        """
        st.markdown(info_metrics, unsafe_allow_html=True)
        
        if len(to_process) < total_followers:
            show_info_box(f"ℹ️ Se procesarán <strong>{len(to_process)}</strong> de {total_followers} seguidores. Ajusta el límite si quieres procesar más.", "info")

        # Procesamiento de seguidores
        show_info_box(f"🚀 Iniciando análisis de {len(to_process)} seguidores. Este proceso puede tomar <strong>{estimated_time/60:.1f} minutos</strong>.", "info")
        
        followers_data: List[Dict[str, Any]] = []
        emails_found_followers = 0
        errors_followers = 0
        private_followers = 0

        # Progress y métricas en tiempo real
        progress_followers = st.progress(0, text="Iniciando análisis de seguidores...")
        
        metrics_container_followers = st.container()
        with metrics_container_followers:
            live_cols_f = st.columns(4)
            live_metrics_f = {
                'processed': live_cols_f[0].empty(),
                'emails': live_cols_f[1].empty(),
                'errors': live_cols_f[2].empty(),
                'private': live_cols_f[3].empty()
            }

        # Log detallado
        log_followers = st.expander("📋 Log detallado del procesamiento", expanded=False)

        for i, username in enumerate(to_process, start=1):
            success = False
            last_error = ""
            
            # Múltiples intentos con backoff
            for attempt in range(attempts_followers):
                try:
                    if delay_followers: 
                        backoff_sleep(delay_followers * (1.3**attempt if attempt else 1))
                    
                    with log_followers:
                        if attempt == 0:
                            st.text(f"🔄 [{i}/{len(to_process)}] Analizando @{username}")
                        else:
                            st.text(f"🔄 [@{username}] Reintento {attempt+1}/{attempts_followers}")
                    
                    profile_data = cached_profile(L, username)
                    followers_data.append(profile_data)
                    
                    # Actualizar contadores
                    email_count = int(profile_data.get("emails_count", 0) or 0)
                    emails_found_followers += email_count
                    
                    if profile_data.get("is_private"):
                        private_followers += 1
                    
                    success = True
                    
                    with log_followers:
                        if email_count > 0:
                            st.text(f"✅ [@{username}] {email_count} emails encontrados")
                        else:
                            st.text(f"✅ [@{username}] Sin emails públicos")
                    break
                    
                except Exception as e:
                    last_error = str(e)
                    if attempt == attempts_followers - 1:  # Último intento
                        with log_followers:
                            st.text(f"❌ [@{username}] Error final: {last_error}")

            if not success:
                errors_followers += 1
                followers_data.append({
                    "username": username, "error": last_error, "emails": "", "emails_count": 0,
                    "bio": "", "external_url": "", "full_name": "", "is_private": None, "email_sources": ""
                })

            # Actualizar progress y métricas
            progress_pct = int(i * 100 / len(to_process))
            progress_followers.progress(progress_pct, text=f"Analizando seguidores... {i}/{len(to_process)} ({progress_pct}%)")
            
            # Métricas en tiempo real cada 5 perfiles o al final
            if i % 5 == 0 or i == len(to_process):
                live_metrics_f['processed'].metric("✅ Procesados", f"{i}/{len(to_process)}")
                live_metrics_f['emails'].metric("📧 Emails", emails_found_followers)
                live_metrics_f['errors'].metric("❌ Errores", errors_followers)
                live_metrics_f['private'].metric("🔒 Privados", private_followers)

        # Finalización y resultados
        df_followers = as_df(followers_data)
        success_rate_followers = ((len(to_process) - errors_followers) / len(to_process) * 100) if to_process else 0
        
        st.balloons()
        st.success("🎉 ¡Análisis de seguidores completado!")

        # Métricas finales
        st.markdown('<div class="section-header"><span class="section-icon">📈</span><div class="section-title">Resultados del Análisis</div></div>', unsafe_allow_html=True)
        
        final_metrics_followers = f"""
        <div class="metrics-grid">
            {create_metric_card("Seguidores Analizados", len(to_process), "👥")}
            {create_metric_card("Emails Encontrados", emails_found_followers, "📧")}
            {create_metric_card("Tasa de Éxito", f"{success_rate_followers:.1f}%", "🎯")}
            {create_metric_card("Cuentas Privadas", private_followers, "🔒")}
        </div>
        """
        st.markdown(final_metrics_followers, unsafe_allow_html=True)

        # Análisis de insights
        if emails_found_followers > 0:
            email_rate = (emails_found_followers / len(to_process)) * 100
            show_info_box(f"🎯 <strong>Excelentes resultados!</strong> {emails_found_followers} emails encontrados de {len(to_process)} seguidores analizados. Tasa de emails: {email_rate:.1f}%", "success")
        elif private_followers > len(to_process) * 0.7:
            show_info_box(f"🔒 <strong>Muchos perfiles privados:</strong> {private_followers} de {len(to_process)} son privados. Esto limita la extracción de datos.", "info")
        else:
            show_info_box("ℹ️ Análisis completado. Los seguidores tienden a tener pocos emails públicos - esto es completamente normal.", "info")

        # Tabla de resultados de seguidores
        st.markdown('<div class="section-header"><span class="section-icon">📋</span><div class="section-title">Datos de Seguidores</div></div>', unsafe_allow_html=True)
        
        st.data_editor(
            df_followers,
            use_container_width=True,
            hide_index=True,
            key="editor_followers",
            column_config={
                "username": st.column_config.TextColumn("👤 Seguidor", width="medium"),
                "full_name": st.column_config.TextColumn("📝 Nombre", width="medium"), 
                "emails": st.column_config.TextColumn("📧 Emails", help="Emails públicos encontrados", width="large"),
                "emails_count": st.column_config.NumberColumn("🔢 N.º", width="small"),
                "bio": st.column_config.TextColumn("📄 Bio", width="large"),
                "external_url": st.column_config.LinkColumn("🔗 URL", width="medium"),
                "is_private": st.column_config.CheckboxColumn("🔒 Privado", width="small"),
                "error": st.column_config.TextColumn("❌ Error", width="medium")
            }
        )
        
        download_buttons(df_followers, base="seguidores_emails_publicos")

# =========================
# FOOTER MEJORADO
# =========================
st.divider()

footer_html = """
<div style="background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%); 
            border-radius: 16px; padding: 2rem; margin-top: 2rem; text-align: center;">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
        <div>
            <h4 style="margin: 0; color: var(--text-primary);">🛡️ Uso Responsable</h4>
            <p style="margin: 0.5rem 0 0 0; color: var(--text-secondary); font-size: 0.9rem;">
                Solo extrae información pública • Respeta RGPD y términos de servicio • Evita el spam
            </p>
        </div>
        <div style="display: flex; gap: 1rem; align-items: center;">
            <span style="background: rgba(16, 185, 129, 0.1); color: #10b981; padding: 0.5rem 1rem; 
                        border-radius: 20px; font-size: 0.85rem; font-weight: 500;">✅ Ético</span>
            <span style="background: rgba(59, 130, 246, 0.1); color: #3b82f6; padding: 0.5rem 1rem; 
                        border-radius: 20px; font-size: 0.85rem; font-weight: 500;">🔒 Seguro</span>
            <span style="background: rgba(139, 69, 19, 0.1); color: #8b4513; padding: 0.5rem 1rem; 
                        border-radius: 20px; font-size: 0.85rem; font-weight: 500;">⚡ Rápido</span>
        </div>
    </div>
</div>
"""

st.markdown(footer_html, unsafe_allow_html=True)