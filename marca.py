"""Datos de la marca en un solo sitio (colores de apruebatcae.com, web, cuenta y cifra de preguntas).

Los colores salen del propio CSS de la web app (index.html): --teal #1a9e8f, --teal-dark #0f7a6d, --teal-light #e6f7f5,
--text #1f2937, --muted #6b7280, --bg #f7f9fa, --border #e2e8f0, --green #2e9e5b, --red #d64545 y el dorado #e8c93d.
La cifra de preguntas que se anuncia se cambia con la variable de GitHub APP_PREGUNTAS (p. ej. "10.000").
"""
import os

WEB = os.environ.get("APP_WEB", "apruebatcae.com")
HANDLE = os.environ.get("IG_HANDLE", "@apruebatcae")
PREGUNTAS = os.environ.get("APP_PREGUNTAS", "10.000")          # se anuncia como "más de X preguntas"
PREGUNTAS_FRASE = f"más de {PREGUNTAS} preguntas"


def preguntas_num():
    try:
        return int(PREGUNTAS.replace(".", "").replace(" ", ""))
    except Exception:
        return 0
