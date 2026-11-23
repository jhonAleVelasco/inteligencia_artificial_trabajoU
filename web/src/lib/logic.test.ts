import { describe, expect, it } from 'vitest'
import { accionDeFruta, decidirAccion, precioFinal, resumirEscena } from './logic'
import type { Ajustes } from './tipos'

const ajustes = { confianza: 0.6, descuento: 0.3, descuentoDesde: 0.4, retirarDesde: 0.8, precios: {} } satisfies Ajustes

describe('decidirAccion (igual que tests/test_detectar.py)', () => {
  it('respeta los umbrales', () => {
    expect(decidirAccion(0.39, 0.4, 0.8)).toBe('normal')
    expect(decidirAccion(0.4, 0.4, 0.8)).toBe('descuento')
    expect(decidirAccion(0.79, 0.4, 0.8)).toBe('descuento')
    expect(decidirAccion(0.8, 0.4, 0.8)).toBe('retirar')
  })
  it('pide revisar si no hay confianza en la clase, salvo que ya se deba retirar', () => {
    expect(accionDeFruta({ prob_podrida: 0.5, probabilidad: 0.3 }, ajustes)).toBe('revisar')
    expect(accionDeFruta({ prob_podrida: 0.9, probabilidad: 0.3 }, ajustes)).toBe('retirar')
    expect(accionDeFruta({ prob_podrida: 0.1, probabilidad: 0.9 }, ajustes)).toBe('normal')
  })
})

describe('resumirEscena', () => {
  it('calcula el descuento y excluye retiradas y por revisar', () => {
    const frutas = [
      { accion: 'normal' as const, fruta: 'manzana' },
      { accion: 'descuento' as const, fruta: 'manzana' },
      { accion: 'retirar' as const, fruta: 'banano' },
      { accion: 'revisar' as const, fruta: 'uva' },
    ]
    const s = resumirEscena(frutas, { manzana: 1000, banano: 500, uva: 2000 }, 0.3)
    expect(s.conteo).toEqual({ normal: 1, descuento: 1, retirar: 1, revisar: 1 })
    expect(s.valorSin).toBe(2000)
    expect(s.valorCon).toBeCloseTo(1700)
    expect(s.ahorro).toBeCloseTo(300)
  })
  it('precioFinal por acción', () => {
    expect(precioFinal('normal', 1000, 0.25)).toBe(1000)
    expect(precioFinal('descuento', 1000, 0.25)).toBeCloseTo(750)
    expect(precioFinal('retirar', 1000, 0.25)).toBeNull()
    expect(precioFinal('revisar', 1000, 0.25)).toBeNull()
  })
})
