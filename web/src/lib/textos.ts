import type { Accion } from './tipos'

export const ETIQUETA_ACCION: Record<Accion, string> = {
  normal: 'Vender',
  descuento: 'Descuento',
  retirar: 'Retirar',
  revisar: 'Revisar a mano',
}

export const COLOR_ACCION: Record<Accion, string> = {
  normal: 'var(--vender)',
  descuento: 'var(--descuento)',
  retirar: 'var(--retirar)',
  revisar: 'var(--revisar)',
}

export const ORDEN_ACCIONES: Accion[] = ['normal', 'descuento', 'retirar', 'revisar']

export const LEYENDA_ACCION: Record<Accion, (n: number) => string> = {
  normal: (n) => (n === 1 ? 'a precio normal' : 'a precio normal'),
  descuento: (n) => (n === 1 ? 'con descuento' : 'con descuento'),
  retirar: (n) => (n === 1 ? 'para retirar' : 'para retirar'),
  revisar: (n) => (n === 1 ? 'por revisar a mano' : 'por revisar a mano'),
}
