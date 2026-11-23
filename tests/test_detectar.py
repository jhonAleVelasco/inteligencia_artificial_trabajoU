"""Pruebas de src/detectar.py (deteccion de varias frutas y descuento).

Ejecutar desde la raiz del repositorio:
    pytest tests/test_detectar.py
No necesitan el modelo real ni fotos: usan frutas dibujadas y un modelo falso.
"""
import numpy as np
import pytest
from PIL import Image, ImageDraw

from src.detectar import (Deteccion, decidir_accion, detectar_frutas, dibujar_detecciones,
                          resumir_escena, precio_final, segmentar_frutas)
from src.preprocessing import cargar_imagen

FONDO = (236, 233, 226)


def escena(circulos, tamano=(900, 600), fondo=FONDO):
    """Foto de prueba: circulos de colores (cx, cy, radio, color) sobre un fondo claro."""
    img = Image.new("RGB", tamano, fondo)
    pincel = ImageDraw.Draw(img)
    for cx, cy, r, c in circulos:
        pincel.ellipse((cx - r, cy - r, cx + r, cy + r), fill=c)
    return img


class ModeloFalso:
    """Imita al pipeline: siempre responde `proba` sobre las clases `clases`."""

    def __init__(self, clases, proba):
        self.classes_ = np.array(clases)
        self._proba = np.array(proba, dtype=float)

    def predict_proba(self, X):
        return np.tile(self._proba, (len(X), 1))


def test_cuenta_tres_frutas_separadas_de_izquierda_a_derecha():
    foto = escena([(700, 300, 80, (200, 40, 40)), (150, 300, 80, (230, 190, 30)), (420, 300, 80, (60, 150, 60))])
    mascaras = segmentar_frutas(np.asarray(foto))
    assert len(mascaras) == 3
    centros = [np.where(m)[1].mean() for m in mascaras]
    assert centros == sorted(centros)


def test_separa_dos_frutas_pegadas():
    foto = escena([(380, 300, 90, (200, 40, 40)), (530, 300, 90, (200, 40, 40))])  # se tocan
    assert len(segmentar_frutas(np.asarray(foto), separar=True)) == 2
    assert len(segmentar_frutas(np.asarray(foto), separar=False)) == 1


def test_fondo_liso_no_tiene_frutas():
    assert segmentar_frutas(np.asarray(escena([]))) == []


def test_ignora_motas_diminutas():
    foto = escena([(450, 300, 80, (200, 40, 40)), (100, 100, 3, (30, 30, 30))])
    assert len(segmentar_frutas(np.asarray(foto))) == 1


def test_decidir_accion_en_los_umbrales():
    assert decidir_accion(0.39) == "normal"
    assert decidir_accion(0.40) == "descuento"
    assert decidir_accion(0.79) == "descuento"
    assert decidir_accion(0.80) == "retirar"
    assert decidir_accion(0.55, umbral_descuento=0.6, umbral_retiro=0.9) == "normal"


def test_decidir_accion_rechaza_umbrales_invalidos():
    with pytest.raises(ValueError):
        decidir_accion(0.5, umbral_descuento=0.9, umbral_retiro=0.5)


def test_detectar_frutas_decide_segun_la_probabilidad_de_podrida():
    # 50 % de probabilidad para manzana_podrida -> prob. de podrida 0.5: descuento
    modelo = ModeloFalso(["manzana_fresca", "manzana_podrida"], [0.5, 0.5])
    foto = escena([(250, 300, 80, (200, 40, 40)), (600, 300, 80, (200, 40, 40))])
    _, dets = detectar_frutas(modelo, foto, umbral=0.5)
    assert len(dets) == 2
    assert all(d.accion == "descuento" and d.resultado["fruta"] == "manzana" for d in dets)


def test_fruta_con_poca_confianza_se_marca_para_revisar():
    modelo = ModeloFalso(["manzana_fresca", "manzana_podrida", "banano_fresco", "banano_podrido"],
                         [0.3, 0.3, 0.2, 0.2])
    _, dets = detectar_frutas(modelo, escena([(450, 300, 80, (200, 40, 40))]), umbral=0.6)
    assert [d.accion for d in dets] == ["revisar"]


def test_fruta_muy_probablemente_podrida_se_retira_aunque_no_se_sepa_cual_es():
    # clase mas probable 0.30 (< umbral 0.6) pero 0.9 de probabilidad total de podrida
    modelo = ModeloFalso(["manzana_fresca", "manzana_podrida", "banano_podrido", "uva_podrida", "fresa_podrida"],
                         [0.05, 0.30, 0.25, 0.20, 0.20])
    _, dets = detectar_frutas(modelo, escena([(450, 300, 80, (200, 40, 40))]), umbral=0.6)
    assert [d.accion for d in dets] == ["retirar"]


def fruta_falsa(fruta, accion):
    return Deteccion(caja=(0, 0, 10, 10), area=100, recorte=Image.new("RGB", (8, 8)),
                     resultado={"fruta": fruta}, accion=accion)


def test_resumir_escena_calcula_descuento_y_excluye_retiradas():
    dets = [fruta_falsa("manzana", "normal"), fruta_falsa("manzana", "descuento"),
            fruta_falsa("banano", "retirar"), fruta_falsa("uva", "revisar")]
    r = resumir_escena(dets, {"manzana": 1000, "banano": 500, "uva": 2000}, descuento=0.30)
    assert (r["total"], r["normal"], r["descuento"], r["retirar"], r["revisar"]) == (4, 1, 1, 1, 1)
    assert r["valor_sin_descuento"] == 2000
    assert r["valor_con_descuento"] == pytest.approx(1700)
    assert r["descuento_total"] == pytest.approx(300)


def test_precio_final_por_accion():
    precios = {"manzana": 1000}
    assert precio_final(fruta_falsa("manzana", "normal"), precios) == 1000
    assert precio_final(fruta_falsa("manzana", "descuento"), precios, 0.25) == pytest.approx(750)
    assert precio_final(fruta_falsa("manzana", "retirar"), precios) is None
    assert precio_final(fruta_falsa("manzana", "revisar"), precios) is None


def test_resumir_escena_rechaza_descuento_invalido():
    with pytest.raises(ValueError):
        resumir_escena([], {}, descuento=1.5)


def test_dibujar_detecciones_devuelve_imagen_del_mismo_tamano():
    foto = escena([(450, 300, 80, (200, 40, 40))])
    modelo = ModeloFalso(["manzana_fresca", "manzana_podrida"], [0.9, 0.1])
    foto_trabajo, dets = detectar_frutas(modelo, foto)
    assert dibujar_detecciones(foto_trabajo, dets).size == foto_trabajo.size


def test_cargar_imagen_acepta_objetos_pil():
    assert cargar_imagen(Image.new("RGB", (40, 30), (10, 20, 30))).size == (40, 30)
