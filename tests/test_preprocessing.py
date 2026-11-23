"""Pruebas de src/preprocessing.py.

Ejecutar desde la raiz del repositorio:
    pip install -r requirements-dev.txt
    pytest
"""
import io

import numpy as np
import pytest
from PIL import Image

from src.preprocessing import (TAMANO, cargar_imagen, extraer_caracteristicas,
                               nombres_caracteristicas, normalizar_imagen)


def imagen_de_prueba(ancho=300, alto=200, color=(200, 60, 40)):
    return Image.new("RGB", (ancho, alto), color)


def test_normalizar_imagen_devuelve_cuadrado_del_tamano_esperado():
    normal = normalizar_imagen(imagen_de_prueba(300, 200))
    assert normal.size == (TAMANO, TAMANO)


def test_vector_tiene_1806_caracteristicas_y_coincide_con_los_nombres():
    vector = extraer_caracteristicas(imagen_de_prueba())
    assert vector.shape == (1806,)
    assert len(nombres_caracteristicas()) == vector.size


def test_vector_no_tiene_nulos_ni_infinitos():
    vector = extraer_caracteristicas(imagen_de_prueba())
    assert np.isfinite(vector).all()


def test_histogramas_de_color_y_textura_suman_uno():
    vector = extraer_caracteristicas(imagen_de_prueba())
    h, s, v, lbp = vector[:16], vector[16:24], vector[24:32], vector[32:42]
    for bloque in (h, s, v, lbp):
        assert bloque.sum() == pytest.approx(1.0, abs=1e-5)


def test_imagenes_de_distinto_color_dan_vectores_distintos():
    roja = extraer_caracteristicas(imagen_de_prueba(color=(200, 30, 30)))
    verde = extraer_caracteristicas(imagen_de_prueba(color=(30, 200, 30)))
    assert not np.allclose(roja, verde)


def test_cargar_imagen_desde_memoria():
    buffer = io.BytesIO()
    imagen_de_prueba().save(buffer, format="PNG")
    buffer.seek(0)
    assert cargar_imagen(buffer).mode == "RGB"


def test_cargar_imagen_rechaza_archivo_que_no_es_imagen():
    with pytest.raises(ValueError):
        cargar_imagen(io.BytesIO(b"esto no es una imagen"))
