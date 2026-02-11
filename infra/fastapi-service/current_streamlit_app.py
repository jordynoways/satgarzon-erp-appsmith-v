# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import requests
import json
import os
import re
import pdfplumber
import pdfplumber
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import hashlib
import threading
from datetime import datetime
from pathlib import Path


# ==========================================
# ⚙️ CONFIGURACIÓN RYZEN 9 AI
# ==========================================
# ==========================================
# ⚙️ CONFIGURACIÓN RYZEN 9 AI
# ==========================================
OLLAMA_URL = "http://192.168.1.226:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:3b"  # Balance entre velocidad y precisión

 

STEL_API_KEY = "0RjnBmi37UswuylVpjIyi7I6gvX54i2ShBnJLsC0"
STEL_URL = "https://app.stelorder.com/app"

CLIENTE_WASHTEC_ID = 111
CLIENTE_ISTOBAL_ID = 12482218
ISTOBAL_PRODUCT_CATEGORY_ID = 116398
PORTES_ID_FIJO = 39320611
PORTES_PRICE_VENTA = 15.00
LOGO_PATH = "logo_garzon.png"

# Directorio para almacenar trabajos persistentes
JOBS_DIR = Path(".jobs_cache")
JOBS_DIR.mkdir(exist_ok=True)


st.set_page_config(
    page_title="GARZON AI PRO", 
    layout="wide", 
    page_icon="🤖",
    initial_sidebar_state="collapsed"  # Mejora velocidad inicial
)


# --- CSS ESTILO APPLE PREMIUM ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    :root {
        --primary: #007aff;
        --bg-color: #f5f5f7;
        --card-bg: #ffffff;
        --text-primary: #1d1d1f;
        --text-secondary: #86868b;
        --border-radius: 16px;
        --shadow-sm: 0 4px 6px -1px rgba(0,0,0,0.05);
        --shadow-md: 0 10px 15px -3px rgba(0,0,0,0.08);
    }

    .stApp {
        background-color: var(--bg-color);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Headers bonitos */
    h1, h2, h3 {
        color: var(--text-primary);
        font-weight: 600;
        letter-spacing: -0.02em;
    }
    
    /* Cards Modernas */
    div.stMarkdown > div[data-testid="stMarkdownContainer"] > div.card-apple {
        background: var(--card-bg);
        border-radius: var(--border-radius);
        padding: 24px;
        box-shadow: var(--shadow-sm);
        border: 1px solid rgba(0,0,0,0.04);
        margin-bottom: 20px;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    /* Botones Premium */
    div.stButton > button {
        border-radius: 12px;
        font-weight: 500;
        padding: 0.6rem 1.5rem;
        background-color: #111;
        color: white;
        border: none;
        transition: all 0.2s ease;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    div.stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        background-color: #000;
    }
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #007aff 0%, #0056b3 100%);
        border: none;
    }

    /* Inputs y Areas de texto */
    .stTextInput > div > div > input, 
    .stTextArea > div > textarea {
        border-radius: 12px !important;
        border: 1px solid #e1e1e6 !important;
        background-color: #fff !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.03) !important;
        padding: 12px 16px;
        transition: border-color 0.2s;
    }
    .stTextInput > div > div > input:focus, 
    .stTextArea > div > textarea:focus {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 3px rgba(0,122,255,0.1) !important;
    }

    /* File Uploader mejorado */
    div[data-testid="stFileUploader"] {
        border-radius: var(--border-radius);
        background-color: white;
        padding: 20px;
        border: 1px dashed #c7c7cc;
        text-align: center;
    }
    
    /* Status Container */
    div[data-testid="stStatusWidget"] {
        border-radius: 12px;
        box-shadow: var(--shadow-md);
        background: white;
        border: 1px solid #eee;
    }
    
    /* Success/Error/Info boxes */
    div[data-testid="stAlert"] {
        border-radius: 12px;
        border: none;
        box-shadow: var(--shadow-sm);
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: rgba(118, 118, 128, 0.12);
        padding: 4px;
        border-radius: 12px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        color: var(--text-secondary);
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background-color: white !important;
        color: var(--text-primary) !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    /* Skeleton loader para carga */
    @keyframes shimmer {
        0% { background-position: -468px 0; }
        100% { background-position: 468px 0; }
    }
    .skeleton {
        animation: shimmer 1.5s ease-in-out infinite;
        background: linear-gradient(to right, #eeeeee 8%, #dddddd 18%, #eeeeee 33%);
        background-size: 800px 104px;
        height: 20px;
        border-radius: 6px;
        margin: 8px 0;
    }
    </style>

    
    <script>
    // SISTEMA ANTI-REPOSO EXTREMO PARA iOS/iPhone
    let wakeLock = null;
    let videoElement = null;
    let keepAliveInterval = null;
    
    // Método 1: Wake Lock API (para navegadores compatibles)
    async function requestWakeLock() {
        try {
            if ('wakeLock' in navigator) {
                wakeLock = await navigator.wakeLock.request('screen');
                console.log('✅ Wake Lock activado');
            }
        } catch (err) {
            console.log('⚠️ Wake Lock no disponible');
        }
    }
    
    // Método 2: Video invisible (MÁS EFECTIVO EN iOS)
    function createInvisibleVideo() {
        if (!videoElement) {
            videoElement = document.createElement('video');
            videoElement.setAttribute('playsinline', 'true');
            videoElement.setAttribute('muted', 'true');
            videoElement.setAttribute('loop', 'true');
            videoElement.style.position = 'fixed';
            videoElement.style.opacity = '0';
            videoElement.style.width = '1px';
            videoElement.style.height = '1px';
            videoElement.style.pointerEvents = 'none';
            
            // Crear un video de 1 frame negro (base64)
            videoElement.src = 'data:video/mp4;base64,AAAAIGZ0eXBpc29tAAACAGlzb21pc28yYXZjMW1wNDEAAAAIZnJlZQAAAu1tZGF0AAACrQYF//+c3EXpvebZSLeWLNgg2SPu73gyNjQgLSBjb3JlIDE1NSByMjkwMSA3ZDBmZjIyIC0gSC4yNjQvTVBFRy00IEFWQyBjb2RlYyAtIENvcHlsZWZ0IDIwMDMtMjAxOCAtIGh0dHA6Ly93d3cudmlkZW9sYW4ub3JnL3gyNjQuaHRtbCAtIG9wdGlvbnM6IGNhYmFjPTEgcmVmPTMgZGVibG9jaz0xOjA6MCBhbmFseXNlPTB4MzoweDExMyBtZT1oZXggc3VibWU9NyBwc3k9MSBwc3lfcmQ9MS4wMDowLjAwIG1peGVkX3JlZj0xIG1lX3JhbmdlPTE2IGNocm9tYV9tZT0xIHRyZWxsaXM9MSA4eDhkY3Q9MSBjcW09MCBkZWFkem9uZT0yMSwxMSBmYXN0X3Bza2lwPTEgY2hyb21hX3FwX29mZnNldD0tMiB0aHJlYWRzPTEyIGxvb2thaGVhZF90aHJlYWRzPTIgc2xpY2VkX3RocmVhZHM9MCBucj0wIGRlY2ltYXRlPTEgaW50ZXJsYWNlZD0wIGJsdXJheV9jb21wYXQ9MCBjb25zdHJhaW5lZF9pbnRyYT0wIGJmcmFtZXM9MyBiX3B5cmFtaWQ9MiBiX2FkYXB0PTEgYl9iaWFzPTAgZGlyZWN0PTEgd2VpZ2h0Yj0xIG9wZW5fZ29wPTAgd2VpZ2h0cD0yIGtleWludD0yNTAga2V5aW50X21pbj0yNSBzY2VuZWN1dD00MCBpbnRyYV9yZWZyZXNoPTAgcmNfbG9va2FoZWFkPTQwIHJjPWNyZiBtYnRyZWU9MSBjcmY9MjMuMCBxY29tcD0wLjYwIHFwbWluPTAgcXBtYXg9NjkgcXBzdGVwPTQgaXBfcmF0aW89MS40MCBhcT0xOjEuMDAAgAAAAA9liIQAV/0TAAYdgAAAAwAAAwAAAwAAAwAAHxgBmAAAAwAAAwAAAwBwAAADBGABFBhIhYARAAAPCgBgQrxABYVhdG';
            
            document.body.appendChild(videoElement);
        }
        
        // Intentar reproducir
        videoElement.play().then(() => {
            console.log('✅ Video anti-reposo activado');
        }).catch(err => {
            console.log('⚠️ No se pudo activar video:', err);
        });
    }
    
    // Método 3: Mantener conexión activa con requestAnimationFrame (mejor que setInterval en iOS)
    function keepConnectionAlive() {
        let lastTime = Date.now();
        
        function animate() {
            const now = Date.now();
            if (now - lastTime >= 5000) { // Cada 5 segundos
                // Crear y destruir elemento para mantener conexión
                const ping = document.createElement('div');
                ping.style.display = 'none';
                document.body.appendChild(ping);
                setTimeout(() => ping.remove(), 50);
                lastTime = now;
            }
            keepAliveInterval = requestAnimationFrame(animate);
        }
        
        keepAliveInterval = requestAnimationFrame(animate);
    }
    
    // Activar/desactivar sistema
    function activateAntiSleep() {
        console.log('🔥 Activando sistema anti-reposo');
        requestWakeLock();
        createInvisibleVideo();
        keepConnectionAlive();
    }
    
    function deactivateAntiSleep() {
        console.log('💤 Desactivando sistema anti-reposo');
        
        if (wakeLock) {
            wakeLock.release();
            wakeLock = null;
        }
        
        if (videoElement) {
            videoElement.pause();
            videoElement.remove();
            videoElement = null;
        }
        
        if (keepAliveInterval) {
            cancelAnimationFrame(keepAliveInterval);
            keepAliveInterval = null;
        }
    }
    
    // Monitorizar cuando se está procesando
    function monitorProcessing() {
        const observer = new MutationObserver(() => {
            const statusWidget = document.querySelector('[data-testid="stStatusWidget"]');
            const spinner = document.querySelector('.stSpinner');
            
            if (statusWidget || spinner) {
                activateAntiSleep();
            } else {
                deactivateAntiSleep();
            }
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true,
            attributes: true
        });
    }
    
    // Iniciar cuando carga la página
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', monitorProcessing);
    } else {
        monitorProcessing();
    }
    </script>
""", unsafe_allow_html=True)



# ==========================================
# 🛡️ SEGURIDAD DE CANTIDADES
# ==========================================

def limpiar_cantidad(qty_ia):
    try:
        q = str(qty_ia).strip().replace(' ', '')
        if ',' in q: q = q.split(',')[0]
        if '.' in q: q = q.split('.')[0]
        valor = int(re.sub(r'[^0-9]', '', q))
        return valor if valor <= 100 else 1 
    except:
        return 1

def limpiar_para_stel(texto):
    """Elimina emojis y caracteres especiales para STEL Order"""
    # Eliminar caracteres fuera del rango BMP y símbolos específicos
    return re.sub(r'[^\w\s,.\-:\n@()áéíóúÁÉÍÓÚñÑ€/]', '', texto).strip()

# ==========================================
# 🔄 SISTEMA DE TRABAJOS EN SERVIDOR
# ==========================================

def get_file_hash(file_bytes):
    """Genera un hash único para identificar el archivo"""
    return hashlib.md5(file_bytes).hexdigest()

def create_job(file_bytes, filename):
    """Crea un nuevo trabajo de análisis"""
    job_id = get_file_hash(file_bytes)
    job_path = JOBS_DIR / job_id
    job_path.mkdir(exist_ok=True)
    
    # Guardar el PDF
    (job_path / "file.pdf").write_bytes(file_bytes)
    
    # Crear metadata del job
    metadata = {
        "job_id": job_id,
        "filename": filename,
        "status": "pending",  # pending, processing, completed, error
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    import json
    (job_path / "metadata.json").write_text(json.dumps(metadata, indent=2))
    
    return job_id

def get_job_status(job_id):
    """Consulta el estado de un trabajo"""
    job_path = JOBS_DIR / job_id
    if not job_path.exists():
        return None
    
    import json
    metadata_file = job_path / "metadata.json"
    if metadata_file.exists():
        return json.loads(metadata_file.read_text())
    return None

def get_job_result(job_id):
    """Obtiene el resultado de un trabajo completado"""
    job_path = JOBS_DIR / job_id
    result_file = job_path / "result.json"
    
    if result_file.exists():
        import json
        return json.loads(result_file.read_text())
    return None

def process_job_async(job_id, df_tarifa):
    """Procesa un trabajo de forma asíncrona en un hilo separado"""
    def worker():
        import json
        job_path = JOBS_DIR / job_id
        
        try:
            # Actualizar estado a processing
            metadata = json.loads((job_path / "metadata.json").read_text())
            metadata["status"] = "processing"
            metadata["updated_at"] = datetime.now().isoformat()
            (job_path / "metadata.json").write_text(json.dumps(metadata, indent=2))
            
            # Leer el PDF
            file_bytes = (job_path / "file.pdf").read_bytes()
            txt = extraer_pdf_pro(file_bytes)
            
            # Analizar con IA
            res = consultar_ollama_cache(txt)
            
            if res and res.get('tipo_documento') != "ERROR":
                # Procesar items
                cesta = []
                for l in res.get('items', []):
                    p = buscar_en_csv(l.get('ref'), df_tarifa)
                    cesta.append({
                        "ref": p['sku_canonical'] if p is not None else normalizar_referencia(l.get('ref')),
                        "desc": p['description'] if p is not None else l.get('desc', 'NUEVO'),
                        "qty": limpiar_cantidad(l.get('qty', 1)),
                        "precio": float(p['price']) if p is not None else 0.0
                    })
                
                result = {
                    "meta": res,
                    "cesta": cesta,
                    "error": None
                }
            else:
                result = {
                    "meta": res or {},
                    "cesta": [],
                    "error": res.get('error') if res else "Error desconocido"
                }
            
            # Guardar resultado
            (job_path / "result.json").write_text(json.dumps(result, indent=2))
            
            # Actualizar estado a completed
            metadata["status"] = "completed"
            metadata["updated_at"] = datetime.now().isoformat()
            (job_path / "metadata.json").write_text(json.dumps(metadata, indent=2))
            
        except Exception as e:
            # En caso de error
            metadata = json.loads((job_path / "metadata.json").read_text())
            metadata["status"] = "error"
            metadata["error"] = str(e)
            metadata["updated_at"] = datetime.now().isoformat()
            (job_path / "metadata.json").write_text(json.dumps(metadata, indent=2))
    
    # Iniciar el procesamiento en un hilo separado
    thread = threading.Thread(target=worker, daemon=True)
    thread.start()



# ==========================================
# 🧠 LÓGICA DE BÚSQUEDA Y TARIFAS
# ==========================================

def normalizar_referencia(texto_sucio: str) -> str:
    if not texto_sucio: return ""
    s = str(texto_sucio).strip().upper().replace(" ", "")
    tokens = re.split(r"[^A-Z0-9]+", s)
    codigo = next((t for t in tokens if len(t) > 2 and any(c.isdigit() for c in t)), s.replace("-", ""))
    if codigo.startswith("E") and len(codigo) > 2:
        return codigo[1:]
    return codigo

@st.cache_data
def cargar_tarifa():
    if os.path.exists("prices_2026.csv"):
        return pd.read_csv("prices_2026.csv", dtype={"sku_canonical": str, "price": float})
    return None

def buscar_en_csv(ref_sucia, df):
    if df is None or not ref_sucia: return None
    ref_norm = normalizar_referencia(ref_sucia)
    res = df[df["sku_canonical"].str.upper() == ref_norm.upper()]
    if res.empty and ref_norm.endswith("1"): res = df[df["sku_canonical"].str.upper() == ref_norm[:-1]+"I"]
    if res.empty and ref_norm.endswith("I"): res = df[df["sku_canonical"].str.upper() == ref_norm[:-1]+"1"]
    return res.iloc[0] if not res.empty else None

def buscar_por_texto(query, df):
    if df is None or not query: return pd.DataFrame()
    q = query.upper()
    mask = df.apply(lambda x: q in str(x['sku_canonical']).upper() or q in str(x['description']).upper(), axis=1)
    return df[mask].head(15)

# ==========================================
# 🎨 UI COMPONENTS
# ==========================================

def shipping_box(color_left, titulo, texto_html):
    st.markdown(
        f"""
        <div class="card-apple" style="border-left: 5px solid {color_left};">
            <h3 style="margin: 0 0 10px 0; font-size: 1.1rem;">{titulo}</h3>
            <div style="color: #333; font-size: 0.95rem; line-height: 1.5;">
                {texto_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ==========================================
# 📄 PROCESAMIENTO PDF Y IA
# ==========================================

@st.cache_data(show_spinner=False)
def extraer_pdf_pro(file_content):
    texto_completo = []
    import io
    with pdfplumber.open(io.BytesIO(file_content)) as pdf:
        # Volvemos a un límite seguro de 8 páginas para mayor contexto
        paginas = pdf.pages[:8] 
        for page in paginas:
            texto_pagina = [page.extract_text(layout=True) or ""]
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    if row and any(row): texto_pagina.append(" | ".join([str(c).strip() for c in row if c]))
            texto_completo.append("\n".join(texto_pagina))
    return "\n".join(texto_completo)

# ==========================================
# 🤖 GEMINI API (RÁPIDO Y PRECISO)
# ==========================================
import google.generativeai as genai

GEMINI_API_KEY = "AIzaSyBqTTFLRST2xzti0VpWM2HJTO2wg08ibSU"

# Detección dinámica de modelo (Lógica Original Restaurada)
try:
    genai.configure(api_key=GEMINI_API_KEY)
    lista_modelos = []
    try:
        for m in genai.list_models():
            if "generateContent" in m.supported_generation_methods:
                lista_modelos.append(m.name)
    except Exception:
        pass

    modelo_final = None
    # Preferir Flash
    for m in lista_modelos:
        if "flash" in m and "exp" not in m:
            modelo_final = m
            break
    # Si no, el primero disponible
    if not modelo_final and lista_modelos:
        modelo_final = lista_modelos[0]

    # Fallback si falla la detección
    if not modelo_final:
        modelo_final = "models/gemini-1.5-flash"

except Exception as e:
    modelo_final = "models/gemini-1.5-flash"

# Guardar variable global o en session si es necesario, 
# pero aquí lo usaremos para configurar por defecto.
GEMINI_MODEL_DEFAULT = modelo_final

@st.cache_data(show_spinner=False)
def consultar_gemini_cache(texto: str) -> dict:
    """Analiza PDF usando Gemini API - Rápido (~5-10 seg)"""
    texto_ia = texto.replace("C/ MENDEZ ALVARO, 44", "[DIR_FACT_ELIMINADA]").replace("28043 MADRID", "")
    
    prompt = f"""Analiza este presupuesto y extrae JSON:
{{
    "tipo_documento": "ISTOBAL" o "WASHTEC",
    "titulo_lugar": "Nombre Cliente/Estación",
    "pedido_ref": "Número Pedido",
    "direcciones_candidatas": ["Dirección entrega completa"],
    "items": [{{"ref": "CODIGO", "qty": 1, "desc": "DESCRIPCION"}}]
}}

TEXTO: {texto_ia[:15000]}"""
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        res = json.loads(response.text)
        
        if res.get('direcciones_candidatas'):
            res['direccion_envio'] = res['direcciones_candidatas'][0]
        else:
            res['direccion_envio'] = ""
        
        txt_upper = texto.upper()
        if "WASHTEC" in txt_upper: res['tipo_documento'] = "WASHTEC"
        elif "ISTOBAL" in txt_upper: res['tipo_documento'] = "ISTOBAL"
        
        return res
    except Exception as e:
        return {"tipo_documento": "ERROR", "items": [], "direcciones_candidatas": [], "error": str(e)}



# ==========================================
# 📦 INTEGRACIÓN STEL ORDER
# ==========================================

def asegurar_producto_stel(ref, desc, pvp):
    """
    Busca el producto en STEL por referencia.
    Si existe, devuelve su ID. Si no existe, lo crea.
    Basado en el código antiguo funcional del usuario.
    """
    if not ref:
        return None
    
    headers = {"Content-Type": "application/json", "APIKEY": STEL_API_KEY}
    
    # 1) Buscar producto existente
    try:
        url = f"{STEL_URL}/products?reference={ref}"
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            data = r.json()
            # STEL puede devolver lista o dict con "data"
            items = data if isinstance(data, list) else data.get("data", [])
            if items:
                for prod in items:
                    if str(prod.get("reference", "")).upper() == ref.upper():
                        prod_id = prod.get("id")
                        # Actualizar precio si existe
                        try:
                            p_compra = round(float(pvp) * 0.66, 2)
                            payload_update = {
                                "sales-price": float(pvp),
                                "purchase-price": p_compra
                            }
                            requests.put(f"{STEL_URL}/products/{prod_id}", json=payload_update, headers=headers)
                        except:
                            pass
                        return prod_id
    except Exception as e:
        pass  # Si falla la búsqueda, intentamos crear
    
    # 2) Crear nuevo producto
    p_compra = round(float(pvp) * 0.66, 2)
    payload = {
        "serial-number-id": -2,  # CRÍTICO: -2 indica referencia MANUAL
        "reference": ref,
        "name": desc[:250] if desc else f"Producto {ref}",
        "sales-price": float(pvp),
        "purchase-price": p_compra,
        "tax-rate": 21,
        "product-category-id": int(ISTOBAL_PRODUCT_CATEGORY_ID),
    }
    
    try:
        r = requests.post(f"{STEL_URL}/products", json=payload, headers=headers)
        if r.status_code in [200, 201]:
            body = r.json()
            # Puede devolver lista o dict
            if isinstance(body, list) and body:
                return body[0].get("id")
            return body.get("id")
        else:
            # Log del error para debug
            print(f"Error creando producto {ref}: ({r.status_code}) {r.text}")
            return None
    except Exception as e:
        print(f"Excepción creando producto {ref}: {e}")
        return None

def enviar_a_stel(cliente_id, lineas, tipo, ref_ped, direccion, titulo, email_texto):
    headers = {"Content-Type": "application/json", "APIKEY": STEL_API_KEY}
    endpoint = "workOrders" if tipo == "ISTOBAL" else "salesOrders"
    dto = 27 if tipo == "ISTOBAL" else 10
    items_api = []
    for l in lineas:
        sid = asegurar_producto_stel(l['ref'], l['desc'], l['precio'])
        if sid:
            items_api.append({"line-type": "ITEM", "item-id": int(sid), "units": float(l['qty']), "item-base-price": float(l['precio']), "discount-percentage": dto})
    if tipo == "WASHTEC":
        items_api.append({"line-type": "ITEM", "item-id": PORTES_ID_FIJO, "units": 1.0, "item-base-price": PORTES_PRICE_VENTA, "discount-percentage": 0})
    
    # Limpiamos los comentarios para STEL Order (sin emojis)
    texto_limpio = limpiar_para_stel(email_texto)
    payload = {"account-id": int(cliente_id), "title": f"{tipo} - {ref_ped} - {titulo}", "lines": items_api, "private-comments": texto_limpio, "comments": f"PEDIDO: {ref_ped}\nENTREGA: {direccion}"}
    return requests.post(f"{STEL_URL}/{endpoint}", json=payload, headers=headers)

def enviar_email_smtp(destinatario_principal, copia_oculta, asunto, cuerpo, password_app):
    remitente = "incidencias@satgarzon.com"
    msg = MIMEMultipart()
    msg['From'] = remitente
    msg['To'] = destinatario_principal
    msg['Subject'] = asunto

    msg.attach(MIMEText(cuerpo, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(remitente, password_app)
        # Enviar a todos (principal + copia oculta + remitente como copia)
        destinatarios = [destinatario_principal] + copia_oculta + [remitente]
        server.sendmail(remitente, destinatarios, msg.as_string())
        server.quit()
        return True, "Email enviado correctamente"
    except Exception as e:
        return False, str(e)


# ==========================================
# 🖥️ INTERFAZ PRINCIPAL
# ==========================================

# Cabecera con Logos
# Cabecera Premium
st.markdown("---")
col_h1, col_h2 = st.columns([1, 5])

with col_h1:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=100)
    else:
        st.write("📍")

with col_h2:
    st.markdown("""
        <div style="padding-top: 5px;">
            <h1 style="margin-bottom: 5px; font-size: 2.2rem; font-weight: 600; font-family: -apple-system, BlinkMacSystemFont, sans-serif;">GARZON <span style="color: #0066CC;">Pedidos Pro</span></h1>
            <p style="color: #6e6e73; font-size: 1rem; margin-top: 0px; font-weight: 400;">
                Gestión Inteligente de Logística · Powered by Ryzen AI
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Logo Coches debajo del título para seriedad
    if os.path.exists("Coches garzon.png"):
        st.write("") # Espacio
        st.image("Coches garzon.png", width=350)

st.markdown("---")




# Carga optimizada de tarifa con indicador visual
if 'tarifa_cargada' not in st.session_state:
    with st.spinner('Cargando sistema...'):
        df_tarif = cargar_tarifa()
        st.session_state['tarifa_cargada'] = True
        st.session_state['df_tarif'] = df_tarif
else:
    df_tarif = st.session_state.get('df_tarif')

if 'cesta' not in st.session_state: st.session_state.cesta = []
if 'meta' not in st.session_state: st.session_state.meta = {}

# Recuperar trabajos pendientes al iniciar (por si cerró el navegador)
if 'current_job_id' not in st.session_state:
    # Buscar trabajos recientes en los últimos 5 minutos (reducido)
    import json
    from datetime import datetime, timedelta
    
    for job_dir in sorted(JOBS_DIR.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
        if job_dir.is_dir():
            metadata_file = job_dir / "metadata.json"
            if metadata_file.exists():
                try:
                    metadata = json.loads(metadata_file.read_text())
                    created_at = datetime.fromisoformat(metadata.get('created_at', ''))
                    
                    # Solo trabajos muy recientes (5 minutos)
                    if datetime.now() - created_at < timedelta(minutes=5):
                        status = metadata.get('status')
                        
                        # SOLO si está completado (no processing, para evitar loops)
                        if status == 'completed':
                            st.session_state.current_job_id = metadata['job_id']
                            break
                except Exception:
                    pass

# Inicializar contador de polling para evitar loops infinitos
if 'polling_count' not in st.session_state:
    st.session_state.polling_count = 0


with st.sidebar:
    st.markdown("### 🛠️ Herramientas")
    
    # Input para contraseña de aplicación (SMTP)
    pass_smtp = st.text_input("🔑 Clave Email (Google App)", type="password", help="Contraseña de aplicación de Gmail para incidencias@satgarzon.com")
    
    if st.button("🔄 LIMPIAR CACHÉ", use_container_width=True):
        st.cache_data.clear()
        st.success("Caché limpiado")
        time.sleep(1)
        st.rerun()
    
    if st.button("🧹 VACIAR TODO", use_container_width=True):


        st.session_state.cesta = []
        st.session_state.meta = {}
        st.rerun()

t1, t2 = st.tabs(["✨ Análisis Inteligente", "🔍 Catálogo"])

with t1:
    st.info("✨ Usando Gemini AI - Análisis rápido (~10 segundos)")




    
    f_pdf = st.file_uploader("Sube PDF o Foto del pedido", type=["pdf", "jpg", "jpeg", "png"], key="pdf_upload")
    
    if st.button("🚀 ANALIZAR PEDIDO", use_container_width=True, type="primary"):
        if f_pdf:
            st.session_state.cesta = []
            
            modelo_usar = st.session_state.get("modelo_elegido", GEMINI_MODEL_DEFAULT)
            genai.configure(api_key=GEMINI_API_KEY)

            model = genai.GenerativeModel(modelo_usar)

            
            with st.spinner("Analizando documento..."):
                prompt_text = """
                Analiza este documento visualmente. Extrae la siguiente información:
                
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
                
                contenido_analizar = f_pdf.getvalue()
                
                # Detectar tipo Mime
                mime = "application/pdf"
                if f_pdf.type in ["image/jpeg", "image/jpg"]: mime = "image/jpeg"
                elif f_pdf.type == "image/png": mime = "image/png"
                
                content = [prompt_text, {"mime_type": mime, "data": contenido_analizar}]

                
                exito = False
                data = None
                errores_log = []
                
                for _ in range(3):
                    try:
                        response = model.generate_content(
                            content,
                            generation_config={"response_mime_type": "application/json"},
                        )
                        data = json.loads(response.text)
                        exito = True
                        break
                    except Exception as e:
                        errores_log.append(str(e))
                        time.sleep(2)
                
                if exito and data:
                    # Validar con tarifa
                    lineas_previas = data.get("lineas", [])
                    
                    st.session_state.meta = data
                    st.session_state.cesta = []
                    
                    for l in lineas_previas:
                        p = buscar_en_csv(l.get('ref'), df_tarif)
                        st.session_state.cesta.append({
                            "ref": p['sku_canonical'] if p is not None else normalizar_referencia(l.get('ref')),
                            "desc": p['description'] if p is not None else l.get('desc', 'NUEVO'),
                            "qty": limpiar_cantidad(l.get('qty', 1)),
                            "precio": float(p['price']) if p is not None else 0.0
                        })
                    
                    st.rerun()
                else:
                    st.error("Error analizando documento. Revisa el PDF o inténtalo de nuevo.")
                    if errores_log:
                        st.caption(f"Detalle interno: {errores_log[-1]}")







with t2:
    q = st.text_input("Buscador de piezas")
    if q:
        res = buscar_por_texto(q, df_tarif)
        for i, r in res.iterrows():
            c1, c2, c3 = st.columns([3, 0.8, 1.2])
            c1.write(f"**{r['sku_canonical']}** - {r['description']} | **{r['price']:.2f} €**")
            
            if c2.button("➕", key=f"cat_{i}", help="Añadir a cesta"):
                st.session_state.cesta.append({"ref": r['sku_canonical'], "desc": r['description'], "qty": 1, "precio": r['price']})
                st.rerun()
                
            if c3.button("☁️ STEL", key=f"sync_{i}", help="Crear/Actualizar en STEL"):
                with st.spinner("Sincronizando..."):
                    sid = asegurar_producto_stel(r['sku_canonical'], r['description'], r['price'])
                    if sid:
                        st.success(f"OK (ID: {sid})")
                    else:
                        st.error("Error")

# --- ÁREA DE RESULTADOS ---
if st.session_state.cesta:
    st.divider()
    m = st.session_state.meta
    
    tipo_det = m.get('tipo_documento', 'ISTOBAL')
    tipo_d = st.radio("Maquinaria detectada:", ["ISTOBAL", "WASHTEC"], index=0 if tipo_det == "ISTOBAL" else 1, horizontal=True)
    
    st.markdown(f"### 📋 Confirmación:")
    
    c1, c2 = st.columns(2)
    tit_f = c1.text_input("Estación", m.get('titulo_lugar', ''))
    ped_f = c2.text_input("Referencia Pedido", m.get('pedido_ref', ''))
    
    dirs = m.get('direcciones_candidatas', [])
    if dirs:
        st.info(f"📍 {len(dirs)} direcciones detectadas. Selecciona la correcta:")
        d_sel = st.selectbox("Dirección de envío:", dirs, key="sel_dir_main")
        dir_f = st.text_area("Dirección final:", d_sel)
    else:
        st.warning("⚠️ No se han detectado direcciones claras en el PDF.")
        dir_f = st.text_area("Dirección final:", m.get('direccion_envio', ''))

    
    # Editor de datos
    df_v = pd.DataFrame(st.session_state.cesta)
    df_v["status"] = ["✅" if buscar_en_csv(r['ref'], df_tarif) is not None else "❌ ??" for _, r in df_v.iterrows()]
    cols = ["status", "ref", "desc", "qty", "precio"]
    
    df_ed = st.data_editor(df_v[cols], use_container_width=True, num_rows="dynamic")
    
    # Sincronización
    nueva = []
    total = 0.0
    for r in df_ed.to_dict('records'):
        p = buscar_en_csv(r['ref'], df_tarif)
        if p is not None and r['desc'] == 'NUEVO':
            r['desc'] = p['description']
            r['precio'] = float(p['price'])
        nueva.append({"ref": r['ref'], "desc": r['desc'], "qty": r['qty'], "precio": r['precio']})
        total += float(r['qty']) * float(r['precio'])
    st.session_state.cesta = nueva
    
    st.metric("TOTAL PEDIDO", f"{total:,.2f} €")
    
    # Email Premium solicitado por el usuario
    asunto = f"🛠️ Pedido de Repuestos | Ref: {ped_f} | SAT Garzón"
    
    txt_e = f"Asunto: {asunto}\n\n"
    txt_e += f"Buenos días,\n\n"
    txt_e += f"Adjuntamos los detalles para la gestión del pedido nº {ped_f}. Por favor, procesen el siguiente material para su envío:\n\n"
    txt_e += "⚙️ Detalle de Materiales\n\n"
    for l in st.session_state.cesta:
        txt_e += f"Ref. {l['ref']} — {l['desc']} 📦 x{l['qty']}\n\n"
    
    txt_e += f"🚚 Dirección de Envío\n\n"
    txt_e += f"{tit_f} 📍 Ubicación: {dir_f}\n\n"
    txt_e += "Agradecemos nos confirmen la disponibilidad y la fecha prevista de entrega. Quedamos a su disposición para cualquier aclaración.\n\n"
    txt_e += "Atentamente,\n\n"
    txt_e += "SAT Garzón Servicio de Asistencia Técnica\n\n"
    txt_e += "✨ Este pedido ha sido procesado y optimizado por el Sistema de IA Avanzada de SAT Garzón (Ryzen 9) para garantizar la máxima precisión en la logística."
    
    email_f = st.text_area("📧 Email a enviar:", txt_e, height=450)

    
    col_stel, col_email = st.columns(2)
    
    with col_stel:
        label = f"🚀 STEL ORDER ({tipo_d})"
        if st.button(label, use_container_width=True, type="primary"):
            cid = CLIENTE_ISTOBAL_ID if tipo_d == "ISTOBAL" else CLIENTE_WASHTEC_ID
            with st.spinner("⏳ Enviando a STEL Order..."):
                enviar_a_stel(cid, st.session_state.cesta, tipo_d, ped_f, dir_f, tit_f, email_f)
                
            st.toast("✅ Pedido creado correctamente en STEL Order", icon="🚀")
            shipping_box("#28cd41", "STEL Order Sincronizado", 
                f"""
                <div style="font-weight: 500; font-size: 1.1rem; margin-bottom: 5px;">Envío Completado</div>
                Se ha generado el documento en <strong>{tipo_d}</strong><br>
                Referencia: <code style="background: #eed; padding: 2px 5px; border-radius: 4px;">{ped_f}</code>
                """)
            
    with col_email:
        if st.button("📧 ENVIAR EMAIL DIRECTO", use_container_width=True):
            if not pass_smtp:
                st.toast("❌ Error: Falta clave de email", icon="⚠️")
                shipping_box("#ff3b30", "Error de Configuración", "Falta la clave de email en el menú lateral")
            else:
                if tipo_d == "ISTOBAL":
                    destinatario = "atencionclientes@istobal.com"
                    bccs = []
                else: 
                    destinatario = "atencionclientes@istobal.com"
                    bccs = ["pedidos@washtec.com"]
                
                with st.spinner(f"📨 Enviando correo a {destinatario}..."):
                    ok, msg = enviar_email_smtp(destinatario, bccs, asunto, email_f, pass_smtp)
                    
                    if ok:
                        st.toast("✅ Email enviado correctamente", icon="📧")
                        shipping_box("#007aff", "Email Enviado", 
                            f"""
                            <div style="font-weight: 500; font-size: 1.1rem; margin-bottom: 5px;">Notificación Enviada</div>
                            <strong>Destinatario:</strong> {destinatario}<br>
                            <strong>Copia (BCC):</strong> {', '.join(bccs) if bccs else 'Ninguno'}
                            """)
                    else:
                        st.toast("❌ Error al enviar email", icon="🚫")
                        shipping_box("#ff3b30", "Error envío Email", f"Detalle: {msg}")