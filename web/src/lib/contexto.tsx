import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { api } from './api'
import type { Ajustes, Config } from './tipos'

const CLAVE_AJUSTES = 'frutacheck.ajustes.v2'

interface Valor {
  config: Config | null
  errorConfig: string | null
  ajustes: Ajustes | null
  cambiarAjustes: (cambios: Partial<Ajustes>) => void
  restablecer: () => void
}

const Contexto = createContext<Valor | null>(null)

function ajustesPorDefecto(c: Config): Ajustes {
  return {
    confianza: c.por_defecto.confianza,
    descuento: c.por_defecto.descuento,
    descuentoDesde: c.por_defecto.descuento_desde,
    retirarDesde: c.por_defecto.retirar_desde,
    precios: Object.fromEntries(c.frutas.map((f) => [f.id, f.precio_unidad])),
  }
}

export function Proveedor({ children }: { children: ReactNode }) {
  const [config, setConfig] = useState<Config | null>(null)
  const [errorConfig, setErrorConfig] = useState<string | null>(null)
  const [ajustes, setAjustes] = useState<Ajustes | null>(null)

  useEffect(() => {
    api
      .config()
      .then((c) => {
        setConfig(c)
        const base = ajustesPorDefecto(c)
        try {
          const guardados = JSON.parse(localStorage.getItem(CLAVE_AJUSTES) ?? 'null')
          setAjustes(guardados ? { ...base, ...guardados, precios: { ...base.precios, ...guardados.precios } } : base)
        } catch {
          setAjustes(base)
        }
      })
      .catch((e: Error) => setErrorConfig(e.message))
  }, [])

  useEffect(() => {
    if (!ajustes) return
    try {
      localStorage.setItem(CLAVE_AJUSTES, JSON.stringify(ajustes))
    } catch {
      /* el navegador no permite guardar; los ajustes duran mientras la pestaña esté abierta */
    }
  }, [ajustes])

  const cambiarAjustes = useCallback((cambios: Partial<Ajustes>) => {
    setAjustes((a) => {
      if (!a) return a
      const siguiente = { ...a, ...cambios }
      // El umbral de retiro nunca puede quedar por debajo del de descuento.
      if (siguiente.retirarDesde < siguiente.descuentoDesde) {
        if ('descuentoDesde' in cambios) siguiente.retirarDesde = siguiente.descuentoDesde
        else siguiente.descuentoDesde = siguiente.retirarDesde
      }
      return siguiente
    })
  }, [])

  const restablecer = useCallback(() => {
    if (!config) return
    // Solo las reglas; los precios que el usuario escribió se conservan.
    const base = ajustesPorDefecto(config)
    setAjustes((a) => (a ? { ...base, precios: a.precios } : base))
  }, [config])

  const valor = useMemo(
    () => ({ config, errorConfig, ajustes, cambiarAjustes, restablecer }),
    [config, errorConfig, ajustes, cambiarAjustes, restablecer],
  )
  return <Contexto.Provider value={valor}>{children}</Contexto.Provider>
}

export function usarPanel(): Valor & { config: Config; ajustes: Ajustes } {
  const v = useContext(Contexto)
  if (!v) throw new Error('usarPanel debe usarse dentro de <Proveedor>')
  return v as Valor & { config: Config; ajustes: Ajustes }
}

export function usarEstado(): Pick<Valor, 'config' | 'errorConfig' | 'ajustes'> {
  const v = useContext(Contexto)
  if (!v) throw new Error('usarEstado debe usarse dentro de <Proveedor>')
  return v
}
