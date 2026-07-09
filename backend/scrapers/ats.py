"""
Scraper de multinacionales vía sus ATS (Applicant Tracking Systems).

Muchas empresas globales publican sus vacantes en APIs PÚBLICAS y legales
(sin login, sin key, sin anti-bot):
  - Greenhouse: https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true
  - Lever:      https://api.lever.co/v0/postings/{token}?mode=json
  - Ashby:      https://api.ashbyhq.com/posting-api/job-board/{token}

Filtramos por roles relevantes al perfil de Carlos (soporte, atención al
cliente, customer success) y por ubicación remota / LATAM / Chile, ya que
son las que realmente puede tomar desde Santiago.
"""
import httpx
import re
from datetime import datetime
from typing import List, Dict, Optional
from scorer import score_job

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json",
}

# Empresas que suelen contratar soporte/atención remoto en LATAM.
# (token del board, plataforma)
COMPANIES = [
    ("gympass",     "greenhouse"),   # Wellhub — soporte LATAM
    ("intercom",    "greenhouse"),   # soporte / CS
    ("gleanwork",   "greenhouse"),
    ("remote",      "greenhouse"),   # Remote.com — hiring global
    ("crunchyroll", "greenhouse"),   # soporte / community
    ("gitlab",      "greenhouse"),   # support engineer remoto LATAM
    ("getwingapp",  "lever"),        # Wing — customer service LATAM
]

# Palabras clave de roles que le sirven a Carlos
RELEVANT_ROLE = re.compile(
    r"(customer\s+(support|service|success|experience)|"
    r"support\s+(specialist|agent|representative|engineer)|"
    r"technical\s+support|help\s?desk|service\s+desk|it\s+support|"
    r"soporte|atenci[oó]n|mesa\s+de\s+ayuda|"
    r"account\s+manager|onboarding|community)",
    re.I,
)

# Ubicaciones que Carlos SÍ puede tomar desde Santiago
GOOD_LOCATION = re.compile(
    r"(anywhere|worldwide|\bglobal\b|latam|latin\s*america|"
    r"am[eé]rica\s+latina|chile|santiago|south\s+america|"
    r"remote\s*[-,]?\s*(latam|americas|global|worldwide)?$|remote\b)",
    re.I,
)

# Ubicaciones geo-bloqueadas que NO le sirven (aunque digan "remote")
BAD_LOCATION = re.compile(
    r"(philippines|india|pakistan|bangladesh|nigeria|kenya|egypt|"
    r"united\s+states|\bus\b|\busa\b|ohio|texas|california|new\s+york|"
    r"united\s+kingdom|\buk\b|germany|france|spain|portugal|poland|"
    r"canada|australia|singapore|japan|china|indonesia|vietnam|"
    r"manila|cebu|delhi|mumbai|bangalore|london|munich|berlin|madrid|"
    r"north\s+america|emea|apac|\beurope\b|middle\s+east|"
    r"united\s+arab|dubai|emirates|africa|asia)",
    re.I,
)


async def scrape(limit: int = 60, keywords: List[str] = None) -> List[Dict]:
    """Scrape vacantes relevantes de multinacionales vía ATS."""
    jobs = {}

    async with httpx.AsyncClient(timeout=20, headers=HEADERS, follow_redirects=True) as client:
        for token, platform in COMPANIES:
            try:
                if platform == "greenhouse":
                    results = await _greenhouse(client, token)
                elif platform == "lever":
                    results = await _lever(client, token)
                elif platform == "ashby":
                    results = await _ashby(client, token)
                else:
                    results = []

                for job in results:
                    if job["id"] not in jobs:
                        jobs[job["id"]] = job
            except Exception as e:
                print(f"[ATS] Error {platform}:{token}: {e}")

            if len(jobs) >= limit:
                break

    return list(jobs.values())[:limit]


def _relevant(title: str, location: str, is_remote: bool = False) -> bool:
    """Filtra: rol relevante + ubicación tomable desde Chile (LATAM/global)."""
    if not RELEVANT_ROLE.search(title or ""):
        return False

    combined = f"{title} {location}"

    # Descartar si está geo-bloqueada a un país que no sirve
    if BAD_LOCATION.search(combined):
        # ...salvo que además diga explícitamente LATAM/Chile
        if not re.search(r"(latam|latin\s*america|am[eé]rica\s+latina|chile)", combined, re.I):
            return False

    # Aceptar si ubicación es LATAM/Chile/global/remota-genérica
    return bool(GOOD_LOCATION.search(combined))


def _build_job(job_id, title, company, location, url, description, modality, posted_at) -> Dict:
    desc = re.sub(r"<[^>]+>", " ", description or "")
    desc = re.sub(r"\s+", " ", desc).strip()[:450] or title
    score, tags = score_job(title, f"{title} {desc}", location, modality or "")
    return {
        "id": job_id,
        "title": title,
        "company": company,
        "location": location or "Remoto",
        "modality": modality,
        "salary": None,
        "description": desc,
        "url": url,
        "source": "ats",
        "posted_at": posted_at,
        "scraped_at": datetime.utcnow().isoformat(),
        "match_score": score,
        "match_tags": tags,
        "status": "nueva",
        "cover_letter": None,
    }


async def _greenhouse(client, token: str) -> List[Dict]:
    url = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true"
    r = await client.get(url)
    if r.status_code != 200:
        return []
    out = []
    company = token.capitalize()
    for j in r.json().get("jobs", []):
        title = j.get("title", "")
        loc = (j.get("location") or {}).get("name", "")
        is_remote = "remote" in (title + " " + loc).lower()
        if not _relevant(title, loc, is_remote):
            continue
        out.append(_build_job(
            job_id=f"ats_gh_{token}_{j.get('id')}",
            title=title, company=company, location=loc,
            url=j.get("absolute_url", ""),
            description=j.get("content", ""),
            modality="Remoto" if is_remote else None,
            posted_at=(j.get("updated_at") or "")[:10],
        ))
    return out


async def _lever(client, token: str) -> List[Dict]:
    url = f"https://api.lever.co/v0/postings/{token}?mode=json"
    r = await client.get(url)
    if r.status_code != 200:
        return []
    out = []
    company = token.capitalize()
    for j in r.json():
        title = j.get("text", "")
        cats = j.get("categories", {}) or {}
        loc = cats.get("location", "") or (j.get("country", "") or "")
        wp = (j.get("workplaceType", "") or "").lower()
        is_remote = wp == "remote" or "remote" in (title + " " + loc).lower()
        if not _relevant(title, loc, is_remote):
            continue
        out.append(_build_job(
            job_id=f"ats_lv_{token}_{j.get('id')}",
            title=title, company=company, location=loc,
            url=j.get("hostedUrl", "") or j.get("applyUrl", ""),
            description=j.get("descriptionPlain", "") or j.get("description", ""),
            modality="Remoto" if is_remote else None,
            posted_at=None,
        ))
    return out


async def _ashby(client, token: str) -> List[Dict]:
    url = f"https://api.ashbyhq.com/posting-api/job-board/{token}"
    r = await client.get(url)
    if r.status_code != 200:
        return []
    out = []
    company = token.capitalize()
    for j in r.json().get("jobs", []):
        title = j.get("title", "")
        loc = j.get("location", "")
        is_remote = bool(j.get("isRemote")) or "remote" in (title + " " + loc).lower()
        if not _relevant(title, loc, is_remote):
            continue
        out.append(_build_job(
            job_id=f"ats_ab_{token}_{j.get('id')}",
            title=title, company=company, location=loc,
            url=j.get("jobUrl", "") or j.get("applyUrl", ""),
            description=j.get("descriptionPlain", ""),
            modality="Remoto" if is_remote else None,
            posted_at=(j.get("publishedAt") or "")[:10],
        ))
    return out
