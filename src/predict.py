"""Carga del modelo serializado y prediccion de la calidad de una fruta.

Las clases del modelo tienen la forma <fruta>_<estado>, por ejemplo "manzana_fresca" o
"banano_podrido". Este modulo traduce esa clase a algo util para el tendero: que fruta es,
si esta apta para la venta y que hacer con ella.
"""
import json
from pathlib import Path

import joblib
import numpy as np

from src.preprocessing import cargar_imagen, extraer_caracteristicas

RAIZ = Path(__file__).resolve().parents[1]
RUTA_MODELO = RAIZ / "models" / "modelo.pkl"
RUTA_METADATOS = RAIZ / "models" / "metadata.json"
LADO_MINIMO = 32

NOMBRES_FRUTA = {
    "manzana": "Manzana",
    "banano": "Banano",
    "naranja": "Naranja",
    "guayaba": "Guayaba",
    "fresa": "Fresa",
    "uva": "Uva",
    "granada": "Granada",
    "azufaifa": "Azufaifa",
}

RECOMENDACIONES = {
    "fresca": "Apta para la venta. Mantenerla en exhibición y revisarla de nuevo en 1 o 2 días.",
    "podrida": ("Retirar ya del exhibidor: el moho y el etileno aceleran el daño de las frutas vecinas. "
                "No venderla; destinarla a compost o alimento animal."),
}


def cargar_modelo(ruta=RUTA_MODELO):
    """Carga el pipeline entrenado (StandardScaler + SVC)."""
    ruta = Path(ruta)
    if not ruta.exists():
        raise FileNotFoundError(f"No existe el modelo en {ruta}. Ejecute primero notebooks/01_training.ipynb.")
    return joblib.load(ruta)


def cargar_metadatos(ruta=RUTA_METADATOS):
    """Clases, metricas y parametros guardados al entrenar (vacio si no existe)."""
    ruta = Path(ruta)
    return json.loads(ruta.read_text(encoding="utf-8")) if ruta.exists() else {}


def interpretar_clase(clase):
    """Separa la clase del modelo en fruta y estado: 'banano_podrido' -> ('banano', 'podrida')."""
    fruta, _, estado = str(clase).rpartition("_")
    estado = "podrida" if estado.startswith("podrid") else "fresca"
    return fruta or str(clase), estado


def nombre_fruta(fruta):
    return NOMBRES_FRUTA.get(fruta, fruta.replace("_", " ").capitalize())


def nombre_clase(clase):
    """Texto legible de una clase: 'manzana_podrida' -> 'Manzana podrida'."""
    fruta, estado = interpretar_clase(clase)
    masculino = fruta == "banano"   # concuerda el genero: banano fresco / podrido, manzana fresca / podrida
    palabra = ("podrido" if masculino else "podrida") if estado == "podrida" else ("fresco" if masculino else "fresca")
    return f"{nombre_fruta(fruta)} {palabra}"


def predecir(modelo, origen_imagen, umbral=0.5):
    """Clasifica una imagen.

    Devuelve un diccionario con la clase mas probable, la fruta, el estado, la probabilidad,
    la probabilidad total de que este podrida, si la prediccion supera el umbral, la
    recomendacion para el tendero y el ranking de todas las clases.
    """
    if not 0 <= umbral <= 1:
        raise ValueError("El umbral debe estar entre 0 y 1.")
    imagen = cargar_imagen(origen_imagen)
    if min(imagen.size) < LADO_MINIMO:
        raise ValueError(f"la imagen es demasiado pequeña (mínimo {LADO_MINIMO} x {LADO_MINIMO} píxeles).")
    vector = extraer_caracteristicas(imagen).reshape(1, -1)
    probabilidades = modelo.predict_proba(vector)[0]
    clases = [str(c) for c in modelo.classes_]
    orden = np.argsort(probabilidades)[::-1]
    mejor = clases[orden[0]]
    fruta, estado = interpretar_clase(mejor)
    prob_podrida = float(sum(p for c, p in zip(clases, probabilidades) if interpretar_clase(c)[1] == "podrida"))
    return {
        "clase": mejor,
        "fruta": fruta,
        "estado": estado,
        "probabilidad": float(probabilidades[orden[0]]),
        "prob_podrida": prob_podrida,
        "confiable": bool(probabilidades[orden[0]] >= umbral),
        "recomendacion": RECOMENDACIONES[estado],
        "ranking": [(clases[i], float(probabilidades[i])) for i in orden],
    }


def resumir_lote(resultados, peso_unitario_g, precio_kg, tolerancia):
    """Resume la inspeccion de un lote de frutas.

    resultados: lista de diccionarios de predecir() (solo imagenes validas).
    Devuelve conteos, porcentaje de podridas, perdida estimada en pesos y si el lote se acepta
    (porcentaje de podridas <= tolerancia). Las predicciones por debajo del umbral se cuentan
    aparte como 'revisar a mano' y no entran en el porcentaje.
    """
    if peso_unitario_g <= 0 or precio_kg < 0:
        raise ValueError("El peso por fruta debe ser mayor que 0 y el precio no puede ser negativo.")
    seguras = [r for r in resultados if r["confiable"]]
    podridas = sum(r["estado"] == "podrida" for r in seguras)
    frescas = len(seguras) - podridas
    revisar = len(resultados) - len(seguras)
    porcentaje = podridas / len(seguras) if seguras else 0.0
    perdida = podridas * peso_unitario_g / 1000 * precio_kg
    return {
        "total": len(resultados),
        "frescas": frescas,
        "podridas": podridas,
        "revisar": revisar,
        "porcentaje_podridas": porcentaje,
        "perdida_estimada": perdida,
        "aceptado": bool(seguras) and porcentaje <= tolerancia,
    }
