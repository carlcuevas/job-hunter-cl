"""
Sistema de deduplicación de ofertas entre portales.

Una misma oferta puede aparecer en Computrabajo, Get on Board y Chiletrabajos
con IDs distintos. Detectamos duplicados por similitud de título + empresa
y conservamos la de mayor score (o la que tenga más información).
"""
import re
from typing import List, Dict


def _normalize(text: str) -> str:
    """Normaliza texto para comparación: minúsculas, sin tildes, sin ruido."""
    if not text:
        return ""
    text = text.lower()
    for a, b in [("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"),
                 ("ú", "u"), ("ü", "u"), ("ñ", "n")]:
        text = text.replace(a, b)
    # quitar palabras de ruido comunes
    text = re.sub(r"\b(part\s*time|full\s*time|urgente|remoto|presencial|hibrido)\b", "", text)
    # solo alfanumérico
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _tokens(text: str) -> set:
    return set(_normalize(text).split())


def _similarity(a: str, b: str) -> float:
    """Similitud Jaccard entre dos strings basada en tokens."""
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    inter = len(ta & tb)
    union = len(ta | tb)
    return inter / union if union else 0.0


def _is_duplicate(job_a: Dict, job_b: Dict) -> bool:
    """Determina si dos ofertas son la misma."""
    # Mismo URL exacto
    if job_a.get("url") and job_a.get("url") == job_b.get("url"):
        return True

    title_sim = _similarity(job_a.get("title", ""), job_b.get("title", ""))
    company_sim = _similarity(job_a.get("company", ""), job_b.get("company", ""))

    # Título muy similar + empresa parecida → duplicado
    if title_sim >= 0.8 and company_sim >= 0.5:
        return True
    # Título idéntico (normalizado)
    if title_sim >= 0.95:
        return True

    return False


def _richness(job: Dict) -> int:
    """Puntaje de 'riqueza' de datos para elegir cuál conservar."""
    score = 0
    if job.get("salary"):
        score += 3
    if job.get("modality"):
        score += 2
    if job.get("posted_at"):
        score += 1
    if job.get("description"):
        score += min(len(job["description"]) // 100, 3)
    score += len(job.get("match_tags", []))
    return score


def deduplicate(jobs: List[Dict]) -> List[Dict]:
    """
    Elimina duplicados de una lista de ofertas.
    Conserva la versión más rica (más datos) de cada oferta única.
    Agrega el campo 'also_in' con los otros portales donde aparece.
    """
    unique: List[Dict] = []

    for job in jobs:
        matched = False
        for i, u in enumerate(unique):
            if _is_duplicate(job, u):
                matched = True
                # registrar portales cruzados
                sources = set(u.get("also_in", []))
                sources.add(u.get("source", ""))
                sources.add(job.get("source", ""))

                # conservar la más rica
                if _richness(job) > _richness(u):
                    winner, loser = job, u
                else:
                    winner, loser = u, job

                winner["also_in"] = sorted(s for s in sources if s and s != winner.get("source"))
                unique[i] = winner
                break

        if not matched:
            job.setdefault("also_in", [])
            unique.append(job)

    return unique


def dedup_stats(before: int, after: int) -> Dict:
    return {
        "total_scraped": before,
        "unique": after,
        "duplicates_removed": before - after,
    }
