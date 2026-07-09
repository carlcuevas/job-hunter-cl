# Perfil profesional de Carlos Cuevas — usado para scoring y filtrado de ofertas

PROFILE = {
    "name": "Carlos Rodrigo Cuevas Nuñez",
    "email": "rodrigo14nunez@gmail.com",
    "phone": "+56 9 2254 6892",
    "location": "Santiago, Chile",
    "linkedin": "linkedin.com/in/carloscuevas-43342b268",
    "modality": ["híbrido", "presencial", "remoto"],

    "target_roles": [
        "soporte TI",
        "help desk",
        "soporte técnico",
        "técnico TI",
        "infraestructura TI",
        "atención al cliente",
        "customer success",
        "customer service",
        "ejecutivo de cuentas",
        "asistente RRHH",
        "administración de personal",
        "barista",
        "encargado de cafetería",
    ],

    "keywords_high": [
        "soporte TI", "help desk", "soporte técnico", "AWS", "SAP", "infraestructura",
        "cloud", "redes", "hardware", "atención al cliente", "customer success",
        "customer service", "RRHH", "recursos humanos", "ERP", "excel", "modelado",
        "base de datos", "barista", "cafetería", "liderazgo", "capacitación", "onboarding",
    ],

    "keywords_medium": [
        "técnico", "administrativo", "gestión", "KPIs", "freelance", "emprendimiento",
        "operaciones", "ventas", "backoffice", "coordinador", "encargado",
    ],

    "keywords_low": [
        "digitación", "recepción", "digitalizacion", "archivos", "bodega",
    ],

    "experience_years": 3,
    "education": "Ingeniería en Infraestructura Tecnológica (en curso) — Duoc UC",
    "certifications": ["AWS Cloud Practitioner (en progreso)", "Técnico Administración RRHH — CFT Estatal RM"],
    "languages": {"español": "nativo", "inglés": "técnico"},
    "availability": "inmediata",
    "contract_type": "full-time",

    "cover_letter_template": """Estimado/a equipo de selección,

Mi nombre es Carlos Cuevas, tengo disponibilidad inmediata y estoy muy interesado en el cargo de {job_title} en {company}.

Cuento con más de 3 años de experiencia en atención al cliente y gestión de equipos, complementado con formación activa en infraestructura cloud y soporte TI. Durante mi paso por Arcos Dorados Chile (McDonald's — McCafé) fui Entrenador Barista y Gerente de Turno, liderando equipos y manteniendo KPIs de satisfacción del cliente. Actualmente curso Ingeniería en Infraestructura Tecnológica en Duoc UC y tengo en progreso mi certificación AWS Cloud Practitioner.

Adicionalmente, manejo SAP ERP, Excel Avanzado, configuración de redes y hardware, y tengo experiencia práctica en procesos de RRHH. Soy emprendedor tecnológico (RespawnFix), lo que demuestra mi capacidad de autogestión y orientación a resultados.

Estoy disponible para una entrevista cuando estimen conveniente.

Saludos cordiales,
Carlos Cuevas
+56 9 2254 6892 | rodrigo14nunez@gmail.com
""",

    # ── Campos específicos de Get on Board ──────────────────────────

    # Plantillas base por área — se selecciona según keywords del trabajo
    "gob_experience_templates": {

        "ti": """Tengo más de 3 años de experiencia combinada en soporte TI, atención al cliente y gestión de equipos. Actualmente dirijo RespawnFix, emprendimiento de servicios informáticos donde realizo diagnóstico, reparación de hardware/software y asesoría técnica a clientes particulares.

Durante mi paso por Arcos Dorados Chile (McDonald's) ascendí a Gerente de Turno, liderando equipos de hasta 10 personas, controlando KPIs operacionales y gestionando apertura y cierre de local. Realicé práctica profesional como Asistente de RRHH manejando SAP ERP en procesos de remuneraciones y asistencia.

Manejo: AWS EC2/S3/IAM, SAP ERP, hardware PC (armado y mantención), redes básicas, modelado de base de datos, Excel avanzado y soporte técnico nivel 1/2. Tengo disponibilidad inmediata y full time.""",

        "atencion_cliente": """Cuento con más de 3 años de experiencia directa en atención al cliente en entornos de alto volumen. En Arcos Dorados Chile (McDonald's — McCafé) comencé como Barista, llegué a Entrenador certificando a nuevos colaboradores, y ascendí a Gerente de Turno gestionando equipo, KPIs de satisfacción y operación completa del turno.

Actualmente trabajo en Shukran Coffee (cafetería de especialidad) con foco en experiencia personalizada y educación sobre café. Soy emprendedor tecnológico (RespawnFix), lo que refuerza mis habilidades de autogestión, trato con clientes y resolución de problemas.

Tengo disponibilidad inmediata, full time, y me manejo bien bajo presión manteniendo calidad de servicio.""",

        "rrhh": """Cuento con título de Técnico en Administración de RRHH (CFT Estatal RM, 2024) y experiencia práctica en el área a través de mi práctica profesional en Arcos Dorados Chile (McDonald's), donde utilicé SAP ERP para gestión de asistencia, vacaciones y procesos de remuneraciones en entorno corporativo.

Complementariamente, como Gerente de Turno lideré equipos, gestioné conflictos y participé en procesos de onboarding y capacitación de nuevos colaboradores. Manejo Excel avanzado, tengo buen trato con personas y disponibilidad inmediata.""",

        "default": """Soy un profesional versátil con más de 3 años de experiencia en atención al cliente, liderazgo de equipos y soporte TI. Formé como Entrenador Barista y Gerente de Turno en Arcos Dorados Chile (McDonald's — McCafé), donde gestioné equipos, KPIs y operación de turno completa.

Actualmente curso Ingeniería en Infraestructura Tecnológica en Duoc UC y dirijo RespawnFix, mi emprendimiento de servicios informáticos. Manejo SAP ERP, AWS (en certificación), Excel avanzado, hardware y redes.

Soy proactivo, me adapto rápido y tengo disponibilidad inmediata full time.""",
    },

    "gob_education_template": """Actualmente curso Ingeniería en Infraestructura Tecnológica en Duoc UC (Santiago, desde 2025), carrera orientada a cloud computing, redes, infraestructura y administración de sistemas.

Soy Técnico en Administración de RRHH, titulado en CFT Estatal RM (2024), con formación en gestión de personas, legislación laboral y herramientas administrativas.

Además, tengo en progreso la certificación AWS Cloud Practitioner (Amazon Web Services), que valida conocimientos en servicios cloud: EC2, S3, IAM y arquitectura básica en la nube.

Inglés técnico (lectura y comprensión de documentación).""",
}
