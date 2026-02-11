"""
Servicio de IA: analiza PDFs con Gemini Vision.
Portado desde: container garzon_pedidos → app.py (consultar_gemini_cache, extraer_pdf_pro)
"""
import json
import io
import logging
import re
from typing import Optional

import google.generativeai as genai
import pdfplumber

from app.config import settings

logger = logging.getLogger(__name__)

# Modelo de Gemini detectado al arrancar
_gemini_model: Optional[str] = None


def _detectar_modelo() -> str:
    """Detecta el mejor modelo Gemini disponible. Prioriza Flash."""
    global _gemini_model
    if _gemini_model:
        return _gemini_model

    try:
        genai.configure(api_key=settings.gemini_api_key)
        modelos = []
        for m in genai.list_models():
            if "generateContent" in m.supported_generation_methods:
                modelos.append(m.name)

        # Preferir Flash (estable, no experimental)
        for m in modelos:
            if "flash" in m and "exp" not in m:
                _gemini_model = m
                logger.info(f"Gemini model detectado: {m}")
                return m

        if modelos:
            _gemini_model = modelos[0]
            return modelos[0]
    except Exception as e:
        logger.warning(f"Error detectando modelo Gemini: {e}")

    _gemini_model = "models/gemini-1.5-flash"
    return _gemini_model


def get_gemini_model() -> str:
    """Retorna el nombre del modelo Gemini activo."""
    return _detectar_modelo()


def extraer_texto_pdf(file_bytes: bytes) -> str:
    """Extrae texto de un PDF usando pdfplumber (mejor que pypdf para tablas)."""
    texto_completo = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        paginas = pdf.pages[:8]  # Límite seguro de 8 páginas
        for page in paginas:
            texto_pagina = [page.extract_text(layout=True) or ""]
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    if row and any(row):
                        texto_pagina.append(" | ".join([str(c).strip() for c in row if c]))
            texto_completo.append("\n".join(texto_pagina))
    return "\n".join(texto_completo)


def analizar_documento(file_bytes: bytes, mime_type: str = "application/pdf") -> dict:
    """
    Analiza un documento (PDF o imagen) con Gemini Vision.
    Envía el archivo como binary para análisis visual directo.
    Retorna dict con tipo_documento, titulo_lugar, pedido_ref, direcciones, items.
    """
    modelo_nombre = _detectar_modelo()
    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel(modelo_nombre)

    prompt = """Analiza este documento visualmente. Extrae la siguiente información:

1. **titulo_lugar**: El NOMBRE DEL CLIENTE, EMPRESA o ESTACIÓN DE SERVICIO a quien va dirigido el pedido. Busca nombres como "ESTACION SERVICIO...", "E.S. ...", "GASOLINERA...", o el nombre comercial del cliente.

2. **pedido_ref**: Número de referencia o pedido (ej: "1496", "ESOF00081044", etc.)

3. **direccion_envio**: Dirección COMPLETA de entrega (calle, número, código postal, ciudad)

4. **direcciones_candidatas**: Lista con TODAS las direcciones que encuentres en el documento

5. **lineas**: Lista de materiales con referencia y cantidad

IMPORTANTE: 
- IGNORA conceptos de Mano de Obra, Horas de trabajo, Reparación, Desplazamiento, Kilometraje o Portes.
- SOLO extrae MATERIALES, PIEZAS y PRODUCTOS tangibles.

Salida JSON: { "titulo_lugar": "NOMBRE CLIENTE/ESTACION", "pedido_ref": "...", "direccion_envio": "...", "direcciones_candidatas": ["dir1", "dir2"], "lineas": [ {"ref": "...", "qty": 1, "desc": "..."} ] }
"""

    content = [prompt, {"mime_type": mime_type, "data": file_bytes}]

    # Reintentar hasta 3 veces
    errores = []
    for intento in range(3):
        try:
            response = model.generate_content(
                content,
                generation_config={"response_mime_type": "application/json"},
            )
            data = json.loads(response.text)

            # Post-proceso: detectar tipo por texto
            if "direcciones_candidatas" in data and data["direcciones_candidatas"]:
                data["direccion_envio"] = data["direcciones_candidatas"][0]

            # Determinar fabricante por contenido del PDF
            texto_ref = json.dumps(data).upper()
            if "WASHTEC" in texto_ref:
                data["tipo_documento"] = "WASHTEC"
            elif "ISTOBAL" in texto_ref:
                data["tipo_documento"] = "ISTOBAL"
            else:
                # Intentar leer texto del PDF para detectar
                try:
                    texto_pdf = extraer_texto_pdf(file_bytes).upper()
                    if "WASHTEC" in texto_pdf:
                        data["tipo_documento"] = "WASHTEC"
                    elif "ISTOBAL" in texto_pdf:
                        data["tipo_documento"] = "ISTOBAL"
                    else:
                        data["tipo_documento"] = "ISTOBAL"  # default
                except Exception:
                    data["tipo_documento"] = "ISTOBAL"

            logger.info(f"Documento analizado: {data.get('tipo_documento')} - {len(data.get('lineas', []))} items")
            return data

        except Exception as e:
            errores.append(str(e))
            logger.warning(f"Intento {intento+1}/3 fallido: {e}")
            import time
            time.sleep(2)

    return {
        "tipo_documento": "ERROR",
        "titulo_lugar": "",
        "pedido_ref": "",
        "direccion_envio": "",
        "direcciones_candidatas": [],
        "lineas": [],
        "error": errores[-1] if errores else "Error desconocido"
    }
