import { useEffect, useState } from 'react'

export const VISTAS = ['revisar', 'precios'] as const
export type Vista = (typeof VISTAS)[number]

export interface Ruta {
  vista: Vista
  params: URLSearchParams
}

/** Lee la ruta del hash: "#/revisar?ejemplo=01". */
function leer(): Ruta {
  const [camino, consulta = ''] = window.location.hash.replace(/^#\/?/, '').split('?')
  const vista = (VISTAS as readonly string[]).includes(camino) ? (camino as Vista) : 'revisar'
  return { vista, params: new URLSearchParams(consulta) }
}

export function usarRuta(): Ruta {
  const [ruta, setRuta] = useState<Ruta>(leer)
  useEffect(() => {
    const alCambiar = () => setRuta(leer())
    window.addEventListener('hashchange', alCambiar)
    return () => window.removeEventListener('hashchange', alCambiar)
  }, [])
  return ruta
}
