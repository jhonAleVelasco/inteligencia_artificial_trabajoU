# Guion de la demostración (exposición, 12 minutos)

App: https://frutacheck-grupo1.streamlit.app

## Antes de exponer (10 minutos antes)

- [ ] Abrir la URL de la app. Si aparece "This app has gone to sleep", hacer clic en **Yes, get this app back up** y esperar unos 30 segundos.
- [ ] Tener a mano una fruta fresca, una dañada (manzana o banano con manchas) y una hoja blanca de fondo.
- [ ] Dejar en una carpeta 6 a 10 fotos para el lote (mezcla de frescas y podridas) y un archivo que no sea imagen (por ejemplo un `.txt` renombrado a `.jpg`).
- [ ] Tener abierto el video de respaldo (plan B) y el proyecto local por si falla internet.

## Demostración (unos 3 minutos)

1. **Presentar la pantalla:** "FrutaCheck revisa la calidad de la fruta con una foto. A la izquierda está la confianza mínima y el desempeño del modelo."
2. **Fruta fresca con la cámara:** pestaña *Revisar una fruta* → *Cámara* → foto centrada. Resultado esperado: **FRESCA**, apta para la venta.
3. **Fruta dañada:** misma pestaña. Resultado esperado: **PODRIDA**, retirarla del exhibidor. Mostrar la "probabilidad de estar podrida".
4. **Umbral:** subir la confianza mínima a 0,90 y repetir una foto dudosa: la app responde "No estoy seguro" y pide revisar a mano.
5. **Lote:** pestaña *Inspeccionar un lote* → precio 6.000 COP/kg, peso 180 g, tolerancia 10 % → subir las fotos. Explicar las métricas, la pérdida estimada y la decisión (aceptar o rechazar).
6. **Manejo de errores:** subir el archivo que no es imagen al lote: la app lo reporta y sigue con las demás fotos.

## Plan B

- **Sin internet:** ejecutar localmente con `streamlit run app/app.py` (las fotos de prueba están en `data/raw/`).
- **Sin cámara:** usar *Subir imagen* con fotos guardadas.
- **Nada funciona:** reproducir el video grabado de la demo.

## Frases clave

- "El modelo es un SVM entrenado desde cero; no usamos redes neuronales ni modelos pre-entrenados."
- "Acierta el 86,6 % en 16 clases y el 93,4 % al decir si la fruta está podrida."
- "Cuando no está seguro no adivina: pide revisión manual."
