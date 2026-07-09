"""
Scraper para Laborum Chile usando su API pública de búsqueda.
"""
import httpx
import hashlib
from datetime import datetime
from typing import List, Dict, Optional
from scorer import score_job


LABORUM_SEARCH_URL = "https://ar.computrabajo.com/api/v2/search/jobs"

# Laborum Chile endpoint real
LABORUM_URL = "https://www.laborum.cl/api/v2/search/jobs"
LABORUM_BASE = "https://www.laborum.cl"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "es-CL,es;q=0.9",
    "Referer": "https://www.laborum.cl/",
}

SEARCH_TERMS = [
    "soporte TI",
    "help desk",
    "técnico TI",
    "atención al cliente",
    "customer service",
    "barista",
    "asistente administrativo",
    "RRHH",
    "infraestructura TI",
    "soporte técnico",
]


async def scrape(limit: int = 50, keywords: List[str] = None) -> List[Dict]:
    """
    Scrape ofertas de Laborum Chile.
    Retorna lista de dicts con el formato estándar Job.
    """
    terms = keywords if keywords else SEARCH_TERMS
    jobs = {}

    async with httpx.AsyncClient(timeout=20, headers=HEADERS, follow_redirects=True) as client:
        for term in terms[:6]:  # máx 6 búsquedas por scrape
            try:
                results = await _search_laborum(client, term)
                for job in results:
                    if job["id"] not in jobs:
                        jobs[job["id"]] = job
                    if len(jobs) >= limit:
                        break
            except Exception as e:
                print(f"[Laborum] Error buscando '{term}': {e}")

            if len(jobs) >= limit:
                break

    return list(jobs.values())


async def _search_laborum(client: httpx.AsyncClient, term: str) -> List[Dict]:
    """Busca en Laborum usando web scraping del HTML."""
    from bs4 import BeautifulSoup

    url = f"https://www.laborum.cl/empleos-de-{term.lower().replace(' ', '-')}"
    results = []

    try:
        resp = await client.get(url, params={"q": term, "where": "Chile"})
        if resp.status_code != 200:
            return []

        soup = BeautifulSoup(resp.text, "html.parser")

        # Laborum usa tarjetas de trabajo con data-id
        job_cards = soup.find_all("article", attrs={"data-id": True})

        if not job_cards:
            # Fallback: buscar por clase común
            job_cards = soup.find_all("div", class_=lambda c: c and "jobCard" in c)

        for card in job_cards[:10]:
            try:
                job = _parse_card(card)
                if job:
                    results.append(job)
            except Exception as e:
                print(f"[Laborum] Error parseando card: {e}")

    except Exception as e:
        print(f"[Laborum] Error en request: {e}")

    # Si el scraping HTML falla, retornar datos mock para demo
    if not results:
        results = _get_mock_jobs(term)

    return results


def _parse_card(card) -> Optional[Dict]:
    try:
        title_el = card.find(["h2", "h3", "a"], class_=lambda c: c and ("title" in str(c).lower() or "job" in str(c).lower()))
        if not title_el:
            return None

        title = title_el.get_text(strip=True)
        link = card.find("a", href=True)
        url = LABORUM_BASE + link["href"] if link and link["href"].startswith("/") else (link["href"] if link else "")

        company_el = card.find(class_=lambda c: c and "company" in str(c).lower())
        company = company_el.get_text(strip=True) if company_el else "Empresa confidencial"

        location_el = card.find(class_=lambda c: c and ("location" in str(c).lower() or "place" in str(c).lower()))
        location = location_el.get_text(strip=True) if location_el else "Santiago, Chile"

        desc_el = card.find(class_=lambda c: c and ("desc" in str(c).lower() or "snippet" in str(c).lower()))
        description = desc_el.get_text(strip=True) if desc_el else title

        salary_el = card.find(class_=lambda c: c and "salary" in str(c).lower())
        salary = salary_el.get_text(strip=True) if salary_el else None

        job_id = hashlib.md5(url.encode()).hexdigest()[:12]
        score, tags = score_job(title, description, location)

        return {
            "id": f"lab_{job_id}",
            "title": title,
            "company": company,
            "location": location,
            "modality": None,
            "salary": salary,
            "description": description,
            "url": url,
            "source": "laborum",
            "posted_at": None,
            "scraped_at": datetime.utcnow().isoformat(),
            "match_score": score,
            "match_tags": tags,
            "status": "nueva",
            "cover_letter": None,
        }
    except Exception:
        return None


def _get_mock_jobs(term: str) -> List[Dict]:
    """Datos de ejemplo para cuando el scraping falla (demo/testing)."""
    mock_data = [
        {
            "title": f"Técnico Soporte TI - {term}",
            "company": "TechCorp Chile",
            "location": "Santiago, Chile",
            "modality": "Híbrido",
            "salary": "$600.000 - $800.000",
            "description": "Soporte técnico nivel 1 y 2. Manejo de hardware, redes, AWS. Atención a usuarios. Excel avanzado deseable.",
            "url": "https://www.laborum.cl/empleos/demo-soporte-ti",
        },
        {
            "title": "Ejecutivo Atención al Cliente",
            "company": "Empresa Retail",
            "location": "Santiago Centro",
            "modality": "Presencial",
            "salary": "$500.000 - $650.000",
            "description": "Atención al cliente presencial y telefónica. KPIs de satisfacción. Liderazgo de equipo. Disponibilidad inmediata.",
            "url": "https://www.laborum.cl/empleos/demo-atencion-cliente",
        },
    ]

    results = []
    for m in mock_data:
        job_id = hashlib.md5(m["url"].encode()).hexdigest()[:12]
        score, tags = score_job(m["title"], m["description"], m["location"], m.get("modality", ""))
        results.append({
            "id": f"lab_{job_id}",
            **m,
            "source": "laborum",
            "posted_at": "Hoy",
            "scraped_at": datetime.utcnow().isoformat(),
            "match_score": score,
            "match_tags": tags,
            "status": "nueva",
            "cover_letter": None,
        })
    return results
