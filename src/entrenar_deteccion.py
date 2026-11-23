"""Entrena models/modelo_deteccion.pkl: el mismo SVM del proyecto, pero aprendido con RECORTES.

Por que hace falta: models/modelo.pkl se entreno con fotos completas, donde la fruta casi siempre
llena el cuadro. Al detectar varias frutas en una foto, la app recorta cada una con
src/detectar.py y el recorte se ve distinto (otro encuadre, fondo plano en los bordes, vecinas
borradas). Un modelo entrenado con fotos completas pierde mucha precision con esos recortes.
Aqui el SVM aprende con los mismos recortes que va a ver en uso.

Se usa la MISMA division entrenamiento/prueba del notebook (grupos de casi duplicados por dHash,
semilla 42): ningun recorte de prueba viene de una foto vista al entrenar.

Uso (desde la raiz del repositorio):
    python -m src.entrenar_deteccion              # hiperparametros de models/metadata.json
    python -m src.entrenar_deteccion --buscar     # ademas busca C y gamma con validacion cruzada
"""
import argparse
import hashlib
import json
import time
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import sklearn
from PIL import ImageOps
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import GridSearchCV, StratifiedGroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from src.detectar import RUTA_MODELO_DETECCION, extraer_recortes
from src.predict import RAIZ, cargar_modelo, interpretar_clase
from src.preprocessing import (cargar_imagen, extraer_caracteristicas, listar_imagenes,
                               normalizar_imagen)

SEMILLA = 42
MIN_AREA_RECORTE = 0.04      # un recorte debe cubrir al menos 4 % de la foto (descarta ruido y fragmentos)
MAX_RECORTES_FOTO = 4        # de una foto con muchas frutas iguales se usan las 4 mas grandes
RUTA_MODELO_DET = RUTA_MODELO_DETECCION
RUTA_META_DET = RAIZ / "models" / "metadata_deteccion.json"


def dividir_como_el_notebook(registros):
    """Reproduce la division 80/20 del notebook. Devuelve (indices_train, indices_test, grupos)."""
    rutas = [r for r, _ in registros]
    clases = np.array([c for _, c in registros])
    hashes = [hashlib.md5(r.read_bytes()).hexdigest() for r in rutas]

    def dhash(ruta, lado=8):
        g = np.asarray(normalizar_imagen(cargar_imagen(ruta)).convert("L").resize((lado + 1, lado)),
                       dtype=np.int16)
        return (g[:, 1:] > g[:, :-1]).flatten()

    huellas = np.array([dhash(r) for r in rutas])
    padre = list(range(len(rutas)))

    def raiz(i):
        while padre[i] != i:
            padre[i] = padre[padre[i]]
            i = padre[i]
        return i

    for clase in np.unique(clases):
        idx = np.where(clases == clase)[0]
        h = huellas[idx]
        d = (h[:, None, :] != h[None, :, :]).sum(axis=2)
        for a, b in zip(*np.where(np.triu(d <= 6, k=1))):
            padre[raiz(idx[a])] = raiz(idx[b])
    grupos = np.array([f"g{raiz(i)}" for i in range(len(rutas))])

    vistos, conservar = set(), []
    for i, h in enumerate(hashes):
        if h not in vistos:
            conservar.append(i)
        vistos.add(h)
    conservar = np.array(conservar)
    division = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=SEMILLA)
    i_train, i_test = next(division.split(np.zeros(len(conservar)), clases[conservar], groups=grupos[conservar]))
    return conservar[i_train], conservar[i_test], grupos


def recortes_de_foto(ruta):
    """Recortes (PIL) que el detector sacaria de una foto del dataset, los mas grandes primero."""
    foto, recortes = extraer_recortes(ruta)
    area_foto = foto.size[0] * foto.size[1]
    buenos = [r for r in recortes if r[2] >= MIN_AREA_RECORTE * area_foto]
    buenos.sort(key=lambda r: -r[2])
    return [r[0] for r in buenos[:MAX_RECORTES_FOTO]]


def construir_conjunto(registros, indices, con_espejo):
    """(X, y, grupo de cada recorte, fotos sin recortes) para las fotos `indices`."""
    X, y, origen, sin_recorte = [], [], [], 0
    for n, i in enumerate(indices, 1):
        ruta, clase = registros[i]
        recortes = recortes_de_foto(ruta)
        if not recortes:
            sin_recorte += 1
        for rec in recortes:
            X.append(extraer_caracteristicas(rec))
            y.append(clase)
            origen.append(i)
            if con_espejo:
                X.append(extraer_caracteristicas(ImageOps.mirror(rec)))
                y.append(clase)
                origen.append(i)
        if n % 400 == 0:
            print(f"  ... {n}/{len(indices)} fotos", flush=True)
    return np.array(X), np.array(y), np.array(origen), sin_recorte


def metricas(y_real, y_pred):
    estado = lambda v: np.array([interpretar_clase(c)[1] for c in v])
    fruta = lambda v: np.array([interpretar_clase(c)[0] for c in v])
    er, ep = estado(y_real), estado(y_pred)
    return {"accuracy": round(accuracy_score(y_real, y_pred), 4),
            "precision_macro": round(precision_score(y_real, y_pred, average="macro", zero_division=0), 4),
            "recall_macro": round(recall_score(y_real, y_pred, average="macro", zero_division=0), 4),
            "f1_macro": round(f1_score(y_real, y_pred, average="macro", zero_division=0), 4),
            "accuracy_estado": round(accuracy_score(er, ep), 4),
            "accuracy_fruta": round(accuracy_score(fruta(y_real), fruta(y_pred)), 4),
            "recall_podrida": round(recall_score(er, ep, pos_label="podrida"), 4),
            "precision_podrida": round(precision_score(er, ep, pos_label="podrida", zero_division=0), 4)}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--buscar", action="store_true", help="busca C y gamma con validacion cruzada")
    args = ap.parse_args()

    inicio = time.time()
    registros = listar_imagenes(RAIZ / "data" / "raw")
    if not registros:
        raise SystemExit("[ERROR] No hay imagenes en data/raw/<clase>/. Ejecute src/preparar_datos.py")
    print("[INFO] Reproduciendo la division entrenamiento/prueba del notebook...", flush=True)
    i_train, i_test, grupos = dividir_como_el_notebook(registros)
    print(f"[INFO] {len(i_train)} fotos de entrenamiento y {len(i_test)} de prueba", flush=True)

    print("[INFO] Recortando frutas de las fotos de entrenamiento (con espejo)...", flush=True)
    X_tr, y_tr, o_tr, sr_tr = construir_conjunto(registros, i_train, con_espejo=True)
    print("[INFO] Recortando frutas de las fotos de prueba...", flush=True)
    X_te, y_te, o_te, sr_te = construir_conjunto(registros, i_test, con_espejo=False)
    print(f"[OK] Entrenamiento: {len(X_tr)} ejemplos | prueba: {len(X_te)} recortes | fotos sin recortes: "
          f"{sr_tr} (entrenamiento), {sr_te} (prueba) | {time.time() - inicio:.0f} s", flush=True)

    base = json.loads((RAIZ / "models" / "metadata.json").read_text(encoding="utf-8"))["mejores_hiperparametros"]
    pipeline = Pipeline([("escalador", StandardScaler()),
                         ("svm", SVC(kernel="rbf", C=base["C"], gamma=base["gamma"], probability=True,
                                     random_state=SEMILLA))])
    if args.buscar:
        print("[INFO] Buscando hiperparametros (validacion cruzada por grupos)...", flush=True)
        g_tr = grupos[o_tr]
        busqueda = GridSearchCV(
            Pipeline([("escalador", StandardScaler()), ("svm", SVC(kernel="rbf", random_state=SEMILLA))]),
            {"svm__C": [10, 100], "svm__gamma": ["scale", 1e-4]}, scoring="f1_macro", n_jobs=-1,
            cv=StratifiedGroupKFold(n_splits=3, shuffle=True, random_state=SEMILLA))
        busqueda.fit(X_tr, y_tr, groups=g_tr)
        mejores = {k.replace("svm__", ""): v for k, v in busqueda.best_params_.items()}
        print(f"[OK] Mejores hiperparametros: {mejores} (F1 macro CV {busqueda.best_score_:.3f})", flush=True)
        pipeline.set_params(svm__C=mejores["C"], svm__gamma=mejores["gamma"])
    print("[INFO] Entrenando el modelo final...", flush=True)
    pipeline.fit(X_tr, y_tr)

    m_nuevo = metricas(y_te, pipeline.predict(X_te))
    m_viejo = metricas(y_te, cargar_modelo().predict(X_te))
    print(f"[OK] Recortes de prueba | modelo NUEVO: {m_nuevo}", flush=True)
    print(f"[OK] Recortes de prueba | modelo ORIGINAL (fotos completas): {m_viejo}", flush=True)

    joblib.dump(pipeline, RUTA_MODELO_DET, compress=3)
    meta = {"proyecto": "FrutaCheck: modelo para deteccion de varias frutas por foto",
            "algoritmo": "Support Vector Machine (sklearn.svm.SVC), entrenado con recortes de src/detectar.py",
            "fecha_entrenamiento": datetime.now().isoformat(timespec="seconds"),
            "clases": [str(c) for c in pipeline.classes_],
            "hiperparametros": {"kernel": "rbf", "C": pipeline.named_steps["svm"].C,
                                "gamma": pipeline.named_steps["svm"].gamma},
            "recortes": {"entrenamiento": int(len(X_tr)), "prueba": int(len(X_te)),
                         "area_minima": MIN_AREA_RECORTE, "max_por_foto": MAX_RECORTES_FOTO},
            "metricas_recortes_prueba": m_nuevo,
            "metricas_modelo_original_en_los_mismos_recortes": m_viejo,
            "n_caracteristicas": int(X_tr.shape[1]),
            "versiones": {"scikit-learn": sklearn.__version__, "numpy": np.__version__}}
    RUTA_META_DET.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[OK] Guardados {RUTA_MODELO_DET.name} y {RUTA_META_DET.name} ({time.time() - inicio:.0f} s)", flush=True)


if __name__ == "__main__":
    main()
