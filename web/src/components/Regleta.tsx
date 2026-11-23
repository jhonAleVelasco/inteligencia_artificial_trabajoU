import type { CSSProperties } from 'react'
import { COLOR_ACCION, ETIQUETA_ACCION, ORDEN_ACCIONES } from '../lib/textos'
import type { Accion } from '../lib/tipos'

type Conteo = Record<Accion, number>

/** Barra segmentada: cuántas frutas hay en cada decisión. */
export function Regleta({ conteo, etiqueta }: { conteo: Conteo; etiqueta?: string }) {
  const segmentos = ORDEN_ACCIONES.filter((a) => conteo[a] > 0)
  const resumen = segmentos.map((a) => `${conteo[a]} ${ETIQUETA_ACCION[a].toLowerCase()}`).join(', ')
  if (!segmentos.length) return <div className="regleta regleta--vacia" role="img" aria-label="Sin frutas" />
  return (
    <div className="regleta" role="img" aria-label={etiqueta ?? resumen}>
      {segmentos.map((a) => (
        <i key={a} style={{ '--n': conteo[a], '--c': COLOR_ACCION[a] } as CSSProperties} />
      ))}
    </div>
  )
}

const TEXTO: Record<Accion, string> = {
  normal: 'a precio normal',
  descuento: 'con descuento',
  retirar: 'para retirar',
  revisar: 'por revisar a mano',
}

export function Leyenda({ conteo }: { conteo: Conteo }) {
  return (
    <ul className="leyenda">
      {ORDEN_ACCIONES.filter((a) => conteo[a] > 0).map((a) => (
        <li key={a} style={{ '--c': COLOR_ACCION[a] } as CSSProperties}>
          <b>{conteo[a]}</b> {TEXTO[a]}
        </li>
      ))}
    </ul>
  )
}
