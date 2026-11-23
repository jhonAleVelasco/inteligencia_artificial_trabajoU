"""Pruebas de src/predict.py: interpretacion de clases, prediccion y resumen de lotes.

Ejecutar desde la raiz del repositorio:
    pip install -r requirements-dev.txt
    pytest
"""
import io

import pytest
from PIL import Image

from src.predict import (cargar_modelo, interpretar_clase, nombre_clase, predecir,
                         resumir_lote)


@pytest.fixture(scope="module")
def modelo():
    return cargar_modelo()


def foto(lado=200, color=(220, 120, 30)):
    buffer = io.BytesIO()
    Image.new("RGB", (lado, lado), color).save(buffer, format="JPEG")
    buffer.seek(0)
    return buffer


@pytest.mark.parametrize("clase, esperado", [
    ("manzana_fresca", ("manzana", "fresca")),
    ("manzana_podrida", ("manzana", "podrida")),
    ("banano_fresco", ("banano", "fresca")),
    ("banano_podrido", ("banano", "podrida")),
])
def test_interpretar_clase(clase, esperado):
    assert interpretar_clase(clase) == esperado


def test_nombre_clase_legible():
    assert nombre_clase("guayaba_podrida") == "Guayaba podrida"


def test_prediccion_tiene_todos_los_campos(modelo):
    r = predecir(modelo, foto(), umbral=0.6)
    for campo in ("clase", "fruta", "estado", "probabilidad", "prob_podrida", "confiable",
                  "recomendacion", "ranking"):
        assert campo in r
    assert r["estado"] in ("fresca", "podrida")
    assert 0 <= r["probabilidad"] <= 1 and 0 <= r["prob_podrida"] <= 1
    assert len(r["ranking"]) == len(modelo.classes_)
    assert sum(p for _, p in r["ranking"]) == pytest.approx(1.0, abs=1e-6)


def test_imagen_muy_pequena_da_error(modelo):
    with pytest.raises(ValueError):
        predecir(modelo, foto(lado=20))


def test_umbral_fuera_de_rango_da_error(modelo):
    with pytest.raises(ValueError):
        predecir(modelo, foto(), umbral=1.5)


def _r(estado, confiable=True):
    return {"estado": estado, "confiable": confiable}


def test_resumen_de_lote_rechazado_y_perdida_en_pesos():
    lote = [_r("fresca"), _r("fresca"), _r("podrida"), _r("podrida", confiable=False)]
    resumen = resumir_lote(lote, peso_unitario_g=200, precio_kg=5000, tolerancia=0.10)
    assert resumen["frescas"] == 2
    assert resumen["podridas"] == 1
    assert resumen["revisar"] == 1
    assert resumen["perdida_estimada"] == pytest.approx(1000.0)
    assert resumen["aceptado"] is False


def test_resumen_de_lote_aceptado():
    lote = [_r("fresca")] * 9 + [_r("podrida")]
    assert resumir_lote(lote, 150, 4000, tolerancia=0.10)["aceptado"] is True


def test_resumen_de_lote_valida_datos():
    with pytest.raises(ValueError):
        resumir_lote([_r("fresca")], peso_unitario_g=0, precio_kg=1000, tolerancia=0.1)
