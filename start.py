"""
Entry point para Render / producción.
Agrega backend/ al path para que los imports funcionen correctamente.
"""
import sys
import os

# Asegurar que backend/ esté en el path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

# Importar la app DESPUÉS de configurar el path
from backend.main import app  # noqa: F401 — requerido por uvicorn
