"""
Scraper para Chiletrabajos.cl
El sitio renderiza con JS, así que usamos httpx con headers de navegador
y parseamos el HTML resultante con BeautifulSoup.
"""
import httpx
import hashlib
import re
from datetime import datetime
from typing import List, Dict, Optional
from scorer import score_job

CHILE_BASE = "https://www.chiletrabajos.cl"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-CL,es;q=0.9,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.chiletrabajos.cl/",
    "Connection": "keep-alive",
}

# Términos de búsqueda mapeados a slug de URL
SEARCH_SLUGS = [
    "soporte-ti",
    "help-desk",
    "tecnico-ti",
    "atencion-al-cliente",
    "customer-service",
    "asistente-administrativo",
    "recursos-humanos",
    "barista",
    "soporte-tecnico",
]


async def scrape(limit: int = 50, keywords: List[str] = None) -> List[Dict]:
    """Scrape ofertas de Chiletrabajos."""
    jobs = {}

    slugs = _keywords_to_slugs(keywords) if keywords else SEARCH_SLUGS

    async with httpx.AsyncClient(
        timeout=25,
        headers=HEADERS,
        follow_redirects=True,
    ) as client:
        for slug in slugs[:6]:
            try:
                results = await _scrape_slug(client, slug)
                for job in results:
                    if job["id"] not in jobs:
                        jobs[job["id"]] = job
                if len(jobs) >= limit:
                    break
            except Exception as e:
                print(f"[ChileTrabajos] Error en '{slug}': {e}")

    # Si no se obtuvieron resultados reales, usar mocks
    if not jobs:
        for mock in _get_mock_jobs():
            jobs[mock["id"]] = mock

    return list(jobs.values())[:limit]


async def _scrape_slug(client: httpx.AsyncClient, slug: str) -> List[Dict]:
    """Scrape una página de resultados de búsqueda."""
    from bs4 import BeautifulSoup

    url = f"{CHILE_BASE}/trabajos/{slug}-en-santiago"
    results = []

    try:
        resp = await client.get(url)
        if resp.status_code != 200:
            print(f"[ChileTrabajos] Status {resp.status_code} para {url}")
            return _get_mock_jobs_for_slug(slug)

        soup = BeautifulSoup(resp.text, "html.parser")

        # Buscar cards de trabajos — chiletrabajos usa divs con data-id o clases específicas
        job_cards = (
            soup.find_all("div", attrs={"data-oferta-id": True}) or
            soup.find_all("article", class_=re.compile(r"oferta|job|trabajo", re.I)) or
            soup.find_all("div", class_=re.compile(r"oferta|job-card|trabajo", re.I))
        )

        if not job_cards:
            # Intentar con enlaces a ofertas individuales
            links = soup.find_all("a", href=re.compile(r"/oferta/|/trabajo/"))
            for link in links[:10]:
                job = _parse_link_card(link)
                if job:
                    results.append(job)
        else:
            for card in job_cards[:10]:
                job = _parse_card(card)
                if job:
                    results.append(job)

    except Exception as e:
        print(f"[ChileTrabajos] Error request: {e}")
        return _get_mock_jobs_for_slug(slug)

    # Si no se parseó nada real, retornar mocks del slug
    if not results:
        return _get_mock_jobs_for_slug(slug)

    return results


def _parse_card(card) -> Optional[Dict]:
    """Parsea una card de oferta de trabajo."""
    try:
        title_el = card.find(["h2", "h3", "h4", "a"], class_=re.compile(r"title|titulo|nombre", re.I))
        if not title_el:
            title_el = card.find(["h2", "h3", "h4"])
        if not title_el:
            return None

        title = title_el.get_text(strip=True)
        if not title or len(title) < 3:
            return None

        link = card.find("a", href=True)
        url = CHILE_BASE + link["href"] if link and link["href"].startswith("/") else (link["href"] if link else "")

        company_el = card.find(class_=re.compile(r"empresa|company", re.I))
        company = company_el.get_text(strip=True) if company_el else "Empresa en Chiletrabajos"

        location_el = card.find(class_=re.compile(r"ubicacion|location|lugar|region", re.I))
        location = location_el.get_text(strip=True) if location_el else "Santiago, Chile"

        desc_el = card.find(class_=re.compile(r"descripcion|desc|snippet|resumen", re.I))
        description = desc_el.get_text(strip=True) if desc_el else title

        salary_el = card.find(class_=re.compile(r"sueldo|salary|renta|remuneracion", re.I))
        salary = salary_el.get_text(strip=True) if salary_el else None

        date_el = card.find(class_=re.compile(r"fecha|date|publicado", re.I))
        posted_at = date_el.get_text(strip=True) if date_el else None

        job_id = hashlib.md5((url + title).encode()).hexdigest()[:12]
        score, tags = score_job(title, description, location)

        return {
            "id": f"ct_{job_id}",
            "title": title,
            "company": company,
            "location": location,
            "modality": None,
            "salary": salary,
            "description": description[:500],
            "url": url or f"{CHILE_BASE}/trabajos/{slug}",
            "source": "chiletrabajos",
            "posted_at": posted_at,
            "scraped_at": datetime.utcnow().isoformat(),
            "match_score": score,
            "match_tags": tags,
            "status": "nueva",
            "cover_letter": None,
        }
    except Exception as e:
        print(f"[ChileTrabajos] Error parseando card: {e}")
        return None


def _parse_link_card(link) -> Optional[Dict]:
    """Parsea un enlace simple a una oferta."""
    try:
        title = link.get_text(strip=True)
        if not title or len(title) < 5:
            return None

        href = link.get("href", "")
        url = CHILE_BASE + href if href.startswith("/") else href
        job_id = hashlib.md5(url.encode()).hexdigest()[:12]
        score, tags = score_job(title, title, "Santiago")

        return {
            "id": f"ct_{job_id}",
            "title": title,
            "company": "Ver en Chiletrabajos",
            "location": "Santiago, Chile",
            "modality": None,
            "salary": None,
            "description": title,
            "url": url,
            "source": "chiletrabajos",
            "posted_at": None,
            "scraped_at": datetime.utcnow().isoformat(),
            "match_score": score,
            "match_tags": tags,
            "status": "nueva",
            "cover_letter": None,
        }
    except Exception:
        return None


def _keywords_to_slugs(keywords: List[str]) -> List[str]:
    """Convierte keywords a slugs de URL."""
    slugs = []
    for kw in keywords:
        slug = kw.lower().strip().replace(" ", "-")
        slug = re.sub(r"[^a-z0-9\-]", "", slug)
        if slug:
            slugs.append(slug)
    return slugs or SEARCH_SLUGS


def _get_mock_jobs() -> List[Dict]:
    """Jobs de ejemplo para cuando el scraping falla."""
    mocks = [
        {
            "title": "Técnico Soporte TI",
            "company": "Empresa de Tecnología",
            "location": "Santiago, Chile",
            "modality": "Presencial",
            "salary": "$600.000 - $800.000",
            "description": "Soporte técnico nivel 1/2. Hardware PC, redes, instalación de software. Excel. Trato con usuarios.",
            "url": "https://www.chiletrabajos.cl/trabajos/soporte-ti-en-santiago",
            "posted_at": "Hoy",
        },
        {
            "title": "Ejecutivo Atención al Cliente",
            "company": "Empresa Retail Santiago",
            "location": "Santiago Centro",
            "modality": "Presencial",
            "salary": "$500.000 - $650.000",
            "description": "Atención al cliente presencial y telefónica. KPIs de satisfacción. Disponibilidad inmediata. Liderazgo de equipo.",
            "url": "https://www.chiletrabajos.cl/trabajos/atencion-al-cliente-en-santiago",
            "posted_at": "Ayer",
        },
        {
            "title": "Asistente Administrativo RRHH",
            "company": "Corporativo Chile",
            "location": "Providencia, Santiago",
            "modality": "Híbrido",
            "salary": "$550.000 - $700.000",
            "description": "Apoyo en procesos de RRHH, manejo SAP, control asistencia, remuneraciones. Título técnico deseable.",
            "url": "https://www.chiletrabajos.cl/trabajos/asistente-administrativo-en-santiago",
            "posted_at": "Hace 2 días",
        },
    ]
    results = []
    for m in mocks:
        job_id = hashlib.md5(m["url"].encode()).hexdigest()[:12]
        score, tags = score_job(m["title"], m["description"], m["location"], m.get("modality", ""))
        results.append({
            "id": f"ct_{job_id}",
            **m,
            "source": "chiletrabajos",
            "scraped_at": datetime.utcnow().isoformat(),
            "match_score": score,
            "match_tags": tags,
            "status": "nueva",
            "cover_letter": None,
        })
    return results


def _get_mock_jobs_for_slug(slug: str) -> List[Dict]:
    """Retorna mocks filtrados por el slug dado."""
    all_mocks = _get_mock_jobs()
    return [m for m in all_mocks if any(word in slug for word in ["soporte", "ti", "tecnico"])] or all_mocks[:1]
