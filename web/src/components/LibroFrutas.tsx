import type { CSSProperties } from 'react'
import { precioFinal } from '../lib/logic'
import { pesos, porcentaje } from '../lib/format'
import { COLOR_ACCION } from '../lib/textos'
import { ChipAccion } from './ChipAccion'
import type { FrutaEvaluada } from './FotoConCajas'

interface Props {
  frutas: FrutaEvaluada[]
  seleccion: number | null
  onSeleccion: (id: number | null) => void
  precios: Record<string, number>
  descuento: number
}

/** Tabla con una fila por fruta detectada. */
export function LibroFrutas({ frutas, seleccion, onSeleccion, precios, descuento }: Props) {
  return (
    <table className="libro libro--fruta">
      <thead>
        <tr>
          <th>Fruta</th>
          <th>Estado</th>
          <th>Está podrida</th>
          <th>Seguridad</th>
          <th>Decisión</th>
          <th className="der">Precio</th>
        </tr>
      </thead>
      <tbody>
        {frutas.map((f) => {
          const base = precios[f.fruta] ?? 0
          const final = precioFinal(f.accionActual, base, descuento)
          const estilo = { '--c': COLOR_ACCION[f.accionActual] } as CSSProperties
          return (
            <tr
              key={f.id}
              style={estilo}
              aria-selected={seleccion === f.id}
              tabIndex={0}
              onClick={() => onSeleccion(seleccion === f.id ? null : f.id)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault()
                  onSeleccion(seleccion === f.id ? null : f.id)
                }
              }}
            >
              <td>
                <div className="fruta-celda">
                  <img src={f.recorte} alt="" />
                  <span>
                    {f.nombre}
                    <small>Fruta {f.id}</small>
                  </span>
                </div>
              </td>
              <td>{f.estado === 'fresca' ? 'Fresca' : 'Podrida'}</td>
              <td>
                <span className="mini">
                  <i><b style={{ width: `${f.prob_podrida * 100}%` }} /></i>
                  <span className="num">{porcentaje(f.prob_podrida)}</span>
                </span>
              </td>
              <td className="num">{porcentaje(f.probabilidad)}</td>
              <td><ChipAccion accion={f.accionActual} /></td>
              <td className="der">
                {final === null ? (
                  <span className="suave nowrap">{f.accionActual === 'retirar' ? 'No se vende' : 'Por revisar'}</span>
                ) : (
                  <span className="precio">
                    {f.accionActual === 'descuento' && <s>{pesos(base)}</s>}
                    {pesos(final)}
                  </span>
                )}
              </td>
            </tr>
          )
        })}
      </tbody>
    </table>
  )
}
