"""
🚀 GARZON Pedidos Pro - FastAPI Microservice
=============================================
Microservicio que reemplaza la app Streamlit para integración con Appsmith.
Procesa PDFs con Gemini Vision, valida contra tarifa CSV/SQL, y crea pedidos en STEL.

Endpoints:
  POST /analizar-pedido    → Sube PDF/imagen → IA → cesta de productos
  POST /confirmar-pedido   → Cesta validada → Crea pedido en STEL Order
  POST /enviar-email       → Envía email con detalle del pedido
  GET  /buscar-precio/{ref} → Busca referencia en tarifa
  GET  /catalogo?q=...     → Busca en catálogo por texto libre
  GET  /health             → Health check con estado de servicios
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models import (
    AnalisisResponse, LineaCesta,
    ConfirmarPedidoRequest, ConfirmarPedidoResponse,
    EnviarEmailRequest, EnviarEmailResponse,
    BuscarPrecioResponse, BuscarCatalogoResponse,
    HealthResponse,
)
from app.services.tarifa import (
    cargar_tarifa, buscar_en_csv, buscar_por_texto,
    normalizar_referencia, limpiar_cantidad, get_tarifa_stats
)
from app.services.ia import analizar_documento, get_gemini_model
from app.services.stel import enviar_pedido
from app.services.email import enviar_email

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Pre-carga tarifa y modelo Gemini al arrancar."""
    logger.info("🚀 Iniciando GARZON Pedidos Pro API...")
    cargar_tarifa()
    stats = get_tarifa_stats()
    logger.info(f"📊 Tarifa: {stats['rows']} productos cargados")
    modelo = get_gemini_model()
    logger.info(f"🤖 Gemini: {modelo}")
    yield
    logger.info("👋 Apagando API...")


app = FastAPI(
    title="GARZON Pedidos Pro API",
    description="Procesamiento inteligente de pedidos Istobal/WashTec con IA",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS abierto para Appsmith
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# ENDPOINTS
# ==========================================


@app.post("/analizar-pedido", response_model=AnalisisResponse)
async def analizar_pedido(file: UploadFile = File(...)):
    """
    Sube un PDF o imagen de pedido → IA lo analiza → Retorna cesta con precios.
    Acepta: PDF, JPG, PNG.
    """
    # Leer archivo primero
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(400, "Archivo vacío")

    # Detectar MIME real (Appsmith puede enviar application/octet-stream)
    content_type = file.content_type or ""
    filename = (file.filename or "").lower()

    # Si el content_type no es específico, detectar por extensión o magic bytes
    if content_type in ("application/octet-stream", "", "multipart/form-data"):
        if filename.endswith(".pdf") or file_bytes[:5] == b"%PDF-":
            content_type = "application/pdf"
        elif filename.endswith((".jpg", ".jpeg")) or file_bytes[:3] == b"\xff\xd8\xff":
            content_type = "image/jpeg"
        elif filename.endswith(".png") or file_bytes[:4] == b"\x89PNG":
            content_type = "image/png"
        else:
            content_type = "application/pdf"  # Default a PDF
        logger.info(f"Content-type detectado: {content_type} (original: {file.content_type})")

    if content_type not in ["application/pdf", "image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(400, f"Tipo de archivo no soportado: {content_type}. Usa PDF, JPG o PNG.")

    # Mapear MIME
    mime_map = {
        "application/pdf": "application/pdf",
        "image/jpeg": "image/jpeg",
        "image/jpg": "image/jpeg",
        "image/png": "image/png",
    }
    mime = mime_map.get(content_type, "application/pdf")

    # Analizar con IA
    result = analizar_documento(file_bytes, mime)

    if result.get("tipo_documento") == "ERROR":
        raise HTTPException(502, f"Error de IA: {result.get('error', 'desconocido')}")

    # Construir cesta validando contra tarifa
    df = cargar_tarifa()
    cesta = []
    lineas_raw = result.get("lineas", [])

    for l in lineas_raw:
        p = buscar_en_csv(l.get("ref"), df)
        cesta.append(LineaCesta(
            ref=p["sku_canonical"] if p else normalizar_referencia(l.get("ref", "")),
            desc=p["description"] if p else l.get("desc", "NUEVO"),
            qty=limpiar_cantidad(l.get("qty", 1)),
            precio=float(p["price"]) if p else 0.0,
        ))

    return AnalisisResponse(
        tipo_documento=result.get("tipo_documento", "ISTOBAL"),
        titulo_lugar=result.get("titulo_lugar", ""),
        pedido_ref=result.get("pedido_ref", ""),
        direccion_envio=result.get("direccion_envio", ""),
        direcciones_candidatas=result.get("direcciones_candidatas", []),
        cesta=cesta,
        lineas_raw=lineas_raw,
    )


@app.post("/confirmar-pedido", response_model=ConfirmarPedidoResponse)
async def confirmar_pedido(request: Request):
    """Crea el pedido en STEL Order con la cesta confirmada.
    Acepta body como JSON object o como string JSON (Appsmith envía string)."""
    import json as json_mod
    raw_body = await request.body()
    body_str = raw_body.decode("utf-8").strip()
    logger.info(f"Confirmar pedido raw body: {body_str[:200]}")

    # Intentar parsear - puede ser JSON object o string JSON
    try:
        data = json_mod.loads(body_str)
        # Si el resultado es un string, es un JSON.stringify doble - parsear de nuevo
        if isinstance(data, str):
            data = json_mod.loads(data)
    except json_mod.JSONDecodeError as e:
        raise HTTPException(400, f"JSON inválido: {e}")

    # Validar con el modelo Pydantic
    try:
        req = ConfirmarPedidoRequest(**data)
    except Exception as e:
        raise HTTPException(400, f"Datos inválidos: {e}")

    cesta_dicts = [item.model_dump() for item in req.cesta]
    result = enviar_pedido(
        tipo=req.tipo_documento,
        cesta=cesta_dicts,
        pedido_ref=req.pedido_ref,
        direccion=req.direccion_envio,
        titulo=req.titulo_lugar,
        email_texto=req.email_texto,
    )
    return ConfirmarPedidoResponse(**result)


@app.post("/enviar-email", response_model=EnviarEmailResponse)
async def enviar_email_endpoint(req: EnviarEmailRequest):
    """Envía email SMTP con el detalle del pedido."""
    if not req.smtp_password:
        raise HTTPException(400, "Falta smtp_password (Google App Password)")

    result = enviar_email(
        destinatario=req.destinatario,
        copia_oculta=req.copia_oculta,
        asunto=req.asunto,
        cuerpo=req.cuerpo,
        smtp_password=req.smtp_password,
    )
    return EnviarEmailResponse(**result)


@app.get("/buscar-precio/{referencia}", response_model=BuscarPrecioResponse)
async def buscar_precio(referencia: str):
    """Busca una referencia en la tarifa de precios."""
    ref_norm = normalizar_referencia(referencia)
    p = buscar_en_csv(referencia)

    if p:
        return BuscarPrecioResponse(
            encontrado=True,
            ref=p["sku_canonical"],
            ref_normalizada=ref_norm,
            precio=p["price"],
            descripcion=p["description"],
        )
    return BuscarPrecioResponse(
        encontrado=False,
        ref=referencia,
        ref_normalizada=ref_norm,
    )


@app.get("/catalogo", response_model=BuscarCatalogoResponse)
async def buscar_catalogo(q: str = "", limit: int = 15):
    """Busca en el catálogo por texto libre (referencia o descripción)."""
    if not q or len(q) < 2:
        raise HTTPException(400, "Búsqueda requiere mínimo 2 caracteres")

    resultados = buscar_por_texto(q, limit)
    return BuscarCatalogoResponse(
        resultados=resultados,
        total=len(resultados),
    )


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check con estado de servicios."""
    stats = get_tarifa_stats()
    return HealthResponse(
        status="ok",
        version="1.0.0",
        price_source=settings.price_source,
        gemini_model=get_gemini_model(),
        csv_rows=stats["rows"],
    )
