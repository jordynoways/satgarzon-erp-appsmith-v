"""
Pydantic models para request/response de la API.
"""
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class TipoDocumento(str, Enum):
    WASHTEC = "WASHTEC"
    ISTOBAL = "ISTOBAL"
    DESCONOCIDO = "DESCONOCIDO"


class LineaCesta(BaseModel):
    """Una línea de producto en la cesta."""
    ref: str = Field(..., description="Referencia del producto (normalizada)")
    desc: str = Field("NUEVO", description="Descripción del producto")
    qty: int = Field(1, description="Cantidad (máx 100)")
    precio: float = Field(0.0, description="Precio de venta (tarifa)")


class AnalisisResponse(BaseModel):
    """Respuesta del endpoint /analizar-pedido."""
    tipo_documento: str = "ISTOBAL"
    titulo_lugar: str = ""
    pedido_ref: str = ""
    direccion_envio: str = ""
    direcciones_candidatas: list[str] = Field(default_factory=list)
    cesta: list[LineaCesta] = Field(default_factory=list)
    lineas_raw: list[dict] = Field(default_factory=list, description="Items raw de la IA")
    error: Optional[str] = None


class ConfirmarPedidoRequest(BaseModel):
    """Request para confirmar y crear pedido en STEL."""
    tipo_documento: str = "ISTOBAL"
    pedido_ref: str = ""
    titulo_lugar: str = ""
    direccion_envio: str = ""
    email_texto: str = ""
    cesta: list[LineaCesta]


class ConfirmarPedidoResponse(BaseModel):
    """Respuesta de la creación del pedido en STEL."""
    success: bool
    stel_response_code: Optional[int] = None
    message: str = ""


class EnviarEmailRequest(BaseModel):
    """Request para enviar email SMTP."""
    tipo_documento: str = "ISTOBAL"
    destinatario: str = ""
    copia_oculta: list[str] = Field(default_factory=list)
    asunto: str = ""
    cuerpo: str = ""
    smtp_password: str = ""


class EnviarEmailResponse(BaseModel):
    success: bool
    message: str = ""


class BuscarPrecioResponse(BaseModel):
    """Respuesta de búsqueda de precio por referencia."""
    encontrado: bool
    ref: str = ""
    ref_normalizada: str = ""
    precio: Optional[float] = None
    descripcion: Optional[str] = None


class BuscarCatalogoResponse(BaseModel):
    """Respuesta de búsqueda en catálogo por texto."""
    resultados: list[dict] = Field(default_factory=list)
    total: int = 0


class HealthResponse(BaseModel):
    """Respuesta del health check."""
    status: str = "ok"
    version: str = "1.0.0"
    price_source: str = "csv"
    gemini_model: str = ""
    csv_rows: int = 0
