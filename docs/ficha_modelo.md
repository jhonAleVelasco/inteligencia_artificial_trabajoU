# Ficha del modelo: FrutaCheck SVM

## Descripción

| Campo | Valor |
|---|---|
| Tarea | Clasificación de imágenes en 16 clases `<fruta>_<estado>` (8 frutas, fresca o podrida) |
| Algoritmo | Support Vector Machine, `sklearn.svm.SVC`, kernel RBF, C = 100, gamma = 0,0001 |
| Pipeline | `StandardScaler` → `SVC(probability=True)` |
| Entrada | Foto RGB de una fruta (mínimo 32 × 32 píxeles) |
| Características | 1.806: histogramas HSV (32), LBP uniforme (10) y HOG (1.764), sobre la foto recortada al centro y reducida a 128 × 128 |
| Salida | Clase, fruta, estado, probabilidad de cada clase y probabilidad total de estar podrida |
| Archivo | `models/modelo.pkl` (joblib, unos 35 MB); detalles en `models/metadata.json` |
| Entrenamiento | Desde cero, sin modelos pre-entrenados; `notebooks/01_training.ipynb` |

## Uso previsto

Apoyar a tenderos, fruteros y encargados de recibo en la **revisión de calidad**: detectar fruta podrida para retirarla del exhibidor y estimar la calidad de un lote antes de recibirlo. Es una ayuda para decidir: no reemplaza la revisión de la persona cuando la app dice "revisar a mano".

**No está pensado para:** frutas distintas a las 8 entrenadas, fotos con varias frutas mezcladas, decisiones de inocuidad alimentaria ni certificaciones de calidad.

## Datos

*Fresh and Rotten Fruits Dataset* (Sultana, Jahan y Uddin, 2022), Mendeley Data, CC BY 4.0: 3.200 fotos reales (3.193 tras quitar duplicados) tomadas en fruterías y en campo. Ver `data/README.md`.

- **Entrenamiento:** 2.560 fotos, más su versión en espejo (5.120 ejemplos).
- **Prueba:** 633 fotos. Las fotos casi iguales (dHash) se mantienen en el mismo conjunto para evitar *data leakage*.

## Desempeño (conjunto de prueba)

| Métrica | Valor |
|---|---|
| Accuracy (16 clases) | 86,6 % |
| F1 macro | 86,4 % |
| Fresca vs. podrida (accuracy) | 93,4 % |
| Recall de podridas | 92,1 % |
| Precision de podridas | 94,5 % |
| Fruta correcta | 89,3 % |
| Clasificador base (clase más frecuente) | 5,2 % |

Con el umbral por defecto de la app (0,60), el modelo responde en el 81 % de las fotos, con 95,3 % de acierto; el resto queda para revisión manual.

**Clases más débiles:** manzana podrida (F1 0,73), granada podrida (0,76) y uva (0,79–0,81). Suelen ser pudriciones incipientes o racimos con fondo variado.

## Limitaciones y riesgos

- Las fotos vienen de fruterías de Bangladés: la luz, el fondo o las variedades de una tienda colombiana pueden bajar el desempeño.
- Cualquier fruta desconocida se parecerá a alguna de las 8 clases; el umbral de confianza reduce, pero no elimina, ese riesgo.
- Una podrida que pasa como fresca (8 de cada 100) puede quedarse en el exhibidor: por eso la app muestra la probabilidad de estar podrida y permite subir el umbral.

## Mantenimiento

Para adaptar el modelo a una tienda: tomar fotos propias con `src/capturar_fotos.py --clase <fruta>_<estado>`, volver a ejecutar el notebook y publicar el nuevo `modelo.pkl`.

## Modelo para varias frutas por foto

| Campo | Valor |
|---|---|
| Archivo | `models/modelo_deteccion.pkl` (unos 40 MB); detalles en `models/metadata_deteccion.json` |
| Algoritmo | El mismo pipeline `StandardScaler` → `SVC` (RBF, C = 100, gamma = 0,0001), entrenado con **recortes** de cada fruta |
| Entrada | Foto con varias frutas separadas sobre un fondo liso y claro; `src/detectar.py` segmenta y recorta cada fruta |
| Entrenamiento | `python -m src.entrenar_deteccion`: 5.864 ejemplos (recortes y sus espejos) de las 2.560 fotos de entrenamiento |
| Prueba | 728 recortes de las 633 fotos de prueba, con la misma división del notebook |

Desempeño en los recortes de prueba: accuracy 80,1 % (16 clases), F1 macro 80,3 %, fresca vs. podrida 89,6 %, fruta correcta 85,7 %, recall de podridas 92,3 %. El modelo original da 12,9 % sobre esos mismos recortes, por eso se entrena aparte.

La decisión de descuento usa la **probabilidad de estar podrida** (descuento desde 40 %, retiro desde 80 %). No es el porcentaje de la fruta que está dañada.

**Limitaciones adicionales:** necesita fondo liso y claro y frutas separadas; no se validó con fotos reales de varias frutas (las pruebas usan escenas armadas con fotos de prueba, ver `src/evaluar_deteccion.py`); no separa bien frutas muy montadas ni racimos.
