import type { Accion, Ajustes, Resultado } from './tipos'

/**
 * Misma lógica que src/detectar.py y src/predict.py, para que el panel recalcule al instante
 * cuando se mueve un control sin volver a analizar la foto.
 */
export function decidirAccion(probPodrida: number, desde: number, retirar: number): 'normal' | 'descuento' | 'retirar' {
  if (probPodrida >= retirar) return 'retirar'
  if (probPodrida >= desde) return 'descuento'
  return 'normal'
}

/** Retirar no necesita saber qué fruta es; para lo demás hace falta confianza en la clase. */
export function accionDeFruta(f: Pick<Resultado, 'prob_podrida' | 'probabilidad'>, a: Ajustes): Accion {
  const base = decidirAccion(f.prob_podrida, a.descuentoDesde, a.retirarDesde)
  if (base !== 'retirar' && f.probabilidad < a.confianza) return 'revisar'
  return base
}

/** Precio que se cobra por una fruta; null si no se vende (retirar) o hay que revisarla. */
export function precioFinal(accion: Accion, precioBase: number, descuento: number): number | null {
  if (accion === 'normal') return precioBase
  if (accion === 'descuento') return precioBase * (1 - descuento)
  return null
}

export interface ResumenEscena {
  total: number
  conteo: Record<Accion, number>
  valorSin: number
  valorCon: number
  ahorro: number
}

export function resumirEscena(frutas: { accion: Accion; fruta: string }[], precios: Record<string, number>, descuento: number): ResumenEscena {
  const conteo: Record<Accion, number> = { normal: 0, descuento: 0, retirar: 0, revisar: 0 }
  let valorSin = 0
  let valorCon = 0
  for (const f of frutas) {
    conteo[f.accion] += 1
    const precio = precios[f.fruta] ?? 0
    const final = precioFinal(f.accion, precio, descuento)
    if (final !== null) {
      valorSin += precio
      valorCon += final
    }
  }
  return { total: frutas.length, conteo, valorSin, valorCon, ahorro: valorSin - valorCon }
}
