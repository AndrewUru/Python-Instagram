# Instagram Tools (Streamlit)

App en **Python + Streamlit** para trabajar con datos públicos de Instagram (sin login).

## Instalación local

```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
streamlit run app.py
```

## Análisis público de Instagram

Nueva página en Streamlit: `IG Public Analyzer` (menú lateral).

### Qué hace

- Consulta el endpoint no oficial:
  `https://i.instagram.com/api/v1/users/web_profile_info/?username=<username>`
- Normaliza perfil y posts recientes (hasta N).
- Aplica **caché local** en `.ig_cache/` por username (JSON, sin dependencias extra).
- Exporta a **CSV/JSON** y permite generar un **snapshot** descargable.

### Cómo usarlo (UI)

1. Abre la página `IG Public Analyzer`.
2. Pega un `@username` o una URL del perfil (`https://instagram.com/<user>`).
3. Pulsa **Analizar**.
4. Revisa perfil, tabla de posts, KPI de ER estimado y gráficos.
5. Descarga `perfil.csv`, `posts.csv`, `perfil.json`, `posts.json`, `summary.json` o el snapshot.

### Cómo usarlo (CLI)

Ejemplo:

```bash
python examples/run_ig_cli.py --username @notjustanalytics --max-posts 24 --out out/
```

Genera en `out/`:
- `perfil.csv` (1 fila)
- `posts.csv` (N filas)
- `perfil.json`, `posts.json`
- `summary.json`
- `report_ig_<username>_<fecha>.json` (snapshot)

### Variables de entorno (.env opcional)

Si no existe `.env`, la app usa defaults.

```env
IG_USER_AGENT="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
IG_MAX_POSTS=24
IG_CACHE_TTL_HOURS=6
IG_REQUEST_DELAY_SEC=2.5
```

Opcional:
- `IG_TIMEZONE` (por defecto `Europe/Madrid`) para el heatmap de día/hora.

### Límites y consideraciones

- **Solo datos públicos**: no incluye métricas privadas (reach/impresiones/saves).
- Es un endpoint no oficial: puede romperse si Instagram cambia su web o aplica bloqueos (403/429).
- El rate limiting básico se controla con `IG_REQUEST_DELAY_SEC` y un candado por username.

