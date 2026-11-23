"""Evalua la deteccion de varias frutas con escenas armadas SOLO con fotos de PRUEBA.

No hay fotos reales con varias frutas etiquetadas, asi que se fabrican escenas: se toman fotos del
conjunto de prueba (que ningun modelo vio al entrenar), se recorta cada fruta con GrabCut (otro
algoritmo distinto al del detector) y se pegan, separadas, sobre un fondo claro liso con sombra
suave. Es una prueba mas dificil que una foto real en un aspecto (los bordes recortados) y mas
facil en otros (fondo perfectamente liso): sirve para comparar, no reemplaza probar con fotos propias.

Uso (desde la raiz; requiere opencv: pip install -r requirements-captura.txt):
    python -m src.evaluar_deteccion --escenas 40 --guardar escenas_prueba
Una deteccion cuenta como correcta si cae dentro de la caja de una foto de origen (algunas fotos
del dataset ya traen dos frutas y el detector debe separarlas).
"""
import argparse
import collections
import random
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageFilter

from src.detectar import cargar_modelo_deteccion, detectar_frutas, dibujar_detecciones, reducir, segmentar_frutas
from src.entrenar_deteccion import dividir_como_el_notebook
from src.predict import RAIZ, cargar_modelo, interpretar_clase
from src.preprocessing import listar_imagenes

FONDOS = [(236, 233, 226), (226, 233, 239), (241, 239, 231), (223, 228, 223), (232, 226, 232)]


def recorte_grabcut(ruta):
    """Fruta de una foto sobre fondo transparente, o None si la foto no tiene una sola fruta clara."""
    img = reducir(Image.open(ruta).convert("RGB"), 512)
    rgb = np.asarray(img)
    masks = segmentar_frutas(rgb, separar=False)
    if len(masks) != 1 or not 0.08 < masks[0].mean() < 0.75:
        return None
    m = masks[0]
    ys, xs = np.where(m)
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    rect = (max(int(x0) - 4, 1), max(int(y0) - 4, 1), int(x1 - x0) + 8, int(y1 - y0) + 8)
    gc = np.zeros(rgb.shape[:2], np.uint8)
    try:
        cv2.grabCut(cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR), gc, rect, np.zeros((1, 65)), np.zeros((1, 65)), 4,
                    cv2.GC_INIT_WITH_RECT)
    except cv2.error:
        return None
    fg = ((gc == 1) | (gc == 3)).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(fg)
    if n < 2:
        return None
    fg = (lab == 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])).astype(np.uint8)
    if not 0.5 * m.sum() < fg.sum() < 1.3 * m.sum():      # recorte dudoso
        return None
    ys, xs = np.where(fg)
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    alfa = Image.fromarray(fg[y0:y1, x0:x1] * 255).filter(ImageFilter.GaussianBlur(1.2))
    corte = img.crop((x0, y0, x1, y1)).convert("RGBA")
    corte.putalpha(alfa)
    return corte


def fondo_liso(ancho, alto, rng):
    base = np.array(rng.choice(FONDOS), float)
    gx, gy = np.linspace(-1, 1, ancho)[None, :, None], np.linspace(-1, 1, alto)[:, None, None]
    ruido = np.random.default_rng(rng.randint(0, 9999)).normal(0, 1.2, (alto, ancho, 1))
    return Image.fromarray(np.clip(base + 5 * gx + 4 * gy + ruido, 0, 255).astype(np.uint8)).convert("RGBA")


def armar_escena(cortes, rng, ancho=1400, alto=1000):
    """Pega los recortes sin que se toquen. Devuelve (imagen, [(caja, clase)])."""
    lienzo, sombra = fondo_liso(ancho, alto, rng), Image.new("RGBA", (ancho, alto), (0, 0, 0, 0))
    puestas, ocupado = [], []
    for corte, clase in cortes:
        esc = rng.randint(230, 330) / max(corte.size)
        c = corte.resize((max(1, int(corte.width * esc)), max(1, int(corte.height * esc))), Image.Resampling.LANCZOS)
        for _ in range(200):
            x, y = rng.randint(30, ancho - c.width - 30), rng.randint(30, alto - c.height - 30)
            caja = (x - 45, y - 45, x + c.width + 45, y + c.height + 45)
            if all(caja[2] < o[0] or caja[0] > o[2] or caja[3] < o[1] or caja[1] > o[3] for o in ocupado):
                break
        else:
            continue
        ocupado.append(caja)
        sm = Image.new("RGBA", c.size, (0, 0, 0, 0))
        sm.putalpha(c.getchannel("A").point(lambda v: int(v * 0.25)))
        sombra.alpha_composite(sm, (x + 8, y + 10))
        puestas.append(((x, y, x + c.width, y + c.height), clase, c))
    lienzo.alpha_composite(sombra.filter(ImageFilter.GaussianBlur(9)))
    for caja, _, c in puestas:
        lienzo.alpha_composite(c, (caja[0], caja[1]))
    return lienzo.convert("RGB"), [(caja, clase) for caja, clase, _ in puestas]


def dentro(c, t):
    """Fraccion del area de la caja c que cae dentro de la caja t."""
    x0, y0, x1, y1 = max(c[0], t[0]), max(c[1], t[1]), min(c[2], t[2]), min(c[3], t[3])
    return max(0, x1 - x0) * max(0, y1 - y0) / ((c[2] - c[0]) * (c[3] - c[1]))


def evaluar(modelo, escenas, umbral):
    tot = collections.Counter()
    for img, verdad in escenas:
        foto, dets = detectar_frutas(modelo, img, umbral=umbral)
        w = foto.size[0] / img.size[0]
        verdad = [([v * w for v in caja], clase) for caja, clase in verdad]
        halladas = set()
        tot["escenas"] += 1
        tot["detecciones"] += len(dets)
        tot["origenes"] += len(verdad)
        for d in dets:
            j = max(range(len(verdad)), key=lambda k: dentro(d.caja, verdad[k][0]))
            if dentro(d.caja, verdad[j][0]) < 0.7:
                tot["falsas"] += 1
                continue
            halladas.add(j)
            real = verdad[j][1]
            fruta, estado = interpretar_clase(real)
            r = d.resultado
            tot["ok"] += 1
            tot["clase"] += r["clase"] == real
            tot["fruta"] += r["fruta"] == fruta
            tot["estado"] += r["estado"] == estado
            tot["revisar"] += d.accion == "revisar"
            podrida = estado == "podrida"
            tot["podridas"] += podrida
            tot["podridas_marcadas"] += podrida and d.accion in ("descuento", "retirar")
            tot["podridas_normal"] += podrida and d.accion == "normal"
            tot["frescas"] += not podrida
            tot["frescas_marcadas"] += (not podrida) and d.accion in ("descuento", "retirar")
        tot["sin_detectar"] += len(verdad) - len(halladas)
    return tot


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--escenas", type=int, default=40)
    ap.add_argument("--semilla", type=int, default=7)
    ap.add_argument("--umbral", type=float, default=0.6, help="confianza minima de la clase")
    ap.add_argument("--guardar", help="carpeta donde guardar las escenas con las cajas dibujadas")
    args = ap.parse_args()

    registros = listar_imagenes(RAIZ / "data" / "raw")
    _, i_test, _ = dividir_como_el_notebook(registros)
    rng = random.Random(args.semilla)
    por_clase = collections.defaultdict(list)
    for i in i_test:
        por_clase[registros[i][1]].append(registros[i][0])
    banco = {}
    for clase, rutas in sorted(por_clase.items()):
        rng.shuffle(rutas)
        for ruta in rutas:
            if len(banco.get(clase, [])) >= 8:
                break
            corte = recorte_grabcut(ruta)
            if corte is not None:
                banco.setdefault(clase, []).append(corte)
    clases = sorted(banco)
    escenas = []
    for _ in range(args.escenas):
        elegidas = rng.sample(clases, rng.randint(3, 6))
        img, verdad = armar_escena([(rng.choice(banco[c]), c) for c in elegidas], rng)
        escenas.append((img, verdad))
    print(f"[INFO] {len(escenas)} escenas con fotos de prueba ({sum(len(v) for _, v in escenas)} cajas de origen)")

    modelos = {"modelo de deteccion (recortes)": cargar_modelo_deteccion()[0],
               "modelo original (fotos completas)": cargar_modelo()}
    for nombre, modelo in modelos.items():
        t = evaluar(modelo, escenas, args.umbral)
        n = t["ok"]
        print(f"\n== {nombre} ==")
        print(f"detecciones {t['detecciones']} | falsas {t['falsas']} | fotos de origen sin detectar {t['sin_detectar']}")
        print(f"sobre {n} detecciones correctas: 16 clases {t['clase'] / n:.1%} | fruta {t['fruta'] / n:.1%} | "
              f"fresca/podrida {t['estado'] / n:.1%} | a revisar a mano {t['revisar']}")
        print(f"podridas con descuento o retiro: {t['podridas_marcadas']}/{t['podridas']} | "
              f"podridas que pasaron como normales: {t['podridas_normal']} | "
              f"frescas marcadas por error: {t['frescas_marcadas']}/{t['frescas']}")
    if args.guardar:
        salida = Path(args.guardar)
        salida.mkdir(parents=True, exist_ok=True)
        for k, (img, _) in enumerate(escenas):
            foto, dets = detectar_frutas(modelos["modelo de deteccion (recortes)"], img, umbral=args.umbral)
            dibujar_detecciones(foto, dets).save(salida / f"escena_{k:02d}.jpg", quality=90)
        print(f"\n[OK] Escenas con cajas guardadas en {salida}/")


if __name__ == "__main__":
    main()
