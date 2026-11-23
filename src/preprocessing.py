"""Preprocesamiento de imagenes y extraccion de caracteristicas.

Cada imagen se convierte en un vector numerico que el SVM puede usar:
  1. Se corrige la orientacion (EXIF), se recorta al cuadrado central y se reduce a 128 x 128.
  2. Color: histogramas normalizados de los canales H, S y V (32 valores).
  3. Textura: histograma LBP uniforme (10 valores); capta manchas y moho de la cascara.
  4. Forma: descriptor HOG (Histograma de Gradientes Orientados) en escala de grises (1.764 valores).

El mismo codigo se usa en el notebook de entrenamiento y en la aplicacion, asi el modelo
recibe siempre las caracteristicas calculadas de la misma forma.
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps
from skimage.feature import hog, local_binary_pattern

TAMANO = 128                      # lado de la imagen cuadrada (pixeles)
BINS_H, BINS_S, BINS_V = 16, 8, 8  # barras de los histogramas de color
LBP_PUNTOS, LBP_RADIO = 8, 1       # textura: 8 vecinos a 1 pixel de distancia (10 barras)
HOG_ORIENTACIONES = 9
HOG_PIXELES_CELDA = (16, 16)
HOG_CELDAS_BLOQUE = (2, 2)
EXTENSIONES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def cargar_imagen(origen):
    """Abre una imagen desde una ruta, un archivo en memoria o un objeto PIL y la devuelve en RGB."""
    try:
        imagen = origen if isinstance(origen, Image.Image) else Image.open(origen)
        imagen = ImageOps.exif_transpose(imagen)
        return imagen.convert("RGB")
    except Exception as error:  # archivo corrupto o formato no soportado
        raise ValueError("el archivo no es una imagen válida o está dañado.") from error


def normalizar_imagen(imagen, tamano=TAMANO):
    """Recorta el cuadrado central y lo reduce a tamano x tamano."""
    ancho, alto = imagen.size
    lado = min(ancho, alto)
    izquierda, arriba = (ancho - lado) // 2, (alto - lado) // 2
    cuadrada = imagen.crop((izquierda, arriba, izquierda + lado, arriba + lado))
    return cuadrada.resize((tamano, tamano), Image.Resampling.BILINEAR)


def caracteristicas_color(imagen):
    """Histogramas de tono (H), saturacion (S) y brillo (V); cada uno suma 1."""
    hsv = np.asarray(imagen.convert("HSV"))
    partes = []
    for canal, bins in zip(range(3), (BINS_H, BINS_S, BINS_V)):
        conteo, _ = np.histogram(hsv[:, :, canal], bins=bins, range=(0, 256))
        partes.append(conteo / conteo.sum())
    return np.concatenate(partes)


def caracteristicas_forma(imagen):
    """Descriptor HOG: direccion de los bordes en cada zona de la imagen."""
    gris = np.asarray(imagen.convert("L"), dtype=np.float32) / 255.0
    return hog(gris, orientations=HOG_ORIENTACIONES, pixels_per_cell=HOG_PIXELES_CELDA,
               cells_per_block=HOG_CELDAS_BLOQUE, block_norm="L2-Hys", feature_vector=True)


def caracteristicas_textura(imagen):
    """Histograma LBP uniforme: describe la textura de la cascara.

    Las zonas podridas tienen manchas, arrugas y moho que cambian la textura local aunque el
    color general se parezca. LBP compara cada pixel con sus 8 vecinos y cuenta los patrones.
    """
    gris = np.asarray(imagen.convert("L"))
    lbp = local_binary_pattern(gris, LBP_PUNTOS, LBP_RADIO, method="uniform")
    conteo, _ = np.histogram(lbp, bins=LBP_PUNTOS + 2, range=(0, LBP_PUNTOS + 2))
    return conteo / conteo.sum()


def extraer_caracteristicas(imagen):
    """Vector final de una imagen ya cargada: color + textura + forma."""
    normal = normalizar_imagen(imagen)
    return np.concatenate([caracteristicas_color(normal), caracteristicas_textura(normal),
                           caracteristicas_forma(normal)]).astype(np.float32)


def nombres_caracteristicas():
    """Nombres de cada columna del vector, en el mismo orden de extraer_caracteristicas."""
    color = ([f"h_{i}" for i in range(BINS_H)] + [f"s_{i}" for i in range(BINS_S)]
             + [f"v_{i}" for i in range(BINS_V)])
    textura = [f"lbp_{i}" for i in range(LBP_PUNTOS + 2)]
    n_hog = caracteristicas_forma(Image.new("RGB", (TAMANO, TAMANO))).size
    return color + textura + [f"hog_{i}" for i in range(n_hog)]


def listar_imagenes(carpeta_raw):
    """Devuelve [(ruta, clase)] leyendo data/raw/<clase>/<imagen>."""
    carpeta_raw = Path(carpeta_raw)
    registros = []
    for carpeta_clase in sorted(p for p in carpeta_raw.iterdir() if p.is_dir()):
        for ruta in sorted(carpeta_clase.iterdir()):
            if ruta.suffix.lower() in EXTENSIONES:
                registros.append((ruta, carpeta_clase.name))
    return registros
