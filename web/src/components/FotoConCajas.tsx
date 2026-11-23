import type { CSSProperties } from 'react'
import { precioFinal } from '../lib/logic'
import { pesos } from '../lib/format'
import { ETIQUETA_ACCION } from '../lib/textos'
import type { Accion, FrutaDetectada } from '../lib/tipos'

export interface FrutaEvaluada extends FrutaDetectada {
  accionActual: Accion
}

interface Props {
  url: string
  frutas: FrutaEvaluada[]
  seleccion: number | null
  onSeleccion: (id: number | null) => void
  precios: Record<string, number>
  descuento: number
  cargando: boolean
}

/** La foto con una caja y una etiqueta de precio sobre cada fruta detectada. */
export function FotoConCajas({ url, frutas, seleccion, onSeleccion, precios, descuento, cargando }: Props) {
  return (
    <div className="lienzo" onClick={() => onSeleccion(null)}>
      <img src={url} alt="Foto analizada con las frutas detectadas" />
      {cargando && <div className="lienzo__velo" />}
      {cargando && <div className="lienzo__barra" />}
      {frutas.map((f, i) => {
        const base = precios[f.fruta] ?? 0
        const final = precioFinal(f.accionActual, base, descuento)
        const dentro = f.caja.y0 < 0.09
        const derecha = f.caja.x0 > 0.72
        const estilo = {
          left: `${f.caja.x0 * 100}%`,
          top: `${f.caja.y0 * 100}%`,
          width: `${(f.caja.x1 - f.caja.x0) * 100}%`,
          height: `${(f.caja.y1 - f.caja.y0) * 100}%`,
          '--i': i,
        } as CSSProperties
        const clases = ['caja']
        if (f.accionActual !== 'normal') clases.push(`caja--${f.accionActual}`)
        if (seleccion === f.id) clases.push('caja--sel')
        else if (seleccion !== null) clases.push('caja--atenuada')
        return (
          <button
            key={f.id}
            type="button"
            className={clases.join(' ')}
            style={estilo}
            aria-pressed={seleccion === f.id}
            aria-label={`${f.nombre}, ${f.estado}: ${ETIQUETA_ACCION[f.accionActual]}`}
            onClick={(e) => {
              e.stopPropagation()
              onSeleccion(seleccion === f.id ? null : f.id)
            }}
          >
            <span className={`etiqueta${dentro ? ' etiqueta--dentro' : ''}${derecha ? ' etiqueta--der' : ''}`}>
              {final !== null ? (
                <>
                  <b>{pesos(final)}</b>
                  {f.accionActual === 'descuento' && <s>{pesos(base)}</s>}
                </>
              ) : (
                <b>{f.accionActual === 'revisar' ? 'Revisar' : ETIQUETA_ACCION[f.accionActual]}</b>
              )}
            </span>
          </button>
        )
      })}
    </div>
  )
}
