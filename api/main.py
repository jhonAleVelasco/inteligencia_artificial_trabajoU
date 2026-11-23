"""API de FrutaCheck: el modelo y el detector como servicio web.

Sirve el panel en React (web/dist) y expone los mismos modelos que usa la app de Streamlit:
  GET  /api/estado          ¿estan cargados los modelos?
  GET  /api/config          frutas con su precio por unidad y reglas por defecto
  POST /api/revisar         encuentra cada fruta de la foto (una o varias) y decide vender, descuento o retirar

Ejecutar desde la raiz del repositorio:
    python -m uvicorn api.main:app --port 8000
"""
import base64
import io
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image

from src.detectar import (DESCUENTO_DEFECTO, PRECIO_UNIDAD_EJEMPLO, UMBRAL_DESCUENTO, UMBRAL_RETIRO,
                          cargar_modelo_deteccion, detectar_frutas)
from src.predict import RAIZ, cargar_modelo, interpretar_clase, nombre_clase, nombre_fruta
from src.preprocessing import cargar_imagen

MAX_BYTES = 12 * 1024 * 1024     # tamano maximo de cada foto
MIN_AREA_RELATIVA = 0.08         # una region menor que esto frente a la mayor se considera ruido
UMBRAL_CONFIANZA = 0.60
DIST = RAIZ / "web" / "dist"


@asynccontextmanager
async def ciclo_de_vida(app):
    """Carga los modelos una vez al arrancar. Si faltan, la API responde 503 con la causa."""
    app.state.error = None
    app.state.modelo = app.state.modelo_deteccion = None
    app.state.deteccion_propia = False
    try:
        app.state.modelo = cargar_modelo()
        app.state.modelo_deteccion, app.state.deteccion_propia = cargar_modelo_deteccion()
    except Exception as error:  # archivo ausente o de otra version de scikit-learn
        app.state.error = str(error)
    yield


app = FastAPI(title="FrutaCheck", version="2.0", lifespan=ciclo_de_vida)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
                   allow_methods=["*"], allow_headers=["*"])


# ------------------------------------------------------------------------------ utilidades
def modelos_o_503():
    if app.state.error or app.state.modelo is None:
        raise HTTPException(503, f"No se pudieron cargar los modelos: {app.state.error or 'sin detalle'}")
    return app.state.modelo, app.state.modelo_deteccion


def leer_imagen(archivo: UploadFile) -> Image.Image:
    """Lee la foto subida; devuelve un error 422 claro si no es una imagen o pesa demasiado."""
    datos = archivo.file.read(MAX_BYTES + 1)
    if len(datos) > MAX_BYTES:
        raise HTTPException(422, f"{archivo.filename or 'La foto'} pesa más de {MAX_BYTES // 1024 // 1024} MB.")
    try:
        imagen = cargar_imagen(io.BytesIO(datos))
    except ValueError as error:
        raise HTTPException(422, f"{archivo.filename or 'La foto'}: {error}") from error
    return imagen


def a_data_url(imagen: Image.Image, lado: int = 160) -> str:
    """Miniatura JPEG en base64 para incrustar en el JSON."""
    mini = imagen.copy()
    mini.thumbnail((lado, lado))
    memoria = io.BytesIO()
    mini.save(memoria, "JPEG", quality=82)
    return "data:image/jpeg;base64," + base64.b64encode(memoria.getvalue()).decode()


def ranking(r, cuantos=None):
    filas = [{"clase": c, "nombre": nombre_clase(c), "probabilidad": p} for c, p in r["ranking"]]
    return filas if cuantos is None else filas[:cuantos]


def resultado_json(r, top=None):
    return {"clase": r["clase"], "nombre_clase": nombre_clase(r["clase"]), "fruta": r["fruta"],
            "nombre": nombre_fruta(r["fruta"]), "estado": r["estado"], "probabilidad": r["probabilidad"],
            "prob_podrida": r["prob_podrida"], "confiable": r["confiable"],
            "recomendacion": r["recomendacion"], "ranking": ranking(r, top)}


def rango(valor, minimo, maximo, nombre):
    if not minimo <= valor <= maximo:
        raise HTTPException(422, f"{nombre} debe estar entre {minimo} y {maximo}.")
    return valor


# ---------------------------------------------------------------------------------- rutas
@app.get("/api/estado")
def estado():
    return {"listo": app.state.error is None and app.state.modelo is not None, "error": app.state.error,
            "modelo_deteccion_propio": app.state.deteccion_propia}


@app.get("/api/config")
def config():
    modelo, _ = modelos_o_503()
    frutas = sorted({interpretar_clase(c)[0] for c in modelo.classes_})
    return {
        "frutas": [{"id": f, "nombre": nombre_fruta(f), "precio_unidad": PRECIO_UNIDAD_EJEMPLO.get(f, 1000)}
                   for f in frutas],
        "por_defecto": {"confianza": UMBRAL_CONFIANZA, "descuento": DESCUENTO_DEFECTO,
                        "descuento_desde": UMBRAL_DESCUENTO, "retirar_desde": UMBRAL_RETIRO},
    }


@app.post("/api/revisar")
def revisar(foto: UploadFile = File(...), confianza: float = Query(UMBRAL_CONFIANZA),
                  descuento_desde: float = Query(UMBRAL_DESCUENTO), retirar_desde: float = Query(UMBRAL_RETIRO)):
    _, modelo_det = modelos_o_503()
    rango(confianza, 0, 1, "La confianza mínima")
    rango(descuento_desde, 0, 1, "El umbral de descuento")
    rango(retirar_desde, descuento_desde, 1, "El umbral de retiro")
    imagen = leer_imagen(foto)
    try:
        trabajo, detecciones = detectar_frutas(modelo_det, imagen, umbral=confianza,
                                               umbral_descuento=descuento_desde, umbral_retiro=retirar_desde)
    except ValueError as error:
        raise HTTPException(422, f"No se pudo analizar la foto: {error}") from error
    ancho, alto = trabajo.size
    if detecciones:   # manchas minusculas junto a una fruta grande son ruido del fondo, no frutas
        mayor = max(d.area for d in detecciones)
        detecciones = [d for d in detecciones if d.area >= MIN_AREA_RELATIVA * mayor]
    frutas = []
    for i, d in enumerate(detecciones, 1):
        x0, y0, x1, y1 = d.caja
        frutas.append({**resultado_json(d.resultado, top=5), "id": i, "accion": d.accion, "area": d.area,
                       "caja": {"x0": x0 / ancho, "y0": y0 / alto, "x1": x1 / ancho, "y1": y1 / alto},
                       "recorte": a_data_url(d.recorte)})
    return {"ancho": ancho, "alto": alto, "frutas": frutas}


# ------------------------------------------------------------------------- panel (React)
if DIST.exists():
    if (DIST / "assets").exists():
        app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.get("/{ruta:path}", include_in_schema=False)
    def panel(ruta: str):
        """Sirve el archivo pedido de web/dist o, si no existe, la pagina principal del panel."""
        if ruta.startswith("api/"):
            raise HTTPException(404, "Ruta de la API inexistente.")
        archivo = (DIST / ruta).resolve()
        if ruta and archivo.is_file() and DIST.resolve() in archivo.parents:
            return FileResponse(archivo)
        return FileResponse(DIST / "index.html")
