# 📧 Instagram Public Email Collector — sin login

[![Streamlit](https://img.shields.io/badge/Streamlit-Deployed-brightgreen)](https://andrewuru-python-instagram-app-jjymjx.streamlit.app/)
[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Extrae **emails públicos visibles** desde bios y enlaces de perfiles de Instagram.  
Sin necesidad de login ni contraseñas. Úsalo con responsabilidad (nada de spam).

---

## ✨ Funcionalidades

- 🔎 **Perfil único**: ingresa una URL o @username → extrae los emails públicos de la bio y del `external_url`.  
- 📋 **Lista de usernames**: procesa múltiples perfiles de forma masiva.  
- 👥 **Importar seguidores**: sube tu ZIP/JSON oficial descargado desde Instagram → procesa todos tus seguidores.  
- 📂 **Exporta resultados** en **CSV** o **XLSX**.  
- ⏱ **Delay configurable** entre peticiones para evitar bloqueos.  
- 🔗 **Scraping extendido** en links externos (`Linktree`, webs personales, etc.) hasta 5 enlaces de primer nivel.

---

## 🚀 Demo en vivo

👉 [Accede aquí](https://andrewuru-python-instagram-app-jjymjx.streamlit.app/)

---

## 🛠 Instalación local

```bash
# Clonar el repositorio
git clone <tu-repo-url>
cd python-instagram-app

# Crear y activar entorno virtual
python -m venv .venv
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar la app
streamlit run app.py

📂 Estructura del proyecto
python-instagram-app/
├─ app.py                 # Interfaz principal en Streamlit
├─ scraper.py             # Funciones de scraping y extracción de emails
├─ parsers.py             # Parseo de JSON de seguidores de Instagram
├─ requirements.txt       # Dependencias del proyecto
└─ runtime.txt            # Versión de Python (ej. 3.11 para despliegue en Streamlit Cloud)

⚠️ Consideraciones técnicas

La app solo funciona en modo anónimo → no obtiene la lista de seguidores de cuentas de terceros.

Para procesar seguidores, el usuario debe subir su propio ZIP/JSON oficial de Instagram (followers.json).

No todos los perfiles tendrán correos disponibles (depende de lo que compartan en bio o links).

Usa delay si procesas muchas cuentas para evitar bloqueos.

🌐 Cómo exportar tus seguidores

Entra a Instagram web
 → Configuración y privacidad → Centro de cuentas.

Ve a Tu información y permisos → Descargar tu información.

Elige Formato: JSON y selecciona Seguidores/Seguidos.

Recibirás un ZIP por email.

Sube ese ZIP a la pestaña Importar seguidores en la app.

📜 Ética y uso responsable

Solo recolecta datos públicos expuestos por el propio usuario.

No usar para campañas de spam ni prácticas ilegales.

Si lo conviertes en SaaS, incluye términos de uso y política de privacidad.

🗺 Roadmap / Futuras mejoras

✅ Validación de emails vía MX/SMTP.

✅ Integración OAuth (API Graph oficial de Meta) para scraping autorizado.

✅ Exportación adicional a Google Sheets.

✅ Planes de suscripción con límite de créditos.

✅ UI avanzada con Next.js + FastAPI backend.

📄 Licencia

Este proyecto está bajo licencia MIT. Consulta el archivo LICENSE
 para más información.