"""
Servicio STEL Order: gestión de productos y pedidos.
Portado desde: container garzon_pedidos → app.py (asegurar_producto_stel, enviar_a_stel)
"""
import re
import logging
from typing import Optional

import requests

from app.config import settings

logger = logging.getLogger(__name__)

HEADERS = {
    "Content-Type": "application/json",
    "APIKEY": settings.stel_api_key
}


def limpiar_para_stel(texto: str) -> str:
    """Elimina emojis y caracteres especiales para STEL Order."""
    return re.sub(r'[^\w\s,.\-:\n@()áéíóúÁÉÍÓÚñÑ€/]', '', texto).strip()


def asegurar_producto(ref: str, desc: str, pvp: float) -> Optional[int]:
    """
    Busca producto en STEL por referencia.
    Si existe, actualiza precio y devuelve ID.
    Si no existe, lo crea y devuelve ID.
    """
    if not ref:
        return None

    # 1) Buscar existente
    try:
        url = f"{settings.stel_base_url}/products?reference={ref}"
        r = requests.get(url, headers=HEADERS)
        if r.status_code == 200:
            data = r.json()
            items = data if isinstance(data, list) else data.get("data", [])
            if items:
                for prod in items:
                    if str(prod.get("reference", "")).upper() == ref.upper():
                        prod_id = prod.get("id")
                        # Actualizar precio
                        try:
                            p_compra = round(float(pvp) * 0.66, 2)
                            requests.put(
                                f"{settings.stel_base_url}/products/{prod_id}",
                                json={"sales-price": float(pvp), "purchase-price": p_compra},
                                headers=HEADERS
                            )
                        except Exception:
                            pass
                        return prod_id
    except Exception as e:
        logger.warning(f"Error buscando producto {ref}: {e}")

    # 2) Crear nuevo
    p_compra = round(float(pvp) * 0.66, 2)
    payload = {
        "serial-number-id": -2,  # -2 = referencia MANUAL
        "reference": ref,
        "name": desc[:250] if desc else f"Producto {ref}",
        "sales-price": float(pvp),
        "purchase-price": p_compra,
        "tax-rate": 21,
        "product-category-id": int(settings.istobal_category_id),
    }

    try:
        r = requests.post(f"{settings.stel_base_url}/products", json=payload, headers=HEADERS)
        if r.status_code in [200, 201]:
            body = r.json()
            if isinstance(body, list) and body:
                return body[0].get("id")
            return body.get("id")
        else:
            logger.error(f"Error creando producto {ref}: ({r.status_code}) {r.text}")
            return None
    except Exception as e:
        logger.error(f"Excepción creando producto {ref}: {e}")
        return None


def enviar_pedido(
    tipo: str,
    cesta: list[dict],
    pedido_ref: str,
    direccion: str,
    titulo: str,
    email_texto: str
) -> dict:
    """
    Crea pedido en STEL Order.
    tipo ISTOBAL → workOrders (con 27% dto)
    tipo WASHTEC → salesOrders (con 10% dto + portes)
    """
    cliente_id = settings.istobal_client_id if tipo == "ISTOBAL" else settings.washtec_client_id
    endpoint = "workOrders" if tipo == "ISTOBAL" else "salesOrders"
    dto = settings.istobal_discount if tipo == "ISTOBAL" else settings.washtec_discount

    items_api = []
    for l in cesta:
        sid = asegurar_producto(l['ref'], l['desc'], l['precio'])
        if sid:
            items_api.append({
                "line-type": "ITEM",
                "item-id": int(sid),
                "units": float(l['qty']),
                "item-base-price": float(l['precio']),
                "discount-percentage": dto
            })

    # Portes para WashTec
    if tipo == "WASHTEC":
        items_api.append({
            "line-type": "ITEM",
            "item-id": settings.portes_id,
            "units": 1.0,
            "item-base-price": settings.portes_price,
            "discount-percentage": 0
        })

    texto_limpio = limpiar_para_stel(email_texto)
    payload = {
        "account-id": int(cliente_id),
        "title": f"{tipo} - {pedido_ref} - {titulo}",
        "lines": items_api,
        "private-comments": texto_limpio,
        "comments": f"PEDIDO: {pedido_ref}\nENTREGA: {direccion}"
    }

    try:
        r = requests.post(
            f"{settings.stel_base_url}/{endpoint}",
            json=payload,
            headers=HEADERS
        )
        logger.info(f"STEL {endpoint}: {r.status_code}")
        return {
            "success": r.status_code in [200, 201],
            "stel_response_code": r.status_code,
            "message": f"Pedido creado en {endpoint}" if r.status_code in [200, 201] else f"Error: {r.text[:200]}"
        }
    except Exception as e:
        return {"success": False, "stel_response_code": None, "message": str(e)}
