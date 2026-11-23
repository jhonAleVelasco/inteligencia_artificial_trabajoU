"""Prepara data/raw/ a partir del dataset "Fresh and Rotten Fruits" (Mendeley Data).

Fuente: N. Sultana, M. Jahan y M. S. Uddin, "Fresh and Rotten Fruits Dataset for Machine-Based
Evaluation of Fruit Quality", Mendeley Data, v1, 2022. doi: 10.17632/bdd69gyhv8.1 (CC BY 4.0).

Pasos:
  1. Descargar "Original Image.zip" desde https://data.mendeley.com/datasets/bdd69gyhv8/1
     y descomprimirlo en cualquier carpeta.
  2. Ejecutar desde la raiz del repositorio:
        python src/preparar_datos.py --origen "RUTA/A/Original Image"

El script recorre las carpetas del dataset (FreshApple, RottenBanana, ...), traduce cada clase
al formato <fruta>_<estado> en espanol y guarda cada foto en data/raw/<clase>/ reducida a
256 pixeles por el lado corto (JPG calidad 90). Asi el repositorio queda liviano y el modelo
recibe el mismo tipo de imagen que en la aplicacion. Solo se usan las imagenes originales:
las aumentadas del dataset no se usan, porque el aumento se hace en el notebook y solo
sobre el entrenamiento.
"""
import argparse
import re
import shutil
from pathlib import Path

from PIL import Image, ImageOps

RAIZ = Path(__file__).resolve().parents[1]
LADO_CORTO = 256
EXTENSIONES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

FRUTAS = {
    "apple": ("manzana", "a"),
    "banana": ("banano", "o"),
    "orange": ("naranja", "a"),
    "guava": ("guayaba", "a"),
    "strawberry": ("fresa", "a"),
    "grape": ("uva", "a"),
    "pomegranate": ("granada", "a"),
    "jujube": ("azufaifa", "a"),
}


def traducir_clase(nombre_carpeta):
    """'FreshApple' / 'Rotten Banana' / 'fresh_apple' -> 'manzana_fresca' / 'banano_podrido'."""
    texto = re.sub(r"[^a-z]", "", nombre_carpeta.lower())
    if texto.startswith("fresh"):
        estado, resto = "fresc", texto[len("fresh"):]
    elif texto.startswith("rotten"):
        estado, resto = "podrid", texto[len("rotten"):]
    else:
        return None
    for ingles, (espanol, genero) in FRUTAS.items():
        if resto.startswith(ingles):
            return f"{espanol}_{estado}{genero}"
    return None


def reducir(ruta_origen, ruta_destino):
    with Image.open(ruta_origen) as img:
        img = ImageOps.exif_transpose(img).convert("RGB")
        escala = LADO_CORTO / min(img.size)
        if escala < 1:
            nuevo = (round(img.width * escala), round(img.height * escala))
            img = img.resize(nuevo, Image.Resampling.LANCZOS)
        img.save(ruta_destino, "JPEG", quality=90)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--origen", required=True, help="carpeta descomprimida de 'Original Image'")
    parser.add_argument("--destino", default=str(RAIZ / "data" / "raw"))
    parser.add_argument("--frutas", nargs="*", default=None,
                        help="limitar a estas frutas en espanol (por ejemplo: manzana banano naranja)")
    parser.add_argument("--limpiar", action="store_true", help="borrar data/raw/<clase> antes de copiar")
    args = parser.parse_args()

    origen, destino = Path(args.origen), Path(args.destino)
    if not origen.is_dir():
        raise SystemExit(f"[ERROR] No existe la carpeta de origen: {origen}")

    carpetas = {}
    for carpeta in sorted(p for p in origen.rglob("*") if p.is_dir()):
        clase = traducir_clase(carpeta.name)
        if clase and (args.frutas is None or clase.rpartition("_")[0] in args.frutas):
            carpetas.setdefault(clase, []).append(carpeta)
    if not carpetas:
        raise SystemExit("[ERROR] No se encontraron carpetas tipo FreshApple / RottenApple en el origen.")

    total, fallidas = 0, 0
    for clase, lista in sorted(carpetas.items()):
        salida = destino / clase
        if args.limpiar and salida.exists():
            shutil.rmtree(salida)
        salida.mkdir(parents=True, exist_ok=True)
        rutas = sorted(r for c in lista for r in c.rglob("*") if r.suffix.lower() in EXTENSIONES)
        n = 0
        for ruta in rutas:
            try:
                reducir(ruta, salida / f"{clase}_{n:04d}.jpg")
                n += 1
            except Exception as error:  # foto corrupta: se reporta y se sigue
                fallidas += 1
                print(f"[WARN] No se pudo procesar {ruta.name}: {error}")
        total += n
        print(f"[OK] {clase}: {n} fotos")
    print(f"[OK] {total} fotos guardadas en {destino} ({fallidas} con error)")


if __name__ == "__main__":
    main()
