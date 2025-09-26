import re
from typing import Optional, List, Dict, Tuple
import instaloader
import httpx
from bs4 import BeautifulSoup

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", re.IGNORECASE)

def extract_emails(text: Optional[str]) -> List[str]:
    if not text:
        return []
    return sorted(set(EMAIL_REGEX.findall(text)))

def username_from_url(url_or_username: str) -> str:
    s = url_or_username.strip()
    if s.startswith("http"):
        parts = s.rstrip("/").split("/")
        return parts[-1]
    return s.lstrip("@")

def create_loader_anonymous() -> instaloader.Instaloader:
    """Crea un loader de Instaloader en modo anónimo (sin login)."""
    return instaloader.Instaloader(
        download_pictures=False,
        download_videos=False,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        compress_json=False,
        max_connection_attempts=2,
        request_timeout=15.0,
        quiet=True,
    )

def fetch_emails_from_url(url: str, timeout: float = 10.0) -> Tuple[List[str], List[str]]:
    """Busca emails en la URL (HTML + mailto:) y sigue hasta 5 enlaces de primer nivel."""
    emails: List[str] = []
    sources: List[str] = []
    if not url:
        return emails, sources

    headers = {"User-Agent": "Mozilla/5.0 (compatible; EmailCollector/1.0)"}
    try:
        with httpx.Client(headers=headers, follow_redirects=True, timeout=timeout) as client:
            resp = client.get(url)
            if resp.status_code >= 400 or not resp.text:
                return emails, sources

            html = resp.text
            emails += extract_emails(html)

            soup = BeautifulSoup(html, "html.parser")
            for a in soup.select('a[href^="mailto:"]'):
                mail = a.get("href", "").replace("mailto:", "").split("?")[0]
                if mail:
                    emails.append(mail)

            candidate_links = []
            for a in soup.find_all("a"):
                href = (a.get("href") or "").strip()
                if href and href.startswith("http"):
                    candidate_links.append(href)

            candidate_links = list(dict.fromkeys(candidate_links))[:5]
            for link in candidate_links:
                try:
                    r = client.get(link, timeout=timeout)
                    if r.status_code < 400 and r.text:
                        found = extract_emails(r.text)
                        if found:
                            emails += found
                            sources.append(link)
                except Exception:
                    continue
    except Exception:
        return sorted(set(emails)), sorted(set(sources))

    return sorted(set(emails)), sorted(set(sources))

def get_public_profile_data_anonymous(L: instaloader.Instaloader, url_or_username: str) -> Dict:
    """Lee metadata pública sin login y extrae emails de bio y external_url."""
    user = username_from_url(url_or_username)
    profile = instaloader.Profile.from_username(L.context, user)
    bio = profile.biography or ""
    external_url = profile.external_url or ""

    bio_emails = extract_emails(bio)
    ext_emails, ext_sources = fetch_emails_from_url(external_url) if external_url else ([], [])
    emails = sorted(set(bio_emails + ext_emails))

    return {
        "username": profile.username,
        "full_name": profile.full_name,
        "is_private": profile.is_private,
        "external_url": external_url,
        "bio": bio,
        "emails": ", ".join(emails),
        "emails_count": len(emails),
        "email_sources": ", ".join(ext_sources) if ext_sources else "",
    }
