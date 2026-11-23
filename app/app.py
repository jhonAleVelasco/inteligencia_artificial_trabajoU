"""FrutaCheck: control de calidad de fruta (fresca o podrida) con un modelo SVM.

Necesidad: en fruterias, tiendas de barrio y plazas de mercado la fruta se revisa a ojo.
Una fruta podrida que se queda en el exhibidor contagia a las vecinas y aumenta la perdida.
La app permite revisar una fruta con la camara o inspeccionar un lote completo de fotos y
estimar cuanto dinero se pierde.

Ejecutar desde la raiz del repositorio:
    streamlit run app/app.py
"""
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from src.predict import (cargar_metadatos, cargar_modelo, interpretar_clase, nombre_clase,  # noqa: E402
                         nombre_fruta, predecir, resumir_lote)

TIPOS_IMAGEN = ["jpg", "jpeg", "png", "bmp", "webp"]
MAX_LOTE = 60

st.set_page_config(page_title="FrutaCheck", page_icon="🍎", layout="centered")


@st.cache_resource
def obtener_modelo():
    return cargar_modelo()


@st.cache_data
def obtener_metadatos():
    return cargar_metadatos()


def pesos(valor):
    return f"${valor:,.0f}".replace(",", ".")


st.title("FrutaCheck")
st.write("Control de calidad de fruta para fruterías y plazas de mercado: tome una foto y el modelo "
         "le dice qué fruta es, si está **fresca o podrida** y qué hacer con ella.")

try:
    modelo = obtener_modelo()
except FileNotFoundError as error:
    st.error(str(error))
    st.stop()
except Exception as error:  # modelo corrupto o de otra version de scikit-learn
    st.error(f"No se pudo cargar el modelo: {error}")
    st.stop()
metadatos = obtener_metadatos()
frutas = sorted({interpretar_clase(c)[0] for c in modelo.classes_})

with st.sidebar:
    st.header("Configuración")
    umbral = st.slider("Confianza mínima para aceptar la predicción", 0.30, 0.95, 0.60, 0.05,
                       help="Si la probabilidad más alta queda por debajo, la app pide revisar la fruta a mano.")
    ver_probabilidades = st.checkbox("Mostrar probabilidad de cada clase", value=False)
    st.divider()
    st.subheader("Modelo")
    st.write("Algoritmo: **Support Vector Machine (SVC)**, entrenado desde cero.")
    st.write("Frutas: " + ", ".join(nombre_fruta(f) for f in frutas))
    if metadatos.get("metricas"):
        m = metadatos["metricas"]
        st.write(f"Accuracy en prueba: **{m['accuracy']:.1%}**")
        st.write(f"F1 macro en prueba: **{m['f1_macro']:.1%}**")
    st.caption("Funciona mejor con una sola fruta, centrada, bien iluminada y ocupando buena parte de la foto.")

tab_una, tab_lote = st.tabs(["Revisar una fruta", "Inspeccionar un lote"])

with tab_una:
    fuente = st.radio("Fuente de la imagen", ["Cámara", "Subir imagen"], horizontal=True)
    if fuente == "Cámara":
        archivo = st.camera_input("Ponga la fruta en el centro de la imagen y tome la foto")
    else:
        archivo = st.file_uploader("Suba una foto de la fruta", type=TIPOS_IMAGEN)

    if archivo is None:
        st.info("Esperando una imagen.")
    else:
        try:
            r = predecir(modelo, archivo, umbral=umbral)
        except ValueError as error:
            st.error(f"No se pudo analizar la imagen: {error}")
        else:
            if fuente == "Subir imagen":
                st.image(archivo, caption="Imagen recibida", width=300)
            fruta = nombre_fruta(r["fruta"])
            if not r["confiable"]:
                st.warning(f"No estoy seguro ({r['probabilidad']:.0%}, por debajo del umbral de {umbral:.0%}). "
                           f"Lo más parecido es **{nombre_clase(r['clase'])}**. Revise la fruta a mano o tome "
                           "otra foto más cerca, centrada y con mejor luz.")
            elif r["estado"] == "podrida":
                st.error(f"**{fruta}: PODRIDA** ({r['probabilidad']:.0%} de confianza)")
                st.write(r["recomendacion"])
            else:
                st.success(f"**{fruta}: FRESCA** ({r['probabilidad']:.0%} de confianza)")
                st.write(r["recomendacion"])
            c1, c2 = st.columns(2)
            c1.metric("Fruta detectada", fruta)
            c2.metric("Probabilidad de estar podrida", f"{r['prob_podrida']:.0%}")
            if ver_probabilidades:
                tabla = pd.DataFrame(r["ranking"], columns=["Clase", "Probabilidad"])
                tabla["Clase"] = tabla["Clase"].map(nombre_clase)
                st.bar_chart(tabla.set_index("Clase"), horizontal=True)

with tab_lote:
    st.write("Revise un pedido o un canastillo completo: suba varias fotos (una fruta por foto) y la app "
             "calcula cuántas están podridas, cuánto dinero representan y si conviene recibir el lote.")
    c1, c2, c3 = st.columns(3)
    precio_kg = c1.number_input("Precio por kg (COP)", min_value=0, max_value=200_000, value=6_000, step=500)
    peso_g = c2.number_input("Peso promedio por fruta (g)", min_value=5, max_value=2_000, value=180, step=10)
    tolerancia = c3.slider("Máximo de podridas aceptable", 0, 50, 10, 1, format="%d%%") / 100
    archivos = st.file_uploader(f"Fotos del lote (máximo {MAX_LOTE})", type=TIPOS_IMAGEN,
                                accept_multiple_files=True, key="lote")

    if not archivos:
        st.info("Suba las fotos del lote para empezar.")
    else:
        if len(archivos) > MAX_LOTE:
            st.warning(f"Se recibieron {len(archivos)} fotos; solo se analizan las primeras {MAX_LOTE}.")
            archivos = archivos[:MAX_LOTE]
        validos, filas, fallidos = [], [], []
        barra = st.progress(0.0, text="Analizando fotos...")
        for i, f in enumerate(archivos, 1):
            try:
                r = predecir(modelo, f, umbral=umbral)
            except ValueError as error:
                fallidos.append(f"{f.name}: {error}")
            else:
                validos.append(r)
                estado = "Revisar a mano" if not r["confiable"] else r["estado"].capitalize()
                filas.append({"Foto": f.name, "Fruta": nombre_fruta(r["fruta"]), "Estado": estado,
                              "Confianza": f"{r['probabilidad']:.0%}"})
            barra.progress(i / len(archivos), text=f"Analizando fotos... {i}/{len(archivos)}")
        barra.empty()

        for mensaje in fallidos:
            st.error(f"No se pudo analizar {mensaje}")
        if validos:
            resumen = resumir_lote(validos, peso_g, precio_kg, tolerancia)
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Frescas", resumen["frescas"])
            m2.metric("Podridas", resumen["podridas"])
            m3.metric("Revisar a mano", resumen["revisar"])
            m4.metric("Pérdida estimada", pesos(resumen["perdida_estimada"]))
            texto = (f"{resumen['porcentaje_podridas']:.0%} de podridas frente a un máximo de {tolerancia:.0%}.")
            if resumen["frescas"] + resumen["podridas"] == 0:
                st.warning("Ninguna foto superó el umbral de confianza: revise el lote a mano.")
            elif resumen["aceptado"]:
                st.success(f"Lote ACEPTADO: {texto}")
            else:
                st.error(f"Lote RECHAZADO: {texto} Devuelva o negocie el precio con el proveedor y "
                         "separe las podridas de inmediato.")
            st.dataframe(pd.DataFrame(filas), hide_index=True, use_container_width=True)
