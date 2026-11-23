# Datos

## data/raw/

Fotos usadas para entrenar el modelo de FrutaCheck: **3.200 imágenes originales** en 16 carpetas, una por clase con la forma `<fruta>_<estado>`.

| Fruta | Fresca | Podrida |
|---|---|---|
| Manzana | `manzana_fresca` (200) | `manzana_podrida` (200) |
| Banano | `banano_fresco` (200) | `banano_podrido` (200) |
| Naranja | `naranja_fresca` (200) | `naranja_podrida` (200) |
| Guayaba | `guayaba_fresca` (200) | `guayaba_podrida` (200) |
| Fresa | `fresa_fresca` (200) | `fresa_podrida` (200) |
| Uva | `uva_fresca` (200) | `uva_podrida` (200) |
| Granada | `granada_fresca` (200) | `granada_podrida` (200) |
| Azufaifa | `azufaifa_fresca` (200) | `azufaifa_podrida` (200) |

- **Fuente:** N. Sultana, M. Jahan y M. S. Uddin, *Fresh and Rotten Fruits Dataset for Machine-Based Evaluation of Fruit Quality*, Mendeley Data, v1, 2022. doi: [10.17632/bdd69gyhv8.1](https://doi.org/10.17632/bdd69gyhv8.1)
- **Licencia:** [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Las imágenes pertenecen a sus autores; aquí se redistribuyen reducidas, con atribución.
- **Origen de las fotos:** fruterías y campo; un experto de un instituto agrícola etiquetó cada fruta como fresca o podrida.
- **Cambios hechos por el grupo:** solo se usan las imágenes originales (no las aumentadas del dataset). Cada foto se redujo a 256 píxeles por el lado corto (JPG calidad 90) con `src/preparar_datos.py`. Los nombres de archivo son `<clase>_<número>.jpg`.
- **Calidad:** sin valores nulos; hay 7 duplicados exactos que el notebook quita, y 162 grupos de fotos casi iguales que se mantienen juntos al dividir entrenamiento y prueba.

Para regenerar la carpeta desde el dataset original:

```bash
python src/preparar_datos.py --origen "RUTA/Original Image" --limpiar
```

## data/processed/

`caracteristicas.csv`: una fila por imagen con las 1.806 características (color HSV, textura LBP y forma HOG). Lo genera `notebooks/01_training.ipynb` y no se sube a GitHub (unos 60 MB; está en `.gitignore`).
