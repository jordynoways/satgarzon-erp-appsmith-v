"""
Servicio de Tarifas: carga y busca precios desde CSV o SQL Server.
Portado desde: container garzon_pedidos → app.py (funciones cargar_tarifa, buscar_en_csv, buscar_por_texto)
"""
import pandas as pd
import re
import os
import logging
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)

# Cache global del DataFrame de precios
_df_tarifa: Optional[pd.DataFrame] = None


def normalizar_referencia(texto_sucio: str) -> str:
    """Normaliza una referencia de producto eliminando separadores y prefijos."""
    if not texto_sucio:
        return ""
    s = str(texto_sucio).strip().upper().replace(" ", "")
    tokens = re.split(r"[^A-Z0-9]+", s)
    codigo = next(
        (t for t in tokens if len(t) > 2 and any(c.isdigit() for c in t)),
        s.replace("-", "")
    )
    if codigo.startswith("E") and len(codigo) > 2:
        return codigo[1:]
    return codigo


def limpiar_cantidad(qty_ia) -> int:
    """Limpia la cantidad extraída por la IA. Máximo 100."""
    try:
        q = str(qty_ia).strip().replace(' ', '')
        if ',' in q:
            q = q.split(',')[0]
        if '.' in q:
            q = q.split('.')[0]
        valor = int(re.sub(r'[^0-9]', '', q))
        return valor if valor <= 100 else 1
    except Exception:
        return 1


def cargar_tarifa() -> Optional[pd.DataFrame]:
    """Carga la tarifa de precios desde CSV o SQL Server."""
    global _df_tarifa

    if _df_tarifa is not None:
        return _df_tarifa

    if settings.price_source == "csv":
        path = settings.csv_prices_path
        if os.path.exists(path):
            try:
                _df_tarifa = pd.read_csv(
                    path,
                    dtype={"sku_canonical": str, "price": float}
                )
                logger.info(f"Tarifa CSV cargada: {len(_df_tarifa)} productos desde {path}")
                return _df_tarifa
            except Exception as e:
                logger.error(f"Error cargando CSV: {e}")
                return None
        else:
            logger.warning(f"Archivo CSV no encontrado: {path}")
            return None

    # TODO: Implementar cuando iQuote tenga datos
    elif settings.price_source == "sqlserver":
        logger.warning("SQL Server como fuente de precios aún no implementado")
        # Futuro: conectar a SQL Server IQUOTE y cargar tabla de precios
        # import pymssql
        # conn = pymssql.connect(
        #     server=f"{settings.sqlserver_host}\\{settings.sqlserver_instance}",
        #     port=settings.sqlserver_port,
        #     database=settings.sqlserver_db,
        # )
        # _df_tarifa = pd.read_sql("SELECT * FROM [tabla_precios]", conn)
        return None

    return None


def buscar_en_csv(ref_sucia: str, df: Optional[pd.DataFrame] = None) -> Optional[dict]:
    """
    Busca una referencia en la tarifa. Prueba variantes I/1.
    Retorna dict con sku_canonical, description, price o None.
    """
    if df is None:
        df = cargar_tarifa()
    if df is None or not ref_sucia:
        return None

    ref_norm = normalizar_referencia(ref_sucia)

    # Búsqueda exacta
    res = df[df["sku_canonical"].str.upper() == ref_norm.upper()]

    # Variantes: 1 ↔ I (confusión común en OCR)
    if res.empty and ref_norm.endswith("1"):
        res = df[df["sku_canonical"].str.upper() == ref_norm[:-1] + "I"]
    if res.empty and ref_norm.endswith("I"):
        res = df[df["sku_canonical"].str.upper() == ref_norm[:-1] + "1"]

    if not res.empty:
        row = res.iloc[0]
        return {
            "sku_canonical": row["sku_canonical"],
            "description": row.get("description", ""),
            "price": float(row["price"])
        }
    return None


def buscar_por_texto(query: str, limit: int = 15) -> list[dict]:
    """Busca en el catálogo por texto libre (ref o descripción)."""
    df = cargar_tarifa()
    if df is None or not query:
        return []

    q = query.upper()
    mask = df.apply(
        lambda x: q in str(x['sku_canonical']).upper() or q in str(x.get('description', '')).upper(),
        axis=1
    )
    results = df[mask].head(limit)
    return results.to_dict('records')


def get_tarifa_stats() -> dict:
    """Retorna estadísticas de la tarifa cargada."""
    df = cargar_tarifa()
    if df is None:
        return {"loaded": False, "rows": 0}
    return {"loaded": True, "rows": len(df)}
