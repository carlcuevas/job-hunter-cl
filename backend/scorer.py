"""
Motor de scoring v2 — evalúa qué tan bien encaja una oferta con el perfil de Carlos.

Enfoque:
  1. CATEGORÍAS con rol CENTRAL obligatorio (barista, garzón, soporte TI,
     atención al cliente, RRHH/admin). Una oferta necesita al menos un término
     central para tener puntaje relevante — evita falsos positivos por palabras
     sueltas como "café" en "auxiliar de aseo de cafetería".
  2. EXCLUSIONES: cargos claramente ajenos (cocina, aseo, guardia, salud,
     contabilidad, ventas terreno, etc.) se descartan salvo que el título tenga
     un rol central válido.
  3. UBICACIÓN como modificador (remoto/RM suma, otras regiones resta) que solo
     pesa cuando ya hay relevancia de rol.
  4. Coincidencias por límite de palabra (no substring) para evitar ruido.

Mantiene la firma score_job(title, description, location, modality) -> (int, tags).
"""
import re
from typing import Tuple, List


def normalize(text: str) -> str:
    """Minúsculas y sin tildes."""
    replacements = {
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
        "ü": "u", "ñ": "n",
    }
    text = (text or "").lower()
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text


def _has(term: str, text: str) -> bool:
    """Coincidencia por límite de palabra (evita 'cafe' dentro de otras palabras)."""
    return re.search(r"(?<![a-z0-9])" + re.escape(normalize(term)) + r"(?![a-z0-9])", text) is not None


# ── Categorías: cada una con términos CENTRALES (obligatorios) y de APOYO ──────
CATEGORIES = {
    "barista": {
        "core": ["barista", "baristas"],
        "support": ["espresso", "latte art", "cappuccino", "cold brew", "cafe de especialidad",
                    "especialidad", "molino", "metodos de filtrado", "cafeteria de especialidad"],
        "label": "Barista",
    },
    "garzon": {
        "core": ["garzon", "garzona", "garzones", "mesero", "mesera", "mozo"],
        "support": ["servicio de mesa", "salon", "runner", "atencion de mesa", "propinas"],
        "label": "Garzón / Servicio",
    },
    "atencion_cliente": {
        "core": ["atencion al cliente", "servicio al cliente", "customer service",
                 "customer success", "customer experience", "customer support",
                 "ejecutivo de atencion", "call center", "contact center",
                 "atencion de clientes", "servicio a clientes", "ejecutivo de servicio"],
        "support": ["kpi", "satisfaccion", "fidelizacion", "postventa", "telefonica",
                    "reclamos", "soporte a clientes", "experiencia del cliente"],
        "label": "Atención al Cliente",
    },
    "soporte_ti": {
        "core": ["soporte ti", "soporte tecnico", "help desk", "helpdesk", "mesa de ayuda",
                 "service desk", "tecnico en computacion", "tecnico informatico",
                 "soporte informatico", "tecnico de soporte", "it support",
                 "technical support", "support engineer", "soporte de sistemas"],
        "support": ["hardware", "redes", "aws", "cloud", "windows", "office 365",
                    "impresoras", "tickets", "nivel 1", "nivel 2", "n1", "n2",
                    "active directory", "remoto", "software"],
        "label": "Soporte TI",
    },
    "rrhh_admin": {
        "core": ["asistente de recursos humanos", "asistente rrhh", "administracion de personal",
                 "asistente administrativo", "auxiliar administrativo", "administrativo rrhh",
                 "analista de recursos humanos", "asistente de personas"],
        "support": ["sap", "remuneraciones", "asistencia", "excel", "planillas",
                    "contratos", "onboarding", "reclutamiento"],
        "label": "RRHH / Admin",
    },
}

# ── Exclusiones: cargos claramente fuera del perfil de Carlos ─────────────────
EXCLUSIONS = [
    # cocina / gastronomía de producción
    "cocina", "cocinero", "cocinera", "chef", "ayudante de cocina", "maestro de cocina",
    "pizzero", "sushiman", "panadero", "pastelero", "carnicero", "repostero",
    # aseo / limpieza / mantención
    "aseo", "limpieza", "auxiliar de aseo", "nochero", "jardinero", "sanitizacion",
    # seguridad
    "guardia", "vigilante", "seguridad", "nochero",
    # salud
    "dentista", "odontolog", "enfermer", "medico", "kinesiolog", "matron",
    "tecnico paramedico", "auxiliar de enfermeria", "farmaceutic", "psicolog",
    # finanzas / legal
    "contador", "contable", "contabilidad", "auditor", "tesoreria", "abogad",
    # ventas terreno / comercial dura
    "vendedor", "ejecutivo comercial", "ejecutivo de ventas", "ingeniero de ventas",
    "asesor comercial", "promotor", "corredor",
    # ingeniería/oficios pesados
    "ingeniero civil", "ingeniero comercial", "arquitecto", "topografo",
    "soldador", "electricista", "gasfiter", "maestro", "obrero", "construccion",
    "operario de produccion", "prevencionista",
    # logística/transporte
    "chofer", "conductor", "repartidor", "bodeguero", "grua", "peoneta",
]


def score_job(title: str, description: str, location: str = "", modality: str = "") -> Tuple[int, List[str]]:
    """Retorna (score 0-100, tags relevantes)."""
    ntitle = normalize(title)
    ndesc = normalize(description)
    nall = f"{ntitle} {ndesc}"

    tags: List[str] = []

    # ── 1. Detectar mejor categoría ────────────────────────────────────────
    best_cat_score = 0
    best_cat_tags: List[str] = []
    core_in_title = False

    for cat, cfg in CATEGORIES.items():
        core_hit_title = any(_has(t, ntitle) for t in cfg["core"])
        core_hit_desc = any(_has(t, ndesc) for t in cfg["core"])
        if not (core_hit_title or core_hit_desc):
            continue

        # Base según dónde aparece el rol central
        cat_score = 50 if core_hit_title else 22
        cat_tags = [cfg["label"]]

        # Términos de apoyo
        support_hits = [s for s in cfg["support"] if _has(s, nall)]
        cat_score += min(len(support_hits) * 6, 24)
        cat_tags += support_hits[:4]

        if cat_score > best_cat_score:
            best_cat_score = cat_score
            best_cat_tags = cat_tags
            core_in_title = core_hit_title

    score = best_cat_score
    tags = best_cat_tags

    # ── 2. Exclusiones ─────────────────────────────────────────────────────
    excl_in_title = any(_has(e, ntitle) for e in EXCLUSIONS)
    if excl_in_title and not core_in_title:
        # Cargo ajeno y sin rol válido en el título → descartar
        return (min(score, 6), [])

    # Si no hubo ninguna categoría, es irrelevante
    if best_cat_score == 0:
        return (0, [])

    # ── 3. Modificador por ubicación (solo pesa si ya hay relevancia) ──────
    loc = normalize(f"{location} {modality}")
    is_remote = any(_has(x, loc) or x in loc for x in ["remoto", "remote", "teletrabajo", "hibrido", "home office"])
    is_rm = any(x in loc for x in [
        "santiago", "metropolit", "providencia", "las condes", "nunoa", "maipu",
        "la florida", "puente alto", "vitacura", "recoleta", "estacion central",
        "san bernardo", "quilicura", "penalolen", "la reina", "macul",
    ])
    otras = ["antofagasta", "vina del mar", "valparaiso", "concepcion", "temuco",
             "puerto varas", "puerto montt", "iquique", "arica", "la serena",
             "rancagua", "talca", "chillan", "osorno", "calama", "copiapo",
             "punta arenas", "coquimbo", "los angeles", "valdivia"]
    is_otra = any(x in loc for x in otras)

    if is_remote:
        score += 15
    elif is_rm:
        score += 6
    elif is_otra:
        score -= 25

    # ── 4. Penalizaciones por requisitos fuera de alcance ──────────────────
    if re.search(r"\b([6-9]|1[0-9])\s*anos", ndesc):   # 6+ años de experiencia
        score -= 15
    if re.search(r"(titulo universitario|ingeniero civil|carrera profesional completa|"
                 r"licenciatura|magister|mba)", nall):
        score -= 12

    score = max(0, min(100, score))

    # Deduplicar tags
    seen, uniq = set(), []
    for t in tags:
        if t and t not in seen:
            seen.add(t)
            uniq.append(t)

    return score, uniq[:6]


def get_score_label(score: int) -> str:
    if score >= 70:
        return "excelente"
    elif score >= 45:
        return "bueno"
    elif score >= 20:
        return "regular"
    return "bajo"


def get_score_color(score: int) -> str:
    if score >= 70:
        return "#22c55e"
    elif score >= 45:
        return "#f59e0b"
    elif score >= 20:
        return "#f97316"
    return "#ef4444"
