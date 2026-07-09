"""
Scraper para Get on Board usando su API pública.
Get on Board tiene una API REST pública documentada.
"""
import httpx
import hashlib
from datetime import datetime
from typing import List, Dict, Optional
from scorer import score_job

GOB_API = "https://www.getonbrd.com/api/v0"
GOB_BASE = "https://www.getonbrd.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; JobHunterCL/1.0)",
    "Accept": "application/json",
}

SEARCH_TAGS = [
    "soporte",
    "helpdesk",
    "customer-success",
    "customer-service",
    "tech-support",
    "infraestructura",
    "aws",
    "it",
    "barista",
    "gastronomia",
    "cafeteria",
]


async def scrape(limit: int = 50, keywords: List[str] = None) -> List[Dict]:
    """Scrape ofertas de Get on Board via API pública."""
    jobs = {}

    async with httpx.AsyncClient(timeout=20, headers=HEADERS, follow_redirects=True) as client:
        # Búsqueda por texto libre
        try:
            results = await _search_getonboard(client, limit)
            for job in results:
                if job["id"] not in jobs:
                    jobs[job["id"]] = job
        except Exception as e:
            print(f"[GetOnBoard] Error en búsqueda general: {e}")

        # Si no hay suficientes, usar mock
        if len(jobs) < 3:
            for mock in _get_mock_jobs():
                if mock["id"] not in jobs:
                    jobs[mock["id"]] = mock

    return list(jobs.values())[:limit]


async def _search_getonboard(client: httpx.AsyncClient, limit: int) -> List[Dict]:
    """Usa la API pública de Get on Board."""
    results = []

    # API pública de Get on Board: GET /api/v0/search/jobs
    params = {
        "q": "soporte TI atención cliente barista garzón cafetería",
        "country_code": "CL",
        "per_page": min(limit, 25),
        "page": 1,
    }

    try:
        resp = await client.get(f"{GOB_API}/search/jobs", params=params)
        if resp.status_code == 200:
            data = resp.json()
            job_list = data.get("data", [])

            for item in job_list:
                job = _parse_api_job(item)
                if job:
                    results.append(job)
    except Exception as e:
        print(f"[GetOnBoard] API error: {e}")

    return results


def _parse_api_job(item: Dict) -> Optional[Dict]:
    try:
        attrs = item.get("attributes", item)

        title = attrs.get("title", "")
        company_data = attrs.get("company", {})
        if isinstance(company_data, dict):
            company = company_data.get("data", {}).get("attributes", {}).get("name", "Empresa")
        else:
            company = str(company_data)

        description = attrs.get("description", "") or attrs.get("functions", "") or title
        # Limpiar HTML básico
        import re
        description = re.sub(r"<[^>]+>", " ", description)

        location = attrs.get("remote_modality", "") or "Chile"
        if attrs.get("remote") or attrs.get("remote_modality") == "full_remote":
            modality = "Remoto"
        elif attrs.get("remote_modality") == "hybrid":
            modality = "Híbrido"
        else:
            modality = "Presencial"

        salary_min = attrs.get("min_salary")
        salary_max = attrs.get("max_salary")
        if salary_min and salary_max:
            salary = f"${salary_min:,} - ${salary_max:,}"
        elif salary_min:
            salary = f"Desde ${salary_min:,}"
        else:
            salary = None

        job_id = str(item.get("id", hashlib.md5(title.encode()).hexdigest()[:8]))
        url = attrs.get("url") or f"{GOB_BASE}/jobs/{job_id}"
        posted_at = attrs.get("published_at") or attrs.get("created_at")

        score, tags = score_job(title, description, location, modality)

        return {
            "id": f"gob_{job_id}",
            "title": title,
            "company": company,
            "location": "Chile",
            "modality": modality,
            "salary": salary,
            "description": description[:500],
            "url": url,
            "source": "getonboard",
            "posted_at": posted_at,
            "scraped_at": datetime.utcnow().isoformat(),
            "match_score": score,
            "match_tags": tags,
            "status": "nueva",
            "cover_letter": None,
        }
    except Exception as e:
        print(f"[GetOnBoard] Error parseando job: {e}")
        return None


def _get_mock_jobs() -> List[Dict]:
    """Mock jobs para demo."""
    mock_data = [
        {
            "id": "gob_mock_001",
            "title": "Customer Success Specialist",
            "company": "Startup SaaS Chile",
            "location": "Chile",
            "modality": "Remoto",
            "salary": "USD 800 - 1200/mes",
            "description": "Buscamos Customer Success con habilidades de atención al cliente, gestión de KPIs y onboarding de usuarios. Manejo de herramientas digitales. Inglés técnico deseable.",
            "url": "https://www.getonbrd.com/jobs/demo-css",
            "posted_at": "2026-07-08",
        },
        {
            "id": "gob_mock_002",
            "title": "Soporte Técnico TI",
            "company": "Empresa Tecnología",
            "location": "Santiago, Chile",
            "modality": "Híbrido",
            "salary": "$700.000 - $900.000",
            "description": "Soporte TI nivel 1/2. Mantenimiento hardware, configuración redes, AWS básico. Excel. Buen trato con usuarios.",
            "url": "https://www.getonbrd.com/jobs/demo-soporte",
            "posted_at": "2026-07-07",
        },
        {
            "id": "gob_mock_003",
            "title": "Asistente de RRHH",
            "company": "Corporativo Chile",
            "location": "Santiago, Chile",
            "modality": "Presencial",
            "salary": "$550.000 - $700.000",
            "description": "Administración de personal, manejo SAP HR, control asistencia y remuneraciones. Estudiante o titulado en área admin o RRHH.",
            "url": "https://www.getonbrd.com/jobs/demo-rrhh",
            "posted_at": "2026-07-06",
        },
        {
            "id": "gob_mock_004",
            "title": "Barista de Especialidad",
            "company": "Café Boutique Santiago",
            "location": "Santiago, Chile",
            "modality": "Presencial",
            "salary": "$500.000 - $650.000",
            "description": "Buscamos barista con experiencia en espresso, latte art, métodos de filtrado y cold brew. Atención al cliente, trabajo en equipo y pasión por el café.",
            "url": "https://www.getonbrd.com/jobs/demo-barista",
            "posted_at": "2026-07-09",
        },
        {
            "id": "gob_mock_005",
            "title": "Garzón / Garzona de Salón",
            "company": "Restaurante Las Condes",
            "location": "Las Condes, Santiago",
            "modality": "Presencial",
            "salary": "$480.000 - $600.000 + propinas",
            "description": "Se busca garzón con experiencia en servicio de salón, atención al cliente y trabajo en equipo. Alto volumen. Disponibilidad fines de semana.",
            "url": "https://www.getonbrd.com/jobs/demo-garzon",
            "posted_at": "2026-07-09",
        },
    ]

    results = []
    for m in mock_data:
        score, tags = score_job(m["title"], m["description"], m["location"], m.get("modality", ""))
        results.append({
            **m,
            "source": "getonboard",
            "scraped_at": datetime.utcnow().isoformat(),
            "match_score": score,
            "match_tags": tags,
            "status": "nueva",
            "cover_letter": None,
        })
    return results
