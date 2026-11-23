import { ETIQUETA_ACCION } from '../lib/textos'
import type { Accion } from '../lib/tipos'

export function ChipAccion({ accion }: { accion: Accion }) {
  return <span className={`chip chip--${accion}`}>{ETIQUETA_ACCION[accion]}</span>
}
