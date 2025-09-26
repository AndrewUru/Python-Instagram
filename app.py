import time
from io import BytesIO
import pandas as pd
import streamlit as st
from scraper import (
    create_loader_anonymous,
    get_public_profile_data_anonymous,
    username_from_url,
)
from parsers import parse_followers_from_instagram_json

# --- Configuración de página ---
st.set_page_config(
    page_title="Instagram Public Email Collector — sin login",
    page_icon="📧",
    layout="wide",
)

# CSS personalizado para mejorar la apariencia
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #833ab4, #fd1d1d, #fcb045);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    
    .subtitle {
        text-align: center;
        color: #666;
        font-size: 1.1rem;
        margin-bottom: 2rem;
        padding: 0 1rem;
    }
    
    .feature-box {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #833ab4;
        margin: 1rem 0;
    }
    
    .stats-container {
        display: flex;
        justify-content: space-around;
        margin: 1rem 0;
    }
    
    .stat-item {
        text-align: center;
        padding: 1rem;
        background: white;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Header mejorado
st.markdown('<div class="main-header">📧 Instagram Public Email Collector</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Extrae emails públicos de forma ética y responsable • Sin necesidad de login</div>', unsafe_allow_html=True)

# Aclaración útil para usuarios con mejor diseño
with st.expander("🛡️ **Información importante y límites de la herramienta**", expanded=False):
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**✅ Qué hace esta herramienta:**")
        st.markdown("""
        - 🔍 Extrae datos **públicos** de perfiles de Instagram
        - 📧 Busca emails visibles en biografías y enlaces externos
        - 📊 Procesa múltiples perfiles de forma automática
        - 💾 Exporta resultados en CSV y Excel
        """)
    
    with col2:
        st.markdown("**⚠️ Limitaciones importantes:**")
        st.markdown("""
        - 🚫 No requiere login ni contraseñas
        - 👁️ Solo accede a información **pública**
        - 🐌 Incluye delays para evitar bloqueos
        - 📁 Para seguidores: usa archivos oficiales de Instagram
        """)

# Loader en modo anónimo (sin credenciales)
L = create_loader_anonymous()

# --- Tabs principales con iconos mejorados ---
tab1, tab2, tab3 = st.tabs([
    "🔎 Perfil único", 
    "📋 Lista de usuarios", 
    "👥 Importar seguidores"
])

# =========================================================
# TAB 1: PERFIL ÚNICO
# =========================================================
with tab1:
    st.markdown("### 🎯 Analizar un perfil específico")
    
    # Layout mejorado en columnas
    col1, col2 = st.columns([3, 1])
    
    with col1:
        url = st.text_input(
            "**URL de perfil o @username**",
            placeholder="Ejemplo: https://www.instagram.com/instagram/ o @instagram",
            help="Puedes usar la URL completa o solo el @username"
        )
    
    with col2:
        delay_single = st.number_input(
            "**Delay (segundos)**",
            min_value=0.0, max_value=5.0, step=0.5, value=1.0,
            key="delay_single",
            help="Tiempo de espera para evitar límites"
        )

    # Botón principal más prominente
    if st.button("🚀 **Extraer información del perfil**", type="primary", use_container_width=True):
        if not url.strip():
            st.error("⚠️ Por favor introduce una URL o @username válido.")
        else:
            # Contenedor de progreso mejorado
            with st.container():
                progress_container = st.empty()
                status_container = st.empty()
                
                try:
                    status_container.info("🔄 Procesando perfil...")
                    progress_bar = progress_container.progress(0)
                    
                    if delay_single > 0:
                        status_container.info(f"⏳ Esperando {delay_single}s para evitar límites...")
                        time.sleep(delay_single)
                    
                    progress_bar.progress(50)
                    status_container.info("📊 Extrayendo datos públicos...")
                    
                    data = get_public_profile_data_anonymous(L, url)
                    df = pd.DataFrame([data])
                    
                    progress_bar.progress(100)
                    status_container.success("✅ ¡Perfil procesado correctamente!")
                    
                    # Mostrar estadísticas
                    if data.get('emails_count', 0) > 0:
                        st.success(f"🎉 ¡Encontrados {data['emails_count']} email(s)!")
                    else:
                        st.warning("📭 No se encontraron emails públicos en este perfil")
                    
                    # Mostrar datos en formato mejorado
                    st.markdown("### 📋 Resultados:")
                    st.dataframe(df, use_container_width=True)
                    
                    # Botones de descarga mejorados
                    col_csv, col_xlsx = st.columns(2)
                    with col_csv:
                        st.download_button(
                            "📄 Descargar CSV",
                            df.to_csv(index=False).encode("utf-8"),
                            file_name=f"{username_from_url(url)}_perfil.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                    
                    with col_xlsx:
                        buf = BytesIO()
                        df.to_excel(buf, index=False)
                        st.download_button(
                            "📊 Descargar Excel",
                            buf.getvalue(),
                            file_name=f"{username_from_url(url)}_perfil.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                        
                except Exception as e:
                    progress_container.empty()
                    status_container.error(f"❌ Error al procesar el perfil: {str(e)}")

# =========================================================
# TAB 2: LISTA DE USERNAMES
# =========================================================
with tab2:
    st.markdown("### 📊 Procesamiento masivo de perfiles")
    
    # Entrada de datos mejorada
    input_method = st.radio(
        "**Selecciona el método de entrada:**",
        ["✏️ Escribir usernames", "📁 Subir archivo CSV"],
        horizontal=True
    )
    
    usernames = []
    
    if input_method == "✏️ Escribir usernames":
        col1, col2 = st.columns([2, 1])
        
        with col1:
            sample = "@instagram\n@natgeo\n@github\n@spotify"
            userlist_text = st.text_area(
                "**Lista de usernames** (uno por línea)",
                height=200,
                placeholder=sample,
                help="Escribe un @username por línea. El @ es opcional."
            )
            
            if userlist_text.strip():
                usernames = [u.strip().lstrip("@") for u in userlist_text.splitlines() if u.strip()]
        
        with col2:
            st.markdown("**📝 Consejos:**")
            st.markdown("""
            - Un username por línea
            - El símbolo @ es opcional
            - Se eliminan duplicados automáticamente
            - Espacios en blanco se ignoran
            """)
    
    else:  # Upload CSV
        uploaded = st.file_uploader(
            "**Sube un archivo CSV con columna 'username'**", 
            type=["csv"],
            help="El archivo debe contener una columna llamada 'username'"
        )
        
        if uploaded is not None:
            try:
                df_in = pd.read_csv(uploaded)
                if "username" in df_in.columns:
                    usernames = df_in["username"].astype(str).str.strip().str.lstrip("@").tolist()
                    st.success(f"✅ Archivo cargado: {len(usernames)} usernames encontrados")
                else:
                    st.error("❌ El CSV debe tener una columna llamada 'username'.")
            except Exception as e:
                st.error(f"❌ Error al leer el CSV: {e}")

    # Configuración del procesamiento
    col1, col2, col3 = st.columns(3)
    
    with col1:
        delay_batch = st.number_input(
            "**Delay por perfil (seg)**",
            min_value=0.0, max_value=5.0, step=0.5, value=1.0,
            key="delay_batch",
            help="Tiempo entre peticiones para evitar bloqueos"
        )
    
    with col2:
        # Limpiar y mostrar stats
        usernames = sorted(set([u for u in usernames if u]))
        st.metric("📊 **Usernames únicos**", len(usernames))
    
    with col3:
        if usernames:
            estimated_time = len(usernames) * delay_batch
            st.metric("⏱️ **Tiempo estimado**", f"{estimated_time:.1f}s")

    # Botón de procesamiento
    if st.button("🚀 **Procesar todos los perfiles**", type="primary", use_container_width=True, disabled=len(usernames)==0):
        if not usernames:
            st.error("⚠️ No hay usernames para procesar.")
        else:
            # Contenedor de progreso
            progress_container = st.container()
            
            with progress_container:
                st.info(f"🔄 Iniciando procesamiento de {len(usernames)} perfiles...")
                
                # Barra de progreso y estadísticas en tiempo real
                progress_bar = st.progress(0)
                status_text = st.empty()
                stats_container = st.empty()
                
                rows = []
                emails_found = 0
                errors_count = 0
                
                for i, u in enumerate(usernames, start=1):
                    try:
                        # Actualizar status
                        status_text.text(f"📊 Procesando: @{u} ({i}/{len(usernames)})")
                        
                        if delay_batch > 0:
                            time.sleep(delay_batch)
                        
                        data = get_public_profile_data_anonymous(L, u)
                        rows.append(data)
                        
                        # Contar emails encontrados
                        if data.get('emails_count', 0) > 0:
                            emails_found += data['emails_count']
                            
                    except Exception as e:
                        errors_count += 1
                        rows.append({
                            "username": u,
                            "error": str(e),
                            "emails": "",
                            "emails_count": 0,
                            "bio": "",
                            "external_url": "",
                            "full_name": "",
                            "is_private": None,
                            "email_sources": ""
                        })
                    
                    # Actualizar progreso y stats
                    progress_bar.progress(int(i * 100 / len(usernames)))
                    
                    # Mostrar estadísticas en tiempo real
                    col1, col2, col3 = stats_container.columns(3)
                    col1.metric("✅ Procesados", i)
                    col2.metric("📧 Emails encontrados", emails_found)
                    col3.metric("❌ Errores", errors_count)

                # Resultados finales
                df = pd.DataFrame(rows)
                
                # Mostrar resumen final
                st.success(f"🎉 ¡Procesamiento completado!")
                
                # Estadísticas finales
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("📊 Total procesados", len(usernames))
                col2.metric("📧 Total emails", emails_found)
                col3.metric("✅ Exitosos", len(usernames) - errors_count)
                col4.metric("❌ Errores", errors_count)
                
                # Mostrar tabla de resultados
                st.markdown("### 📋 Resultados detallados:")
                st.dataframe(df, use_container_width=True)

                # Botones de descarga
                col_csv, col_xlsx = st.columns(2)
                with col_csv:
                    st.download_button(
                        "📄 Descargar CSV completo",
                        df.to_csv(index=False).encode("utf-8"),
                        file_name="emails_publicos_instagram_lote.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                
                with col_xlsx:
                    buf = BytesIO()
                    df.to_excel(buf, index=False)
                    st.download_button(
                        "📊 Descargar Excel completo",
                        buf.getvalue(),
                        file_name="emails_publicos_instagram_lote.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )

# =========================================================
# TAB 3: IMPORTAR SEGUIDORES (JSON/ZIP OFICIAL)
# =========================================================
with tab3:
    st.markdown("### 👥 Procesar seguidores desde archivo oficial")
    
    # Instrucciones mejoradas
    with st.container():
        st.markdown("""
        <div class="feature-box">
        <h4>📱 ¿Cómo obtener el archivo de seguidores?</h4>
        <ol>
        <li><strong>Instagram App</strong> → Configuración → Privacidad → Descargar tu información</li>
        <li>Solicita el archivo en formato <strong>JSON</strong></li>
        <li>Instagram te enviará un ZIP con tus datos</li>
        <li>Sube aquí el <strong>ZIP completo</strong> o extrae el archivo <code>followers_*.json</code></li>
        </ol>
        </div>
        """, unsafe_allow_html=True)
    
    # Upload mejorado
    col1, col2 = st.columns([2, 1])
    
    with col1:
        up = st.file_uploader(
            "**📁 Sube tu archivo de seguidores**", 
            type=["json", "zip"],
            help="Acepta archivos JSON individuales o el ZIP completo de Instagram"
        )
    
    with col2:
        st.markdown("**📋 Formatos aceptados:**")
        st.markdown("""
        - 📦 **ZIP oficial** de Instagram
        - 📄 **JSON** de seguidores extraído
        - 🔍 Auto-detecta archivos relevantes
        """)
    
    # Configuración del procesamiento
    col1, col2 = st.columns(2)
    
    with col1:
        limit = st.number_input(
            "**🎯 Límite de perfiles a procesar**", 
            min_value=1, max_value=10000, value=200, step=50,
            help="Para evitar tiempos excesivos, limita la cantidad inicial"
        )
    
    with col2:
        delay_follow = st.number_input(
            "**⏱️ Delay por perfil (seg)**",
            min_value=0.0, max_value=5.0, step=0.5, value=1.0,
            key="delay_follow",
            help="Tiempo entre peticiones para evitar bloqueos"
        )

    # Botón de procesamiento
    if st.button("🚀 **Procesar archivo de seguidores**", type="primary", use_container_width=True, disabled=up is None):
        if not up:
            st.error("⚠️ Por favor sube un archivo JSON o ZIP.")
        else:
            try:
                # Análisis inicial del archivo
                with st.spinner("🔍 Analizando archivo..."):
                    usernames = []
                    
                    if up.type == "application/zip" or up.name.lower().endswith(".zip"):
                        import pyzipper
                        with pyzipper.AESZipFile(up, "r") as zf:
                            candidates = [
                                n for n in zf.namelist()
                                if "followers" in n.lower() and n.lower().endswith(".json")
                            ]
                            
                            if not candidates:
                                st.error("❌ No se encontraron archivos JSON de seguidores en el ZIP.")
                                st.stop()
                            
                            st.info(f"📁 Archivos encontrados: {', '.join(candidates)}")
                            
                            for name in candidates:
                                data_bytes = zf.read(name)
                                usernames.extend(parse_followers_from_instagram_json(data_bytes))
                    else:
                        usernames = parse_followers_from_instagram_json(up.getvalue())

                # Procesamiento de usernames
                usernames = sorted(set(usernames))
                
                if not usernames:
                    st.warning("⚠️ No se detectaron usernames de seguidores en el archivo.")
                    st.stop()

                # Aplicar límite
                original_count = len(usernames)
                usernames = usernames[:limit]
                
                # Mostrar estadísticas iniciales
                col1, col2, col3 = st.columns(3)
                col1.metric("👥 Total en archivo", original_count)
                col2.metric("🎯 A procesar", len(usernames))
                col3.metric("⏱️ Tiempo estimado", f"{len(usernames) * delay_follow:.1f}s")
                
                if original_count > limit:
                    st.info(f"ℹ️ Se procesarán los primeros {limit} seguidores de {original_count} totales.")

                # Procesamiento con progreso mejorado
                st.markdown("### 🔄 Procesando seguidores...")
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                stats_container = st.empty()
                
                rows = []
                emails_found = 0
                errors_count = 0
                
                for i, u in enumerate(usernames, start=1):
                    try:
                        # Actualizar status
                        status_text.text(f"📊 Procesando seguidor: @{u} ({i}/{len(usernames)})")
                        
                        if delay_follow > 0:
                            time.sleep(delay_follow)
                        
                        data = get_public_profile_data_anonymous(L, u)
                        rows.append(data)
                        
                        # Contar emails
                        if data.get('emails_count', 0) > 0:
                            emails_found += data['emails_count']
                            
                    except Exception as e:
                        errors_count += 1
                        rows.append({
                            "username": u,
                            "error": str(e),
                            "emails": "",
                            "emails_count": 0,
                            "bio": "",
                            "external_url": "",
                            "full_name": "",
                            "is_private": None,
                            "email_sources": ""
                        })
                    
                    # Actualizar progreso
                    progress_bar.progress(int(i * 100 / len(usernames)))
                    
                    # Stats en tiempo real cada 10 procesamientos
                    if i % 10 == 0 or i == len(usernames):
                        col1, col2, col3 = stats_container.columns(3)
                        col1.metric("✅ Procesados", i)
                        col2.metric("📧 Emails encontrados", emails_found)
                        col3.metric("❌ Errores", errors_count)

                # Resultados finales
                df = pd.DataFrame(rows)
                
                st.success("🎉 ¡Procesamiento de seguidores completado!")
                
                # Estadísticas finales
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("👥 Seguidores procesados", len(usernames))
                col2.metric("📧 Total emails encontrados", emails_found)
                col3.metric("✅ Perfiles exitosos", len(usernames) - errors_count)
                col4.metric("📊 Tasa de éxito", f"{((len(usernames) - errors_count) / len(usernames) * 100):.1f}%")
                
                # Tabla de resultados
                st.markdown("### 📋 Resultados de seguidores:")
                st.dataframe(df, use_container_width=True)

                # Botones de descarga
                col_csv, col_xlsx = st.columns(2)
                with col_csv:
                    st.download_button(
                        "📄 Descargar CSV de seguidores",
                        df.to_csv(index=False).encode("utf-8"),
                        file_name="seguidores_emails_publicos.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                
                with col_xlsx:
                    buf = BytesIO()
                    df.to_excel(buf, index=False)
                    st.download_button(
                        "📊 Descargar Excel de seguidores",
                        buf.getvalue(),
                        file_name="seguidores_emails_publicos.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                    
            except Exception as e:
                st.error(f"❌ Error procesando el archivo: {str(e)}")

# Footer mejorado
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem;">
    <p>🛡️ <strong>Uso responsable:</strong> Esta herramienta solo accede a información pública de Instagram.</p>
    <p>📧 Utiliza los emails obtenidos de forma ética y respetando las políticas anti-spam.</p>
    <p>⚖️ El usuario es responsable del cumplimiento de las leyes locales de privacidad y protección de datos.</p>
</div>
""", unsafe_allow_html=True)