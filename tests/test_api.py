"""Pruebas de la API (api/main.py) con los modelos reales y fotos dibujadas.

Ejecutar desde la raiz del repositorio:  pytest tests/test_api.py
"""
import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

from api.main import app

FONDO = (236, 233, 226)


def foto(circulos, tamano=(900, 600)):
    img = Image.new("RGB", tamano, FONDO)
    pincel = ImageDraw.Draw(img)
    for cx, cy, r, c in circulos:
        pincel.ellipse((cx - r, cy - r, cx + r, cy + r), fill=c)
    memoria = io.BytesIO()
    img.save(memoria, "JPEG")
    return memoria.getvalue()


TRES = foto([(150, 300, 80, (200, 40, 40)), (420, 300, 80, (230, 190, 30)), (700, 300, 80, (60, 150, 60))])


def archivo(datos, nombre="foto.jpg", campo="foto"):
    return (campo, (nombre, datos, "image/jpeg"))


@pytest.fixture(scope="module")
def cliente():
    with TestClient(app) as c:       # el "with" ejecuta la carga de los modelos
        yield c


def test_estado_y_config(cliente):
    e = cliente.get("/api/estado").json()
    assert e["listo"] is True and e["modelo_deteccion_propio"] is True
    c = cliente.get("/api/config").json()
    assert len(c["frutas"]) == 8 and {"id", "nombre", "precio_unidad"} <= set(c["frutas"][0])
    assert c["por_defecto"]["descuento_desde"] == 0.4 and c["por_defecto"]["retirar_desde"] == 0.8


def test_archivo_que_no_es_imagen_da_422_claro(cliente):
    r = cliente.post("/api/revisar", files=[archivo(b"esto no es una imagen", "notas.txt")])
    assert r.status_code == 422 and "notas.txt" in r.json()["detail"]


def test_confianza_fuera_de_rango_da_422(cliente):
    r = cliente.post("/api/revisar?confianza=1.5", files=[archivo(TRES)])
    assert r.status_code == 422


def test_revisar_encuentra_cada_fruta_con_su_caja(cliente):
    d = cliente.post("/api/revisar", files=[archivo(TRES)]).json()
    assert len(d["frutas"]) == 3 and d["ancho"] > 0 and d["alto"] > 0
    xs = [f["caja"]["x0"] for f in d["frutas"]]
    assert xs == sorted(xs)                              # de izquierda a derecha
    for f in d["frutas"]:
        c = f["caja"]
        assert 0 <= c["x0"] < c["x1"] <= 1 and 0 <= c["y0"] < c["y1"] <= 1
        assert f["recorte"].startswith("data:image/jpeg;base64,")
        assert f["accion"] in ("normal", "descuento", "retirar", "revisar") and len(f["ranking"]) == 5


def test_revisar_sin_frutas_devuelve_lista_vacia(cliente):
    d = cliente.post("/api/revisar", files=[archivo(foto([]))]).json()
    assert d["frutas"] == []


def test_revisar_valida_los_umbrales(cliente):
    r = cliente.post("/api/revisar?descuento_desde=0.9&retirar_desde=0.5", files=[archivo(TRES)])
    assert r.status_code == 422


def test_revisar_una_sola_fruta(cliente):
    d = cliente.post("/api/revisar", files=[archivo(foto([(450, 300, 110, (200, 40, 40))]))]).json()
    assert len(d["frutas"]) == 1 and d["frutas"][0]["id"] == 1


def test_revisar_descarta_manchas_diminutas(cliente):
    una_y_ruido = foto([(300, 300, 120, (200, 40, 40)), (720, 120, 6, (60, 60, 60))])
    assert len(cliente.post("/api/revisar", files=[archivo(una_y_ruido)]).json()["frutas"]) == 1
