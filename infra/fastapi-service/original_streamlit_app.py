# -*- coding: latin-1 -*-
import streamlit as st
import pandas as pd
import requests
import google.generativeai as genai
import json
import os
import time
from pypdf import PdfReader
import re

# ==========================================
# CONFIGURACION API
# ==========================================
STEL_API_KEY = "0RjnBmi37UswuylVpjIyi7I6gvX54i2ShBnJLsC0"
STEL_URL = "https://app.stelorder.com/app"

# CLAVE DE GEMINI
GEMINI_KEY = "AIzaSyBqTTFLRST2xzti0VpWM2HJTO2wg08ibSU"

# WEBHOOK PARA SUBIR PDF A DRIVE (Opcional)
MAKE_DRIVE_WEBHOOK = "https://hook.eu1.make.com/nox3zd6q88ldhcefn7mu26qpxnnurssj"

# ==========================================
# CONSTANTES ESPECIFICAS
# ==========================================

# WASHTEC (pedido de venta)
PORTES_REF = "PPW"
PORTES_ID_FIJO = 39320611
PORTES_NAME = "PORTES PEDIDOS WASHTEC"
PORTES_PRICE_VENTA = 16.50
DESCUENTO_WASHTEC = 10.0  # 10% para Washtec
CLIENTE_WASHTEC_ID = 111

# ISTOBAL (pedido de trabajo)
CLIENTE_ISTOBAL_ID = 12482218
DESCUENTO_ISTOBAL = 27.0  # 27% para Istobal

# Familia de productos ISTOBAL (para todos los productos nuevos)
ISTOBAL_PRODUCT_CATEGORY_ID = 116398

LOGO_PATH = "logo_garzon.png"

st.set_page_config(
    page_title="GARZON PEDIDOS ISTOBAL / WASHTEC",
    page_icon="",
    layout="wide"
)

# ==========================================
# ESTADO INICIAL DE SESION
# ==========================================
if "modelo_elegido" not in st.session_state:
    st.session_state["modelo_elegido"] = "models/gemini-1.5-flash"

# Evita duplicar pedidos
if "pedido_confirmado" not in st.session_state:
    st.session_state["pedido_confirmado"] = False

if "texto_origen_pedido" not in st.session_state:
    st.session_state["texto_origen_pedido"] = ""

# ==========================================
# ESTILO APPLE MINIMAL
# ==========================================
st.markdown(
    """
<style>
.main {
    background-color: #f5f5f7;
}
.block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
}
.main-title {
    font-size: 34px;
    font-weight: 600;
    letter-spacing: 0.02em;
    color: #111;
}
.subtitle {
    font-size: 14px;
    color: #6e6e73;
    margin-top: -6px;
}
.card-apple {
    border-radius: 16px;
    padding: 20px 24px;
    background: rgba(255,255,255,0.92);
    border: 1px solid rgba(0,0,0,0.06);
    box-shadow: 0 14px 32px rgba(0,0,0,0.07);
    margin-bottom: 20px;
}
.card-apple-title {
    font-size: 20px;
    font-weight: 600;
    color: #000;
}
.card-apple-body {
    font-size: 15px;
    color: #3a3a3c;
}
.stButton>button {
    border-radius: 999px !important;
    padding: 0.55rem 1.6rem !important;
    font-weight: 600 !important;
    background-color: #111 !important;
    color: white !important;
}
</style>
""",
    unsafe_allow_html=True,
)

# ==========================================
# CABECERA: LOGO + TITULO
# ==========================================
col_logo, col_titulo = st.columns([1, 4])

with col_logo:
    try:
        st.image(LOGO_PATH, use_container_width=True)
    except Exception as e:
        st.write("No se pudo cargar el logo:", e)

with col_titulo:
    st.markdown(
        '<div class="main-title">GARZON PEDIDOS ISTOBAL / WASHTEC</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="subtitle">Servicio técnico de Autolavados S.L · Gestión automatizada de pedidos ISTOBAL / WashTec</p>',
        unsafe_allow_html=True,
    )

# ==========================================
# DETECCION MODELO GEMINI
# ==========================================
try:
    genai.configure(api_key=GEMINI_KEY)
    lista_modelos = []
    try:
        for m in genai.list_models():
            if "generateContent" in m.supported_generation_methods:
                lista_modelos.append(m.name)
    except Exception:
        pass

    modelo_final = None
    for m in lista_modelos:
        if "flash" in m and "exp" not in m:
            modelo_final = m
            break
    if not modelo_final and lista_modelos:
        modelo_final = lista_modelos[0]

    if modelo_final:
        st.session_state["modelo_elegido"] = modelo_final
        st.sidebar.success(f"Sistema listo: {modelo_final}")
    else:
        st.sidebar.info("Modo por defecto (Flash)")

except Exception as e:
    st.sidebar.error(f"Error Conexion Google: {e}")

# ==========================================
# FUNCIONES AUXILIARES
# ==========================================

def normalizar_referencia(texto_sucio: str) -> str:
    if not texto_sucio:
        return ""
    s = str(texto_sucio).strip().upper()
    tokens = re.split(r"[^A-Z0-9]+", s)
    codigo = ""
    for t in tokens:
        if len(t) > 2 and any(c.isdigit() for c in t):
            codigo = t
            break
    if not codigo:
        return ""
    codigo = codigo.replace("-", "").strip()
    if codigo.startswith("E") and len(codigo) > 2:
        codigo = codigo[1:]
    return codigo


@st.cache_data
def cargar_tarifa():
    archivo = "prices_clean.csv"
    if os.path.exists(archivo):
        try:
            return pd.read_csv(
                archivo,
                dtype={"sku_canonical": str, "price": float},
                encoding="utf-8",
            )
        except Exception:
            return pd.read_csv(
                archivo,
                dtype={"sku_canonical": str, "price": float},
                encoding="latin-1",
            )
    return None


def leer_pdf(uploaded_file) -> str:
    try:
        reader = PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            pag_text = page.extract_text()
            if pag_text:
                text += pag_text + "\n"
        return text
    except Exception as e:
        return f"Error leyendo PDF: {e}"


def validar_con_tarifa(lineas, df):
    if df is None or df.empty:
        return [], ["Tarifa no cargada"]

    logs = []
    lineas_ok = []

    def buscar_codigo(codigo_norm):
        if not codigo_norm:
            return pd.DataFrame()
        m = df[df["sku_canonical"].str.upper() == codigo_norm.upper()]
        if not m.empty:
            return m
        variantes = set()
        if codigo_norm[-1] == "1":
            variantes.add(codigo_norm[:-1] + "I")
        elif codigo_norm[-1] == "I":
            variantes.add(codigo_norm[:-1] + "1")
        for v in variantes:
            m2 = df[df["sku_canonical"].str.upper() == v.upper()]
            if not m2.empty:
                return m2
        return pd.DataFrame()

    for l in lineas:
        ref_original = str(l.get("ref", "")).strip()
        if not ref_original:
            logs.append("Línea sin referencia, descartada.")
            continue
        ref_normalizada = normalizar_referencia(ref_original)
        match = buscar_codigo(ref_normalizada)
        if match.empty:
            posibles_codigos = re.findall(r"\((\w+)\)", ref_original)
            for codigo in posibles_codigos:
                cod_norm = normalizar_referencia(codigo)
                sub_match = buscar_codigo(cod_norm)
                if not sub_match.empty:
                    match = sub_match
                    ref_normalizada = cod_norm
                    break
        if not match.empty:
            info = match.iloc[0]
            ref_tarifa = str(info["sku_canonical"]).strip().upper()
            precio_tarifa = float(info["price"])
            l["ref"] = ref_tarifa
            l["precio_venta"] = precio_tarifa
            l["descripcion_oficial"] = info.get("description", l.get("desc", "Sin Descripción"))
            l["precio_compra"] = round(precio_tarifa * 0.66, 2)
            logs.append(f"Ref {ref_tarifa}: OK")
            lineas_ok.append(l)
        else:
            logs.append(f"ELIMINADA: '{ref_original}' no encontrada en tarifa.")

    return lineas_ok, logs


def detectar_tipo_doc(texto: str) -> str:
    if not texto:
        return "DESCONOCIDO"
    t = texto.upper()
    if "ISTOBAL" in t:
        return "ISTOBAL"
    if "WASHTEC" in t:
        return "WASHTEC"
    return "DESCONOCIDO"


def gestionar_producto_stel(ref, desc, precio_venta, precio_compra):
    if not ref:
        return None, "Referencia vacía"
    headers = {"Content-Type": "application/json", "APIKEY": STEL_API_KEY}
    try:
        url = f"{STEL_URL}/products?reference={ref}"
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            data = r.json()
            items = data if isinstance(data, list) else data.get("data", [])
            if items:
                for prod in items:
                    if str(prod.get("reference", "")).upper() == ref.upper():
                        return prod.get("id"), "Existía"
    except Exception as e:
        return None, f"Error Busqueda: {e}"
    payload = {
        "serial-number-id": -2,
        "reference": ref,
        "name": desc[:250] if desc else f"Producto {ref}",
        "sales-price": float(precio_venta or 0.0),
        "purchase-price": float(precio_compra or 0.0),
        "tax-rate": 21,
        "product-category-id": int(ISTOBAL_PRODUCT_CATEGORY_ID),
    }
    try:
        r = requests.post(f"{STEL_URL}/products", json=payload, headers=headers)
        if r.status_code in [200, 201]:
            body = r.json()
            if isinstance(body, list) and body:
                return body[0].get("id"), "Creado Nuevo"
            return body.get("id"), "Creado Nuevo"
        else:
            return None, f"Error Creacion ({r.status_code}): {r.text}"
    except Exception as e:
        return None, f"Excepcion Creacion: {e}"


def crear_pedido_venta(cliente_id, lineas, ref_pedido, portes_id,
                        direccion_envio, email_borrador):
    headers = {"Content-Type": "application/json", "APIKEY": STEL_API_KEY}
    payload = {
        "account-id": int(cliente_id),
        "reference": None,
        "title": str(ref_pedido),
        "comments": f"DIRECCION DE ENTREGA:\n{direccion_envio}",
        "private-comments": f"--- EMAIL ISTOBAL/WASHTEC ---\n\n{email_borrador}",
        "lines": [],
    }
    for l in lineas:
        p_venta = l.get("precio_venta", 0.0)
        payload["lines"].append({
            "line-type": "ITEM",
            "item-id": int(l.get("stel_id", 0)),
            "units": float(l.get("qty", 1)),
            "item-base-price": float(p_venta),
            "discount-percentage": float(DESCUENTO_WASHTEC),
        })
    if portes_id:
        payload["lines"].append({
            "line-type": "ITEM",
            "item-id": int(portes_id),
            "units": 1.0,
            "item-base-price": float(PORTES_PRICE_VENTA),
            "discount-percentage": float(DESCUENTO_WASHTEC),
        })
    return requests.post(f"{STEL_URL}/salesOrders", json=payload, headers=headers)


def crear_pedido_trabajo(cliente_id, lineas, ref_pedido,
                          direccion_envio, email_borrador):
    headers = {"Content-Type": "application/json", "APIKEY": STEL_API_KEY}
    payload = {
        "account-id": int(cliente_id),
        "reference": None,
        "title": str(ref_pedido),
        "comments": f"DIRECCION DE TRABAJO:\n{direccion_envio}",
        "private-comments": f"--- EMAIL ISTOBAL ---\n\n{email_borrador}",
        "lines": [],
    }
    for l in lineas:
        p_venta = l.get("precio_venta", 0.0)
        payload["lines"].append({
            "line-type": "ITEM",
            "item-id": int(l.get("stel_id", 0)),
            "units": float(l.get("qty", 1)),
            "item-base-price": float(p_venta),
            "discount-percentage": float(DESCUENTO_ISTOBAL),
        })
    return requests.post(f"{STEL_URL}/workOrders", json=payload, headers=headers)


def enviar_pdf_a_make(file_bytes, filename, webhook_url, extra_data=None):
    try:
        files = {"file": (filename, file_bytes, "application/pdf")}
        data = extra_data or {}
        r = requests.post(webhook_url, files=files, data=data, timeout=30)
        return (r.status_code == 200, r.text)
    except Exception as e:
        return (False, str(e))
