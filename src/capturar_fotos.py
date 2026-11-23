"""Toma fotos propias de fruta con la camara del computador para ampliar el dataset.

Uso (desde la raiz del repositorio):
    python src/capturar_fotos.py --clase manzana_fresca
    python src/capturar_fotos.py --clase banano_podrido --n 120

Controles de la ventana:
    ESPACIO  empieza / pausa la rafaga de fotos
    q        termina

Use el formato <fruta>_<estado> de data/raw (por ejemplo guayaba_podrida). Mientras captura, gire la fruta,
acerquela y alejela y cambie un poco la luz. Las fotos se guardan en
data/raw/<clase>/ como JPG de 256 x 256 (recorte cuadrado central).
Requiere opencv-python (ver requirements-captura.txt).
"""
import argparse
import time
from pathlib import Path

import cv2

RAIZ = Path(__file__).resolve().parents[1]


def recorte_cuadrado(frame):
    alto, ancho = frame.shape[:2]
    lado = min(alto, ancho)
    y0, x0 = (alto - lado) // 2, (ancho - lado) // 2
    return frame[y0:y0 + lado, x0:x0 + lado]


def main():
    parser = argparse.ArgumentParser(description="Captura de fotos para el dataset")
    parser.add_argument("--clase", required=True, help="Clase <fruta>_<estado>, ej. manzana_fresca")
    parser.add_argument("--n", type=int, default=120, help="Cantidad de fotos a tomar")
    parser.add_argument("--intervalo", type=float, default=0.25, help="Segundos entre fotos")
    parser.add_argument("--camara", type=int, default=0, help="Indice de la camara")
    args = parser.parse_args()

    destino = RAIZ / "data" / "raw" / args.clase.strip().lower().replace(" ", "_")
    destino.mkdir(parents=True, exist_ok=True)
    existentes = len(list(destino.glob("*.jpg")))

    camara = cv2.VideoCapture(args.camara)
    if not camara.isOpened():
        raise SystemExit("[ERROR] No se pudo abrir la camara. Pruebe con --camara 1")

    print(f"[INFO] Guardando en {destino} ({existentes} fotos previas). ESPACIO = iniciar/pausar, q = salir")
    capturando, tomadas, ultima = False, 0, 0.0
    while tomadas < args.n:
        ok, frame = camara.read()
        if not ok:
            print("[ERROR] La camara no entrego imagen")
            break
        cuadro = recorte_cuadrado(frame)
        vista = cuadro.copy()
        estado = "CAPTURANDO" if capturando else "PAUSA (ESPACIO)"
        cv2.putText(vista, f"{args.clase}: {tomadas}/{args.n}  {estado}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255) if capturando else (0, 200, 0), 2)
        cv2.imshow("Captura de dataset", vista)

        ahora = time.time()
        if capturando and ahora - ultima >= args.intervalo:
            nombre = destino / f"{args.clase}_{existentes + tomadas + 1:04d}.jpg"
            cv2.imwrite(str(nombre), cv2.resize(cuadro, (256, 256)), [cv2.IMWRITE_JPEG_QUALITY, 90])
            tomadas += 1
            ultima = ahora

        tecla = cv2.waitKey(1) & 0xFF
        if tecla == ord(" "):
            capturando = not capturando
        elif tecla == ord("q"):
            break

    camara.release()
    cv2.destroyAllWindows()
    print(f"[OK] {tomadas} fotos nuevas en {destino} (total {existentes + tomadas})")


if __name__ == "__main__":
    main()
