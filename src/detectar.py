"""Deteccion de varias frutas en una misma foto y descuento por fruta podrida.

Idea: el SVM del proyecto clasifica UNA fruta por imagen. Para una foto con varias frutas
separadas sobre un fondo claro se hace lo siguiente, sin redes neuronales:
  1. Se estima el color del fondo con el borde de la foto (mediana en el espacio CIELAB).
  2. Todo pixel que se aleja del fondo es "fruta" (umbral de Otsu sobre la distancia de color).
     Las sombras casi no cambian el color, por eso pesan menos que la diferencia de tono.
  3. Morfologia (abrir, cerrar, rellenar huecos) y componentes conexos: cada mancha es una fruta.
     Si una mancha parece dos frutas pegadas (poco convexa), se separa con watershed.
  4. Cada fruta se recorta (cuadrado con margen), el fondo y las frutas vecinas se pintan de gris
     neutro para que el modelo vea solo la fruta, y se clasifica con el mismo modelo y las mismas caracteristicas de siempre (src/predict.py).
  5. Con la probabilidad de que la fruta este podrida se decide: normal, descuento o retirar.

Limitaciones: necesita fondo liso y claro y frutas que no se solapen mucho. Un fondo con
dibujos, frutas del mismo color del fondo o fotos con mucha sombra dura pueden fallar.
"""
from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps
from scipy import ndimage as ndi
from skimage import color, feature, filters, measure, morphology, segmentation

from src.predict import RAIZ, cargar_modelo, nombre_fruta, predecir
from src.preprocessing import cargar_imagen

RUTA_MODELO_DETECCION = RAIZ / "models" / "modelo_deteccion.pkl"
LADO_TRABAJO = 1024          # la foto se reduce a este lado mayor antes de analizarla
PESO_LUMINOSIDAD = 0.5       # las sombras cambian la luz, no el tono: pesan la mitad que el color
UMBRAL_DIST_MIN, UMBRAL_DIST_MAX = 9.0, 35.0   # limites del umbral de Otsu (distancia CIELAB)
AREA_MINIMA = 0.003          # una mancha menor a esta fraccion de la foto se descarta como ruido
MARGEN_RECORTE = 0.12        # margen alrededor de cada fruta al recortarla
FONDO_NEUTRO = (235, 235, 235)  # color con el que se reemplaza todo lo que no es la fruta en el recorte
SOLIDEZ_SEPARAR = 0.95       # por debajo, la mancha se intenta separar en frutas pegadas
CUELLO_MAXIMO = 0.75         # dos frutas pegadas solo se separan si el cuello mide < 75 % de la menor

UMBRAL_DESCUENTO = 0.40      # probabilidad de podrida desde la cual la fruta lleva descuento
UMBRAL_RETIRO = 0.80         # desde aqui no se vende: se retira del exhibidor
DESCUENTO_DEFECTO = 0.30     # descuento sugerido (fraccion del precio)

# Precios de ejemplo en pesos colombianos por unidad; la app permite editarlos.
PRECIO_UNIDAD_EJEMPLO = {"manzana": 1500, "banano": 600, "naranja": 800, "guayaba": 1000,
                         "fresa": 700, "uva": 2500, "granada": 2500, "azufaifa": 500}

ACCIONES = ("normal", "descuento", "retirar", "revisar")
COLORES_ACCION = {"normal": (46, 158, 91), "descuento": (230, 140, 20),
                  "retirar": (200, 40, 40), "revisar": (110, 110, 110)}


@dataclass
class Deteccion:
    """Una fruta encontrada en la foto."""
    caja: tuple            # (x0, y0, x1, y1) sobre la imagen de trabajo
    area: int              # pixeles de la mancha
    recorte: Image.Image   # recorte cuadrado que se le entrego al modelo
    resultado: dict        # salida de predecir()
    accion: str = "normal"  # normal | descuento | retirar | revisar


def cargar_modelo_deteccion():
    """Carga models/modelo_deteccion.pkl (entrenado con recortes). Devuelve (modelo, es_especifico).

    Si ese archivo no existe usa models/modelo.pkl y es_especifico=False: funciona, pero con
    menos precision porque ese modelo se entreno con fotos completas y no con recortes.
    """
    if RUTA_MODELO_DETECCION.exists():
        return cargar_modelo(RUTA_MODELO_DETECCION), True
    return cargar_modelo(), False


# --------------------------------------------------------------------------- segmentacion
def reducir(imagen, lado=LADO_TRABAJO):
    """Imagen RGB con orientacion corregida y lado mayor de, como maximo, `lado` pixeles."""
    imagen = cargar_imagen(imagen)
    if max(imagen.size) > lado:
        imagen = imagen.copy()
        imagen.thumbnail((lado, lado), Image.Resampling.LANCZOS)
    return imagen


def color_de_fondo(lab):
    """Mediana CIELAB del borde de la foto (3 % del lado menor)."""
    alto, ancho = lab.shape[:2]
    b = max(2, int(0.03 * min(alto, ancho)))
    borde = np.concatenate([lab[:b].reshape(-1, 3), lab[-b:].reshape(-1, 3),
                            lab[:, :b].reshape(-1, 3), lab[:, -b:].reshape(-1, 3)])
    return np.median(borde, axis=0)


def mascara_primer_plano(rgb):
    """Mascara booleana: True donde hay fruta (todo lo que se aleja del color del fondo)."""
    lab = color.rgb2lab(rgb)
    d = lab - color_de_fondo(lab)
    distancia = np.sqrt((PESO_LUMINOSIDAD * d[..., 0]) ** 2 + d[..., 1] ** 2 + d[..., 2] ** 2)
    distancia = filters.gaussian(distancia, sigma=1.5)
    if distancia.max() - distancia.min() < 1e-3:
        return np.zeros(distancia.shape, dtype=bool)
    umbral = float(np.clip(filters.threshold_otsu(distancia), UMBRAL_DIST_MIN, UMBRAL_DIST_MAX))
    mascara = distancia > umbral
    escala = min(rgb.shape[:2]) / 400
    radio = max(1, int(round(2 * escala)))
    mascara = morphology.binary_opening(mascara, morphology.disk(radio))
    mascara = morphology.binary_closing(mascara, morphology.disk(2 * radio))
    return ndi.binary_fill_holes(mascara)


def separar_pegadas(mascara_region):
    """Divide una mancha formada por frutas pegadas usando la transformada de distancia.

    Solo separa si entre cada par de frutas vecinas hay un cuello claro (mas angosto que
    CUELLO_MAXIMO veces la fruta menor); asi una fruta alargada o curva, como un banano, no
    se parte en dos.
    """
    dist = ndi.distance_transform_edt(mascara_region)
    dist = filters.gaussian(dist, sigma=2)
    picos = feature.peak_local_max(dist, min_distance=max(8, int(0.35 * dist.max())),
                                   threshold_abs=0.45 * dist.max(), labels=mascara_region.astype(int))
    if len(picos) < 2:
        return [mascara_region]
    marcadores = np.zeros(mascara_region.shape, dtype=int)
    for k, (f, c) in enumerate(picos, 1):
        marcadores[f, c] = k
    partes = segmentation.watershed(-dist, marcadores, mask=mascara_region)
    area = mascara_region.sum()
    resultado = [partes == k for k in range(1, len(picos) + 1)]
    # Si alguna parte es diminuta, la separacion no es confiable: se deja la mancha entera.
    if any(p.sum() < 0.15 * area for p in resultado):
        return [mascara_region]
    cuadro = np.ones((3, 3), dtype=bool)
    for a in range(len(resultado)):
        for b in range(a + 1, len(resultado)):
            frontera = (morphology.binary_dilation(resultado[a], cuadro) & resultado[b]) | \
                       (morphology.binary_dilation(resultado[b], cuadro) & resultado[a])
            if not frontera.any():
                continue          # no son vecinas
            cuello = dist[frontera].max()
            menor = min(dist[tuple(picos[a])], dist[tuple(picos[b])])
            if cuello >= CUELLO_MAXIMO * menor:
                return [mascara_region]
    return resultado


def segmentar_frutas(rgb, separar=True):
    """Lista de mascaras booleanas, una por fruta, ordenadas de izquierda a derecha."""
    mascara = mascara_primer_plano(rgb)
    etiquetas = measure.label(mascara)
    area_min = AREA_MINIMA * mascara.size
    frutas = []
    for region in measure.regionprops(etiquetas):
        if region.area < area_min:
            continue
        propia = etiquetas == region.label
        if separar and region.solidity < SOLIDEZ_SEPARAR:
            frutas.extend(p for p in separar_pegadas(propia) if p.sum() >= area_min)
        else:
            frutas.append(propia)
    caja = lambda m: np.where(m.any(axis=0))[0][0]
    return sorted(frutas, key=caja)


# ------------------------------------------------------------------------------ recortes
def recortar_fruta(imagen, mascara, otras, fondo, margen=MARGEN_RECORTE, aislar_fondo=True):
    """Recorte cuadrado de una fruta.

    Con aislar_fondo=True (lo que usa el modelo de deteccion) todo lo que no es la fruta se pinta
    de gris neutro: el modelo ve solo la fruta, sin depender del color, la textura ni las sombras
    del fondo. Con False solo se borran las frutas vecinas y se conserva el fondo real.

    imagen: PIL RGB | mascara: la fruta | otras: mascara de todas las frutas | fondo: color RGB.
    Devuelve (recorte PIL cuadrado, caja (x0, y0, x1, y1)).
    """
    ys, xs = np.where(mascara)
    x0, x1, y0, y1 = int(xs.min()), int(xs.max()) + 1, int(ys.min()), int(ys.max()) + 1
    arr = np.asarray(imagen).copy()
    if aislar_fondo:
        propia = morphology.binary_dilation(mascara, morphology.disk(2))   # conserva el borde de la fruta
        arr[~propia] = FONDO_NEUTRO
        fondo = FONDO_NEUTRO
    elif otras is not None and otras.any():
        vecinas = morphology.binary_dilation(otras & ~mascara, morphology.disk(3))
        arr[vecinas & ~mascara] = fondo
    lado = int(max(x1 - x0, y1 - y0) * (1 + 2 * margen))
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    ix0, iy0 = cx - lado // 2, cy - lado // 2
    lienzo = Image.new("RGB", (lado, lado), tuple(int(v) for v in fondo))
    sx0, sy0 = max(ix0, 0), max(iy0, 0)
    sx1, sy1 = min(ix0 + lado, arr.shape[1]), min(iy0 + lado, arr.shape[0])
    lienzo.paste(Image.fromarray(arr[sy0:sy1, sx0:sx1]), (sx0 - ix0, sy0 - iy0))
    return lienzo, (x0, y0, x1, y1)


# ------------------------------------------------------------------------------ decision
def decidir_accion(prob_podrida, umbral_descuento=UMBRAL_DESCUENTO, umbral_retiro=UMBRAL_RETIRO):
    """normal | descuento | retirar segun la probabilidad de que la fruta este podrida."""
    if not 0 <= umbral_descuento <= umbral_retiro <= 1:
        raise ValueError("Los umbrales deben cumplir 0 <= descuento <= retiro <= 1.")
    if prob_podrida >= umbral_retiro:
        return "retirar"
    if prob_podrida >= umbral_descuento:
        return "descuento"
    return "normal"


def extraer_recortes(imagen, separar=True):
    """Segmenta la foto y devuelve (imagen_de_trabajo, [(recorte, caja, area), ...]).

    Es el paso que comparten la app y el entrenamiento de models/modelo_deteccion.pkl, para que
    el modelo vea en uso el mismo tipo de recorte con el que aprendio.
    """
    foto = reducir(imagen)
    rgb = np.asarray(foto)
    masks = segmentar_frutas(rgb, separar=separar)
    if not masks:
        return foto, []
    fondo = np.round(color.lab2rgb(color_de_fondo(color.rgb2lab(rgb))[None, None, :])[0, 0] * 255)
    todas = np.logical_or.reduce(masks)
    recortes = []
    for m in masks:
        recorte, caja = recortar_fruta(foto, m, todas, fondo)
        recortes.append((recorte, caja, int(m.sum())))
    return foto, recortes


def detectar_frutas(modelo, imagen, umbral=0.5, umbral_descuento=UMBRAL_DESCUENTO,
                    umbral_retiro=UMBRAL_RETIRO, separar=True):
    """Encuentra cada fruta de la foto, la clasifica y decide su accion.

    Devuelve (imagen_de_trabajo, [Deteccion, ...]) con las frutas de izquierda a derecha.
    Si la clase mas probable queda por debajo de `umbral` de confianza (no se sabe cual fruta es),
    se marca "revisar", salvo que ya sea claramente podrida: esa se retira.
    """
    foto, recortes = extraer_recortes(imagen, separar=separar)
    detecciones = []
    for recorte, caja, area in recortes:
        r = predecir(modelo, recorte, umbral=umbral)
        accion = decidir_accion(r["prob_podrida"], umbral_descuento, umbral_retiro)
        # Si no hay seguridad sobre QUE fruta es, no se puede poner precio: se pide revisar a mano.
        # Retirar no necesita saber cual fruta es, asi que esa decision se mantiene.
        if accion != "retirar" and not r["confiable"]:
            accion = "revisar"
        detecciones.append(Deteccion(caja=caja, area=area, recorte=recorte, resultado=r, accion=accion))
    return foto, detecciones


# ---------------------------------------------------------------------------- resultados
def resumir_escena(detecciones, precios, descuento=DESCUENTO_DEFECTO):
    """Totales de la foto: conteos por accion y valor sin descuento y con descuento.

    precios: {fruta: precio por unidad}. Las frutas a "retirar" o "revisar" no suman al total.
    """
    if not 0 <= descuento <= 1:
        raise ValueError("El descuento debe estar entre 0 y 1.")
    conteo = {a: 0 for a in ACCIONES}
    sin_descuento = con_descuento = 0.0
    for d in detecciones:
        conteo[d.accion] += 1
        precio = precios.get(d.resultado["fruta"], 0)
        if d.accion == "normal":
            sin_descuento += precio
            con_descuento += precio
        elif d.accion == "descuento":
            sin_descuento += precio
            con_descuento += precio * (1 - descuento)
    return {"total": len(detecciones), **conteo, "valor_sin_descuento": sin_descuento,
            "valor_con_descuento": con_descuento, "descuento_total": sin_descuento - con_descuento}


def precio_final(d, precios, descuento=DESCUENTO_DEFECTO):
    """Precio que se cobra por una fruta (None si no se vende o hay que revisarla)."""
    precio = precios.get(d.resultado["fruta"], 0)
    if d.accion == "normal":
        return precio
    if d.accion == "descuento":
        return precio * (1 - descuento)
    return None


def dibujar_detecciones(foto, detecciones):
    """Copia de la foto con una caja por fruta (color segun la accion) y su numero."""
    lienzo = foto.copy()
    pincel = ImageDraw.Draw(lienzo)
    grosor = max(3, min(lienzo.size) // 200)
    tamano = max(14, min(lienzo.size) // 28)
    try:
        fuente = ImageFont.load_default(size=tamano)
    except TypeError:  # Pillow antiguo sin tamano
        fuente = ImageFont.load_default()
    for i, d in enumerate(detecciones, 1):
        c = COLORES_ACCION[d.accion]
        pincel.rectangle(d.caja, outline=c, width=grosor)
        etiqueta = f"{i} {nombre_fruta(d.resultado['fruta'])} {d.resultado['prob_podrida']:.0%}"
        x0, y0 = d.caja[0], d.caja[1]
        ancho = pincel.textlength(etiqueta, font=fuente)
        arriba = max(0, y0 - tamano - 6)
        pincel.rectangle((x0, arriba, x0 + ancho + 8, arriba + tamano + 6), fill=c)
        pincel.text((x0 + 4, arriba + 2), etiqueta, fill="white", font=fuente)
    return lienzo
