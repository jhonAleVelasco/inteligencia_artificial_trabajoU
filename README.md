# Reconocedor de objetos con SVM

Aplicación web que reconoce qué fruta se le muestra a la cámara del computador (aguacate, banano, limón, manzana roja o naranja), usando un modelo **Support Vector Machine (SVM)** entrenado desde cero con fotografías reales. Proyecto de la Actividad 3 de Inteligencia Artificial I, Fundación Universitaria Los Libertadores.

## Descripción

El usuario abre la aplicación en el navegador, pone un objeto frente a la cámara y toma una foto (o sube una imagen). La aplicación responde qué objeto es y con qué confianza. Si la confianza queda por debajo de un umbral que el usuario elige, la aplicación avisa que no está segura en lugar de dar una respuesta equivocada.

Es un problema de **clasificación multiclase de imágenes**. El proyecto recorre el flujo completo de un sistema de machine learning en producción: recolección de datos reales, entrenamiento y evaluación, serialización del modelo, aplicación web y despliegue en la nube.

## Demostración

- Aplicación desplegada: **[pendiente: URL de Streamlit Cloud]**
- Repositorio: https://github.com/jhonAleVelasco/inteligencia_artificial_trabajoU

## Algoritmo utilizado

**Support Vector Machine** (`sklearn.svm.SVC`) dentro de un pipeline `StandardScaler → SVC`.

**Por qué es apropiado:** cada foto se describe con 1.796 características numéricas (color y forma). El SVM busca la frontera que separa las clases con el mayor margen posible y, con el kernel RBF, también separa clases que no son linealmente separables. Rinde bien cuando hay muchas variables y pocos cientos de ejemplos, que es justo este caso, y con `probability=True` entrega la probabilidad de cada clase, que la aplicación usa para el umbral de confianza.

**Cómo se entrenó:**

- División aproximada 80 % entrenamiento / 20 % prueba **por bloques de 30 fotos consecutivas**, estratificada por clase y con semilla fija (42). Las fotos consecutivas son casi idénticas; si se repartieran una a una, la prueba quedaría contaminada (*data leakage*).
- Aumento de datos solo en entrenamiento: cada foto se agrega también en espejo.
- Búsqueda de hiperparámetros con `GridSearchCV` y validación cruzada de 3 particiones (`StratifiedGroupKFold` con los mismos bloques): kernel lineal o RBF, `C` y `gamma`. El modelo final se reentrena con los mejores valores y `probability=True`.
- Métrica de selección: F1 macro.

**Métricas en el conjunto de prueba** (626 fotos que el modelo no vio):

| Métrica | Valor |
|---|---|
| Accuracy | 100,0 % |
| Precision (macro) | 100,0 % |
| Recall (macro) | 100,0 % |
| F1 (macro) | 100,0 % |
| F1 macro en validación cruzada | 99,9 % |
| Clasificador base (clase más frecuente) | 18,8 % de accuracy |

Mejores hiperparámetros: kernel lineal, C = 0,01. Las métricas son tan altas porque las fotos del dataset tienen fondo blanco uniforme; con la cámara, en condiciones reales, el desempeño es menor, por eso la app usa un umbral de confianza.

## Dataset

- **Fuente:** Fruits-360 [1], fotografías reales de frutas tomadas por cámara mientras cada fruta gira (licencia MIT). Disponible en Kaggle y GitHub.
- **Tamaño:** 3.177 imágenes de 100 × 100 píxeles: aguacate 570, banano 656, limón 656, manzana roja 656 y naranja 639.
- **Clases:** 5 frutas. Cada carpeta de `data/raw/` es una clase. Los nombres de archivo indican la clase, el video (`a` o `b`) y el número de cuadro.
- **Fotos propias:** `src/capturar_fotos.py` permite agregar fotos tomadas con la cámara del computador para que el modelo se adapte mejor al lugar de la demostración.
- **Features utilizadas** (calculadas en `src/preprocessing.py` sobre la foto recortada al cuadrado central y reducida a 128 × 128 píxeles):
  - Histograma de tono H (16 valores): qué colores tiene el objeto.
  - Histograma de saturación S (8 valores): qué tan vivos son los colores.
  - Histograma de brillo V (8 valores): qué tan clara u oscura es la foto.
  - Descriptor HOG (1.764 valores): dirección de los bordes en cada zona, es decir, la forma del objeto.

No se usan modelos pre-entrenados ni redes neuronales: el SVM se entrena desde cero con estas fotos.

[1] H. Mureșan and M. Oltean, "Fruit recognition from images using deep learning," *Acta Univ. Sapientiae, Informatica*, vol. 10, no. 1, pp. 26–42, 2018. Dataset: https://github.com/Horea94/Fruit-Images-Dataset

## Instalación local

### Requisitos

- Python 3.11 o superior
- pip
- Una cámara web (solo para tomar fotos nuevas o usar la cámara en la app)

### Pasos

```bash
git clone https://github.com/jhonAleVelasco/inteligencia_artificial_trabajoU.git
cd inteligencia_artificial_trabajoU
python -m venv .venv
# Windows: .venv\Scripts\activate    |    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

### Ejecutar la aplicación

```bash
streamlit run app/app.py
```

### Volver a entrenar el modelo

1. Tomar fotos de cada objeto (necesita `pip install -r requirements-captura.txt`):
   ```bash
   python src/capturar_fotos.py --clase taza --n 120
   ```
   Con ESPACIO empieza la ráfaga y con `q` termina. Mientras captura, mueva y gire el objeto, acérquelo y aléjelo.
2. Abrir y ejecutar completo `notebooks/01_training.ipynb`. Al final genera `models/modelo.pkl` y `models/metadata.json`.

## Uso

1. Abra la aplicación y permita el acceso a la cámara. Para mejores resultados, muestre la fruta frente a un fondo blanco (una hoja de papel).
2. En la barra lateral elija la fuente (cámara o subir imagen) y la confianza mínima.
3. Ponga el objeto en el centro de la imagen, con buena luz, y tome la foto.
4. La aplicación muestra el objeto reconocido, su confianza y la probabilidad de cada objeto. Si la confianza es baja, sugiere acercar o centrar el objeto.

## Estructura del proyecto

```
inteligencia_artificial_trabajoU/
├── README.md                  Documentación principal
├── requirements.txt           Dependencias de la app y del notebook
├── requirements-captura.txt   Dependencia extra para tomar fotos (OpenCV)
├── .gitignore
├── LICENSE
├── data/
│   ├── raw/<clase>/           Fotos originales, una carpeta por objeto
│   └── processed/             caracteristicas.csv generado por el notebook
├── notebooks/
│   └── 01_training.ipynb      EDA, preprocesamiento, entrenamiento, evaluación y serialización
├── models/
│   ├── modelo.pkl             Pipeline entrenado (StandardScaler + SVC)
│   └── metadata.json          Clases, hiperparámetros, métricas y versiones
├── src/
│   ├── __init__.py
│   ├── preprocessing.py       Carga de imágenes y extracción de características
│   ├── predict.py             Carga del modelo y predicción
│   └── capturar_fotos.py      Captura de fotos para el dataset
├── app/
│   ├── app.py                 Aplicación Streamlit
│   └── static/
└── docs/
    ├── captura_app_*.png      Capturas de la app funcionando localmente
    └── presentacion.pdf       Presentación final (pendiente)
```

## Despliegue

Servicio: **Streamlit Cloud**. En https://share.streamlit.io se conecta este repositorio, se elige la rama `main`, el archivo principal `app/app.py` y Python 3.12. La plataforma instala `requirements.txt` y publica la URL. La cámara funciona desde el navegador del usuario, así que no se necesita instalar nada.

## Limitaciones y trabajo futuro

- El modelo solo reconoce las 5 frutas con las que se entrenó; un objeto nuevo siempre se parecerá a alguna. Por eso la app usa un umbral de confianza.
- El rendimiento baja si el fondo o la luz son muy distintos a los de las fotos de entrenamiento.
- Mejoras: más fotos en distintos lugares, una clase "sin objeto", características de textura (LBP) y reconocimiento continuo en video.

## Autores

- Jhon Alejandro Velasco García ([rol])
- Yesid Esteban Avendaño Barbosa ([rol])
- Keiner Astos ([rol])

## Licencia

MIT License. Ver `LICENSE`.
