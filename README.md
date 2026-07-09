# 🎯 Job Hunter CL — Carlos Cuevas

App web semi-automática para buscar y postular a trabajos en Chile.

## Stack
- **Backend**: FastAPI (Python)
- **Frontend**: HTML/CSS/JS vanilla
- **Deploy**: Render.com (gratis)
- **DB**: JSON en disco (simple, sin configuración)

## Portales soportados
- 🔵 Laborum Chile
- 🟢 Get on Board

## Funcionalidades
- 🔍 Scraping automático de ofertas
- 📊 Match score basado en tu perfil (0-100%)
- ✉️ Carta de presentación auto-generada y editable
- 🚀 Apertura del portal + registro de postulación con 1 clic
- 📋 Historial de postulaciones con seguimiento de estado
- 🔖 Guardar / descartar ofertas

## Correr localmente

```bash
pip install -r requirements.txt
uvicorn backend.main:app --reload
# Abre http://localhost:8000
```

## Deploy en Render

1. Sube este repo a GitHub
2. Ve a [render.com](https://render.com) → New → Web Service
3. Conecta tu repo
4. Render detecta el `render.yaml` automáticamente
5. Deploy ✅

## Estructura

```
job-hunter/
├── backend/
│   ├── main.py           # FastAPI app
│   ├── profile.py        # Perfil de Carlos (editar aquí)
│   ├── models.py         # Schemas Pydantic
│   ├── database.py       # DB JSON simple
│   ├── scorer.py         # Motor de match score
│   ├── routers/
│   │   ├── jobs.py
│   │   ├── applications.py
│   │   └── scraper.py
│   └── scrapers/
│       ├── laborum.py
│       └── getonboard.py
├── frontend/
│   ├── index.html
│   └── static/
│       ├── style.css
│       └── app.js
├── requirements.txt
├── render.yaml
└── Procfile
```
