"""
Scraper para Computrabajo Chile (cl.computrabajo.com).
Este portal SÍ renderiza el HTML en el servidor, así que el scraping
con httpx + BeautifulSoup funciona de forma confiable.

Estructura verificada:
  - article.box_offer         → cada oferta (20 por página)
  - h2 a                       → título + href
  - <p> internos              → [rating+empresa, ubicación, fecha, estado]
  - data-id                    → id único de la oferta
"""
import httpx
import re
from datetime import datetime
from typing import List, Dict, Optional
from scorer import score_job

CT_BASE = "https://cl.computrabajo.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-CL,es;q=0.9,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

# Términos de búsqueda alineados al perfil de Carlos.
# Computrabajo usa URLs tipo /trabajo-de-{termino-con-guiones}
SEARCH_TERMS = [
    "barista",
    "garzon",
    "atencion-al-cliente",
    "soporte-tecnico",
    "help-desk",
    "mesa-de-ayuda",
    "tecnico-en-computacion",
    "asistente-administrativo",
    "cafeteria",
    "call-center",
    "recursos-humanos",
]


async def scrape(limit: int = 60, keywords: List[str] = None) -> List[Dict]:
    """Scrape ofertas reales de Computrabajo Chile."""
    terms = _keywords_to_terms(keywords) if keywords else SEARCH_TERMS
    jobs = {}

    async with httpx.AsyncClient(
        timeout=25,
        headers=HEADERS,
        follow_redirects=True,
    ) as client:
        for term in terms[:8]:  # hasta 8 búsquedas por corrida
            try:
                results = await _search_term(client, term)
                for job in results:
                    if job["id"] not in jobs:
                        jobs[job["id"]] = job
                if len(jobs) >= limit:
                    break
            except Exception as e:
                print(f"[Computrabajo] Error en '{term}': {e}")

    return list(jobs.values())[:limit]


async def _search_term(client: httpx.AsyncClient, term: str) -> List[Dict]:
    """Busca ofertas para un término dado."""
    from bs4 import BeautifulSoup

    url = f"{CT_BASE}/trabajo-de-{term}"
    results = []

    resp = await client.get(url)
    if resp.status_code != 200:
        print(f"[Computrabajo] HTTP {resp.status_code} para {url}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    articles = soup.select("article.box_offer")

    for art in articles:
        job = _parse_article(art)
        if job:
            results.append(job)

    return results


def _parse_article(art) -> Optional[Dict]:
    """Extrae los datos de una oferta desde un <article.box_offer>."""
    try:
        title_el = art.select_one("h2 a") or art.select_one("a.js-o-link")
        if not title_el:
            return None

        title = title_el.get_text(strip=True)
        if not title:
            return None

        href = title_el.get("href", "")
        # Limpiar el fragmento #lc=... de la URL
        href = href.split("#")[0]
        url = CT_BASE + href if href.startswith("/") else href

        data_id = art.get("data-id") or ""

        # Los <p> internos: [rating+empresa, ubicación, fecha, estado]
        ps = [p.get_text(strip=True) for p in art.select("p")]

        company = "Empresa en Computrabajo"
        location = "Chile"
        posted_at = None

        if len(ps) >= 1 and ps[0]:
            # Quitar el rating tipo "4,0" o "4,2" del inicio
            company = re.sub(r"^\d[,\.]\d\s*", "", ps[0]).strip() or company
        if len(ps) >= 2 and ps[1]:
            location = ps[1]
        if len(ps) >= 3 and ps[2]:
            posted_at = re.sub(r"\s+", " ", ps[2]).strip()

        # Salario: buscar span/p con signo $ o "sueldo"
        salary = None
        salary_el = art.find(string=re.compile(r"\$\s?\d|sueldo|remuneraci", re.I))
        if salary_el:
            salary = re.sub(r"\s+", " ", str(salary_el)).strip()[:60]

        # Modalidad: buscar "remoto", "híbrido", "presencial"
        art_text = art.get_text(" ", strip=True).lower()
        if "remoto" in art_text and "presencial" in art_text:
            modality = "Presencial y remoto"
        elif "remoto" in art_text or "teletrabajo" in art_text:
            modality = "Remoto"
        elif "híbrido" in art_text or "hibrido" in art_text:
            modality = "Híbrido"
        elif "presencial" in art_text:
            modality = "Presencial"
        else:
            modality = None

        # Descripción: texto del artículo sin el título
        desc = art.get_text(" ", strip=True)
        desc = desc.replace(title, "").strip()
        desc = re.sub(r"\s+", " ", desc)[:400] or title

        job_id = f"cot_{data_id}" if data_id else f"cot_{abs(hash(url)) % (10**12)}"
        score, tags = score_job(title, desc, location, modality or "")

        return {
            "id": job_id,
            "title": title,
            "company": company,
            "location": location,
            "modality": modality,
            "salary": salary,
            "description": desc,
            "url": url,
            "source": "computrabajo",
            "posted_at": posted_at,
            "scraped_at": datetime.utcnow().isoformat(),
            "match_score": score,
            "match_tags": tags,
            "status": "nueva",
            "cover_letter": None,
        }
    except Exception as e:
        print(f"[Computrabajo] Error parseando artículo: {e}")
        return None


def _keywords_to_terms(keywords: List[str]) -> List[str]:
    """Convierte keywords a términos de URL de Computrabajo."""
    terms = []
    for kw in keywords:
        t = kw.lower().strip()
        # normalizar tildes
        for a, b in [("á","a"),("é","e"),("í","i"),("ó","o"),("ú","u"),("ñ","n")]:
            t = t.replace(a, b)
        t = re.sub(r"[^a-z0-9\s-]", "", t)
        t = re.sub(r"\s+", "-", t).strip("-")
        if t:
            terms.append(t)
    return terms or SEARCH_TERMS
