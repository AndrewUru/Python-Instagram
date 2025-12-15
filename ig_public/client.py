from __future__ import annotations

import json
import logging
import random
import threading
import time
from typing import Dict, Optional

import requests

from ig_public.cache import username_lock
from ig_public.utils import get_ig_user_agent, get_request_delay_sec, parse_username


LOGGER = logging.getLogger(__name__)

IG_APP_ID = "936619743392459"
PROFILE_ENDPOINT = "https://i.instagram.com/api/v1/users/web_profile_info/"

DEFAULT_TIMEOUT_SEC = 30
DEFAULT_MAX_RETRIES = 3

_LAST_REQUEST_AT = 0.0
_RATE_LOCK = threading.Lock()


class InstagramPublicFetchError(RuntimeError):
    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


def build_instagram_headers(extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    headers = {
        "User-Agent": get_ig_user_agent(),
        "Accept": "*/*",
        "Referer": "https://www.instagram.com/",
        "x-ig-app-id": IG_APP_ID,
    }
    if extra:
        headers.update({str(k): str(v) for k, v in extra.items()})
    return headers


def _respect_min_delay(delay_sec: float) -> None:
    global _LAST_REQUEST_AT  # noqa: PLW0603 - module-level rate limiter.
    delay = max(0.0, float(delay_sec or 0.0))
    if delay <= 0:
        return
    with _RATE_LOCK:
        now = time.monotonic()
        wait = (_LAST_REQUEST_AT + delay) - now
        if wait > 0:
            time.sleep(wait)
        _LAST_REQUEST_AT = time.monotonic()


def fetch_public_profile(
    username: str,
    headers: Optional[Dict[str, str]] = None,
    *,
    timeout_sec: int = DEFAULT_TIMEOUT_SEC,
    max_retries: int = DEFAULT_MAX_RETRIES,
    request_delay_sec: float | None = None,
) -> Dict[str, object]:
    """Fetch public profile + recent posts using Instagram's web_profile_info endpoint."""
    clean = parse_username(username)
    if not clean:
        raise ValueError("Username inválido. Usa '@usuario', 'usuario' o URL de perfil.")

    url = f"{PROFILE_ENDPOINT}?username={clean}"
    merged_headers = build_instagram_headers(headers)
    delay = float(request_delay_sec) if request_delay_sec is not None else float(get_request_delay_sec())

    with username_lock(clean):
        with requests.Session() as session:
            last_error: Optional[Exception] = None
            for attempt in range(max(1, int(max_retries))):
                _respect_min_delay(delay)
                try:
                    response = session.get(url, headers=merged_headers, timeout=int(timeout_sec))
                except requests.Timeout as exc:
                    last_error = exc
                    backoff = min(20.0, (2**attempt) + random.uniform(0.0, 0.3))
                    LOGGER.warning("Timeout consultando @%s (intento %s/%s).", clean, attempt + 1, max_retries)
                    time.sleep(backoff)
                    continue
                except requests.RequestException as exc:
                    last_error = exc
                    raise InstagramPublicFetchError(f"Error de red consultando @{clean}: {exc}") from exc

                status = int(response.status_code)
                if status == 200:
                    try:
                        payload = response.json()
                    except json.JSONDecodeError as exc:
                        raise InstagramPublicFetchError(
                            f"Respuesta inválida (no JSON) al consultar @{clean}."
                        ) from exc
                    if not isinstance(payload, dict):
                        raise InstagramPublicFetchError(
                            f"Respuesta JSON inesperada al consultar @{clean}."
                        )
                    return payload  # type: ignore[return-value]

                if status == 404:
                    raise InstagramPublicFetchError(f"Perfil @{clean} no encontrado (404).", status_code=404)
                if status == 403:
                    raise InstagramPublicFetchError(
                        "Instagram rechazó la petición (403). "
                        "Puede ser un bloqueo temporal. Prueba a cambiar `IG_USER_AGENT` o espera unos minutos.",
                        status_code=403,
                    )

                retryable = status == 429 or status >= 500
                if retryable and attempt < max_retries - 1:
                    retry_after = response.headers.get("Retry-After")
                    backoff = min(30.0, (2**attempt) + random.uniform(0.0, 0.6))
                    if retry_after:
                        try:
                            backoff = max(backoff, float(retry_after))
                        except ValueError:
                            pass
                    LOGGER.warning(
                        "HTTP %s consultando @%s (intento %s/%s). Reintentando en %.1fs",
                        status,
                        clean,
                        attempt + 1,
                        max_retries,
                        backoff,
                    )
                    time.sleep(backoff)
                    continue

                message = response.text.strip()
                message = message[:400] + ("…" if len(message) > 400 else "")
                if status == 429:
                    raise InstagramPublicFetchError(
                        "Rate limit (429). Espera un poco o aumenta `IG_REQUEST_DELAY_SEC`.",
                        status_code=429,
                    )
                raise InstagramPublicFetchError(
                    f"Error HTTP {status} consultando @{clean}. {message}",
                    status_code=status,
                )

            if last_error:
                raise InstagramPublicFetchError(
                    f"No se pudo consultar @{clean} tras {max_retries} intentos: {last_error}"
                ) from last_error
            raise InstagramPublicFetchError(f"No se pudo consultar @{clean} tras {max_retries} intentos.")
