import { usarPanel } from '../lib/contexto'
import { pesos, porcentaje } from '../lib/format'
import { Deslizador } from '../components/Deslizador'

/** Lista de precios: lo que vale cada fruta por unidad y cuánto queda con descuento. */
export function Precios() {
  const { ajustes, config, cambiarAjustes } = usarPanel()
  return (
    <>
      <header className="cab">
        <div>
          <h1 className="titulo">Precios</h1>
          <p>El precio de cada fruta por unidad. Con él se calcula el valor en venta de cada foto que se revisa.</p>
        </div>
      </header>

      <div className="cuerpo">
        <div className="principal">
          <table className="libro libro--precios">
            <thead>
              <tr>
                <th>Fruta</th>
                <th>Precio por unidad</th>
                <th className="der">Con descuento del {porcentaje(ajustes.descuento)}</th>
              </tr>
            </thead>
            <tbody>
              {config.frutas.map((f) => {
                const precio = ajustes.precios[f.id] ?? 0
                return (
                  <tr key={f.id} className="sin-clic">
                    <td><span className="fruta-celda">{f.nombre}</span></td>
                    <td>
                      <label className="precio-campo">
                        <span aria-hidden="true">$</span>
                        <input
                          className="campo"
                          type="number"
                          inputMode="numeric"
                          min={0}
                          step={50}
                          value={precio}
                          aria-label={`Precio de ${f.nombre} en pesos`}
                          onChange={(e) =>
                            cambiarAjustes({ precios: { ...ajustes.precios, [f.id]: Math.max(0, Number(e.target.value) || 0) } })
                          }
                        />
                      </label>
                    </td>
                    <td className="der"><span className="precio">{pesos(precio * (1 - ajustes.descuento))}</span></td>
                  </tr>
                )
              })}
            </tbody>
          </table>
          <p className="suave">Los precios se guardan en este navegador. Las frutas que el modelo retira no se cobran.</p>
        </div>

        <aside className="inspector">
          <div className="bloque">
            <h2>Descuento por fruta con riesgo</h2>
            <Deslizador
              etiqueta="Descuento aplicado"
              valor={ajustes.descuento}
              minimo={0.05}
              maximo={0.9}
              paso={0.05}
              formato={porcentaje}
              onCambio={(v) => cambiarAjustes({ descuento: v })}
              ayuda={`Se aplica a las frutas con probabilidad de estar podridas desde ${porcentaje(ajustes.descuentoDesde)}. Esas reglas se cambian en Revisar.`}
            />
          </div>
        </aside>
      </div>
    </>
  )
}
