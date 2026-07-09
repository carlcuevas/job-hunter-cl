"""
Motor de scoring: evalúa qué tan bien encaja una oferta con el perfil de Carlos.
Retorna un score de 0-100 y los tags que matchearon.
"""
import re
from typing import Tuple, List
from profile import PROFILE


def normalize(text: str) -> str:
    """Minúsculas y sin tildes para comparar."""
    replacements = {
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
        "ü": "u", "ñ": "n", "Á": "a", "É": "e", "Í": "i",
        "Ó": "o", "Ú": "u", "Ü": "u", "Ñ": "n",
    }
    text = text.lower()
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text


def score_job(title: str, description: str, location: str = "", modality: str = "") -> Tuple[int, List[str]]:
    """
    Retorna (score: int 0-100, matched_tags: list[str])
    """
    text = normalize(f"{title} {description} {location}")
    matched_tags = []
    score = 0

    # ── 1. Match de roles objetivo (peso alto) ─────────────────────────────
    for role in PROFILE["target_roles"]:
        if normalize(role) in text:
            score += 20
            matched_tags.append(role)
            break  # Solo contar una vez el role match

    # ── 2. Keywords de alta relevancia (peso: 8 c/u, máx 40) ──────────────
    high_matches = []
    for kw in PROFILE["keywords_high"]:
        if normalize(kw) in text:
            high_matches.append(kw)

    score += min(len(high_matches) * 8, 40)
    matched_tags.extend(high_matches)

    # ── 3. Keywords de media relevancia (peso: 3 c/u, máx 15) ─────────────
    medium_matches = []
    for kw in PROFILE["keywords_medium"]:
        if normalize(kw) in text and kw not in matched_tags:
            medium_matches.append(kw)

    score += min(len(medium_matches) * 3, 15)
    matched_tags.extend(medium_matches)

    # ── 4. Keywords de baja relevancia (peso: 1 c/u, máx 5) ───────────────
    low_matches = []
    for kw in PROFILE["keywords_low"]:
        if normalize(kw) in text and kw not in matched_tags:
            low_matches.append(kw)

    score += min(len(low_matches) * 1, 5)

    # ── 5. Bonus/penalización por ubicación (Carlos vive en Santiago) ──────
    loc = normalize(location + " " + modality)
    is_remote = any(x in loc for x in ["remoto", "remote", "teletrabajo", "hibrido"])
    is_metropolitana = any(x in loc for x in [
        "santiago", "metropolit", "providencia", "las condes", "nunoa",
        "maipu", "la florida", "puente alto", "vitacura", "recoleta",
        "estacion central", "san bernardo", "quilicura",
    ])

    # Regiones lejanas — si es presencial fuera de RM, no le sirve a Carlos
    otras_regiones = [
        "antofagasta", "vina del mar", "valparaiso", "concepcion", "temuco",
        "puerto varas", "puerto montt", "iquique", "arica", "la serena",
        "rancagua", "talca", "chillan", "osorno", "calama", "copiapo",
        "punta arenas", "coquimbo", "los angeles", "valdivia",
    ]
    is_otra_region = any(x in loc for x in otras_regiones)

    if is_remote:
        score += 5
    elif is_metropolitana:
        score += 8
    elif is_otra_region:
        score -= 20  # presencial fuera de RM: poco útil

    # ── 6. Penalización si requiere experiencia muy alta ───────────────────
    if re.search(r"\b([5-9]|10|\d{2})\s*años", normalize(description)):
        score -= 15

    # ── 7. Penalización si requiere título universitario completo ──────────
    if re.search(r"(titulo universitario|carrera completa|egresado|ingeniero civil)", normalize(description)):
        score -= 10

    # Clamp entre 0 y 100
    score = max(0, min(100, score))

    # Deduplicar tags
    seen = set()
    unique_tags = []
    for tag in matched_tags:
        if tag not in seen:
            seen.add(tag)
            unique_tags.append(tag)

    return score, unique_tags[:8]  # máx 8 tags visibles


def get_score_label(score: int) -> str:
    if score >= 75:
        return "excelente"
    elif score >= 50:
        return "bueno"
    elif score >= 25:
        return "regular"
    else:
        return "bajo"


def get_score_color(score: int) -> str:
    if score >= 75:
        return "#22c55e"   # verde
    elif score >= 50:
        return "#f59e0b"   # amarillo
    elif score >= 25:
        return "#f97316"   # naranja
    else:
        return "#ef4444"   # rojo
