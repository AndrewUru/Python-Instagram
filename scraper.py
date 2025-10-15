from __future__ import annotations

import random
import re
import time
from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, List, Optional, Sequence, Tuple
from urllib.parse import urlparse

import httpx
import instaloader
from bs4 import BeautifulSoup

try:  # Optional dependency for MX validation.
    import dns.resolver  # type: ignore
except ImportError:  # pragma: no cover - optional dependency missing at runtime.
    dns = None  # type: ignore
else:
    dns = dns.resolver  # type: ignore


EMAIL_REGEX = re.compile(
    r"\b[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,63}\b",
    re.IGNORECASE,
)
DEFAULT_TIMEOUT = 12.0
DEFAULT_DELAY_RANGE = (1.0, 2.5)
MAX_EXTERNAL_LINKS = 5
MAX_REQUEST_RETRIES = 3

USER_AGENTS: Sequence[str] = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/16.6 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1",
)


@dataclass(frozen=True)
class ScrapeSettings:
    """Configuration controlling outbound HTTP requests."""

    timeout: float = DEFAULT_TIMEOUT
    delay_range: Tuple[float, float] = DEFAULT_DELAY_RANGE
    max_links: int = MAX_EXTERNAL_LINKS
    max_retries: int = MAX_REQUEST_RETRIES


def extract_emails(text: Optional[str]) -> List[str]:
    """Return sorted unique emails found inside ``text``."""
    if not text:
        return []
    matches = {
        match.group(0).strip(".,;:?!)(").lower()
        for match in EMAIL_REGEX.finditer(text)
    }
    return sorted(matches)


def username_from_url(url_or_username: str) -> str:
    """Normalize username or profile URL to a plain username."""
    value = (url_or_username or "").strip()
    if not value:
        return ""
    if value.startswith(("http://", "https://")):
        parsed = urlparse(value)
        path = parsed.path.rstrip("/")
        if not path:
            return ""
        return path.split("/")[-1].lstrip("@")
    return value.lstrip("@")


def create_loader_anonymous() -> instaloader.Instaloader:
    """Instantiate Instaloader configured for anonymous, lightweight usage."""
    loader = instaloader.Instaloader(
        download_pictures=False,
        download_videos=False,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        compress_json=False,
        max_connection_attempts=3,
        request_timeout=DEFAULT_TIMEOUT,
        quiet=True,
    )
    loader.context.user_agent = random.choice(USER_AGENTS)
    return loader


def _sleep_with_jitter(delay_range: Tuple[float, float], *, multiplier: float = 1.0) -> None:
    low, high = delay_range
    low = max(0.0, low)
    high = max(low, high)
    if high <= 0.0:
        return
    time.sleep(random.uniform(low, high) * multiplier)


def _build_headers() -> Dict[str, str]:
    ua = random.choice(USER_AGENTS)
    return {
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Referer": "https://www.google.com/",
    }


def _request_url(
    client: httpx.Client,
    url: str,
    settings: ScrapeSettings,
) -> Optional[httpx.Response]:
    last_error: Optional[Exception] = None
    for attempt in range(settings.max_retries):
        try:
            response = client.get(url, headers=_build_headers(), timeout=settings.timeout)
            if response.status_code < 400 and response.text:
                return response
        except httpx.HTTPError as exc:
            last_error = exc
        _sleep_with_jitter(settings.delay_range, multiplier=1.0 + attempt * 0.5)
    if last_error:
        return None
    return None


def fetch_emails_from_url(
    url: str,
    settings: ScrapeSettings | None = None,
) -> Tuple[List[str], List[str]]:
    """Extract emails from the provided URL and its first-level links."""
    if not url:
        return [], []

    settings = settings or ScrapeSettings()
    emails: set[str] = set()
    sources: set[str] = set()

    with httpx.Client(follow_redirects=True, timeout=settings.timeout) as client:
        response = _request_url(client, url, settings)
        if not response:
            return [], []

        _parse_html_for_emails(response.text, emails)

        candidate_links = _candidate_links(response.text, settings.max_links)
        for link in candidate_links:
            resp = _request_url(client, link, settings)
            if not resp:
                continue
            found = extract_emails(resp.text)
            if found:
                emails.update(found)
                sources.add(link)

    return sorted(emails), sorted(sources)


def _parse_html_for_emails(html: str, emails: set[str]) -> None:
    emails.update(extract_emails(html))
    soup = BeautifulSoup(html, "html.parser")
    for mailto in soup.select('a[href^="mailto:"]'):
        address = (mailto.get("href") or "")[7:].split("?")[0].strip()
        if address:
            emails.update(extract_emails(address))


def _candidate_links(html: str, max_links: int) -> List[str]:
    soup = BeautifulSoup(html, "html.parser")
    links: List[str] = []
    for anchor in soup.find_all("a"):
        href = (anchor.get("href") or "").strip()
        if not href:
            continue
        if href.startswith(("http://", "https://")):
            links.append(href)
        if len(links) >= max_links:
            break
    return list(dict.fromkeys(links))


def get_public_profile_data_anonymous(
    loader: instaloader.Instaloader,
    url_or_username: str,
    settings: ScrapeSettings | None = None,
) -> Dict[str, object]:
    """Fetch public profile metadata and collect emails from bio and external URL."""
    settings = settings or ScrapeSettings()
    username = username_from_url(url_or_username)
    if not username:
        raise ValueError("El username no puede estar vacio.")

    _sleep_with_jitter(settings.delay_range)

    try:
        profile = instaloader.Profile.from_username(loader.context, username)
    except instaloader.exceptions.ProfileNotExistsException as exc:  # pragma: no cover
        raise ValueError(f"El perfil @{username} no existe.") from exc
    except instaloader.exceptions.PrivateProfileNotFollowedException as exc:
        raise PermissionError(f"El perfil @{username} es privado.") from exc
    except instaloader.InstaloaderException as exc:  # pragma: no cover
        raise RuntimeError(f"Error al obtener @{username}: {exc}") from exc

    bio = profile.biography or ""
    external_url = profile.external_url or ""

    emails = set(extract_emails(bio))
    email_sources: List[str] = []
    if external_url:
        ext_emails, sources = fetch_emails_from_url(external_url, settings=settings)
        emails.update(ext_emails)
        email_sources = sources

    sorted_emails = sorted(emails)
    return {
        "username": profile.username,
        "full_name": profile.full_name,
        "is_private": profile.is_private,
        "external_url": external_url,
        "bio": bio,
        "emails": sorted_emails,
        "emails_count": len(sorted_emails),
        "email_sources": email_sources,
    }


@lru_cache(maxsize=512)
def _domain_has_mx(domain: str, timeout: float = 2.0) -> bool:
    if dns is None:
        return True
    try:
        answers = dns.resolve(domain, "MX", lifetime=timeout)
        return bool(answers)
    except Exception:  # pragma: no cover - keep optional validation resilient.
        return False


def validate_email_mx(address: str, timeout: float = 2.0) -> bool:
    """Return True if the email address points to a domain with MX records."""
    if not address or "@" not in address:
        return False
    domain = address.split("@", 1)[1].lower()
    return _domain_has_mx(domain, timeout=timeout)
